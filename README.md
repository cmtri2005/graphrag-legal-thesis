# graphrag-legal-thesis

Crawler + graph builder for a temporal-aware Vietnamese legal knowledge graph,
sourced from `vbpl.vn` (Bộ Tư pháp's legal document portal). Built to feed a
Temporal GraphRAG system that can answer "what was the law at time T" style
questions, not just "what is the law now."

Three docs sit behind this one, and they answer different questions:

- **[docs/plans/active/master-plan.md](docs/plans/active/master-plan.md)** —
  *where the project stands*: the thesis timeline, every task's status with
  evidence. This is the source of truth for progress.
- **[docs/crawling-plan.md](docs/crawling-plan.md)** — *why* the pipeline is
  shaped this way, and every trap the data turned out to hold. Read it before
  touching Stage 1-3.
- **[docs/audit_dataset.md](docs/audit_dataset.md)** — *what the corpus
  actually holds* as of 2026-09-12, gaps included.

This README is the orientation map and the how-to-run.

## Crawl status (2026-09-04, historical — current progress lives in the master plan)

| Stage | State | Output |
|---|---|---|
| 1. Seed discovery | done, 4 domains | `data/seeds.json` |
| 2. Graph expansion (forward BFS) | done | folded into Stage 3's run |
| 2b. Reverse-edge closure | done | `data/diagrams/`, `data/reverse_seeds.json` |
| 3. Full fetch | done, resumable | `data/raw/*.json`, `data/manifest.sqlite` |
| 3b. `referenceType` mapping | done, hand-verified | `data/reference_type_map.json` |
| 4. Field-based review | done, human-confirmed | `data/excluded_ids.txt` |
| 5a. Provision trees | done, 99%+ | `data/trees/*.json` |
| 5b. Text → tree mapping | done, 98.9% of matchable nodes | `data/provisions/*.json` |
| 6. Temporal graph build | **not started** | — |
| 6b. Delta/incremental crawl | done | `scripts/pipeline/delta_crawl.py`, `data/delta_runs.jsonl` |
| — history backfill (Stage 6 input) | done | `data/history/*.json` |
| — verification | `scripts/check/verify_pipeline.py`, all passing | — |

Current corpus: **20,749 documents**, **148,505 edges**, **1.19M provision
nodes** (239k Điều / 513k Khoản / 380k Điểm).

| Domain | Seeds |
|---|---|
| `dat_dai` (đất đai/nhà ở/BĐS/sử dụng đất) | 772 |
| `thue` (thuế/phí/hải quan/hóa đơn) | 3,486 |
| `doanh_nghiep_dau_tu` (doanh nghiệp/đầu tư/chứng khoán) | 3,745 |
| `giao_thong` (đường bộ/sắt/thủy/hàng không/hàng hải/đăng kiểm) | 2,545 |

Domain counts sum to more than the 9,806 unique seed ids — 588 documents match
more than one domain's keywords. Provenance of every document is recoverable:
9,806 seeds, ~8,900 forward-BFS, 2,335 from Stage 2b.

## Why this data source, and why it's messy

`vbpl.vn`'s frontend is server-rendered and has no listing API you can call
directly (search/list endpoints all 401 — internal token, CORS-only). The
actual data comes from a public JSON gateway
(`vbpl-bientap-gateway.moj.gov.vn/api`) that *is* open, but:

- There's no "list all documents" or "list by category" endpoint. Discovery
  has to go through the site's `sitemap.xml` (keyword-filter the slug) plus
  BFS through each document's own `references[]` (its amendment/replacement
  lineage).
- The government's own document metadata (`documentMajors`,
  `documentFields` — i.e. which ministry/topic a doc is tagged under) is
  noisy enough that we do **not** trust it for automated filtering. See
  "Field-based filtering" below — this bit us for real during Stage 4.
- `referenceType` (the edge label between two documents) is a bare integer
  with no client-side label anywhere — it had to be hand-verified against
  the live UI, once, and frozen into a config file.

If you're about to write code that trusts a metadata field at face value,
check whether Stage 4's postmortem already tells you not to.

## Architecture

```
src/legal_crawler/
  config.py       per-domain seed keywords, API base URL, sitemap shard range
  models.py       Edge and SitemapEntry dataclasses

  -- acquisition: talks to vbpl.vn, writes data/, never interprets --
  sources/        api_client.py (JSON gateway), sitemap.py (shards, keyword match)
  storage/        documents.py (the data/ layout), manifest.py (delta side-table)
  vocab/          verified code tables, fail-loud on unknown codes
  graph/          expand.py (Stage 2 BFS), diagram.py (Stage 2b inbound relations)
  provisions/     tree.py (Stage 5a), text.py (Stage 5b)

  -- interpretation: reads data/, never writes it --
  temporal/       domain model + formula (2)(3): version_chain, validity, snapshot,
                  event_applier. Storage-free, stdlib only.
  extraction/     target_resolver.py: locator ("Khoản 1, Điều 3") -> provision id
  ingest.py       data/ -> temporal objects; the only module that knows both shapes
  index.py        TemporalIndex: SQLite, derived from data/, delete and rebuild freely
```

`data/` is the system of record. `data/temporal.sqlite` is an index over it, so
there is no migration story: `build_store.py` deletes it and rebuilds whole.

Data flow: `seeds.json` (Stage 1) → `build_graph.py` BFS-expands and fetches
into `data/raw/*.json` + `data/manifest.sqlite` + `data/edges.jsonl` (Stage
2+3) → `expand_reverse.py` finds the documents that acted *on* the corpus and
feeds their ids back through `build_graph.py --extra-seeds` (Stage 2b) →
`filter_by_field.py` produces a review list, a human decides, and
`apply_field_review.py` writes the confirmed `data/excluded_ids.txt` (Stage
4) → `fetch_provision_trees.py` and `fetch_histories.py` add the per-document
structure and effectivity timeline that Stage 6 needs →
`attach_provision_text.py` joins the body text onto those tree nodes
(Stage 5b) → `delta_crawl.py` decides what has gone stale and deletes exactly
those cached files, so re-running the same chain refills only the gap.

Nothing downstream deletes raw JSON — exclusion is a skip-list applied at read
time, so re-including a document later is a one-line config change, not a
re-crawl.

Run `verify_pipeline.py` after any crawl: it re-checks the whole corpus offline
in seconds and exits non-zero on the first inconsistency.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

Requires Python 3.10+. Only runtime dependency is `requests`.

## Running the pipeline

All scripts are resumable/idempotent — safe to re-run, safe to interrupt.
Run from the repo root with the venv active.

```bash
# Stage 1 — rebuild seed list from the live sitemap (cheap, ~1.5MB x 12 shards)
python3 scripts/pipeline/collect_seeds.py

# Stage 2+3 — BFS-expand through genealogy edges, fetch every doc, persist.
# --max-documents is a circuit breaker, NOT a scope limit (see docs/crawling-plan.md).
# ALWAYS pass a value comfortably above your current data/raw count, or a
# resumed run will truncate edges.jsonl to the breaker value — see Gotchas.
# --extra-seeds keeps Stage 2b's finds in the graph; drop it and they vanish
# from edges.jsonl even though their JSON is still on disk.
python3 scripts/pipeline/build_graph.py --max-documents 40000 \
    --extra-seeds data/reverse_seeds.json

# Stage 2b — pull in the documents that amended/repealed/replaced the corpus.
# Forward BFS cannot find these: references[] only points outward.
python3 scripts/pipeline/expand_reverse.py
# -> then re-run build_graph.py above so edges.jsonl includes them

# Stage 4 — flag seed docs whose ministry/topic tag looks off-domain
python3 scripts/review/filter_by_field.py
# -> inspect data/field_filter_review.txt by hand, then encode your decisions
#    in scripts/review/apply_field_review.py's CONFIRMED_EXCLUSIONS dict and run it
python3 scripts/review/apply_field_review.py

# Stage 5a + history backfill — independent, different hosts, safe in parallel
python3 scripts/pipeline/fetch_provision_trees.py
python3 scripts/pipeline/fetch_histories.py

# Stage 5b — offline, no network; ~40 min for the whole corpus
python3 scripts/pipeline/attach_provision_text.py

# Stage 6 — derived query index, then resolve expiryProvisions onto it
python3 scripts/pipeline/build_store.py            # ~5 min, data/temporal.sqlite
python3 scripts/pipeline/resolve_expiry_targets.py

# Keeping the corpus current (§6b). --dry-run reports without touching anything;
# without it, stale caches are deleted and the commands to refill them printed.
python3 scripts/pipeline/delta_crawl.py --dry-run

# Always finish here
python3 scripts/check/verify_pipeline.py
```

Adding a domain, or widening an existing one: edit `KEYWORDS_BY_DOMAIN` in
`src/legal_crawler/config.py`, then re-run Stage 1 and Stage 2+3 — both are
additive and won't touch already-crawled documents. Keywords match whole
dash-separated words, so a short keyword already covers longer phrases
containing it (`su-dung-dat` covers `quy-hoach-su-dung-dat`).

`measure_recall.py` estimates what the current keyword list still misses; run
it before deciding which keywords to add.

Run tests with `pytest` (or `python3 -m pytest`) from the repo root.

## Data files

| File | What it is | Safe to delete? |
|---|---|---|
| `data/seeds.json` | keyword-matched seed doc ids per domain | yes, `collect_seeds.py` rebuilds it |
| `data/raw/{id}.json` | one file per document, full API response | **no** — this is the crawl; losing it means re-crawling |
| `data/manifest.sqlite` | id → last-crawled/lastmod/removed_at, for delta runs | rebuildable from `data/raw/`, but you lose delta history |
| `data/edges.jsonl` | fully regenerated every `build_graph.py` run from `data/raw/` | yes |
| `data/failed_ids.txt` | ids that failed on the *last* run (dangling refs get moved to manifest's `removed_at`; only transient failures should reappear here) | yes, regenerated each run |
| `data/reference_type_map.json` | hand-verified `referenceType` code → label/group | **no** — this took manual browser verification, see §3b |
| `data/field_filter_map.json` | blocklist of confidently off-topic majors/fields, used by Stage 4 | edit with care, read its own `note` field first |
| `data/trees/{id}.json` | Chương/Điều/Khoản/Điểm tree, `[]` when the document has no structure | yes, but it's ~5h to refetch |
| `data/history/{id}.json` | effectivity timeline — Stage 6's core input | yes, but slow to refetch |
| `data/diagrams/{id}.json` | inbound + outbound relations, Stage 2b's discovery source | yes, slow to refetch |
| `data/reverse_seeds.json` | ids Stage 2b discovered; **pass to `build_graph.py --extra-seeds`** | no — without it those documents drop out of `edges.jsonl` |
| `data/central_sitemap.json` | cached central sitemap enumeration, used by `measure_recall.py` | yes, refetched in ~1 min |
| `data/recall_candidates.txt` | sample of in-scope-looking documents we do NOT hold (§5e) | yes, regenerated |
| `data/provisions/{id}.json` | Stage 5b — text keyed by tree node id, plus that document's coverage | yes, ~40 min to rebuild offline |
| `data/provision_review.txt` | documents under 50% node coverage — almost all have unnumbered trees | yes, regenerated |
| `data/fetch_failures.txt` | the 18+2 documents that permanently fail; scripts skip them by default | no — an unexplained gap and a known-bad document must not look alike |
| `data/delta_runs.jsonl` | when each delta run happened and what it moved | **no** — this is what lets the corpus say "as of when" |
| `data/tree_content_mismatch.txt` | documents whose tree claims articles the body lacks — review queue for Stage 5b | yes, regenerated |
| `data/field_filter_review.txt` | Stage 4 candidates, regenerated each run | yes |
| `data/excluded_ids.txt` | **human-confirmed** exclusions from `apply_field_review.py` | no — encodes a manual decision, don't hand-edit without updating the script's `CONFIRMED_EXCLUSIONS` too |

## Gotchas (learned the hard way — read before you crawl)

1. **`--max-documents` default is 5000.** The corpus is already past that.
   Running `build_graph.py` with no flag once truncated `edges.jsonl` down
   to 5000 docs and silently overwrote the full file (raw JSON was fine —
   edges.jsonl is regenerated from *whatever* `result.documents` came back
   with, truncated or not). Always pass an explicit `--max-documents` above
   your current `data/raw` count.
2. **4xx from the API is not transient.** `/doc/{id}` returns HTTP 400 with
   `messageCode: invalid.document.entity.not.found` for a dangling reference
   — a real, permanent condition (the target was removed from vbpl.vn but
   another document still cites it). `sources/api_client.py` does not retry these;
   only network errors and 5xx get the retry/backoff. If you see 4xx being
   retried again, that's a regression — the whole point of `DocumentNotFoundError`
   is to fail fast on it.
3. **Don't trust `documentMajors`/`documentFields` for automated filtering.**
   56% of the corpus has no classification at all (`Chưa phân loại`), and
   worse — a *Personal Income Tax Law implementing decree* was found tagged
   solely under `Lao động - Thương binh và Xã hội` (Labor ministry), and a
   VAT enforcement directive was tagged `Công an` (Police) alongside
   `Tài chính`. `vocab/field_filter.py` treats a document as off-topic only when
   **every** major/field it has is on the blocklist, and even then the
   result is a review candidate, never an auto-delete. If you're tempted to
   skip the human-review step "just this once," don't — re-read the exclude
   list in `data/excluded_ids.txt` for the kind of false positive this
   would have produced.
4. **Genealogy edges vs. citation edges are not interchangeable.** Stage 2
   only recurses through `amends/replaces/repeals/consolidates/implements`
   edges (`EdgeGroup.GENEALOGY`); `cites/applies/basis` edges
   (`EdgeGroup.OPEN_CITATION`) are recorded but never used to discover new
   documents, specifically to stop the crawl from wandering into an
   unrelated legal domain through an open-ended citation chain. If Stage 5/6
   work ever needs to expand scope, expand the keyword list (Stage 1), don't
   change which edges Stage 2 follows.
5. **A `referenceType` code missing from `reference_type_map.json` is a hard
   stop, by design** (`UnknownReferenceTypeError`). Don't add a fallback
   default label — a silently mislabeled edge (e.g. "bãi bỏ" read as "sửa
   đổi") corrupts point-in-time inference downstream. Run
   `collect_reference_types.py` then `scrape_luoc_do.py` to verify the new
   code against the live UI before adding it.

6. **`references[]` is one-directional, and that once hid 2,335 documents.**
   If B amends A, the edge lives in **B's** references, never in A's. Forward
   BFS therefore never learns A was amended unless B turns up some other way —
   and `verify_pipeline.py` cannot catch this, because an edge you never saw
   leaves nothing to check. `/doc/{id}/diagram`'s `documentNamesBySource` is
   the fix (Stage 2b). Follow only codes 1/5/6/10/11/12 through it: inbound
   code 3 alone occurs 555,592 times and would drag in the whole 172k database.

7. **The provision tree is good, not gospel.** 1.2% of documents have a tree
   listing articles the body text doesn't contain (`data/tree_content_mismatch.txt`),
   and some `Article` nodes are titled just `"Điều"` with no number. Key nodes
   by `id`/`orderIndex`, never by parsing the title, and treat a tree/body
   conflict as a review item rather than picking a side.

8. **`history[].createdDate` is only a legal date when `createdBy == "Job"`.**
   `Admin` rows carry the data-entry timestamp instead — one 2006 law has a
   `DATE_BH` row dated 2025. Using it blindly dates documents to whenever a
   clerk typed them in, with nothing to flag the error.

9. **`hasContent: true` can be a lie** — 287 documents claim it with a
   completely empty body. Measure the text length instead. Overall ~10% of the
   corpus has no text, but that concentrates in doc types §4 excludes anyway
   (Công văn 88% empty, Văn bản hợp nhất 85%); real QPPL is 5.4%.

10. **Document bodies come in two unrelated HTML formats.** Modern records tag
    every paragraph with the provision tree's own node uuid
    (`<p id="…" class="prov-article">`), so mapping text to nodes is an exact
    join — no parsing heuristics needed. Older records are plain HTML with no
    ids, and they wrap paragraphs in `<div>`, not `<p>`. A `<p>`-only parser
    returns *nothing* for those and it looks exactly like an empty document.

11. **An empty field is not a changed field.** The first delta run reported
    2,345 stale documents and 904 vanished ones; both were zero. 3,168 documents
    were found by BFS and never had a `sitemap_lastmod` recorded, so comparing
    `""` against any real value flagged them all — and documents that were never
    on the central sitemap can't be "missing" from it. Real counts: 84 and 0.

## What's next

See [docs/plans/active/master-plan.md](docs/plans/active/master-plan.md). The
storage stack (Neo4j + Milvus, both derived from `data/`) is fixed by
[docs/decisions/0001](docs/decisions/0001-neo4j-milvus-la-kho-dan-xuat.md);
`index.py`/`build_store.py` below are a bridge until the Neo4j loader lands.

**Two known limits, both deliberate:**
- 748 documents sit in `data/provision_review.txt` — old records whose tree is
  unnumbered (`Phần`, `Điều`, five sibling nodes all titled `Khoản 1`) while the
  body runs `I.` / `1.1.`. There is no honest way to align those, so they are
  listed rather than guessed at.
- The numeric suffix on `HHL1P1..4` is unresolved. Every `HHL1P*` is treated as
  "partly expired" and nothing more; see `data/eff_status_map.json`.

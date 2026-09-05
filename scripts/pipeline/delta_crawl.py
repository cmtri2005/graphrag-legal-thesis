#!/usr/bin/env python3
"""Stage C — work out what changed since the last crawl (docs/crawling-plan.md §6b).

It does not re-crawl anything itself. Every fetching script here is already
resumable and skips whatever is already on disk, so the only thing a delta run
has to do is **decide what is stale and delete those cached files**; the normal
pipeline then refills exactly that gap. Reimplementing BFS for the delta path
would be a second copy of the hard part, kept in sync by hope.

What counts as stale:

* **`lastmod` advanced** on the sitemap for a document we hold.
* **New id** whose slug matches a domain keyword — a real effect, not a
  precaution: 12 in-domain documents appeared in the 11 days after the first
  crawl (§5e).
* **Silently expired**: status still `Còn hiệu lực` in the manifest but `effTo`
  is now in the past. This is the trap that makes `lastmod` alone insufficient —
  a law reaching its own expiry date changes nothing on its page, so the sitemap
  never notices. `--recheck-all-active` widens this to every active document,
  for an occasional deep pass.
* **Gone from the sitemap** → `removed_at`, never deleted: history queries still
  need the document. Only documents we once *saw* on the sitemap qualify —
  ~900 held documents were reached by BFS and never appeared on the central
  shards at all, and calling those "removed" would be a fabrication.

One correction the first run forced: a document whose manifest `sitemap_lastmod`
is empty (BFS-discovered, never seen on a shard) is not evidence of a change.
Comparing "" against a real lastmod flagged 2,264 unchanged documents as stale.
Those are only stale if the sitemap edit is *newer than our copy*, which is what
`last_crawled_at` is for.

Every run appends to `data/delta_runs.jsonl`. A point-in-time corpus whose parts
were fetched on different days is a corpus that quietly lies about "as of when",
so the timestamp is written whether anything changed or not.

Usage:
    python scripts/pipeline/delta_crawl.py --dry-run     # report only, touch nothing
    python scripts/pipeline/delta_crawl.py               # stage the delta, print next steps
"""
from __future__ import annotations

import argparse
import json
from datetime import date, datetime, timezone
from pathlib import Path

import requests

from legal_crawler.config import KEYWORDS_BY_DOMAIN
from legal_crawler.storage.manifest import CrawlManifest
from legal_crawler.sources.sitemap import fetch_central_entries, matches_any_keyword
from legal_crawler.storage.documents import DocumentStore


def domain_of(slug: str) -> str | None:
    for domain, keywords in KEYWORDS_BY_DOMAIN.items():
        if matches_any_keyword(slug, keywords):
            return domain
    return None


def is_stale(record: tuple[str, str] | None, sitemap_lastmod: str) -> bool:
    """Whether the sitemap says our copy is out of date.

    Dates only — `lastmod` is date-precision on this site while
    `last_crawled_at` is a UTC timestamp, so comparing further would just
    compare noise.
    """
    if record is None:
        return True
    recorded, crawled_at = record
    if recorded == sitemap_lastmod:
        return False
    if not recorded:
        # Never recorded, so a difference is our gap, not the site's edit.
        # Only a sitemap edit newer than our copy actually means anything.
        return not crawled_at or sitemap_lastmod[:10] > crawled_at[:10]
    return True


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=Path("data"))
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--recheck-all-active",
        action="store_true",
        help="re-fetch every 'Còn hiệu lực' document, not just those past their effTo",
    )
    args = parser.parse_args()

    store = DocumentStore(args.data)
    d = args.data
    manifest = CrawlManifest(d / "manifest.sqlite")
    held = store.ids("raw")
    today = date.today().isoformat()
    now = datetime.now(timezone.utc).isoformat()

    print("fetching central sitemap shards…", flush=True)
    with requests.Session() as session:
        entries = list(fetch_central_entries(session))
    print(f"  {len(entries):,} document entries on the sitemap")

    known = manifest.freshness()

    stale: set[str] = set()
    new_seeds: dict[str, list[str]] = {domain: [] for domain in KEYWORDS_BY_DOMAIN}
    seen: set[str] = set()
    for entry in entries:
        seen.add(entry.doc_id)
        if entry.doc_id in held:
            if is_stale(known.get(entry.doc_id), entry.lastmod):
                stale.add(entry.doc_id)
        elif (domain := domain_of(entry.slug)) is not None:
            new_seeds[domain].append(entry.doc_id)

    expired = [
        doc_id
        for doc_id in manifest.expired_but_still_active(today, all_active=args.recheck_all_active)
        if doc_id in held
    ]
    stale.update(expired)
    # Never on a central shard in the first place => absence proves nothing.
    vanished = sorted(i for i in held - seen if (known.get(i) or ("", ""))[0])
    new_count = sum(len(v) for v in new_seeds.values())

    print(f"\n  stale (lastmod moved or past effTo): {len(stale):,}  [{len(expired):,} from effTo]")
    print(f"  new in-domain ids not held:          {new_count:,}")
    print(f"  held but gone from sitemap:          {len(vanished):,}")

    if args.dry_run:
        print("\n--dry-run: nothing written")
        return

    dropped = sum(store.drop(doc_id) for doc_id in stale)
    if vanished:
        manifest.mark_removed(vanished, now)

    seeds_path = d / "delta_seeds.json"
    if new_count:
        seeds_path.write_text(
            json.dumps(
                {k: [{"doc_id": i, "slug": ""} for i in v] for k, v in new_seeds.items() if v},
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

    with (d / "delta_runs.jsonl").open("a", encoding="utf-8") as f:
        f.write(
            json.dumps(
                {
                    "at": now,
                    "sitemap_entries": len(entries),
                    "held_before": len(held),
                    "stale": len(stale),
                    "expired_by_date": len(expired),
                    "new_in_domain": new_count,
                    "vanished": len(vanished),
                    "recheck_all_active": args.recheck_all_active,
                },
                ensure_ascii=False,
            )
            + "\n"
        )

    print(f"\ndropped {dropped} cached file(s); run logged to {d / 'delta_runs.jsonl'}")
    if not stale and not new_count and not vanished:
        print("nothing to do — corpus is current.")
        return

    print("\nNow re-run the pipeline; each step refills only what was dropped:")
    extra = f" --extra-seeds {seeds_path}" if new_count else ""
    print("  python scripts/pipeline/build_graph.py --max-documents 40000 --extra-seeds data/reverse_seeds.json")
    if new_count:
        print(f"    (and again with{extra} to pull the {new_count} new in-domain document(s))")
    print("  python scripts/pipeline/expand_reverse.py")
    print("  python scripts/pipeline/fetch_provision_trees.py")
    print("  python scripts/pipeline/fetch_histories.py")
    print("  python scripts/pipeline/attach_provision_text.py")
    print("  python scripts/check/verify_pipeline.py")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""L2 (master plan P3.11) — provision-level events read from acting documents.

For every document that acts on another through a genealogy edge, read its
own text for "Bãi bỏ khoản 2 Điều 11 Nghị định số X" / "Điều 1. Sửa đổi …
Nghị định số X như sau: 1. Sửa đổi khoản 2 Điều 5 …" (see
`extraction.provision_ops`), then resolve the cited number and locator
through the same `TargetResolver` the expiry strings use. Nothing is guessed:
an unresolved or ambiguous reference is written with its code, not dropped.

Each row is an event in the store of docs/plans/active/l2-event-store.md: a
stable `id`, and a `status` (`EventStatus`) that decides whether P3.15 may
apply it:

* `verified` — the portal's own `expiryProvisions` lists the provision this
  ending operation hits (`expiry_targets.jsonl`, resolved exactly);
* `auto_accepted` — resolved, dated and carrying what `EventApplier` needs:
  nothing for a repeal, the new text per node for an amendment
  (`extraction.wording`);
* `needs_review` — everything else, with `status_reason`.

Reads `data/raw`, `data/edges.jsonl`, `data/expiry_targets.jsonl` and the index
from `build_store.py --with-subtrees` (derived Khoản/Điểm must be resolvable).
Writes `data/derived/provision_events.jsonl`, one line per (mention, locator).
Offline, a pure function of `data/` — delete and re-run.

Usage:
    python scripts/pipeline/extract_provision_events.py
"""
from __future__ import annotations

import argparse
import collections
import json
import re
from pathlib import Path

from datetime import date

from legal_crawler.extraction import TargetReference, TargetResolver, TargetScope
from legal_crawler.extraction.provision_ops import extract_mentions, normalize_number, title_document
from legal_crawler.extraction.wording import fit, parse_items, wording_blocks
from legal_crawler.index import TemporalIndex
from legal_crawler.provisions.text import parse_paragraphs
from legal_crawler.storage.documents import DocumentStore
from legal_crawler.temporal.ids import make_document_id, make_event_id

# Operations that end the version the portal calls expired (see measure_provision_events.py).
ENDING = {"repeal", "replace", "amend", "correct", "suspend"}
TEXT_OPS = {"amend", "replace", "correct"}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--data", type=Path, default=Path("data"))
    parser.add_argument("--index", type=Path, default=None, help="default: <data>/temporal.sqlite")
    args = parser.parse_args()
    data = args.data
    store = DocumentStore(data)
    index = TemporalIndex(args.index or data / "temporal.sqlite")
    resolver = TargetResolver(index)

    by_number: dict[str, list[str]] = collections.defaultdict(list)
    for doc in index.documents():
        if doc.number:
            by_number[normalize_number(doc.number)].append(doc.id)

    targets_of: dict[str, set[str]] = collections.defaultdict(set)
    actors: dict[str, str] = {}  # domain id -> portal id, which names the file under data/raw
    for line in (data / "edges.jsonl").read_text(encoding="utf-8").splitlines():
        edge = json.loads(line)
        source = make_document_id(edge["source_id"])
        targets_of[source].add(make_document_id(edge["target_id"]))
        if edge["group"] == "genealogy":
            actors[source] = edge["source_id"]

    # Only a central normative act can amend one (ADR 0002 scope): a provincial
    # resolution or a consolidated text that cites "Điều 4 Nghị định số X" is
    # quoting it, not changing it.
    central = {
        make_document_id(row["doc_id"]) for row in map(json.loads, (data / "derived/eligibility.jsonl").read_text(encoding="utf-8").splitlines())
        if row.get("doc_class") == "qppl"
    }

    gold: set[tuple[str, str]] = set()
    for line in (data / "expiry_targets.jsonl").read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row.get("code") == "resolved_exact":
            gold.update((row["doc_id"], pid) for pid in row.get("provision_ids", []))
    tree_cache: dict[str, dict] = {}

    def provision(doc_id: str, pid: str):
        if doc_id not in tree_cache:
            tree_cache.clear()  # ponytail: one document at a time is enough, rows come grouped by actor
            tree_cache[doc_id] = {p.id: p for p in index.document_order(doc_id)}
        return tree_cache[doc_id].get(pid)

    stats: collections.Counter[str] = collections.Counter()
    rows: collections.Counter[str] = collections.Counter()
    skipped_mismatch: list[str] = []
    out_path = data / "derived" / "provision_events.jsonl"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as out:
        for actor_id, portal_id in sorted(actors.items()):
            if actor_id not in central:
                stats["actor out of scope"] += 1
                continue
            raw = store.load("raw", portal_id)
            html = ((raw or {}).get("documentContent") or {}).get("content") or ""
            if not html:
                stats["actor without body"] += 1
                continue
            paragraphs = [p.text for p in parse_paragraphs(html)]
            if not _body_is_own(paragraphs, raw.get("docNum") or ""):
                skipped_mismatch.append(actor_id)
                continue
            stats["actors read"] += 1
            actor = index.document(actor_id)
            effective_on = actor.effective_from.isoformat() if actor and actor.effective_from else None
            mentions = extract_mentions(paragraphs, title_document(raw.get("title") or ""))
            blocks = wording_blocks(paragraphs)
            for n, mention in enumerate(mentions):
                candidates = [c for c in by_number.get(normalize_number(mention.document_number), []) if c != actor_id]
                narrowed = [c for c in candidates if c in targets_of[actor_id]]
                candidates = narrowed or candidates
                base = {
                    "actor_id": actor_id,
                    "actor_number": raw.get("docNum"),
                    "operation": mention.operation.value,
                    "method": mention.method,
                    "document_number": mention.document_number,
                    "candidate_document_ids": candidates,
                    "effective_on": effective_on,
                    "evidence": mention.evidence,
                }
                references = (
                    [TargetReference(f"{actor_id}:{n}", mention.evidence or "?", TargetScope.DOCUMENT,
                                     document_reference=mention.document_number)]
                    if not mention.locators else
                    [TargetReference(f"{actor_id}:{n}:{k}", mention.evidence or "?", TargetScope.SUBTREE,
                                     document_reference=mention.document_number, locator=loc)
                     for k, loc in enumerate(mention.locators)]
                )
                for ref in references:
                    row = dict(base, locator=[[p.level.value, p.label] for p in ref.locator.parts] if ref.locator else None)
                    if not candidates:
                        row.update(code="document_not_in_corpus", target_document_id=None,
                                   target_provision_id=None, affected_provision_ids=[])
                    else:
                        res = resolver.resolve(ref, candidates)
                        target = res.target
                        row.update(
                            code=res.code.value,
                            target_document_id=target.target_document_id,
                            target_provision_id=target.target_provision_ids[0] if target.target_provision_ids else None,
                            affected_provision_ids=list(target.affected_provision_ids),
                        )
                    updates = None
                    block = blocks.get(mention.paragraph)
                    if row["operation"] in TEXT_OPS and block and row["target_provision_id"]:
                        items = parse_items(block.lines)
                        root = provision(row["target_document_id"], row["target_provision_id"])
                        if items and root:
                            updates = fit(items, {p.level: p.label for p in ref.locator.parts}, root,
                                          index.descendants_of(root.id))
                    row["text_updates"] = [{"target_provision_id": k, "new_text": v} for k, v in (updates or {}).items()]
                    row["status"], row["status_reason"] = _status(row, block is not None, gold)
                    row["id"] = make_event_id(
                        actor_id, row["operation"],
                        [row["target_provision_id"]] if row["target_provision_id"] else [],
                        date.fromisoformat(effective_on) if effective_on else None,
                        target_document_id=row["target_document_id"],
                        evidence_text=f"{mention.evidence}|{row['locator']}",
                    )
                    stats[f"status {row['status']:<13} {row['status_reason'] or ''}"] += 1
                    rows[f"{row['operation']:<10} {'document' if ref.locator is None else 'provision':<9} {row['code']}"] += 1
                    out.write(json.dumps(row, ensure_ascii=False) + "\n")

    print(f"{stats['actors read']:,} acting documents read -> {out_path}")
    print(f"  skipped: {stats['actor out of scope']:,} not central normative, {stats['actor without body']:,} without body, "
          f"{len(skipped_mismatch):,} whose body carries another document's number: {skipped_mismatch[:12]}")
    for key, count in sorted(rows.items()):
        print(f"  {count:>7,}  {key}")
    for key, count in sorted((k, v) for k, v in stats.items() if k.startswith("status ")):
        print(f"  {count:>7,}  {key}")


def _status(row: dict, quoted: bool, gold: set[tuple[str, str]]) -> tuple[str, str | None]:
    """(EventStatus value, reason) — the gate P3.15 reads before applying."""
    op = row["operation"]
    if not row["code"].startswith("resolved"):
        return "needs_review", row["code"]
    if row["locator"] is None:
        return "needs_review", "document_scope"  # the document's own effTo already dates it
    if row["effective_on"] is None:
        return "needs_review", "missing_effective_date"
    if op in TEXT_OPS and not row["text_updates"]:
        return "needs_review", "structure_mismatch" if quoted else "missing_resulting_text"
    if op not in ENDING or op == "suspend":
        return "needs_review", f"{op}_not_materializable"
    if any((row["target_document_id"], pid) in gold for pid in row["affected_provision_ids"]):
        return "verified", None
    return "auto_accepted", None


_BODY_NUMBER = re.compile(r"Số\s*:?\s*(\d[^\s,;]*(?:\s?[/\-]\s?[^\s,;]+)*)")


def _body_is_own(paragraphs: list[str], doc_num: str) -> bool:
    """False when the "Số: …" header in the body names a different document.

    The portal occasionally serves another document's body under an id (e.g.
    26/2025/QĐ-TTg carrying a joint resolution amending 72/2025/NQLT); every
    event read from it would be dated by the wrong act. No header: trust it.
    """
    for text in paragraphs[:8]:
        m = _BODY_NUMBER.search(text)
        if m:
            body, own = normalize_number(m.group(1)), normalize_number(doc_num)
            return body == own or body.startswith(own) or own.startswith(body)
    return True


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Backfill T2 — write `data/derived/eligibility.jsonl` and the manual-text queue.

Offline and a pure function of `data/`: delete the outputs and run again.

Per document:
    doc_class           vocab.scope.document_class
    in_scope            central QPPL (ADR 0002)
    anchor_problem      vocab.status_codes.anchor_problem, None when anchored
    has_text            its provisions file carries at least one node
    has_body            the portal's body shows any text at all
    benchmark_eligible  in_scope, anchored, has text
    manual_text         priority for typing the text in by hand, or null — only
                        for an in-scope document whose body is empty:
                        1  not fully repealed
                        2  fully repealed, a seed on a genealogy path
                        Any other empty-bodied document is not needed and stays
                        out of retrieval and benchmark (decision 2026-09-14).
                        A body with text but no provisions needs structure, not
                        typing, and is counted separately.

Also writes `data/derived/manual_text_queue.tsv` (the queue, priority order)
and prints the recount of gaps on the in-scope set (T2.3).

Usage:
    python scripts/pipeline/build_eligibility.py
"""
from __future__ import annotations

import argparse
import collections
import json
from datetime import date
from pathlib import Path

from legal_crawler.provisions.text import has_visible_text
from legal_crawler.storage.documents import DocumentStore, read_json
from legal_crawler.vocab.scope import QPPL, document_class
from legal_crawler.vocab.status_codes import anchor_problem

FULLY_REPEALED = "HHL"


def manual_text_priority(in_scope: bool, has_body: bool, status_code: str | None,
                         is_seed: bool, on_genealogy: bool) -> int | None:
    if not in_scope or has_body:
        return None
    if status_code != FULLY_REPEALED:
        return 1
    if is_seed and on_genealogy:
        return 2
    return None


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=Path("data"))
    args = parser.parse_args()

    store = DocumentStore(args.data)
    today = date.today()
    seeds = {e["doc_id"] for entries in read_json(args.data / "seeds.json").values() for e in entries}
    genealogy: set[str] = set()
    for line in (args.data / "edges.jsonl").read_text(encoding="utf-8").splitlines():
        edge = json.loads(line)
        if edge["group"] == "genealogy":
            genealogy.update((edge["source_id"], edge["target_id"]))
    with_provisions = store.ids("provisions")

    out_dir = args.data / "derived"
    out_dir.mkdir(exist_ok=True)
    rows = []
    for doc_id in sorted(store.ids("raw")):
        doc = store.load("raw", doc_id)
        doc_class = document_class(doc)
        in_scope = doc_class == QPPL
        problem = anchor_problem(doc, today)
        has_text = doc_id in with_provisions and bool(store.load("provisions", doc_id)["nodes"])
        has_body = has_visible_text((doc.get("documentContent") or {}).get("content") or "")
        status = (doc.get("effStatus") or {}).get("code")
        rows.append({
            "doc_id": doc_id,
            "doc_num": doc.get("docNum"),
            "doc_class": doc_class,
            "in_scope": in_scope,
            "anchor_problem": problem,
            "has_text": has_text,
            "has_body": has_body,
            "benchmark_eligible": in_scope and problem is None and has_text,
            "manual_text": manual_text_priority(in_scope, has_body, status, doc_id in seeds, doc_id in genealogy),
            "status": status,
            "pdf": doc.get("documentContentFileName"),
        })

    with (out_dir / "eligibility.jsonl").open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    queue = sorted((r for r in rows if r["manual_text"]), key=lambda r: (r["manual_text"], r["doc_id"]))
    with (out_dir / "manual_text_queue.tsv").open("w", encoding="utf-8") as f:
        f.write("priority\tdoc_id\tdoc_num\tstatus\tpdf\n")
        for r in queue:
            f.write(f"{r['manual_text']}\t{r['doc_id']}\t{r['doc_num']}\t{r['status']}\t{r['pdf'] or ''}\n")

    by_class = collections.Counter(r["doc_class"] for r in rows)
    scoped = [r for r in rows if r["in_scope"]]
    problems = collections.Counter(r["anchor_problem"] for r in scoped if r["anchor_problem"])
    print(f"{len(rows):,} documents -> {out_dir / 'eligibility.jsonl'}")
    for name, count in by_class.most_common():
        print(f"  {count:>6,}  {name}")
    print(f"\nin scope: {len(scoped):,}")
    print(f"  {sum(r['benchmark_eligible'] for r in scoped):>6,}  benchmark eligible (anchored, with text)")
    print(f"  {sum(not r['has_body'] for r in scoped):>6,}  empty body (manual text or excluded)")
    print(f"  {sum(r['has_body'] and not r['has_text'] for r in scoped):>6,}  body text but no provisions (needs structure)")
    for reason, count in problems.most_common():
        print(f"  {count:>6,}  {reason}")
    priorities = collections.Counter(r["manual_text"] for r in queue)
    print(f"\nmanual text queue: {len(queue):,} -> {out_dir / 'manual_text_queue.tsv'}")
    for priority in sorted(priorities):
        print(f"  {priorities[priority]:>6,}  priority {priority}")


if __name__ == "__main__":
    main()

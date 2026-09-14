#!/usr/bin/env python3
"""Stage 5b — write `data/provisions/{id}.json`, node text keyed by tree node id.

Resumable and offline: it only reads `data/raw/` and `data/trees/`, and skips a
document whose output already exists, so an interrupted run just continues.

Only nodes that actually got text are written — the skeleton already lives in
`data/trees/`, and duplicating 1.2M empty nodes would buy nothing.

Documents below `REVIEW_THRESHOLD` coverage go to `data/provision_review.txt`
instead of being quietly accepted. The queue is rebuilt from every file in
`data/provisions/` at the end of each run, not from the documents this run
happened to process — a resumed run used to overwrite 778 entries with 20.
Most of them are old records whose tree is
unnumbered ("Phần", "Điều", five nodes all titled "Khoản 1") while the body uses
"I." / "1.1." — there is no honest way to match those, so they are listed rather
than guessed at (§3b).

Usage:
    python scripts/pipeline/attach_provision_text.py            # whole corpus
    python scripts/pipeline/attach_provision_text.py --limit 200
"""
from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path

from legal_crawler.provisions.text import REVIEW_THRESHOLD, align, flatten
from legal_crawler.storage.documents import DocumentStore

REVIEW_HEADER = "# doc_id\tmethod\tcoverage\tmatched/total — below threshold, need a look\n"


def write_review_queue(store: DocumentStore, path: Path) -> int:
    """Rewrite the review queue from every provisions file; returns its size."""
    rows = []
    for doc_id in sorted(store.ids("provisions")):
        rec = store.load("provisions", doc_id)
        if rec["coverage"] < REVIEW_THRESHOLD:
            rows.append(
                f"{doc_id}\t{rec['method']}\t{rec['coverage']:.2f}\t"
                f"{len(rec['nodes'])}/{rec['total_nodes']}"
            )
    tmp = path.with_suffix(".tmp")
    tmp.write_text(REVIEW_HEADER + "".join(f"{row}\n" for row in rows), encoding="utf-8")
    tmp.replace(path)
    return len(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=Path("data"))
    parser.add_argument("--limit", type=int)
    parser.add_argument("--force", action="store_true", help="rewrite existing outputs")
    args = parser.parse_args()

    store = DocumentStore(args.data)
    out_dir = store.dir("provisions")
    out_dir.mkdir(exist_ok=True)

    tree_paths = sorted(store.dir("trees").glob("*.json"))
    if args.limit:
        tree_paths = tree_paths[: args.limit]

    stats: Counter[str] = Counter()
    matched_nodes = 0

    for i, tree_path in enumerate(tree_paths, 1):
        doc_id = tree_path.stem
        out_path = out_dir / f"{doc_id}.json"
        if out_path.exists() and not args.force:
            stats["skipped"] += 1
            continue

        tree = store.load("trees", doc_id)
        if not tree:
            stats["empty_tree"] += 1
            continue
        raw = store.load("raw", doc_id)
        html = (raw.get("documentContent") or {}).get("content") or ""
        if not html:
            stats["no_content"] += 1
            continue

        result = align(tree, html)
        by_id = {n["id"]: n for n in flatten(tree)}
        store.save(
            "provisions",
            doc_id,
            {
                "doc_id": doc_id,
                "method": result.method,
                "coverage": round(result.coverage, 4),
                "total_nodes": result.total_nodes,
                "nodes": {
                    nid: {
                        "level": by_id[nid].get("level"),
                        "title": by_id[nid].get("title"),
                        "order_index": by_id[nid].get("orderIndex"),
                        "parent_id": by_id[nid].get("parent_id"),
                        "text": text,
                    }
                    for nid, text in result.texts.items()
                },
            },
        )
        stats[result.method] += 1
        matched_nodes += len(result.texts)
        if i % 2000 == 0:
            print(f"  {i}/{len(tree_paths)} …", flush=True)

    queued = write_review_queue(store, args.data / "provision_review.txt")

    print(f"\n{sum(stats.values())} documents")
    for k, v in sorted(stats.items()):
        print(f"  {k:12} {v:,}")
    print(f"  {'nodes':12} {matched_nodes:,} with text (this run)")
    print(f"  {'review':12} {queued:,} below {REVIEW_THRESHOLD:.0%} (whole corpus)")


if __name__ == "__main__":
    main()

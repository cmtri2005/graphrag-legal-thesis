#!/usr/bin/env python3
"""Stage 5b — write `data/provisions/{id}.json`, node text keyed by tree node id.

Resumable and offline: it only reads `data/raw/` and `data/trees/`, and skips a
document whose output already exists, so an interrupted run just continues.

Only nodes that actually got text are written — the skeleton already lives in
`data/trees/`, and duplicating 1.2M empty nodes would buy nothing.

Documents below `--review-threshold` coverage go to `data/provision_review.txt`
instead of being quietly accepted. Most of them are old records whose tree is
unnumbered ("Phần", "Điều", five nodes all titled "Khoản 1") while the body uses
"I." / "1.1." — there is no honest way to match those, so they are listed rather
than guessed at (§3b).

Usage:
    python scripts/attach_provision_text.py            # whole corpus
    python scripts/attach_provision_text.py --limit 200
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from legal_crawler.provision_text import align, flatten  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--data", type=Path, default=Path("data"))
    ap.add_argument("--limit", type=int)
    ap.add_argument("--review-threshold", type=float, default=0.5)
    ap.add_argument("--force", action="store_true", help="rewrite existing outputs")
    args = ap.parse_args()

    out_dir = args.data / "provisions"
    out_dir.mkdir(exist_ok=True)

    tree_paths = sorted((args.data / "trees").glob("*.json"))
    if args.limit:
        tree_paths = tree_paths[: args.limit]

    stats: Counter[str] = Counter()
    review: list[str] = []
    matched_nodes = 0

    for i, tree_path in enumerate(tree_paths, 1):
        doc_id = tree_path.stem
        out_path = out_dir / f"{doc_id}.json"
        if out_path.exists() and not args.force:
            stats["skipped"] += 1
            continue

        tree = json.loads(tree_path.read_text(encoding="utf-8"))
        if not tree:
            stats["empty_tree"] += 1
            continue
        raw = json.loads((args.data / "raw" / f"{doc_id}.json").read_text(encoding="utf-8"))
        html = (raw.get("documentContent") or {}).get("content") or ""
        if not html:
            stats["no_content"] += 1
            continue

        result = align(tree, html)
        by_id = {n["id"]: n for n in flatten(tree)}
        out_path.write_text(
            json.dumps(
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
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        stats[result.method] += 1
        matched_nodes += len(result.texts)
        if result.coverage < args.review_threshold:
            review.append(
                f"{doc_id}\t{result.method}\t{result.coverage:.2f}\t"
                f"{len(result.texts)}/{result.total_nodes}"
            )
        if i % 2000 == 0:
            print(f"  {i}/{len(tree_paths)} …", flush=True)

    if review:
        (args.data / "provision_review.txt").write_text(
            "# doc_id\tmethod\tcoverage\tmatched/total — below threshold, need a look\n"
            + "\n".join(sorted(review))
            + "\n",
            encoding="utf-8",
        )

    print(f"\n{sum(stats.values())} documents")
    for k, v in sorted(stats.items()):
        print(f"  {k:12} {v:,}")
    print(f"  {'nodes':12} {matched_nodes:,} with text")
    print(f"  {'review':12} {len(review):,} below {args.review_threshold:.0%}")


if __name__ == "__main__":
    main()

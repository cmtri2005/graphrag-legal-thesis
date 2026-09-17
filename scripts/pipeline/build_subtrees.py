#!/usr/bin/env python3
"""Backfill T5 — write `data/derived/subtrees/{doc_id}.json` for leaf articles/clauses.

Offline, a pure function of `data/raw` and `data/trees`; delete the directory
and run again. Also writes `data/derived/subtree_sample.tsv`: 100 split nodes
drawn with a fixed seed for the hand check (T5.2, accept at >= 95% correct).

Usage:
    python scripts/pipeline/build_subtrees.py
"""
from __future__ import annotations

import argparse
import collections
import random
import shutil
from pathlib import Path

from legal_crawler.provisions.subtree import METHOD, split_document
from legal_crawler.storage.documents import DocumentStore

SAMPLE_SIZE = 100
SAMPLE_SEED = 20260914
URL = "https://vbpl.vn/van-ban/chi-tiet/van-ban--{}"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=Path("data"))
    args = parser.parse_args()
    store = DocumentStore(args.data)
    out = args.data / "derived" / "subtrees"
    shutil.rmtree(out, ignore_errors=True)
    out.mkdir(parents=True)

    written = nodes = preambles = 0
    levels: collections.Counter[str] = collections.Counter()
    reasons: collections.Counter[str] = collections.Counter()
    pool: list[tuple[str, str, dict]] = []
    for doc_id in sorted(store.ids("trees")):
        tree = store.load("trees", doc_id)
        if not tree:
            continue
        raw = store.load("raw", doc_id)
        html = (raw.get("documentContent") or {}).get("content") or ""
        if not html:
            continue
        split = split_document(tree, html)
        for skip in split.skipped:
            reasons[skip["reason"].split(" [")[0]] += 1
        if not split.nodes:
            continue
        store.save("derived/subtrees", doc_id, {
            "doc_id": doc_id, "method": METHOD, "nodes": split.nodes,
            "preambles": split.preambles, "skipped": split.skipped,
        })
        written += 1
        nodes += len(split.nodes)
        preambles += len(split.preambles)
        for node in split.nodes:
            levels[node["level"]] += 1
            pool.append((doc_id, raw.get("docNum") or "", node))

    sample = random.Random(SAMPLE_SEED).sample(pool, min(SAMPLE_SIZE, len(pool)))
    with (args.data / "derived" / "subtree_sample.tsv").open("w", encoding="utf-8") as f:
        f.write("doc_id\tdoc_num\tnode_id\ttitle\tcorrect(y/n)\ttext\turl\n")
        for doc_id, doc_num, node in sample:
            f.write(f"{doc_id}\t{doc_num}\t{node['id']}\t{node['title']}\t\t{node['text'][:300]}\t{URL.format(doc_id)}\n")

    print(f"{written:,} documents, {nodes:,} split nodes, {preambles:,} preambles recovered -> {out}")
    for level, count in levels.most_common():
        print(f"  {count:>8,}  {level}")
    print("parents refused:")
    for reason, count in reasons.most_common(8):
        print(f"  {count:>8,}  {reason}")


if __name__ == "__main__":
    main()

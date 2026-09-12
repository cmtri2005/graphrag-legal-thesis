#!/usr/bin/env python3
"""Resolve `history[].expiryProvisions` onto provision-tree node ids (Stage 6 L3).

Every history entry that changes a document's effectivity carries an
`expiryProvisions` list saying *which parts* stopped applying — "Khoản 1, Điều
3, Chương I" — and 30k of those are article- or clause-level rather than the
whole document. That is the ground truth the thesis argument needs: a document
flagged "Còn hiệu lực" whose Khoản 2 was repealed three years ago is exactly
the case document-level metadata cannot express, and the portal already
publishes the answer.

So this does not extract anything from statutory text. It parses the portal's
own structured field and joins it to the tree node it names, which makes the
result auditable — every row points at a node id a human can open.

Matching is deliberately tolerant about intermediate levels: the path is
matched against a node's ancestor chain, not its immediate parent, because the
strings routinely skip a level the tree actually has ("Điều 5, Chương II" for a
document where Điều 5 sits under Mục 1 under Chương II). A path that lands on
more than one node is reported as ambiguous rather than guessed at.

Writes `data/expiry_targets.jsonl`, one row per (document, expiry provision).

Usage:
    python scripts/pipeline/resolve_expiry_targets.py
    python scripts/pipeline/resolve_expiry_targets.py --unresolved   # print the misses
"""
from __future__ import annotations

import argparse
import collections
import json
import re
from pathlib import Path

from legal_crawler.storage.documents import DocumentStore

# The portal writes the Vietnamese level word; the tree writes an English one.
LEVELS = {
    "phần": "Part",
    "chương": "Chapter",
    "mục": "Section",
    "tiểu mục": "Subsection",
    "điều": "Article",
    "khoản": "Clause",
    "điểm": "Point",
}
COMPONENT = re.compile(
    r"(tiểu mục|phần|chương|mục|điều|khoản|điểm)\s*([^\s,]*)",
    re.IGNORECASE,
)


def parse_path(text: str) -> list[tuple[str, str]] | None:
    """"Khoản 1, Điều 3, Chương I" -> [(Chapter, i), (Article, 3), (Clause, 1)].

    Returns outermost-first (the source string runs innermost-first), or None
    when the string names no addressable component at all.
    """
    found = [
        (LEVELS[level.lower()], ordinal.strip(".:").casefold())
        for level, ordinal in COMPONENT.findall(text)
    ]
    # An ordinal is what makes a component addressable: bare "Mục, Phần" says
    # only that some section somewhere lapsed, which is not a target.
    if not found or any(not ordinal for _, ordinal in found):
        return None
    return list(reversed(found))


def index_tree(tree: list[dict]) -> list[tuple[dict, list[tuple[str, str]]]]:
    """Every node paired with its own (level, ordinal) plus its ancestors'."""
    out: list[tuple[dict, list[tuple[str, str]]]] = []

    def walk(nodes: list[dict], trail: list[tuple[str, str]]) -> None:
        for node in nodes:
            title = (node.get("title") or "").split()
            ordinal = title[-1].casefold() if len(title) > 1 else ""
            here = trail + [(node.get("level") or "", ordinal)]
            out.append((node, here))
            walk(node.get("children") or [], here)

    walk(tree, [])
    return out


def resolve(path: list[tuple[str, str]], indexed) -> list[dict]:
    """Nodes whose ancestor chain contains every component, innermost last."""
    target = path[-1]
    hits = []
    for node, trail in indexed:
        if trail[-1] != target:
            continue
        if all(component in trail for component in path):
            hits.append(node)
    return hits


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=Path("data"))
    parser.add_argument("--unresolved", action="store_true", help="list what failed")
    args = parser.parse_args()
    store = DocumentStore(args.data)

    stats: collections.Counter[str] = collections.Counter()
    distinct: set[tuple[str, str]] = set()
    distinct_resolved: set[tuple[str, str]] = set()
    misses: collections.Counter[str] = collections.Counter()
    rows: list[dict] = []
    tree_ids = set(store.ids("trees"))

    for doc_id in sorted(store.ids("history")):
        entries = store.load("history", doc_id).get("history") or []
        provisions = [
            (entry, text)
            for entry in entries
            for text in (entry.get("expiryProvisions") or [])
        ]
        if not provisions:
            continue

        indexed = index_tree(store.load("trees", doc_id)) if doc_id in tree_ids else []
        for entry, text in provisions:
            text = text.strip()
            row = {
                "doc_id": doc_id,
                "raw": text,
                "at": entry.get("createdDate"),
                "status": entry.get("content"),
            }
            if text.casefold().startswith("toàn bộ"):
                stats["whole_document"] += 1
                rows.append(row | {"scope": "document", "node_id": None})
                continue

            path = parse_path(text)
            if path is None:
                stats["unparsed"] += 1
                misses[f"unparsed: {text[:50]}"] += 1
                continue
            if not indexed:
                stats["no_tree"] += 1
                continue

            # The portal repeats a document's whole expiry list on every later
            # status edit, so the same provision arrives many times over. Both
            # numbers matter: the rows are per history event, but "how much of
            # this corpus is addressable" is a question about distinct targets.
            distinct.add((doc_id, text))
            hits = resolve(path, indexed)
            if len(hits) == 1:
                distinct_resolved.add((doc_id, text))
                stats["resolved"] += 1
                rows.append(
                    row
                    | {
                        "scope": "provision",
                        "node_id": hits[0]["id"],
                        "level": hits[0].get("level"),
                        "title": hits[0].get("title"),
                        "path": ["%s %s" % c for c in path],
                    }
                )
            elif hits:
                stats["ambiguous"] += 1
                misses[f"ambiguous ({len(hits)} nodes): {text[:50]}"] += 1
            else:
                stats["not_in_tree"] += 1
                misses[f"not in tree: {text[:50]}"] += 1

    out = args.data / "expiry_targets.jsonl"
    with out.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    addressable = sum(
        stats[k] for k in ("resolved", "ambiguous", "not_in_tree", "unparsed", "no_tree")
    )
    print(f"wrote {len(rows):,} rows to {out}\n")
    print(f"  whole-document expiries : {stats['whole_document']:,}")
    print(f"  provision-level entries : {addressable:,}")
    for key, label in (
        ("resolved", "resolved to a tree node"),
        ("ambiguous", "matched more than one node"),
        ("not_in_tree", "named a node the tree lacks"),
        ("unparsed", "no addressable component"),
        ("no_tree", "document has no tree"),
    ):
        share = 100 * stats[key] / addressable if addressable else 0
        print(f"    {stats[key]:>6} ({share:5.1f}%)  {label}")

    if distinct:
        print(
            f"\n  distinct (document, provision) pairs: {len(distinct):,} — "
            f"{len(distinct_resolved):,} resolved "
            f"({100 * len(distinct_resolved) / len(distinct):.1f}%)"
        )
        print("  the gap is dominated by trees that stop at Điều and never "
              "declare the Khoản/Điểm the expiry names")

    if args.unresolved:
        print("\n  most common misses:")
        for text, count in misses.most_common(25):
            print(f"    {count:>5}  {text}")


if __name__ == "__main__":
    main()

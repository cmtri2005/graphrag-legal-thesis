#!/usr/bin/env python3
"""What is actually in `data/` right now — inventory, gaps, temporal readiness.

`verify_pipeline.py` answers "is the corpus self-consistent?" and exits
non-zero when it is not. This answers the different question you have when you
come back to the repo after three weeks: *what do I hold, what is missing, and
is it enough to build Stage 6 on?* It never fails a build — it just reports.

The section that matters most is TEMPORAL READINESS. The whole thesis rests on
answering "what was in force at time t", and the inputs for that are
`effStatus` / `effFrom` on the raw document plus `expiryProvisions` inside
`history/`. That last field carries the article-level repeals that document
level metadata cannot express, and nothing downstream reads it yet.

Read-only and offline. Usage:

    python scripts/check/data_status.py
    python scripts/check/data_status.py --skip-scan   # inventory only, ~1s
"""
from __future__ import annotations

import argparse
import collections
import datetime as dt
import json
from pathlib import Path

from legal_crawler.storage.documents import PER_DOCUMENT_DIRS, DocumentStore, read_json
from legal_crawler.vocab.status_codes import anchor_problem


def _mtime_range(directory: Path) -> str:
    files = list(directory.glob("*.json"))
    if not files:
        return "—"
    times = [f.stat().st_mtime for f in files]
    fmt = "%Y-%m-%d %H:%M"
    oldest = dt.datetime.fromtimestamp(min(times)).strftime(fmt)
    newest = dt.datetime.fromtimestamp(max(times)).strftime(fmt)
    return f"{oldest} -> {newest}"


def _known_failures(data: Path) -> dict[str, set[str]]:
    """doc_ids in fetch_failures.txt, grouped by the stage that failed."""
    path = data / "fetch_failures.txt"
    by_stage: dict[str, set[str]] = collections.defaultdict(set)
    if not path.exists():
        return by_stage
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("#") or not line.strip():
            continue
        parts = line.split("\t")
        if len(parts) >= 2:
            by_stage[parts[0].strip()].add(parts[1].strip())
    return by_stage


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=Path("data"))
    parser.add_argument(
        "--skip-scan",
        action="store_true",
        help="inventory and freshness only; skip the full raw/history read",
    )
    args = parser.parse_args()
    d = args.data
    store = DocumentStore(d)

    ids = {stage: set(store.ids(stage)) for stage in PER_DOCUMENT_DIRS}
    raw = ids["raw"]
    failures = _known_failures(d)

    # ------------------------------------------------------------- inventory
    print("INVENTORY")
    print(f"  {'stage':<12} {'files':>7}  {'vs raw':>8}   last written")
    for stage in PER_DOCUMENT_DIRS:
        n = len(ids[stage])
        pct = f"{100 * n / len(raw):.1f}%" if raw else "—"
        print(f"  {stage:<12} {n:>7}  {pct:>8}   {_mtime_range(store.dir(stage))}")

    # ------------------------------------------------------------------ gaps
    print("\nGAPS (raw documents missing a downstream artefact)")
    for stage in ("trees", "history", "diagrams", "provisions"):
        missing = raw - ids[stage]
        if not missing:
            print(f"  {stage:<12} complete")
            continue
        known = missing & failures.get(stage, set())
        line = f"  {stage:<12} {len(missing):>6} missing"
        if known:
            line += f"  ({len(known)} in fetch_failures.txt)"
        print(line)

    # `provisions` is the one gap with a legitimate bulk explanation (a
    # document with no article structure gets an empty tree and no provision
    # file). Anything left over after that is unexplained, and unexplained is
    # exactly what must not look the same as known-bad.
    empty_tree, no_content, unexplained = [], [], []
    for doc_id in sorted(raw - ids["provisions"]):
        if doc_id not in ids["trees"]:
            continue
        if not store.load("trees", doc_id):
            empty_tree.append(doc_id)
            continue
        content = (store.load("raw", doc_id).get("documentContent") or {}).get("content")
        (no_content if not content else unexplained).append(doc_id)

    print(f"\n  provisions gap breakdown ({len(raw - ids['provisions'])} total)")
    print(f"    {len(empty_tree):>6}  document has no article structure (empty tree)")
    print(f"    {len(no_content):>6}  tree exists but the API returned no body text")
    print(f"    {len(unexplained):>6}  UNEXPLAINED — investigate")
    for doc_id in no_content:
        doc = store.load("raw", doc_id)
        print(f"            no-text: {doc_id:<10} {doc.get('docNum')}")

    if args.skip_scan:
        return

    # ---------------------------------------------------- temporal readiness
    print("\nTEMPORAL READINESS (Stage 6 inputs)")
    status = collections.Counter()
    missing_eff_from = 0
    for doc_id in raw:
        doc = store.load("raw", doc_id)
        status[(doc.get("effStatus") or {}).get("name") or "(no effStatus)"] += 1
        if not doc.get("effFrom"):
            missing_eff_from += 1

    print("  effStatus:")
    for name, count in status.most_common():
        print(f"    {count:>6}  {name}")
    print(f"  {missing_eff_from:>8}  documents with no effFrom date")

    whole, article_level = 0, 0
    docs_with_article_level: set[str] = set()
    empty_history = 0
    for doc_id in ids["history"]:
        entries = store.load("history", doc_id).get("history") or []
        if not entries:
            empty_history += 1
        for entry in entries:
            for provision in entry.get("expiryProvisions") or []:
                if provision.strip().lower().startswith("toàn bộ"):
                    whole += 1
                else:
                    article_level += 1
                    docs_with_article_level.add(doc_id)

    print(f"\n  history files with no entries: {empty_history}")
    print("  expiryProvisions — the article-level repeal ground truth:")
    print(f"    {whole:>6}  whole-document ('Toàn bộ văn bản')")
    print(f"    {article_level:>6}  article/clause-level, across "
          f"{len(docs_with_article_level)} documents")

    # ------------------------------------------------- temporal coherence
    # snapshot(u, t) needs each document placed on the timeline. These are the
    # ways the portal's own metadata makes that impossible, counted in
    # provision nodes rather than documents: one unanchored Luật costs the
    # retrieval space far more than one unanchored Công văn.
    print("\n  temporal coherence — documents that cannot be placed in time:")
    today = dt.date.today()
    broken: dict[str, str] = {}
    for doc_id in raw:
        problem = anchor_problem(store.load("raw", doc_id), today)
        if problem:
            broken[doc_id] = problem

    nodes_total = nodes_broken = 0
    by_reason: collections.Counter[str] = collections.Counter()
    for doc_id in ids["provisions"]:
        count = len(store.load("provisions", doc_id)["nodes"])
        nodes_total += count
        if doc_id in broken:
            nodes_broken += count
            by_reason[broken[doc_id]] += count
    for reason, count in by_reason.most_common():
        print(f"    {count:>8,} nodes  {reason}")
    share = 100 * nodes_broken / nodes_total if nodes_total else 0
    print(f"    {nodes_broken:>8,} of {nodes_total:,} retrievable nodes "
          f"({share:.1f}%) are not anchored in time")
    print(f"    across {len(broken):,} documents")

    delta_log = d / "delta_runs.jsonl"
    runs = len(delta_log.read_text(encoding="utf-8").strip().splitlines()) if (
        delta_log.exists() and delta_log.stat().st_size
    ) else 0
    print(f"\n  delta runs recorded: {runs}"
          + ("  (corpus cannot state 'as of when' until one runs)" if not runs else ""))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Build the queryable SQLite store from `data/` (docs/audit_dataset.md §Stage 6).

`data/` stays the system of record; this file is derived and disposable.

Usage:
    python scripts/pipeline/build_store.py
    python scripts/pipeline/build_store.py --limit 500     # quick smoke run
"""
from __future__ import annotations

import argparse
import time
from pathlib import Path

from legal_crawler.ingest import ingest
from legal_crawler.index import TemporalIndex


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=Path("data"))
    parser.add_argument("--out", type=Path, default=Path("data/temporal.sqlite"))
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--with-subtrees", action="store_true",
                        help="also store derived Khoản/Điểm (backfill T5), for measurement")
    args = parser.parse_args()

    if args.out.exists():
        args.out.unlink()  # derived: always rebuilt whole, never migrated

    started = time.time()
    with TemporalIndex(args.out) as store:
        report = ingest(args.data, store, limit=args.limit, with_subtrees=args.with_subtrees)
        counts = store.counts()

    for key in sorted(report):
        print(f"  {report[key]:>9,}  {key.replace('_', ' ')}")
    print(f"\nstored: {counts} in {time.time() - started:.0f}s -> {args.out}")


if __name__ == "__main__":
    main()

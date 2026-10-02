#!/usr/bin/env python3
"""Build the retrieval index the experiments search (plan phase-5-6, P1).

Derived and rebuildable (ADR 0001 §2): delete the file and run this again.
Stages are recorded, so an interrupted run resumes where it stopped.

Usage:
    python scripts/eval/index_corpus.py
    python scripts/eval/index_corpus.py --counts
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from vilexgraph.framework.corpus import Corpus, build, build_lexical  # noqa: E402

DEFAULT_OUT = Path("data/derived/corpus/index.sqlite")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data", type=Path, default=Path("data"))
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    ap.add_argument("--counts", action="store_true", help="report an existing index and exit")
    ap.add_argument("--lexical", action="store_true",
                    help="build the BM25 index (the slow half; needs the base index first)")
    args = ap.parse_args()

    if args.counts:
        corpus = Corpus(args.out)
        print(json.dumps(corpus.counts(), indent=1, ensure_ascii=False))
        corpus.close()
        return

    started = time.monotonic()
    log = lambda m: print(f"[{time.monotonic() - started:7.1f}s] {m}", flush=True)
    if args.lexical:
        print(json.dumps(build_lexical(args.out, log=log), indent=1))
        print(f"{args.out} ({args.out.stat().st_size / 1e9:.2f} GB)")
        return
    counts = build(args.data, args.out,
                   log=log)
    print(f"\n{args.out} ({args.out.stat().st_size / 1e9:.2f} GB)")
    print(json.dumps(counts, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()

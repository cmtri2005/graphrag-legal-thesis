#!/usr/bin/env python3
"""Stage 5 prep: fetch the Chương/Điều/Khoản/Điểm tree for every crawled doc.

Reads the id list straight off `data/raw/` (that IS the crawled set) and
writes one `data/trees/{id}.json` per document.

Resumable with no checkpoint file: an already-written tree file is the
checkpoint, so re-running only fetches what's missing. Interrupt it freely.

An empty tree (`[]`) is a real answer for documents with no article structure
(Công văn, Bản dịch, 1940s Sắc lệnh...) — it still gets written, so the next
run doesn't keep re-fetching it. See provision_tree.py's docstring.

Documents listed in `data/fetch_failures.txt` are skipped by default. They fail
permanently (HTTP 500 from the site, or a response with no payload row at all),
so a re-run would otherwise spend every request on them — and, worse, trip the
stale-build-id abort below, since a run of nothing but known-bad documents looks
exactly like a rotated NEXT_ACTION_ID. Use `--retry-failures` to try anyway.

Usage:
    python scripts/pipeline/fetch_provision_trees.py
    python scripts/pipeline/fetch_provision_trees.py --limit 50   # try a slice first
    python scripts/pipeline/fetch_provision_trees.py --retry-failures
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

from legal_crawler.provisions.tree import (
    MissingPayloadRowError,
    count_by_level,
    fetch_tree,
    make_session,
)
from legal_crawler.storage.documents import load_permanent_failures

# Consecutive payload-less responses before we stop blaming individual
# documents and conclude NEXT_ACTION_ID itself rotated.
STALE_ABORT_THRESHOLD = 5


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw", type=Path, default=Path("data/raw"))
    parser.add_argument("--out", type=Path, default=Path("data/trees"))
    parser.add_argument("--limit", type=int, default=0, help="stop after N fetches (0 = no limit)")
    parser.add_argument(
        "--failures",
        type=Path,
        default=Path("data/fetch_failures.txt"),
        help="known-permanent failures to skip",
    )
    parser.add_argument("--retry-failures", action="store_true", help="do not skip them")
    parser.add_argument(
        "--min-interval",
        type=float,
        default=0.3,
        help="seconds between requests, matching api_client.py's pacing",
    )
    args = parser.parse_args()

    args.out.mkdir(parents=True, exist_ok=True)
    doc_ids = sorted(p.stem for p in args.raw.glob("*.json"))
    known_bad = set() if args.retry_failures else load_permanent_failures(args.failures, "tree")
    pending = [
        d for d in doc_ids
        if not (args.out / f"{d}.json").exists() and d not in known_bad
    ]

    print(f"crawled documents: {len(doc_ids)}")
    print(f"trees already fetched: {sum(1 for d in doc_ids if (args.out / f'{d}.json').exists())}")
    if known_bad:
        print(f"known-permanent failures skipped: {len(known_bad)} (--retry-failures to include)")
    print(f"to fetch now: {len(pending)}" + (f" (limited to {args.limit})" if args.limit else ""))
    if not pending:
        return

    session = make_session()
    totals: dict[str, int] = {}
    empty = failed = done = 0
    # A rotated build id breaks every document, so it shows up as an unbroken
    # run of these; an isolated server hiccup does not. Only the former should
    # stop the crawl — losing hours of progress to one bad response is worse
    # than the retries this costs.
    consecutive_stale = 0

    for doc_id in pending:
        if args.limit and done >= args.limit:
            break
        try:
            tree = fetch_tree(session, doc_id)
            consecutive_stale = 0
        except MissingPayloadRowError as exc:
            consecutive_stale += 1
            failed += 1
            print(f"  [{doc_id}] no payload row ({consecutive_stale} in a row)")
            if consecutive_stale >= STALE_ABORT_THRESHOLD:
                print(
                    f"\nABORT: {consecutive_stale} documents in a row returned no payload row.\n"
                    "NEXT_ACTION_ID is stale — refresh it (see provisions/tree.py) and re-run;\n"
                    f"the {done} trees already written will be skipped.",
                    file=sys.stderr,
                )
                raise SystemExit(1) from exc
            continue
        except Exception as exc:  # noqa: BLE001 — one bad doc must not kill the run
            failed += 1
            print(f"  [{doc_id}] failed: {type(exc).__name__}: {exc}")
            continue

        (args.out / f"{doc_id}.json").write_text(
            json.dumps(tree, ensure_ascii=False), encoding="utf-8"
        )
        done += 1
        if tree:
            for level, count in count_by_level(tree).items():
                totals[level] = totals.get(level, 0) + count
        else:
            empty += 1

        if done % 200 == 0:
            print(f"  {done}/{len(pending)} fetched | empty so far: {empty} | failed: {failed}")
        time.sleep(args.min_interval)

    print(f"\nfetched: {done} | empty tree: {empty} | failed: {failed}")
    print("nodes collected: " + (", ".join(f"{k}={v}" for k, v in sorted(totals.items())) or "none"))
    if failed:
        print("re-run to retry the failures (already-written trees are skipped)")


if __name__ == "__main__":
    main()

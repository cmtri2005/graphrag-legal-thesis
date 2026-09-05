#!/usr/bin/env python3
"""Backfill `/doc/{id}/history` for every crawled document (Stage 6 input).

Stage 2-3 only ever persisted `/doc/{id}`, so `data/raw/` carries just a
snapshot — `effFrom`/`effTo`/`effStatus` as they stood at crawl time. That is
not enough to build validity intervals:

- 1,054 documents are "Hết hiệu lực một phần" (partly repealed). Their
  `effTo` is null and their `effStatus` says nothing about WHICH articles
  died or when. Only history's `expiryProvisions` does.
- history names the document that caused each transition
  (`sourceDocumentName`), which cross-checks the edges built from
  `referenceType`.

Writes one `data/history/{id}.json` per document, holding the raw payload —
same split as `data/raw/`: scrape now, interpret in Stage 6.

Resumable with no checkpoint file: an existing output file is the checkpoint.
Pacing and retry/backoff come from ApiClient, so there's no sleep here.

Usage:
    python scripts/fetch_histories.py
    python scripts/fetch_histories.py --limit 50
"""
from __future__ import annotations

import argparse
import collections
import json
from pathlib import Path

from legal_crawler.api_client import ApiClient, DocumentNotFoundError
from legal_crawler.store import load_permanent_failures


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw", type=Path, default=Path("data/raw"))
    parser.add_argument("--out", type=Path, default=Path("data/history"))
    parser.add_argument("--limit", type=int, default=0, help="stop after N fetches (0 = no limit)")
    parser.add_argument(
        "--failures",
        type=Path,
        default=Path("data/fetch_failures.txt"),
        help="known-permanent failures to skip",
    )
    parser.add_argument("--retry-failures", action="store_true", help="do not skip them")
    args = parser.parse_args()

    args.out.mkdir(parents=True, exist_ok=True)
    doc_ids = sorted(p.stem for p in args.raw.glob("*.json"))
    known_bad = set() if args.retry_failures else load_permanent_failures(args.failures, "history")
    have = {d for d in doc_ids if (args.out / f"{d}.json").exists()}
    pending = [d for d in doc_ids if d not in have and d not in known_bad]

    print(f"crawled documents: {len(doc_ids)}")
    print(f"histories already fetched: {len(have)}")
    if known_bad:
        print(f"known-permanent failures skipped: {len(known_bad)} (--retry-failures to include)")
    print(f"to fetch now: {len(pending)}" + (f" (limited to {args.limit})" if args.limit else ""))
    if not pending:
        return

    client = ApiClient()
    # The `content` field is an undocumented status code (DATE_BH, DATE_HL,
    # HHL, HHL1P3, CHL...) with no label mapping anywhere — the same problem
    # `referenceType` had. Tally the vocabulary now so Stage 6 knows the full
    # set it must map before it starts interpreting any of them.
    content_codes: collections.Counter[str] = collections.Counter()
    with_provisions = gone = failed = done = 0

    for doc_id in pending:
        if args.limit and done >= args.limit:
            break
        try:
            payload = client.get_history(doc_id)
        except DocumentNotFoundError:
            # 4xx: the document is gone upstream while another still cites it.
            # Permanent, already handled the same way in build_graph.py.
            gone += 1
            continue
        except Exception as exc:  # noqa: BLE001 — one bad doc must not kill the run
            failed += 1
            print(f"  [{doc_id}] failed: {type(exc).__name__}: {exc}")
            continue

        (args.out / f"{doc_id}.json").write_text(
            json.dumps(payload, ensure_ascii=False), encoding="utf-8"
        )
        done += 1
        for row in payload.get("history") or []:
            content_codes[row.get("content") or "?"] += 1
            if row.get("expiryProvisions"):
                with_provisions += 1

        if done % 200 == 0:
            print(f"  {done}/{len(pending)} fetched | gone: {gone} | failed: {failed}")

    print(f"\nfetched: {done} | permanently gone (4xx): {gone} | failed: {failed}")
    print(f"history rows carrying expiryProvisions: {with_provisions}")
    print("status codes seen (Stage 6 must map every one of these):")
    for code, count in content_codes.most_common():
        print(f"  {code:12} {count:>8,}")
    if failed:
        print("re-run to retry the failures (already-written histories are skipped)")


if __name__ == "__main__":
    main()

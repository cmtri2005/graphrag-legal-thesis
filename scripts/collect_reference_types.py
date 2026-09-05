#!/usr/bin/env python3
"""Stage 3b: collect the union of `referenceType` codes seen across a sample
of documents, merging examples into data/reference_type_map.json.

This script only *observes and records* codes/example doc ids — it never
sets `verified` or `label_vi`/`group`. Those must be filled in by hand after
checking the real vbpl.vn UI (see docs/crawling-plan.md §3b).

Usage:
    python scripts/collect_reference_types.py 177815 142881 19419 1 100000 178536
    python scripts/collect_reference_types.py --seeds data/seeds.json --sample 30
"""
from __future__ import annotations

import argparse
import json
import random
import sys
import threading
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from legal_crawler.api_client import ApiClient, ApiClientError
from legal_crawler.reference_types import DEFAULT_MAP_PATH
from legal_crawler.store import read_json

MAX_EXAMPLES_PER_CODE = 5


def ids_from_seeds(seeds_path: Path, sample_size: int | None) -> list[str]:
    """All unique ids across every domain, optionally down-sampled."""
    seeds = read_json(seeds_path)
    unique_ids = sorted({entry["doc_id"] for entries in seeds.values() for entry in entries})
    if sample_size is None or sample_size >= len(unique_ids):
        return unique_ids
    return random.sample(unique_ids, sample_size)


def collect(doc_ids: list[str], concurrency: int) -> dict[int, list[str]]:
    """Returns {referenceType: [doc_id that showed it, ...]}.

    Each worker thread gets its own ApiClient (own connection + own pacing
    clock), so total throughput scales with `concurrency` while every
    individual thread still respects ApiClient's per-request pacing.
    """
    observed: dict[int, list[str]] = defaultdict(list)
    thread_local = threading.local()

    def client_for_this_thread() -> ApiClient:
        if not hasattr(thread_local, "client"):
            thread_local.client = ApiClient()
        return thread_local.client

    def fetch_one(doc_id: str) -> tuple[str, dict | None]:
        try:
            return doc_id, client_for_this_thread().get_document(doc_id)
        except ApiClientError as exc:
            print(f"  skip {doc_id}: {exc}", file=sys.stderr)
            return doc_id, None

    done = 0
    with ThreadPoolExecutor(max_workers=concurrency) as pool:
        futures = [pool.submit(fetch_one, doc_id) for doc_id in doc_ids]
        for future in as_completed(futures):
            doc_id, document = future.result()
            done += 1
            if done % 200 == 0:
                print(f"  ...{done}/{len(doc_ids)} fetched", file=sys.stderr)
            if document is None:
                continue
            for reference in document.get("references") or []:
                ref_type = reference.get("referenceType")
                if ref_type is not None:
                    observed[int(ref_type)].append(doc_id)
    return observed


def merge_into_map_file(observed: dict[int, list[str]], map_path: Path) -> list[int]:
    """Merges observed codes/examples in-place; returns newly-seen codes."""
    data = read_json(map_path) if map_path.exists() else {"codes": {}}
    codes = data.setdefault("codes", {})
    new_codes: list[int] = []

    for ref_type, doc_ids in observed.items():
        key = str(ref_type)
        if key not in codes:
            new_codes.append(ref_type)
            codes[key] = {"label_vi": None, "group": None, "verified": False, "example_doc_ids": []}
        existing = codes[key]["example_doc_ids"]
        for doc_id in doc_ids:
            if doc_id not in existing and len(existing) < MAX_EXAMPLES_PER_CODE:
                existing.append(doc_id)

    map_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return new_codes


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("doc_ids", nargs="*", help="explicit doc ids to sample")
    parser.add_argument("--seeds", type=Path, help="seeds.json to sample ids from")
    parser.add_argument(
        "--sample", type=int, default=None,
        help="down-sample to this many seed ids; omit to use every unique id",
    )
    parser.add_argument("--concurrency", type=int, default=8)
    parser.add_argument("--map-path", type=Path, default=DEFAULT_MAP_PATH)
    args = parser.parse_args()

    doc_ids = list(args.doc_ids)
    if args.seeds:
        doc_ids += ids_from_seeds(args.seeds, args.sample)
    if not doc_ids:
        parser.error("provide doc_ids and/or --seeds")

    print(f"fetching {len(doc_ids)} document(s) with concurrency={args.concurrency}...")
    observed = collect(doc_ids, args.concurrency)
    new_codes = merge_into_map_file(observed, args.map_path)

    print(f"observed codes: {sorted(observed)}")
    if new_codes:
        print(f"NEW codes needing manual label/group review: {sorted(new_codes)}")
    print(f"updated {args.map_path}")


if __name__ == "__main__":
    main()

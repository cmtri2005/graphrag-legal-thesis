#!/usr/bin/env python3
"""Step 1 of the §3b routine, for `history[].content` (docs/plans/completed/2026-09-04-truoc-stage-6.md §A).

Scans every fetched history payload and reports the full set of `content`
values, so the mapping table can be built against reality rather than a
sample. Same role `collect_reference_types.py` plays for edges.

`content` is not always a code: some rows carry a free-text Vietnamese
sentence ("Cập nhật trạng thái hiệu lực từ X sang Y."). Those are reported
separately — they are data, not codes to be mapped, and they happen to be the
cross-check that confirms what several codes mean.

Usage:
    python scripts/explore/collect_status_codes.py
"""
from __future__ import annotations

import argparse
import collections
import re
from pathlib import Path

from legal_crawler.vocab.status_codes import FREE_TEXT_PATTERN, StatusCodeMap
from legal_crawler.storage.documents import read_json


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--history", type=Path, default=Path("data/history"))
    parser.add_argument("--map-path", type=Path, default=None)
    args = parser.parse_args()

    codes: collections.Counter[str] = collections.Counter()
    free_text: collections.Counter[tuple[str, str]] = collections.Counter()
    by_author: collections.Counter[str] = collections.Counter()
    files = 0

    for path in args.history.glob("*.json"):
        files += 1
        for row in read_json(path).get("history") or []:
            content = str(row.get("content") or "")
            by_author[str(row.get("createdBy"))] += 1
            match = re.match(FREE_TEXT_PATTERN, content)
            if match:
                free_text[(match.group(1).strip(), match.group(2).strip())] += 1
            else:
                codes[content] += 1

    print(f"scanned {files:,} history files\n")
    print(f"{len(codes)} distinct codes:")
    for code, count in codes.most_common():
        print(f"  {code:12} {count:>8,}")

    print(f"\n{len(free_text)} distinct free-text transitions (not codes):")
    for (before, after), count in free_text.most_common():
        print(f"  {count:>6,}  {before}  →  {after}")

    print(f"\ncreatedBy: {dict(by_author)}")
    print("  only `Job` rows carry real legal dates — see status_codes.is_legal_date")

    status_map = StatusCodeMap.load() if args.map_path is None else StatusCodeMap.load(args.map_path)
    unmapped = {c for c in codes if not status_map.knows(c)}
    if unmapped:
        print(f"\nUNMAPPED — add to the map before Stage 6 reads them: {sorted(unmapped)}")
        raise SystemExit(1)
    print(f"\nall {len(codes)} codes are present in the mapping table")


if __name__ == "__main__":
    main()

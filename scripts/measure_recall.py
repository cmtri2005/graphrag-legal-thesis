#!/usr/bin/env python3
"""Estimate what the crawl MISSED — the one gap no local check can find.

`verify_pipeline.py` proves the corpus is internally consistent, but it can
only reason about documents we already hold. A document we never discovered
leaves no trace to check against. This measures that blind spot.

Why not the API's keyword search: `/doc/all?keyword=` is a noisy full-text
match over all 172k documents, local ones included ("giao thông" returns
102k hits, among them a circular about school boards). It cannot define
"documents about this domain".

What is used instead: the central-government sitemap, which enumerates the
in-scope universe exactly — the same definition Stage 1 already used. Recall
is then measured in two steps:

  1. How much of the central universe do we hold at all?
  2. Of the central documents we DON'T hold, how many look in-domain under a
     WIDER keyword list than Stage 1's? Those are the documents the narrow
     slug filter missed and genealogy expansion never happened to reach.

Step 2's wider list is deliberately generous: it over-counts rather than
under-counts, so the answer is an upper bound on what we're missing.

Usage:
    python scripts/measure_recall.py
    python scripts/measure_recall.py --samples 40
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from legal_crawler.config import KEYWORDS_BY_DOMAIN  # noqa: E402
from legal_crawler.sitemap import fetch_central_entries, matches_any_keyword  # noqa: E402

# Wider than config.KEYWORDS_BY_DOMAIN on purpose — this is a measuring stick,
# not a crawl filter. Terms a domain expert would accept as in-scope but which
# Stage 1's narrower list does not match (e.g. "gia-dat" is land law, but the
# slug never contains "dat-dai").
WIDER_KEYWORDS: dict[str, tuple[str, ...]] = {
    "dat_dai": (
        "dat-dai", "nha-o", "kinh-doanh-bat-dong-san", "gia-dat", "thu-hoi-dat",
        "giao-dat", "cho-thue-dat", "su-dung-dat", "quy-hoach-su-dung-dat",
        "boi-thuong-ho-tro-tai-dinh-cu", "dang-ky-dat-dai", "do-dac-ban-do",
    ),
    "thue": (
        "thue", "phi-va-le-phi", "hai-quan", "hoa-don", "ke-toan", "kiem-toan",
        "thu-ngan-sach", "quan-ly-thue", "tri-gia-hai-quan", "xuat-nhap-khau",
    ),
    "doanh_nghiep_dau_tu": (
        "doanh-nghiep", "dau-tu", "chung-khoan", "hop-tac-xa", "dang-ky-kinh-doanh",
        "co-phan-hoa", "pha-san", "canh-tranh", "dau-thau", "von-nha-nuoc",
    ),
    "giao_thong": (
        "giao-thong", "duong-bo", "duong-sat", "duong-thuy", "hang-khong",
        "hang-hai", "van-tai", "phuong-tien-giao-thong", "dang-kiem",
        "giay-phep-lai-xe", "cang-bien", "logistics",
    ),
}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw", type=Path, default=Path("data/raw"))
    parser.add_argument("--cache", type=Path, default=Path("data/central_sitemap.json"))
    parser.add_argument("--out", type=Path, default=Path("data/recall_candidates.txt"))
    parser.add_argument("--samples", type=int, default=15, help="example titles to print per domain")
    args = parser.parse_args()

    if args.cache.exists():
        entries = json.loads(args.cache.read_text(encoding="utf-8"))
        print(f"central sitemap: {len(entries):,} entries (cached)")
    else:
        print("fetching central sitemap shards...")
        with requests.Session() as session:
            entries = [
                {"doc_id": e.doc_id, "slug": e.slug} for e in fetch_central_entries(session)
            ]
        args.cache.write_text(json.dumps(entries, ensure_ascii=False), encoding="utf-8")
        print(f"central sitemap: {len(entries):,} entries (cached to {args.cache})")

    held = {p.stem for p in args.raw.glob("*.json")}
    central_ids = {e["doc_id"] for e in entries}

    held_central = held & central_ids
    print(f"\ncorpus: {len(held):,} documents")
    print(f"  of which listed in the central sitemap: {len(held_central):,}")
    print(f"  not in the central sitemap: {len(held - central_ids):,}")
    print(
        f"    (expected — genealogy pulled in documents the sitemap shards don't cover, "
        f"e.g. newer UUID ids)"
    )
    print(f"\ncentral universe: {len(central_ids):,}")
    print(
        f"  HELD    {len(held_central):>7,} ({len(held_central)/len(central_ids)*100:.1f}%)"
    )
    print(
        f"  NOT held {len(central_ids - held):>6,} ({len(central_ids - held)/len(central_ids)*100:.1f}%)"
    )

    missing = [e for e in entries if e["doc_id"] not in held]
    print("\nOf the central documents NOT held, how many look in-domain?")
    print("(wider keyword list than Stage 1 — an upper bound, see module docstring)\n")

    lines: list[str] = []
    total_flagged = 0
    for domain, wide in WIDER_KEYWORDS.items():
        narrow = KEYWORDS_BY_DOMAIN[domain]
        hits = [e for e in missing if matches_any_keyword(e["slug"], wide)]
        # Anything matching the NARROW list should be impossible: those are
        # exactly Stage 1's seeds, and verify_pipeline proves we hold them all.
        narrow_hits = [e for e in hits if matches_any_keyword(e["slug"], narrow)]
        total_flagged += len(hits)
        print(f"  {domain:22} {len(hits):>5,} missed  (narrow-list misses: {len(narrow_hits)})")
        for e in hits[: args.samples]:
            lines.append(f"{domain}\t{e['doc_id']}\t{e['slug']}")

    print(f"\n  TOTAL flagged as plausibly in-domain but missing: {total_flagged:,}")
    print(f"  as a share of the central universe: {total_flagged/len(central_ids)*100:.1f}%")

    args.out.write_text("\n".join(lines), encoding="utf-8")
    print(f"\nsample slugs written to {args.out} — read them before acting on the number:")
    print("a slug matching a wide keyword is not proof the document is in scope.")


if __name__ == "__main__":
    main()

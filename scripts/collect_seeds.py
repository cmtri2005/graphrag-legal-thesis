#!/usr/bin/env python3
"""Stage 1: filter the central-government sitemap into per-domain seed lists.

Usage:
    python scripts/collect_seeds.py [-o data/seeds.json]
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import requests

from legal_crawler.config import KEYWORDS_BY_DOMAIN
from legal_crawler.sitemap import fetch_central_entries, matches_any_keyword


def collect_seeds() -> dict[str, list[dict[str, str]]]:
    seeds: dict[str, list[dict[str, str]]] = {domain: [] for domain in KEYWORDS_BY_DOMAIN}
    with requests.Session() as session:
        for entry in fetch_central_entries(session):
            for domain, keywords in KEYWORDS_BY_DOMAIN.items():
                if matches_any_keyword(entry.slug, keywords):
                    seeds[domain].append(
                        {"doc_id": entry.doc_id, "slug": entry.slug, "lastmod": entry.lastmod}
                    )
    return seeds


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-o", "--output", type=Path, default=Path("data/seeds.json"))
    args = parser.parse_args()

    seeds = collect_seeds()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(seeds, ensure_ascii=False, indent=2), encoding="utf-8")

    for domain, entries in seeds.items():
        print(f"{domain}: {len(entries)} seed(s)")
    print(f"written to {args.output}")


if __name__ == "__main__":
    main()

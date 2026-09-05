#!/usr/bin/env python3
"""Stage 4: field-based filtering pass (docs/crawling-plan.md §3/§4).

Only checks the keyword-seeded documents (data/seeds.json) — documents
pulled in later by genealogy BFS (Stage 2) are kept regardless of their
field/major classification, since they're already legally linked to a
verified seed and aren't at risk of the "matched the keyword, wrong domain"
false positive this stage targets.

Output is a REVIEW CANDIDATE list, not an auto-exclusion — vbpl.vn's own
major/field tags proved too noisy to delete on unattended (see
field_filter_map.json's note). Read the flagged ids before wiring them into
Stage 5/6 as a skip-list.

Usage:
    python scripts/filter_by_field.py --seeds data/seeds.json --raw data/raw
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from legal_crawler.field_filter import DEFAULT_MAP_PATH, FieldFilterMap


def load_seed_ids_by_domain(seeds_path: Path) -> dict[str, str]:
    """doc_id -> domain name (dat_dai / thue / doanh_nghiep_dau_tu)."""
    seeds = json.loads(seeds_path.read_text(encoding="utf-8"))
    doc_id_to_domain: dict[str, str] = {}
    for domain, entries in seeds.items():
        for entry in entries:
            doc_id_to_domain[entry["doc_id"]] = domain
    return doc_id_to_domain


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", type=Path, default=Path("data/seeds.json"))
    parser.add_argument("--raw", type=Path, default=Path("data/raw"))
    parser.add_argument("--map-path", type=Path, default=DEFAULT_MAP_PATH)
    parser.add_argument("--out", type=Path, default=Path("data/field_filter_review.txt"))
    args = parser.parse_args()

    doc_id_to_domain = load_seed_ids_by_domain(args.seeds)
    field_filter = FieldFilterMap.load(args.map_path)

    excluded: list[tuple[str, str, str]] = []  # (doc_id, domain, matched_names)
    missing = 0
    for doc_id, domain in doc_id_to_domain.items():
        raw_path = args.raw / f"{doc_id}.json"
        if not raw_path.exists():
            missing += 1
            continue
        document = json.loads(raw_path.read_text(encoding="utf-8"))
        verdict = field_filter.classify(document)
        if verdict.is_foreign:
            excluded.append((doc_id, domain, ", ".join(verdict.matched_names)))

    args.out.write_text(
        "\n".join(f"{doc_id}\t{domain}\t{names}" for doc_id, domain, names in excluded),
        encoding="utf-8",
    )

    print(f"seed documents checked: {len(doc_id_to_domain) - missing} ({missing} not yet crawled)")
    print(f"flagged for human review (NOT auto-excluded): {len(excluded)} -> {args.out}")
    by_domain: dict[str, int] = {}
    for _, domain, _ in excluded:
        by_domain[domain] = by_domain.get(domain, 0) + 1
    for domain, count in sorted(by_domain.items()):
        print(f"  {domain}: {count}")


if __name__ == "__main__":
    main()

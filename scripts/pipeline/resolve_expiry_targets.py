#!/usr/bin/env python3
"""Resolve `history[].expiryProvisions` onto provision ids via `TargetResolver`.

The portal publishes *which* provision stopped applying ("Khoản 1, Điều 3,
Chương I") but not *when* nor *by whom* — see docs/audit_dataset.md §5. This
script only parses that string into a locator; the matching is
`extraction.target_resolver`, so the rules and outcome codes are the same ones
L2 extraction will use, and the 31k real strings here are its test bed.

Reads the index built by `build_store.py`. Writes `data/expiry_targets.jsonl`.

Usage:
    python scripts/pipeline/resolve_expiry_targets.py
"""
from __future__ import annotations

import argparse
import collections
import json
import re
from pathlib import Path

from legal_crawler.extraction import (
    ProvisionLocator,
    ProvisionReferencePart,
    TargetReference,
    TargetResolver,
    TargetScope,
)
from legal_crawler.index import TemporalIndex
from legal_crawler.storage.documents import DocumentStore
from legal_crawler.temporal import ProvisionLevel

LEVELS = {
    "phần": ProvisionLevel.PART,
    "chương": ProvisionLevel.CHAPTER,
    "mục": ProvisionLevel.SECTION,
    "tiểu mục": ProvisionLevel.SUBSECTION,
    "điều": ProvisionLevel.ARTICLE,
    "khoản": ProvisionLevel.CLAUSE,
    "điểm": ProvisionLevel.POINT,
}
COMPONENT = re.compile(
    r"(tiểu mục|phần|chương|mục|điều|khoản|điểm)\s*((?:thứ\s+[^\s,]+)|[^\s,]*)", re.IGNORECASE
)


def locator_for(text: str) -> ProvisionLocator | None:
    """"Khoản 1, Điều 3, Chương I" -> Chương I / Điều 3 / Khoản 1 (outermost first)."""
    found = [(level.lower(), ordinal.strip(".:")) for level, ordinal in COMPONENT.findall(text)]
    if not found or any(not ordinal for _, ordinal in found):
        return None  # e.g. bare "Mục, Phần": says a section lapsed, not which
    return ProvisionLocator(
        tuple(ProvisionReferencePart(LEVELS[level], ordinal) for level, ordinal in reversed(found))
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=Path("data"))
    parser.add_argument("--index", type=Path, default=Path("data/temporal.sqlite"))
    args = parser.parse_args()

    source = DocumentStore(args.data)
    index = TemporalIndex(args.index)
    resolver = TargetResolver(index)

    codes: collections.Counter[str] = collections.Counter()
    distinct: dict[tuple[str, str], str] = {}
    out = args.data / "expiry_targets.jsonl"
    with out.open("w", encoding="utf-8") as f:
        for doc_id in sorted(source.ids("history")):
            entries = source.load("history", doc_id).get("history") or []
            for entry in entries:
                for text in entry.get("expiryProvisions") or []:
                    text = text.strip()
                    row = {"doc_id": doc_id, "raw": text,
                           "recorded_at": entry.get("createdDate"), "status": entry.get("content")}
                    if text.casefold().startswith("toàn bộ"):
                        code, provision_ids = "whole_document", []
                    elif not index.exists(doc_id):
                        code, provision_ids = "document_not_indexed", []
                    elif (locator := locator_for(text)) is None:
                        code, provision_ids = "unparsed", []
                    else:
                        reference = TargetReference(f"{doc_id}:{text}", text, TargetScope.EXACT,
                                                    locator=locator)
                        result = resolver.resolve(reference, (doc_id,))
                        code = result.code.value
                        provision_ids = list(result.target.candidate_provision_ids)
                    codes[code] += 1
                    distinct[(doc_id, text)] = code
                    f.write(json.dumps(row | {"code": code, "provision_ids": provision_ids},
                                       ensure_ascii=False) + "\n")

    total = sum(codes.values())
    print(f"wrote {total:,} rows to {out}\n")
    for code, count in codes.most_common():
        print(f"  {count:>7,} ({100 * count / total:5.1f}%)  {code}")
    provision_level = {k: v for k, v in distinct.items() if v != "whole_document"}
    resolved = sum(1 for v in provision_level.values() if v.startswith("resolved"))
    print(f"\n  distinct provision-level pairs: {len(provision_level):,} — "
          f"{resolved:,} resolved ({100 * resolved / max(len(provision_level), 1):.1f}%)")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Apply the human review decision on data/field_filter_review.txt.

data/field_filter_review.txt lists Stage 4 candidates; a human (see chat
history for the 2026-08-25 review) decided which of those are genuinely
off-topic. This writes the confirmed exclusions to data/excluded_ids.txt —
the file Stage 5/6 should actually skip on — while everything else on the
candidate list is kept (the tag that flagged it was noise, not a real
domain mismatch; see field_filter_map.json's note).

Usage:
    python scripts/apply_field_review.py
"""
from __future__ import annotations

from pathlib import Path

REVIEW_PATH = Path("data/field_filter_review.txt")
OUT_PATH = Path("data/excluded_ids.txt")

# docNum -> reason, decided by hand against the actual document content
# (not just the misleading major/field tag) on 2026-08-25.
CONFIRMED_EXCLUSIONS = {
    "14/2014/TT-BTTTT": "chuẩn kỹ thuật truyền hình cáp, không liên quan thuế",
    "02/2020/TT-BCA": "quản lý đầu tư xây dựng nội bộ Bộ Công an, không phải luật đầu tư chung",
    "66.10/2025/NQ-CP": "hạ tầng dùng chung cho quốc phòng/an ninh, không phải luật doanh nghiệp",
    "103/2026/TT-BCA": "đầu tư xây dựng công trình an ninh nội bộ",
    "102/2026/TT/BCA": "đầu tư, mua sắm nội bộ Công an nhân dân",
    "35/2026/TT-BCA": "quyết toán đầu tư nội bộ Công an nhân dân",
    "10/2022/TT-BYT": "chương trình hỗ trợ dược liệu dân tộc thiểu số, không phải luật đầu tư",
    "34/2015/TT-BTTTT": "chuẩn kỹ thuật thiết bị radio hàng hải, ít giá trị temporal-legal",
}


def main() -> None:
    import json

    lines = REVIEW_PATH.read_text(encoding="utf-8").splitlines()
    excluded = []
    for line in lines:
        doc_id, domain, matched = line.split("\t")
        doc_num = json.loads(Path(f"data/raw/{doc_id}.json").read_text(encoding="utf-8")).get(
            "docNum", ""
        )
        if doc_num in CONFIRMED_EXCLUSIONS:
            excluded.append(f"{doc_id}\t{domain}\t{CONFIRMED_EXCLUSIONS[doc_num]}")

    OUT_PATH.write_text("\n".join(excluded), encoding="utf-8")
    print(f"{len(excluded)} document(s) confirmed excluded -> {OUT_PATH}")
    print(f"{len(lines) - len(excluded)} candidate(s) kept (flagged tag was noise, not a real mismatch)")


if __name__ == "__main__":
    main()

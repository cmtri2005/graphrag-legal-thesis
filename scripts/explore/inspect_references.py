#!/usr/bin/env python3
"""Human-verification helper for Stage 3b (docs/crawling-plan.md §3b).

Prints, for one document, its browser URL plus every reference grouped by
referenceType code with the *title* of the other document — so you can just
open the page, Ctrl+F for that title, and read off which heading/tab it sits
under. No DevTools/JSON reading required.

Usage:
    python scripts/explore/inspect_references.py 177815
"""
from __future__ import annotations

import sys
from collections import defaultdict
from pathlib import Path

from legal_crawler.sources.api_client import ApiClient

DETAIL_URL = "https://vbpl.vn/van-ban/chi-tiet/van-ban--{doc_id}"


def main() -> None:
    if len(sys.argv) < 2:
        sys.exit("usage: inspect_references.py DOC_ID")
    doc_id = sys.argv[1]

    client = ApiClient()
    document = client.get_document(doc_id)

    print(f"{document.get('docNum')} — {document.get('title')}")
    print(f"Mở trang này trên trình duyệt: {DETAIL_URL.format(doc_id=doc_id)}")
    print()

    by_type: dict[int, set[str]] = defaultdict(set)
    for reference in document.get("references") or []:
        ref_type = reference.get("referenceType")
        target = reference.get("targetDocument") or {}
        title = target.get("title") or target.get("docNum") or "(không có tiêu đề)"
        by_type[ref_type].add(title)

    if not by_type:
        print("Văn bản này không có references[] — thử id khác.")
        return

    for ref_type in sorted(by_type):
        titles = sorted(by_type[ref_type])
        print(f"--- referenceType = {ref_type} ({len(titles)} văn bản khác nhau) ---")
        for title in titles:
            print(f"  Ctrl+F tìm: {title}")
        print()

    print("Cách dùng: mở URL ở trên, với mỗi khối referenceType, Ctrl+F từng")
    print("tiêu đề vừa in, xem nó nằm dưới heading/tab nào trên trang —")
    print("đó chính là label_vi cần điền vào data/reference_type_map.json.")


if __name__ == "__main__":
    main()

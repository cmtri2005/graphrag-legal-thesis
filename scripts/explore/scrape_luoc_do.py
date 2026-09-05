#!/usr/bin/env python3
"""One-off helper (not part of the crawl pipeline) to read the real "Lược đồ"
relation panel for a document via a headless browser, for building the
ground-truth referenceType mapping (docs/crawling-plan.md §3b).

Requires: pip install playwright && playwright install chromium

Usage:
    python scripts/explore/scrape_luoc_do.py 177815 19419 118930
"""
from __future__ import annotations

import sys

from playwright.sync_api import sync_playwright

DETAIL_URL = "https://vbpl.vn/van-ban/chi-tiet/van-ban--{doc_id}"
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
)


def dump_luoc_do(doc_id: str) -> None:
    with sync_playwright() as p:
        browser = p.chromium.launch(args=["--disable-blink-features=AutomationControlled"])
        context = browser.new_context(user_agent=USER_AGENT, locale="vi-VN")
        page = context.new_page()
        # The site's WAF fingerprints the default headless webdriver flag.
        page.add_init_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        )
        page.goto(DETAIL_URL.format(doc_id=doc_id), wait_until="domcontentloaded", timeout=30000)
        page.wait_for_selector("#rc-tabs-0-tab-luoc-do", timeout=30000)
        page.click("#rc-tabs-0-tab-luoc-do")
        page.wait_for_timeout(2000)
        print(f"\n===== doc_id={doc_id} =====")
        print(page.locator("#rc-tabs-0-panel-luoc-do").inner_text())
        browser.close()


if __name__ == "__main__":
    for doc_id in sys.argv[1:]:
        dump_luoc_do(doc_id)

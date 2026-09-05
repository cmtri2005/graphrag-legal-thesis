import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from legal_crawler.sources.sitemap import matches_any_keyword, parse_document_entries, parse_shard_urls

SHARD_INDEX_XML = """<?xml version="1.0" encoding="UTF-8"?>
<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <sitemap><loc>https://vbpl.vn/sitemap/1.xml</loc></sitemap>
  <sitemap><loc>https://vbpl.vn/sitemap/2.xml</loc></sitemap>
</sitemapindex>
"""

SHARD_XML = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url><loc>https://vbpl.vn/van-ban/chi-tiet/luat-dat-dai-so-31-2024-qh15--177815</loc><lastmod>2026-08-24</lastmod></url>
  <url><loc>https://vbpl.vn/van-ban/chi-tiet/nghi-dinh-so-316-2026-nd-cp--d35ac6b0-96fd-11f1-8653-7f716ce825da</loc><lastmod>2026-08-01</lastmod></url>
  <url><loc>https://vbpl.vn/gioi-thieu</loc><lastmod>2026-01-01</lastmod></url>
</urlset>
"""


def test_parse_shard_urls():
    assert parse_shard_urls(SHARD_INDEX_XML) == [
        "https://vbpl.vn/sitemap/1.xml",
        "https://vbpl.vn/sitemap/2.xml",
    ]


def test_parse_document_entries_splits_id_on_last_double_dash():
    entries = parse_document_entries(SHARD_XML)
    assert len(entries) == 2  # non-detail /gioi-thieu url is skipped

    law = entries[0]
    assert law.doc_id == "177815"
    assert law.slug == "luat-dat-dai-so-31-2024-qh15"
    assert law.lastmod == "2026-08-24"

    decree = entries[1]
    assert decree.doc_id == "d35ac6b0-96fd-11f1-8653-7f716ce825da"
    assert decree.slug == "nghi-dinh-so-316-2026-nd-cp"


def test_matches_any_keyword_is_whole_word_not_substring():
    assert matches_any_keyword("luat-dat-dai-so-31-2024-qh15", ["dat-dai"])
    assert matches_any_keyword("nghi-quyet-ve-thue-thu-nhap", ["thue"])
    # "nha-nuoc" must not match keyword "nha-o" despite sharing "nha"
    assert not matches_any_keyword("luat-to-chuc-nha-nuoc", ["nha-o"])


def test_matches_any_keyword_multi_word():
    assert matches_any_keyword("luat-kinh-doanh-bat-dong-san-2023", ["kinh-doanh-bat-dong-san"])

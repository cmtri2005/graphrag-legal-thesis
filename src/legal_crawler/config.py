"""Static configuration: keyword seeds and reference-type edge groups.

Values here are the ones agreed in docs/crawling-plan.md. Keep this the
single place these lists live so scripts don't hard-code them separately.
"""
from __future__ import annotations

API_BASE = "https://vbpl-bientap-gateway.moj.gov.vn/api"
SITEMAP_INDEX_URL = "https://vbpl.vn/sitemap.xml"
REQUEST_HEADERS = {
    "Referer": "https://vbpl.vn/",
    # requests' default UA is blocked by the site's WAF (403); anything
    # browser-shaped is accepted.
    "User-Agent": "Mozilla/5.0 (compatible; legal-crawler/0.1)",
}

# Slug keywords used for Stage 1 coarse filtering of the central-government
# sitemap shards. Matched against the slug portion of the URL only, as whole
# dash-separated words (see sitemap.matches_any_keyword) — so a keyword also
# matches any longer phrase containing it: "su-dung-dat" covers
# "quy-hoach-su-dung-dat" and "ke-hoach-su-dung-dat" already. Don't add the
# longer forms, they are dead weight.
#
# The second line of each domain was added 2026-09-04 after measuring recall
# (docs/crawling-plan.md §5e): these phrasings are the common ones in their
# field and the original list missed them outright — "dat-dai" never matches
# "sử dụng đất", which is how most land-law titles are actually worded.
KEYWORDS_BY_DOMAIN: dict[str, tuple[str, ...]] = {
    "dat_dai": (
        "dat-dai", "nha-o", "kinh-doanh-bat-dong-san",
        "su-dung-dat", "giao-dat",
    ),
    "thue": (
        "thue", "phi-va-le-phi", "hai-quan",
        "hoa-don",
    ),
    "doanh_nghiep_dau_tu": (
        "doanh-nghiep", "dau-tu", "chung-khoan", "hop-tac-xa",
        "co-phan-hoa", "dang-ky-kinh-doanh",
    ),
    "giao_thong": (
        "giao-thong", "duong-bo", "duong-sat", "duong-thuy",
        "hang-khong", "hang-hai", "van-tai",
        "dang-kiem", "cang-bien",
    ),
}

# Central-government sitemap shards are index 1..12 (see docs/crawling-plan.md
# section 1); shards after that are local-government and out of scope.
CENTRAL_SHARD_RANGE = range(1, 13)

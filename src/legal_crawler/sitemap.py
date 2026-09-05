"""Sitemap discovery for vbpl.vn (Stage 1: seed discovery).

The site's search API requires an internal token (401 for anonymous callers),
so the sitemap is the only anonymous way to enumerate document ids. Parsing
is kept separate from fetching so it can be unit-tested with static XML.
"""
from __future__ import annotations

from collections.abc import Iterable, Iterator
from xml.etree import ElementTree as ET

import requests

from .config import CENTRAL_SHARD_RANGE, REQUEST_HEADERS, SITEMAP_INDEX_URL
from .models import SitemapEntry

_NS = "{http://www.sitemaps.org/schemas/sitemap/0.9}"
_DETAIL_PATH = "/van-ban/chi-tiet/"


def parse_shard_urls(index_xml: str) -> list[str]:
    """Extract shard <loc> URLs from the top-level sitemap.xml."""
    root = ET.fromstring(index_xml)
    return [loc.text.strip() for loc in root.iter(f"{_NS}loc") if loc.text]


def parse_document_entries(shard_xml: str) -> list[SitemapEntry]:
    """Extract document entries from one sitemap shard.

    Detail URLs look like `.../van-ban/chi-tiet/{slug}--{id}`; the id is
    whatever follows the *last* "--" separator (slugs use single dashes,
    ids may themselves contain dashes when they're a UUID).
    """
    root = ET.fromstring(shard_xml)
    entries: list[SitemapEntry] = []
    for url_el in root.iter(f"{_NS}url"):
        loc = url_el.findtext(f"{_NS}loc")
        lastmod = url_el.findtext(f"{_NS}lastmod") or ""
        if not loc or _DETAIL_PATH not in loc:
            continue
        rest = loc.split(_DETAIL_PATH, 1)[1]
        if "--" not in rest:
            continue
        slug, doc_id = rest.rsplit("--", 1)
        entries.append(SitemapEntry(doc_id=doc_id, slug=slug, lastmod=lastmod))
    return entries


def matches_any_keyword(slug: str, keywords: Iterable[str]) -> bool:
    """Whole-token match against a slug's dash-separated words.

    A plain substring check would let "thue" match "phuong-thuc-...", so we
    match against tokenized runs of the keyword's own words instead.
    """
    words = slug.split("-")
    for keyword in keywords:
        kw_words = keyword.split("-")
        n = len(kw_words)
        if any(words[i : i + n] == kw_words for i in range(len(words) - n + 1)):
            return True
    return False


def fetch_central_entries(session: requests.Session) -> Iterator[SitemapEntry]:
    """Fetch every document entry from the central-government shards."""
    shard_urls = parse_shard_urls(_get_text(session, SITEMAP_INDEX_URL))
    for shard_index in CENTRAL_SHARD_RANGE:
        shard_url = f"https://vbpl.vn/sitemap/{shard_index}.xml"
        if shard_url not in shard_urls:
            continue
        yield from parse_document_entries(_get_text(session, shard_url))


def _get_text(session: requests.Session, url: str) -> str:
    response = session.get(url, headers=REQUEST_HEADERS, timeout=30)
    response.raise_for_status()
    return response.text

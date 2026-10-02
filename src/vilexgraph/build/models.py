"""Plain data containers shared across the crawler.

Kept dependency-free (no requests, no I/O) so they can be imported and
unit-tested without a network stack.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SitemapEntry:
    """One <url> row from a vbpl.vn sitemap shard."""

    doc_id: str
    slug: str
    lastmod: str


@dataclass(frozen=True, slots=True)
class Edge:
    """A directed reference edge discovered while expanding the graph."""

    source_id: str
    target_id: str
    reference_type: int

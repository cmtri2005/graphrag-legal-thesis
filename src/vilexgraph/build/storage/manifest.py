"""Local crawl manifest for delta/incremental crawling (docs/crawling-plan.md §6b).

SQLite is the whole "database" here — one file, no server, upsert semantics
by doc_id. Good enough at this scale; revisit only if concurrent writers or
multi-machine crawling become a real need.
"""
from __future__ import annotations

import sqlite3
from collections.abc import Iterable
from contextlib import closing
from dataclasses import dataclass
from pathlib import Path

_SCHEMA = """
CREATE TABLE IF NOT EXISTS documents (
    doc_id TEXT PRIMARY KEY,
    sitemap_lastmod TEXT,
    content_hash TEXT,
    eff_status TEXT,
    eff_to TEXT,
    last_crawled_at TEXT,
    removed_at TEXT
);
"""


@dataclass(frozen=True, slots=True)
class ManifestRecord:
    doc_id: str
    sitemap_lastmod: str | None
    content_hash: str | None
    eff_status: str | None
    eff_to: str | None
    last_crawled_at: str | None
    removed_at: str | None


class CrawlManifest:
    """Tracks what has been crawled and when, to support delta re-runs."""

    def __init__(self, db_path: Path) -> None:
        self._db_path = db_path
        with closing(self._connect()) as conn:
            conn.execute(_SCHEMA)
            conn.commit()

    def get(self, doc_id: str) -> ManifestRecord | None:
        with closing(self._connect()) as conn:
            row = conn.execute(
                "SELECT * FROM documents WHERE doc_id = ?", (doc_id,)
            ).fetchone()
        return ManifestRecord(*row) if row else None

    def needs_refetch(self, doc_id: str, sitemap_lastmod: str) -> bool:
        """True for a new id or one whose sitemap lastmod has advanced."""
        record = self.get(doc_id)
        return record is None or record.sitemap_lastmod != sitemap_lastmod

    def active_doc_ids(self) -> list[str]:
        """Docs last seen as 'còn hiệu lực' — re-check these every delta run
        regardless of lastmod, since effect status can flip on a schedule
        with no sitemap edit (docs/crawling-plan.md §6b point 3)."""
        with closing(self._connect()) as conn:
            rows = conn.execute(
                "SELECT doc_id FROM documents "
                "WHERE removed_at IS NULL AND eff_status = 'Còn hiệu lực'"
            ).fetchall()
        return [row[0] for row in rows]

    def freshness(self) -> dict[str, tuple[str, str]]:
        """doc_id -> (sitemap_lastmod, last_crawled_at), in one pass.

        Delta runs compare both fields for every document at once, so reading
        them row by row through `get` would be tens of thousands of queries.
        """
        with closing(self._connect()) as conn:
            return {
                row[0]: (row[1] or "", row[2] or "")
                for row in conn.execute(
                    "SELECT doc_id, sitemap_lastmod, last_crawled_at FROM documents"
                )
            }

    def expired_but_still_active(self, today: str, *, all_active: bool = False) -> list[str]:
        """Documents the manifest still calls 'Còn hiệu lực' past their `effTo`.

        Effect status is the one field that changes with nobody editing the
        page, so the sitemap's `lastmod` cannot detect it — a law reaching its
        own expiry date leaves no trace to compare against. `all_active` widens
        this to every active document, for an occasional deep pass.
        """
        active = "removed_at IS NULL AND eff_status = 'Còn hiệu lực'"
        with closing(self._connect()) as conn:
            if all_active:
                rows = conn.execute(f"SELECT doc_id FROM documents WHERE {active}").fetchall()
            else:
                rows = conn.execute(
                    f"SELECT doc_id FROM documents WHERE {active} "
                    "AND eff_to IS NOT NULL AND eff_to != '' AND substr(eff_to, 1, 10) <= ?",
                    (today,),
                ).fetchall()
        return [row[0] for row in rows]

    def row_counts(self) -> tuple[int, int]:
        """(rows, distinct doc_ids) — equal unless the upsert key has broken."""
        with closing(self._connect()) as conn:
            return conn.execute(
                "SELECT COUNT(*), COUNT(DISTINCT doc_id) FROM documents"
            ).fetchone()

    def removed_ids(self) -> set[str]:
        """Documents known to be gone — accounted for, not merely absent."""
        with closing(self._connect()) as conn:
            return {
                row[0]
                for row in conn.execute("SELECT doc_id FROM documents WHERE removed_at IS NOT NULL")
            }

    def upsert(
        self,
        doc_id: str,
        *,
        sitemap_lastmod: str,
        content_hash: str,
        eff_status: str | None,
        eff_to: str | None,
        crawled_at: str,
    ) -> None:
        with closing(self._connect()) as conn:
            conn.execute(
                """
                INSERT INTO documents
                    (doc_id, sitemap_lastmod, content_hash, eff_status, eff_to,
                     last_crawled_at, removed_at)
                VALUES (?, ?, ?, ?, ?, ?, NULL)
                ON CONFLICT(doc_id) DO UPDATE SET
                    sitemap_lastmod = excluded.sitemap_lastmod,
                    content_hash = excluded.content_hash,
                    eff_status = excluded.eff_status,
                    eff_to = excluded.eff_to,
                    last_crawled_at = excluded.last_crawled_at,
                    removed_at = NULL
                """,
                (doc_id, sitemap_lastmod, content_hash, eff_status, eff_to, crawled_at),
            )
            conn.commit()

    def mark_removed(self, doc_ids: Iterable[str], removed_at: str) -> None:
        with closing(self._connect()) as conn:
            conn.executemany(
                "UPDATE documents SET removed_at = ? WHERE doc_id = ? AND removed_at IS NULL",
                [(removed_at, doc_id) for doc_id in doc_ids],
            )
            conn.commit()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self._db_path)

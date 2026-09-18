"""SQLite store for the temporal legal graph.

`data/` stays the system of record: this file is a derived index, safe to
delete and rebuild from the crawl at any time. SQLite rather than a graph
service because the queries the thesis actually runs — "which version of this
provision was in force at t", "what hangs under this node" — are an indexed
lookup and a prefix scan, and stdlib already ships the engine.

Provision ancestry is stored as a materialized path (`/root/child/leaf`), so
`descendants_of` is one indexed range scan on `path` instead of a recursive
query. That is the whole reason a graph database is not needed here.

Open with `TemporalIndex(":memory:")` in tests; the schema is identical.
"""
from __future__ import annotations

import sqlite3
from collections.abc import Iterable, Iterator
from datetime import date
from pathlib import Path

from .temporal import (
    LegalDocument,
    Provision,
    ProvisionLevel,
    ProvisionVersion,
    TemporalInterval,
)

SCHEMA = """
CREATE TABLE IF NOT EXISTS documents (
    id             TEXT PRIMARY KEY,
    number         TEXT NOT NULL,
    title          TEXT NOT NULL,
    issued_on      TEXT,
    effective_from TEXT,
    effective_to   TEXT,
    issuer         TEXT,
    rank           TEXT,
    source_url     TEXT,
    raw_status_code TEXT
);

CREATE TABLE IF NOT EXISTS provisions (
    id          TEXT PRIMARY KEY,
    document_id TEXT NOT NULL,
    level       TEXT NOT NULL,
    title       TEXT NOT NULL,
    parent_id   TEXT,
    order_index INTEGER,
    path        TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS provisions_document ON provisions(document_id, order_index);
CREATE INDEX IF NOT EXISTS provisions_path ON provisions(path);

CREATE TABLE IF NOT EXISTS versions (
    id            TEXT PRIMARY KEY,
    provision_id  TEXT NOT NULL,
    ordinal       INTEGER NOT NULL,
    text          TEXT NOT NULL,
    valid_from    TEXT,
    valid_to      TEXT
);
CREATE INDEX IF NOT EXISTS versions_provision ON versions(provision_id, ordinal);
"""


def _as_date(value: str | None) -> date | None:
    return date.fromisoformat(value) if value else None


class TemporalIndex:
    """Everything the temporal graph needs to answer a point-in-time query."""

    def __init__(self, path: str | Path = ":memory:") -> None:
        self._db = sqlite3.connect(path)
        self._db.row_factory = sqlite3.Row
        self._db.executescript(SCHEMA)

    def close(self) -> None:
        self._db.close()

    def __enter__(self) -> "TemporalIndex":
        return self

    def __exit__(self, *exc: object) -> None:
        self._db.commit()
        self.close()

    # ------------------------------------------------------------------ write

    def put_documents(self, documents: Iterable[LegalDocument]) -> int:
        rows = [
            (
                d.id, d.number, d.title,
                d.issued_on.isoformat() if d.issued_on else None,
                d.effective_from.isoformat() if d.effective_from else None,
                d.effective_to.isoformat() if d.effective_to else None,
                d.issuer, d.rank, d.source_url, d.raw_status_code,
            )
            for d in documents
        ]
        self._db.executemany(
            "INSERT OR REPLACE INTO documents VALUES (?,?,?,?,?,?,?,?,?,?)", rows
        )
        return len(rows)

    def put_provisions(self, provisions: Iterable[Provision]) -> int:
        """Insert provisions parents-first, materializing each node's path.

        Paths are resolved from the batch itself rather than by querying back
        per row: a depth-first walk of a crawled tree already yields parents
        before children, and 1.26M round-trips is the difference between
        seconds and an hour.
        """
        paths: dict[str, str] = {}
        rows = []
        for provision in provisions:
            parent_path = ""
            if provision.parent_id:
                parent_path = paths.get(provision.parent_id) or ""
                if not parent_path:
                    row = self._db.execute(
                        "SELECT path FROM provisions WHERE id = ?",
                        (provision.parent_id,),
                    ).fetchone()
                    parent_path = row["path"] if row else ""
            path = f"{parent_path}/{provision.id}"
            paths[provision.id] = path
            rows.append(
                (
                    provision.id, provision.document_id, provision.level.value,
                    provision.title, provision.parent_id, provision.order_index, path,
                )
            )
        self._db.executemany(
            "INSERT OR REPLACE INTO provisions VALUES (?,?,?,?,?,?,?)", rows
        )
        return len(rows)

    def put_versions(self, versions: Iterable[ProvisionVersion]) -> int:
        rows = [
            (
                v.id, v.provision_id, v.ordinal, v.text,
                v.validity.start.isoformat() if v.validity else None,
                v.validity.end.isoformat() if v.validity and v.validity.end else None,
            )
            for v in versions
        ]
        self._db.executemany("INSERT OR REPLACE INTO versions VALUES (?,?,?,?,?,?)", rows)
        return len(rows)

    def commit(self) -> None:
        self._db.commit()

    # ------------------------------------------------------------------- read

    def exists(self, document_id: str) -> bool:
        return (
            self._db.execute(
                "SELECT 1 FROM documents WHERE id = ?", (document_id,)
            ).fetchone()
            is not None
        )

    def document(self, document_id: str) -> LegalDocument | None:
        row = self._db.execute(
            "SELECT * FROM documents WHERE id = ?", (document_id,)
        ).fetchone()
        if row is None:
            return None
        return LegalDocument(
            id=row["id"], number=row["number"], title=row["title"],
            issued_on=_as_date(row["issued_on"]),
            effective_from=_as_date(row["effective_from"]),
            effective_to=_as_date(row["effective_to"]),
            issuer=row["issuer"], rank=row["rank"], source_url=row["source_url"],
            raw_status_code=row["raw_status_code"],
        )

    def documents(self) -> Iterator[LegalDocument]:
        """Every document, for callers that need to build their own lookup."""
        rows = self._db.execute("SELECT * FROM documents")
        for row in rows:
            yield LegalDocument(
                id=row["id"], number=row["number"], title=row["title"],
                issued_on=_as_date(row["issued_on"]),
                effective_from=_as_date(row["effective_from"]),
                effective_to=_as_date(row["effective_to"]),
                issuer=row["issuer"], rank=row["rank"], source_url=row["source_url"],
                raw_status_code=row["raw_status_code"],
            )

    def document_order(self, document_id: str) -> tuple[Provision, ...]:
        """Every provision of a document, in the order the source declared."""
        rows = self._db.execute(
            "SELECT * FROM provisions WHERE document_id = ? "
            "ORDER BY order_index IS NULL, order_index, path",
            (document_id,),
        )
        return tuple(_provision(row) for row in rows)

    def descendants_of(self, provision_id: str) -> tuple[Provision, ...]:
        row = self._db.execute(
            "SELECT path FROM provisions WHERE id = ?", (provision_id,)
        ).fetchone()
        if row is None:
            return ()
        # A range, not LIKE: SQLite's LIKE is case-insensitive, so it cannot
        # use the BINARY path index and scans all ~1.7M rows on every call.
        # "0" is the character right after "/", so the range is exactly "path/…".
        rows = self._db.execute(
            "SELECT * FROM provisions WHERE path >= ? AND path < ? ORDER BY path",
            (f"{row['path']}/", f"{row['path']}0"),
        )
        return tuple(_provision(r) for r in rows)

    def version_at(self, provision_id: str, at: date) -> ProvisionVersion | None:
        """The version in force at `at`, per the half-open interval [from, to).

        A version with no `valid_from` is undated — 4.4% of the corpus, where
        the portal never published an effective date — and is deliberately not
        returned: a point-in-time answer must not rest on a guessed date.
        """
        row = self._db.execute(
            "SELECT * FROM versions WHERE provision_id = ? AND valid_from IS NOT NULL "
            "AND valid_from <= ? AND (valid_to IS NULL OR valid_to > ?) "
            "ORDER BY ordinal DESC LIMIT 1",
            (provision_id, at.isoformat(), at.isoformat()),
        ).fetchone()
        return _version(row) if row else None

    def versions_of(self, provision_id: str) -> tuple[ProvisionVersion, ...]:
        rows = self._db.execute(
            "SELECT * FROM versions WHERE provision_id = ? ORDER BY ordinal",
            (provision_id,),
        )
        return tuple(_version(row) for row in rows)

    def counts(self) -> dict[str, int]:
        return {
            table: self._db.execute(f"SELECT count(*) FROM {table}").fetchone()[0]
            for table in ("documents", "provisions", "versions")
        }


def _provision(row: sqlite3.Row) -> Provision:
    return Provision(
        id=row["id"], document_id=row["document_id"],
        level=ProvisionLevel(row["level"]), title=row["title"],
        parent_id=row["parent_id"], order_index=row["order_index"],
    )


def _version(row: sqlite3.Row) -> ProvisionVersion:
    return ProvisionVersion(
        id=row["id"], provision_id=row["provision_id"], ordinal=row["ordinal"],
        text=row["text"],
        validity=(
            TemporalInterval(_as_date(row["valid_from"]), _as_date(row["valid_to"]))
            if row["valid_from"]
            else None
        ),
    )

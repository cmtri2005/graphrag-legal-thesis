"""The retrieval index every system in the experiments searches (plan phase-5-6, P1).

One SQLite file derived from `data/derived/corpus/` plus `data/temporal.sqlite`.
It is a derived store in the sense of ADR 0001 §2: delete it and rebuild.

Why a file of its own rather than more tables in `data/temporal.sqlite`: that
database is an *input* to the scorer and to `verify_pipeline.py`, so writing
into it would make a read-only artifact mutable.

**The two kinds of window, which is the distinction the main result rests on.**
`temporal/effective_intervals.py` intersects a version's own window with the
document's and with every ancestor's coverage, so the `effective_intervals` in
`data/derived/corpus/versions.jsonl` are already the *propagated* ones. The
version chain's own window is a different column — `valid_from`/`valid_to` in
`data/derived/versions.jsonl`. Both are stored here, because the representation
ladder needs them apart:

    tier `document`    the document's dates                          (B7)
    tier `version`     document ∩ the chain's own window             (B7+)
    tier `propagated`  document ∩ chain ∩ every ancestor, formula (3) (proposed)

Each tier intersects strictly more than the one above it, so
𝒰ₜ(propagated) ⊆ 𝒰ₜ(version) ⊆ 𝒰ₜ(document) — an invariant `temporal.py`
asserts. Measured on the real corpus: the propagated window differs from the
local one on 790.025 of 1.595.823 versions (49,5%).

`context` is the document's own heading plus the first line of each ancestor
(Phần/Chương/Mục/Điều). It exists because a unit's own text does not identify
it: 207.419 of 1.455.372 layer-A units share their text with another unit, and
79.850 distinct texts occur in more than one document. Adding this header lifts
the question-token coverage of the gold unit from 0,555 to 0,740. That is an
ordinary chunk-header gain, not a graph result, so every system that wants it
gets it (`SystemSpec.context`).

Usage:
    python scripts/eval/index_corpus.py            # build
    python scripts/eval/index_corpus.py --counts   # report what is in it
"""
from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path

ANCESTOR_LEVELS = ("Part", "Chapter", "Section", "Subsection", "Article")
HEADING_CHARS = 150          # an ancestor contributes its heading, never its body
BATCH = 20_000

SCHEMA = """
CREATE TABLE IF NOT EXISTS units (
    unit_id      TEXT PRIMARY KEY,
    layer        TEXT NOT NULL,          -- 'asis' | 'version'
    kind         TEXT NOT NULL,          -- 'provision' | 'instruction' | 'version'
    provision_id TEXT,                   -- instruction units: the target, when resolved
    document_id  TEXT NOT NULL,
    level        TEXT,
    ordinal      INTEGER,                -- layer B only
    local_from   TEXT,                   -- tier `version`: the chain's own window
    local_to     TEXT,
    text         TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS prop_iv (     -- tier `propagated`; several disjoint windows allowed (C7)
    unit_id TEXT NOT NULL,
    start   TEXT,
    end     TEXT,
    PRIMARY KEY (unit_id, start)
) WITHOUT ROWID;
CREATE TABLE IF NOT EXISTS documents (
    document_id    TEXT PRIMARY KEY,
    law_id         TEXT,
    title          TEXT,
    rank           TEXT,
    issued_on      TEXT,
    effective_from TEXT,
    effective_to   TEXT
);
CREATE TABLE IF NOT EXISTS pctx (        -- provision -> document + ancestor headings
    provision_id TEXT PRIMARY KEY,
    header       TEXT NOT NULL
) WITHOUT ROWID;
CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT NOT NULL);
"""
INDEXES = (
    "CREATE INDEX IF NOT EXISTS units_provision ON units(provision_id)",
    "CREATE INDEX IF NOT EXISTS units_document  ON units(document_id)",
    "CREATE INDEX IF NOT EXISTS units_layer     ON units(layer)",
)


@dataclass(frozen=True, slots=True)
class Unit:
    """One retrievable unit, with whichever window the caller's tier needs."""

    unit_id: str
    layer: str
    kind: str
    provision_id: str | None
    document_id: str
    level: str | None
    ordinal: int | None
    text: str
    context: str

    def retrieval_text(self, with_context: bool) -> str:
        """What the index sees, and what a prompt quotes."""
        if with_context and self.context:
            return f"{self.context}\n{self.text}"
        return self.text


def _heading(text: str) -> str:
    """An ancestor's first line, which is its heading — never its whole body."""
    line = (text or "").strip().split("\n", 1)[0].strip()
    return line[:HEADING_CHARS]


def _document_heading(number: str | None, title: str | None, rank: str | None) -> str:
    """The document's heading, without repeating its own number.

    `documents.title` on this portal usually already opens with the rank and the
    number ("Thông tư số 23/2026/TT-BXD Quy định…"), so prefixing them again
    produced a header that said the number twice.
    """
    title = (title or "").strip()
    number = (number or "").strip()
    if number and number in title:
        return title
    return " ".join(filter(None, ((rank or "").strip(), number, title))).strip()


def _connect(path: Path) -> sqlite3.Connection:
    db = sqlite3.connect(path)
    db.executescript("PRAGMA journal_mode=WAL; PRAGMA synchronous=OFF;")
    return db


def _done(db: sqlite3.Connection, stage: str) -> bool:
    row = db.execute("SELECT value FROM meta WHERE key=?", (f"stage:{stage}",)).fetchone()
    return bool(row and row[0] == "done")


def _finish(db: sqlite3.Connection, stage: str) -> None:
    db.execute("INSERT OR REPLACE INTO meta VALUES (?,?)", (f"stage:{stage}", "done"))
    db.commit()


def _rows(path: Path):
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            yield json.loads(line)


def build(data: Path, out: Path, *, log=lambda _m: None) -> dict[str, int]:
    """Build the index. Each stage is recorded, so an interrupted run resumes."""
    corpus = data / "derived/corpus"
    out.parent.mkdir(parents=True, exist_ok=True)
    db = _connect(out)
    db.executescript(SCHEMA)

    if not _done(db, "documents"):
        log("documents...")
        db.executemany(
            "INSERT OR REPLACE INTO documents VALUES (:document_id,:law_id,:title,:rank,"
            ":issued_on,:effective_from,:effective_to)",
            ({k: d.get(k) for k in ("document_id", "law_id", "title", "rank",
                                    "issued_on", "effective_from", "effective_to")}
             for d in _rows(corpus / "documents.jsonl")))
        _finish(db, "documents")

    if not _done(db, "asis"):
        log("layer A units...")
        batch = []
        for u in _rows(corpus / "asis.jsonl"):
            target = u.get("target_provision_id")
            batch.append((u["unit_id"], "asis", u["kind"],
                          u.get("provision_id") or (target if target not in (None, "None") else None),
                          u["document_id"], u.get("level"), None, None, None, u.get("text") or ""))
            if len(batch) >= BATCH:
                db.executemany("INSERT OR REPLACE INTO units (unit_id,layer,kind,provision_id,"
                               "document_id,level,ordinal,local_from,local_to,text) "
                               "VALUES (?,?,?,?,?,?,?,?,?,?)", batch)
                batch.clear()
        if batch:
            db.executemany("INSERT OR REPLACE INTO units (unit_id,layer,kind,provision_id,"
                           "document_id,level,ordinal,local_from,local_to,text) "
                           "VALUES (?,?,?,?,?,?,?,?,?,?)", batch)
        _finish(db, "asis")

    if not _done(db, "versions"):
        log("layer B units + propagated windows...")
        units, ivs = [], []
        for u in _rows(corpus / "versions.jsonl"):
            units.append((u["unit_id"], "version", "version", u["provision_id"], u["document_id"],
                          u.get("level"), u.get("ordinal"), None, None, u.get("text") or ""))
            for window in u.get("effective_intervals") or ():
                ivs.append((u["unit_id"], window.get("start"), window.get("end")))
            if len(units) >= BATCH:
                db.executemany("INSERT OR REPLACE INTO units (unit_id,layer,kind,provision_id,"
                               "document_id,level,ordinal,local_from,local_to,text) "
                               "VALUES (?,?,?,?,?,?,?,?,?,?)", units)
                db.executemany("INSERT OR REPLACE INTO prop_iv VALUES (?,?,?)", ivs)
                units.clear(); ivs.clear()
        db.executemany("INSERT OR REPLACE INTO units (unit_id,layer,kind,provision_id,"
                       "document_id,level,ordinal,local_from,local_to,text) "
                       "VALUES (?,?,?,?,?,?,?,?,?,?)", units)
        db.executemany("INSERT OR REPLACE INTO prop_iv VALUES (?,?,?)", ivs)
        _finish(db, "versions")

    if not _done(db, "local"):
        # The chain's own window lives only in the L3 output, keyed by the same id.
        log("local windows from the version chain...")
        db.execute("CREATE TEMP TABLE local_iv (unit_id TEXT PRIMARY KEY, f TEXT, t TEXT)")
        batch = []
        for v in _rows(data / "derived/versions.jsonl"):
            batch.append((v["id"], v.get("valid_from"), v.get("valid_to")))
            if len(batch) >= BATCH:
                db.executemany("INSERT OR REPLACE INTO local_iv VALUES (?,?,?)", batch)
                batch.clear()
        db.executemany("INSERT OR REPLACE INTO local_iv VALUES (?,?,?)", batch)
        db.execute("UPDATE units SET local_from=local_iv.f, local_to=local_iv.t "
                   "FROM local_iv WHERE units.unit_id=local_iv.unit_id")
        _finish(db, "local")

    if not _done(db, "context"):
        log("context headers...")
        src = sqlite3.connect(data / "temporal.sqlite")
        heading = {pid: _heading(text) for pid, text in src.execute(
            "SELECT p.id, v.text FROM provisions p JOIN versions v"
            "  ON v.provision_id = p.id AND v.ordinal = 1"
            f" WHERE p.level IN ({','.join('?' * len(ANCESTOR_LEVELS))})", ANCESTOR_LEVELS)}
        doc = {d: _document_heading(n, t, r)
               for d, n, t, r in src.execute("SELECT id, number, title, rank FROM documents")}
        batch = []
        for pid, document_id, path in src.execute("SELECT id, document_id, path FROM provisions"):
            parts = [p for p in (path or "").split("/") if p and p != pid]
            crumbs = [heading[p] for p in parts if p in heading and heading[p]]
            batch.append((pid, " › ".join([doc.get(document_id, ""), *crumbs]).strip(" ›")))
            if len(batch) >= BATCH:
                db.executemany("INSERT OR REPLACE INTO pctx VALUES (?,?)", batch)
                batch.clear()
        db.executemany("INSERT OR REPLACE INTO pctx VALUES (?,?)", batch)
        src.close()
        _finish(db, "context")

    if not _done(db, "indexes"):
        log("indexes...")
        for statement in INDEXES:
            db.execute(statement)
        _finish(db, "indexes")

    db.commit()
    counts = _counts(db)
    db.execute("INSERT OR REPLACE INTO meta VALUES ('counts', ?)", (json.dumps(counts),))
    db.commit()
    db.close()
    return counts


def _counts(db: sqlite3.Connection) -> dict[str, int]:
    one = lambda q: db.execute(q).fetchone()[0]
    return {
        "documents": one("SELECT COUNT(*) FROM documents"),
        "units_asis": one("SELECT COUNT(*) FROM units WHERE layer='asis'"),
        "units_version": one("SELECT COUNT(*) FROM units WHERE layer='version'"),
        "instructions": one("SELECT COUNT(*) FROM units WHERE kind='instruction'"),
        "propagated_windows": one("SELECT COUNT(*) FROM prop_iv"),
        "versions_with_local_window": one(
            "SELECT COUNT(*) FROM units WHERE layer='version' AND local_from IS NOT NULL"),
        "provisions_with_context": one("SELECT COUNT(*) FROM pctx WHERE header <> ''"),
    }


# ---------------------------------------------------------------- lexical index

#: One contentless FTS5 table with two columns, so a single build serves both
#: `context` settings: B2 matches and scores `body` alone via a column filter
#: plus a zero weight on `ctx`, while B2+ctx searches both. Vietnamese needs its
#: diacritics kept, so `remove_diacritics` is explicitly 0 — the default would
#: fold "hiệu lực" and "hieu luc" together and change what BM25 counts.
FTS_SCHEMA = """
CREATE VIRTUAL TABLE IF NOT EXISTS units_fts USING fts5(
    ctx, body, content='', tokenize='unicode61 remove_diacritics 0'
);
-- Document frequency per term, so a long question can be cut down to its rare
-- words before it is run. "định" occurs in 2.541.452 of 2.978.024 units and
-- costs most of the index to score while carrying almost no signal.
CREATE VIRTUAL TABLE IF NOT EXISTS units_vocab USING fts5vocab(units_fts, 'row');
"""


def build_lexical(out: Path, *, log=lambda _m: None) -> dict[str, int]:
    """Build the BM25 index over the units already in `out`.

    Separate from `build` because it is the slow half and is only needed once a
    system actually retrieves; `index_corpus.py --lexical` runs it.
    """
    db = _connect(out)
    db.executescript(FTS_SCHEMA)
    if not _done(db, "lexical"):
        log("BM25 index over context + text...")
        db.execute("INSERT INTO units_fts(rowid, ctx, body) "
                   "SELECT u.rowid, COALESCE(c.header,''), u.text "
                   "FROM units u LEFT JOIN pctx c ON c.provision_id = u.provision_id")
        _finish(db, "lexical")
    if not _done(db, "lexical-optimize"):
        log("optimising the BM25 index...")
        db.execute("INSERT INTO units_fts(units_fts) VALUES ('optimize')")
        _finish(db, "lexical-optimize")
    db.commit()
    counts = {"indexed": db.execute("SELECT COUNT(*) FROM units_fts").fetchone()[0]}
    db.close()
    return counts


def has_lexical(db: sqlite3.Connection) -> bool:
    return bool(db.execute("SELECT 1 FROM sqlite_master WHERE name='units_fts'").fetchone())


class Corpus:
    """Read access to the built index."""

    def __init__(self, path: Path | str) -> None:
        self.path = Path(path)
        if not self.path.exists():
            raise FileNotFoundError(
                f"no retrieval index at {self.path}; build it with "
                f"`python scripts/eval/index_corpus.py`")
        self.db = sqlite3.connect(f"file:{self.path}?mode=ro", uri=True)
        self.db.row_factory = sqlite3.Row

    # `context` is joined, not stored per unit: one header serves every unit under it.
    _SELECT = ("SELECT u.unit_id, u.layer, u.kind, u.provision_id, u.document_id, u.level,"
               " u.ordinal, u.text, COALESCE(c.header,'') AS context"
               " FROM units u LEFT JOIN pctx c ON c.provision_id = u.provision_id")

    def unit(self, unit_id: str) -> Unit | None:
        row = self.db.execute(f"{self._SELECT} WHERE u.unit_id=?", (unit_id,)).fetchone()
        return Unit(**dict(row)) if row else None

    def units(self, unit_ids: list[str]) -> list[Unit]:
        """The named units, in the order asked — a ranking must survive the lookup."""
        if not unit_ids:
            return []
        found = {}
        for chunk in (unit_ids[i:i + 500] for i in range(0, len(unit_ids), 500)):
            rows = self.db.execute(
                f"{self._SELECT} WHERE u.unit_id IN ({','.join('?' * len(chunk))})", chunk)
            for row in rows:
                found[row["unit_id"]] = Unit(**dict(row))
        return [found[u] for u in unit_ids if u in found]

    def document(self, document_id: str) -> sqlite3.Row | None:
        return self.db.execute("SELECT * FROM documents WHERE document_id=?",
                               (document_id,)).fetchone()

    @property
    def lexical(self) -> bool:
        return has_lexical(self.db)

    @property
    def total_units(self) -> int:
        if getattr(self, "_total", None) is None:
            self._total = self.db.execute("SELECT COUNT(*) FROM units").fetchone()[0]
        return self._total

    @property
    def vocab(self) -> bool:
        return bool(self.db.execute(
            "SELECT 1 FROM sqlite_master WHERE name='units_vocab'").fetchone())

    def counts(self) -> dict[str, int]:
        row = self.db.execute("SELECT value FROM meta WHERE key='counts'").fetchone()
        return json.loads(row[0]) if row else _counts(self.db)

    def close(self) -> None:
        self.db.close()

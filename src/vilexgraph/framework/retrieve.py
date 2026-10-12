"""Ranking inside 𝒰ₜ (plan phase-5-6, P2/P4).

Formula (4) narrows the search space before ranking, so the effectivity filter
and the ranking happen in one statement: SQLite applies the FTS match, keeps
only what the tier admits, and only then takes the top k. Filtering after a
top-k would be a different system — it would rank against units the tier was
supposed to have removed.

The graph does not supply similarity between a question and a provision, so
candidates inside 𝒰ₜ are still ordered by text signals. Each signal is kept
separately on the `Hit` rather than collapsed into one number, because A1–A4
re-read them without re-running the grid.

Lexical retrieval is SQLite FTS5. One contentless table carries `ctx` and
`body`, so `context=False` is a column filter plus a zero weight rather than a
second index — which is what lets B2 and B2+ctx be the same build and makes the
chunk-header gain a reported number.
"""
from __future__ import annotations

import hashlib
import json
import re
import sqlite3
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path

from .systems import SystemSpec
from .temporal import predicate

MAX_TERMS = 30          # an OR of every word in a long question scans most of the index
MIN_TERM = 2
# Selection is OFF by default: it was measured against gold and it costs real
# recall. See `select_terms` for the table. `--fast-retrieval` turns it on for
# dev iteration only.
KEEP_TERMS = MAX_TERMS
MAX_DF_RATIO = 1.01
FAST_KEEP, FAST_DF_RATIO = 20, 0.50
CTX_WEIGHT = 1.0        # when the header is in play
NO_CTX_WEIGHT = 0.0


@dataclass(frozen=True, slots=True)
class Hit:
    """One candidate, with each signal that put it there kept apart."""

    unit_id: str
    signals: dict[str, float] = field(default_factory=dict)

    @property
    def score(self) -> float:
        return sum(self.signals.values())


class RetrievalCache:
    """Ranked results per (retrieval configuration, question, date).

    Retrieval here is deterministic and slow — a long Vietnamese question costs
    seconds against a 2,98M-unit BM25 index — while the grid reuses the same
    (question, date) across systems that share a retrieval configuration. Of the
    registered systems only about six configurations are distinct, so caching
    turns the grid from one pass per system into one pass per configuration, and
    makes every re-score free.

    Keyed by the configuration, so changing a tier or `k` cannot return a stale
    ranking. Without a filter or an expansion the date reaches no query, so it is
    left out of the key: the four dates of a question then cost one search.
    """

    def __init__(self, path: Path | str | None) -> None:
        self.db = None
        if path is None:
            return
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(path)
        self.db.execute("CREATE TABLE IF NOT EXISTS hits (key TEXT PRIMARY KEY, payload TEXT)")
        self.db.commit()

    @staticmethod
    def key(spec: SystemSpec, question: str, as_of: str) -> str:
        signature = json.dumps([spec.layer, spec.temporal, spec.context, spec.k, spec.lexical,
                                spec.dense, spec.rerank, spec.expand, spec.expand_edges,
                                question, as_of if spec.temporal != "none" or spec.expand else None],
                               ensure_ascii=False)
        return hashlib.sha256(signature.encode()).hexdigest()

    def get(self, key: str) -> list[Hit] | None:
        if self.db is None:
            return None
        row = self.db.execute("SELECT payload FROM hits WHERE key=?", (key,)).fetchone()
        if row is None:
            return None
        return [Hit(unit_id, signals) for unit_id, signals in json.loads(row[0])]

    def put(self, key: str, hits: list[Hit]) -> None:
        if self.db is None:
            return
        payload = json.dumps([[h.unit_id, h.signals] for h in hits], ensure_ascii=False)
        self.db.execute("INSERT OR REPLACE INTO hits VALUES (?,?)", (key, payload))
        self.db.commit()

    def close(self) -> None:
        if self.db is not None:
            self.db.close()


def query_terms(question: str, *, min_len: int = MIN_TERM, limit: int = MAX_TERMS) -> list[str]:
    """A question as FTS5 terms, quoted so no word can act as syntax.

    FTS5's `unicode61` tokenizer does the real tokenisation; this only has to
    produce safe, meaningful terms. Diacritics are kept, because the index keeps
    them: folding them here would match words the index stores separately.
    """
    text = unicodedata.normalize("NFC", question or "").lower()
    text = "".join(" " if unicodedata.category(ch).startswith("P") else ch for ch in text)
    seen, terms = set(), []
    for word in text.split():
        word = word.strip('"')
        if len(word) < min_len or word in seen or not re.search(r"\w", word):
            continue
        seen.add(word)
        terms.append(word)
        if len(terms) >= limit:
            break
    return terms


def match_expression(terms: list[str], *, body_only: bool) -> str:
    """An FTS5 MATCH over the terms, optionally restricted to the `body` column."""
    joined = " OR ".join(f'"{t}"' for t in terms)
    return f"body : ({joined})" if body_only else joined


def select_terms(corpus, terms: list[str], *, keep: int = KEEP_TERMS,
                 max_df_ratio: float = MAX_DF_RATIO) -> list[str]:
    """Cut a question down to its rarest terms before running it.

    A ViLexTime question carries about 30 content words, and an OR over all of
    them takes 4–8 s because Vietnamese function words have enormous posting
    lists ("định" is in 85% of units, "quy" 74%, "về" 61%).

    Cutting them is **not** free. Measured on 25 answerable dev rows, layer B,
    tier `propagated`:

        config         R@1    R@20   MRR    s/query  terms
        keep10/df.10   0.360  0.840  0.509   1.48      9.8
        keep15/df.30   0.320  0.920  0.526   3.26     15.0
        keep20/df.50   0.400  0.920  0.596   4.76     20.0
        all terms      0.440  0.920  0.610   7.55     27.9

    Under OR semantics BM25 sums a contribution from every matching term, so
    dropping the common ones removes diffuse signal along with the cost — R@1
    falls from 0,440 to 0,360. Selection is therefore **off by default**: the
    cost is one-time because `RetrievalCache` keys on the configuration, and a
    thesis result is not worth trading for wall-clock. `FAST_KEEP` exists for
    dev iteration, where 1,6x the speed for 0,04 of R@1 is a fair trade.

    Whatever the setting, it is applied identically to every system, so it
    cannot tilt the ladder.
    """
    if not terms or not corpus.vocab:
        return terms
    placeholders = ",".join("?" * len(terms))
    frequency = dict(corpus.db.execute(
        f"SELECT term, doc FROM units_vocab WHERE term IN ({placeholders})", terms))
    ranked = sorted(terms, key=lambda term: (frequency.get(term, 0), term))
    cap = corpus.total_units * max_df_ratio
    rare = [term for term in ranked if frequency.get(term, 0) <= cap]
    # Every word common? Then rarity is all the signal there is; keep the rarest.
    return (rare or ranked)[:keep]


def lexical(corpus, question: str, as_of: str, *, layer: str, tier: str,
            context: bool, k: int, fast: bool = False) -> list[Hit]:
    """BM25 over 𝒰ₜ. Empty when the question has no usable term."""
    limits = {"keep": FAST_KEEP, "max_df_ratio": FAST_DF_RATIO} if fast else {}
    terms = select_terms(corpus, query_terms(question), **limits)
    if not terms:
        return []
    clause, params = predicate(tier, as_of)
    where = f" AND {clause}" if clause else ""
    weight = CTX_WEIGHT if context else NO_CTX_WEIGHT
    sql = (f"SELECT u.unit_id, bm25(units_fts, {weight}, 1.0) AS score"
           " FROM units_fts"
           " JOIN units u ON u.rowid = units_fts.rowid"
           " LEFT JOIN documents d ON d.document_id = u.document_id"
           " WHERE units_fts MATCH ? AND u.layer = ?"
           f"{where} ORDER BY score LIMIT ?")
    rows = corpus.db.execute(
        sql, [match_expression(terms, body_only=not context), layer, *params, k]).fetchall()
    # SQLite's bm25() is negative, better being more negative; report it rising.
    return [Hit(unit_id, {"lexical": -score}) for unit_id, score in rows]


def searcher(corpus, spec: SystemSpec, cache: "RetrievalCache | None" = None, *,
             fast: bool = False):
    """The search callable for one system: `(question, as_of) -> [Hit, ...]`."""
    if not spec.retrieves:
        raise ValueError(f"{spec.name} does not retrieve")
    if spec.lexical and not corpus.lexical:
        raise RuntimeError(
            "this index has no BM25 table; build it with "
            "`python scripts/eval/index_corpus.py --lexical`")
    if spec.dense:
        raise NotImplementedError(
            f"{spec.name} wants dense retrieval, which is not built yet (plan P4). "
            f"Run it on lexical retrieval alone with --no-dense, or build the "
            f"embeddings first.")
    graph = None
    if spec.expand:
        from .graphx import Graph  # late: graphx imports Hit from this module
        graph = Graph(corpus)

    def search(question: str, as_of: str) -> list[Hit]:
        key = RetrievalCache.key(spec, question, as_of) if cache else None
        if key is not None:
            hit = cache.get(key)
            if hit is not None:
                return hit
        found = lexical(corpus, question, as_of, layer=spec.layer, tier=spec.temporal,
                        context=spec.context, k=spec.k, fast=fast)
        if graph is not None:
            from .graphx import expand
            found = expand(graph, spec, found, as_of)
        if key is not None:
            cache.put(key, found)
        return found

    return search

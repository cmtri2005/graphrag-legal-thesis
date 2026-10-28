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

Dense retrieval reads the vectors `scripts/eval/embed_corpus.py` wrote and
scores every text exhaustively, then walks candidates best-first keeping only
what the tier admits: exactly the top k of 𝒰ₜ, without materialising 𝒰ₜ.
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
RRF_K = 60            # standard reciprocal-rank offset for the approved B4 descriptive baseline


@dataclass(frozen=True, slots=True)
class Hit:
    """One candidate, with each signal that put it there kept apart."""

    unit_id: str
    signals: dict[str, float] = field(default_factory=dict)

    @property
    def score(self) -> float:
        return sum(self.signals.values())


def fuse_rrf(lexical_hits: list[Hit], dense_hits: list[Hit], k: int) -> list[Hit]:
    """Merge two already-filtered rankings; keep the source contributions separate."""
    scores: dict[str, dict[str, float]] = {}
    for name, hits in (("lexical_rrf", lexical_hits), ("dense_rrf", dense_hits)):
        for rank, hit in enumerate(hits, 1):
            scores.setdefault(hit.unit_id, {})[name] = 1 / (RRF_K + rank)
    merged = [Hit(unit_id, signals) for unit_id, signals in scores.items()]
    return sorted(merged, key=lambda hit: (-hit.score, hit.unit_id))[:k]


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

    def __init__(self, path: Path | str | None, scope: str = "") -> None:
        # `scope` names what the configuration does not: the corpus and the vectors searched.
        # A rebuilt corpus under the same key would otherwise hand back the old ranking.
        self.db, self.scope = None, scope
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
        row = self.db.execute("SELECT payload FROM hits WHERE key=?", (self._scoped(key),)).fetchone()
        if row is None:
            return None
        return [Hit(unit_id, signals) for unit_id, signals in json.loads(row[0])]

    def put(self, key: str, hits: list[Hit]) -> None:
        if self.db is None:
            return
        payload = json.dumps([[h.unit_id, h.signals] for h in hits], ensure_ascii=False)
        self.db.execute("INSERT OR REPLACE INTO hits VALUES (?,?)", (self._scoped(key), payload))
        self.db.commit()

    def _scoped(self, key: str) -> str:
        return hashlib.sha256(f"{self.scope}|{key}".encode()).hexdigest() if self.scope else key

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


class Dense:
    """Cosine search over one layer's embeddings (W2-12, B3).

    `encode` maps a question to an L2-normalised vector; by default it loads the
    model named in the embeddings' own meta, so a query is encoded exactly as
    the corpus was (including pyvi word segmentation for PhoBERT).
    """

    POOL = 500      # candidate texts looked up per round trip

    def __init__(self, path: Path | str, encode=None) -> None:
        import numpy as np
        path = Path(path)
        self.db = sqlite3.connect(path / "texts.sqlite")
        # one-off: reverse lookups the embedding run did not need
        self.db.execute("CREATE INDEX IF NOT EXISTS unit_sha ON unit(sha)")
        self.db.execute("CREATE INDEX IF NOT EXISTS text_pos ON text(shard, row)")
        self.db.commit()
        self.meta = dict(self.db.execute("SELECT key, value FROM meta"))
        # read into RAM (2.3 GB for layer A): an mmap is re-read from disk on every
        # question once the page cache cannot hold it, which made a search take ~16 s
        self.shards = [np.load(f) for f in sorted(path.glob("shard-*.npy"))]
        if not self.shards:
            raise RuntimeError(f"{path} has no shard-*.npy; run scripts/eval/embed_corpus.py")
        self.starts = np.cumsum([0] + [len(x) for x in self.shards])
        self.encode = encode or self._model()

    def _model(self):
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer(self.meta["model"])
        model.max_seq_length = int(self.meta["max_seq_length"])
        segment = self.meta["text"].startswith("pyvi(")

        def encode(text: str):
            if segment:
                from pyvi.ViTokenizer import tokenize
                text = tokenize(text)
            return model.encode([text], normalize_embeddings=True, convert_to_numpy=True)[0]
        return encode

    def search(self, corpus, question: str, as_of: str, *, layer: str, tier: str,
               k: int) -> list[Hit]:
        import numpy as np
        if layer != self.meta["layer"]:
            raise ValueError(f"embeddings are of layer {self.meta['layer']!r}, not {layer!r}")
        import torch     # ships with sentence-transformers
        # fp16 -> fp32 per shard, then an exact fp32 dot: torch converts ~5x faster than
        # numpy here (2.3 s vs 11 s over 1.48M vectors on the 4-core dev box); a pure fp16
        # product is faster still but moves scores by ~1e-3, enough to reorder near-ties.
        q = torch.from_numpy(np.asarray(self.encode(question), dtype=np.float32))
        scores = torch.cat([torch.from_numpy(shard).float() @ q for shard in self.shards]).numpy()
        order = np.argsort(-scores, kind="stable")
        clause, params = predicate(tier, as_of)
        where = f" AND {clause}" if clause else ""
        hits: list[Hit] = []
        for start in range(0, len(order), self.POOL):
            batch = order[start:start + self.POOL]
            shard_of = np.searchsorted(self.starts, batch, side="right") - 1
            sha_at = {}
            for shard in set(shard_of.tolist()):
                rows = [int(i - self.starts[shard]) for i, s in zip(batch, shard_of) if s == shard]
                sha_at.update(((shard, row), sha) for row, sha in self.db.execute(
                    f"SELECT row, sha FROM text WHERE shard=? AND row IN ({','.join('?' * len(rows))})",
                    [shard, *rows]))
            shas = [sha_at[(int(s), int(i - self.starts[s]))] for i, s in zip(batch, shard_of)]
            owners: dict[str, list[str]] = {}
            for unit_id, sha in self.db.execute(
                    f"SELECT unit_id, sha FROM unit WHERE sha IN ({','.join('?' * len(shas))})", shas):
                owners.setdefault(sha, []).append(unit_id)
            candidates = [u for sha in shas for u in sorted(owners.get(sha, ()))]
            if not candidates:
                continue
            admitted = {row[0] for row in corpus.db.execute(
                "SELECT u.unit_id FROM units u LEFT JOIN documents d ON d.document_id = u.document_id"
                f" WHERE u.unit_id IN ({','.join('?' * len(candidates))}) AND u.layer = ?{where}",
                [*candidates, layer, *params])}
            for i, sha in zip(batch, shas):
                for unit_id in sorted(owners.get(sha, ())):
                    if unit_id in admitted:
                        hits.append(Hit(unit_id, {"dense": float(scores[i])}))
                        if len(hits) == k:
                            return hits
        return hits


def searcher(corpus, spec: SystemSpec, cache: "RetrievalCache | None" = None, *,
             fast: bool = False, dense: Dense | None = None):
    """The search callable for one system: `(question, as_of) -> [Hit, ...]`."""
    if not spec.retrieves:
        raise ValueError(f"{spec.name} does not retrieve")
    if spec.lexical and not corpus.lexical:
        raise RuntimeError(
            "this index has no BM25 table; build it with "
            "`python scripts/eval/index_corpus.py --lexical`")
    if spec.rerank:
        raise NotImplementedError(
            f"{spec.name} needs a reranker, which is not built. "
            f"Run it on lexical retrieval alone with --no-dense.")
    if spec.dense and dense is None:
        raise RuntimeError(f"{spec.name} needs the embeddings: pass --embed <dir>")
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
        if spec.lexical and spec.dense:
            lexical_hits = lexical(corpus, question, as_of, layer=spec.layer, tier=spec.temporal,
                                   context=spec.context, k=spec.k, fast=fast)
            dense_hits = dense.search(corpus, question, as_of, layer=spec.layer,
                                      tier=spec.temporal, k=spec.k)
            found = fuse_rrf(lexical_hits, dense_hits, spec.k)
        elif spec.dense:
            found = dense.search(corpus, question, as_of, layer=spec.layer,
                                 tier=spec.temporal, k=spec.k)
        else:
            found = lexical(corpus, question, as_of, layer=spec.layer, tier=spec.temporal,
                            context=spec.context, k=spec.k, fast=fast)
        if graph is not None:
            from .graphx import expand
            found = expand(graph, spec, found, as_of)
        if key is not None:
            cache.put(key, found)
        return found

    return search

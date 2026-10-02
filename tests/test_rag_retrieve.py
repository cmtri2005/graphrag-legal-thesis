"""Ranking inside 𝒰ₜ: term building, the context column, and filter-before-rank."""
from __future__ import annotations

from pathlib import Path

import pytest

from vilexgraph.framework.corpus import Corpus, build, build_lexical
from vilexgraph.framework.retrieve import (MAX_TERMS, Hit, lexical, match_expression, query_terms,
                                        searcher)
from vilexgraph.framework.systems import REGISTRY, SystemSpec
from test_rag_corpus import CLAUSE, data  # noqa: F401  (fixture)

VERSION_UNIT = f"version:{CLAUSE.split(':')[1]}:1"


@pytest.fixture
def indexed(data: Path, tmp_path: Path) -> Corpus:
    out = tmp_path / "index.sqlite"
    build(data, out)
    build_lexical(out)
    return Corpus(out)


def test_terms_are_deduped_capped_and_safe() -> None:
    assert query_terms("quy định quy định về") == ["quy", "định", "về"]
    assert query_terms("a bb") == ["bb"], "one-character tokens carry no signal"
    assert query_terms('nội "bộ"') == ["nội", "bộ"], "quotes must not reach FTS as syntax"
    assert query_terms("") == []
    assert len(query_terms(" ".join(f"từ{i}" for i in range(100)))) == MAX_TERMS


def test_diacritics_are_kept() -> None:
    assert query_terms("hiệu lực") == ["hiệu", "lực"]


def test_match_expression_can_restrict_to_the_body() -> None:
    assert match_expression(["a", "b"], body_only=False) == '"a" OR "b"'
    assert match_expression(["a"], body_only=True) == 'body : ("a")'


def test_lexical_finds_the_clause_by_its_own_words(indexed: Corpus) -> None:
    hits = lexical(indexed, "nội dung khoản", "2021-01-01", layer="version",
                   tier="none", context=False, k=10)
    assert VERSION_UNIT in [h.unit_id for h in hits]
    assert all(h.signals["lexical"] == pytest.approx(h.score) for h in hits)


def test_the_header_is_searchable_only_when_context_is_on(indexed: Corpus) -> None:
    """"Chương" appears in the ancestor header, never in the clause body."""
    with_ctx = lexical(indexed, "Chương QUY ĐỊNH CHUNG", "2021-01-01", layer="version",
                       tier="none", context=True, k=10)
    without = lexical(indexed, "Chương QUY ĐỊNH CHUNG", "2021-01-01", layer="version",
                      tier="none", context=False, k=10)
    assert VERSION_UNIT in [h.unit_id for h in with_ctx]
    assert without == [], "context=False must not match the header"


def test_the_tier_filters_before_the_top_k(indexed: Corpus) -> None:
    """Formula (4): a unit the tier excludes must not appear, however well it matches.

    At 2023-01-01 the clause's own chain is still open but its Điều was repealed,
    so `version` keeps it and `propagated` must not.
    """
    question = "nội dung khoản một"
    kept = lexical(indexed, question, "2023-01-01", layer="version", tier="version",
                   context=False, k=10)
    dropped = lexical(indexed, question, "2023-01-01", layer="version", tier="propagated",
                      context=False, k=10)
    assert VERSION_UNIT in [h.unit_id for h in kept]
    assert VERSION_UNIT not in [h.unit_id for h in dropped]
    # before the ancestor's repeal both tiers agree
    assert VERSION_UNIT in [h.unit_id for h in lexical(
        indexed, question, "2021-01-01", layer="version", tier="propagated",
        context=False, k=10)]


def test_layer_is_respected(indexed: Corpus) -> None:
    a = lexical(indexed, "nội dung khoản", "2021-01-01", layer="asis", tier="none",
                context=False, k=10)
    assert all(h.unit_id.startswith("asis:") for h in a)


def test_k_bounds_the_result(indexed: Corpus) -> None:
    assert len(lexical(indexed, "nội dung khoản một", "2021-01-01", layer="version",
                       tier="none", context=False, k=1)) <= 1


def test_a_question_with_no_usable_term_returns_nothing(indexed: Corpus) -> None:
    assert lexical(indexed, "? ! -", "2021-01-01", layer="version", tier="none",
                   context=False, k=5) == []


def test_searcher_builds_a_callable_for_a_lexical_system(indexed: Corpus) -> None:
    search = searcher(indexed, REGISTRY["b2"])
    assert all(isinstance(h, Hit) for h in search("nội dung khoản", "2021-01-01"))


def test_searcher_refuses_dense_until_it_is_built(indexed: Corpus) -> None:
    with pytest.raises(NotImplementedError, match="dense"):
        searcher(indexed, REGISTRY["b3"])
    with pytest.raises(ValueError, match="does not retrieve"):
        searcher(indexed, REGISTRY["b1"])


def test_searcher_says_how_to_build_a_missing_bm25_index(data: Path, tmp_path: Path) -> None:
    out = tmp_path / "bare.sqlite"
    build(data, out)
    with pytest.raises(RuntimeError, match="--lexical"):
        searcher(Corpus(out), REGISTRY["b2"])


def test_dense_free_variant_of_the_ladder_is_runnable(indexed: Corpus) -> None:
    """How P2 runs the main table before any embedding exists."""
    for name in ("b7", "b7plus", "proposed"):
        spec = REGISTRY[name].variant(f"{name}-lex", dense=False, rerank=False,
                                      expand=0, expand_edges="none")
        assert callable(searcher(indexed, spec))


def test_retrieval_cache_round_trip(indexed: Corpus, tmp_path: Path) -> None:
    from vilexgraph.framework.retrieve import RetrievalCache

    cache = RetrievalCache(tmp_path / "hits.sqlite")
    spec = REGISTRY["b2"]
    key = RetrievalCache.key(spec, "nội dung khoản", "2021-01-01")
    assert cache.get(key) is None
    cache.put(key, [Hit("version:x:1", {"lexical": 2.5})])
    got = cache.get(key)
    assert got == [Hit("version:x:1", {"lexical": 2.5})]
    cache.close()


def test_retrieval_cache_key_tracks_the_configuration() -> None:
    from vilexgraph.framework.retrieve import RetrievalCache

    base = REGISTRY["b7plus"]
    key = RetrievalCache.key(base, "q", "2021-01-01")
    for changed in (base.variant("x", temporal="propagated"), base.variant("x", k=5),
                    base.variant("x", context=False), base.variant("x", layer="asis",
                                                                   temporal="none")):
        assert RetrievalCache.key(changed, "q", "2021-01-01") != key, \
            "a configuration change must not return a stale ranking"
    assert RetrievalCache.key(base, "q", "2022-01-01") != key


def test_searcher_serves_the_second_call_from_cache(indexed: Corpus, tmp_path: Path) -> None:
    from vilexgraph.framework import retrieve as module

    cache = module.RetrievalCache(tmp_path / "hits.sqlite")
    search = module.searcher(indexed, REGISTRY["b2"], cache)
    first = search("nội dung khoản", "2021-01-01")
    calls = []
    real = module.lexical
    module.lexical = lambda *a, **k: calls.append(1) or real(*a, **k)
    try:
        assert search("nội dung khoản", "2021-01-01") == first
        assert calls == [], "a cached configuration must not hit the index again"
    finally:
        module.lexical = real

"""The representation ladder: four tiers, nested, over the same rows."""
from __future__ import annotations

import pytest

from vilexgraph.framework.temporal import (TIERS, TierError, assert_monotone, in_force, predicate,
                                        windows_for)
from test_rag_corpus import CLAUSE, corpus, data  # noqa: F401  (fixtures)

VERSION_UNIT = f"version:{CLAUSE.split(':')[1]}:1"


def passes(corpus, tier: str, as_of: str) -> set[str]:
    clause, params = predicate(tier, as_of)
    where = f"AND {clause}" if clause else ""
    return {r[0] for r in corpus.db.execute(
        "SELECT u.unit_id FROM units u LEFT JOIN documents d ON d.document_id = u.document_id"
        f" WHERE u.layer='version' {where}", params)}


def test_every_tier_is_known() -> None:
    assert TIERS == ("none", "document", "version", "propagated")
    with pytest.raises(TierError, match="unknown tier"):
        predicate("nope", "2020-01-01")


def test_tier_none_places_no_restriction() -> None:
    assert predicate("none", "2020-01-01") == ("", [])


def test_version_tier_carries_the_document_predicate() -> None:
    """Without it the ladder stops being nested and the tiers stop being comparable."""
    clause, params = predicate("version", "2020-01-01")
    assert "d.effective_from" in clause and "u.local_from" in clause
    assert len(params) == 4


def test_propagated_tier_reads_the_precomputed_windows() -> None:
    clause, _ = predicate("propagated", "2020-01-01")
    assert "prop_iv" in clause
    assert "u.local_from" not in clause, "tier 4 uses the intersected window, not the local one"


def test_the_clause_outlives_its_repealed_ancestor_only_under_the_local_tier(corpus) -> None:
    """The one case that distinguishes B7+ from the proposed system.

    The clause's own chain never closed, so tier `version` keeps it at a date
    after its Điều was repealed. Tier `propagated` drops it, because formula (3)
    intersects the ancestor's coverage.
    """
    after = "2023-01-01"
    assert VERSION_UNIT in passes(corpus, "document", after)
    assert VERSION_UNIT in passes(corpus, "version", after)
    assert VERSION_UNIT not in passes(corpus, "propagated", after)
    # and before the repeal every tier agrees
    assert VERSION_UNIT in passes(corpus, "propagated", "2021-01-01")


def test_ladder_is_nested_on_the_fixture(corpus) -> None:
    for as_of in ("2019-01-01", "2021-01-01", "2023-01-01"):
        assert_monotone(corpus, as_of, sample=10)


def test_assert_monotone_catches_a_crossed_window(corpus, monkeypatch) -> None:
    """A collapsed ladder must name the two window kinds, not just fail.

    Simulated by making tier `version` reject a unit tier `propagated` accepts,
    which is what reading the wrong column for one of them would look like.
    """
    real = predicate

    def broken(tier, as_of):
        return ("1=0", []) if tier == "version" else real(tier, as_of)

    monkeypatch.setattr("vilexgraph.framework.temporal.predicate", broken)
    with pytest.raises(AssertionError, match="effective_intervals"):
        assert_monotone(corpus, "2021-01-01", sample=10)


def test_assert_monotone_catches_a_version_tier_without_document_bounds(corpus, monkeypatch) -> None:
    real = predicate

    def broken(tier, as_of):
        return ("1=0", []) if tier == "document" else real(tier, as_of)

    monkeypatch.setattr("vilexgraph.framework.temporal.predicate", broken)
    with pytest.raises(AssertionError, match="must be nested"):
        assert_monotone(corpus, "2021-01-01", sample=10)


def test_in_force_is_half_open() -> None:
    """Invariant D1, and the same reading the scorer uses."""
    window = [("2020-01-01", "2021-01-01")]
    assert in_force(window, "2020-01-01")
    assert in_force(window, "2020-12-31")
    assert not in_force(window, "2021-01-01")
    assert not in_force(window, "2019-12-31")
    assert in_force([("2020-01-01", None)], "2999-01-01")
    assert not in_force([(None, None)], "2020-01-01")
    assert not in_force([], "2020-01-01")


def test_windows_for_each_tier(corpus) -> None:
    assert windows_for(corpus, VERSION_UNIT, "document") == [("2020-01-01", None)]
    assert windows_for(corpus, VERSION_UNIT, "version") == [("2020-01-01", None)]
    assert windows_for(corpus, VERSION_UNIT, "propagated") == [("2020-01-01", "2022-01-01")]
    assert windows_for(corpus, "version:absent:1", "propagated") == []
    with pytest.raises(TierError):
        windows_for(corpus, VERSION_UNIT, "nope")

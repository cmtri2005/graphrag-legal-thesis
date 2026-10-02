"""The experiment table: every system is one row, and a bad row cannot exist."""
from __future__ import annotations

import pytest

from vilexgraph.framework.systems import LADDER, REGISTRY, SystemError_, SystemSpec, get


def test_the_ladder_walks_the_tiers_in_order() -> None:
    """The main result: one retriever, one generator, only ρ changes."""
    tiers = [REGISTRY[name].temporal for name in LADDER]
    assert tiers == ["none", "document", "version", "propagated"]
    shared = {(REGISTRY[n].lexical, REGISTRY[n].context) for n in LADDER}
    assert shared == {(True, True)}, "the ladder must differ only in its tier"


def test_b7plus_is_the_proposed_system_without_the_online_graph() -> None:
    proposed, b7plus = REGISTRY["proposed"], REGISTRY["b7plus"]
    assert b7plus.layer == proposed.layer == "version"
    assert (b7plus.expand, b7plus.verify) == (0, "off")
    assert proposed.expand == 1 and proposed.verify == "reject"


def test_a4_drops_propagation_which_is_what_h3_needs() -> None:
    assert REGISTRY["a4"].temporal == "version"
    assert REGISTRY["proposed"].temporal == "propagated"
    for field in ("layer", "lexical", "dense", "rerank", "context", "expand", "verify"):
        assert getattr(REGISTRY["a4"], field) == getattr(REGISTRY["proposed"], field)


def test_each_ablation_changes_exactly_one_axis() -> None:
    proposed = REGISTRY["proposed"]
    axes = ("layer", "lexical", "dense", "rerank", "temporal", "context", "expand",
            "expand_edges", "verify")
    for name in ("a1", "a2", "a3", "a4"):
        differing = [a for a in axes if getattr(REGISTRY[name], a) != getattr(proposed, a)]
        # A2 moves `expand` and `expand_edges` together: one switch, two fields.
        assert differing in (["temporal"], ["verify"], ["expand", "expand_edges"]), \
            f"{name} changes {differing}"


def test_b2_is_registered_with_and_without_the_header() -> None:
    """The chunk-header gain is reported, not quietly folded into the graph's result."""
    assert REGISTRY["b2"].context is False
    assert REGISTRY["b2ctx"].context is True
    for field in ("layer", "lexical", "dense", "temporal"):
        assert getattr(REGISTRY["b2"], field) == getattr(REGISTRY["b2ctx"], field)


def test_every_retrieval_baseline_may_use_the_header() -> None:
    for name in ("b3", "b4", "b5", "b6", "b7", "b7plus", "proposed"):
        assert REGISTRY[name].context is True, f"{name} must not be denied a chunk header"


def test_a_version_tier_needs_layer_b() -> None:
    with pytest.raises(SystemError_, match="carry no version window"):
        SystemSpec(name="bad", layer="asis", lexical=True, temporal="version")


def test_no_retrieval_means_no_filter() -> None:
    with pytest.raises(SystemError_, match="cannot retrieve or filter"):
        SystemSpec(name="bad", lexical=True)
    with pytest.raises(SystemError_, match="needs lexical or dense"):
        SystemSpec(name="bad", layer="asis")


def test_expansion_needs_an_edge_set() -> None:
    with pytest.raises(SystemError_, match="needs an edge set"):
        SystemSpec(name="bad", layer="version", lexical=True, expand=2)


def test_unknown_names_are_rejected_with_the_list() -> None:
    with pytest.raises(SystemError_, match="proposed"):
        get("b99")


def test_variant_renames_and_overrides() -> None:
    lex = REGISTRY["proposed"].variant("proposed-lex", dense=False, rerank=False)
    assert (lex.name, lex.dense, lex.rerank) == ("proposed-lex", False, False)
    assert lex.temporal == "propagated"
    assert REGISTRY["proposed"].dense is True, "variants must not mutate the registry"

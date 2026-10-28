"""One-hop expansion: the hierarchy (B6), the instructions aimed at a unit (B5), and the tier."""
from __future__ import annotations

import pytest

from vilexgraph.framework.corpus import Corpus, build
from vilexgraph.framework.graphx import Graph, expand
from vilexgraph.framework.retrieve import Hit
from vilexgraph.framework.systems import SystemSpec
from vilexgraph.framework.verify import invalid_units
from test_rag_corpus import ARTICLE, CLAUSE, DOC, data, write  # noqa: F401  (fixtures)

SEED = f"asis:{CLAUSE}"
PARENT = f"asis:{ARTICLE}"
COMMAND = "asis:event:e2"


@pytest.fixture
def graph(data, tmp_path):
    """The shared fixture plus a parent unit and a command that targets the clause."""
    asis = data / "derived/corpus/asis.jsonl"
    write(asis, [
        {"unit_id": SEED, "kind": "provision", "provision_id": CLAUSE, "document_id": DOC,
         "level": "Clause", "text": "1. Nội dung khoản một."},
        {"unit_id": PARENT, "kind": "provision", "provision_id": ARTICLE, "document_id": DOC,
         "level": "Article", "text": "Điều 1. Phạm vi"},
        {"unit_id": COMMAND, "kind": "instruction", "event_id": "event:e2", "operation": "amend",
         "document_id": DOC, "target_provision_id": CLAUSE, "text": "Sửa đổi khoản 1."},
    ])
    build(data, tmp_path / "index.sqlite")
    corpus = Corpus(tmp_path / "index.sqlite")
    yield Graph(corpus, data / "temporal.sqlite"), corpus
    corpus.close()


def spec(**kw) -> SystemSpec:
    base = dict(name="t", layer="asis", lexical=True, expand=1, expand_edges="part")
    return SystemSpec(**{**base, **kw})


def ids(hits) -> list[str]:
    return [h.unit_id for h in hits]


def test_no_expansion_returns_the_hits_untouched(graph) -> None:
    g, _ = graph
    hits = [Hit(SEED, {"lexical": 1.0})]
    assert expand(g, spec(expand=0, expand_edges="none"), hits, "2021-01-01") is hits


def test_part_adds_the_parent_after_the_hits(graph) -> None:
    g, _ = graph
    out = expand(g, spec(), [Hit(SEED, {"lexical": 1.0})], "2021-01-01")
    assert ids(out) == [SEED, PARENT]
    assert out[1].signals == {"graph": 1.0}


def test_rel_adds_the_instruction_that_targets_the_unit(graph) -> None:
    g, _ = graph
    out = expand(g, spec(expand_edges="rel"), [Hit(SEED, {"lexical": 1.0})], "2021-01-01")
    assert ids(out) == [SEED, COMMAND]


def test_a_neighbour_already_ranked_is_not_added_twice(graph) -> None:
    g, _ = graph
    hits = [Hit(SEED, {"lexical": 2.0}), Hit(PARENT, {"lexical": 1.0})]
    assert ids(expand(g, spec(), hits, "2021-01-01")) == [SEED, PARENT]


def test_a_temporal_tier_drops_neighbours_whose_document_is_not_yet_in_force(graph) -> None:
    """The document starts 2020-01-01: before that, a temporal system admits nothing."""
    g, _ = graph
    hits = [Hit(SEED, {"lexical": 1.0})]
    early = "2019-06-01"
    assert ids(expand(g, spec(temporal="document"), hits, early)) == [SEED]
    assert ids(expand(g, spec(temporal="document", expand_edges="rel"), hits, early)) == [SEED]
    # the non-temporal baseline admits them — that is what makes it the baseline
    assert ids(expand(g, spec(temporal="none"), hits, early)) == [SEED, PARENT]
    assert ids(expand(g, spec(expand_edges="rel"), hits, early)) == [SEED, COMMAND]


@pytest.mark.parametrize("tier", ["document", "version", "propagated"])
def test_the_verifier_judges_an_instruction_by_its_document_like_expansion(graph, tier) -> None:
    """Expansion admits a command by its document; the Verifier must agree, or `proposed` regenerates."""
    _, corpus = graph
    assert invalid_units(corpus, tier, "2021-01-01", [COMMAND]) == ()
    assert invalid_units(corpus, tier, "2019-06-01", [COMMAND]) == (COMMAND,)

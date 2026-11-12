"""One-hop expansion: the hierarchy (B6), the instructions aimed at a unit (B5), and the tier."""
from __future__ import annotations

import pytest
from pathlib import Path

from vilexgraph.framework.corpus import Corpus, build
from vilexgraph.framework.graphx import Graph, expand
from vilexgraph.framework.retrieve import Hit
from vilexgraph.framework.systems import SystemSpec
from vilexgraph.framework.verify import invalid_units
from test_rag_corpus import ARTICLE, CLAUSE, DOC, data, write  # noqa: F401  (fixtures)

SEED = f"asis:{CLAUSE}"
PARENT = f"asis:{ARTICLE}"
COMMAND = "asis:event:e2"
REPEAL_UP = "asis:event:e3"     # aimed at the article, not at the clause


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
        {"unit_id": REPEAL_UP, "kind": "instruction", "event_id": "event:e3", "operation": "repeal",
         "document_id": DOC, "target_provision_id": ARTICLE, "text": "Bãi bỏ Điều 1."},
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


@pytest.mark.parametrize("tier", ["document", "version", "propagated"])
def test_rel_filters_effectivity_before_fanout(graph, tier):
    import sqlite3

    g, corpus = graph
    inactive = [f"asis:event:a{i}" for i in range(3)]
    active = "asis:event:a3"
    with sqlite3.connect(corpus.path) as db:
        db.execute("INSERT INTO documents(document_id,effective_from) VALUES (?,?)",
                   ("future", "2030-01-01"))
        db.executemany("INSERT INTO units(unit_id,layer,kind,provision_id,document_id,text) "
                       "VALUES (?, 'asis', 'instruction', ?, ?, '')",
                       [(uid, CLAUSE, "future" if uid in inactive else DOC)
                        for uid in [*inactive, active]])
    temporal = spec(layer="asis" if tier == "document" else "version",
                    expand_edges="rel", temporal=tier)
    found = ids(expand(g, temporal, [Hit(SEED)], "2021-01-01"))
    assert active in found, "eligible fourth instruction was lost before temporal filtering"
    assert not set(inactive) & set(found)
    # The non-temporal baseline still takes its original first three instructions.
    assert ids(expand(g, spec(expand_edges="rel"), [Hit(SEED)], "2021-01-01")) == [SEED, *inactive]


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


def test_propagated_follows_a_repeal_aimed_at_an_ancestor_from_seeds_the_filter_removed(graph) -> None:
    """The clause is gone from `hits` once its article is repealed; the seeds still reach the repeal."""
    g, _ = graph
    seeds = [Hit(SEED, {"lexical": 1.0})]
    up = spec(layer="version", expand_edges="rel_up", temporal="propagated")
    assert ids(expand(g, up, [], "2021-01-01", seeds)) == [COMMAND, REPEAL_UP]
    assert ids(expand(g, up, [Hit(PARENT, {"lexical": 1.0})], "2021-01-01")) == [PARENT, REPEAL_UP]
    # other tiers keep one hop: a repeal of the article is not found from the clause
    assert ids(expand(g, spec(expand_edges="rel", temporal="document"), seeds, "2021-01-01")) == [SEED, COMMAND]


def test_rel_keeps_one_hop_even_with_propagation(graph):
    g, _ = graph
    hits = [Hit(SEED, {"lexical": 1.0})]
    old = spec(layer="version", expand_edges="rel", temporal="propagated")
    assert ids(expand(g, old, hits, "2021-01-01")) == [SEED, COMMAND]
    assert expand(g, old, [], "2021-01-01", hits) == []


@pytest.mark.parametrize("effective_on,operation,as_of,expected", [
    ("2021-01-01", "repeal", "2021-01-01", True),
    ("2021-01-02", "repeal", "2021-01-01", False),
    ("2021-01-01", "amend", "2021-01-01", False),
    ("2018-01-01", "repeal", "2019-01-01", False),  # acting document starts in 2020
])
@pytest.mark.parametrize("seed_id", [SEED, PARENT])
@pytest.mark.parametrize("reuse_seeds", [False, True])
def test_repeal_note_links_parent_and_keeps_other_prompts_identical(
        graph, tmp_path, monkeypatch, effective_on, operation, as_of, expected, seed_id, reuse_seeds):
    from vilexgraph.framework import generate, graphx, retrieve
    g, corpus = graph
    events = tmp_path / "events.jsonl"
    write(events, [{"id": "event:e3", "operation": operation,
                    "target_provision_id": ARTICLE, "effective_on": effective_on}])
    def lexical(*args, **kwargs):
        assert not reuse_seeds, "repeal notes searched again despite supplied seed lookup"
        return [Hit(seed_id)]

    monkeypatch.setattr(retrieve, "lexical", lexical)
    new = spec(layer="version", temporal="propagated", expand_edges="rel_up", repeal_note=True)
    hits = [Hit(REPEAL_UP, {"graph": 1.0})]
    kwargs = {"seed_search": lambda question, date: [Hit(seed_id)]} if reuse_seeds else {}
    notes = graphx.repeal_notes(corpus, new, "q", as_of, hits, **kwargs,
                               temporal_db=g.tree.execute("PRAGMA database_list").fetchone()[2],
                               events=events)
    units = corpus.units([REPEAL_UP])
    old_prompt = generate.build_prompt("q", as_of, units, with_context=True)
    prompt = generate.build_prompt("q", as_of, units, with_context=True, repeal_notes=notes)
    assert prompt[0] == old_prompt[0] == generate.SYSTEM
    assert bool(notes) is expected
    if expected:
        assert "[1] BÃI BỎ" in prompt[1]
        assert (CLAUSE if seed_id == SEED else ARTICLE) in prompt[1] and ARTICLE in prompt[1]
        assert "ngày hiệu lực: 2021-01-01" in prompt[1]
        assert "Điều 1" in prompt[1]
        if seed_id == SEED:
            assert "Khoản 1" in prompt[1]
    else:
        assert prompt == old_prompt


def test_repeal_note_does_not_read_events_for_old_system_or_no_graph_command(graph):
    from vilexgraph.framework.graphx import repeal_notes
    _, corpus = graph
    new = spec(layer="version", temporal="propagated", expand_edges="rel_up", repeal_note=True)
    assert repeal_notes(corpus, new, "q", "2021-01-01", []) == []
    assert repeal_notes(corpus, new.variant("old", repeal_note=False), "q", "2021-01-01",
                        [Hit(REPEAL_UP, {"graph": 1.0})], events=Path("absent")) == []


@pytest.mark.parametrize("tier", ["document", "version", "propagated"])
def test_a_command_keeps_its_effect_after_its_document_lapses(graph, tier):
    """Repeal persists when the repealing act expires (12/11/2026); the Verifier agrees."""
    import sqlite3

    g, corpus = graph
    lapsed = "asis:event:lapsed"
    with sqlite3.connect(corpus.path) as db:
        db.execute("INSERT INTO documents(document_id,effective_from,effective_to) VALUES (?,?,?)",
                   ("old_act", "2015-01-01", "2018-01-01"))
        db.execute("INSERT INTO units(unit_id,layer,kind,provision_id,document_id,text) "
                   "VALUES (?, 'asis', 'instruction', ?, 'old_act', '')", (lapsed, CLAUSE))
    temporal = spec(layer="asis" if tier == "document" else "version", expand_edges="rel", temporal=tier)
    assert lapsed in ids(expand(g, temporal, [Hit(SEED)], "2021-01-01"))
    assert lapsed not in ids(expand(g, temporal, [Hit(SEED)], "2014-06-01"))   # not yet issued
    assert invalid_units(corpus, tier, "2021-01-01", [lapsed]) == ()
    assert invalid_units(corpus, tier, "2014-06-01", [lapsed]) == (lapsed,)

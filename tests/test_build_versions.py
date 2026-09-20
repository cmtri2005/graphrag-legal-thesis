from datetime import date

from build_versions import build_document_versions, effective_intervals
from legal_crawler.index import TemporalIndex
from legal_crawler.ingest import build_versions
from legal_crawler.temporal import (
    EventApplier, LegalDocument, Provision, ProvisionLevel, make_provision_id as P,
)


def _index(effective_from: date | None) -> TemporalIndex:
    index = TemporalIndex()
    target = LegalDocument("T", "01/2020", "Luật", effective_from=effective_from)
    actor = LegalDocument("A", "02/2024", "Nghị định", effective_from=date(2024, 1, 1))
    index.put_documents([target, actor])
    provisions = [Provision(P("d1"), "T", ProvisionLevel.ARTICLE, "Điều 1", None, 0),
                  Provision(P("k1"), "T", ProvisionLevel.CLAUSE, "Khoản 1", P("d1"), 1)]
    index.put_provisions(provisions)
    index.put_versions(build_versions(provisions, {"d1": {"text": "Điều 1"}, "k1": {"text": "cũ"}}, target))
    return index


def _row(event_id, operation, on, node="k1", new_text=None):
    return {"id": event_id, "actor_id": "A", "operation": operation, "target_document_id": "T",
            "target_provision_id": P(node), "effective_on": on, "status": "auto_accepted", "evidence": "e",
            "text_updates": [{"target_provision_id": P(node), "new_text": new_text}] if new_text else []}


def _build(index, rows):
    versions, outcomes, _, _ = build_document_versions(
        index, index.document("T"), {}, rows, EventApplier())
    return versions, outcomes


def _windows(index, rows):
    """{provision_id: (effective_from, effective_to)} of each node's last version."""
    versions, _, state, provisions = build_document_versions(
        index, index.document("T"), {}, rows, EventApplier())
    intervals = effective_intervals(index.document("T"), provisions, state)
    latest = {}
    for v in sorted(versions, key=lambda v: v.ordinal):
        latest[v.provision_id] = intervals.get(v.id)
    return latest


def test_amendment_closes_version_one_and_opens_two():
    versions, outcomes = _build(_index(date(2020, 1, 1)), [_row("e1", "amend", "2024-01-01", new_text="mới")])
    k1 = [v for v in versions if v.provision_id == P("k1")]
    assert outcomes == {"e1": None}
    assert [(v.ordinal, v.text) for v in k1] == [(1, "cũ"), (2, "mới")]
    assert (k1[0].validity.end, k1[1].validity.start, k1[1].validity.end) == (date(2024, 1, 1), date(2024, 1, 1), None)
    assert k1[0].ended_by_event_id == k1[1].created_by_event_id == "e1"


def test_event_on_a_closed_node_is_rejected_not_forced():
    rows = [_row("repeal", "repeal", "2023-01-01"), _row("late", "amend", "2024-01-01", new_text="mới")]
    versions, outcomes = _build(_index(date(2020, 1, 1)), rows)
    assert outcomes["repeal"] is None and "no open version" in outcomes["late"]
    assert [v.ordinal for v in versions if v.provision_id == P("k1")] == [1]


def test_document_without_effective_date_keeps_undated_versions_and_rejects_events():
    versions, outcomes = _build(_index(None), [_row("e1", "amend", "2024-01-01", new_text="mới")])
    assert len(versions) == 2 and all(v.validity is None for v in versions)
    assert outcomes["e1"] is not None


def test_repealing_the_parent_ends_the_child_window_too():
    """Formula (3): Khoản 1's own version stays open, but Điều 1 ended in 2024."""
    index = _index(date(2020, 1, 1))
    windows = _windows(index, [_row("e1", "repeal", "2024-01-01", node="d1")])

    assert windows[P("d1")] == (date(2020, 1, 1), date(2024, 1, 1))
    assert windows[P("k1")] == (date(2020, 1, 1), date(2024, 1, 1))


def test_the_document_window_bounds_every_version():
    index = TemporalIndex()
    document = LegalDocument("T", "01/2020", "Luật", effective_from=date(2020, 1, 1),
                             effective_to=date(2023, 1, 1))
    index.put_documents([document, LegalDocument("A", "02/2024", "NĐ",
                                                 effective_from=date(2024, 1, 1))])
    provisions = [Provision(P("d1"), "T", ProvisionLevel.ARTICLE, "Điều 1", None, 0)]
    index.put_provisions(provisions)
    index.put_versions(build_versions(provisions, {"d1": {"text": "x"}}, document))
    _, _, state, ordered = build_document_versions(index, document, {}, [], EventApplier())

    assert effective_intervals(document, ordered, state) == {
        list(state.versions)[0].id: (date(2020, 1, 1), date(2023, 1, 1))
    }

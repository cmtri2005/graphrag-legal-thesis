from datetime import date

import pytest

from legal_crawler.ingest import build_document, build_versions, walk_tree, IngestReport
from legal_crawler.index import TemporalIndex
from legal_crawler.temporal import (
    InvalidityReason,
    LegalDocument,
    Provision,
    ProvisionLevel,
    TemporalState,
    ValidityService,
    make_document_id,
    make_provision_id,
)


def _tree():
    return [
        {
            "id": "ch1", "level": "Chapter", "title": "Chương I", "orderIndex": 1,
            "children": [
                {
                    "id": "d1", "level": "Article", "title": "Điều 1", "orderIndex": 2,
                    "children": [
                        {"id": "k1", "level": "Clause", "title": "Khoản 1", "orderIndex": 3},
                    ],
                }
            ],
        }
    ]


def test_walk_tree_yields_parents_before_children():
    items = list(walk_tree(_tree(), "doc1"))
    assert [p.id for p in items] == [
        "provision:ch1",
        "provision:d1",
        "provision:k1",
    ]
    assert [p.parent_id for p in items] == [
        None,
        "provision:ch1",
        "provision:d1",
    ]
    assert {p.document_id for p in items} == {"document:doc1"}


def test_descendants_use_materialized_path():
    store = TemporalIndex()
    store.put_documents([LegalDocument("document:doc1", "01/2020", "Luật A")])
    store.put_provisions(walk_tree(_tree(), "doc1"))
    assert [p.id for p in store.descendants_of("provision:ch1")] == [
        "provision:d1",
        "provision:k1",
    ]
    assert [p.id for p in store.descendants_of("provision:k1")] == []
    assert len(store.document_order("document:doc1")) == 3


def test_contradictory_effective_to_is_dropped_not_the_document():
    report = IngestReport()
    document = build_document(
        "x", {"docNum": "78/2014", "title": "T", "effFrom": "2014-08-02",
              "effTo": "2012-09-10"}, report)
    assert document.effective_from == date(2014, 8, 2)
    assert document.effective_to is None
    assert report["effective_to_dropped"] == 1


def test_undated_document_yields_versions_no_query_can_return():
    report = IngestReport()
    document = build_document("x", {"docNum": "n", "title": "t"}, report)
    provisions = list(walk_tree(_tree(), "x"))
    versions = build_versions(provisions, {"d1": {"text": "nội dung"}}, document)

    assert len(versions) == 1
    assert versions[0].validity is None
    assert versions[0].is_locally_valid_at(date(2020, 1, 1)) is False

    store = TemporalIndex()
    store.put_documents([document])
    store.put_provisions(provisions)
    store.put_versions(versions)
    stored = store.versions_of("provision:d1")
    assert len(stored) == 1
    assert stored[0].validity is None


def test_initial_version_stays_locally_open_but_document_expiry_is_enforced():
    report = IngestReport()
    document = build_document(
        "x", {"docNum": "n", "title": "t", "effFrom": "2020-01-01", "effTo": "2025-01-01"},
        report)
    provisions = list(walk_tree(_tree(), "x"))
    store = TemporalIndex()
    store.put_documents([document])
    store.put_provisions(provisions)
    store.put_versions(build_versions(
        provisions,
        {"ch1": {"text": "Chương I"}, "d1": {"text": "Điều 1"},
         "k1": {"text": "Khoản 1"}},
        document,
    ))

    provision_id = "provision:k1"
    local = store.versions_of(provision_id)
    assert len(local) == 1
    assert local[0].validity.end is None
    assert local[0].is_locally_valid_at(date(2025, 1, 1))

    state = TemporalState()
    state.add_document(store.document(document.id))
    for provision in store.document_order(document.id):
        state.add_provision(provision)
    for version in store.versions_for_document(document.id):
        state.add_version(version)
    validity = ValidityService(state)
    assert validity.check(provision_id, date(2019, 12, 31)).reason is (
        InvalidityReason.DOCUMENT_NOT_YET_EFFECTIVE
    )
    assert validity.is_valid(provision_id, date(2024, 12, 31))
    assert validity.check(provision_id, date(2025, 1, 1)).reason is (
        InvalidityReason.DOCUMENT_EXPIRED
    )


def test_sqlite_index_does_not_expose_an_incomplete_point_in_time_answer():
    assert not hasattr(TemporalIndex, "version_at")


def test_order_comes_from_the_walk_not_the_overflowing_portal_counter():
    tree = [{"id": "a", "level": "Article", "title": "Điều 1", "orderIndex": 32767,
             "children": [{"id": "b", "level": "Clause", "title": "Khoản 1", "orderIndex": -32768}]}]
    assert [p.order_index for p in walk_tree(tree, "doc")] == [0, 1]


def test_derived_subtree_nodes_resolve_under_their_article():
    from legal_crawler.ingest import subtree_provisions
    from legal_crawler.index import TemporalIndex
    from legal_crawler.temporal import Provision, ProvisionLevel

    index = TemporalIndex(":memory:")
    index.put_provisions([
        Provision(
            make_provision_id("a1"),
            make_document_id("D"),
            ProvisionLevel.ARTICLE,
            "Điều 1",
            None,
            0,
        )
    ])
    index.put_provisions(subtree_provisions(
        {"nodes": [
            {"id": "a1#k1", "parent_id": "a1", "level": "Clause", "title": "Khoản 1"},
            {"id": "a1#k1#a", "parent_id": "a1#k1", "level": "Point", "title": "Điểm a"},
        ]},
        "D",
    ))
    assert [p.id for p in index.descendants_of(make_provision_id("a1"))] == [
        make_provision_id("a1#k1"),
        make_provision_id("a1#k1#a"),
    ]

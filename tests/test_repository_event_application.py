from dataclasses import replace
from datetime import date

import pytest

from legal_crawler.adapters.memory import MemoryUnitOfWork
from legal_crawler.application import RepositoryEventApplicationService
from legal_crawler.ports import RepositoryConflictError
from legal_crawler.temporal import (
    EventApplicationError,
    EventStatus,
    ExtractionMethod,
    LegalDocument,
    LegalEvent,
    LegalOperation,
    Provenance,
    Provision,
    ProvisionInsertion,
    ProvisionLevel,
    ProvisionVersion,
    RelationType,
    TemporalInterval,
    TextUpdate,
    UnsupportedEventError,
)

SOURCE_DOCUMENT = "document:amending-law"
TARGET_DOCUMENT = "document:law"
EFFECTIVE_ON = date(2024, 7, 1)


def provenance() -> tuple[Provenance, ...]:
    return (
        Provenance(
            SOURCE_DOCUMENT,
            ExtractionMethod.RULE,
            source_provision_id="provision:source-article",
            evidence_text="Khoản 1 Điều 2 được sửa đổi như sau...",
        ),
    )


def seed_uow(*, include_second_version: bool = True) -> MemoryUnitOfWork:
    uow = MemoryUnitOfWork()
    uow.documents.put_many(
        (
            LegalDocument(
                TARGET_DOCUMENT,
                "01/2020/QH",
                "Luật kiểm thử",
                effective_from=date(2020, 1, 1),
            ),
            LegalDocument(
                SOURCE_DOCUMENT,
                "02/2024/QH",
                "Luật sửa đổi",
                effective_from=EFFECTIVE_ON,
            ),
        )
    )
    article = Provision(
        "provision:article-2",
        TARGET_DOCUMENT,
        ProvisionLevel.ARTICLE,
        "Điều 2",
        None,
        order_index=2,
    )
    first = Provision(
        "provision:clause-1",
        TARGET_DOCUMENT,
        ProvisionLevel.CLAUSE,
        "Khoản 1",
        article.id,
        order_index=1,
    )
    second = Provision(
        "provision:clause-2",
        TARGET_DOCUMENT,
        ProvisionLevel.CLAUSE,
        "Khoản 2",
        article.id,
        order_index=2,
    )
    uow.provisions.put_many((article, first, second))
    versions = [
        ProvisionVersion(
            "version:article-2:1",
            article.id,
            1,
            "Nội dung Điều 2.",
            TemporalInterval(date(2020, 1, 1)),
            provenance=provenance(),
        ),
        ProvisionVersion(
            "version:clause-1:1",
            first.id,
            1,
            "Nội dung Khoản 1 ban đầu.",
            TemporalInterval(date(2020, 1, 1)),
            provenance=provenance(),
        ),
    ]
    if include_second_version:
        versions.append(
            ProvisionVersion(
                "version:clause-2:1",
                second.id,
                1,
                "Nội dung Khoản 2 ban đầu.",
                TemporalInterval(date(2020, 1, 1)),
                provenance=provenance(),
            )
        )
    uow.versions.put_many(versions)
    return uow


def legal_event(
    identifier: str = "event:amend",
    operation: LegalOperation = LegalOperation.AMEND,
    **changes,
) -> LegalEvent:
    values = {
        "id": identifier,
        "operation": operation,
        "source_document_id": SOURCE_DOCUMENT,
        "target_document_id": TARGET_DOCUMENT,
        "effective_on": EFFECTIVE_ON,
        "target_provision_ids": ("provision:clause-1",),
        "new_text": "Nội dung Khoản 1 sau sửa đổi.",
        "status": EventStatus.VERIFIED,
        "provenance": provenance(),
    }
    values.update(changes)
    return LegalEvent(**values)


def test_service_commits_amendment_versions_event_snapshots_and_graph_edges():
    uow = seed_uow()
    event = legal_event()
    service = RepositoryEventApplicationService(uow)

    result = service.apply(event)

    assert result.applied
    assert result.closed_version_ids == ("version:clause-1:1",)
    assert result.created_version_ids == ("version:provision%3Aclause-1:2",)
    closed = uow.versions.get("version:clause-1:1")
    current = uow.versions.current_for("provision:clause-1")
    assert closed.validity.end == EFFECTIVE_ON
    assert closed.ended_by_event_id == event.id
    assert current.text == "Nội dung Khoản 1 sau sửa đổi."
    assert current.created_by_event_id == event.id
    assert uow.events.is_applied(event.id)
    assert uow.snapshots.snapshot(
        "provision:clause-1", date(2024, 6, 30)
    ).text == "Nội dung Khoản 1 ban đầu."
    assert uow.snapshots.snapshot(
        "provision:clause-1", EFFECTIVE_ON
    ).text == "Nội dung Khoản 1 sau sửa đổi."

    operation_edges = uow.graph.outgoing(
        event.id, relations=frozenset({RelationType.AMENDS})
    )
    version_edges = uow.graph.outgoing(current.id)
    assert len(operation_edges) == 1
    assert operation_edges[0].target_id == TARGET_DOCUMENT
    assert {item.relation for item in version_edges} == {
        RelationType.VERSION_OF,
        RelationType.CAUSED_BY,
    }


def test_service_replay_is_idempotent_across_every_repository():
    uow = seed_uow()
    event = legal_event()
    service = RepositoryEventApplicationService(uow)
    first = service.apply(event)
    edge_ids = tuple(sorted(uow.store.edges))

    replay = service.apply(event)

    assert first.applied
    assert replay.already_applied
    assert not replay.applied
    assert len(uow.versions.chain_for("provision:clause-1")) == 2
    assert tuple(sorted(uow.store.edges)) == edge_ids


def test_service_applies_an_event_that_was_registered_but_not_yet_applied():
    uow = seed_uow()
    event = legal_event("event:pending")
    uow.events.put(event)

    result = RepositoryEventApplicationService(uow).apply(event)

    assert result.applied
    assert uow.events.is_applied(event.id)
    current = uow.versions.current_for("provision:clause-1")
    assert current.created_by_event_id == event.id


def test_distinct_events_on_same_date_do_not_collide_in_the_graph():
    uow = seed_uow()
    service = RepositoryEventApplicationService(uow)
    first = legal_event("event:first")
    second = legal_event(
        "event:second",
        target_provision_ids=("provision:clause-2",),
        new_text="Nội dung Khoản 2 sau sửa đổi.",
    )

    service.apply(first)
    service.apply(second)

    assert len(uow.graph.outgoing(first.id)) == 1
    assert len(uow.graph.outgoing(second.id)) == 1
    assert uow.versions.current_for("provision:clause-1").text == first.new_text
    assert uow.versions.current_for("provision:clause-2").text == second.new_text


@pytest.mark.parametrize(
    ("operation", "relation"),
    (
        (LegalOperation.REPLACE, RelationType.REPLACES),
        (LegalOperation.CORRECT, RelationType.CORRECTS),
    ),
)
def test_service_maps_each_remaining_text_operation_to_its_graph_relation(
    operation,
    relation,
):
    uow = seed_uow()
    event = legal_event(f"event:{operation.value.lower()}", operation)

    RepositoryEventApplicationService(uow).apply(event)

    edges = uow.graph.outgoing(
        event.id,
        relations=frozenset({relation}),
    )
    assert len(edges) == 1
    assert edges[0].target_id == TARGET_DOCUMENT


def test_service_rejects_conflicting_reuse_of_an_applied_event_id():
    uow = seed_uow()
    service = RepositoryEventApplicationService(uow)
    original = legal_event()
    service.apply(original)

    with pytest.raises(RepositoryConflictError):
        service.apply(replace(original, new_text="Nội dung xung đột."))

    assert uow.versions.current_for("provision:clause-1").text == original.new_text


def test_service_persists_repeal_and_snapshot_audit_event():
    uow = seed_uow()
    event = legal_event(
        "event:repeal",
        LegalOperation.REPEAL,
        new_text=None,
    )

    result = RepositoryEventApplicationService(uow).apply(event)
    snapshot = uow.snapshots.snapshot("provision:clause-1", EFFECTIVE_ON)

    assert result.created_version_ids == ()
    assert result.directly_repealed_provision_ids == ("provision:clause-1",)
    assert not snapshot.validity.valid
    assert snapshot.caused_by_event == event
    assert snapshot.ended_by_event == event
    assert uow.graph.outgoing(
        event.id, relations=frozenset({RelationType.REPEALS})
    )


def test_service_persists_supplemented_tree_in_dependency_order():
    uow = seed_uow()
    event = legal_event(
        "event:supplement",
        LegalOperation.SUPPLEMENT,
        target_provision_ids=(),
        new_text=None,
        insertions=(
            ProvisionInsertion(
                "provision:point-a-new",
                ProvisionLevel.POINT,
                "Điểm a",
                "Nội dung điểm mới.",
                "provision:clause-3-new",
            ),
            ProvisionInsertion(
                "provision:clause-3-new",
                ProvisionLevel.CLAUSE,
                "Khoản 3",
                "Nội dung khoản mới.",
                "provision:article-2",
                after_provision_id="provision:clause-2",
            ),
        ),
    )

    result = RepositoryEventApplicationService(uow).apply(event)

    assert result.created_provision_ids == (
        "provision:clause-3-new",
        "provision:point-a-new",
    )
    assert uow.snapshots.snapshot(
        "provision:point-a-new", EFFECTIVE_ON
    ).text == "Nội dung điểm mới."
    contains = uow.graph.incoming(
        "provision:clause-3-new",
        relations=frozenset({RelationType.CONTAINS}),
    )
    assert contains[0].source_id == "provision:article-2"


def test_invalid_multi_target_event_rolls_back_stored_event_and_all_versions():
    uow = seed_uow(include_second_version=False)
    before = uow.versions.current_for("provision:clause-1")
    event = legal_event(
        "event:atomic",
        new_text=None,
        target_provision_ids=(),
        text_updates=(
            TextUpdate("provision:clause-1", "Nội dung không được commit."),
            TextUpdate("provision:clause-2", "Target không có version."),
        ),
    )

    with pytest.raises(EventApplicationError, match="has no version"):
        RepositoryEventApplicationService(uow).apply(event)

    assert uow.events.get(event.id) is None
    assert not uow.events.is_applied(event.id)
    assert uow.versions.current_for("provision:clause-1") == before


def test_late_graph_failure_rolls_back_closed_and_created_versions():
    uow = seed_uow()
    event = legal_event("event:graph-failure")

    def fail_graph_write(edges):
        raise RuntimeError("graph unavailable")

    uow.graph.put_many = fail_graph_write

    with pytest.raises(RuntimeError, match="graph unavailable"):
        RepositoryEventApplicationService(uow).apply(event)

    current = uow.versions.current_for("provision:clause-1")
    assert current.id == "version:clause-1:1"
    assert current.validity.end is None
    assert uow.events.get(event.id) is None
    assert not uow.events.is_applied(event.id)


def test_unsupported_operation_rolls_back_event_registration():
    uow = seed_uow()
    event = legal_event(
        "event:suspend",
        LegalOperation.SUSPEND,
        new_text=None,
    )

    with pytest.raises(UnsupportedEventError):
        RepositoryEventApplicationService(uow).apply(event)

    assert uow.events.get(event.id) is None


def test_service_rejects_non_uow_and_non_event_inputs():
    with pytest.raises(TypeError, match="unit_of_work"):
        RepositoryEventApplicationService(object())

    service = RepositoryEventApplicationService(seed_uow())
    with pytest.raises(TypeError, match="LegalEvent"):
        service.apply(object())

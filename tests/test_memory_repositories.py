from dataclasses import replace
from datetime import date

import pytest

from legal_crawler.adapters.memory import MemoryUnitOfWork
from legal_crawler.ports import (
    DocumentRepository,
    EntityNotFoundError,
    EventRepository,
    ProvisionRepository,
    RepositoryConflictError,
    RepositoryIntegrityError,
    SnapshotRepository,
    TemporalGraphRepository,
    TemporalUnitOfWork,
    TransactionError,
    VersionRepository,
    WriteDisposition,
)
from legal_crawler.temporal import (
    EventStatus,
    ExtractionMethod,
    GraphEdge,
    InvalidityReason,
    LegalDocument,
    LegalEvent,
    LegalOperation,
    Provenance,
    Provision,
    ProvisionLevel,
    ProvisionVersion,
    RelationType,
    TemporalInterval,
)


def document(
    identifier: str = "document:law",
    *,
    start: date | None = date(2020, 1, 1),
    end: date | None = None,
) -> LegalDocument:
    return LegalDocument(
        identifier,
        identifier.removeprefix("document:"),
        f"Văn bản {identifier}",
        effective_from=start,
        effective_to=end,
    )


def provision(
    identifier: str,
    *,
    document_id: str = "document:law",
    level: ProvisionLevel = ProvisionLevel.ARTICLE,
    parent_id: str | None = None,
    order: int | None = None,
    after: str | None = None,
) -> Provision:
    return Provision(
        identifier,
        document_id,
        level,
        identifier,
        parent_id,
        order_index=order,
        inserted_after_id=after,
    )


def version(
    identifier: str,
    provision_id: str,
    ordinal: int,
    start: date,
    end: date | None = None,
    *,
    text: str | None = None,
    ended_by: str | None = None,
    evidence: Provenance | None = None,
) -> ProvisionVersion:
    return ProvisionVersion(
        identifier,
        provision_id,
        ordinal,
        text or f"Nội dung {ordinal}",
        TemporalInterval(start, end),
        ended_by_event_id=ended_by,
        provenance=(evidence,) if evidence else (),
    )


def event(
    identifier: str = "event:amend",
    *,
    operation: LegalOperation = LegalOperation.AMEND,
    effective_on: date | None = date(2022, 1, 1),
    target_ids: tuple[str, ...] = ("provision:article-1",),
    evidence: Provenance | None = None,
) -> LegalEvent:
    return LegalEvent(
        identifier,
        operation,
        "document:source",
        "document:law",
        effective_on,
        target_provision_ids=target_ids,
        status=(EventStatus.VERIFIED if target_ids else EventStatus.NEEDS_REVIEW),
        provenance=(evidence,) if evidence else (),
    )


def seeded_uow() -> MemoryUnitOfWork:
    uow = MemoryUnitOfWork()
    uow.documents.put_many((document(), document("document:source")))
    uow.provisions.put(provision("provision:article-1", order=1))
    return uow


def test_memory_bundle_satisfies_every_authoritative_repository_protocol():
    uow = MemoryUnitOfWork()

    assert isinstance(uow, TemporalUnitOfWork)
    assert isinstance(uow.documents, DocumentRepository)
    assert isinstance(uow.provisions, ProvisionRepository)
    assert isinstance(uow.versions, VersionRepository)
    assert isinstance(uow.events, EventRepository)
    assert isinstance(uow.graph, TemporalGraphRepository)
    assert isinstance(uow.snapshots, SnapshotRepository)


def test_document_repository_is_idempotent_conflict_safe_and_half_open():
    uow = MemoryUnitOfWork()
    expired = document(end=date(2023, 1, 1))

    assert uow.documents.put(expired).disposition is WriteDisposition.CREATED
    assert uow.documents.put(expired).disposition is WriteDisposition.UNCHANGED
    assert uow.documents.exists(expired.id)
    assert uow.documents.get_many((expired.id, "missing")) == {expired.id: expired}
    assert uow.documents.list_effective_at(date(2022, 12, 31)) == (expired,)
    assert uow.documents.list_effective_at(date(2023, 1, 1)) == ()

    with pytest.raises(RepositoryConflictError):
        uow.documents.put(replace(expired, title="Nội dung xung đột"))


def test_document_batch_is_atomic_when_later_item_conflicts():
    uow = MemoryUnitOfWork()
    original = document()
    uow.documents.put(original)

    with pytest.raises(RepositoryConflictError):
        uow.documents.put_many(
            (
                document("document:new"),
                replace(original, title="Nội dung xung đột"),
            )
        )

    assert uow.documents.get("document:new") is None
    assert uow.documents.get(original.id) == original


def test_provision_batch_resolves_parent_and_anchor_in_any_input_order():
    uow = MemoryUnitOfWork()
    uow.documents.put(document())
    article = provision("provision:article-1", order=1)
    clause = provision(
        "provision:clause-1",
        level=ProvisionLevel.CLAUSE,
        parent_id=article.id,
        order=1,
    )
    inserted = provision(
        "provision:clause-1a",
        level=ProvisionLevel.CLAUSE,
        parent_id=article.id,
        after=clause.id,
    )

    result = uow.provisions.put_many((inserted, clause, article))

    assert result.created_ids == (inserted.id, clause.id, article.id)
    assert tuple(item.id for item in uow.provisions.document_order(document().id)) == (
        article.id,
        clause.id,
        inserted.id,
    )
    assert uow.provisions.descendants_of(article.id) == (clause, inserted)


def test_provision_batch_rolls_back_unresolved_or_cross_document_structure():
    uow = MemoryUnitOfWork()
    uow.documents.put_many((document(), document("document:other")))
    parent = provision("provision:parent")
    invalid_child = provision(
        "provision:child",
        document_id="document:other",
        level=ProvisionLevel.CLAUSE,
        parent_id=parent.id,
    )

    with pytest.raises(RepositoryIntegrityError):
        uow.provisions.put_many((parent, invalid_child))

    assert uow.provisions.get(parent.id) is None
    assert uow.provisions.get(invalid_child.id) is None


def test_version_batch_sorts_dependencies_but_preserves_result_order():
    uow = seeded_uow()
    first = version(
        "version:article-1:1",
        "provision:article-1",
        1,
        date(2020, 1, 1),
        date(2022, 1, 1),
    )
    second = version(
        "version:article-1:2",
        "provision:article-1",
        2,
        date(2022, 1, 1),
    )

    result = uow.versions.put_many((second, first))

    assert result.created_ids == (second.id, first.id)
    assert uow.versions.version_at(first.provision_id, date(2021, 12, 31)) == first
    assert uow.versions.version_at(first.provision_id, date(2022, 1, 1)) == second
    assert uow.versions.current_for(first.provision_id) == second


def test_version_repository_rejects_overlap_and_returns_detached_chain():
    uow = seeded_uow()
    current = version(
        "version:article-1:1", "provision:article-1", 1, date(2020, 1, 1)
    )
    uow.versions.put(current)

    with pytest.raises(RepositoryIntegrityError):
        uow.versions.put(
            version(
                "version:article-1:2",
                current.provision_id,
                2,
                date(2021, 1, 1),
            )
        )

    detached = uow.versions.chain_for(current.provision_id)
    assert detached is not None
    detached.close_current(date(2023, 1, 1))
    assert uow.versions.current_for(current.provision_id) == current


def test_event_repository_indexes_events_and_applied_state():
    uow = seeded_uow()
    first = event("event:first", effective_on=date(2021, 1, 1))
    second = event("event:second", effective_on=date(2022, 1, 1))
    uow.events.put_many((second, first))

    during_2021 = TemporalInterval(date(2021, 1, 1), date(2022, 1, 1))
    assert uow.events.list_by_source_document(
        "document:source", effective_during=during_2021
    ) == (first,)
    assert uow.events.list_by_target_document("document:law") == (first, second)
    assert uow.events.list_for_provision("provision:article-1") == (first, second)
    assert uow.events.mark_applied(first.id)
    assert not uow.events.mark_applied(first.id)
    assert uow.events.is_applied(first.id)

    with pytest.raises(EntityNotFoundError):
        uow.events.mark_applied("event:missing")


def test_event_batch_requires_documents_and_rolls_back_prior_items():
    uow = seeded_uow()
    valid = event("event:valid")
    invalid = replace(event("event:invalid"), source_document_id="document:missing")

    with pytest.raises(RepositoryIntegrityError):
        uow.events.put_many((valid, invalid))

    assert uow.events.get(valid.id) is None


def test_temporal_graph_filters_direction_relation_and_half_open_time():
    uow = MemoryUnitOfWork()
    active = GraphEdge(
        "provision:a",
        "provision:b",
        RelationType.REFERS_TO,
        TemporalInterval(date(2020, 1, 1), date(2022, 1, 1)),
    )
    structural = GraphEdge(
        "document:law", "provision:a", RelationType.CONTAINS
    )
    active_id = uow.graph.put(active).entity_id
    uow.graph.put(structural)

    assert uow.graph.get(active_id) == active
    assert uow.graph.outgoing(
        "provision:a",
        relations=frozenset({RelationType.REFERS_TO}),
        at=date(2021, 1, 1),
    ) == (active,)
    assert uow.graph.outgoing("provision:a", at=date(2022, 1, 1)) == ()
    assert uow.graph.incoming("provision:b") == (active,)
    assert {
        (item.source_id, item.relation, item.target_id)
        for item in uow.graph.neighbors("provision:a")
    } == {
        (active.source_id, active.relation, active.target_id),
        (structural.source_id, structural.relation, structural.target_id),
    }


def test_graph_idempotency_and_atomic_batch_conflict():
    uow = MemoryUnitOfWork()
    edge = GraphEdge("a", "b", RelationType.REFERS_TO)
    edge_id = uow.graph.put(edge).entity_id
    assert uow.graph.put(edge).disposition is WriteDisposition.UNCHANGED

    conflicting = replace(edge, properties={"kind": "different"})
    with pytest.raises(RepositoryConflictError):
        uow.graph.put_many(
            (GraphEdge("b", "c", RelationType.REFERS_TO), conflicting)
        )

    assert uow.graph.get(edge_id) == edge
    assert uow.graph.outgoing("b") == ()


def test_provenance_can_be_read_from_version_event_edge_and_provision():
    uow = seeded_uow()
    evidence = Provenance(
        "document:source",
        ExtractionMethod.RULE,
        evidence_text="Điều 1 được sửa đổi như sau...",
    )
    item_version = version(
        "version:article-1:1",
        "provision:article-1",
        1,
        date(2020, 1, 1),
        evidence=evidence,
    )
    item_event = event(evidence=evidence)
    item_edge = GraphEdge(
        "document:source",
        "provision:article-1",
        RelationType.AMENDS,
        provenance=(evidence,),
    )
    uow.versions.put(item_version)
    uow.events.put(item_event)
    edge_id = uow.graph.put(item_edge).entity_id

    assert uow.provenance.for_entity(item_version.id) == (evidence,)
    assert uow.provenance.for_entity(item_event.id) == (evidence,)
    assert uow.provenance.for_entity(edge_id) == (evidence,)
    assert uow.provenance.for_entity("provision:article-1") == (evidence,)


def test_snapshot_repository_is_a_live_view_of_repository_writes():
    uow = seeded_uow()
    item = version(
        "version:article-1:1", "provision:article-1", 1, date(2020, 1, 1)
    )

    before = uow.snapshots.snapshot(item.provision_id, date(2021, 1, 1))
    uow.versions.put(item)
    after = uow.snapshots.snapshot(item.provision_id, date(2021, 1, 1))

    assert before.validity.reason is InvalidityReason.PROVISION_NOT_YET_EFFECTIVE
    assert after.text == item.text


def test_transaction_rolls_back_all_authoritative_state_in_place():
    uow = MemoryUnitOfWork()
    documents_repo = uow.documents
    snapshots_repo = uow.snapshots
    edge = GraphEdge("document:source", "document:law", RelationType.AMENDS)

    with pytest.raises(RuntimeError, match="abort"):
        with uow.transaction():
            uow.documents.put_many((document(), document("document:source")))
            uow.provisions.put(provision("provision:article-1"))
            uow.versions.put(
                version(
                    "version:article-1:1",
                    "provision:article-1",
                    1,
                    date(2020, 1, 1),
                )
            )
            uow.events.put(event())
            uow.events.mark_applied("event:amend")
            uow.graph.put(edge)
            raise RuntimeError("abort")

    assert uow.documents is documents_repo
    assert uow.snapshots is snapshots_repo
    assert uow.documents.get("document:law") is None
    assert uow.provisions.get("provision:article-1") is None
    assert uow.versions.get("version:article-1:1") is None
    assert uow.events.get("event:amend") is None
    assert not uow.events.is_applied("event:amend")
    assert uow.graph.outgoing("document:source") == ()
    assert snapshots_repo.snapshot(
        "provision:article-1", date(2021, 1, 1)
    ).validity.reason is InvalidityReason.UNKNOWN_PROVISION


def test_transaction_commits_and_rejects_nested_boundaries():
    uow = MemoryUnitOfWork()
    with uow.transaction():
        uow.documents.put(document())
    assert uow.documents.exists("document:law")

    with pytest.raises(TransactionError):
        with uow.transaction():
            uow.documents.put(document("document:temporary"))
            with uow.transaction():
                pass

    assert uow.documents.get("document:temporary") is None

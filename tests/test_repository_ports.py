import inspect
from datetime import date
from types import SimpleNamespace

import pytest

from legal_crawler.ports import (
    BatchWriteResult,
    DocumentRepository,
    EntityNotFoundError,
    EventRepository,
    ProvenanceRepository,
    ProvisionRepository,
    RepositoryConflictError,
    RepositoryError,
    RepositoryIntegrityError,
    SnapshotRepository,
    TemporalGraphRepository,
    TemporalUnitOfWork,
    TransactionError,
    VectorMatch,
    VectorRepository,
    VectorSearchQuery,
    VersionEmbedding,
    VersionRepository,
    WriteDisposition,
    WriteResult,
)
from legal_crawler.temporal import (
    ExtractionMethod,
    Provenance,
    ProvisionLevel,
    SnapshotService,
    TemporalInterval,
    TemporalState,
)


def method_stub(*names, **attributes):
    values = {name: (lambda *args, **kwargs: None) for name in names}
    values.update(attributes)
    return SimpleNamespace(**values)


def version_embedding() -> VersionEmbedding:
    return VersionEmbedding(
        id="embedding:version-2:model-a",
        version_id="version:clause-3:2",
        provision_id="provision:clause-3",
        document_id="document:law-1",
        model="model-a",
        vector=(0.1, -0.2, 0.3),
        validity=TemporalInterval(date(2024, 7, 1)),
        level=ProvisionLevel.CLAUSE,
        provenance=(
            Provenance(
                "document:amending-law",
                ExtractionMethod.RULE,
                evidence_text="Khoản 3 được sửa đổi như sau...",
            ),
        ),
        metadata={"language": "vi", "source": "verified-corpus"},
    )


def test_single_write_result_has_only_created_or_unchanged_outcome():
    created = WriteResult("document:1", WriteDisposition.CREATED)
    unchanged = WriteResult("document:2", WriteDisposition.UNCHANGED)

    assert created.created
    assert not unchanged.created
    assert {item.value for item in WriteDisposition} == {"created", "unchanged"}


def test_write_result_rejects_empty_id_and_untyped_disposition():
    with pytest.raises(ValueError, match="entity_id"):
        WriteResult("", WriteDisposition.CREATED)
    with pytest.raises(ValueError, match="WriteDisposition"):
        WriteResult("document:1", "created")


def test_batch_write_result_preserves_order_and_summarizes_outcomes():
    batch = BatchWriteResult(
        (
            WriteResult("document:1", WriteDisposition.CREATED),
            WriteResult("document:2", WriteDisposition.UNCHANGED),
            WriteResult("document:3", WriteDisposition.CREATED),
        )
    )

    assert batch.created_ids == ("document:1", "document:3")
    assert batch.unchanged_ids == ("document:2",)


def test_batch_write_result_rejects_duplicate_entity_ids():
    with pytest.raises(ValueError, match="duplicate"):
        BatchWriteResult(
            (
                WriteResult("document:1", WriteDisposition.CREATED),
                WriteResult("document:1", WriteDisposition.UNCHANGED),
            )
        )


def test_repository_errors_share_one_backend_neutral_base():
    for error_type in (
        RepositoryConflictError,
        EntityNotFoundError,
        RepositoryIntegrityError,
        TransactionError,
    ):
        assert issubclass(error_type, RepositoryError)


@pytest.mark.parametrize(
    ("protocol", "methods"),
    (
        (
            DocumentRepository,
            ("get", "get_many", "exists", "list_effective_at", "put", "put_many"),
        ),
        (
            ProvisionRepository,
            (
                "get",
                "get_many",
                "list_by_document",
                "children_of",
                "descendants_of",
                "document_order",
                "put",
                "put_many",
            ),
        ),
        (
            VersionRepository,
            (
                "get",
                "get_many",
                "chain_for",
                "version_at",
                "current_for",
                "put",
                "put_many",
            ),
        ),
        (
            EventRepository,
            (
                "get",
                "get_many",
                "list_by_source_document",
                "list_by_target_document",
                "list_for_provision",
                "put",
                "put_many",
                "is_applied",
                "mark_applied",
            ),
        ),
        (
            TemporalGraphRepository,
            (
                "get",
                "get_many",
                "put",
                "put_many",
                "outgoing",
                "incoming",
                "neighbors",
            ),
        ),
        (ProvenanceRepository, ("for_entity",)),
        (
            SnapshotRepository,
            ("snapshot", "snapshot_document", "valid_provisions"),
        ),
        (
            VectorRepository,
            ("get", "get_many", "put", "put_many", "delete", "search"),
        ),
    ),
)
def test_repository_protocols_are_runtime_checkable(protocol, methods):
    complete = method_stub(*methods)
    incomplete = method_stub(*methods[:-1])

    assert isinstance(complete, protocol)
    assert not isinstance(incomplete, protocol)


def test_unit_of_work_requires_all_authoritative_repositories_and_transaction():
    repositories = {
        "documents": object(),
        "provisions": object(),
        "versions": object(),
        "events": object(),
        "graph": object(),
        "provenance": object(),
        "snapshots": object(),
    }
    complete = method_stub("transaction", **repositories)
    missing_events = repositories.copy()
    missing_events.pop("events")
    incomplete = method_stub("transaction", **missing_events)

    assert isinstance(complete, TemporalUnitOfWork)
    assert not isinstance(incomplete, TemporalUnitOfWork)


def test_existing_snapshot_service_satisfies_snapshot_read_port():
    service = SnapshotService(TemporalState())

    assert isinstance(service, SnapshotRepository)


def test_temporal_query_points_are_explicit_in_port_signatures():
    assert "at" in inspect.signature(DocumentRepository.list_effective_at).parameters
    assert "at" in inspect.signature(VersionRepository.version_at).parameters
    assert "effective_during" in inspect.signature(
        EventRepository.list_for_provision
    ).parameters
    assert "at" in inspect.signature(TemporalGraphRepository.outgoing).parameters
    assert "at" in inspect.signature(SnapshotRepository.snapshot).parameters


def test_version_embedding_is_bound_to_version_time_level_and_provenance():
    record = version_embedding()

    assert record.version_id == "version:clause-3:2"
    assert record.validity.contains(date(2025, 1, 1))
    assert record.level is ProvisionLevel.CLAUSE
    assert record.provenance[0].source_document_id == "document:amending-law"


@pytest.mark.parametrize(
    "vector",
    (
        (),
        (True,),
        (float("nan"),),
        (float("inf"),),
        ("not-a-number",),
    ),
)
def test_version_embedding_rejects_invalid_vectors(vector):
    valid = version_embedding()

    with pytest.raises(ValueError, match="vector"):
        VersionEmbedding(
            id=valid.id,
            version_id=valid.version_id,
            provision_id=valid.provision_id,
            document_id=valid.document_id,
            model=valid.model,
            vector=vector,
            validity=valid.validity,
            level=valid.level,
        )


def test_vector_search_requires_point_in_time_and_valid_filters():
    query = VectorSearchQuery(
        vector=(0.1, 0.2, 0.3),
        at=date(2024, 7, 1),
        limit=5,
        document_ids=("document:law-1",),
        levels=frozenset({ProvisionLevel.ARTICLE, ProvisionLevel.CLAUSE}),
    )

    assert query.at == date(2024, 7, 1)
    assert query.limit == 5

    with pytest.raises(ValueError, match="must be positive"):
        VectorSearchQuery((0.1,), date(2024, 7, 1), limit=0)
    with pytest.raises(ValueError, match="must be a date"):
        VectorSearchQuery((0.1,), "2024-07-01")
    with pytest.raises(ValueError, match="duplicates"):
        VectorSearchQuery(
            (0.1,),
            date(2024, 7, 1),
            document_ids=("document:1", "document:1"),
        )


def test_vector_match_rejects_non_finite_backend_score():
    assert VectorMatch(version_embedding(), 0.91).score == 0.91

    with pytest.raises(ValueError, match="finite"):
        VectorMatch(version_embedding(), float("nan"))

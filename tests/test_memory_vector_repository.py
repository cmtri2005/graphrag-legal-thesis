from dataclasses import replace
from datetime import date

import pytest

from legal_crawler.adapters.memory import MemoryVectorRepository
from legal_crawler.ports import (
    RepositoryConflictError,
    RepositoryIntegrityError,
    VectorRepository,
    VectorSearchQuery,
    VersionEmbedding,
    WriteDisposition,
)
from legal_crawler.temporal import ProvisionLevel, TemporalInterval


def embedding(
    identifier: str,
    vector: tuple[float, ...],
    *,
    model: str = "model-a",
    document_id: str = "document:law",
    level: ProvisionLevel = ProvisionLevel.ARTICLE,
    start: date = date(2020, 1, 1),
    end: date | None = None,
) -> VersionEmbedding:
    return VersionEmbedding(
        identifier,
        f"version:{identifier}",
        f"provision:{identifier}",
        document_id,
        model,
        vector,
        TemporalInterval(start, end),
        level,
    )


def query(
    vector: tuple[float, ...] = (1.0, 0.0),
    *,
    at: date = date(2021, 1, 1),
    model: str = "model-a",
    limit: int = 10,
    documents: tuple[str, ...] = (),
    levels: frozenset[ProvisionLevel] = frozenset(),
) -> VectorSearchQuery:
    return VectorSearchQuery(vector, at, model, limit, documents, levels)


def test_vector_repository_protocol_idempotency_conflict_and_delete():
    repository = MemoryVectorRepository()
    record = embedding("embedding:a", (1.0, 0.0))

    assert isinstance(repository, VectorRepository)
    assert repository.put(record).disposition is WriteDisposition.CREATED
    assert repository.put(record).disposition is WriteDisposition.UNCHANGED
    assert repository.get_many((record.id, "missing")) == {record.id: record}
    with pytest.raises(RepositoryConflictError):
        repository.put(replace(record, vector=(0.0, 1.0)))
    assert repository.delete(record.id)
    assert not repository.delete(record.id)


def test_vector_batch_is_atomic_for_dimension_failure():
    repository = MemoryVectorRepository()
    first = embedding("embedding:a", (1.0, 0.0))
    incompatible = embedding("embedding:b", (1.0, 0.0, 0.0))

    with pytest.raises(RepositoryIntegrityError, match="dimension"):
        repository.put_many((first, incompatible))

    assert repository.get(first.id) is None
    assert repository.put(incompatible).created


def test_search_filters_model_time_document_and_level_before_scoring():
    repository = MemoryVectorRepository()
    expected = embedding("embedding:expected", (1.0, 0.0))
    expired = embedding(
        "embedding:expired", (1.0, 0.0), end=date(2021, 1, 1)
    )
    other_document = embedding(
        "embedding:other-document",
        (1.0, 0.0),
        document_id="document:other",
    )
    other_level = embedding(
        "embedding:clause", (1.0, 0.0), level=ProvisionLevel.CLAUSE
    )
    other_model = embedding(
        "embedding:other-model", (1.0, 0.0), model="model-b"
    )
    repository.put_many(
        (expected, expired, other_document, other_level, other_model)
    )

    matches = repository.search(
        query(
            at=date(2021, 1, 1),
            documents=("document:law",),
            levels=frozenset({ProvisionLevel.ARTICLE}),
        )
    )

    assert tuple(match.record for match in matches) == (expected,)
    assert matches[0].score == pytest.approx(1.0)


def test_search_orders_by_score_then_deterministic_id_and_applies_limit():
    repository = MemoryVectorRepository()
    repository.put_many(
        (
            embedding("embedding:b", (1.0, 0.0)),
            embedding("embedding:a", (1.0, 0.0)),
            embedding("embedding:c", (0.0, 1.0)),
        )
    )

    matches = repository.search(query(limit=2))

    assert tuple(match.record.id for match in matches) == (
        "embedding:a",
        "embedding:b",
    )


def test_search_rejects_wrong_dimension_for_known_model():
    repository = MemoryVectorRepository()
    repository.put(embedding("embedding:a", (1.0, 0.0)))

    with pytest.raises(RepositoryIntegrityError, match="dimension"):
        repository.search(query((1.0, 0.0, 0.0)))

"""Deterministic in-memory implementation of version-aware vector search."""
from __future__ import annotations

import math
from collections.abc import Iterable, Sequence

from legal_crawler.ports.repositories import (
    BatchWriteResult,
    RepositoryConflictError,
    RepositoryIntegrityError,
    WriteDisposition,
    WriteResult,
)
from legal_crawler.ports.vector import (
    VectorMatch,
    VectorSearchQuery,
    VersionEmbedding,
)


class MemoryVectorRepository:
    def __init__(self) -> None:
        self._records: dict[str, VersionEmbedding] = {}
        self._dimensions: dict[str, int] = {}

    def get(self, embedding_id: str) -> VersionEmbedding | None:
        return self._records.get(embedding_id)

    def get_many(
        self, embedding_ids: Sequence[str]
    ) -> dict[str, VersionEmbedding]:
        return {
            embedding_id: self._records[embedding_id]
            for embedding_id in embedding_ids
            if embedding_id in self._records
        }

    def put(self, record: VersionEmbedding) -> WriteResult:
        existing = self.get(record.id)
        if existing is not None:
            if existing != record:
                raise RepositoryConflictError(
                    f"embedding id {record.id} already has different content"
                )
            return WriteResult(record.id, WriteDisposition.UNCHANGED)
        expected = self._dimensions.get(record.model)
        if expected is not None and expected != len(record.vector):
            raise RepositoryIntegrityError(
                f"embedding model {record.model} expects dimension {expected}, "
                f"got {len(record.vector)}"
            )
        self._dimensions.setdefault(record.model, len(record.vector))
        self._records[record.id] = record
        return WriteResult(record.id, WriteDisposition.CREATED)

    def put_many(self, records: Iterable[VersionEmbedding]) -> BatchWriteResult:
        items = tuple(records)
        ids = tuple(item.id for item in items)
        if len(ids) != len(set(ids)):
            raise RepositoryIntegrityError(
                "embedding batch contains duplicate deterministic IDs"
            )
        previous_records = self._records.copy()
        previous_dimensions = self._dimensions.copy()
        try:
            results = tuple(self.put(item) for item in items)
        except BaseException:
            self._records.clear()
            self._records.update(previous_records)
            self._dimensions.clear()
            self._dimensions.update(previous_dimensions)
            raise
        return BatchWriteResult(results)

    def delete(self, embedding_id: str) -> bool:
        return self._records.pop(embedding_id, None) is not None

    def search(self, query: VectorSearchQuery) -> tuple[VectorMatch, ...]:
        expected = self._dimensions.get(query.model)
        if expected is not None and expected != len(query.vector):
            raise RepositoryIntegrityError(
                f"embedding model {query.model} expects dimension {expected}, "
                f"got {len(query.vector)}"
            )
        document_filter = set(query.document_ids)
        matches = [
            VectorMatch(record, _cosine(query.vector, record.vector))
            for record in self._records.values()
            if record.model == query.model
            and record.validity.contains(query.at)
            and (not document_filter or record.document_id in document_filter)
            and (not query.levels or record.level in query.levels)
        ]
        matches.sort(key=lambda item: (-item.score, item.record.id))
        return tuple(matches[: query.limit])


def _cosine(left: tuple[float, ...], right: tuple[float, ...]) -> float:
    numerator = sum(a * b for a, b in zip(left, right))
    left_norm = math.sqrt(sum(item * item for item in left))
    right_norm = math.sqrt(sum(item * item for item in right))
    return numerator / (left_norm * right_norm)

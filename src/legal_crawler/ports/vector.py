"""Minimal version-aware vector storage port.

The richer query/evidence contract belongs to the query layer. This module only
ensures embeddings cannot be detached from a concrete provision version and
its temporal metadata.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import date
from typing import Any, Iterable, Mapping, Protocol, Sequence, runtime_checkable

from legal_crawler.temporal.models import (
    Provenance,
    ProvisionLevel,
    TemporalInterval,
)

from .repositories import BatchWriteResult, WriteResult


@dataclass(frozen=True, slots=True)
class VersionEmbedding:
    """One embedding tied to an exact provision version and model."""

    id: str
    version_id: str
    provision_id: str
    document_id: str
    model: str
    vector: tuple[float, ...]
    validity: TemporalInterval
    level: ProvisionLevel
    provenance: tuple[Provenance, ...] = ()
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for value, name in (
            (self.id, "embedding id"),
            (self.version_id, "embedding version_id"),
            (self.provision_id, "embedding provision_id"),
            (self.document_id, "embedding document_id"),
            (self.model, "embedding model"),
        ):
            _required(value, name)
        _vector(self.vector, "embedding vector")
        if not isinstance(self.validity, TemporalInterval):
            raise ValueError("embedding validity must be a TemporalInterval")
        if not isinstance(self.level, ProvisionLevel):
            raise ValueError("embedding level must be a ProvisionLevel")
        if not isinstance(self.provenance, tuple) or any(
            not isinstance(item, Provenance) for item in self.provenance
        ):
            raise ValueError("embedding provenance must be a tuple of Provenance")
        if not isinstance(self.metadata, Mapping):
            raise ValueError("embedding metadata must be a mapping")


@dataclass(frozen=True, slots=True)
class VectorSearchQuery:
    """Backend-neutral temporal filter for nearest-neighbor search."""

    vector: tuple[float, ...]
    at: date
    model: str
    limit: int = 10
    document_ids: tuple[str, ...] = ()
    levels: frozenset[ProvisionLevel] = frozenset()

    def __post_init__(self) -> None:
        _vector(self.vector, "query vector")
        if type(self.at) is not date:
            raise ValueError("vector query at must be a date")
        _required(self.model, "vector query model")
        if isinstance(self.limit, bool) or not isinstance(self.limit, int):
            raise ValueError("vector query limit must be an integer")
        if self.limit < 1:
            raise ValueError("vector query limit must be positive")
        if not isinstance(self.document_ids, tuple):
            raise ValueError("vector query document_ids must be a tuple")
        for document_id in self.document_ids:
            _required(document_id, "vector query document_id")
        if len(self.document_ids) != len(set(self.document_ids)):
            raise ValueError("vector query document_ids must not contain duplicates")
        if not isinstance(self.levels, frozenset) or any(
            not isinstance(level, ProvisionLevel) for level in self.levels
        ):
            raise ValueError("vector query levels must contain ProvisionLevel values")


@dataclass(frozen=True, slots=True)
class VectorMatch:
    """One backend score and its complete version-aware record."""

    record: VersionEmbedding
    score: float

    def __post_init__(self) -> None:
        if not isinstance(self.record, VersionEmbedding):
            raise ValueError("vector match record must be a VersionEmbedding")
        if isinstance(self.score, bool) or not isinstance(self.score, (int, float)):
            raise ValueError("vector match score must be a number")
        if not math.isfinite(float(self.score)):
            raise ValueError("vector match score must be finite")


@runtime_checkable
class VectorRepository(Protocol):
    """Version-aware embedding persistence and temporal similarity search."""

    def get(self, embedding_id: str) -> VersionEmbedding | None:
        ...

    def get_many(
        self, embedding_ids: Sequence[str]
    ) -> Mapping[str, VersionEmbedding]:
        ...

    def put(self, record: VersionEmbedding) -> WriteResult:
        ...

    def put_many(self, records: Iterable[VersionEmbedding]) -> BatchWriteResult:
        ...

    def delete(self, embedding_id: str) -> bool:
        """Delete one derived embedding; domain entities are unaffected."""
        ...

    def search(self, query: VectorSearchQuery) -> tuple[VectorMatch, ...]:
        """Apply query temporal filters before returning at most ``limit`` hits."""
        ...


def _required(value: Any, name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must not be empty")


def _vector(value: Any, name: str) -> None:
    if not isinstance(value, tuple) or not value:
        raise ValueError(f"{name} must be a non-empty tuple")
    for component in value:
        if isinstance(component, bool) or not isinstance(component, (int, float)):
            raise ValueError(f"{name} components must be numbers")
        if not math.isfinite(float(component)):
            raise ValueError(f"{name} components must be finite")
    if not any(float(component) != 0.0 for component in value):
        raise ValueError(f"{name} must not be a zero vector")

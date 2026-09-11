"""Public storage boundaries for legal domain services and adapters."""

from .repositories import (
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
    VersionRepository,
    WriteDisposition,
    WriteResult,
)
from .vector import (
    VectorMatch,
    VectorRepository,
    VectorSearchQuery,
    VersionEmbedding,
)

__all__ = [
    "BatchWriteResult",
    "DocumentRepository",
    "EntityNotFoundError",
    "EventRepository",
    "ProvenanceRepository",
    "ProvisionRepository",
    "RepositoryConflictError",
    "RepositoryError",
    "RepositoryIntegrityError",
    "SnapshotRepository",
    "TemporalGraphRepository",
    "TemporalUnitOfWork",
    "TransactionError",
    "VectorMatch",
    "VectorRepository",
    "VectorSearchQuery",
    "VersionEmbedding",
    "VersionRepository",
    "WriteDisposition",
    "WriteResult",
]


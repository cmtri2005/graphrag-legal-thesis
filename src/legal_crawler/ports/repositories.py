"""Storage-neutral repository contracts for the temporal legal domain.

Ports expose domain objects and deterministic IDs, never driver sessions,
database-native IDs or backend query languages. Concrete adapters must retain
the temporal and idempotency rules documented by these protocols.
"""
from __future__ import annotations

from contextlib import AbstractContextManager
from dataclasses import dataclass
from datetime import date
from enum import Enum
from typing import Iterable, Mapping, Protocol, Sequence, runtime_checkable

from legal_crawler.temporal.models import (
    GraphEdge,
    LegalDocument,
    LegalEvent,
    Provenance,
    Provision,
    ProvisionLevel,
    ProvisionVersion,
    RelationType,
    TemporalInterval,
)
from legal_crawler.temporal.snapshot import SnapshotResult
from legal_crawler.temporal.version_chain import VersionChain


class RepositoryError(RuntimeError):
    """Base class for failures exposed by any repository adapter."""


class RepositoryConflictError(RepositoryError):
    """A deterministic ID already exists with different domain content."""


class EntityNotFoundError(RepositoryError):
    """An operation requires a domain entity that does not exist."""


class RepositoryIntegrityError(RepositoryError):
    """Persisted entities would violate a domain or temporal invariant."""


class TransactionError(RepositoryError):
    """A transaction could not begin, commit or roll back safely."""


class WriteDisposition(str, Enum):
    """Outcome required from every idempotent repository write."""

    CREATED = "created"
    UNCHANGED = "unchanged"


@dataclass(frozen=True, slots=True)
class WriteResult:
    """Result of writing one entity by deterministic domain ID."""

    entity_id: str
    disposition: WriteDisposition

    def __post_init__(self) -> None:
        if not isinstance(self.entity_id, str) or not self.entity_id.strip():
            raise ValueError("write result entity_id must not be empty")
        if not isinstance(self.disposition, WriteDisposition):
            raise ValueError("write result disposition must be WriteDisposition")

    @property
    def created(self) -> bool:
        return self.disposition is WriteDisposition.CREATED


@dataclass(frozen=True, slots=True)
class BatchWriteResult:
    """Ordered outcomes for one batch write operation."""

    results: tuple[WriteResult, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.results, tuple) or any(
            not isinstance(item, WriteResult) for item in self.results
        ):
            raise ValueError("batch results must be a tuple of WriteResult values")
        ids = tuple(item.entity_id for item in self.results)
        if len(ids) != len(set(ids)):
            raise ValueError("batch results must not contain duplicate entity IDs")

    @property
    def created_ids(self) -> tuple[str, ...]:
        return tuple(item.entity_id for item in self.results if item.created)

    @property
    def unchanged_ids(self) -> tuple[str, ...]:
        return tuple(item.entity_id for item in self.results if not item.created)


@runtime_checkable
class DocumentRepository(Protocol):
    """Documents, including historical and expired source documents."""

    def get(self, document_id: str) -> LegalDocument | None:
        """Return a document by domain ID, or ``None`` when absent."""
        ...

    def get_many(self, document_ids: Sequence[str]) -> Mapping[str, LegalDocument]:
        """Return found documents keyed by requested ID; omit missing IDs."""
        ...

    def exists(self, document_id: str) -> bool:
        ...

    def list_effective_at(self, at: date) -> tuple[LegalDocument, ...]:
        """Return documents whose document-level interval contains ``at``."""
        ...

    def put(self, document: LegalDocument) -> WriteResult:
        """Create or confirm an exact duplicate; conflicting reuse must fail."""
        ...

    def put_many(self, documents: Iterable[LegalDocument]) -> BatchWriteResult:
        """Apply the same idempotency contract to a batch."""
        ...


@runtime_checkable
class ProvisionRepository(Protocol):
    """Stable provision identities and their legal structure ordering."""

    def get(self, provision_id: str) -> Provision | None:
        ...

    def get_many(self, provision_ids: Sequence[str]) -> Mapping[str, Provision]:
        ...

    def list_by_document(self, document_id: str) -> tuple[Provision, ...]:
        ...

    def children_of(
        self, parent_id: str | None, document_id: str
    ) -> tuple[Provision, ...]:
        ...

    def descendants_of(self, provision_id: str) -> tuple[Provision, ...]:
        ...

    def document_order(self, document_id: str) -> tuple[Provision, ...]:
        """Return depth-first legal order, including insertion anchors."""
        ...

    def put(self, provision: Provision) -> WriteResult:
        ...

    def put_many(self, provisions: Iterable[Provision]) -> BatchWriteResult:
        ...


@runtime_checkable
class VersionRepository(Protocol):
    """Non-overlapping textual versions of stable legal provisions."""

    def get(self, version_id: str) -> ProvisionVersion | None:
        ...

    def get_many(
        self, version_ids: Sequence[str]
    ) -> Mapping[str, ProvisionVersion]:
        ...

    def chain_for(self, provision_id: str) -> VersionChain | None:
        """Return a detached chain preserving ``[start, end)`` semantics.

        Mutating the returned domain chain must not bypass repository writes.
        """
        ...

    def version_at(self, provision_id: str, at: date) -> ProvisionVersion | None:
        ...

    def current_for(self, provision_id: str) -> ProvisionVersion | None:
        ...

    def put(self, version: ProvisionVersion) -> WriteResult:
        """Reject overlaps, ordinal conflicts and conflicting IDs."""
        ...

    def put_many(self, versions: Iterable[ProvisionVersion]) -> BatchWriteResult:
        ...


@runtime_checkable
class EventRepository(Protocol):
    """Extracted legal events and their application state."""

    def get(self, event_id: str) -> LegalEvent | None:
        ...

    def get_many(self, event_ids: Sequence[str]) -> Mapping[str, LegalEvent]:
        ...

    def list_by_source_document(
        self,
        document_id: str,
        *,
        effective_during: TemporalInterval | None = None,
    ) -> tuple[LegalEvent, ...]:
        ...

    def list_by_target_document(
        self,
        document_id: str,
        *,
        effective_during: TemporalInterval | None = None,
    ) -> tuple[LegalEvent, ...]:
        ...

    def list_for_provision(
        self,
        provision_id: str,
        *,
        effective_during: TemporalInterval | None = None,
    ) -> tuple[LegalEvent, ...]:
        ...

    def put(self, event: LegalEvent) -> WriteResult:
        ...

    def put_many(self, events: Iterable[LegalEvent]) -> BatchWriteResult:
        ...

    def is_applied(self, event_id: str) -> bool:
        ...

    def mark_applied(self, event_id: str) -> bool:
        """Mark an existing event in its transaction.

        Return ``True`` for the first transition and ``False`` when it was
        already marked. A missing event must raise ``EntityNotFoundError``.
        """
        ...


@runtime_checkable
class TemporalGraphRepository(Protocol):
    """Typed graph edges with optional validity intervals."""

    def get(self, edge_id: str) -> GraphEdge | None:
        ...

    def get_many(self, edge_ids: Sequence[str]) -> Mapping[str, GraphEdge]:
        ...

    def put(self, edge: GraphEdge) -> WriteResult:
        ...

    def put_many(self, edges: Iterable[GraphEdge]) -> BatchWriteResult:
        ...

    def outgoing(
        self,
        node_id: str,
        *,
        relations: frozenset[RelationType] | None = None,
        at: date | None = None,
    ) -> tuple[GraphEdge, ...]:
        ...

    def incoming(
        self,
        node_id: str,
        *,
        relations: frozenset[RelationType] | None = None,
        at: date | None = None,
    ) -> tuple[GraphEdge, ...]:
        ...

    def neighbors(
        self,
        node_id: str,
        *,
        relations: frozenset[RelationType] | None = None,
        at: date | None = None,
    ) -> tuple[GraphEdge, ...]:
        ...


@runtime_checkable
class ProvenanceRepository(Protocol):
    """Evidence lookup independent of the entity's storage representation."""

    def for_entity(self, entity_id: str) -> tuple[Provenance, ...]:
        ...


@runtime_checkable
class SnapshotRepository(Protocol):
    """Point-in-time read model consumed by retrieval and verification."""

    def snapshot(self, provision_id: str, at: date) -> SnapshotResult:
        ...

    def snapshot_document(
        self,
        document_id: str,
        at: date,
        *,
        levels: frozenset[ProvisionLevel] | None = None,
        valid_only: bool = False,
    ) -> tuple[SnapshotResult, ...]:
        ...

    def valid_provisions(
        self,
        document_id: str,
        at: date,
        *,
        levels: frozenset[ProvisionLevel] | None = None,
    ) -> tuple[SnapshotResult, ...]:
        ...


@runtime_checkable
class TemporalUnitOfWork(Protocol):
    """Atomic boundary for applying one legal event across repositories.

    Implementations must roll back every write when the context exits with an
    exception. Event changes and ``mark_applied`` must commit together.
    """

    documents: DocumentRepository
    provisions: ProvisionRepository
    versions: VersionRepository
    events: EventRepository
    graph: TemporalGraphRepository
    provenance: ProvenanceRepository
    snapshots: SnapshotRepository

    def transaction(self) -> AbstractContextManager[None]:
        ...

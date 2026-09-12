"""Transactional composition of authoritative in-memory repositories."""
from __future__ import annotations

from contextlib import contextmanager
from collections.abc import Iterator

from legal_crawler.ports.repositories import TransactionError

from .repositories import (
    MemoryDocumentRepository,
    MemoryEventRepository,
    MemoryProvenanceRepository,
    MemoryProvisionRepository,
    MemoryTemporalGraphRepository,
    MemoryVersionRepository,
)
from .snapshot import MemorySnapshotRepository
from .store import MemoryStore


class MemoryUnitOfWork:
    """Repository bundle with rollback on every exceptional transaction exit."""

    def __init__(self, store: MemoryStore | None = None) -> None:
        self.store = store or MemoryStore()
        self.documents = MemoryDocumentRepository(self.store)
        self.provisions = MemoryProvisionRepository(self.store)
        self.versions = MemoryVersionRepository(self.store)
        self.events = MemoryEventRepository(self.store)
        self.graph = MemoryTemporalGraphRepository(self.store)
        self.provenance = MemoryProvenanceRepository(self.store)
        self.snapshots = MemorySnapshotRepository(self.store)
        self._transaction_active = False

    @contextmanager
    def transaction(self) -> Iterator[None]:
        if self._transaction_active:
            raise TransactionError("nested memory transactions are not supported")
        snapshot = self.store.snapshot()
        self._transaction_active = True
        try:
            yield None
        except BaseException:
            self.store.restore(snapshot)
            raise
        finally:
            self._transaction_active = False


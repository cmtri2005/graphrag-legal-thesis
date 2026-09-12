"""Live snapshot read adapter over the shared in-memory temporal state."""
from __future__ import annotations

from datetime import date

from legal_crawler.temporal.models import ProvisionLevel
from legal_crawler.temporal.snapshot import SnapshotResult, SnapshotService

from .store import MemoryStore


class MemorySnapshotRepository:
    def __init__(self, store: MemoryStore) -> None:
        self._service = SnapshotService(store.state)

    def snapshot(self, provision_id: str, at: date) -> SnapshotResult:
        return self._service.snapshot(provision_id, at)

    def snapshot_document(
        self,
        document_id: str,
        at: date,
        *,
        levels: frozenset[ProvisionLevel] | None = None,
        valid_only: bool = False,
    ) -> tuple[SnapshotResult, ...]:
        return self._service.snapshot_document(
            document_id,
            at,
            levels=levels,
            valid_only=valid_only,
        )

    def valid_provisions(
        self,
        document_id: str,
        at: date,
        *,
        levels: frozenset[ProvisionLevel] | None = None,
    ) -> tuple[SnapshotResult, ...]:
        return self._service.valid_provisions(document_id, at, levels=levels)


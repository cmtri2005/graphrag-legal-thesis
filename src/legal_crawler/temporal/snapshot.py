"""Point-in-time views over provisions and complete legal documents."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from .models import LegalEvent, Provenance, Provision, ProvisionLevel, ProvisionVersion
from .state import TemporalState
from .validity import ValidityResult, ValidityService


@dataclass(frozen=True, slots=True)
class SnapshotResult:
    provision: Provision | None
    at: date
    validity: ValidityResult
    version: ProvisionVersion | None = None
    created_by_event: LegalEvent | None = None
    ended_by_event: LegalEvent | None = None
    caused_by_event: LegalEvent | None = None
    provenance: tuple[Provenance, ...] = ()
    warnings: tuple[str, ...] = ()

    @property
    def text(self) -> str | None:
        return self.version.text if self.version and self.validity.valid else None


class SnapshotService:
    """Resolve deterministic legal text as it stood at a requested date."""

    def __init__(self, state: TemporalState) -> None:
        self._state = state
        self._validity = ValidityService(state)

    def snapshot(self, provision_id: str, at: date) -> SnapshotResult:
        validity = self._validity.check(provision_id, at)
        provision = self._state.provision(provision_id)
        version = validity.version if validity.valid else None
        relevant_version = validity.version
        warnings: list[str] = []
        if validity.valid and version is not None and not version.provenance:
            warnings.append("version_has_no_provenance")
        return SnapshotResult(
            provision=provision,
            at=at,
            validity=validity,
            version=version,
            created_by_event=self._state.event(
                relevant_version.created_by_event_id if relevant_version else None
            ),
            ended_by_event=self._state.event(
                relevant_version.ended_by_event_id if relevant_version else None
            ),
            caused_by_event=self._state.event(validity.caused_by_event_id),
            provenance=version.provenance if version else (),
            warnings=tuple(warnings),
        )

    def snapshot_document(
        self,
        document_id: str,
        at: date,
        *,
        levels: frozenset[ProvisionLevel] | None = None,
        valid_only: bool = False,
    ) -> tuple[SnapshotResult, ...]:
        results: list[SnapshotResult] = []
        for provision in self._state.document_order(document_id):
            if levels is not None and provision.level not in levels:
                continue
            result = self.snapshot(provision.id, at)
            if not valid_only or result.validity.valid:
                results.append(result)
        return tuple(results)

    def valid_provisions(
        self,
        document_id: str,
        at: date,
        *,
        levels: frozenset[ProvisionLevel] | None = None,
    ) -> tuple[SnapshotResult, ...]:
        return self.snapshot_document(
            document_id, at, levels=levels, valid_only=True
        )

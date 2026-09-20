"""Provision-level validity with propagation through the legal structure tree."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from enum import Enum

from .models import LegalOperation, ProvisionVersion
from .state import TemporalState


class InvalidityReason(str, Enum):
    UNKNOWN_PROVISION = "unknown_provision"
    UNKNOWN_DOCUMENT = "unknown_document"
    DOCUMENT_NOT_YET_EFFECTIVE = "document_not_yet_effective"
    DOCUMENT_EXPIRED = "document_expired"
    PROVISION_NOT_YET_EFFECTIVE = "provision_not_yet_effective"
    NO_VERSION_HELD = "no_version_held"
    PROVISION_REPEALED = "provision_repealed"
    INACTIVE_GAP = "inactive_gap"
    PARENT_INVALID = "parent_invalid"
    STRUCTURE_CYCLE = "structure_cycle"


@dataclass(frozen=True, slots=True)
class ValidityResult:
    provision_id: str
    at: date
    valid: bool
    version: ProvisionVersion | None = None
    reason: InvalidityReason | None = None
    invalid_ancestor_id: str | None = None
    caused_by_event_id: str | None = None


class ValidityService:
    """Evaluate ``valid(u, t)`` using both local and parent validity."""

    def __init__(self, state: TemporalState) -> None:
        self._state = state

    def check(self, provision_id: str, at: date) -> ValidityResult:
        return self._check(provision_id, at, path=())

    def is_valid(self, provision_id: str, at: date) -> bool:
        return self.check(provision_id, at).valid

    def valid_descendants(self, provision_id: str, at: date) -> tuple[str, ...]:
        return tuple(
            item.id
            for item in self._state.descendants_of(provision_id)
            if self.is_valid(item.id, at)
        )

    def _check(
        self,
        provision_id: str,
        at: date,
        *,
        path: tuple[str, ...],
        as_ancestor: bool = False,
    ) -> ValidityResult:
        if provision_id in path:
            return ValidityResult(
                provision_id,
                at,
                False,
                reason=InvalidityReason.STRUCTURE_CYCLE,
                invalid_ancestor_id=provision_id,
            )
        provision = self._state.provision(provision_id)
        if provision is None:
            return ValidityResult(
                provision_id, at, False, reason=InvalidityReason.UNKNOWN_PROVISION
            )
        document = self._state.document(provision.document_id)
        if document is None:
            return ValidityResult(
                provision_id, at, False, reason=InvalidityReason.UNKNOWN_DOCUMENT
            )
        if document.effective_from is not None and at < document.effective_from:
            return ValidityResult(
                provision_id,
                at,
                False,
                reason=InvalidityReason.DOCUMENT_NOT_YET_EFFECTIVE,
            )
        if document.effective_to is not None and at >= document.effective_to:
            return ValidityResult(
                provision_id, at, False, reason=InvalidityReason.DOCUMENT_EXPIRED
            )

        chain = self._state.chain(provision_id)
        version = chain.at(at) if chain else None
        # A node we hold no text for says nothing about its children. Chương and
        # Mục are headings that carry no words of their own, and an Điều whose
        # text the corpus lacks is missing data, not data to the contrary
        # (master plan §11). Such a node is transparent to propagation, and
        # still answers NO_VERSION_HELD about itself.
        never_had_text = not (chain and chain.versions)
        if version is None and not (as_ancestor and never_had_text):
            return self._missing_version_result(provision_id, at, chain)

        if provision.parent_id is not None:
            parent = self._check(
                provision.parent_id,
                at,
                path=(*path, provision_id),
                as_ancestor=True,
            )
            if not parent.valid:
                ancestor = parent.invalid_ancestor_id or parent.provision_id
                return ValidityResult(
                    provision_id,
                    at,
                    False,
                    version=version,
                    reason=(
                        InvalidityReason.STRUCTURE_CYCLE
                        if parent.reason is InvalidityReason.STRUCTURE_CYCLE
                        else InvalidityReason.PARENT_INVALID
                    ),
                    invalid_ancestor_id=ancestor,
                    caused_by_event_id=parent.caused_by_event_id,
                )

        return ValidityResult(provision_id, at, True, version=version)

    def _missing_version_result(
        self,
        provision_id: str,
        at: date,
        chain,
    ) -> ValidityResult:
        versions = chain.versions if chain else ()
        if not versions:
            return ValidityResult(
                provision_id, at, False, reason=InvalidityReason.NO_VERSION_HELD
            )
        if at < versions[0].validity.start:
            return ValidityResult(
                provision_id,
                at,
                False,
                reason=InvalidityReason.PROVISION_NOT_YET_EFFECTIVE,
            )

        previous = next(
            (
                version
                for version in reversed(versions)
                if version.validity.end is not None and version.validity.end <= at
            ),
            None,
        )
        event = self._state.event(previous.ended_by_event_id) if previous else None
        if event and event.operation is LegalOperation.REPEAL:
            return ValidityResult(
                provision_id,
                at,
                False,
                version=previous,
                reason=InvalidityReason.PROVISION_REPEALED,
                caused_by_event_id=event.id,
            )
        return ValidityResult(
            provision_id,
            at,
            False,
            version=previous,
            reason=InvalidityReason.INACTIVE_GAP,
            caused_by_event_id=previous.ended_by_event_id if previous else None,
        )

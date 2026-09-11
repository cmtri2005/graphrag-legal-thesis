"""In-memory version-chain invariants and point-in-time lookup.

This module owns the temporal rules for versions of one stable provision.  It
does not know where versions are stored and does not apply legal events; those
concerns are handled by repository adapters and the event applier respectively.
"""
from __future__ import annotations

from collections.abc import Iterable, Iterator
from dataclasses import replace
from datetime import date

from .models import ProvisionVersion, TemporalInterval


class VersionChainError(ValueError):
    """Base class for an invalid operation on a provision's version chain."""


class ProvisionMismatchError(VersionChainError):
    """A version belongs to a different provision."""


class DuplicateVersionError(VersionChainError):
    """A version conflicts with an ID or ordinal already in the chain."""


class OverlappingVersionError(VersionChainError):
    """Two textual versions claim validity at the same time."""


class NoCurrentVersionError(VersionChainError):
    """The chain has no open-ended version to close."""


class VersionChain:
    """Ordered, non-overlapping versions of one stable legal provision."""

    def __init__(
        self,
        provision_id: str,
        versions: Iterable[ProvisionVersion] = (),
    ) -> None:
        if not provision_id:
            raise ValueError("provision_id must not be empty")
        self.provision_id = provision_id
        self._versions: list[ProvisionVersion] = []
        for version in versions:
            if self._validate_candidate(version):
                self._versions.append(version)
        self._sort()
        self.assert_consistent()

    def __len__(self) -> int:
        return len(self._versions)

    def __iter__(self) -> Iterator[ProvisionVersion]:
        return iter(self.versions)

    @property
    def versions(self) -> tuple[ProvisionVersion, ...]:
        """Versions in validity-start order, exposed as an immutable tuple."""
        return tuple(self._versions)

    def add(self, version: ProvisionVersion) -> bool:
        """Add a version while preserving chain invariants.

        Returns ``False`` when the exact same version is already present. This
        makes ingestion idempotent without hiding a conflicting reuse of the
        same ID or ordinal.
        """
        if not self._validate_candidate(version):
            return False
        previous = self._versions.copy()
        self._versions.append(version)
        self._sort()
        try:
            self.assert_consistent()
        except VersionChainError:
            self._versions = previous
            raise
        return True

    def _validate_candidate(self, version: ProvisionVersion) -> bool:
        if version.provision_id != self.provision_id:
            raise ProvisionMismatchError(
                f"version belongs to {version.provision_id!r}, expected {self.provision_id!r}"
            )

        for existing in self._versions:
            if existing == version:
                return False
            if existing.id == version.id:
                raise DuplicateVersionError(f"version id already exists: {version.id}")
            if existing.ordinal == version.ordinal:
                raise DuplicateVersionError(
                    f"version ordinal already exists: {version.ordinal}"
                )
            if existing.validity.overlaps(version.validity):
                raise OverlappingVersionError(
                    f"version {version.id} overlaps existing version {existing.id}"
                )
        return True

    def _sort(self) -> None:
        self._versions.sort(key=lambda item: (item.validity.start, item.ordinal, item.id))

    def at(self, query_date: date) -> ProvisionVersion | None:
        """Return the unique version valid at ``query_date``, if one exists."""
        for version in self._versions:
            if version.validity.start > query_date:
                break
            if version.is_valid_at(query_date):
                return version
        return None

    def current(self) -> ProvisionVersion | None:
        """Return the open-ended version, or ``None`` after repeal/no creation."""
        return next(
            (version for version in reversed(self._versions) if version.validity.end is None),
            None,
        )

    def close_current(self, effective_on: date) -> ProvisionVersion:
        """End the open version at ``effective_on`` and return its new value."""
        current = self.current()
        if current is None:
            raise NoCurrentVersionError("version chain has no open-ended current version")
        if effective_on <= current.validity.start:
            raise VersionChainError(
                "a version must remain valid for at least one day before it is closed"
            )

        closed = replace(
            current,
            validity=TemporalInterval(current.validity.start, effective_on),
        )
        index = self._versions.index(current)
        self._versions[index] = closed
        self.assert_consistent()
        return closed

    def assert_consistent(self) -> None:
        """Validate IDs, ordinals, order and non-overlapping intervals."""
        ids = [version.id for version in self._versions]
        if len(ids) != len(set(ids)):
            raise DuplicateVersionError("version ids must be unique")

        ordinals = sorted(version.ordinal for version in self._versions)
        if ordinals != list(range(1, len(self._versions) + 1)):
            raise DuplicateVersionError("version ordinals must be contiguous starting at 1")

        for version in self._versions:
            if version.provision_id != self.provision_id:
                raise ProvisionMismatchError(
                    f"version {version.id} belongs to another provision"
                )

        for previous, following in zip(self._versions, self._versions[1:]):
            if previous.validity.start > following.validity.start:
                raise VersionChainError("versions are not ordered by validity start")
            if previous.validity.overlaps(following.validity):
                raise OverlappingVersionError(
                    f"version {previous.id} overlaps version {following.id}"
                )

"""Storage-independent contracts for extracting legal amendment events.

These models preserve the distinction between source evidence, a textual legal
reference, and a resolved domain identifier. Ambiguous candidates remain
explicit review data and cannot be materialized into an applicable event.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from enum import Enum
from typing import Any, Mapping

from legal_crawler.temporal.models import (
    EventStatus,
    ExtractionMethod,
    LegalEvent,
    LegalOperation,
    Provenance,
    ProvisionInsertion,
    ProvisionLevel,
    TextUpdate,
)


class ExtractionModelError(ValueError):
    """An extraction object violates its structural contract."""


class EventMaterializationError(ExtractionModelError):
    """An extraction result is not safe to convert into a legal event."""


class TargetScope(str, Enum):
    """How much of the resolved legal structure a reference denotes."""

    EXACT = "exact"
    SUBTREE = "subtree"
    DOCUMENT = "document"


class ResolutionStatus(str, Enum):
    """Whether a textual target has one accepted domain resolution."""

    RESOLVED = "resolved"
    NEEDS_REVIEW = "needs_review"
    UNRESOLVED = "unresolved"


class ExtractionStatus(str, Enum):
    """Review state of the complete extraction result."""

    READY = "ready"
    NEEDS_REVIEW = "needs_review"
    REJECTED = "rejected"


class WarningSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


class WarningCode(str, Enum):
    """Stable codes for review queues and later extraction evaluation."""

    MISSING_EFFECTIVE_DATE = "missing_effective_date"
    UNKNOWN_OPERATION = "unknown_operation"
    UNKNOWN_TARGET_DOCUMENT = "unknown_target_document"
    TARGET_NOT_FOUND = "target_not_found"
    AMBIGUOUS_TARGET = "ambiguous_target"
    INCOMPLETE_LOCATOR = "incomplete_locator"
    UNRESOLVED_INSERTION_ANCHOR = "unresolved_insertion_anchor"
    MISSING_RESULTING_TEXT = "missing_resulting_text"
    LOW_CONFIDENCE = "low_confidence"
    SOURCE_SPAN_MISMATCH = "source_span_mismatch"


@dataclass(frozen=True, slots=True)
class SourceSpan:
    """Half-open character offsets ``[start, end)`` in a source provision."""

    start: int
    end: int

    def __post_init__(self) -> None:
        if isinstance(self.start, bool) or isinstance(self.end, bool):
            raise ExtractionModelError("source span offsets must be integers")
        if not isinstance(self.start, int) or not isinstance(self.end, int):
            raise ExtractionModelError("source span offsets must be integers")
        if self.start < 0:
            raise ExtractionModelError("source span start must not be negative")
        if self.end <= self.start:
            raise ExtractionModelError("source span end must be later than start")

    def extract_from(self, source_text: str) -> str:
        """Return the covered text, rejecting offsets outside the source."""
        if self.end > len(source_text):
            raise ExtractionModelError("source span exceeds source text length")
        return source_text[self.start : self.end]


@dataclass(frozen=True, slots=True)
class RawAmendmentMention:
    """Verbatim amendment evidence found in one source provision."""

    id: str
    source_document_id: str
    text: str
    source_provision_id: str | None = None
    span: SourceSpan | None = None
    provenance: tuple[Provenance, ...] = ()

    def __post_init__(self) -> None:
        _require_text(self.id, "mention id")
        _require_text(self.source_document_id, "mention source_document_id")
        _require_text(self.text, "mention text")
        if self.source_provision_id is not None:
            _require_text(
                self.source_provision_id, "mention source_provision_id"
            )
        if self.span is not None and not isinstance(self.span, SourceSpan):
            raise ExtractionModelError("mention span must be a SourceSpan")
        _require_tuple_items(self.provenance, Provenance, "mention provenance")
        for item in self.provenance:
            if item.source_document_id != self.source_document_id:
                raise ExtractionModelError(
                    "mention provenance must refer to its source document"
                )


@dataclass(frozen=True, slots=True)
class ProvisionReferencePart:
    """One normalized component such as Điều 6, Khoản 3 or Điểm d."""

    level: ProvisionLevel
    label: str

    def __post_init__(self) -> None:
        _require_enum(self.level, ProvisionLevel, "provision reference level")
        _require_text(self.label, "provision reference label")


_LEVEL_ORDER = {
    ProvisionLevel.PART: 0,
    ProvisionLevel.CHAPTER: 1,
    ProvisionLevel.SECTION: 2,
    ProvisionLevel.SUBSECTION: 3,
    ProvisionLevel.ARTICLE: 4,
    ProvisionLevel.CLAUSE: 5,
    ProvisionLevel.POINT: 6,
}


@dataclass(frozen=True, slots=True)
class ProvisionLocator:
    """Canonical outer-to-inner path to a provision described in legal text."""

    parts: tuple[ProvisionReferencePart, ...]

    def __post_init__(self) -> None:
        if not self.parts:
            raise ExtractionModelError("provision locator requires at least one part")
        if not isinstance(self.parts, tuple) or any(
            not isinstance(item, ProvisionReferencePart) for item in self.parts
        ):
            raise ExtractionModelError(
                "provision locator parts must be ProvisionReferencePart values"
            )
        levels = [item.level for item in self.parts]
        if len(levels) != len(set(levels)):
            raise ExtractionModelError("provision locator levels must be unique")
        orders = [_LEVEL_ORDER[level] for level in levels]
        if orders != sorted(orders):
            raise ExtractionModelError(
                "provision locator parts must be ordered from outer to inner"
            )

    @property
    def leaf(self) -> ProvisionReferencePart:
        return self.parts[-1]

    def label_for(self, level: ProvisionLevel) -> str | None:
        return next((item.label for item in self.parts if item.level is level), None)


@dataclass(frozen=True, slots=True)
class TargetReference:
    """A target as written in the source, before domain ID resolution."""

    id: str
    raw_text: str
    scope: TargetScope
    document_reference: str | None = None
    locator: ProvisionLocator | None = None
    is_insertion: bool = False
    insert_under: ProvisionLocator | None = None
    insert_after: ProvisionLocator | None = None

    def __post_init__(self) -> None:
        _require_text(self.id, "target reference id")
        _require_text(self.raw_text, "target reference raw_text")
        _require_enum(self.scope, TargetScope, "target reference scope")
        if not isinstance(self.is_insertion, bool):
            raise ExtractionModelError("target reference is_insertion must be boolean")
        if self.document_reference is not None:
            _require_text(
                self.document_reference, "target reference document_reference"
            )
        if self.scope is TargetScope.DOCUMENT:
            if self.locator is not None:
                raise ExtractionModelError(
                    "document-scoped reference cannot contain a provision locator"
                )
            if self.is_insertion or self.insert_under is not None or self.insert_after is not None:
                raise ExtractionModelError(
                    "document-scoped reference cannot contain an insertion anchor"
                )
        elif self.locator is None:
            raise ExtractionModelError(
                "exact and subtree references require a provision locator"
            )
        if self.locator is not None and not isinstance(self.locator, ProvisionLocator):
            raise ExtractionModelError("target reference locator must be a ProvisionLocator")
        if self.insert_under is not None and not isinstance(
            self.insert_under, ProvisionLocator
        ):
            raise ExtractionModelError(
                "target reference insert_under must be a ProvisionLocator"
            )
        if self.insert_after is not None and not isinstance(
            self.insert_after, ProvisionLocator
        ):
            raise ExtractionModelError(
                "target reference insert_after must be a ProvisionLocator"
            )
        if self.is_insertion:
            if self.scope is not TargetScope.EXACT:
                raise ExtractionModelError("an insertion reference must use exact scope")
            if self.insert_under is None and self.insert_after is None:
                raise ExtractionModelError(
                    "an insertion reference requires a parent or sibling anchor"
                )
        elif self.insert_under is not None or self.insert_after is not None:
            raise ExtractionModelError(
                "insertion anchors require is_insertion=True"
            )


@dataclass(frozen=True, slots=True)
class ResolvedTarget:
    """Auditable resolution of one textual reference to stable domain IDs."""

    reference_id: str
    scope: TargetScope
    status: ResolutionStatus
    target_document_id: str | None = None
    target_provision_ids: tuple[str, ...] = ()
    affected_provision_ids: tuple[str, ...] = ()
    candidate_document_ids: tuple[str, ...] = ()
    candidate_provision_ids: tuple[str, ...] = ()
    method: ExtractionMethod | None = None
    confidence: float | None = None
    resolves_insertion: bool = False
    introduced_provision_id: str | None = None
    insertion_parent_id: str | None = None
    insertion_after_provision_id: str | None = None

    def __post_init__(self) -> None:
        _require_text(self.reference_id, "resolved target reference_id")
        _require_enum(self.scope, TargetScope, "resolved target scope")
        _require_enum(self.status, ResolutionStatus, "resolution status")
        if self.method is not None:
            _require_enum(self.method, ExtractionMethod, "resolution method")
        if not isinstance(self.resolves_insertion, bool):
            raise ExtractionModelError("resolves_insertion must be boolean")
        _unique_nonempty(
            self.target_provision_ids, "target_provision_ids", allow_empty=True
        )
        _unique_nonempty(
            self.affected_provision_ids,
            "affected_provision_ids",
            allow_empty=True,
        )
        _unique_nonempty(
            self.candidate_document_ids, "candidate_document_ids", allow_empty=True
        )
        _unique_nonempty(
            self.candidate_provision_ids, "candidate_provision_ids", allow_empty=True
        )
        _optional_confidence(self.confidence, "resolution confidence")

        if self.status is ResolutionStatus.RESOLVED:
            if not self.target_document_id:
                raise ExtractionModelError(
                    "resolved target requires target_document_id"
                )
            if self.method is None or self.confidence is None:
                raise ExtractionModelError(
                    "resolved target requires method and confidence"
                )
            if self.resolves_insertion:
                if self.scope is not TargetScope.EXACT:
                    raise ExtractionModelError(
                        "resolved insertion must use exact scope"
                    )
                if self.target_provision_ids:
                    raise ExtractionModelError(
                        "resolved insertion cannot contain existing target ids"
                    )
                if self.affected_provision_ids:
                    raise ExtractionModelError(
                        "resolved insertion cannot contain affected provision ids"
                    )
                if not self.introduced_provision_id:
                    raise ExtractionModelError(
                        "resolved insertion requires introduced_provision_id"
                    )
            elif self.scope is TargetScope.EXACT:
                if len(self.target_provision_ids) != 1:
                    raise ExtractionModelError(
                        "resolved exact target requires exactly one provision id"
                    )
                if (
                    self.affected_provision_ids
                    and self.target_provision_ids[0]
                    not in self.affected_provision_ids
                ):
                    raise ExtractionModelError(
                        "affected ids must include the exact target"
                    )
            if self.scope is TargetScope.SUBTREE:
                if len(self.target_provision_ids) != 1:
                    raise ExtractionModelError(
                        "resolved subtree target requires exactly one root id"
                    )
                if not self.affected_provision_ids:
                    raise ExtractionModelError(
                        "resolved subtree target requires affected provision ids"
                    )
                if self.target_provision_ids[0] not in self.affected_provision_ids:
                    raise ExtractionModelError(
                        "subtree affected ids must include its root target"
                    )
            if self.scope is TargetScope.DOCUMENT:
                if self.target_provision_ids or self.affected_provision_ids:
                    raise ExtractionModelError(
                        "resolved document target cannot contain provision ids"
                    )
            if not self.resolves_insertion and any(
                value is not None
                for value in (
                    self.introduced_provision_id,
                    self.insertion_parent_id,
                    self.insertion_after_provision_id,
                )
            ):
                raise ExtractionModelError(
                    "insertion metadata requires resolves_insertion=True"
                )
        else:
            if (
                self.target_document_id is not None
                or self.target_provision_ids
                or self.affected_provision_ids
                or self.resolves_insertion
                or self.introduced_provision_id is not None
                or self.insertion_parent_id is not None
                or self.insertion_after_provision_id is not None
            ):
                raise ExtractionModelError(
                    "unaccepted resolution must keep possible targets as candidates"
                )
        for value, name in (
            (self.introduced_provision_id, "introduced_provision_id"),
            (self.insertion_parent_id, "insertion_parent_id"),
            (self.insertion_after_provision_id, "insertion_after_provision_id"),
        ):
            if value is not None:
                _require_text(value, name)

    @property
    def is_resolved(self) -> bool:
        return self.status is ResolutionStatus.RESOLVED


@dataclass(frozen=True, slots=True)
class PhraseReplacement:
    """A source instruction that still needs deterministic text consolidation."""

    reference_ids: tuple[str, ...]
    old_text: str
    new_text: str

    def __post_init__(self) -> None:
        _unique_nonempty(self.reference_ids, "phrase replacement reference_ids")
        _require_text(self.old_text, "phrase replacement old_text")
        if not isinstance(self.new_text, str):
            raise ExtractionModelError("phrase replacement new_text must be a string")


@dataclass(frozen=True, slots=True)
class ExtractionWarning:
    """One structured issue retained for review and error analysis."""

    code: WarningCode
    message: str
    severity: WarningSeverity = WarningSeverity.WARNING
    mention_id: str | None = None
    reference_id: str | None = None
    span: SourceSpan | None = None
    details: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        _require_enum(self.code, WarningCode, "extraction warning code")
        _require_enum(self.severity, WarningSeverity, "warning severity")
        _require_text(self.message, "extraction warning message")
        if self.span is not None and not isinstance(self.span, SourceSpan):
            raise ExtractionModelError("warning span must be a SourceSpan")
        if not isinstance(self.details, Mapping):
            raise ExtractionModelError("warning details must be a mapping")
        if self.mention_id is not None:
            _require_text(self.mention_id, "extraction warning mention_id")
        if self.reference_id is not None:
            _require_text(self.reference_id, "extraction warning reference_id")


@dataclass(frozen=True, slots=True)
class ExtractionResult:
    """Complete output passed from extraction/resolution to event creation."""

    id: str
    mention: RawAmendmentMention
    status: ExtractionStatus = ExtractionStatus.NEEDS_REVIEW
    operation: LegalOperation | None = None
    effective_on: date | None = None
    target_references: tuple[TargetReference, ...] = ()
    resolved_targets: tuple[ResolvedTarget, ...] = ()
    text_updates: tuple[TextUpdate, ...] = ()
    insertions: tuple[ProvisionInsertion, ...] = ()
    phrase_replacements: tuple[PhraseReplacement, ...] = ()
    extraction_confidence: float | None = None
    warnings: tuple[ExtractionWarning, ...] = ()

    def __post_init__(self) -> None:
        _require_text(self.id, "extraction result id")
        if not isinstance(self.mention, RawAmendmentMention):
            raise ExtractionModelError("extraction result mention is invalid")
        _require_enum(self.status, ExtractionStatus, "extraction status")
        if self.operation is not None:
            _require_enum(self.operation, LegalOperation, "legal operation")
        if self.effective_on is not None and type(self.effective_on) is not date:
            raise ExtractionModelError("effective_on must be a date")
        _require_tuple_items(
            self.target_references, TargetReference, "target_references"
        )
        _require_tuple_items(
            self.resolved_targets, ResolvedTarget, "resolved_targets"
        )
        _require_tuple_items(self.text_updates, TextUpdate, "text_updates")
        _require_tuple_items(self.insertions, ProvisionInsertion, "insertions")
        _require_tuple_items(
            self.phrase_replacements, PhraseReplacement, "phrase_replacements"
        )
        _require_tuple_items(self.warnings, ExtractionWarning, "warnings")
        _optional_confidence(
            self.extraction_confidence, "extraction confidence"
        )
        reference_ids = tuple(item.id for item in self.target_references)
        _unique_nonempty(reference_ids, "target reference ids", allow_empty=True)
        resolved_reference_ids = tuple(
            item.reference_id for item in self.resolved_targets
        )
        _unique_nonempty(
            resolved_reference_ids, "resolved reference ids", allow_empty=True
        )
        unknown_resolutions = sorted(set(resolved_reference_ids) - set(reference_ids))
        if unknown_resolutions:
            raise ExtractionModelError(
                "resolved targets refer to unknown references: "
                + ", ".join(unknown_resolutions)
            )
        replacement_reference_ids = {
            reference_id
            for replacement in self.phrase_replacements
            for reference_id in replacement.reference_ids
        }
        unknown_replacements = sorted(replacement_reference_ids - set(reference_ids))
        if unknown_replacements:
            raise ExtractionModelError(
                "phrase replacements refer to unknown references: "
                + ", ".join(unknown_replacements)
            )
        for warning in self.warnings:
            if warning.mention_id not in {None, self.mention.id}:
                raise ExtractionModelError(
                    "warning mention_id must match the result mention"
                )
            if warning.reference_id is not None:
                if warning.reference_id not in set(reference_ids):
                    raise ExtractionModelError(
                        "warning refers to an unknown target reference"
                    )
        if self.status is ExtractionStatus.READY:
            issues = self._readiness_issues(check_status=False)
            if issues:
                raise ExtractionModelError(
                    "ready extraction result is incomplete: " + "; ".join(issues)
                )

    @property
    def is_event_ready(self) -> bool:
        return not self.readiness_issues()

    def readiness_issues(self) -> tuple[str, ...]:
        """Explain every reason this result cannot yet create an event."""
        return self._readiness_issues(check_status=True)

    def resolved_provision_ids(self) -> tuple[str, ...]:
        """Direct event targets, deduplicated in reference order."""
        return tuple(
            dict.fromkeys(
                provision_id
                for target in self.resolved_targets
                if target.is_resolved
                for provision_id in target.target_provision_ids
            )
        )

    def affected_provision_ids(self) -> tuple[str, ...]:
        """Direct and structural effects, without making descendants targets."""
        return tuple(
            dict.fromkeys(
                provision_id
                for target in self.resolved_targets
                if target.is_resolved
                for provision_id in (
                    target.affected_provision_ids or target.target_provision_ids
                )
            )
        )

    def to_legal_event(
        self,
        event_id: str,
        *,
        event_status: EventStatus,
    ) -> LegalEvent:
        """Create an applicable event only after explicit acceptance."""
        issues = self.readiness_issues()
        if issues:
            raise EventMaterializationError(
                "extraction result cannot create an event: " + "; ".join(issues)
            )
        if event_status not in {EventStatus.VERIFIED, EventStatus.AUTO_ACCEPTED}:
            raise EventMaterializationError(
                "event materialization requires verified or auto_accepted status"
            )

        target_documents = {
            target.target_document_id
            for target in self.resolved_targets
            if target.is_resolved
        }
        target_document_id = next(iter(target_documents))
        assert target_document_id is not None
        assert self.operation is not None
        target_provision_ids = self.resolved_provision_ids()
        if self.operation is LegalOperation.SUPPLEMENT:
            # Resolved references may include an insertion parent or anchor;
            # only provisions whose text changes are explicit event targets.
            target_provision_ids = tuple(
                update.target_provision_id for update in self.text_updates
            )
        return LegalEvent(
            id=event_id,
            operation=self.operation,
            source_document_id=self.mention.source_document_id,
            target_document_id=target_document_id,
            effective_on=self.effective_on,
            target_provision_ids=target_provision_ids,
            text_updates=self.text_updates,
            insertions=self.insertions,
            status=event_status,
            provenance=self.mention.provenance,
        )

    def _readiness_issues(self, *, check_status: bool) -> tuple[str, ...]:
        issues: list[str] = []
        if check_status and self.status is not ExtractionStatus.READY:
            issues.append(f"status is {self.status.value}")
        if self.operation is None:
            issues.append("operation is unresolved")
        if self.effective_on is None:
            issues.append("effective date is unresolved")
        if self.extraction_confidence is None:
            issues.append("extraction confidence is missing")
        if not self.target_references:
            issues.append("no target references")

        resolution_by_reference = {
            target.reference_id: target for target in self.resolved_targets
        }
        for reference in self.target_references:
            resolution = resolution_by_reference.get(reference.id)
            if resolution is None:
                issues.append(f"reference {reference.id} has no resolution")
            elif resolution.scope is not reference.scope:
                issues.append(f"reference {reference.id} has a scope mismatch")
            elif not resolution.is_resolved:
                issues.append(f"reference {reference.id} is not resolved")
            elif resolution.resolves_insertion != reference.is_insertion:
                issues.append(f"reference {reference.id} has an insertion mismatch")

        target_documents = {
            target.target_document_id
            for target in self.resolved_targets
            if target.is_resolved
        }
        if len(target_documents) > 1:
            issues.append("resolved targets belong to multiple documents")
        if any(
            warning.severity is WarningSeverity.ERROR for warning in self.warnings
        ):
            issues.append("result contains error warnings")

        resolved_ids = set(self.resolved_provision_ids())
        update_ids = {update.target_provision_id for update in self.text_updates}
        if not update_ids.issubset(resolved_ids):
            issues.append("text updates contain unresolved target ids")

        insertions_by_id = {item.provision_id: item for item in self.insertions}
        insertion_resolutions = (
            target
            for target in self.resolved_targets
            if target.is_resolved and target.resolves_insertion
        )
        resolved_insertion_ids: set[str] = set()
        for resolution in insertion_resolutions:
            introduced_id = resolution.introduced_provision_id
            if introduced_id is None:
                continue
            resolved_insertion_ids.add(introduced_id)
            insertion = insertions_by_id.get(introduced_id)
            if insertion is None:
                issues.append(
                    f"resolved insertion {introduced_id} has no insertion payload"
                )
            elif (
                insertion.parent_id != resolution.insertion_parent_id
                or insertion.after_provision_id
                != resolution.insertion_after_provision_id
            ):
                issues.append(f"resolved insertion {introduced_id} has an anchor mismatch")
        unresolved_insertion_ids = set(insertions_by_id) - resolved_insertion_ids
        if unresolved_insertion_ids:
            issues.append("insertion payloads do not have resolved positions")

        if self.operation in {
            LegalOperation.AMEND,
            LegalOperation.REPLACE,
            LegalOperation.CORRECT,
        }:
            if not self.text_updates:
                issues.append("text operation has no consolidated text updates")
            elif update_ids != resolved_ids:
                issues.append(
                    "text operation must update every resolved provision"
                )
            if self.insertions:
                issues.append("text operation cannot contain insertions")
        elif self.operation is LegalOperation.REPEAL:
            if self.text_updates or self.insertions:
                issues.append("repeal cannot contain text updates or insertions")
            if not resolved_ids:
                issues.append("repeal has no resolved provisions")
        elif self.operation is LegalOperation.SUPPLEMENT:
            if not self.text_updates and not self.insertions:
                issues.append("supplement has no text update or insertion")
        elif self.operation in {LegalOperation.SUSPEND, LegalOperation.RESUME}:
            issues.append(f"operation {self.operation.value} is not materializable")

        return tuple(dict.fromkeys(issues))


def _require_text(value: Any, name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ExtractionModelError(f"{name} must not be empty")


def _require_enum(value: Any, enum_type: type[Enum], name: str) -> None:
    if not isinstance(value, enum_type):
        raise ExtractionModelError(f"{name} must be a {enum_type.__name__}")


def _require_tuple_items(values: Any, item_type: type, name: str) -> None:
    if not isinstance(values, tuple) or any(
        not isinstance(item, item_type) for item in values
    ):
        raise ExtractionModelError(
            f"{name} must be a tuple of {item_type.__name__} values"
        )


def _optional_confidence(value: float | None, name: str) -> None:
    if value is None:
        return
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ExtractionModelError(f"{name} must be a number")
    if not 0.0 <= value <= 1.0:
        raise ExtractionModelError(f"{name} must be between 0 and 1")


def _unique_nonempty(
    values: Any,
    name: str,
    *,
    allow_empty: bool = False,
) -> None:
    if not isinstance(values, tuple):
        raise ExtractionModelError(f"{name} must be a tuple")
    if not allow_empty and not values:
        raise ExtractionModelError(f"{name} must not be empty")
    for value in values:
        _require_text(value, name)
    if len(values) != len(set(values)):
        raise ExtractionModelError(f"{name} must not contain duplicates")

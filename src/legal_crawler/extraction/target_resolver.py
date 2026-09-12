"""Deterministic resolution of legal locators against a provision tree.

The resolver consumes normalized references produced by extraction and stable
domain objects exposed through repository ports.  It deliberately avoids fuzzy
matching: a reference is accepted only when its structural path identifies one
provision or one insertion-anchor configuration.
"""
from __future__ import annotations

import re
import unicodedata
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from enum import Enum

from legal_crawler.ports import DocumentRepository, ProvisionRepository
from legal_crawler.temporal import ExtractionMethod, Provision, ProvisionLevel

from .models import (
    ProvisionLocator,
    ResolutionStatus,
    ResolvedTarget,
    TargetReference,
    TargetScope,
)


class TargetResolutionError(ValueError):
    """The resolver was called with an invalid contract value."""


class TargetResolutionCode(str, Enum):
    """Stable outcome codes suitable for review queues and error analysis."""

    RESOLVED_EXACT = "resolved_exact"
    RESOLVED_SUBTREE = "resolved_subtree"
    RESOLVED_DOCUMENT = "resolved_document"
    RESOLVED_INSERTION = "resolved_insertion"
    DOCUMENT_NOT_FOUND = "document_not_found"
    AMBIGUOUS_DOCUMENT = "ambiguous_document"
    LOCATOR_NOT_FOUND = "locator_not_found"
    AMBIGUOUS_LOCATOR = "ambiguous_locator"
    UNSUPPORTED_LABEL = "unsupported_label"
    INSERTION_ID_REQUIRED = "insertion_id_required"
    INSERTION_ANCHOR_NOT_FOUND = "insertion_anchor_not_found"
    AMBIGUOUS_INSERTION_ANCHOR = "ambiguous_insertion_anchor"
    INCONSISTENT_INSERTION_ANCHORS = "inconsistent_insertion_anchors"


@dataclass(frozen=True, slots=True)
class TargetResolution:
    """A resolved-target contract plus an auditable decision explanation."""

    target: ResolvedTarget
    code: TargetResolutionCode
    message: str

    def __post_init__(self) -> None:
        if not isinstance(self.target, ResolvedTarget):
            raise TargetResolutionError("target must be a ResolvedTarget")
        if not isinstance(self.code, TargetResolutionCode):
            raise TargetResolutionError("code must be a TargetResolutionCode")
        if not isinstance(self.message, str) or not self.message.strip():
            raise TargetResolutionError("message must not be empty")
        resolved_codes = {
            TargetResolutionCode.RESOLVED_EXACT,
            TargetResolutionCode.RESOLVED_SUBTREE,
            TargetResolutionCode.RESOLVED_DOCUMENT,
            TargetResolutionCode.RESOLVED_INSERTION,
        }
        review_codes = {
            TargetResolutionCode.AMBIGUOUS_DOCUMENT,
            TargetResolutionCode.AMBIGUOUS_LOCATOR,
            TargetResolutionCode.AMBIGUOUS_INSERTION_ANCHOR,
        }
        expected_status = (
            ResolutionStatus.RESOLVED
            if self.code in resolved_codes
            else (
                ResolutionStatus.NEEDS_REVIEW
                if self.code in review_codes
                else ResolutionStatus.UNRESOLVED
            )
        )
        if self.target.status is not expected_status:
            raise TargetResolutionError(
                f"code {self.code.value} requires status {expected_status.value}"
            )


_SPACE = re.compile(r"\s+")
_MARKERS = {
    ProvisionLevel.PART: r"(?:[ivxlcdm]+|\d+[a-zđ]?)",
    ProvisionLevel.CHAPTER: r"(?:[ivxlcdm]+|\d+[a-zđ]?)",
    ProvisionLevel.SECTION: r"(?:[ivxlcdm]+|\d+[a-zđ]?)",
    ProvisionLevel.SUBSECTION: r"(?:[ivxlcdm]+|\d+[a-zđ]?)",
    ProvisionLevel.ARTICLE: r"\d+[a-zđ]?",
    ProvisionLevel.CLAUSE: r"\d+[a-zđ]?",
    ProvisionLevel.POINT: r"[a-zđ]",
}
_PREFIXES = {
    ProvisionLevel.PART: "phần",
    ProvisionLevel.CHAPTER: "chương",
    ProvisionLevel.SECTION: "mục",
    ProvisionLevel.SUBSECTION: "tiểu mục",
    ProvisionLevel.ARTICLE: "điều",
    ProvisionLevel.CLAUSE: "khoản",
    ProvisionLevel.POINT: "điểm",
}


class TargetResolver:
    """Resolve document and provision targets without source-format knowledge."""

    def __init__(
        self,
        documents: DocumentRepository,
        provisions: ProvisionRepository,
    ) -> None:
        if not isinstance(documents, DocumentRepository):
            raise TypeError("documents must satisfy DocumentRepository")
        if not isinstance(provisions, ProvisionRepository):
            raise TypeError("provisions must satisfy ProvisionRepository")
        self._documents = documents
        self._provisions = provisions

    def resolve(
        self,
        reference: TargetReference,
        document_ids: Sequence[str],
        *,
        introduced_provision_id: str | None = None,
    ) -> TargetResolution:
        """Resolve one reference within an explicit set of candidate documents."""
        if not isinstance(reference, TargetReference):
            raise TypeError("reference must be a TargetReference")
        candidates = _document_ids(document_ids)
        missing = tuple(
            document_id
            for document_id in candidates
            if not self._documents.exists(document_id)
        )
        if missing:
            return self._unaccepted(
                reference,
                ResolutionStatus.UNRESOLVED,
                TargetResolutionCode.DOCUMENT_NOT_FOUND,
                "candidate document does not exist: " + ", ".join(missing),
                document_ids=candidates,
            )

        if reference.scope is TargetScope.DOCUMENT:
            return self._resolve_document(reference, candidates)
        if reference.is_insertion:
            return self._resolve_insertion(
                reference,
                candidates,
                introduced_provision_id=introduced_provision_id,
            )
        assert reference.locator is not None
        matches, unsupported = self._matches(reference.locator, candidates)
        if unsupported:
            return self._unaccepted(
                reference,
                ResolutionStatus.UNRESOLVED,
                TargetResolutionCode.UNSUPPORTED_LABEL,
                unsupported,
                document_ids=candidates,
            )
        if not matches:
            return self._unaccepted(
                reference,
                ResolutionStatus.UNRESOLVED,
                TargetResolutionCode.LOCATOR_NOT_FOUND,
                "no provision matches the complete structural locator",
                document_ids=candidates,
            )
        if len(matches) != 1:
            return self._unaccepted(
                reference,
                ResolutionStatus.NEEDS_REVIEW,
                TargetResolutionCode.AMBIGUOUS_LOCATOR,
                f"structural locator matches {len(matches)} provisions",
                document_ids=candidates,
                provision_ids=tuple(item.id for item in matches),
            )

        provision = matches[0]
        affected = ()
        code = TargetResolutionCode.RESOLVED_EXACT
        if reference.scope is TargetScope.SUBTREE:
            affected = (
                provision.id,
                *(item.id for item in self._provisions.descendants_of(provision.id)),
            )
            code = TargetResolutionCode.RESOLVED_SUBTREE
        target = ResolvedTarget(
            reference_id=reference.id,
            scope=reference.scope,
            status=ResolutionStatus.RESOLVED,
            target_document_id=provision.document_id,
            target_provision_ids=(provision.id,),
            affected_provision_ids=affected,
            candidate_document_ids=candidates,
            candidate_provision_ids=(provision.id,),
            method=ExtractionMethod.RULE,
            confidence=1.0,
        )
        return TargetResolution(
            target,
            code,
            "complete structural locator has one deterministic match",
        )

    def resolve_many(
        self,
        references: Sequence[TargetReference],
        document_ids: Sequence[str],
        *,
        introduced_provision_ids: Mapping[str, str] | None = None,
    ) -> tuple[TargetResolution, ...]:
        """Resolve references in input order without merging their outcomes."""
        if isinstance(references, (str, bytes)) or not isinstance(
            references, Sequence
        ):
            raise TargetResolutionError("references must be a sequence")
        if any(not isinstance(item, TargetReference) for item in references):
            raise TargetResolutionError(
                "references must contain TargetReference values"
            )
        reference_ids = tuple(item.id for item in references)
        if len(reference_ids) != len(set(reference_ids)):
            raise TargetResolutionError("references must not contain duplicate IDs")
        introduced = (
            {} if introduced_provision_ids is None else introduced_provision_ids
        )
        if not isinstance(introduced, Mapping):
            raise TargetResolutionError(
                "introduced_provision_ids must be a mapping"
            )
        unknown = set(introduced) - set(reference_ids)
        if unknown:
            raise TargetResolutionError(
                "introduced IDs refer to unknown references: "
                + ", ".join(sorted(unknown))
            )
        return tuple(
            self.resolve(
                reference,
                document_ids,
                introduced_provision_id=introduced.get(reference.id),
            )
            for reference in references
        )

    def _resolve_document(
        self,
        reference: TargetReference,
        document_ids: tuple[str, ...],
    ) -> TargetResolution:
        if len(document_ids) != 1:
            return self._unaccepted(
                reference,
                ResolutionStatus.NEEDS_REVIEW,
                TargetResolutionCode.AMBIGUOUS_DOCUMENT,
                f"document reference has {len(document_ids)} candidates",
                document_ids=document_ids,
            )
        target = ResolvedTarget(
            reference.id,
            reference.scope,
            ResolutionStatus.RESOLVED,
            target_document_id=document_ids[0],
            candidate_document_ids=document_ids,
            method=ExtractionMethod.RULE,
            confidence=1.0,
        )
        return TargetResolution(
            target,
            TargetResolutionCode.RESOLVED_DOCUMENT,
            "document reference has one explicit candidate",
        )

    def _resolve_insertion(
        self,
        reference: TargetReference,
        document_ids: tuple[str, ...],
        *,
        introduced_provision_id: str | None,
    ) -> TargetResolution:
        anchor_locators = tuple(
            item
            for item in (reference.insert_under, reference.insert_after)
            if item is not None
        )
        anchor_matches: list[tuple[Provision, ...]] = []
        for locator in anchor_locators:
            matches, unsupported = self._matches(locator, document_ids)
            if unsupported:
                return self._unaccepted(
                    reference,
                    ResolutionStatus.UNRESOLVED,
                    TargetResolutionCode.UNSUPPORTED_LABEL,
                    unsupported,
                    document_ids=document_ids,
                )
            anchor_matches.append(matches)
        all_anchor_ids = tuple(
            dict.fromkeys(item.id for matches in anchor_matches for item in matches)
        )
        if any(not matches for matches in anchor_matches):
            return self._unaccepted(
                reference,
                ResolutionStatus.UNRESOLVED,
                TargetResolutionCode.INSERTION_ANCHOR_NOT_FOUND,
                "an insertion parent or sibling anchor was not found",
                document_ids=document_ids,
                provision_ids=all_anchor_ids,
            )

        configurations = self._insertion_configurations(reference, anchor_matches)
        if not configurations:
            return self._unaccepted(
                reference,
                ResolutionStatus.UNRESOLVED,
                TargetResolutionCode.INCONSISTENT_INSERTION_ANCHORS,
                "insertion parent and sibling anchor are structurally inconsistent",
                document_ids=document_ids,
                provision_ids=all_anchor_ids,
            )
        if len(configurations) != 1:
            return self._unaccepted(
                reference,
                ResolutionStatus.NEEDS_REVIEW,
                TargetResolutionCode.AMBIGUOUS_INSERTION_ANCHOR,
                f"insertion reference has {len(configurations)} anchor configurations",
                document_ids=document_ids,
                provision_ids=all_anchor_ids,
            )
        if not isinstance(introduced_provision_id, str) or not (
            introduced_provision_id.strip()
        ):
            return self._unaccepted(
                reference,
                ResolutionStatus.UNRESOLVED,
                TargetResolutionCode.INSERTION_ID_REQUIRED,
                "a stable ID is required for the introduced provision",
                document_ids=document_ids,
                provision_ids=all_anchor_ids,
            )

        document_id, parent_id, after_id = configurations[0]
        target = ResolvedTarget(
            reference_id=reference.id,
            scope=reference.scope,
            status=ResolutionStatus.RESOLVED,
            target_document_id=document_id,
            candidate_document_ids=document_ids,
            candidate_provision_ids=all_anchor_ids,
            method=ExtractionMethod.RULE,
            confidence=1.0,
            resolves_insertion=True,
            introduced_provision_id=introduced_provision_id,
            insertion_parent_id=parent_id,
            insertion_after_provision_id=after_id,
        )
        return TargetResolution(
            target,
            TargetResolutionCode.RESOLVED_INSERTION,
            "insertion parent and sibling anchor form one deterministic location",
        )

    @staticmethod
    def _insertion_configurations(
        reference: TargetReference,
        anchor_matches: list[tuple[Provision, ...]],
    ) -> tuple[tuple[str, str | None, str | None], ...]:
        if reference.insert_under is not None and reference.insert_after is not None:
            parents, siblings = anchor_matches
            return tuple(
                (parent.document_id, parent.id, sibling.id)
                for parent in parents
                for sibling in siblings
                if sibling.document_id == parent.document_id
                and sibling.parent_id == parent.id
            )
        if reference.insert_under is not None:
            return tuple(
                (item.document_id, item.id, None)
                for item in anchor_matches[0]
            )
        return tuple(
            (item.document_id, item.parent_id, item.id)
            for item in anchor_matches[0]
        )

    def _matches(
        self,
        locator: ProvisionLocator,
        document_ids: tuple[str, ...],
    ) -> tuple[tuple[Provision, ...], str | None]:
        expected: list[tuple[ProvisionLevel, str]] = []
        for part in locator.parts:
            key = _reference_label(part.level, part.label)
            if key is None:
                return (), (
                    f"unsupported {part.level.value} label: {part.label!r}"
                )
            expected.append((part.level, key))

        matches: list[Provision] = []
        for document_id in document_ids:
            ordered = self._provisions.document_order(document_id)
            by_id = {item.id: item for item in ordered}
            current: tuple[Provision, ...] = ()
            for index, (level, key) in enumerate(expected):
                current_ids = {item.id for item in current}
                current = tuple(
                    item
                    for item in ordered
                    if item.level is level
                    and _title_label(level, item.title) == key
                    and (
                        index == 0
                        or _has_ancestor(item, current_ids, by_id)
                    )
                )
                if not current:
                    break
            matches.extend(current)
        return tuple(matches), None

    @staticmethod
    def _unaccepted(
        reference: TargetReference,
        status: ResolutionStatus,
        code: TargetResolutionCode,
        message: str,
        *,
        document_ids: tuple[str, ...],
        provision_ids: tuple[str, ...] = (),
    ) -> TargetResolution:
        target = ResolvedTarget(
            reference_id=reference.id,
            scope=reference.scope,
            status=status,
            candidate_document_ids=document_ids,
            candidate_provision_ids=provision_ids,
            method=ExtractionMethod.RULE,
            confidence=0.0 if status is ResolutionStatus.UNRESOLVED else None,
        )
        return TargetResolution(target, code, message)


def _document_ids(values: Sequence[str]) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)) or not isinstance(values, Sequence):
        raise TargetResolutionError("document_ids must be a sequence")
    if not values:
        raise TargetResolutionError("document_ids must not be empty")
    if any(not isinstance(item, str) or not item.strip() for item in values):
        raise TargetResolutionError("document_ids must contain non-empty strings")
    result = tuple(item.strip() for item in values)
    if len(result) != len(set(result)):
        raise TargetResolutionError("document_ids must not contain duplicates")
    return result


def _normalized(value: str) -> str:
    return _SPACE.sub(" ", unicodedata.normalize("NFC", value).casefold()).strip()


def _reference_label(level: ProvisionLevel, value: str) -> str | None:
    normalized = _normalized(value)
    marker = _MARKERS[level]
    prefix = re.escape(_PREFIXES[level])
    match = re.fullmatch(
        rf"(?:{prefix}\s+)?(?P<marker>{marker})\s*[.):,-]?",
        normalized,
    )
    return match.group("marker") if match else None


def _title_label(level: ProvisionLevel, value: str) -> str | None:
    normalized = _normalized(value)
    marker = _MARKERS[level]
    prefix = re.escape(_PREFIXES[level])
    if level in {ProvisionLevel.CLAUSE, ProvisionLevel.POINT}:
        prefix = rf"(?:{prefix}\s+)?"
    else:
        prefix = rf"{prefix}\s+"
    match = re.match(
        rf"^{prefix}(?P<marker>{marker})(?=\s|[.):,-]|$)",
        normalized,
    )
    return match.group("marker") if match else None


def _has_ancestor(
    provision: Provision,
    ancestor_ids: set[str],
    by_id: Mapping[str, Provision],
) -> bool:
    parent_id = provision.parent_id
    visited: set[str] = set()
    while parent_id is not None and parent_id not in visited:
        if parent_id in ancestor_ids:
            return True
        visited.add(parent_id)
        parent = by_id.get(parent_id)
        parent_id = parent.parent_id if parent is not None else None
    return False

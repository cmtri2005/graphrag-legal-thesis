"""Typed contracts for temporal retrieval, citation and answer verification.

The query layer consumes point-in-time snapshots instead of reconstructing
legal validity itself.  Evidence is therefore bound to one valid snapshot,
while citations keep their claimed identifiers explicit so a verifier can
report document, provision, version and granularity mistakes without losing
the original output.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import date
from enum import Enum
from typing import cast

from legal_crawler.temporal.models import (
    Provenance,
    Provision,
    ProvisionLevel,
    ProvisionVersion,
    RelationType,
    TemporalInterval,
)
from legal_crawler.temporal.snapshot import SnapshotResult


class QueryModelError(ValueError):
    """A query-layer object violates its structural contract."""


class TemporalResolution(str, Enum):
    """How the point in time of a query was obtained."""

    EXPLICIT = "explicit"
    INFERRED = "inferred"
    UNRESOLVED = "unresolved"


class RetrievalMethod(str, Enum):
    """Independent retrieval signals retained for analysis and ablation."""

    LEXICAL = "lexical"
    DENSE = "dense"
    GRAPH = "graph"
    RERANK = "rerank"


class CitationLevel(str, Enum):
    """Granularity claimed by a citation in an answer."""

    DOCUMENT = "document"
    PART = "part"
    CHAPTER = "chapter"
    SECTION = "section"
    SUBSECTION = "subsection"
    ARTICLE = "article"
    CLAUSE = "clause"
    POINT = "point"


class VerificationSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


class VerificationIssueCode(str, Enum):
    """Stable error vocabulary for temporal and citation evaluation."""

    QUERY_TIME_UNRESOLVED = "query_time_unresolved"
    EVIDENCE_OUTSIDE_QUERY_TIME = "evidence_outside_query_time"
    EVIDENCE_MISSING_PROVENANCE = "evidence_missing_provenance"
    CITATION_EVIDENCE_NOT_FOUND = "citation_evidence_not_found"
    CITATION_DOCUMENT_MISMATCH = "citation_document_mismatch"
    CITATION_PROVISION_MISMATCH = "citation_provision_mismatch"
    CITATION_VERSION_MISMATCH = "citation_version_mismatch"
    CITATION_LEVEL_MISMATCH = "citation_level_mismatch"
    CITATION_TEXT_UNSUPPORTED = "citation_text_unsupported"
    CLAIM_WITHOUT_CITATION = "claim_without_citation"
    CONFLICTING_EVIDENCE = "conflicting_evidence"


class VerificationDecision(str, Enum):
    PASSED = "passed"
    FAILED = "failed"
    NEEDS_REVIEW = "needs_review"


class AnswerStatus(str, Enum):
    ANSWERED = "answered"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"
    NEEDS_REVIEW = "needs_review"


@dataclass(frozen=True, slots=True)
class TemporalQuery:
    """A question with an explicit account of its temporal interpretation."""

    id: str
    text: str
    at: date | None
    temporal_resolution: TemporalResolution
    temporal_expression: str | None = None
    temporal_confidence: float | None = None
    document_ids: tuple[str, ...] = ()
    levels: frozenset[ProvisionLevel] = frozenset()

    def __post_init__(self) -> None:
        _require_text(self.id, "query id")
        _require_text(self.text, "query text")
        _require_enum(
            self.temporal_resolution,
            TemporalResolution,
            "query temporal_resolution",
        )
        if self.at is not None and type(self.at) is not date:
            raise QueryModelError("query at must be a date or None")
        if self.temporal_resolution is TemporalResolution.UNRESOLVED:
            if self.at is not None:
                raise QueryModelError("an unresolved query cannot have an at date")
            if self.temporal_confidence is not None:
                raise QueryModelError(
                    "an unresolved query cannot have temporal confidence"
                )
        elif self.at is None:
            raise QueryModelError("a resolved query requires an at date")
        if self.temporal_resolution is TemporalResolution.INFERRED:
            if self.temporal_confidence is None:
                raise QueryModelError(
                    "an inferred query requires temporal confidence"
                )
            if self.temporal_expression is None:
                raise QueryModelError(
                    "an inferred query requires its temporal expression"
                )
        if self.temporal_expression is not None:
            _require_text(self.temporal_expression, "query temporal_expression")
        _optional_confidence(self.temporal_confidence, "query temporal_confidence")
        _require_unique_strings(self.document_ids, "query document_ids")
        if not isinstance(self.levels, frozenset) or any(
            not isinstance(item, ProvisionLevel) for item in self.levels
        ):
            raise QueryModelError(
                "query levels must be a frozenset of ProvisionLevel values"
            )

    @property
    def temporal_ready(self) -> bool:
        return self.at is not None


@dataclass(frozen=True, slots=True)
class RetrievalSignal:
    """One backend score before or after reranking."""

    method: RetrievalMethod
    score: float
    rank: int | None = None

    def __post_init__(self) -> None:
        _require_enum(self.method, RetrievalMethod, "retrieval signal method")
        _require_finite_number(self.score, "retrieval signal score")
        _optional_positive_int(self.rank, "retrieval signal rank")


@dataclass(frozen=True, slots=True)
class GraphTraversalStep:
    """One typed graph edge traversed while expanding retrieval context."""

    edge_id: str
    source_id: str
    relation: RelationType
    target_id: str

    def __post_init__(self) -> None:
        _require_text(self.edge_id, "graph step edge_id")
        _require_text(self.source_id, "graph step source_id")
        _require_enum(self.relation, RelationType, "graph step relation")
        _require_text(self.target_id, "graph step target_id")


@dataclass(frozen=True, slots=True)
class RetrievedEvidence:
    """One retrieval hit bound to a valid provision snapshot."""

    id: str
    query_id: str
    snapshot: SnapshotResult
    signals: tuple[RetrievalSignal, ...]
    rank: int
    final_score: float | None = None
    graph_path: tuple[GraphTraversalStep, ...] = ()

    def __post_init__(self) -> None:
        _require_text(self.id, "evidence id")
        _require_text(self.query_id, "evidence query_id")
        if not isinstance(self.snapshot, SnapshotResult):
            raise QueryModelError("evidence snapshot must be a SnapshotResult")
        if not self.snapshot.validity.valid:
            raise QueryModelError("evidence snapshot must be valid")
        if self.snapshot.provision is None or self.snapshot.version is None:
            raise QueryModelError(
                "evidence snapshot requires a provision and exact version"
            )
        if self.snapshot.version.provision_id != self.snapshot.provision.id:
            raise QueryModelError(
                "evidence version must belong to its snapshot provision"
            )
        if self.snapshot.validity.provision_id != self.snapshot.provision.id:
            raise QueryModelError(
                "evidence validity must belong to its snapshot provision"
            )
        if self.snapshot.validity.at != self.snapshot.at:
            raise QueryModelError("evidence validity date must match snapshot date")
        if self.snapshot.validity.version != self.snapshot.version:
            raise QueryModelError(
                "evidence validity must select its exact snapshot version"
            )
        if not self.snapshot.version.validity.contains(self.snapshot.at):
            raise QueryModelError(
                "evidence version must be effective at the snapshot date"
            )
        if not self.snapshot.text or not self.snapshot.text.strip():
            raise QueryModelError("evidence snapshot text must not be empty")
        if not self.snapshot.provenance:
            raise QueryModelError("evidence snapshot requires provenance")
        if self.snapshot.provenance != self.snapshot.version.provenance:
            raise QueryModelError(
                "evidence provenance must come from its exact version"
            )
        _require_tuple_items(self.signals, RetrievalSignal, "evidence signals")
        if not self.signals:
            raise QueryModelError("evidence requires at least one retrieval signal")
        methods = tuple(item.method for item in self.signals)
        if len(methods) != len(set(methods)):
            raise QueryModelError("evidence retrieval methods must be unique")
        _positive_int(self.rank, "evidence rank")
        if self.final_score is not None:
            _require_finite_number(self.final_score, "evidence final_score")
        _require_tuple_items(
            self.graph_path, GraphTraversalStep, "evidence graph_path"
        )
        for previous, following in zip(self.graph_path, self.graph_path[1:]):
            if previous.target_id != following.source_id:
                raise QueryModelError("evidence graph_path must be contiguous")
        has_graph_signal = any(
            item.method is RetrievalMethod.GRAPH for item in self.signals
        )
        if self.graph_path and not has_graph_signal:
            raise QueryModelError(
                "evidence graph_path requires a graph retrieval signal"
            )
        if has_graph_signal:
            if not self.graph_path:
                raise QueryModelError(
                    "graph-retrieved evidence requires a graph_path"
                )
            if self.graph_path[-1].target_id != self.snapshot.provision.id:
                raise QueryModelError(
                    "evidence graph_path must end at the retrieved provision"
                )

    @property
    def document_id(self) -> str:
        return cast(Provision, self.snapshot.provision).document_id

    @property
    def provision_id(self) -> str:
        return cast(Provision, self.snapshot.provision).id

    @property
    def version_id(self) -> str:
        return cast(ProvisionVersion, self.snapshot.version).id

    @property
    def level(self) -> ProvisionLevel:
        return cast(Provision, self.snapshot.provision).level

    @property
    def text(self) -> str:
        return cast(str, self.snapshot.text)

    @property
    def validity(self) -> TemporalInterval:
        return cast(ProvisionVersion, self.snapshot.version).validity

    @property
    def provenance(self) -> tuple[Provenance, ...]:
        return self.snapshot.provenance


@dataclass(frozen=True, slots=True)
class Citation:
    """A citation claim kept separate from the evidence used to verify it."""

    id: str
    evidence_id: str
    document_id: str
    level: CitationLevel
    label: str
    provision_id: str | None = None
    version_id: str | None = None
    supporting_text: str | None = None

    def __post_init__(self) -> None:
        _require_text(self.id, "citation id")
        _require_text(self.evidence_id, "citation evidence_id")
        _require_text(self.document_id, "citation document_id")
        _require_enum(self.level, CitationLevel, "citation level")
        _require_text(self.label, "citation label")
        if self.level is CitationLevel.DOCUMENT:
            if self.provision_id is not None or self.version_id is not None:
                raise QueryModelError(
                    "a document citation cannot claim provision or version IDs"
                )
        else:
            _require_text(self.provision_id, "citation provision_id")
            _require_text(self.version_id, "citation version_id")
        if self.supporting_text is not None:
            _require_text(self.supporting_text, "citation supporting_text")


@dataclass(frozen=True, slots=True)
class AnswerClaim:
    """One checkable answer statement and the citations attached to it."""

    id: str
    text: str
    citation_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _require_text(self.id, "claim id")
        _require_text(self.text, "claim text")
        _require_unique_strings(self.citation_ids, "claim citation_ids")


@dataclass(frozen=True, slots=True)
class VerificationIssue:
    """One machine-readable reason a result failed or needs review."""

    code: VerificationIssueCode
    severity: VerificationSeverity
    message: str
    claim_id: str | None = None
    citation_id: str | None = None
    evidence_id: str | None = None

    def __post_init__(self) -> None:
        _require_enum(self.code, VerificationIssueCode, "verification issue code")
        _require_enum(
            self.severity,
            VerificationSeverity,
            "verification issue severity",
        )
        _require_text(self.message, "verification issue message")
        for value, name in (
            (self.claim_id, "verification issue claim_id"),
            (self.citation_id, "verification issue citation_id"),
            (self.evidence_id, "verification issue evidence_id"),
        ):
            if value is not None:
                _require_text(value, name)


@dataclass(frozen=True, slots=True)
class VerificationResult:
    """Auditable verifier outcome with explicit accepted and rejected IDs."""

    query_id: str
    decision: VerificationDecision
    issues: tuple[VerificationIssue, ...] = ()
    verified_evidence_ids: tuple[str, ...] = ()
    verified_citation_ids: tuple[str, ...] = ()
    rejected_citation_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _require_text(self.query_id, "verification query_id")
        _require_enum(self.decision, VerificationDecision, "verification decision")
        _require_tuple_items(self.issues, VerificationIssue, "verification issues")
        _require_unique_strings(
            self.verified_evidence_ids, "verification verified_evidence_ids"
        )
        _require_unique_strings(
            self.verified_citation_ids, "verification verified_citation_ids"
        )
        _require_unique_strings(
            self.rejected_citation_ids, "verification rejected_citation_ids"
        )
        overlap = set(self.verified_citation_ids) & set(
            self.rejected_citation_ids
        )
        if overlap:
            raise QueryModelError(
                "verified and rejected citation IDs must be disjoint"
            )
        has_error = any(
            item.severity is VerificationSeverity.ERROR for item in self.issues
        )
        if self.decision is VerificationDecision.PASSED:
            if has_error or self.rejected_citation_ids:
                raise QueryModelError(
                    "a passed verification cannot contain errors or rejected citations"
                )
        elif self.decision is VerificationDecision.FAILED:
            if not has_error:
                raise QueryModelError(
                    "a failed verification requires an error issue"
                )
        elif not self.issues:
            raise QueryModelError("needs-review verification requires an issue")


@dataclass(frozen=True, slots=True)
class AnswerResult:
    """Complete answer artifact retained for verification and evaluation."""

    id: str
    query: TemporalQuery
    text: str
    status: AnswerStatus
    evidence: tuple[RetrievedEvidence, ...]
    citations: tuple[Citation, ...]
    claims: tuple[AnswerClaim, ...]
    verification: VerificationResult

    def __post_init__(self) -> None:
        _require_text(self.id, "answer id")
        if not isinstance(self.query, TemporalQuery):
            raise QueryModelError("answer query must be a TemporalQuery")
        _require_text(self.text, "answer text")
        _require_enum(self.status, AnswerStatus, "answer status")
        _require_tuple_items(self.evidence, RetrievedEvidence, "answer evidence")
        _require_tuple_items(self.citations, Citation, "answer citations")
        _require_tuple_items(self.claims, AnswerClaim, "answer claims")
        if not isinstance(self.verification, VerificationResult):
            raise QueryModelError(
                "answer verification must be a VerificationResult"
            )
        _require_unique_entity_ids(self.evidence, "answer evidence")
        _require_unique_entity_ids(self.citations, "answer citations")
        _require_unique_entity_ids(self.claims, "answer claims")
        if self.verification.query_id != self.query.id:
            raise QueryModelError("verification must belong to the answer query")

        evidence_by_id = {item.id: item for item in self.evidence}
        citations_by_id = {item.id: item for item in self.citations}
        claim_ids = {item.id for item in self.claims}
        for item in self.evidence:
            if item.query_id != self.query.id:
                raise QueryModelError("all evidence must belong to the answer query")
            if self.query.at is None or item.snapshot.at != self.query.at:
                raise QueryModelError(
                    "all evidence must use the resolved query date"
                )
        for item in self.citations:
            if item.evidence_id not in evidence_by_id:
                raise QueryModelError(
                    f"citation refers to unknown evidence: {item.evidence_id}"
                )
        for item in self.claims:
            missing = set(item.citation_ids) - citations_by_id.keys()
            if missing:
                raise QueryModelError(
                    f"claim refers to unknown citations: {sorted(missing)}"
                )
        self._validate_verification_references(
            evidence_by_id, citations_by_id, claim_ids
        )

        if self.status is AnswerStatus.ANSWERED:
            if not self.query.temporal_ready:
                raise QueryModelError("an answered result requires a resolved date")
            if not self.evidence or not self.citations or not self.claims:
                raise QueryModelError(
                    "an answered result requires evidence, citations and claims"
                )
            if self.verification.decision is not VerificationDecision.PASSED:
                raise QueryModelError(
                    "an answered result requires passed verification"
                )
            if set(self.verification.verified_citation_ids) != set(
                citations_by_id
            ):
                raise QueryModelError(
                    "a passed answer must verify every citation"
                )
            if any(not item.citation_ids for item in self.claims):
                raise QueryModelError(
                    "every claim in an answered result requires a citation"
                )
            cited_ids = {
                citation_id
                for claim in self.claims
                for citation_id in claim.citation_ids
            }
            if cited_ids != set(citations_by_id):
                raise QueryModelError(
                    "every citation in an answered result must support a claim"
                )
            cited_evidence_ids = {
                citations_by_id[citation_id].evidence_id
                for citation_id in cited_ids
            }
            if not cited_evidence_ids.issubset(
                self.verification.verified_evidence_ids
            ):
                raise QueryModelError(
                    "every cited evidence item must be verified"
                )
        elif self.status is AnswerStatus.INSUFFICIENT_EVIDENCE:
            if self.verification.decision is VerificationDecision.PASSED:
                raise QueryModelError(
                    "an insufficient-evidence result cannot pass verification"
                )
        elif self.verification.decision is not VerificationDecision.NEEDS_REVIEW:
            raise QueryModelError(
                "a needs-review answer requires needs-review verification"
            )

    def _validate_verification_references(
        self,
        evidence_by_id: dict[str, RetrievedEvidence],
        citations_by_id: dict[str, Citation],
        claim_ids: set[str],
    ) -> None:
        verified_evidence = set(self.verification.verified_evidence_ids)
        if verified_evidence - evidence_by_id.keys():
            raise QueryModelError("verification refers to unknown evidence")
        classified_citations = set(self.verification.verified_citation_ids) | set(
            self.verification.rejected_citation_ids
        )
        if classified_citations - citations_by_id.keys():
            raise QueryModelError("verification refers to unknown citations")
        for issue in self.verification.issues:
            if issue.claim_id is not None and issue.claim_id not in claim_ids:
                raise QueryModelError("verification issue refers to an unknown claim")
            if (
                issue.citation_id is not None
                and issue.citation_id not in citations_by_id
            ):
                raise QueryModelError(
                    "verification issue refers to an unknown citation"
                )
            if (
                issue.evidence_id is not None
                and issue.evidence_id not in evidence_by_id
            ):
                raise QueryModelError(
                    "verification issue refers to unknown evidence"
                )


def citation_level_for(level: ProvisionLevel) -> CitationLevel:
    """Map a provision level to its user-facing citation granularity."""
    _require_enum(level, ProvisionLevel, "provision level")
    return CitationLevel(level.value.lower())


def _require_text(value: object, name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise QueryModelError(f"{name} must not be empty")


def _require_enum(value: object, expected: type[Enum], name: str) -> None:
    if not isinstance(value, expected):
        raise QueryModelError(f"{name} must be {expected.__name__}")


def _require_tuple_items(value: object, expected: type, name: str) -> None:
    if not isinstance(value, tuple) or any(
        not isinstance(item, expected) for item in value
    ):
        raise QueryModelError(f"{name} must be a tuple of {expected.__name__}")


def _require_unique_strings(value: object, name: str) -> None:
    if not isinstance(value, tuple):
        raise QueryModelError(f"{name} must be a tuple")
    for item in value:
        _require_text(item, name)
    if len(value) != len(set(value)):
        raise QueryModelError(f"{name} must not contain duplicates")


def _require_unique_entity_ids(value: tuple, name: str) -> None:
    ids = tuple(item.id for item in value)
    if len(ids) != len(set(ids)):
        raise QueryModelError(f"{name} must not contain duplicate IDs")


def _require_finite_number(value: object, name: str) -> None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise QueryModelError(f"{name} must be a number")
    if not math.isfinite(float(value)):
        raise QueryModelError(f"{name} must be finite")


def _positive_int(value: object, name: str) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise QueryModelError(f"{name} must be a positive integer")


def _optional_positive_int(value: object, name: str) -> None:
    if value is not None:
        _positive_int(value, name)


def _optional_confidence(value: object, name: str) -> None:
    if value is None:
        return
    _require_finite_number(value, name)
    if not 0.0 <= float(value) <= 1.0:
        raise QueryModelError(f"{name} must be between 0 and 1")

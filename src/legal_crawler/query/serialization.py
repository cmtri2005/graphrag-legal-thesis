"""Strict, versioned JSON serialization for query and verification artifacts.

Query artifacts are persisted separately from temporal domain records because
the two schemas evolve for different reasons. Nested domain objects retain
their own temporal schema envelope, preventing a query-schema migration from
silently changing the meaning of a provision version or legal event.
"""
from __future__ import annotations

import json
import math
from collections.abc import Callable, Mapping
from datetime import date
from enum import Enum
from typing import Any, TypeAlias, cast

from legal_crawler.temporal.models import (
    LegalEvent,
    Provenance,
    Provision,
    ProvisionLevel,
    ProvisionVersion,
    RelationType,
)
from legal_crawler.temporal.serialization import (
    SerializationError as TemporalSerializationError,
    from_record as temporal_from_record,
    to_record as temporal_to_record,
)
from legal_crawler.temporal.snapshot import SnapshotResult
from legal_crawler.temporal.validity import InvalidityReason, ValidityResult

from .models import (
    AnswerClaim,
    AnswerResult,
    AnswerStatus,
    Citation,
    CitationLevel,
    GraphTraversalStep,
    QueryModelError,
    RetrievedEvidence,
    RetrievalMethod,
    RetrievalSignal,
    TemporalQuery,
    TemporalResolution,
    VerificationDecision,
    VerificationIssue,
    VerificationIssueCode,
    VerificationResult,
    VerificationSeverity,
)

QUERY_SCHEMA_VERSION = 1

QueryArtifact: TypeAlias = (
    TemporalQuery
    | RetrievalSignal
    | GraphTraversalStep
    | RetrievedEvidence
    | Citation
    | AnswerClaim
    | VerificationIssue
    | VerificationResult
    | AnswerResult
)
JsonValue: TypeAlias = (
    None | bool | int | float | str | list["JsonValue"] | dict[str, "JsonValue"]
)


class QuerySerializationError(ValueError):
    """Base class for query artifact serialization failures."""


class UnsupportedQuerySchemaVersionError(QuerySerializationError):
    """The artifact uses an unsupported query schema version."""


class UnknownQueryRecordTypeError(QuerySerializationError):
    """The top-level query artifact type is unknown."""


class InvalidQueryRecordError(QuerySerializationError):
    """A query record is malformed or violates a model invariant."""


def to_record(value: QueryArtifact) -> dict[str, JsonValue]:
    """Convert a query artifact to a versioned JSON-compatible record."""
    record_type, data = _encode_artifact(value)
    return {
        "schema_version": QUERY_SCHEMA_VERSION,
        "type": record_type,
        "data": data,
    }


def from_record(record: Mapping[str, Any]) -> QueryArtifact:
    """Decode a strict record and re-run every query model invariant."""
    envelope = _mapping(record, "record")
    _fields(
        envelope,
        required={"schema_version", "type", "data"},
        context="record",
    )
    schema_version = envelope["schema_version"]
    if isinstance(schema_version, bool) or not isinstance(schema_version, int):
        raise InvalidQueryRecordError("record.schema_version must be an integer")
    if schema_version != QUERY_SCHEMA_VERSION:
        raise UnsupportedQuerySchemaVersionError(
            f"unsupported query schema_version {schema_version}; "
            f"expected {QUERY_SCHEMA_VERSION}"
        )
    record_type = _string(envelope["type"], "record.type")
    decoder = _DECODERS.get(record_type)
    if decoder is None:
        raise UnknownQueryRecordTypeError(
            f"unsupported query record type: {record_type}"
        )
    data = _mapping(envelope["data"], "record.data")
    try:
        return decoder(data)
    except QuerySerializationError:
        raise
    except (QueryModelError, TypeError, ValueError) as exc:
        raise InvalidQueryRecordError(f"invalid {record_type}: {exc}") from exc


def dumps(value: QueryArtifact, *, indent: int | None = None) -> str:
    """Serialize an artifact as deterministic UTF-8-friendly JSON."""
    options: dict[str, Any] = {
        "ensure_ascii": False,
        "sort_keys": True,
        "allow_nan": False,
    }
    if indent is None:
        options["separators"] = (",", ":")
    else:
        options["indent"] = indent
    try:
        return json.dumps(to_record(value), **options)
    except (TypeError, ValueError) as exc:
        raise QuerySerializationError(
            f"artifact is not JSON compatible: {exc}"
        ) from exc


def loads(payload: str) -> QueryArtifact:
    """Decode JSON while rejecting duplicate keys and non-finite constants."""
    if not isinstance(payload, str):
        raise InvalidQueryRecordError("JSON payload must be text")
    try:
        decoded = json.loads(
            payload,
            object_pairs_hook=_object_without_duplicate_keys,
            parse_constant=_reject_non_finite_constant,
        )
    except json.JSONDecodeError as exc:
        raise InvalidQueryRecordError(
            f"invalid JSON at line {exc.lineno}, column {exc.colno}: {exc.msg}"
        ) from exc
    return from_record(_mapping(decoded, "JSON root"))


def _encode_artifact(value: QueryArtifact) -> tuple[str, dict[str, JsonValue]]:
    if isinstance(value, TemporalQuery):
        return "TemporalQuery", _encode_query(value)
    if isinstance(value, RetrievalSignal):
        return "RetrievalSignal", _encode_signal(value)
    if isinstance(value, GraphTraversalStep):
        return "GraphTraversalStep", _encode_graph_step(value)
    if isinstance(value, RetrievedEvidence):
        return "RetrievedEvidence", _encode_evidence(value)
    if isinstance(value, Citation):
        return "Citation", _encode_citation(value)
    if isinstance(value, AnswerClaim):
        return "AnswerClaim", _encode_claim(value)
    if isinstance(value, VerificationIssue):
        return "VerificationIssue", _encode_issue(value)
    if isinstance(value, VerificationResult):
        return "VerificationResult", _encode_verification(value)
    if isinstance(value, AnswerResult):
        return "AnswerResult", _encode_answer(value)
    raise QuerySerializationError(
        f"unsupported query artifact: {type(value).__name__}"
    )


def _encode_query(value: TemporalQuery) -> dict[str, JsonValue]:
    return {
        "id": value.id,
        "text": value.text,
        "at": _date_text(value.at),
        "temporal_resolution": value.temporal_resolution.value,
        "temporal_expression": value.temporal_expression,
        "temporal_confidence": value.temporal_confidence,
        "document_ids": list(value.document_ids),
        "levels": sorted(item.value for item in value.levels),
    }


def _encode_signal(value: RetrievalSignal) -> dict[str, JsonValue]:
    return {
        "method": value.method.value,
        "score": value.score,
        "rank": value.rank,
    }


def _encode_graph_step(value: GraphTraversalStep) -> dict[str, JsonValue]:
    return {
        "edge_id": value.edge_id,
        "source_id": value.source_id,
        "relation": value.relation.value,
        "target_id": value.target_id,
    }


def _encode_validity(value: ValidityResult) -> dict[str, JsonValue]:
    return {
        "provision_id": value.provision_id,
        "at": value.at.isoformat(),
        "valid": value.valid,
        "version": _encode_domain(value.version),
        "reason": value.reason.value if value.reason else None,
        "invalid_ancestor_id": value.invalid_ancestor_id,
        "caused_by_event_id": value.caused_by_event_id,
    }


def _encode_snapshot(value: SnapshotResult) -> dict[str, JsonValue]:
    return {
        "provision": _encode_domain(value.provision),
        "at": value.at.isoformat(),
        "validity": _encode_validity(value.validity),
        "version": _encode_domain(value.version),
        "created_by_event": _encode_domain(value.created_by_event),
        "ended_by_event": _encode_domain(value.ended_by_event),
        "caused_by_event": _encode_domain(value.caused_by_event),
        "provenance": [_domain_record(item) for item in value.provenance],
        "warnings": list(value.warnings),
    }


def _encode_evidence(value: RetrievedEvidence) -> dict[str, JsonValue]:
    return {
        "id": value.id,
        "query_id": value.query_id,
        "snapshot": _encode_snapshot(value.snapshot),
        "signals": [_encode_signal(item) for item in value.signals],
        "rank": value.rank,
        "final_score": value.final_score,
        "graph_path": [_encode_graph_step(item) for item in value.graph_path],
    }


def _encode_citation(value: Citation) -> dict[str, JsonValue]:
    return {
        "id": value.id,
        "evidence_id": value.evidence_id,
        "document_id": value.document_id,
        "level": value.level.value,
        "label": value.label,
        "provision_id": value.provision_id,
        "version_id": value.version_id,
        "supporting_text": value.supporting_text,
    }


def _encode_claim(value: AnswerClaim) -> dict[str, JsonValue]:
    return {
        "id": value.id,
        "text": value.text,
        "citation_ids": list(value.citation_ids),
    }


def _encode_issue(value: VerificationIssue) -> dict[str, JsonValue]:
    return {
        "code": value.code.value,
        "severity": value.severity.value,
        "message": value.message,
        "claim_id": value.claim_id,
        "citation_id": value.citation_id,
        "evidence_id": value.evidence_id,
    }


def _encode_verification(value: VerificationResult) -> dict[str, JsonValue]:
    return {
        "query_id": value.query_id,
        "decision": value.decision.value,
        "issues": [_encode_issue(item) for item in value.issues],
        "verified_evidence_ids": list(value.verified_evidence_ids),
        "verified_citation_ids": list(value.verified_citation_ids),
        "rejected_citation_ids": list(value.rejected_citation_ids),
    }


def _encode_answer(value: AnswerResult) -> dict[str, JsonValue]:
    return {
        "id": value.id,
        "query": _encode_query(value.query),
        "text": value.text,
        "status": value.status.value,
        "evidence": [_encode_evidence(item) for item in value.evidence],
        "citations": [_encode_citation(item) for item in value.citations],
        "claims": [_encode_claim(item) for item in value.claims],
        "verification": _encode_verification(value.verification),
    }


def _decode_query(data: Mapping[str, Any]) -> TemporalQuery:
    _fields(
        data,
        required={
            "id",
            "text",
            "at",
            "temporal_resolution",
            "temporal_expression",
            "temporal_confidence",
            "document_ids",
            "levels",
        },
        context="TemporalQuery",
    )
    return TemporalQuery(
        id=_string(data["id"], "TemporalQuery.id"),
        text=_string(data["text"], "TemporalQuery.text"),
        at=_optional_date(data["at"], "TemporalQuery.at"),
        temporal_resolution=_enum(
            TemporalResolution,
            data["temporal_resolution"],
            "TemporalQuery.temporal_resolution",
        ),
        temporal_expression=_optional_string(
            data["temporal_expression"], "TemporalQuery.temporal_expression"
        ),
        temporal_confidence=_optional_number(
            data["temporal_confidence"], "TemporalQuery.temporal_confidence"
        ),
        document_ids=_string_tuple(
            data["document_ids"], "TemporalQuery.document_ids"
        ),
        levels=_enum_frozenset(
            ProvisionLevel, data["levels"], "TemporalQuery.levels"
        ),
    )


def _decode_signal(data: Mapping[str, Any]) -> RetrievalSignal:
    _fields(
        data,
        required={"method", "score", "rank"},
        context="RetrievalSignal",
    )
    return RetrievalSignal(
        method=_enum(RetrievalMethod, data["method"], "RetrievalSignal.method"),
        score=_number(data["score"], "RetrievalSignal.score"),
        rank=_optional_integer(data["rank"], "RetrievalSignal.rank"),
    )


def _decode_graph_step(data: Mapping[str, Any]) -> GraphTraversalStep:
    _fields(
        data,
        required={"edge_id", "source_id", "relation", "target_id"},
        context="GraphTraversalStep",
    )
    return GraphTraversalStep(
        edge_id=_string(data["edge_id"], "GraphTraversalStep.edge_id"),
        source_id=_string(data["source_id"], "GraphTraversalStep.source_id"),
        relation=_enum(
            RelationType, data["relation"], "GraphTraversalStep.relation"
        ),
        target_id=_string(data["target_id"], "GraphTraversalStep.target_id"),
    )


def _decode_validity(data: Mapping[str, Any]) -> ValidityResult:
    _fields(
        data,
        required={
            "provision_id",
            "at",
            "valid",
            "version",
            "reason",
            "invalid_ancestor_id",
            "caused_by_event_id",
        },
        context="ValidityResult",
    )
    result = ValidityResult(
        provision_id=_string(data["provision_id"], "ValidityResult.provision_id"),
        at=_date(data["at"], "ValidityResult.at"),
        valid=_boolean(data["valid"], "ValidityResult.valid"),
        version=_optional_domain(
            data["version"], ProvisionVersion, "ValidityResult.version"
        ),
        reason=_optional_enum(
            InvalidityReason, data["reason"], "ValidityResult.reason"
        ),
        invalid_ancestor_id=_optional_string(
            data["invalid_ancestor_id"], "ValidityResult.invalid_ancestor_id"
        ),
        caused_by_event_id=_optional_string(
            data["caused_by_event_id"], "ValidityResult.caused_by_event_id"
        ),
    )
    _validate_validity(result)
    return result


def _decode_snapshot(data: Mapping[str, Any]) -> SnapshotResult:
    _fields(
        data,
        required={
            "provision",
            "at",
            "validity",
            "version",
            "created_by_event",
            "ended_by_event",
            "caused_by_event",
            "provenance",
            "warnings",
        },
        context="SnapshotResult",
    )
    result = SnapshotResult(
        provision=_optional_domain(
            data["provision"], Provision, "SnapshotResult.provision"
        ),
        at=_date(data["at"], "SnapshotResult.at"),
        validity=_decode_validity(
            _mapping(data["validity"], "SnapshotResult.validity")
        ),
        version=_optional_domain(
            data["version"], ProvisionVersion, "SnapshotResult.version"
        ),
        created_by_event=_optional_domain(
            data["created_by_event"], LegalEvent, "SnapshotResult.created_by_event"
        ),
        ended_by_event=_optional_domain(
            data["ended_by_event"], LegalEvent, "SnapshotResult.ended_by_event"
        ),
        caused_by_event=_optional_domain(
            data["caused_by_event"], LegalEvent, "SnapshotResult.caused_by_event"
        ),
        provenance=_domain_tuple(
            data["provenance"], Provenance, "SnapshotResult.provenance"
        ),
        warnings=_string_tuple(data["warnings"], "SnapshotResult.warnings"),
    )
    _validate_snapshot(result)
    return result


def _decode_evidence(data: Mapping[str, Any]) -> RetrievedEvidence:
    _fields(
        data,
        required={
            "id",
            "query_id",
            "snapshot",
            "signals",
            "rank",
            "final_score",
            "graph_path",
        },
        context="RetrievedEvidence",
    )
    return RetrievedEvidence(
        id=_string(data["id"], "RetrievedEvidence.id"),
        query_id=_string(data["query_id"], "RetrievedEvidence.query_id"),
        snapshot=_decode_snapshot(
            _mapping(data["snapshot"], "RetrievedEvidence.snapshot")
        ),
        signals=_model_tuple(
            data["signals"], "RetrievedEvidence.signals", _decode_signal
        ),
        rank=_integer(data["rank"], "RetrievedEvidence.rank"),
        final_score=_optional_number(
            data["final_score"], "RetrievedEvidence.final_score"
        ),
        graph_path=_model_tuple(
            data["graph_path"], "RetrievedEvidence.graph_path", _decode_graph_step
        ),
    )


def _decode_citation(data: Mapping[str, Any]) -> Citation:
    _fields(
        data,
        required={
            "id",
            "evidence_id",
            "document_id",
            "level",
            "label",
            "provision_id",
            "version_id",
            "supporting_text",
        },
        context="Citation",
    )
    return Citation(
        id=_string(data["id"], "Citation.id"),
        evidence_id=_string(data["evidence_id"], "Citation.evidence_id"),
        document_id=_string(data["document_id"], "Citation.document_id"),
        level=_enum(CitationLevel, data["level"], "Citation.level"),
        label=_string(data["label"], "Citation.label"),
        provision_id=_optional_string(data["provision_id"], "Citation.provision_id"),
        version_id=_optional_string(data["version_id"], "Citation.version_id"),
        supporting_text=_optional_string(
            data["supporting_text"], "Citation.supporting_text"
        ),
    )


def _decode_claim(data: Mapping[str, Any]) -> AnswerClaim:
    _fields(
        data,
        required={"id", "text", "citation_ids"},
        context="AnswerClaim",
    )
    return AnswerClaim(
        id=_string(data["id"], "AnswerClaim.id"),
        text=_string(data["text"], "AnswerClaim.text"),
        citation_ids=_string_tuple(data["citation_ids"], "AnswerClaim.citation_ids"),
    )


def _decode_issue(data: Mapping[str, Any]) -> VerificationIssue:
    _fields(
        data,
        required={
            "code",
            "severity",
            "message",
            "claim_id",
            "citation_id",
            "evidence_id",
        },
        context="VerificationIssue",
    )
    return VerificationIssue(
        code=_enum(
            VerificationIssueCode, data["code"], "VerificationIssue.code"
        ),
        severity=_enum(
            VerificationSeverity,
            data["severity"],
            "VerificationIssue.severity",
        ),
        message=_string(data["message"], "VerificationIssue.message"),
        claim_id=_optional_string(data["claim_id"], "VerificationIssue.claim_id"),
        citation_id=_optional_string(
            data["citation_id"], "VerificationIssue.citation_id"
        ),
        evidence_id=_optional_string(
            data["evidence_id"], "VerificationIssue.evidence_id"
        ),
    )


def _decode_verification(data: Mapping[str, Any]) -> VerificationResult:
    _fields(
        data,
        required={
            "query_id",
            "decision",
            "issues",
            "verified_evidence_ids",
            "verified_citation_ids",
            "rejected_citation_ids",
        },
        context="VerificationResult",
    )
    return VerificationResult(
        query_id=_string(data["query_id"], "VerificationResult.query_id"),
        decision=_enum(
            VerificationDecision,
            data["decision"],
            "VerificationResult.decision",
        ),
        issues=_model_tuple(
            data["issues"], "VerificationResult.issues", _decode_issue
        ),
        verified_evidence_ids=_string_tuple(
            data["verified_evidence_ids"],
            "VerificationResult.verified_evidence_ids",
        ),
        verified_citation_ids=_string_tuple(
            data["verified_citation_ids"],
            "VerificationResult.verified_citation_ids",
        ),
        rejected_citation_ids=_string_tuple(
            data["rejected_citation_ids"],
            "VerificationResult.rejected_citation_ids",
        ),
    )


def _decode_answer(data: Mapping[str, Any]) -> AnswerResult:
    _fields(
        data,
        required={
            "id",
            "query",
            "text",
            "status",
            "evidence",
            "citations",
            "claims",
            "verification",
        },
        context="AnswerResult",
    )
    return AnswerResult(
        id=_string(data["id"], "AnswerResult.id"),
        query=_decode_query(_mapping(data["query"], "AnswerResult.query")),
        text=_string(data["text"], "AnswerResult.text"),
        status=_enum(AnswerStatus, data["status"], "AnswerResult.status"),
        evidence=_model_tuple(
            data["evidence"], "AnswerResult.evidence", _decode_evidence
        ),
        citations=_model_tuple(
            data["citations"], "AnswerResult.citations", _decode_citation
        ),
        claims=_model_tuple(data["claims"], "AnswerResult.claims", _decode_claim),
        verification=_decode_verification(
            _mapping(data["verification"], "AnswerResult.verification")
        ),
    )


_DECODERS: dict[str, Callable[[Mapping[str, Any]], QueryArtifact]] = {
    "TemporalQuery": _decode_query,
    "RetrievalSignal": _decode_signal,
    "GraphTraversalStep": _decode_graph_step,
    "RetrievedEvidence": _decode_evidence,
    "Citation": _decode_citation,
    "AnswerClaim": _decode_claim,
    "VerificationIssue": _decode_issue,
    "VerificationResult": _decode_verification,
    "AnswerResult": _decode_answer,
}


def _validate_validity(value: ValidityResult) -> None:
    if value.version is not None and value.version.provision_id != value.provision_id:
        raise InvalidQueryRecordError(
            "ValidityResult.version must belong to its provision"
        )
    if value.valid:
        if value.version is None:
            raise InvalidQueryRecordError(
                "a valid ValidityResult requires a version"
            )
        if value.reason is not None or value.invalid_ancestor_id is not None:
            raise InvalidQueryRecordError(
                "a valid ValidityResult cannot have an invalidity reason or ancestor"
            )
        if value.caused_by_event_id is not None:
            raise InvalidQueryRecordError(
                "a valid ValidityResult cannot have a causing event"
            )
        if not value.version.validity.contains(value.at):
            raise InvalidQueryRecordError(
                "ValidityResult.version must be effective at its date"
            )
    elif value.reason is None:
        raise InvalidQueryRecordError(
            "an invalid ValidityResult requires an invalidity reason"
        )


def _validate_snapshot(value: SnapshotResult) -> None:
    if value.validity.at != value.at:
        raise InvalidQueryRecordError(
            "SnapshotResult validity date must match snapshot date"
        )
    if (
        value.provision is not None
        and value.validity.provision_id != value.provision.id
    ):
        raise InvalidQueryRecordError(
            "SnapshotResult validity must belong to its provision"
        )
    if value.validity.valid:
        if value.version != value.validity.version:
            raise InvalidQueryRecordError(
                "valid SnapshotResult must expose its selected version"
            )
    elif value.version is not None:
        raise InvalidQueryRecordError(
            "invalid SnapshotResult cannot expose text version for retrieval"
        )
    expected_provenance = value.version.provenance if value.version else ()
    if value.provenance != expected_provenance:
        raise InvalidQueryRecordError(
            "SnapshotResult provenance must match its exposed version"
        )
    relevant = value.validity.version
    if value.created_by_event is not None:
        if (
            relevant is None
            or relevant.created_by_event_id != value.created_by_event.id
        ):
            raise InvalidQueryRecordError(
                "SnapshotResult created_by_event does not match its version"
            )
    if value.ended_by_event is not None:
        if relevant is None or relevant.ended_by_event_id != value.ended_by_event.id:
            raise InvalidQueryRecordError(
                "SnapshotResult ended_by_event does not match its version"
            )
    if value.caused_by_event is not None:
        if value.validity.caused_by_event_id != value.caused_by_event.id:
            raise InvalidQueryRecordError(
                "SnapshotResult caused_by_event does not match validity"
            )


def _domain_record(value: object) -> dict[str, JsonValue]:
    try:
        return cast(dict[str, JsonValue], temporal_to_record(value))
    except TemporalSerializationError as exc:
        raise QuerySerializationError(f"invalid nested temporal model: {exc}") from exc


def _encode_domain(value: object | None) -> dict[str, JsonValue] | None:
    return None if value is None else _domain_record(value)


def _optional_domain(value: Any, expected: type, context: str):
    if value is None:
        return None
    return _decode_domain(value, expected, context)


def _decode_domain(value: Any, expected: type, context: str):
    try:
        decoded = temporal_from_record(_mapping(value, context))
    except TemporalSerializationError as exc:
        raise InvalidQueryRecordError(f"{context} is invalid: {exc}") from exc
    if not isinstance(decoded, expected):
        raise InvalidQueryRecordError(
            f"{context} must contain a {expected.__name__} record"
        )
    return decoded


def _domain_tuple(value: Any, expected: type, context: str) -> tuple:
    return tuple(
        _decode_domain(item, expected, f"{context}[{index}]")
        for index, item in enumerate(_list(value, context))
    )


def _date_text(value: date | None) -> str | None:
    return value.isoformat() if value else None


def _date(value: Any, context: str) -> date:
    text = _string(value, context)
    try:
        parsed = date.fromisoformat(text)
    except ValueError as exc:
        raise InvalidQueryRecordError(
            f"{context} must be an ISO 8601 date"
        ) from exc
    if parsed.isoformat() != text:
        raise InvalidQueryRecordError(
            f"{context} must use canonical YYYY-MM-DD format"
        )
    return parsed


def _optional_date(value: Any, context: str) -> date | None:
    return None if value is None else _date(value, context)


def _enum(enum_type: type[Enum], value: Any, context: str):
    raw = _string(value, context)
    try:
        return enum_type(raw)
    except ValueError as exc:
        allowed = ", ".join(str(item.value) for item in enum_type)
        raise InvalidQueryRecordError(
            f"{context} must be one of: {allowed}"
        ) from exc


def _optional_enum(enum_type: type[Enum], value: Any, context: str):
    return None if value is None else _enum(enum_type, value, context)


def _enum_frozenset(
    enum_type: type[Enum], value: Any, context: str
) -> frozenset:
    items = tuple(
        _enum(enum_type, item, f"{context}[{index}]")
        for index, item in enumerate(_list(value, context))
    )
    if len(items) != len(set(items)):
        raise InvalidQueryRecordError(f"{context} must not contain duplicates")
    return frozenset(items)


def _mapping(value: Any, context: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise InvalidQueryRecordError(f"{context} must be an object")
    if any(not isinstance(key, str) for key in value):
        raise InvalidQueryRecordError(f"{context} keys must be strings")
    return value


def _fields(
    data: Mapping[str, Any],
    *,
    required: set[str],
    context: str,
) -> None:
    missing = sorted(required - data.keys())
    unknown = sorted(data.keys() - required)
    if missing:
        raise InvalidQueryRecordError(
            f"{context} is missing fields: {', '.join(missing)}"
        )
    if unknown:
        raise InvalidQueryRecordError(
            f"{context} has unknown fields: {', '.join(unknown)}"
        )


def _string(value: Any, context: str) -> str:
    if not isinstance(value, str):
        raise InvalidQueryRecordError(f"{context} must be a string")
    if not value:
        raise InvalidQueryRecordError(f"{context} must not be empty")
    return value


def _optional_string(value: Any, context: str) -> str | None:
    return None if value is None else _string(value, context)


def _boolean(value: Any, context: str) -> bool:
    if not isinstance(value, bool):
        raise InvalidQueryRecordError(f"{context} must be a boolean")
    return value


def _integer(value: Any, context: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise InvalidQueryRecordError(f"{context} must be an integer")
    return value


def _optional_integer(value: Any, context: str) -> int | None:
    return None if value is None else _integer(value, context)


def _number(value: Any, context: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise InvalidQueryRecordError(f"{context} must be a number")
    result = float(value)
    if not math.isfinite(result):
        raise InvalidQueryRecordError(f"{context} must be finite")
    return result


def _optional_number(value: Any, context: str) -> float | None:
    return None if value is None else _number(value, context)


def _list(value: Any, context: str) -> list[Any]:
    if not isinstance(value, list):
        raise InvalidQueryRecordError(f"{context} must be an array")
    return value


def _string_tuple(value: Any, context: str) -> tuple[str, ...]:
    return tuple(
        _string(item, f"{context}[{index}]")
        for index, item in enumerate(_list(value, context))
    )


def _model_tuple(value: Any, context: str, decoder: Callable) -> tuple:
    return tuple(
        decoder(_mapping(item, f"{context}[{index}]"))
        for index, item in enumerate(_list(value, context))
    )


def _object_without_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise InvalidQueryRecordError(f"duplicate JSON object key: {key}")
        result[key] = value
    return result


def _reject_non_finite_constant(value: str) -> None:
    raise InvalidQueryRecordError(f"JSON numeric constant is not finite: {value}")

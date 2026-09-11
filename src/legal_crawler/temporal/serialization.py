"""Versioned JSON serialization for temporal legal domain models.

The wire format is deliberately explicit and storage-neutral. Every top-level
record carries a schema version and model type; nested dates and enums use
stable string values. Decoding is strict so malformed or newer records cannot
silently change legal meaning by dropping fields.
"""
from __future__ import annotations

import json
import math
from collections.abc import Callable, Mapping
from datetime import date
from enum import Enum
from typing import Any, TypeAlias

from .models import (
    EventStatus,
    ExtractionMethod,
    GraphEdge,
    LegalDocument,
    LegalEvent,
    LegalOperation,
    Provenance,
    Provision,
    ProvisionInsertion,
    ProvisionLevel,
    ProvisionVersion,
    RelationType,
    TemporalInterval,
    TextUpdate,
)

SCHEMA_VERSION = 1

DomainModel: TypeAlias = (
    TemporalInterval
    | Provenance
    | LegalDocument
    | Provision
    | ProvisionVersion
    | TextUpdate
    | ProvisionInsertion
    | LegalEvent
    | GraphEdge
)
JsonValue: TypeAlias = (
    None | bool | int | float | str | list["JsonValue"] | dict[str, "JsonValue"]
)


class SerializationError(ValueError):
    """Base class for an invalid serialization or deserialization request."""


class UnsupportedSchemaVersionError(SerializationError):
    """The record belongs to a schema version this code does not understand."""


class UnknownRecordTypeError(SerializationError):
    """The top-level record type is not a supported temporal domain model."""


class InvalidRecordError(SerializationError):
    """A record is malformed, ambiguous or violates domain invariants."""


def to_record(value: DomainModel) -> dict[str, JsonValue]:
    """Convert one domain model to a versioned, JSON-compatible record."""
    record_type, data = _encode_model(value)
    return {
        "schema_version": SCHEMA_VERSION,
        "type": record_type,
        "data": data,
    }


def from_record(record: Mapping[str, Any]) -> DomainModel:
    """Reconstruct one domain model from a strict versioned record."""
    envelope = _mapping(record, "record")
    _fields(
        envelope,
        required={"schema_version", "type", "data"},
        context="record",
    )
    schema_version = envelope["schema_version"]
    if isinstance(schema_version, bool) or not isinstance(schema_version, int):
        raise InvalidRecordError("record.schema_version must be an integer")
    if schema_version != SCHEMA_VERSION:
        raise UnsupportedSchemaVersionError(
            f"unsupported schema_version {schema_version}; expected {SCHEMA_VERSION}"
        )

    record_type = _string(envelope["type"], "record.type")
    data = _mapping(envelope["data"], "record.data")
    decoder = _DECODERS.get(record_type)
    if decoder is None:
        raise UnknownRecordTypeError(f"unsupported record type: {record_type}")
    try:
        return decoder(data)
    except SerializationError:
        raise
    except (TypeError, ValueError) as exc:
        raise InvalidRecordError(f"invalid {record_type}: {exc}") from exc


def dumps(value: DomainModel, *, indent: int | None = None) -> str:
    """Serialize a model as deterministic UTF-8-friendly JSON text."""
    options: dict[str, Any] = {
        "ensure_ascii": False,
        "sort_keys": True,
        "allow_nan": False,
    }
    if indent is None:
        options["separators"] = (",", ":")
    else:
        options["indent"] = indent
    return json.dumps(to_record(value), **options)


def loads(payload: str) -> DomainModel:
    """Deserialize JSON text while rejecting duplicate object keys."""
    if not isinstance(payload, str):
        raise InvalidRecordError("JSON payload must be text")
    try:
        decoded = json.loads(
            payload,
            object_pairs_hook=_object_without_duplicate_keys,
            parse_constant=_reject_non_finite_constant,
        )
    except json.JSONDecodeError as exc:
        raise InvalidRecordError(
            f"invalid JSON at line {exc.lineno}, column {exc.colno}: {exc.msg}"
        ) from exc
    return from_record(_mapping(decoded, "JSON root"))


def _encode_model(value: DomainModel) -> tuple[str, dict[str, JsonValue]]:
    if isinstance(value, TemporalInterval):
        return "TemporalInterval", _encode_interval(value)
    if isinstance(value, Provenance):
        return "Provenance", _encode_provenance(value)
    if isinstance(value, LegalDocument):
        return "LegalDocument", _encode_document(value)
    if isinstance(value, Provision):
        return "Provision", _encode_provision(value)
    if isinstance(value, ProvisionVersion):
        return "ProvisionVersion", _encode_version(value)
    if isinstance(value, TextUpdate):
        return "TextUpdate", _encode_text_update(value)
    if isinstance(value, ProvisionInsertion):
        return "ProvisionInsertion", _encode_insertion(value)
    if isinstance(value, LegalEvent):
        return "LegalEvent", _encode_event(value)
    if isinstance(value, GraphEdge):
        return "GraphEdge", _encode_edge(value)
    raise SerializationError(f"unsupported domain model: {type(value).__name__}")


def _encode_interval(value: TemporalInterval) -> dict[str, JsonValue]:
    return {"start": value.start.isoformat(), "end": _date_text(value.end)}


def _encode_provenance(value: Provenance) -> dict[str, JsonValue]:
    return {
        "source_document_id": value.source_document_id,
        "method": value.method.value,
        "source_provision_id": value.source_provision_id,
        "evidence_text": value.evidence_text,
        "source_url": value.source_url,
        "confidence": value.confidence,
        "details": _json_value(value.details, "Provenance.details"),
    }


def _encode_document(value: LegalDocument) -> dict[str, JsonValue]:
    return {
        "id": value.id,
        "number": value.number,
        "title": value.title,
        "issued_on": _date_text(value.issued_on),
        "effective_from": _date_text(value.effective_from),
        "effective_to": _date_text(value.effective_to),
        "issuer": value.issuer,
        "rank": value.rank,
        "source_url": value.source_url,
        "raw_status_code": value.raw_status_code,
    }


def _encode_provision(value: Provision) -> dict[str, JsonValue]:
    return {
        "id": value.id,
        "document_id": value.document_id,
        "level": value.level.value,
        "title": value.title,
        "parent_id": value.parent_id,
        "order_index": value.order_index,
        "inserted_after_id": value.inserted_after_id,
    }


def _encode_version(value: ProvisionVersion) -> dict[str, JsonValue]:
    return {
        "id": value.id,
        "provision_id": value.provision_id,
        "ordinal": value.ordinal,
        "text": value.text,
        "validity": _encode_interval(value.validity),
        "created_by_event_id": value.created_by_event_id,
        "ended_by_event_id": value.ended_by_event_id,
        "provenance": [_encode_provenance(item) for item in value.provenance],
    }


def _encode_text_update(value: TextUpdate) -> dict[str, JsonValue]:
    return {
        "target_provision_id": value.target_provision_id,
        "new_text": value.new_text,
    }


def _encode_insertion(value: ProvisionInsertion) -> dict[str, JsonValue]:
    return {
        "provision_id": value.provision_id,
        "level": value.level.value,
        "title": value.title,
        "text": value.text,
        "parent_id": value.parent_id,
        "after_provision_id": value.after_provision_id,
        "order_index": value.order_index,
    }


def _encode_event(value: LegalEvent) -> dict[str, JsonValue]:
    return {
        "id": value.id,
        "operation": value.operation.value,
        "source_document_id": value.source_document_id,
        "target_document_id": value.target_document_id,
        "effective_on": _date_text(value.effective_on),
        "target_provision_ids": list(value.target_provision_ids),
        "new_text": value.new_text,
        "text_updates": [_encode_text_update(item) for item in value.text_updates],
        "insertions": [_encode_insertion(item) for item in value.insertions],
        "status": value.status.value,
        "provenance": [_encode_provenance(item) for item in value.provenance],
    }


def _encode_edge(value: GraphEdge) -> dict[str, JsonValue]:
    return {
        "source_id": value.source_id,
        "target_id": value.target_id,
        "relation": value.relation.value,
        "validity": _encode_interval(value.validity) if value.validity else None,
        "provenance": [_encode_provenance(item) for item in value.provenance],
        "properties": _json_value(value.properties, "GraphEdge.properties"),
    }


def _decode_interval(data: Mapping[str, Any]) -> TemporalInterval:
    _fields(data, required={"start"}, optional={"end"}, context="TemporalInterval")
    return TemporalInterval(
        start=_date(data["start"], "TemporalInterval.start"),
        end=_optional_date(data.get("end"), "TemporalInterval.end"),
    )


def _decode_provenance(data: Mapping[str, Any]) -> Provenance:
    _fields(
        data,
        required={"source_document_id", "method"},
        optional={
            "source_provision_id",
            "evidence_text",
            "source_url",
            "confidence",
            "details",
        },
        context="Provenance",
    )
    return Provenance(
        source_document_id=_string(
            data["source_document_id"], "Provenance.source_document_id"
        ),
        method=_enum(ExtractionMethod, data["method"], "Provenance.method"),
        source_provision_id=_optional_string(
            data.get("source_provision_id"), "Provenance.source_provision_id"
        ),
        evidence_text=_optional_string(
            data.get("evidence_text"), "Provenance.evidence_text"
        ),
        source_url=_optional_string(data.get("source_url"), "Provenance.source_url"),
        confidence=_number(data.get("confidence", 1.0), "Provenance.confidence"),
        details=_json_mapping(data.get("details", {}), "Provenance.details"),
    )


def _decode_document(data: Mapping[str, Any]) -> LegalDocument:
    _fields(
        data,
        required={"id", "number", "title"},
        optional={
            "issued_on",
            "effective_from",
            "effective_to",
            "issuer",
            "rank",
            "source_url",
            "raw_status_code",
        },
        context="LegalDocument",
    )
    return LegalDocument(
        id=_string(data["id"], "LegalDocument.id"),
        number=_string(data["number"], "LegalDocument.number", allow_empty=True),
        title=_string(data["title"], "LegalDocument.title", allow_empty=True),
        issued_on=_optional_date(data.get("issued_on"), "LegalDocument.issued_on"),
        effective_from=_optional_date(
            data.get("effective_from"), "LegalDocument.effective_from"
        ),
        effective_to=_optional_date(
            data.get("effective_to"), "LegalDocument.effective_to"
        ),
        issuer=_optional_string(data.get("issuer"), "LegalDocument.issuer"),
        rank=_optional_string(data.get("rank"), "LegalDocument.rank"),
        source_url=_optional_string(data.get("source_url"), "LegalDocument.source_url"),
        raw_status_code=_optional_string(
            data.get("raw_status_code"), "LegalDocument.raw_status_code"
        ),
    )


def _decode_provision(data: Mapping[str, Any]) -> Provision:
    _fields(
        data,
        required={"id", "document_id", "level", "title", "parent_id"},
        optional={"order_index", "inserted_after_id"},
        context="Provision",
    )
    return Provision(
        id=_string(data["id"], "Provision.id"),
        document_id=_string(data["document_id"], "Provision.document_id"),
        level=_enum(ProvisionLevel, data["level"], "Provision.level"),
        title=_string(data["title"], "Provision.title", allow_empty=True),
        parent_id=_optional_string(data["parent_id"], "Provision.parent_id"),
        order_index=_optional_integer(data.get("order_index"), "Provision.order_index"),
        inserted_after_id=_optional_string(
            data.get("inserted_after_id"), "Provision.inserted_after_id"
        ),
    )


def _decode_version(data: Mapping[str, Any]) -> ProvisionVersion:
    _fields(
        data,
        required={"id", "provision_id", "ordinal", "text", "validity"},
        optional={"created_by_event_id", "ended_by_event_id", "provenance"},
        context="ProvisionVersion",
    )
    return ProvisionVersion(
        id=_string(data["id"], "ProvisionVersion.id"),
        provision_id=_string(data["provision_id"], "ProvisionVersion.provision_id"),
        ordinal=_integer(data["ordinal"], "ProvisionVersion.ordinal"),
        text=_string(data["text"], "ProvisionVersion.text", allow_empty=True),
        validity=_decode_interval(_mapping(data["validity"], "ProvisionVersion.validity")),
        created_by_event_id=_optional_string(
            data.get("created_by_event_id"), "ProvisionVersion.created_by_event_id"
        ),
        ended_by_event_id=_optional_string(
            data.get("ended_by_event_id"), "ProvisionVersion.ended_by_event_id"
        ),
        provenance=_provenance_tuple(
            data.get("provenance", []), "ProvisionVersion.provenance"
        ),
    )


def _decode_text_update(data: Mapping[str, Any]) -> TextUpdate:
    _fields(
        data,
        required={"target_provision_id", "new_text"},
        context="TextUpdate",
    )
    return TextUpdate(
        target_provision_id=_string(
            data["target_provision_id"], "TextUpdate.target_provision_id"
        ),
        new_text=_string(data["new_text"], "TextUpdate.new_text"),
    )


def _decode_insertion(data: Mapping[str, Any]) -> ProvisionInsertion:
    _fields(
        data,
        required={"provision_id", "level", "title", "text", "parent_id"},
        optional={"after_provision_id", "order_index"},
        context="ProvisionInsertion",
    )
    return ProvisionInsertion(
        provision_id=_string(data["provision_id"], "ProvisionInsertion.provision_id"),
        level=_enum(ProvisionLevel, data["level"], "ProvisionInsertion.level"),
        title=_string(data["title"], "ProvisionInsertion.title"),
        text=_string(data["text"], "ProvisionInsertion.text"),
        parent_id=_optional_string(
            data["parent_id"], "ProvisionInsertion.parent_id"
        ),
        after_provision_id=_optional_string(
            data.get("after_provision_id"),
            "ProvisionInsertion.after_provision_id",
        ),
        order_index=_optional_integer(
            data.get("order_index"), "ProvisionInsertion.order_index"
        ),
    )


def _decode_event(data: Mapping[str, Any]) -> LegalEvent:
    _fields(
        data,
        required={
            "id",
            "operation",
            "source_document_id",
            "target_document_id",
            "effective_on",
        },
        optional={
            "target_provision_ids",
            "new_text",
            "text_updates",
            "insertions",
            "status",
            "provenance",
        },
        context="LegalEvent",
    )
    return LegalEvent(
        id=_string(data["id"], "LegalEvent.id"),
        operation=_enum(LegalOperation, data["operation"], "LegalEvent.operation"),
        source_document_id=_string(
            data["source_document_id"], "LegalEvent.source_document_id"
        ),
        target_document_id=_string(
            data["target_document_id"], "LegalEvent.target_document_id"
        ),
        effective_on=_optional_date(data["effective_on"], "LegalEvent.effective_on"),
        target_provision_ids=_string_tuple(
            data.get("target_provision_ids", []), "LegalEvent.target_provision_ids"
        ),
        new_text=_optional_string(data.get("new_text"), "LegalEvent.new_text"),
        text_updates=_model_tuple(
            data.get("text_updates", []),
            "LegalEvent.text_updates",
            _decode_text_update,
        ),
        insertions=_model_tuple(
            data.get("insertions", []),
            "LegalEvent.insertions",
            _decode_insertion,
        ),
        status=_enum(
            EventStatus,
            data.get("status", EventStatus.NEEDS_REVIEW.value),
            "LegalEvent.status",
        ),
        provenance=_provenance_tuple(
            data.get("provenance", []), "LegalEvent.provenance"
        ),
    )


def _decode_edge(data: Mapping[str, Any]) -> GraphEdge:
    _fields(
        data,
        required={"source_id", "target_id", "relation"},
        optional={"validity", "provenance", "properties"},
        context="GraphEdge",
    )
    validity_data = data.get("validity")
    return GraphEdge(
        source_id=_string(data["source_id"], "GraphEdge.source_id"),
        target_id=_string(data["target_id"], "GraphEdge.target_id"),
        relation=_enum(RelationType, data["relation"], "GraphEdge.relation"),
        validity=(
            _decode_interval(_mapping(validity_data, "GraphEdge.validity"))
            if validity_data is not None
            else None
        ),
        provenance=_provenance_tuple(
            data.get("provenance", []), "GraphEdge.provenance"
        ),
        properties=_json_mapping(data.get("properties", {}), "GraphEdge.properties"),
    )


_DECODERS: dict[str, Callable[[Mapping[str, Any]], DomainModel]] = {
    "TemporalInterval": _decode_interval,
    "Provenance": _decode_provenance,
    "LegalDocument": _decode_document,
    "Provision": _decode_provision,
    "ProvisionVersion": _decode_version,
    "TextUpdate": _decode_text_update,
    "ProvisionInsertion": _decode_insertion,
    "LegalEvent": _decode_event,
    "GraphEdge": _decode_edge,
}


def _date_text(value: date | None) -> str | None:
    return value.isoformat() if value else None


def _date(value: Any, context: str) -> date:
    text = _string(value, context)
    try:
        parsed = date.fromisoformat(text)
    except ValueError as exc:
        raise InvalidRecordError(f"{context} must be an ISO 8601 date") from exc
    if parsed.isoformat() != text:
        raise InvalidRecordError(f"{context} must use canonical YYYY-MM-DD format")
    return parsed


def _optional_date(value: Any, context: str) -> date | None:
    return None if value is None else _date(value, context)


def _enum(enum_type: type[Enum], value: Any, context: str):
    raw = _string(value, context)
    try:
        return enum_type(raw)
    except ValueError as exc:
        allowed = ", ".join(str(item.value) for item in enum_type)
        raise InvalidRecordError(f"{context} must be one of: {allowed}") from exc


def _mapping(value: Any, context: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise InvalidRecordError(f"{context} must be an object")
    if any(not isinstance(key, str) for key in value):
        raise InvalidRecordError(f"{context} keys must be strings")
    return value


def _fields(
    data: Mapping[str, Any],
    *,
    required: set[str],
    optional: set[str] | None = None,
    context: str,
) -> None:
    optional = optional or set()
    missing = sorted(required - data.keys())
    unknown = sorted(data.keys() - required - optional)
    if missing:
        raise InvalidRecordError(f"{context} is missing fields: {', '.join(missing)}")
    if unknown:
        raise InvalidRecordError(f"{context} has unknown fields: {', '.join(unknown)}")


def _string(value: Any, context: str, *, allow_empty: bool = False) -> str:
    if not isinstance(value, str):
        raise InvalidRecordError(f"{context} must be a string")
    if not allow_empty and not value:
        raise InvalidRecordError(f"{context} must not be empty")
    return value


def _optional_string(value: Any, context: str) -> str | None:
    return None if value is None else _string(value, context, allow_empty=True)


def _integer(value: Any, context: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise InvalidRecordError(f"{context} must be an integer")
    return value


def _optional_integer(value: Any, context: str) -> int | None:
    return None if value is None else _integer(value, context)


def _number(value: Any, context: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise InvalidRecordError(f"{context} must be a number")
    result = float(value)
    if not math.isfinite(result):
        raise InvalidRecordError(f"{context} must be finite")
    return result


def _list(value: Any, context: str) -> list[Any]:
    if not isinstance(value, list):
        raise InvalidRecordError(f"{context} must be an array")
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


def _provenance_tuple(value: Any, context: str) -> tuple[Provenance, ...]:
    return _model_tuple(value, context, _decode_provenance)


def _json_mapping(value: Any, context: str) -> dict[str, JsonValue]:
    mapping = _mapping(value, context)
    return {
        key: _json_value(item, f"{context}.{key}") for key, item in mapping.items()
    }


def _json_value(value: Any, context: str) -> JsonValue:
    if value is None or isinstance(value, (bool, str)):
        return value
    if isinstance(value, int) and not isinstance(value, bool):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise SerializationError(f"{context} must not contain NaN or infinity")
        return value
    if isinstance(value, list):
        return [_json_value(item, f"{context}[{index}]") for index, item in enumerate(value)]
    if isinstance(value, Mapping):
        if any(not isinstance(key, str) for key in value):
            raise SerializationError(f"{context} object keys must be strings")
        return {
            key: _json_value(item, f"{context}.{key}") for key, item in value.items()
        }
    raise SerializationError(
        f"{context} contains non-JSON value of type {type(value).__name__}"
    )


def _object_without_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise InvalidRecordError(f"duplicate JSON object key: {key}")
        result[key] = value
    return result


def _reject_non_finite_constant(value: str):
    raise InvalidRecordError(f"non-finite JSON number is not allowed: {value}")

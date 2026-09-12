"""Strict Milvus representation of version-aware legal embeddings."""
from __future__ import annotations

import json
import math
from dataclasses import dataclass
from datetime import date
from types import MappingProxyType
from typing import Any, Mapping

from legal_crawler.ports import VersionEmbedding
from legal_crawler.temporal import Provenance, ProvisionLevel, TemporalInterval
from legal_crawler.temporal.serialization import from_record, to_record

EMBEDDING_SCHEMA_VERSION = 1
OPEN_END_ORDINAL = 3_652_060
MAX_FILTER_TEXT_BYTES = 512
MAX_JSON_BYTES = 65_536

_DATA_FIELDS = {
    "id",
    "version_id",
    "provision_id",
    "document_id",
    "model",
    "vector",
    "validity",
    "level",
    "provenance",
    "metadata",
}


class MilvusCodecError(ValueError):
    """An embedding cannot be represented without losing domain meaning."""


@dataclass(frozen=True, slots=True)
class MilvusEmbeddingRecord:
    """One complete Milvus row with explicit scalar filter projections."""

    id: str
    vector: tuple[float, ...]
    payload: Mapping[str, Any]
    version_id: str
    provision_id: str
    document_id: str
    model: str
    level: str
    eff_from: int
    eff_to: int
    schema_version: int = EMBEDDING_SCHEMA_VERSION

    def __post_init__(self) -> None:
        for value, name in (
            (self.id, "embedding id"),
            (self.version_id, "version id"),
            (self.provision_id, "provision id"),
            (self.document_id, "document id"),
            (self.model, "embedding model"),
            (self.level, "provision level"),
        ):
            _bounded_text(value, name)
        _vector(self.vector)
        if not isinstance(self.payload, Mapping):
            raise MilvusCodecError("embedding payload must be a mapping")
        payload = _json_copy(self.payload, "embedding payload")
        object.__setattr__(self, "payload", MappingProxyType(payload))
        for value, name in (
            (self.eff_from, "eff_from"),
            (self.eff_to, "eff_to"),
            (self.schema_version, "schema_version"),
        ):
            if isinstance(value, bool) or not isinstance(value, int):
                raise MilvusCodecError(f"{name} must be an integer")
        if self.eff_to <= self.eff_from:
            raise MilvusCodecError("embedding validity projection is empty")
        if self.schema_version != EMBEDDING_SCHEMA_VERSION:
            raise MilvusCodecError("unsupported embedding schema version")

    def fields(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "vector": list(self.vector),
            "payload": dict(self.payload),
            "version_id": self.version_id,
            "provision_id": self.provision_id,
            "document_id": self.document_id,
            "model": self.model,
            "level": self.level,
            "eff_from": self.eff_from,
            "eff_to": self.eff_to,
            "schema_version": self.schema_version,
        }


def encode_embedding(value: VersionEmbedding) -> MilvusEmbeddingRecord:
    """Encode an embedding while keeping a versioned authoritative payload."""
    if not isinstance(value, VersionEmbedding):
        raise TypeError("value must be a VersionEmbedding")
    payload = {
        "schema_version": EMBEDDING_SCHEMA_VERSION,
        "type": "VersionEmbedding",
        "data": {
            "id": value.id,
            "version_id": value.version_id,
            "provision_id": value.provision_id,
            "document_id": value.document_id,
            "model": value.model,
            "vector": [float(item) for item in value.vector],
            "validity": {
                "start": value.validity.start.isoformat(),
                "end": value.validity.end.isoformat() if value.validity.end else None,
            },
            "level": value.level.value,
            "provenance": [to_record(item) for item in value.provenance],
            "metadata": _json_copy(value.metadata, "embedding metadata"),
        },
    }
    return MilvusEmbeddingRecord(
        id=value.id,
        vector=tuple(float(item) for item in value.vector),
        payload=payload,
        version_id=value.version_id,
        provision_id=value.provision_id,
        document_id=value.document_id,
        model=value.model,
        level=value.level.value,
        eff_from=value.validity.start.toordinal(),
        eff_to=(
            value.validity.end.toordinal()
            if value.validity.end
            else OPEN_END_ORDINAL
        ),
    )


def decode_embedding(fields: Mapping[str, Any]) -> VersionEmbedding:
    """Decode the payload and verify every identity and temporal projection."""
    row = _mapping(fields, "Milvus embedding row")
    payload = _mapping(row.get("payload"), "embedding payload")
    if set(payload) != {"schema_version", "type", "data"}:
        raise MilvusCodecError("embedding payload envelope has invalid fields")
    if payload.get("schema_version") != EMBEDDING_SCHEMA_VERSION:
        raise MilvusCodecError("unsupported embedding schema version")
    if payload.get("type") != "VersionEmbedding":
        raise MilvusCodecError("embedding payload has an invalid type")
    data = _mapping(payload.get("data"), "embedding payload data")
    if set(data) != _DATA_FIELDS:
        raise MilvusCodecError("embedding payload data has invalid fields")
    try:
        validity_data = _mapping(data["validity"], "embedding validity")
        if set(validity_data) != {"start", "end"}:
            raise MilvusCodecError("embedding validity has invalid fields")
        validity = TemporalInterval(
            _date_value(validity_data["start"], "validity start"),
            (
                _date_value(validity_data["end"], "validity end")
                if validity_data["end"] is not None
                else None
            ),
        )
        provenance = tuple(
            _provenance(item)
            for item in _list(data["provenance"], "embedding provenance")
        )
        value = VersionEmbedding(
            id=_required_text(data["id"], "embedding id"),
            version_id=_required_text(data["version_id"], "version id"),
            provision_id=_required_text(data["provision_id"], "provision id"),
            document_id=_required_text(data["document_id"], "document id"),
            model=_required_text(data["model"], "embedding model"),
            vector=tuple(_number(item) for item in _list(data["vector"], "vector")),
            validity=validity,
            level=ProvisionLevel(_required_text(data["level"], "provision level")),
            provenance=provenance,
            metadata=_json_copy(
                _mapping(data["metadata"], "embedding metadata"),
                "embedding metadata",
            ),
        )
    except MilvusCodecError:
        raise
    except (TypeError, ValueError) as exc:
        raise MilvusCodecError(f"invalid embedding payload: {exc}") from exc
    expected = encode_embedding(value)
    for name, expected_value in (
        ("id", expected.id),
        ("version_id", expected.version_id),
        ("provision_id", expected.provision_id),
        ("document_id", expected.document_id),
        ("model", expected.model),
        ("level", expected.level),
        ("eff_from", expected.eff_from),
        ("eff_to", expected.eff_to),
        ("schema_version", expected.schema_version),
    ):
        if row.get(name) != expected_value:
            raise MilvusCodecError(
                f"embedding {name} does not match its authoritative payload"
            )
    projected_vector = row.get("vector")
    if not isinstance(projected_vector, (list, tuple)):
        raise MilvusCodecError("embedding vector projection must be a list")
    try:
        actual_vector = tuple(_number(item) for item in projected_vector)
    except MilvusCodecError as exc:
        raise MilvusCodecError("embedding vector projection is invalid") from exc
    if len(actual_vector) != len(expected.vector) or any(
        not math.isclose(actual, projected, rel_tol=1e-6, abs_tol=1e-7)
        for actual, projected in zip(expected.vector, actual_vector)
    ):
        raise MilvusCodecError(
            "embedding vector does not match its authoritative payload"
        )
    return value


def _provenance(value: object) -> Provenance:
    try:
        decoded = from_record(_mapping(value, "provenance record"))
    except (TypeError, ValueError) as exc:
        raise MilvusCodecError(f"invalid provenance record: {exc}") from exc
    if not isinstance(decoded, Provenance):
        raise MilvusCodecError("embedding provenance record has an invalid type")
    return decoded


def _date_value(value: object, name: str) -> date:
    text = _required_text(value, name)
    try:
        parsed = date.fromisoformat(text)
    except ValueError as exc:
        raise MilvusCodecError(f"{name} must be an ISO date") from exc
    if parsed.isoformat() != text:
        raise MilvusCodecError(f"{name} must be a canonical ISO date")
    return parsed


def _mapping(value: object, name: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise MilvusCodecError(f"{name} must be a mapping")
    return value


def _list(value: object, name: str) -> list[Any]:
    if not isinstance(value, list):
        raise MilvusCodecError(f"{name} must be a list")
    return value


def _required_text(value: object, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise MilvusCodecError(f"{name} must not be empty")
    return value


def _bounded_text(value: object, name: str) -> str:
    text = _required_text(value, name)
    if len(text.encode("utf-8")) > MAX_FILTER_TEXT_BYTES:
        raise MilvusCodecError(
            f"{name} exceeds {MAX_FILTER_TEXT_BYTES} UTF-8 bytes"
        )
    return text


def _number(value: object) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise MilvusCodecError("vector components must be numbers")
    result = float(value)
    if not math.isfinite(result):
        raise MilvusCodecError("vector components must be finite")
    return result


def _vector(value: object) -> None:
    if not isinstance(value, tuple) or not value:
        raise MilvusCodecError("vector must be a non-empty tuple")
    for item in value:
        _number(item)


def _json_copy(value: object, name: str) -> dict[str, Any]:
    if not isinstance(value, Mapping) or any(
        not isinstance(key, str) for key in value
    ):
        raise MilvusCodecError(f"{name} must use string mapping keys")
    try:
        encoded = json.dumps(
            dict(value),
            ensure_ascii=False,
            sort_keys=True,
            allow_nan=False,
            separators=(",", ":"),
        )
    except (TypeError, ValueError) as exc:
        raise MilvusCodecError(f"{name} must contain JSON-compatible values") from exc
    if len(encoded.encode("utf-8")) > MAX_JSON_BYTES:
        raise MilvusCodecError(f"{name} exceeds {MAX_JSON_BYTES} UTF-8 bytes")
    decoded = json.loads(encoded)
    if not isinstance(decoded, dict):
        raise MilvusCodecError(f"{name} must be a JSON object")
    return decoded

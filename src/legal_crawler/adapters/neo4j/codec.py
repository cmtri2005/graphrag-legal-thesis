"""Strict mapping between temporal domain objects and Neo4j properties.

Every record keeps the versioned domain JSON as its authoritative payload.
Selected properties are duplicated only for indexes and Cypher predicates;
decoding never rebuilds legal meaning from those projections.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import date
from types import MappingProxyType
from typing import Any, Mapping, TypeAlias

from legal_crawler.temporal import (
    GraphEdge,
    LegalDocument,
    LegalEvent,
    NodeKind,
    Provision,
    ProvisionVersion,
)
from legal_crawler.temporal.ids import make_edge_id
from legal_crawler.temporal.serialization import dumps, loads


class Neo4jCodecError(ValueError):
    """A domain object cannot be represented by the Neo4j schema."""


NodeModel: TypeAlias = LegalDocument | Provision | ProvisionVersion | LegalEvent


@dataclass(frozen=True, slots=True)
class Neo4jNodeRecord:
    """Driver-neutral node payload ready for a parameterized Cypher query."""

    id: str
    kind: NodeKind
    payload: str
    indexed_properties: Mapping[str, Any]

    def __post_init__(self) -> None:
        _required_text(self.id, "node id")
        if not isinstance(self.kind, NodeKind):
            raise Neo4jCodecError("node kind must be a NodeKind")
        _required_text(self.payload, "node payload")
        properties = _properties(self.indexed_properties, reserved={"id", "kind"})
        object.__setattr__(self, "indexed_properties", MappingProxyType(properties))

    def parameters(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "kind": self.kind.value,
            "payload": self.payload,
            "properties": dict(self.indexed_properties),
        }


@dataclass(frozen=True, slots=True)
class Neo4jEdgeRecord:
    """Driver-neutral relationship payload with a deterministic domain ID."""

    id: str
    source_id: str
    target_id: str
    relation: str
    payload: str
    indexed_properties: Mapping[str, Any]

    def __post_init__(self) -> None:
        for value, name in (
            (self.id, "edge id"),
            (self.source_id, "edge source_id"),
            (self.target_id, "edge target_id"),
            (self.relation, "edge relation"),
            (self.payload, "edge payload"),
        ):
            _required_text(value, name)
        properties = _properties(
            self.indexed_properties,
            reserved={"id", "source_id", "target_id", "relation"},
        )
        object.__setattr__(self, "indexed_properties", MappingProxyType(properties))

    def parameters(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "source_id": self.source_id,
            "target_id": self.target_id,
            "relation": self.relation,
            "payload": self.payload,
            "properties": dict(self.indexed_properties),
        }


def encode_node(value: NodeModel) -> Neo4jNodeRecord:
    """Encode one supported graph node without losing its domain payload."""
    if isinstance(value, LegalDocument):
        properties = {
            "number": value.number,
            "title": value.title,
            "issued_on": _date_text(value.issued_on),
            "eff_from": _date_text(value.effective_from),
            "eff_to": _date_text(value.effective_to),
            "issuer": value.issuer,
            "rank": value.rank,
            "raw_status_code": value.raw_status_code,
        }
    elif isinstance(value, Provision):
        properties = {
            "document_id": value.document_id,
            "level": value.level.value,
            "title": value.title,
            "parent_id": value.parent_id,
            "order_index": value.order_index,
            "inserted_after_id": value.inserted_after_id,
        }
    elif isinstance(value, ProvisionVersion):
        properties = {
            "provision_id": value.provision_id,
            "ordinal": value.ordinal,
            "text": value.text,
            "eff_from": value.validity.start.isoformat(),
            "eff_to": _date_text(value.validity.end),
            "created_by_event_id": value.created_by_event_id,
            "ended_by_event_id": value.ended_by_event_id,
        }
    elif isinstance(value, LegalEvent):
        properties = {
            "operation": value.operation.value,
            "source_document_id": value.source_document_id,
            "target_document_id": value.target_document_id,
            "effective_on": _date_text(value.effective_on),
            "status": value.status.value,
            "resolved_target_ids": list(value.resolved_target_ids),
            "applied": False,
        }
    else:
        raise TypeError("value must be a supported temporal graph node")
    return Neo4jNodeRecord(value.id, value.kind, dumps(value), properties)


def decode_node(
    properties: Mapping[str, Any],
    *,
    expected_type: type[NodeModel] | None = None,
) -> NodeModel:
    """Decode the authoritative payload and verify its indexed identity."""
    record = _mapping(properties, "node properties")
    identifier = _required_text(record.get("id"), "node id")
    raw_kind = _required_text(record.get("kind"), "node kind")
    payload = _required_text(record.get("payload"), "node payload")
    try:
        kind = NodeKind(raw_kind)
        value = loads(payload)
    except (TypeError, ValueError) as exc:
        raise Neo4jCodecError(f"invalid node payload: {exc}") from exc
    if not isinstance(value, (LegalDocument, Provision, ProvisionVersion, LegalEvent)):
        raise Neo4jCodecError("payload is not a supported graph node")
    if value.id != identifier:
        raise Neo4jCodecError("node id does not match its authoritative payload")
    if value.kind is not kind:
        raise Neo4jCodecError("node kind does not match its authoritative payload")
    if expected_type is not None and not isinstance(value, expected_type):
        raise Neo4jCodecError(
            f"expected {expected_type.__name__}, found {type(value).__name__}"
        )
    return value


def encode_edge(value: GraphEdge) -> Neo4jEdgeRecord:
    """Encode a typed edge; relation remains a whitelisted enum value."""
    if not isinstance(value, GraphEdge):
        raise TypeError("value must be a GraphEdge")
    identifier = make_edge_id(
        value.source_id,
        value.relation,
        value.target_id,
        value.validity.start if value.validity else None,
    )
    properties = {
        "eff_from": (
            value.validity.start.isoformat() if value.validity else None
        ),
        "eff_to": _date_text(value.validity.end) if value.validity else None,
    }
    return Neo4jEdgeRecord(
        identifier,
        value.source_id,
        value.target_id,
        value.relation.value,
        dumps(value),
        properties,
    )


def decode_edge(properties: Mapping[str, Any]) -> GraphEdge:
    """Decode an edge and verify identity, endpoints and relationship type."""
    record = _mapping(properties, "edge properties")
    identifier = _required_text(record.get("id"), "edge id")
    source_id = _required_text(record.get("source_id"), "edge source_id")
    target_id = _required_text(record.get("target_id"), "edge target_id")
    relation = _required_text(record.get("relation"), "edge relation")
    payload = _required_text(record.get("payload"), "edge payload")
    try:
        value = loads(payload)
    except (TypeError, ValueError) as exc:
        raise Neo4jCodecError(f"invalid edge payload: {exc}") from exc
    if not isinstance(value, GraphEdge):
        raise Neo4jCodecError("payload is not a GraphEdge")
    expected_id = make_edge_id(
        value.source_id,
        value.relation,
        value.target_id,
        value.validity.start if value.validity else None,
    )
    if identifier != expected_id:
        raise Neo4jCodecError("edge id does not match its authoritative payload")
    if (source_id, target_id, relation) != (
        value.source_id,
        value.target_id,
        value.relation.value,
    ):
        raise Neo4jCodecError(
            "edge endpoints or relation do not match its authoritative payload"
        )
    return value


def _mapping(value: object, name: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise Neo4jCodecError(f"{name} must be a mapping")
    return value


def _required_text(value: object, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise Neo4jCodecError(f"{name} must be a non-empty string")
    return value


def _properties(
    value: object,
    *,
    reserved: set[str],
) -> dict[str, Any]:
    source = _mapping(value, "indexed_properties")
    if reserved.intersection(source):
        raise Neo4jCodecError("indexed properties contain a reserved key")
    result: dict[str, Any] = {}
    for key, item in source.items():
        _required_text(key, "indexed property key")
        if item is not None and not isinstance(item, (bool, int, float, str, list)):
            raise Neo4jCodecError(
                f"indexed property {key} is not a Neo4j scalar or list"
            )
        if isinstance(item, float) and not math.isfinite(item):
            raise Neo4jCodecError(f"indexed property {key} must be finite")
        if isinstance(item, list) and any(
            not isinstance(element, (bool, int, float, str))
            for element in item
        ):
            raise Neo4jCodecError(
                f"indexed property {key} contains an unsupported list value"
            )
        if isinstance(item, list) and any(
            isinstance(element, float) and not math.isfinite(element)
            for element in item
        ):
            raise Neo4jCodecError(
                f"indexed property {key} contains a non-finite number"
            )
        if isinstance(item, list) and len({type(element) for element in item}) > 1:
            raise Neo4jCodecError(
                f"indexed property {key} must contain one scalar type"
            )
        result[key] = item
    return result


def _date_text(value: date | None) -> str | None:
    return value.isoformat() if value is not None else None

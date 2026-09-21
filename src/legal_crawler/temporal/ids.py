"""Deterministic identifiers for temporal legal graph entities.

Domain identifiers must be reproducible across machines, pipeline reruns and
storage backends.  They must never depend on processing order or an internal
Neo4j/Milvus identifier.

Opaque identifiers originating from the source are Unicode-normalized and URL
escaped, except ``#``, the separator of the derived Khoản/Điểm nodes
(``<article>#k2#c``) and no delimiter of any ID.  Composite entities whose
inputs may be long use a SHA-256 digest of canonical JSON; the readable source
prefix is retained for auditability.  An ID that embeds another ID (version,
event) embeds its local part, never the ``provision:``/``document:`` prefix
twice.
"""
from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from collections.abc import Iterable
from datetime import date
from enum import Enum
from urllib.parse import quote

from .models import LegalOperation, RelationType

_WHITESPACE = re.compile(r"\s+")
_DIGEST_LENGTH = 24


def _required(value: object, name: str) -> str:
    normalized = unicodedata.normalize("NFC", str(value)).strip()
    if not normalized:
        raise ValueError(f"{name} must not be empty")
    return normalized


def _escaped(value: object, name: str) -> str:
    """Canonical, delimiter-safe representation of one opaque source ID."""
    return quote(_required(value, name), safe="-._~#")


def _embedded(domain_id: object, prefix: str, name: str) -> str:
    """Local part of an ID this module already built; anything else is escaped."""
    value = _required(domain_id, name)
    return value[len(prefix):] if value.startswith(prefix) else _escaped(value, name)


def _domain_id(value: object, *, prefix: str, name: str) -> str:
    """Return one canonical domain ID without applying its prefix twice.

    Pipeline boundaries receive a mixture of opaque source IDs and domain IDs:
    raw files use the former while derived stores use the latter.  Keeping the
    constructor idempotent lets every boundary normalize defensively without
    turning ``document:123`` into ``document:document%3A123``.
    """
    normalized = _required(value, name)
    if normalized.startswith(prefix):
        if not normalized.removeprefix(prefix):
            raise ValueError(f"{name} must contain an identifier after {prefix}")
        return normalized
    return f"{prefix}{_escaped(normalized, name)}"


def _enum_value(value: Enum | str, name: str) -> str:
    raw = value.value if isinstance(value, Enum) else value
    return _required(raw, name)


def _canonical_text(value: str | None) -> str | None:
    if value is None:
        return None
    # This normalization is only for a fingerprint. The evidence stored in
    # Provenance remains verbatim and is never rewritten.
    return _WHITESPACE.sub(" ", unicodedata.normalize("NFC", value)).strip()


def _digest(payload: dict[str, object]) -> str:
    canonical = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:_DIGEST_LENGTH]


def make_document_id(source_document_id: str) -> str:
    """ID for one source document, accepting both numeric and UUID source IDs."""
    return _domain_id(
        source_document_id,
        prefix="document:",
        name="source_document_id",
    )


def make_provision_id(tree_node_id: str) -> str:
    """ID for a stable provision identity backed by a source tree-node ID."""
    return _domain_id(
        tree_node_id,
        prefix="provision:",
        name="tree_node_id",
    )


def make_version_id(provision_id: str, ordinal: int) -> str:
    """ID for the ``ordinal``-th textual state of a provision."""
    if ordinal < 1:
        raise ValueError("version ordinal starts at 1")
    return f"version:{_embedded(provision_id, 'provision:', 'provision_id')}:{ordinal}"


def make_event_id(
    source_document_id: str,
    operation: LegalOperation | str,
    target_provision_ids: Iterable[str],
    effective_on: date | None,
    *,
    target_document_id: str | None = None,
    evidence_text: str | None = None,
) -> str:
    """Stable ID for a normalized legal event.

    Target order is intentionally ignored: an event affecting Điều 5 and Điều
    7 is the same event regardless of the order in which a resolver returned
    those nodes. Duplicate targets are removed from the fingerprint as well.
    """
    source = _required(source_document_id, "source_document_id")
    targets = sorted(
        {_required(target, "target_provision_id") for target in target_provision_ids}
    )
    payload: dict[str, object] = {
        "source_document_id": source,
        "target_document_id": (
            _required(target_document_id, "target_document_id")
            if target_document_id is not None
            else None
        ),
        "operation": _enum_value(operation, "operation"),
        "target_provision_ids": targets,
        "effective_on": effective_on.isoformat() if effective_on else None,
        "evidence_text": _canonical_text(evidence_text),
    }
    return f"event:{_embedded(source, 'document:', 'source_document_id')}:{_digest(payload)}"


def make_edge_id(
    source_id: str,
    relation: RelationType | str,
    target_id: str,
    valid_from: date | None = None,
) -> str:
    """Stable ID for a graph edge, including its temporal starting point."""
    source = _required(source_id, "source_id")
    target = _required(target_id, "target_id")
    payload: dict[str, object] = {
        "source_id": source,
        "relation": _enum_value(relation, "relation"),
        "target_id": target,
        "valid_from": valid_from.isoformat() if valid_from else None,
    }
    return f"edge:{_digest(payload)}"

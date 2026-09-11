"""Domain primitives for the temporal legal knowledge graph (Stage 6).

The crawler deliberately keeps raw acquisition separate from interpretation.
This package is the boundary between those two concerns: adapters will turn
`data/raw`, `data/trees`, `data/provisions`, and `data/history` records into the
typed, auditable objects exported here.
"""

from .models import (
    EventStatus,
    ExtractionMethod,
    GraphEdge,
    LegalDocument,
    LegalEvent,
    LegalOperation,
    NodeKind,
    Provenance,
    Provision,
    ProvisionLevel,
    ProvisionVersion,
    RelationType,
    TemporalInterval,
)

__all__ = [
    "EventStatus",
    "ExtractionMethod",
    "GraphEdge",
    "LegalDocument",
    "LegalEvent",
    "LegalOperation",
    "NodeKind",
    "Provenance",
    "Provision",
    "ProvisionLevel",
    "ProvisionVersion",
    "RelationType",
    "TemporalInterval",
]


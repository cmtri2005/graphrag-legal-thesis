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
from .ids import (
    make_document_id,
    make_edge_id,
    make_event_id,
    make_provision_id,
    make_version_id,
)
from .version_chain import (
    DuplicateVersionError,
    NoCurrentVersionError,
    OverlappingVersionError,
    ProvisionMismatchError,
    VersionChain,
    VersionChainError,
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
    "DuplicateVersionError",
    "NoCurrentVersionError",
    "OverlappingVersionError",
    "ProvisionMismatchError",
    "VersionChain",
    "VersionChainError",
    "make_document_id",
    "make_edge_id",
    "make_event_id",
    "make_provision_id",
    "make_version_id",
]


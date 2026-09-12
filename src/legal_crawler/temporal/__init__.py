"""Domain primitives for the temporal legal knowledge graph.

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
    ProvisionInsertion,
    ProvisionLevel,
    ProvisionVersion,
    RelationType,
    TemporalInterval,
    TextUpdate,
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
from .state import TemporalState, TemporalStateError
from .event_applier import (
    ApplyResult,
    EventApplicationError,
    EventApplier,
    UnsupportedEventError,
)
from .validity import InvalidityReason, ValidityResult, ValidityService
from .snapshot import SnapshotResult, SnapshotService
from .serialization import (
    SCHEMA_VERSION,
    DomainModel,
    InvalidRecordError,
    SerializationError,
    UnknownRecordTypeError,
    UnsupportedSchemaVersionError,
    dumps,
    from_record,
    loads,
    to_record,
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
    "ProvisionInsertion",
    "ProvisionLevel",
    "ProvisionVersion",
    "RelationType",
    "TemporalInterval",
    "TextUpdate",
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
    "ApplyResult",
    "EventApplicationError",
    "EventApplier",
    "InvalidityReason",
    "SnapshotResult",
    "SnapshotService",
    "TemporalState",
    "TemporalStateError",
    "UnsupportedEventError",
    "ValidityResult",
    "ValidityService",
    "DomainModel",
    "InvalidRecordError",
    "SCHEMA_VERSION",
    "SerializationError",
    "UnknownRecordTypeError",
    "UnsupportedSchemaVersionError",
    "dumps",
    "from_record",
    "loads",
    "to_record",
]

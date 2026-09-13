"""Typed domain model for the temporal legal knowledge graph.

The thesis needs explicit domain concepts before anything is written to Neo4j
or a vector store: a stable legal unit, its successive versions, the event that
created a change, and the evidence behind that interpretation.

These classes are therefore the storage-independent source of truth for the
temporal domain. They intentionally use only the standard library, matching
the crawler's dependency-light design. Database adapters may flatten them
later, but should not redefine their temporal semantics.

All validity intervals are half-open: ``[start, end)``.  A missing ``end``
means the interval is open-ended.  This is the convention in formula (2) of the
thesis proposal and removes ambiguity exactly at a version transition.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from enum import Enum
from typing import Any, Mapping


class NodeKind(str, Enum):
    """Kinds of nodes that may be persisted in the temporal legal graph."""

    DOCUMENT = "Document"
    PROVISION = "Provision"
    PROVISION_VERSION = "ProvisionVersion"
    LEGAL_EVENT = "LegalEvent"


class ProvisionLevel(str, Enum):
    """Levels returned by vbpl.vn's provision-tree server action."""

    PART = "Part"
    CHAPTER = "Chapter"
    SECTION = "Section"
    SUBSECTION = "Subsection"
    ARTICLE = "Article"
    CLAUSE = "Clause"
    POINT = "Point"


class LegalOperation(str, Enum):
    """Normalized legal changes extracted from an acting document (L2)."""

    AMEND = "amend"
    SUPPLEMENT = "supplement"
    REPEAL = "repeal"
    REPLACE = "replace"
    CORRECT = "correct"
    SUSPEND = "suspend"
    RESUME = "resume"


class RelationType(str, Enum):
    """Edge vocabulary, named after what vbpl.vn actually publishes.

    The three structural relations are derived by this package. The rest map
    one-to-one onto a `referenceType` code in `data/reference_type_map.json`;
    the comment on each is the portal's own Vietnamese label and how many such
    edges the corpus holds, so an edge type that stops appearing is visible.
    """

    # derived here, not published by the source
    CONTAINS = "CONTAINS"
    VERSION_OF = "VERSION_OF"
    CAUSED_BY = "CAUSED_BY"

    # published as referenceType, ordered by how common they are
    ISSUED_UNDER = "ISSUED_UNDER"            # 3  Căn cứ ban hành            67,601
    AMENDS = "AMENDS"                        # 10 Văn bản được sửa đổi bổ sung 29,129
    DETAILS = "DETAILS"                      # 9  Được quy định chi tiết      19,559
    REFERS_TO = "REFERS_TO"                  # 4  Văn bản được dẫn chiếu      17,999
    REPEALS = "REPEALS"                      # 1  Văn bản bị bãi bỏ           12,159
    REPLACES = "REPLACES"                    # 12 Văn bản được thay thế        9,772
    CONSOLIDATES = "CONSOLIDATES"            # 7  Văn bản được hợp nhất           874
    GUIDES = "GUIDES"                        # 8  Được hướng dẫn áp dụng          349
    CORRECTS = "CORRECTS"                    # 6  Văn bản được đính chính         209
    SUSPENDS = "SUSPENDS"                    # 11 Bị tạm ngưng hiệu lực            50
    HALTS_ENFORCEMENT = "HALTS_ENFORCEMENT"  # 5  Bị đình chỉ thi hành             47
    INTERPRETS = "INTERPRETS"                # 14 Văn bản được giải thích          24
    ANNOUNCES = "ANNOUNCES"                  # 2  Văn bản được công bố             23


class ExtractionMethod(str, Enum):
    """How a fact or event was obtained, for audit and error analysis."""

    SOURCE_METADATA = "source_metadata"
    HISTORY = "history"
    EXACT_NODE_ID = "exact_node_id"
    RULE = "rule"
    LLM = "llm"
    MANUAL = "manual"


class EventStatus(str, Enum):
    """Whether an extracted event is safe to apply to a version chain."""

    VERIFIED = "verified"
    AUTO_ACCEPTED = "auto_accepted"
    NEEDS_REVIEW = "needs_review"
    REJECTED = "rejected"


@dataclass(frozen=True, slots=True)
class TemporalInterval:
    """A half-open validity interval ``[start, end)``."""

    start: date
    end: date | None = None

    def __post_init__(self) -> None:
        if self.end is not None and self.end <= self.start:
            raise ValueError("temporal interval end must be later than start")

    def contains(self, at: date) -> bool:
        """Return whether ``at`` lies in this interval."""
        return self.start <= at and (self.end is None or at < self.end)

    def overlaps(self, other: "TemporalInterval") -> bool:
        """Return whether two half-open intervals share at least one day."""
        return (self.end is None or other.start < self.end) and (
            other.end is None or self.start < other.end
        )


@dataclass(frozen=True, slots=True)
class Provenance:
    """Trace from an interpreted fact back to evidence in the source corpus."""

    source_document_id: str
    method: ExtractionMethod
    source_provision_id: str | None = None
    evidence_text: str | None = None
    source_url: str | None = None
    confidence: float = 1.0
    details: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.source_document_id:
            raise ValueError("provenance requires source_document_id")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("provenance confidence must be between 0 and 1")


@dataclass(frozen=True, slots=True)
class LegalDocument:
    """One source document; old and expired documents remain first-class."""

    id: str
    number: str
    title: str
    issued_on: date | None = None
    effective_from: date | None = None
    effective_to: date | None = None
    issuer: str | None = None
    rank: str | None = None
    source_url: str | None = None
    raw_status_code: str | None = None

    @property
    def kind(self) -> NodeKind:
        return NodeKind.DOCUMENT

    def __post_init__(self) -> None:
        if not self.id:
            raise ValueError("document id must not be empty")
        if self.effective_from and self.effective_to:
            if self.effective_to <= self.effective_from:
                raise ValueError("document effective_to must be later than effective_from")


@dataclass(frozen=True, slots=True)
class Provision:
    """Stable identity of a legal unit, independent from its changing text.

    ``id`` should be vbpl.vn's tree-node UUID whenever it exists.  A provision
    is not copied for every amendment; its text lives in ``ProvisionVersion``.
    """

    id: str
    document_id: str
    level: ProvisionLevel
    title: str
    parent_id: str | None
    order_index: int | None = None
    inserted_after_id: str | None = None

    @property
    def kind(self) -> NodeKind:
        return NodeKind.PROVISION

    def __post_init__(self) -> None:
        if not self.id or not self.document_id:
            raise ValueError("provision id and document_id must not be empty")
        if self.parent_id == self.id:
            raise ValueError("a provision cannot be its own parent")
        if self.inserted_after_id == self.id:
            raise ValueError("a provision cannot be inserted after itself")
        if self.order_index is not None and self.order_index < 0:
            raise ValueError("provision order_index must not be negative")


@dataclass(frozen=True, slots=True)
class ProvisionVersion:
    """Textual state of a stable provision during one validity interval."""

    id: str
    provision_id: str
    ordinal: int
    text: str
    validity: TemporalInterval | None = None
    created_by_event_id: str | None = None
    ended_by_event_id: str | None = None
    provenance: tuple[Provenance, ...] = ()

    @property
    def kind(self) -> NodeKind:
        return NodeKind.PROVISION_VERSION

    def __post_init__(self) -> None:
        if not self.id or not self.provision_id:
            raise ValueError("version id and provision_id must not be empty")
        if self.ordinal < 1:
            raise ValueError("version ordinal starts at 1")

    def is_valid_at(self, at: date) -> bool:
        """Undated text is never in force: an answer must not rest on a guess."""
        return self.validity is not None and self.validity.contains(at)


@dataclass(frozen=True, slots=True)
class TextUpdate:
    """The complete resulting text for one existing legal provision.

    ``new_text`` is the consolidated content after the operation, not a text
    fragment to append blindly. Phrase-level substitutions will be resolved
    into this form before they reach the event applier.
    """

    target_provision_id: str
    new_text: str

    def __post_init__(self) -> None:
        if not self.target_provision_id:
            raise ValueError("text update target_provision_id must not be empty")
        if not self.new_text.strip():
            raise ValueError("text update new_text must not be empty")


@dataclass(frozen=True, slots=True)
class ProvisionInsertion:
    """A new legal unit introduced at a precise place in the provision tree."""

    provision_id: str
    level: ProvisionLevel
    title: str
    text: str
    parent_id: str | None
    after_provision_id: str | None = None
    order_index: int | None = None

    def __post_init__(self) -> None:
        if not self.provision_id:
            raise ValueError("insertion provision_id must not be empty")
        if not self.title.strip():
            raise ValueError("insertion title must not be empty")
        if not self.text.strip():
            raise ValueError("insertion text must not be empty")
        if self.parent_id == self.provision_id:
            raise ValueError("an inserted provision cannot be its own parent")
        if self.after_provision_id == self.provision_id:
            raise ValueError("an inserted provision cannot be placed after itself")
        if self.order_index is not None and self.order_index < 0:
            raise ValueError("insertion order_index must not be negative")


@dataclass(frozen=True, slots=True)
class LegalEvent:
    """A normalized amendment/repeal event extracted from a legal source.

    ``target_provision_ids`` may be empty while resolution is pending.  Such an
    event must remain ``NEEDS_REVIEW`` and must not be applied to a version
    chain.  This allows extraction and target resolution to be separate,
    auditable stages instead of forcing a guess.
    """

    id: str
    operation: LegalOperation
    source_document_id: str | None
    target_document_id: str
    effective_on: date | None
    target_provision_ids: tuple[str, ...] = ()
    new_text: str | None = None
    text_updates: tuple[TextUpdate, ...] = ()
    insertions: tuple[ProvisionInsertion, ...] = ()
    status: EventStatus = EventStatus.NEEDS_REVIEW
    provenance: tuple[Provenance, ...] = ()

    @property
    def kind(self) -> NodeKind:
        return NodeKind.LEGAL_EVENT

    @property
    def is_applicable(self) -> bool:
        """Only dated, resolved and accepted events may mutate versions."""
        return (
            self.status in {EventStatus.VERIFIED, EventStatus.AUTO_ACCEPTED}
            and self.effective_on is not None
            and bool(self.resolved_target_ids)
        )

    @property
    def resolved_target_ids(self) -> tuple[str, ...]:
        """All existing and newly introduced provisions affected by the event."""
        ordered = (
            *self.target_provision_ids,
            *(update.target_provision_id for update in self.text_updates),
            *(insertion.provision_id for insertion in self.insertions),
        )
        return tuple(dict.fromkeys(ordered))

    def __post_init__(self) -> None:
        if not self.id or not self.target_document_id:
            raise ValueError("event id and target_document_id must not be empty")
        if len(set(self.target_provision_ids)) != len(self.target_provision_ids):
            raise ValueError("target_provision_ids must not contain duplicates")
        if self.new_text is not None and not self.new_text.strip():
            raise ValueError("event new_text must not be empty")
        update_targets = [update.target_provision_id for update in self.text_updates]
        if len(set(update_targets)) != len(update_targets):
            raise ValueError("text_updates must not contain duplicate targets")
        insertion_ids = [insertion.provision_id for insertion in self.insertions]
        if len(set(insertion_ids)) != len(insertion_ids):
            raise ValueError("insertions must not contain duplicate provision ids")
        if self.status in {EventStatus.VERIFIED, EventStatus.AUTO_ACCEPTED}:
            if self.effective_on is None:
                raise ValueError("an accepted event requires effective_on")
            if not self.resolved_target_ids:
                raise ValueError("an accepted event requires at least one resolved target")


@dataclass(frozen=True, slots=True)
class GraphEdge:
    """A typed, optionally temporal edge ready for a graph-store adapter."""

    source_id: str
    target_id: str
    relation: RelationType
    validity: TemporalInterval | None = None
    provenance: tuple[Provenance, ...] = ()
    properties: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.source_id or not self.target_id:
            raise ValueError("edge source_id and target_id must not be empty")

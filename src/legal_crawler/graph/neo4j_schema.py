"""D1 contract for Neo4j's derived temporal legal graph.

Node uniqueness is enforced by Neo4j. The structural relationship endpoints
are a loader contract: Neo4j constraints do not enforce their node labels.
Neither this schema nor the graph becomes the source of legal truth; ``data/``
and the offline version/event artifacts remain rebuildable inputs (ADR 0001).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence

from legal_crawler.temporal import NodeKind, RelationType


@dataclass(frozen=True, slots=True)
class NodeIdConstraint:
    name: str
    kind: NodeKind

    @property
    def cypher(self) -> str:
        return (
            f"CREATE CONSTRAINT {self.name} IF NOT EXISTS "
            f"FOR (n:{self.kind.value}) REQUIRE n.id IS UNIQUE"
        )


NODE_ID_CONSTRAINTS = (
    NodeIdConstraint("kg_document_id_unique", NodeKind.DOCUMENT),
    NodeIdConstraint("kg_provision_id_unique", NodeKind.PROVISION),
    NodeIdConstraint("kg_provision_version_id_unique", NodeKind.PROVISION_VERSION),
    NodeIdConstraint("kg_legal_event_id_unique", NodeKind.LEGAL_EVENT),
)

# (source label, relationship type, target label). D2 uses MERGE by node id.
# CAUSED_BY may represent creation or termination; D2 must retain that role
# explicitly rather than collapsing created_by_event_id and ended_by_event_id.
STRUCTURAL_RELATIONSHIPS = (
    (NodeKind.DOCUMENT, RelationType.CONTAINS, NodeKind.PROVISION),
    (NodeKind.PROVISION, RelationType.CONTAINS, NodeKind.PROVISION),
    (NodeKind.PROVISION_VERSION, RelationType.VERSION_OF, NodeKind.PROVISION),
    (NodeKind.PROVISION_VERSION, RelationType.CAUSED_BY, NodeKind.LEGAL_EVENT),
)


def constraint_statements() -> tuple[str, ...]:
    """Cypher 5 DDL in stable order; each statement is rerunnable."""
    return tuple(item.cypher for item in NODE_ID_CONSTRAINTS)


def verify_constraints(rows: Sequence[Mapping[str, object]]) -> None:
    """Fail if any expected named constraint is absent or has the wrong shape.

    ``IF NOT EXISTS`` can silently do nothing when a name is already used by
    another constraint. A postcondition check prevents that from looking like
    a successful schema installation.
    """
    by_name = {str(row["name"]): row for row in rows}
    for expected in NODE_ID_CONSTRAINTS:
        row = by_name.get(expected.name)
        if row is None:
            raise ValueError(
                f"missing Neo4j constraint {expected.name} for "
                f":{expected.kind.value}(id); rerun init_neo4j_schema.py or "
                "resolve an existing-schema conflict (Phase 3 D1)"
            )
        actual = (
            row.get("entityType"),
            row.get("type"),
            tuple(row.get("labelsOrTypes") or ()),
            tuple(row.get("properties") or ()),
        )
        if (
            actual[0] != "NODE"
            or actual[1] not in {"UNIQUENESS", "NODE_PROPERTY_UNIQUENESS"}
            or actual[2] != (expected.kind.value,)
            or actual[3] != ("id",)
        ):
            raise ValueError(
                f"Neo4j constraint {expected.name} has shape {actual!r}, expected "
                f"unique :{expected.kind.value}(id) (Phase 3 D1); inspect "
                "SHOW CONSTRAINTS before changing existing schema"
            )

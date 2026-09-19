"""D1 schema contract: repeatable DDL and detectable schema drift."""

import pytest

from init_neo4j_schema import SHOW_CONSTRAINTS, ensure_schema, read_schema
from legal_crawler.graph.neo4j_schema import (
    NODE_ID_CONSTRAINTS,
    STRUCTURAL_RELATIONSHIPS,
    constraint_statements,
    verify_constraints,
)
from legal_crawler.temporal import NodeKind, RelationType


def _row(constraint):
    return {
        "name": constraint.name,
        "type": "UNIQUENESS",
        "entityType": "NODE",
        "labelsOrTypes": [constraint.kind.value],
        "properties": ["id"],
    }


class _Result:
    def __init__(self, rows=()):
        self.rows = rows

    def consume(self):
        return None

    def data(self):
        return list(self.rows)


class _Session:
    def __init__(self):
        self.constraints = {}
        self.statements = []

    def run(self, statement):
        self.statements.append(statement)
        if statement == SHOW_CONSTRAINTS:
            return _Result(self.constraints.values())
        constraint = next(item for item in NODE_ID_CONSTRAINTS if item.cypher == statement)
        self.constraints.setdefault(constraint.name, _row(constraint))
        return _Result()


def test_schema_file_matches_four_domain_node_constraints():
    assert {item.kind for item in NODE_ID_CONSTRAINTS} == set(NodeKind)
    assert len({item.name for item in NODE_ID_CONSTRAINTS}) == 4
    assert read_schema() == constraint_statements()
    assert all("IF NOT EXISTS" in statement for statement in read_schema())


def test_structural_relationship_contract_uses_typed_endpoints():
    assert STRUCTURAL_RELATIONSHIPS == (
        (NodeKind.DOCUMENT, RelationType.CONTAINS, NodeKind.PROVISION),
        (NodeKind.PROVISION, RelationType.CONTAINS, NodeKind.PROVISION),
        (NodeKind.PROVISION_VERSION, RelationType.VERSION_OF, NodeKind.PROVISION),
        (NodeKind.PROVISION_VERSION, RelationType.CAUSED_BY, NodeKind.LEGAL_EVENT),
    )


def test_schema_can_run_twice_then_check_without_writing():
    session = _Session()
    ensure_schema(session)
    ensure_schema(session)
    assert len(session.constraints) == 4
    assert session.statements.count(SHOW_CONSTRAINTS) == 2
    before = tuple(session.statements)
    ensure_schema(session, check_only=True)
    assert session.statements == [*before, SHOW_CONSTRAINTS]


def test_missing_constraint_fails_with_actionable_diagnostic():
    with pytest.raises(ValueError, match="missing Neo4j constraint kg_document_id_unique"):
        verify_constraints([])


def test_same_name_with_wrong_schema_fails_instead_of_silent_noop():
    rows = [_row(item) for item in NODE_ID_CONSTRAINTS]
    rows[0]["properties"] = ["external_id"]
    with pytest.raises(ValueError, match=r"kg_document_id_unique has shape.*SHOW CONSTRAINTS"):
        verify_constraints(rows)


def test_schema_file_rejects_extra_ddl(tmp_path):
    path = tmp_path / "neo4j_schema.cypher"
    path.write_text(
        ";\n".join(constraint_statements()) + ";\nMATCH (n) DETACH DELETE n;\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="differs from approved D1 node constraints"):
        read_schema(path)


def test_schema_file_requires_final_semicolon(tmp_path):
    path = tmp_path / "neo4j_schema.cypher"
    path.write_text(";\n".join(constraint_statements()), encoding="utf-8")
    with pytest.raises(ValueError, match="missing final semicolon"):
        read_schema(path)

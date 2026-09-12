"""Idempotent Neo4j schema for the temporal legal graph."""
from __future__ import annotations

from collections.abc import Iterable

from legal_crawler.temporal import RelationType


NODE_CONSTRAINTS = (
    "CREATE CONSTRAINT domain_entity_id IF NOT EXISTS "
    "FOR (n:DomainEntity) REQUIRE n.id IS UNIQUE",
)

NODE_INDEXES = (
    "CREATE INDEX domain_entity_kind IF NOT EXISTS "
    "FOR (n:DomainEntity) ON (n.kind)",
    "CREATE INDEX domain_entity_document IF NOT EXISTS "
    "FOR (n:DomainEntity) ON (n.document_id)",
    "CREATE INDEX domain_entity_provision IF NOT EXISTS "
    "FOR (n:DomainEntity) ON (n.provision_id)",
    "CREATE INDEX domain_entity_validity IF NOT EXISTS "
    "FOR (n:DomainEntity) ON (n.eff_from, n.eff_to)",
    "CREATE INDEX domain_entity_effective_on IF NOT EXISTS "
    "FOR (n:DomainEntity) ON (n.effective_on)",
    "CREATE INDEX domain_entity_level IF NOT EXISTS "
    "FOR (n:DomainEntity) ON (n.level)",
)


def relationship_constraints() -> tuple[str, ...]:
    """One unique domain-edge ID constraint for each safe relation type."""
    return tuple(
        f"CREATE CONSTRAINT edge_{relation.value.lower()}_id IF NOT EXISTS "
        f"FOR ()-[r:{relation.value}]-() REQUIRE r.id IS UNIQUE"
        for relation in RelationType
    )


def schema_statements() -> tuple[str, ...]:
    """Return the complete deterministic schema initialization plan."""
    return NODE_CONSTRAINTS + NODE_INDEXES + relationship_constraints()


def initialize_schema(executor: object) -> None:
    """Apply every idempotent statement through a write-capable executor."""
    write = getattr(executor, "write", None)
    if not callable(write):
        raise TypeError("executor must provide write(query, parameters)")
    for statement in schema_statements():
        write(statement, {})


def validate_relation(relation: str) -> str:
    """Return a relation safe for Cypher interpolation or reject it."""
    allowed: Iterable[str] = (item.value for item in RelationType)
    if relation not in allowed:
        raise ValueError(f"unsupported graph relation: {relation}")
    return relation

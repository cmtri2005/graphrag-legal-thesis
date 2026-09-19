#!/usr/bin/env python3
"""Apply and verify D1 Neo4j constraints without loading corpus data.

Usage::

    python scripts/pipeline/init_neo4j_schema.py
    python scripts/pipeline/init_neo4j_schema.py --check-only

Credentials follow the local Docker stack: NEO4J_URI (default localhost Bolt),
NEO4J_USER (default neo4j), and NEO4J_PASSWORD (default compose dev password).
No nodes or relationships are created here. The four CREATE statements are
idempotent; a shape check catches name conflicts that IF NOT EXISTS can mask.
"""
from __future__ import annotations

import argparse
import os
from pathlib import Path

from legal_crawler.graph.neo4j_schema import (
    NODE_ID_CONSTRAINTS,
    constraint_statements,
    verify_constraints,
)


SCHEMA_PATH = Path(__file__).with_name("neo4j_schema.cypher")
SHOW_CONSTRAINTS = (
    "SHOW CONSTRAINTS YIELD name, type, entityType, labelsOrTypes, properties "
    "RETURN name, type, entityType, labelsOrTypes, properties"
)


def read_schema(path: Path = SCHEMA_PATH) -> tuple[str, ...]:
    """Read only the four approved DDL statements from the checked-in file."""
    text = "\n".join(
        line for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("//")
    )
    chunks = text.split(";")
    if chunks[-1].strip():
        raise ValueError(f"missing final semicolon in {path}")
    statements = tuple(chunk.strip() for chunk in chunks[:-1] if chunk.strip())
    expected = constraint_statements()
    if statements != expected:
        raise ValueError(
            f"{path} differs from approved D1 node constraints; compare with "
            "legal_crawler.graph.neo4j_schema before applying"
        )
    return statements


def ensure_schema(session, *, check_only: bool = False) -> None:
    """Apply DDL if requested, then verify exact postconditions."""
    statements = read_schema()
    if not check_only:
        for statement in statements:
            session.run(statement).consume()
    rows = session.run(SHOW_CONSTRAINTS).data()
    verify_constraints(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check-only", action="store_true")
    parser.add_argument("--database", default="neo4j")
    args = parser.parse_args()

    try:
        from neo4j import GraphDatabase
    except ImportError as exc:
        raise SystemExit("Install the graph extra first: pip install -e '.[graph]'") from exc

    uri = os.environ.get("NEO4J_URI", "bolt://127.0.0.1:7687")
    user = os.environ.get("NEO4J_USER", "neo4j")
    password = os.environ.get("NEO4J_PASSWORD", "changeme123")
    with GraphDatabase.driver(uri, auth=(user, password)) as driver:
        driver.verify_connectivity()
        with driver.session(database=args.database) as session:
            ensure_schema(session, check_only=args.check_only)
    action = "verified" if args.check_only else "applied and verified"
    print(f"{action} {len(NODE_ID_CONSTRAINTS)} Neo4j id constraints in {args.database}")
    print("no corpus nodes or relationships were loaded")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""P3.1/P3.2 — confirm Neo4j and Milvus are reachable and writable.

Run after `docker compose up -d` and once both containers report healthy
(`docker compose ps`). This does not load any corpus data — it only proves
the stack is usable, which is the prerequisite P3.4 (the real loader) needs.

Usage:
    python scripts/check/verify_graph_stack.py
"""
from __future__ import annotations

import os
import sys


def check_neo4j() -> None:
    from neo4j import GraphDatabase

    password = os.environ.get("NEO4J_PASSWORD", "changeme123")
    driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", password))
    with driver.session() as session:
        session.run("MERGE (n:SmokeTest {id: 1}) SET n.ok = true")
        count = session.run("MATCH (n:SmokeTest) RETURN count(n) AS c").single()["c"]
        session.run("MATCH (n:SmokeTest) DELETE n")
    driver.close()
    print(f"[PASS] Neo4j: wrote and read back a node (count was {count})")


def check_milvus() -> None:
    from pymilvus import MilvusClient

    client = MilvusClient(uri="http://localhost:19530")
    client.create_collection(collection_name="smoke_test", dimension=4)
    client.insert(collection_name="smoke_test", data=[{"id": 1, "vector": [0.1, 0.2, 0.3, 0.4]}])
    result = client.query(collection_name="smoke_test", filter="id == 1", output_fields=["id"])
    client.drop_collection("smoke_test")
    print(f"[PASS] Milvus: wrote and queried back a vector ({result})")


def main() -> int:
    ok = True
    for name, fn in [("Neo4j", check_neo4j), ("Milvus", check_milvus)]:
        try:
            fn()
        except Exception as exc:  # noqa: BLE001 — this is a smoke test, any failure is reportable
            print(f"[FAIL] {name}: {exc}")
            ok = False
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Load the derived L0–L3 graph from the frozen data snapshot into Neo4j.

The SQLite index is built by ``build_store.py --with-subtrees`` from ``data/``;
``versions.jsonl`` and the event files are built by the offline temporal
pipeline. This command never changes those inputs. It MERGEs by stable domain
id and verifies every batch and the final graph counts. A failed/interrupted
run may be rerun; it never requires deleting the source snapshot.

Usage::

    python scripts/pipeline/init_neo4j_schema.py
    python scripts/pipeline/load_neo4j.py --data data
    python scripts/pipeline/load_neo4j.py --data data  # same counts again

D3 document-to-document reference edges are intentionally out of scope.
"""
from __future__ import annotations

import argparse
import json
import os
import sqlite3
import time
from collections import defaultdict
from collections.abc import Iterable, Iterator
from contextlib import closing
from pathlib import Path
from typing import Any

from init_neo4j_schema import SHOW_CONSTRAINTS
from legal_crawler.graph.neo4j_schema import verify_constraints
from legal_crawler.storage.documents import DocumentStore
from legal_crawler.temporal import make_document_id, make_provision_id, make_version_id


DOCUMENTS = """
UNWIND $rows AS row
MERGE (n:Document {id: row.id})
SET n += row.props
RETURN count(n) AS loaded
"""
PROVISIONS = """
UNWIND $rows AS row
MERGE (n:Provision {id: row.id})
SET n += row.props
RETURN count(n) AS loaded
"""
EVENTS = """
UNWIND $rows AS row
MERGE (n:LegalEvent {id: row.id})
SET n += row.props
RETURN count(n) AS loaded
"""
VERSIONS = """
UNWIND $rows AS row
MATCH (p:Provision {id: row.provision_id})
MERGE (v:ProvisionVersion {id: row.id})
SET v += row.props
MERGE (v)-[:VERSION_OF]->(p)
RETURN count(v) AS loaded
"""
ROOT_CONTAINS = """
UNWIND $rows AS row
MATCH (d:Document {id: row.document_id})
MATCH (p:Provision {id: row.id, document_id: row.document_id})
MERGE (d)-[:CONTAINS]->(p)
RETURN count(p) AS loaded
"""
CHILD_CONTAINS = """
UNWIND $rows AS row
MATCH (parent:Provision {id: row.parent_id, document_id: row.document_id})
MATCH (child:Provision {id: row.id, document_id: row.document_id})
MERGE (parent)-[:CONTAINS]->(child)
RETURN count(child) AS loaded
"""
CAUSED_BY = """
UNWIND $rows AS row
MATCH (v:ProvisionVersion {id: row.version_id})
MATCH (e:LegalEvent {id: row.event_id})
MERGE (v)-[:CAUSED_BY {role: row.role}]->(e)
RETURN count(v) AS loaded
"""

COUNTS = {
    "documents": "MATCH (n:Document) RETURN count(n) AS n",
    "provisions": "MATCH (n:Provision) RETURN count(n) AS n",
    "versions": "MATCH (n:ProvisionVersion) RETURN count(n) AS n",
    "events": "MATCH (n:LegalEvent) RETURN count(n) AS n",
    "root_contains": "MATCH (:Document)-[r:CONTAINS]->(:Provision) RETURN count(r) AS n",
    "child_contains": "MATCH (:Provision)-[r:CONTAINS]->(:Provision) RETURN count(r) AS n",
    "version_of": "MATCH (:ProvisionVersion)-[r:VERSION_OF]->(:Provision) RETURN count(r) AS n",
    "created_by": "MATCH (:ProvisionVersion)-[r:CAUSED_BY {role:'created'}]->(:LegalEvent) RETURN count(r) AS n",
    "ended_by": "MATCH (:ProvisionVersion)-[r:CAUSED_BY {role:'ended'}]->(:LegalEvent) RETURN count(r) AS n",
}


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def _required_id(value: Any, prefix: str, context: str) -> str:
    if not isinstance(value, str) or not value.startswith(prefix) or len(value) <= len(prefix):
        raise ValueError(f"{context}: expected nonempty {prefix} ID, got {value!r}")
    return value


def _rows(path: Path) -> Iterator[tuple[int, dict[str, Any]]]:
    with path.open(encoding="utf-8") as stream:
        for line_number, line in enumerate(stream, 1):
            if not line.strip():
                raise ValueError(f"{path}:{line_number}: blank JSONL line")
            row = json.loads(line)
            if not isinstance(row, dict):
                raise ValueError(f"{path}:{line_number}: expected JSON object")
            yield line_number, row


def read_event_nodes(data_dir: Path) -> dict[str, dict[str, Any]]:
    """One LegalEvent per ID, retaining every source line and audit outcome."""
    event_path = data_dir / "derived/provision_events.jsonl"
    log_path = data_dir / "derived/event_log.jsonl"
    logs: dict[int, dict[str, Any]] = {}
    for _, log in _rows(log_path):
        line = log.get("input_line")
        if not isinstance(line, int) or line < 1 or line in logs:
            raise ValueError(f"{log_path}: duplicate/invalid input_line {line!r}")
        logs[line] = log

    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for line, source in _rows(event_path):
        event_id = _required_id(source.get("id"), "event:", f"{event_path}:{line}")
        log = logs.pop(line, None)
        if log is None or log.get("event_id") != event_id:
            raise ValueError(f"{event_path}:{line}: event_log is missing or has a different event_id")
        grouped[event_id].append({"input_line": line, "source": source, "audit": log})
    if logs:
        raise ValueError(f"{log_path}: {len(logs)} audit rows have no input event")

    nodes = {}
    core = ("actor_id", "target_document_id", "operation", "effective_on", "status")
    for event_id, entries in grouped.items():
        first = entries[0]["source"]
        if any(tuple(entry["source"].get(key) for key in core) !=
               tuple(first.get(key) for key in core) for entry in entries[1:]):
            raise ValueError(f"{event_id}: repeated event ID has conflicting core fields")
        actor_id = _required_id(first.get("actor_id"), "document:", event_id)
        target_id = first.get("target_document_id")
        if target_id is not None:
            _required_id(target_id, "document:", event_id)
        target_provision_id = first.get("target_provision_id")
        if target_provision_id is not None:
            _required_id(target_provision_id, "provision:", event_id)
        nodes[event_id] = {
            "id": event_id,
            "props": {
                "actor_id": actor_id,
                "target_document_id": target_id,
                "target_provision_id": target_provision_id,
                "operation": first.get("operation"),
                "effective_on": first.get("effective_on"),
                "status": first.get("status"),
                "status_reason": first.get("status_reason"),
                "evidence": first.get("evidence"),
                "applied": any(entry["audit"].get("outcome") == "applied" for entry in entries),
                "input_lines": [entry["input_line"] for entry in entries],
                "source_and_audit_json": _json(entries),
            },
        }
    return nodes


def _document_rows(db: sqlite3.Connection) -> Iterator[dict[str, Any]]:
    for row in db.execute("SELECT * FROM documents ORDER BY id"):
        item = dict(row)
        item_id = _required_id(item.pop("id"), "document:", "SQLite documents")
        yield {"id": item_id, "props": item}


def _provision_rows(db: sqlite3.Connection) -> Iterator[dict[str, Any]]:
    for row in db.execute("SELECT id, document_id, level, title, parent_id, order_index, path FROM provisions ORDER BY id"):
        item = dict(row)
        item_id = _required_id(item.pop("id"), "provision:", "SQLite provisions")
        _required_id(item["document_id"], "document:", item_id)
        if item["parent_id"] is not None:
            _required_id(item["parent_id"], "provision:", item_id)
        yield {"id": item_id, "props": item}


def _containment_rows(db: sqlite3.Connection) -> Iterator[dict[str, Any]]:
    for row in db.execute("SELECT id, document_id, parent_id FROM provisions ORDER BY id"):
        yield dict(row)


def _version_rows(
    path: Path, event_ids: set[str], causal_edges: list[dict[str, str]]
) -> Iterator[dict[str, Any]]:
    for line, source in _rows(path):
        context = f"{path}:{line}"
        version_id = _required_id(source.get("id"), "version:", context)
        provision_id = _required_id(source.get("provision_id"), "provision:", context)
        ordinal = source.get("ordinal")
        if not isinstance(ordinal, int) or version_id != make_version_id(provision_id, ordinal):
            raise ValueError(f"{context}: version ID/ordinal disagrees with provision ID")
        intervals = source.get("effective_intervals")
        if not isinstance(intervals, list) or source.get("effective_interval_count") != len(intervals):
            raise ValueError(f"{context}: effective interval count disagrees with intervals")
        if not isinstance(source.get("text"), str) or not source["text"]:
            raise ValueError(f"{context}: version text is empty")
        for key, role in (("created_by_event_id", "created"), ("ended_by_event_id", "ended")):
            event_id = source.get(key)
            if event_id is not None:
                if event_id not in event_ids:
                    raise ValueError(f"{context}: {key} {event_id!r} has no source event")
                causal_edges.append({"version_id": version_id, "event_id": event_id, "role": role})
        props = {key: value for key, value in source.items()
                 if key not in {"id", "effective_intervals", "provenance"}}
        props["effective_intervals_json"] = _json(intervals)
        props["provenance_json"] = _json(source.get("provenance") or [])
        yield {"id": version_id, "provision_id": provision_id, "props": props}


def _batches(rows: Iterable[dict[str, Any]], size: int, max_text_bytes: int = 4 * 1024 * 1024):
    batch: list[dict[str, Any]] = []
    text_bytes = 0
    for row in rows:
        current = len(row.get("props", {}).get("text", "").encode("utf-8"))
        if batch and (len(batch) >= size or text_bytes + current > max_text_bytes):
            yield batch
            batch, text_bytes = [], 0
        batch.append(row)
        text_bytes += current
    if batch:
        yield batch


def _write_batch(tx, query: str, rows: list[dict[str, Any]], stage: str) -> int:
    loaded = tx.run(query, rows=rows).single()["loaded"]
    if loaded != len(rows):
        raise ValueError(
            f"D2 {stage}: matched {loaded}/{len(rows)} rows; missing or wrong-label "
            "endpoint in the source/index or Neo4j. Transaction rolled back."
        )
    return loaded


def _load_stage(session, stage: str, query: str, rows: Iterable[dict[str, Any]], batch_size: int) -> int:
    total = 0
    for batch in _batches(rows, batch_size):
        total += session.execute_write(_write_batch, query, batch, stage)
        if total and total % 100_000 < len(batch):
            print(f"  {stage}: {total:,}", flush=True)
    print(f"  {stage}: {total:,} complete", flush=True)
    return total


def _source_document_ids(data_dir: Path) -> set[str]:
    raw = DocumentStore(data_dir).ids("raw")
    if not raw:
        raise ValueError(f"{data_dir / 'raw'} has no source documents")
    return {make_document_id(item) for item in raw}


def _check_counts(session, expected: dict[str, int]) -> None:
    for key, query in COUNTS.items():
        actual = session.run(query).single()["n"]
        if actual != expected[key]:
            raise ValueError(
                f"D2 {key}: Neo4j has {actual:,}, source expects {expected[key]:,}; "
                "inspect partial load/source drift, then rerun loader or rebuild derived graph"
            )


def load_graph(session, data_dir: Path, index_path: Path, *, batch_size: int = 500) -> dict[str, int]:
    if batch_size < 1:
        raise ValueError("batch_size must be at least 1")
    verify_constraints(session.run(SHOW_CONSTRAINTS).data())
    source_ids = _source_document_ids(data_dir)
    event_nodes = read_event_nodes(data_dir)
    with closing(sqlite3.connect(index_path.resolve().as_uri() + "?mode=ro", uri=True)) as db:
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA query_only=ON")
        index_ids = {row[0] for row in db.execute("SELECT id FROM documents")}
        if index_ids != source_ids:
            raise ValueError(
                f"D2 SQLite/raw document IDs differ: {len(index_ids - source_ids)} "
                f"index-only, {len(source_ids - index_ids)} raw-only; rebuild "
                "temporal.sqlite with --with-subtrees before loading"
            )

        expected = {}
        expected["documents"] = _load_stage(session, "documents", DOCUMENTS, _document_rows(db), batch_size)
        expected["provisions"] = _load_stage(session, "provisions", PROVISIONS, _provision_rows(db), batch_size)
        expected["events"] = _load_stage(session, "events", EVENTS, event_nodes.values(), batch_size)

        causal_edges: list[dict[str, str]] = []
        expected["versions"] = _load_stage(
            session, "versions", VERSIONS,
            _version_rows(data_dir / "derived/versions.jsonl", set(event_nodes), causal_edges),
            batch_size,
        )

        expected["root_contains"] = expected["child_contains"] = 0
        for batch in _batches(_containment_rows(db), batch_size):
            roots = [item for item in batch if item["parent_id"] is None]
            children = [item for item in batch if item["parent_id"] is not None]
            if roots:
                expected["root_contains"] += session.execute_write(
                    _write_batch, ROOT_CONTAINS, roots, "root_contains"
                )
            if children:
                expected["child_contains"] += session.execute_write(
                    _write_batch, CHILD_CONTAINS, children, "child_contains"
                )
            loaded_contains = expected["root_contains"] + expected["child_contains"]
            if loaded_contains and loaded_contains % 100_000 < len(batch):
                print(f"  contains: {loaded_contains:,}", flush=True)
        print(
            f"  contains: {expected['root_contains']:,} document roots + "
            f"{expected['child_contains']:,} child provisions", flush=True
        )
        expected["version_of"] = expected["versions"]
        if expected["root_contains"] + expected["child_contains"] != expected["provisions"]:
            raise ValueError("D2 CONTAINS edge count does not cover every provision")
        expected["created_by"] = sum(edge["role"] == "created" for edge in causal_edges)
        expected["ended_by"] = len(causal_edges) - expected["created_by"]
        _load_stage(session, "caused_by", CAUSED_BY, causal_edges, batch_size)

    _check_counts(session, expected)
    return expected


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=Path("data"))
    parser.add_argument("--index", type=Path, default=None)
    parser.add_argument("--batch-size", type=int, default=500)
    parser.add_argument("--database", default="neo4j")
    args = parser.parse_args()

    try:
        from neo4j import GraphDatabase
    except ImportError as exc:
        raise SystemExit("Install the graph extra first: pip install -e '.[graph]'") from exc
    uri = os.environ.get("NEO4J_URI", "bolt://127.0.0.1:7687")
    user = os.environ.get("NEO4J_USER", "neo4j")
    password = os.environ.get("NEO4J_PASSWORD", "changeme123")
    started = time.monotonic()
    with GraphDatabase.driver(uri, auth=(user, password)) as driver:
        driver.verify_connectivity()
        with driver.session(database=args.database) as session:
            counts = load_graph(
                session, args.data, args.index or args.data / "temporal.sqlite",
                batch_size=args.batch_size,
            )
    print(f"D2 graph verified in {time.monotonic() - started:.1f}s: {counts}")


if __name__ == "__main__":
    main()

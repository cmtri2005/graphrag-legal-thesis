#!/usr/bin/env python3
"""D3: load typed document references without inventing missing documents.

Input is the current ``data/edges.jsonl`` snapshot, not the older M1 edge
count. Only edges whose two endpoints are in ``data/raw`` enter Neo4j.
References to absent targets remain in an atomic, deterministic unresolved
report; they are never silently dropped or represented by placeholder nodes.

Usage::

    python scripts/pipeline/load_neo4j_references.py --data data
    python scripts/pipeline/load_neo4j_references.py --data data  # idempotence
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
import time
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from init_neo4j_schema import SHOW_CONSTRAINTS
from legal_crawler.graph.neo4j_references import REFERENCE_RELATION_TYPES, relationship_type
from legal_crawler.graph.neo4j_schema import verify_constraints
from legal_crawler.storage.documents import DocumentStore
from legal_crawler.temporal import RelationType, make_document_id
from legal_crawler.vocab.reference_types import ReferenceTypeMap


@dataclass(slots=True)
class ReferencePlan:
    rows_by_type: dict[RelationType, list[dict[str, Any]]]
    unresolved: list[dict[str, Any]]
    source_lines: int
    distinct_edges: int
    source_sha256: str
    raw_documents: int
    source_by_type: dict[RelationType, int]

    def report(self) -> dict[str, Any]:
        loaded_by_type = {kind.value: len(self.rows_by_type.get(kind, ()))
                          for kind in REFERENCE_RELATION_TYPES.values()}
        unresolved_by_type = Counter(row["relation_type"] for row in self.unresolved)
        return {
            "source": "data/edges.jsonl",
            "source_sha256": self.source_sha256,
            "raw_documents": self.raw_documents,
            "source_lines": self.source_lines,
            "distinct_edges": self.distinct_edges,
            "duplicate_lines": self.source_lines - self.distinct_edges,
            "loaded_edges": sum(loaded_by_type.values()),
            "unresolved_edges": len(self.unresolved),
            "unresolved_target_ids": len({row["target_id"] for row in self.unresolved}),
            "by_type": {
                kind.value: {
                    "source_distinct": self.source_by_type.get(kind, 0),
                    "loaded": loaded_by_type[kind.value],
                    "unresolved": unresolved_by_type[kind.value],
                }
                for kind in REFERENCE_RELATION_TYPES.values()
            },
        }


def _document_id(value: Any, context: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{context}: missing document ID")
    return make_document_id(value)


def plan_references(data_dir: Path) -> ReferencePlan:
    """Validate the whole source and resolve endpoints before any DB writes."""
    source_path = data_dir / "edges.jsonl"
    mapping = ReferenceTypeMap.load(data_dir / "reference_type_map.json")
    if mapping.codes != frozenset(REFERENCE_RELATION_TYPES):
        raise ValueError(
            "D3 code set differs between reference_type_map.json and "
            "neo4j_references.py; verify all 13 mappings before loading"
        )
    raw_ids = {make_document_id(value) for value in DocumentStore(data_dir).ids("raw")}
    if not raw_ids:
        raise ValueError(f"{data_dir / 'raw'} has no source documents")

    digest = hashlib.sha256()
    grouped: dict[tuple[str, str, int], dict[str, Any]] = {}
    line_count = 0
    with source_path.open("rb") as stream:
        for line_count, line in enumerate(stream, 1):
            digest.update(line)
            if not line.strip():
                raise ValueError(f"{source_path}:{line_count}: blank JSONL line")
            row = json.loads(line)
            if not isinstance(row, dict):
                raise ValueError(f"{source_path}:{line_count}: expected JSON object")
            context = f"{source_path}:{line_count}"
            source_id = _document_id(row.get("source_id"), context)
            target_id = _document_id(row.get("target_id"), context)
            code = row.get("reference_type")
            if isinstance(code, bool) or not isinstance(code, int):
                raise ValueError(f"{context}: reference_type must be an integer")
            info = mapping.classify(code)
            kind = relationship_type(code)
            if row.get("label_vi") != info.label_vi or row.get("group") != info.group.value:
                raise ValueError(
                    f"{context}: label/group disagree with verified "
                    "data/reference_type_map.json; rebuild edges.jsonl or review mapping"
                )
            if source_id not in raw_ids:
                raise ValueError(f"{context}: source Document {source_id} is absent from data/raw")
            key = source_id, target_id, code
            previous = grouped.get(key)
            if previous is not None:
                previous["source_lines"].append(line_count)
                continue
            grouped[key] = {
                "source_id": source_id,
                "target_id": target_id,
                "reference_type": code,
                "relation_type": kind.value,
                "label_vi": info.label_vi,
                "group": info.group.value,
                "source_lines": [line_count],
            }

    if line_count == 0:
        raise ValueError(f"{source_path} has no edges")
    rows_by_type: dict[RelationType, list[dict[str, Any]]] = defaultdict(list)
    source_by_type: Counter[RelationType] = Counter()
    unresolved = []
    for row in grouped.values():
        kind = relationship_type(row["reference_type"])
        source_by_type[kind] += 1
        if row["target_id"] not in raw_ids:
            unresolved.append({**row, "reason": "target_not_in_raw"})
        else:
            rows_by_type[kind].append(row)
    return ReferencePlan(
        rows_by_type=dict(rows_by_type),
        unresolved=unresolved,
        source_lines=line_count,
        distinct_edges=len(grouped),
        source_sha256=digest.hexdigest(),
        raw_documents=len(raw_ids),
        source_by_type=dict(source_by_type),
    )


def _query(kind: RelationType) -> str:
    if kind not in REFERENCE_RELATION_TYPES.values():
        raise ValueError(f"D3 relation {kind!r} is not a verified source reference type")
    return (
        "UNWIND $rows AS row\n"
        "MATCH (source:Document {id: row.source_id})\n"
        "MATCH (target:Document {id: row.target_id})\n"
        f"MERGE (source)-[r:{kind.value}]->(target)\n"
        "SET r.reference_type = row.reference_type, r.label_vi = row.label_vi, "
        "r.group = row.group, r.source_lines = row.source_lines\n"
        "RETURN count(r) AS loaded"
    )


def _write_batch(tx, query: str, rows: list[dict[str, Any]], kind: RelationType) -> int:
    loaded = tx.run(query, rows=rows).single()["loaded"]
    if loaded != len(rows):
        raise ValueError(
            f"D3 {kind.value}: matched {loaded}/{len(rows)} edges; a Document "
            "endpoint is missing in Neo4j or duplicate relationships exist. "
            "Transaction rolled back."
        )
    return loaded


def _batches(rows: list[dict[str, Any]], size: int):
    for offset in range(0, len(rows), size):
        yield rows[offset:offset + size]


def load_references(session, plan: ReferencePlan, *, batch_size: int = 500) -> dict[str, Any]:
    if batch_size < 1:
        raise ValueError("batch_size must be at least 1")
    verify_constraints(session.run(SHOW_CONSTRAINTS).data())
    document_count = session.run("MATCH (n:Document) RETURN count(n) AS n").single()["n"]
    if document_count != plan.raw_documents:
        raise ValueError(
            f"D3 requires D2 Document nodes: Neo4j has {document_count:,}, "
            f"data/raw has {plan.raw_documents:,}; run D2 loader first"
        )

    for kind in REFERENCE_RELATION_TYPES.values():
        rows = plan.rows_by_type.get(kind, [])
        loaded = 0
        for batch in _batches(rows, batch_size):
            loaded += session.execute_write(_write_batch, _query(kind), batch, kind)
        actual = session.run(
            f"MATCH ()-[r:{kind.value}]->() RETURN count(r) AS n"
        ).single()["n"]
        if actual != len(rows):
            raise ValueError(
                f"D3 {kind.value}: Neo4j has {actual:,}, expected {len(rows):,}; "
                "inspect partial load/extra edges before rerunning"
            )
        print(f"  {kind.value}: {loaded:,} loaded/verified", flush=True)
    after = session.run("MATCH (n:Document) RETURN count(n) AS n").single()["n"]
    if after != document_count:
        raise ValueError("D3 unexpectedly changed Document node count; inspect Neo4j")
    return plan.report()


def _atomic_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_name = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", newline="\n", dir=path.parent,
            prefix=path.name + ".", suffix=".tmp", delete=False,
        ) as stream:
            temp_name = stream.name
            stream.write(text)
        os.replace(temp_name, path)
    finally:
        if temp_name is not None and os.path.exists(temp_name):
            os.unlink(temp_name)


def write_reports(data_dir: Path, plan: ReferencePlan, report: dict[str, Any]) -> tuple[Path, Path]:
    summary_path = data_dir / "derived/neo4j_reference_load_report.json"
    unresolved_path = data_dir / "derived/neo4j_unresolved_references.jsonl"
    _atomic_text(summary_path, json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    _atomic_text(
        unresolved_path,
        "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n"
                for row in plan.unresolved),
    )
    return summary_path, unresolved_path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=Path("data"))
    parser.add_argument("--batch-size", type=int, default=500)
    parser.add_argument("--database", default="neo4j")
    args = parser.parse_args()

    try:
        from neo4j import GraphDatabase
    except ImportError as exc:
        raise SystemExit("Install the graph extra first: pip install -e '.[graph]'") from exc
    started = time.monotonic()
    plan = plan_references(args.data)
    uri = os.environ.get("NEO4J_URI", "bolt://127.0.0.1:7687")
    user = os.environ.get("NEO4J_USER", "neo4j")
    password = os.environ.get("NEO4J_PASSWORD", "changeme123")
    with GraphDatabase.driver(uri, auth=(user, password)) as driver:
        driver.verify_connectivity()
        with driver.session(database=args.database) as session:
            report = load_references(session, plan, batch_size=args.batch_size)
    summary_path, unresolved_path = write_reports(args.data, plan, report)
    print(
        f"D3 verified in {time.monotonic() - started:.1f}s: "
        f"{report['loaded_edges']:,} graph edges, "
        f"{report['unresolved_edges']:,} unresolved targets"
    )
    print(f"reports: {summary_path}, {unresolved_path}")


if __name__ == "__main__":
    main()

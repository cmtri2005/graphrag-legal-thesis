#!/usr/bin/env python3
"""Export the temporal legal corpus into versioned analytical Parquet tables.

The export mirrors the L0-L3 Neo4j model without requiring Neo4j: documents
and provisions come from the rebuilt SQLite index; versions and events come
from the audited offline artifacts; graph relationships become edge tables.
The destination must not exist, so a failed/new export cannot overwrite a
previous table snapshot.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import sqlite3
import subprocess
import tempfile
from collections import defaultdict
from contextlib import closing
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Iterator

import pyarrow as pa
import pyarrow.parquet as pq

from legal_crawler.graph.neo4j_references import relationship_type
from legal_crawler.temporal import make_document_id
from legal_crawler.vocab.reference_types import ReferenceTypeMap


SCHEMA_VERSION = 1
SNAPSHOT_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}\Z")
TABLE_ORDER = (
    "documents",
    "provisions",
    "provision_versions",
    "legal_events",
    "containment_edges",
    "causal_edges",
    "document_reference_edges",
)


def _schema(*fields: tuple[str, pa.DataType, bool]) -> pa.Schema:
    return pa.schema([pa.field(name, kind, nullable=nullable) for name, kind, nullable in fields])


SCHEMAS = {
    "documents": _schema(
        ("id", pa.string(), False), ("number", pa.string(), False),
        ("title", pa.string(), False), ("issued_on", pa.date32(), True),
        ("effective_from", pa.date32(), True), ("effective_to", pa.date32(), True),
        ("issuer", pa.string(), True), ("rank", pa.string(), True),
        ("source_url", pa.string(), True), ("raw_status_code", pa.string(), True),
    ),
    "provisions": _schema(
        ("id", pa.string(), False), ("document_id", pa.string(), False),
        ("level", pa.string(), False), ("title", pa.string(), False),
        ("parent_id", pa.string(), True), ("order_index", pa.int64(), True),
        ("path", pa.string(), False),
    ),
    "provision_versions": _schema(
        ("id", pa.string(), False), ("provision_id", pa.string(), False),
        ("ordinal", pa.int64(), False), ("text", pa.string(), False),
        ("valid_from", pa.date32(), True), ("valid_to", pa.date32(), True),
        ("effective_interval_count", pa.int64(), False),
        ("effective_from", pa.date32(), True), ("effective_to", pa.date32(), True),
        ("effective_intervals_json", pa.string(), False),
        ("created_by_event_id", pa.string(), True),
        ("ended_by_event_id", pa.string(), True),
        ("provenance_json", pa.string(), False),
    ),
    "legal_events": _schema(
        ("id", pa.string(), False), ("actor_id", pa.string(), False),
        ("target_document_id", pa.string(), True),
        ("target_provision_id", pa.string(), True),
        ("operation", pa.string(), False), ("effective_on", pa.date32(), True),
        ("status", pa.string(), False), ("status_reason", pa.string(), True),
        ("evidence", pa.string(), True), ("applied", pa.bool_(), False),
        ("input_lines_json", pa.string(), False),
        ("source_and_audit_json", pa.string(), False),
    ),
    "containment_edges": _schema(
        ("source_id", pa.string(), False), ("source_kind", pa.string(), False),
        ("target_id", pa.string(), False), ("target_kind", pa.string(), False),
        ("relationship_type", pa.string(), False),
    ),
    "causal_edges": _schema(
        ("source_id", pa.string(), False), ("source_kind", pa.string(), False),
        ("target_id", pa.string(), False), ("target_kind", pa.string(), False),
        ("relationship_type", pa.string(), False), ("role", pa.string(), True),
    ),
    "document_reference_edges": _schema(
        ("source_id", pa.string(), False), ("target_id", pa.string(), False),
        ("reference_type", pa.int64(), False), ("relationship_type", pa.string(), False),
        ("label_vi", pa.string(), False), ("group", pa.string(), False),
        ("source_lines_json", pa.string(), False),
        ("target_resolved", pa.bool_(), False),
        ("loaded_to_neo4j", pa.bool_(), False),
    ),
}


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def _date(value: Any, context: str) -> date | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError(f"{context}: expected ISO date or null, got {value!r}")
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{context}: invalid ISO date {value!r}") from exc


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _jsonl(path: Path) -> Iterator[tuple[int, dict[str, Any]]]:
    with path.open(encoding="utf-8") as stream:
        for line_number, line in enumerate(stream, 1):
            if not line.strip():
                raise ValueError(f"{path}:{line_number}: blank JSONL line")
            value = json.loads(line)
            if not isinstance(value, dict):
                raise ValueError(f"{path}:{line_number}: expected JSON object")
            yield line_number, value


class ParquetSink:
    """Bounded-memory writer that emits stable part files and row counts."""

    def __init__(
        self, root: Path, name: str, *, batch_rows: int, rows_per_file: int
    ) -> None:
        self.root = root / name
        self.root.mkdir(parents=True)
        self.name = name
        self.schema = SCHEMAS[name]
        self.batch_rows = batch_rows
        self.rows_per_file = rows_per_file
        self.buffer: list[dict[str, Any]] = []
        self.writer: pq.ParquetWriter | None = None
        self.file_index = 0
        self.rows_in_file = 0
        self.row_count = 0

    def add(self, row: dict[str, Any]) -> None:
        self.buffer.append(row)
        if len(self.buffer) >= self.batch_rows:
            self.flush()

    def _open(self) -> None:
        path = self.root / f"part-{self.file_index:05d}.parquet"
        self.writer = pq.ParquetWriter(
            path, self.schema, compression="zstd", use_dictionary=False,
            write_statistics=True,
        )

    def _close_part(self) -> None:
        if self.writer is not None:
            self.writer.close()
            self.writer = None
            self.file_index += 1
            self.rows_in_file = 0

    def flush(self) -> None:
        offset = 0
        while offset < len(self.buffer):
            if self.writer is None:
                self._open()
            capacity = self.rows_per_file - self.rows_in_file
            rows = self.buffer[offset:offset + capacity]
            table = pa.Table.from_pylist(rows, schema=self.schema)
            assert self.writer is not None
            self.writer.write_table(table, row_group_size=min(len(rows), self.batch_rows))
            count = len(rows)
            self.row_count += count
            self.rows_in_file += count
            offset += count
            if self.rows_in_file == self.rows_per_file:
                self._close_part()
        self.buffer.clear()

    def close(self) -> None:
        self.flush()
        self._close_part()
        if self.row_count == 0:
            # Preserve a queryable schema even for a legitimately empty table.
            pq.write_table(pa.Table.from_pylist([], schema=self.schema),
                           self.root / "part-00000.parquet", compression="zstd")


def _events(data_dir: Path) -> dict[str, dict[str, Any]]:
    event_path = data_dir / "derived/provision_events.jsonl"
    log_path = data_dir / "derived/event_log.jsonl"
    logs: dict[int, dict[str, Any]] = {}
    for _, audit in _jsonl(log_path):
        input_line = audit.get("input_line")
        if not isinstance(input_line, int) or input_line < 1 or input_line in logs:
            raise ValueError(f"{log_path}: duplicate/invalid input_line {input_line!r}")
        logs[input_line] = audit

    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for line, source in _jsonl(event_path):
        event_id = source.get("id")
        if not isinstance(event_id, str) or not event_id.startswith("event:"):
            raise ValueError(f"{event_path}:{line}: invalid event ID")
        audit = logs.pop(line, None)
        if audit is None or audit.get("event_id") != event_id:
            raise ValueError(f"{event_path}:{line}: missing/mismatched audit row")
        grouped[event_id].append({"input_line": line, "source": source, "audit": audit})
    if logs:
        raise ValueError(f"{log_path}: {len(logs)} audit rows have no input event")

    result = {}
    core = ("actor_id", "target_document_id", "operation", "effective_on", "status")
    for event_id, entries in grouped.items():
        first = entries[0]["source"]
        if any(
            tuple(entry["source"].get(key) for key in core)
            != tuple(first.get(key) for key in core)
            for entry in entries[1:]
        ):
            raise ValueError(f"{event_id}: repeated event ID has conflicting core fields")
        result[event_id] = {
            "id": event_id,
            "actor_id": first.get("actor_id"),
            "target_document_id": first.get("target_document_id"),
            "target_provision_id": first.get("target_provision_id"),
            "operation": first.get("operation"),
            "effective_on": _date(first.get("effective_on"), event_id),
            "status": first.get("status"),
            "status_reason": first.get("status_reason"),
            "evidence": first.get("evidence"),
            "applied": any(entry["audit"].get("outcome") == "applied" for entry in entries),
            "input_lines_json": _json([entry["input_line"] for entry in entries]),
            "source_and_audit_json": _json(entries),
        }
    return result


def _source_metadata(paths: Iterable[Path], data_dir: Path) -> dict[str, Any]:
    result = {}
    for path in paths:
        result[str(path.relative_to(data_dir))] = {
            "bytes": path.stat().st_size,
            "sha256": _sha256(path),
        }
    return result


def export_tables(
    data_dir: Path,
    destination: Path,
    *,
    snapshot_id: str,
    git_commit: str,
    git_dirty: bool = False,
    batch_rows: int = 5_000,
    rows_per_file: int = 250_000,
) -> dict[str, Any]:
    if destination.exists():
        raise ValueError(f"destination already exists: {destination}")
    if not SNAPSHOT_ID.fullmatch(snapshot_id):
        raise ValueError("snapshot ID must contain only letters, digits, '.', '_' or '-'")
    if batch_rows < 1 or rows_per_file < batch_rows:
        raise ValueError("require 1 <= batch_rows <= rows_per_file")
    required = (
        data_dir / "temporal.sqlite",
        data_dir / "derived/versions.jsonl",
        data_dir / "derived/provision_events.jsonl",
        data_dir / "derived/event_log.jsonl",
        data_dir / "edges.jsonl",
        data_dir / "reference_type_map.json",
    )
    missing = [str(path) for path in required if not path.is_file()]
    if missing:
        raise ValueError(f"missing table inputs: {', '.join(missing)}")

    destination.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=destination.name + ".", dir=destination.parent))
    sinks = {
        name: ParquetSink(staging, name, batch_rows=batch_rows, rows_per_file=rows_per_file)
        for name in TABLE_ORDER
    }
    try:
        database_uri = (data_dir / "temporal.sqlite").resolve().as_uri() + "?mode=ro"
        document_ids: set[str] = set()
        with closing(sqlite3.connect(database_uri, uri=True)) as db:
            db.row_factory = sqlite3.Row
            db.execute("PRAGMA query_only=ON")
            for raw in db.execute("SELECT * FROM documents ORDER BY id"):
                row = dict(raw)
                document_ids.add(row["id"])
                for field in ("issued_on", "effective_from", "effective_to"):
                    row[field] = _date(row[field], f"documents:{row['id']}:{field}")
                sinks["documents"].add(row)

            for raw in db.execute(
                "SELECT id, document_id, level, title, parent_id, order_index, path "
                "FROM provisions ORDER BY id"
            ):
                row = dict(raw)
                sinks["provisions"].add(row)
                parent_id = row["parent_id"]
                sinks["containment_edges"].add({
                    "source_id": parent_id or row["document_id"],
                    "source_kind": "Provision" if parent_id else "Document",
                    "target_id": row["id"],
                    "target_kind": "Provision",
                    "relationship_type": "CONTAINS",
                })

        events = _events(data_dir)
        for event_id in sorted(events):
            event = events[event_id]
            if event["actor_id"] not in document_ids:
                raise ValueError(f"{event_id}: actor Document absent from SQLite")
            sinks["legal_events"].add(event)
            sinks["causal_edges"].add({
                "source_id": event_id, "source_kind": "LegalEvent",
                "target_id": event["actor_id"], "target_kind": "Document",
                "relationship_type": "CAUSED_BY", "role": "actor",
            })

        for line, source in _jsonl(data_dir / "derived/versions.jsonl"):
            context = f"versions.jsonl:{line}"
            intervals = source.get("effective_intervals")
            provenance = source.get("provenance") or []
            if not isinstance(intervals, list) or source.get("effective_interval_count") != len(intervals):
                raise ValueError(f"{context}: effective interval count mismatch")
            row = {
                "id": source.get("id"), "provision_id": source.get("provision_id"),
                "ordinal": source.get("ordinal"), "text": source.get("text"),
                "valid_from": _date(source.get("valid_from"), context + ":valid_from"),
                "valid_to": _date(source.get("valid_to"), context + ":valid_to"),
                "effective_interval_count": source.get("effective_interval_count"),
                "effective_from": _date(source.get("effective_from"), context + ":effective_from"),
                "effective_to": _date(source.get("effective_to"), context + ":effective_to"),
                "effective_intervals_json": _json(intervals),
                "created_by_event_id": source.get("created_by_event_id"),
                "ended_by_event_id": source.get("ended_by_event_id"),
                "provenance_json": _json(provenance),
            }
            sinks["provision_versions"].add(row)
            for key, role in (("created_by_event_id", "created"), ("ended_by_event_id", "ended")):
                event_id = source.get(key)
                if event_id is not None:
                    if event_id not in events:
                        raise ValueError(f"{context}: {key} has no LegalEvent")
                    sinks["causal_edges"].add({
                        "source_id": source["id"], "source_kind": "ProvisionVersion",
                        "target_id": event_id, "target_kind": "LegalEvent",
                        "relationship_type": "CAUSED_BY", "role": role,
                    })

        reference_map = ReferenceTypeMap.load(data_dir / "reference_type_map.json")
        grouped: dict[tuple[str, str, int], dict[str, Any]] = {}
        for line, source in _jsonl(data_dir / "edges.jsonl"):
            source_id = make_document_id(source.get("source_id"))
            target_id = make_document_id(source.get("target_id"))
            code = source.get("reference_type")
            if isinstance(code, bool) or not isinstance(code, int):
                raise ValueError(f"edges.jsonl:{line}: reference_type must be integer")
            info = reference_map.classify(code)
            relation = relationship_type(code).value
            if source.get("label_vi") != info.label_vi or source.get("group") != info.group.value:
                raise ValueError(
                    f"edges.jsonl:{line}: label/group disagree with reference_type_map.json"
                )
            key = source_id, target_id, code
            if key in grouped:
                grouped[key]["source_lines"].append(line)
            else:
                grouped[key] = {
                    "source_id": source_id, "target_id": target_id,
                    "reference_type": code, "relationship_type": relation,
                    "label_vi": info.label_vi, "group": info.group.value,
                    "source_lines": [line],
                }
        for item in grouped.values():
            if item["source_id"] not in document_ids:
                raise ValueError(f"reference source absent from SQLite: {item['source_id']}")
            resolved = item["target_id"] in document_ids
            sinks["document_reference_edges"].add({
                **{key: value for key, value in item.items() if key != "source_lines"},
                "source_lines_json": _json(item["source_lines"]),
                "target_resolved": resolved,
                "loaded_to_neo4j": resolved,
            })

        for sink in sinks.values():
            sink.close()

        parquet_files = sorted(staging.glob("*/*.parquet"))
        file_entries = []
        for path in parquet_files:
            metadata = pq.read_metadata(path)
            file_entries.append({
                "path": str(path.relative_to(staging)),
                "bytes": path.stat().st_size,
                "rows": metadata.num_rows,
                "sha256": _sha256(path),
            })
        manifest = {
            "schema_version": SCHEMA_VERSION,
            "snapshot_id": snapshot_id,
            "created_at_utc": datetime.now(timezone.utc).isoformat(),
            "git_commit": git_commit,
            "git_dirty": git_dirty,
            "format": "parquet",
            "compression": "zstd",
            "source": str(data_dir),
            "source_files": _source_metadata(required, data_dir),
            "tables": {
                name: {
                    "rows": sinks[name].row_count,
                    "schema": [
                        {"name": field.name, "type": str(field.type), "nullable": field.nullable}
                        for field in SCHEMAS[name]
                    ],
                    "files": [item for item in file_entries if item["path"].startswith(name + "/")],
                }
                for name in TABLE_ORDER
            },
        }
        (staging / "checksums.sha256").write_text(
            "".join(f"{item['sha256']}  {item['path']}\n" for item in file_entries),
            encoding="ascii",
        )
        (staging / "manifest.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        os.replace(staging, destination)
        return manifest
    except Exception:
        for sink in sinks.values():
            try:
                sink.close()
            except Exception:
                pass
        shutil.rmtree(staging, ignore_errors=True)
        raise


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=Path("data"))
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--snapshot-id", required=True)
    parser.add_argument("--batch-rows", type=int, default=5_000)
    parser.add_argument("--rows-per-file", type=int, default=250_000)
    args = parser.parse_args()
    try:
        commit = subprocess.run(
            ["git", "rev-parse", "HEAD"], check=True, text=True,
            stdout=subprocess.PIPE,
        ).stdout.strip()
        dirty = bool(subprocess.run(
            ["git", "status", "--porcelain"], check=True, text=True,
            stdout=subprocess.PIPE,
        ).stdout.strip())
        manifest = export_tables(
            args.data, args.output, snapshot_id=args.snapshot_id, git_commit=commit,
            git_dirty=dirty,
            batch_rows=args.batch_rows, rows_per_file=args.rows_per_file,
        )
    except (ValueError, OSError, sqlite3.Error) as exc:
        parser.exit(1, f"parquet export: {exc}\n")
    print(f"Exported {args.output}")
    for name in TABLE_ORDER:
        print(f"  {name}: {manifest['tables'][name]['rows']:,} rows")


if __name__ == "__main__":
    main()

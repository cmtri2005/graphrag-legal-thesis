"""Parquet table contract and GCS publication validation."""

import json
import sqlite3
from pathlib import Path

import pyarrow.parquet as pq
import pytest

from export_parquet_tables import TABLE_ORDER, export_tables
from scripts.gcs_tables import render_bigquery_sql, validate_export


def _jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows),
        encoding="utf-8",
    )


def _data(tmp_path: Path) -> Path:
    data = tmp_path / "data"
    data.mkdir()
    with sqlite3.connect(data / "temporal.sqlite") as db:
        db.executescript("""
            CREATE TABLE documents (
              id TEXT PRIMARY KEY, number TEXT NOT NULL, title TEXT NOT NULL,
              issued_on TEXT, effective_from TEXT, effective_to TEXT,
              issuer TEXT, rank TEXT, source_url TEXT, raw_status_code TEXT);
            CREATE TABLE provisions (
              id TEXT PRIMARY KEY, document_id TEXT NOT NULL, level TEXT NOT NULL,
              title TEXT NOT NULL, parent_id TEXT, order_index INTEGER, path TEXT NOT NULL);
        """)
        db.executemany(
            "INSERT INTO documents VALUES (?,?,?,?,?,?,?,?,?,?)",
            [
                ("document:actor", "01/2025", "Văn bản sửa đổi", "2025-01-01",
                 "2025-02-01", None, "CQ", "Luật", "https://actor", "CHL"),
                ("document:target", "02/2020", "Văn bản đích", "2020-01-01",
                 "2020-02-01", None, "CQ", "Luật", "https://target", "CHL"),
            ],
        )
        db.executemany(
            "INSERT INTO provisions VALUES (?,?,?,?,?,?,?)",
            [
                ("provision:article", "document:target", "Article", "Điều 1", None, 0,
                 "/provision:article"),
                ("provision:clause", "document:target", "Clause", "Khoản 1",
                 "provision:article", 0, "/provision:article/provision:clause"),
            ],
        )

    event = {
        "id": "event:one", "actor_id": "document:actor",
        "target_document_id": "document:target",
        "target_provision_id": "provision:clause", "operation": "amend",
        "effective_on": "2025-02-01", "status": "verified",
        "status_reason": None, "evidence": "Sửa đổi khoản 1.",
    }
    _jsonl(data / "derived/provision_events.jsonl", [event])
    _jsonl(data / "derived/event_log.jsonl", [{
        "event_id": "event:one", "input_line": 1, "outcome": "applied",
    }])
    _jsonl(data / "derived/versions.jsonl", [
        {
            "id": "version:article:1", "provision_id": "provision:article",
            "ordinal": 1, "text": "Điều 1", "valid_from": "2020-02-01",
            "valid_to": None, "effective_interval_count": 1,
            "effective_intervals": [{"start": "2020-02-01", "end": None}],
            "effective_from": "2020-02-01", "effective_to": None,
            "created_by_event_id": None, "ended_by_event_id": None, "provenance": [],
        },
        {
            "id": "version:clause:1", "provision_id": "provision:clause",
            "ordinal": 1, "text": "Nội dung cũ", "valid_from": "2020-02-01",
            "valid_to": "2025-02-01", "effective_interval_count": 1,
            "effective_intervals": [{"start": "2020-02-01", "end": "2025-02-01"}],
            "effective_from": "2020-02-01", "effective_to": "2025-02-01",
            "created_by_event_id": None, "ended_by_event_id": "event:one", "provenance": [],
        },
        {
            "id": "version:clause:2", "provision_id": "provision:clause",
            "ordinal": 2, "text": "Nội dung mới", "valid_from": "2025-02-01",
            "valid_to": None, "effective_interval_count": 1,
            "effective_intervals": [{"start": "2025-02-01", "end": None}],
            "effective_from": "2025-02-01", "effective_to": None,
            "created_by_event_id": "event:one", "ended_by_event_id": None,
            "provenance": [],
        },
    ])
    _jsonl(data / "edges.jsonl", [
        {"source_id": "actor", "target_id": "target", "reference_type": 10,
         "label_vi": "Văn bản được sửa đổi bổ sung", "group": "genealogy"},
        {"source_id": "actor", "target_id": "missing", "reference_type": 10,
         "label_vi": "Văn bản được sửa đổi bổ sung", "group": "genealogy"},
    ])
    (data / "reference_type_map.json").write_text(json.dumps({"codes": {"10": {
        "label_vi": "Văn bản được sửa đổi bổ sung", "group": "genealogy", "verified": True,
    }}}), encoding="utf-8")
    return data


def test_export_produces_seven_typed_tables_and_graph_edges(tmp_path):
    data = _data(tmp_path)
    output = tmp_path / "tables"
    manifest = export_tables(
        data, output, snapshot_id="sample-01", git_commit="deadbeef",
        batch_rows=2, rows_per_file=2,
    )

    assert tuple(manifest["tables"]) == TABLE_ORDER
    assert {name: manifest["tables"][name]["rows"] for name in TABLE_ORDER} == {
        "documents": 2, "provisions": 2, "provision_versions": 3,
        "legal_events": 1, "containment_edges": 2, "causal_edges": 3,
        "document_reference_edges": 2,
    }
    assert validate_export(output)["snapshot_id"] == "sample-01"

    references = pq.read_table(output / "document_reference_edges").to_pylist()
    assert [row["target_resolved"] for row in references] == [True, False]
    causal = pq.read_table(output / "causal_edges").to_pylist()
    assert {(row["source_kind"], row["target_kind"], row["role"]) for row in causal} == {
        ("LegalEvent", "Document", "actor"),
        ("ProvisionVersion", "LegalEvent", "ended"),
        ("ProvisionVersion", "LegalEvent", "created"),
    }


def test_export_is_immutable_and_validator_detects_tampering(tmp_path):
    data = _data(tmp_path)
    output = tmp_path / "tables"
    export_tables(data, output, snapshot_id="sample-01", git_commit="deadbeef",
                  batch_rows=2, rows_per_file=2)
    with pytest.raises(ValueError, match="destination already exists"):
        export_tables(data, output, snapshot_id="sample-02", git_commit="deadbeef")

    first = next(output.glob("documents/*.parquet"))
    with first.open("ab") as stream:
        stream.write(b"tampered")
    with pytest.raises(ValueError, match="checksum/size/row mismatch"):
        validate_export(output)


def test_bigquery_sql_uses_all_tables_and_snapshot_prefix():
    sql = render_bigquery_sql(
        "gs://bucket/tables/snapshot-01", "graphrag-509313", "legal_graph"
    )
    for table in TABLE_ORDER:
        assert f"`graphrag-509313.legal_graph.{table}`" in sql
        assert f"gs://bucket/tables/snapshot-01/{table}/*.parquet" in sql
    with pytest.raises(ValueError, match="dataset"):
        render_bigquery_sql("gs://bucket/x", "graphrag-509313", "bad-dataset")

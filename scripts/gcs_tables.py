#!/usr/bin/env python3
"""Validate and publish an immutable Parquet table snapshot to GCS.

Optionally creates a colocated BigQuery dataset and seven external tables that
read the uploaded Parquet objects without duplicating their storage.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import tempfile
from pathlib import Path, PurePosixPath
from typing import Any

import pyarrow.parquet as pq


DEFAULT_BUCKET = "gs://graphrag-legal-thesis"
TABLES = (
    "documents", "provisions", "provision_versions", "legal_events",
    "containment_edges", "causal_edges", "document_reference_edges",
)
IDENTIFIER = re.compile(r"[A-Za-z_][A-Za-z0-9_]{0,1023}\Z")
PROJECT_ID = re.compile(r"[a-z][a-z0-9-]{4,28}[a-z0-9]\Z")
SNAPSHOT_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}\Z")


def _run(*args: str, capture: bool = False, input_text: str | None = None) -> str:
    result = subprocess.run(
        args, check=True, text=True, input=input_text,
        stdout=subprocess.PIPE if capture else None,
    )
    return result.stdout.strip() if capture else ""


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _bucket(value: str) -> str:
    value = value.rstrip("/")
    if not value.startswith("gs://") or not value[5:] or ".." in value.split("/"):
        raise ValueError("bucket must be a gs:// URI without '..' components")
    return value


def validate_export(root: Path) -> dict[str, Any]:
    manifest_path = root / "manifest.json"
    checksum_path = root / "checksums.sha256"
    if not root.is_dir() or not manifest_path.is_file() or not checksum_path.is_file():
        raise ValueError("export must contain manifest.json and checksums.sha256")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    snapshot_id = manifest.get("snapshot_id")
    if manifest.get("schema_version") != 1 or manifest.get("format") != "parquet":
        raise ValueError("unsupported table manifest schema/format")
    if not isinstance(snapshot_id, str) or not SNAPSHOT_ID.fullmatch(snapshot_id):
        raise ValueError("invalid snapshot_id in table manifest")
    if set(manifest.get("tables", {})) != set(TABLES):
        raise ValueError("manifest table set differs from the seven-table contract")

    expected_checksums: dict[str, str] = {}
    manifest_paths: set[str] = set()
    for table_name in TABLES:
        table = manifest["tables"][table_name]
        total_rows = 0
        expected_schema = table.get("schema")
        if not isinstance(expected_schema, list) or not expected_schema:
            raise ValueError(f"{table_name}: manifest has no schema")
        files = table.get("files")
        if not isinstance(files, list) or not files:
            raise ValueError(f"{table_name}: manifest has no Parquet files")
        for item in files:
            relative = item.get("path")
            path = PurePosixPath(relative) if isinstance(relative, str) else None
            if path is None or path.is_absolute() or ".." in path.parts or path.parts[0] != table_name:
                raise ValueError(f"{table_name}: unsafe file path {relative!r}")
            local = root.joinpath(*path.parts)
            if not local.is_file():
                raise ValueError(f"{table_name}: missing {relative}")
            digest = _sha256(local)
            if (
                digest != item.get("sha256")
                or local.stat().st_size != item.get("bytes")
            ):
                raise ValueError(f"{table_name}: checksum/size/row mismatch for {relative}")
            metadata = pq.read_metadata(local)
            if metadata.num_rows != item.get("rows"):
                raise ValueError(f"{table_name}: checksum/size/row mismatch for {relative}")
            actual_schema = [
                {"name": field.name, "type": str(field.type), "nullable": field.nullable}
                for field in pq.read_schema(local)
            ]
            if actual_schema != expected_schema:
                raise ValueError(f"{table_name}: Parquet schema differs from manifest")
            manifest_paths.add(relative)
            total_rows += metadata.num_rows
            expected_checksums[relative] = digest
        if total_rows != table.get("rows"):
            raise ValueError(f"{table_name}: total rows differ from manifest")
    actual_files = {
        str(path.relative_to(root).as_posix())
        for path in root.glob("*/*.parquet")
    }
    if actual_files != manifest_paths:
        raise ValueError("Parquet file set differs from manifest")
    expected_text = "".join(
        f"{expected_checksums[path]}  {path}\n" for path in sorted(expected_checksums)
    )
    if checksum_path.read_text(encoding="ascii") != expected_text:
        raise ValueError("checksums.sha256 differs from manifest/files")
    return manifest


def render_bigquery_sql(prefix: str, project_id: str, dataset: str) -> str:
    if not PROJECT_ID.fullmatch(project_id):
        raise ValueError(f"invalid GCP project ID: {project_id!r}")
    if not IDENTIFIER.fullmatch(dataset):
        raise ValueError(f"invalid BigQuery dataset: {dataset!r}")
    statements = [
        "-- Generated external-table definitions for one immutable GCS snapshot.",
        "-- Re-running replaces definitions, not the Parquet objects.",
    ]
    for table in TABLES:
        statements.append(
            f"\nCREATE OR REPLACE EXTERNAL TABLE `{project_id}.{dataset}.{table}`\n"
            "OPTIONS (\n"
            "  format = 'PARQUET',\n"
            f"  uris = ['{prefix}/{table}/*.parquet']\n"
            ");"
        )
    return "\n".join(statements) + "\n"


def publish(
    root: Path,
    bucket: str,
    *,
    project_id: str,
    dataset: str,
    create_bigquery: bool = False,
    location: str = "us-east1",
) -> str:
    if shutil.which("gcloud") is None:
        raise RuntimeError("gcloud is not installed or not on PATH")
    manifest = validate_export(root)
    prefix = f"{_bucket(bucket)}/tables/{manifest['snapshot_id']}"
    sql = render_bigquery_sql(prefix, project_id, dataset)
    with tempfile.TemporaryDirectory(prefix="gcs-parquet-tables-") as temp:
        sql_path = Path(temp) / "create_external_tables.sql"
        sql_path.write_text(sql, encoding="utf-8")
        files = sorted(path for path in root.rglob("*") if path.is_file())
        # Manifest is the completion marker and must be uploaded last.
        files = [path for path in files if path.name != "manifest.json"]
        for path in [*files, sql_path, root / "manifest.json"]:
            relative = (
                "create_external_tables.sql" if path == sql_path
                else path.relative_to(root).as_posix()
            )
            print(f"Uploading {relative}...", flush=True)
            _run(
                "gcloud", "storage", "cp", str(path), f"{prefix}/{relative}",
                "--if-generation-match=0",
            )
    if create_bigquery:
        if shutil.which("bq") is None:
            raise RuntimeError("bq is not installed or not on PATH")
        show = subprocess.run(
            ["bq", f"--project_id={project_id}", "show", f"{project_id}:{dataset}"],
            text=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        if show.returncode != 0:
            _run(
                "bq", f"--project_id={project_id}", f"--location={location}",
                "mk", "--dataset", "--description=Temporal legal graph analytical tables",
                f"{project_id}:{dataset}",
            )
        _run(
            "bq", f"--project_id={project_id}", f"--location={location}",
            "query", "--use_legacy_sql=false", input_text=sql,
        )
    return prefix


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("export", type=Path)
    parser.add_argument("--bucket", default=DEFAULT_BUCKET)
    parser.add_argument("--project-id", default="graphrag-509313")
    parser.add_argument("--dataset", default="legal_graph")
    parser.add_argument("--location", default="us-east1")
    parser.add_argument("--create-bigquery", action="store_true")
    args = parser.parse_args()
    try:
        prefix = publish(
            args.export, args.bucket, project_id=args.project_id,
            dataset=args.dataset, create_bigquery=args.create_bigquery,
            location=args.location,
        )
    except (ValueError, RuntimeError, OSError, subprocess.CalledProcessError) as exc:
        parser.exit(1, f"GCS table publish: {exc}\n")
    print(f"Published: {prefix}")
    if args.create_bigquery:
        print(f"BigQuery: {args.project_id}.{args.dataset}")


if __name__ == "__main__":
    main()

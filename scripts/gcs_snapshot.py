#!/usr/bin/env python3
"""Publish and restore immutable data snapshots in Cloud Storage.

Source snapshots omit rebuildable artifacts by default. ``push --full`` keeps
the complete ``data/`` tree for an exact project-data backup.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import tarfile
import tempfile
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath


DEFAULT_BUCKET = "gs://graphrag-legal-thesis"
EXCLUDED = ("data/derived", "data/temporal.sqlite", "data/expiry_targets.jsonl")
ARCHIVE = "data.tar.gz"
CHECKSUM = "data.tar.gz.sha256"
MANIFEST = "manifest.json"
SNAPSHOT_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}\Z")


def _run(*args: str, capture: bool = False) -> str:
    result = subprocess.run(
        args, check=True, text=True,
        stdout=subprocess.PIPE if capture else None,
    )
    return result.stdout.strip() if capture else ""


def _bucket(value: str) -> str:
    value = value.rstrip("/")
    if not value.startswith("gs://") or not value[5:] or ".." in value.split("/"):
        raise ValueError("bucket must be a gs:// URI without '..' components")
    return value


def _snapshot_id(value: str) -> str:
    if not SNAPSHOT_ID.fullmatch(value):
        raise ValueError("snapshot ID must contain only letters, digits, '.', '_' or '-' ")
    return value


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _git_commit() -> str:
    return _run("git", "rev-parse", "HEAD", capture=True)


def make_archive(
    data_dir: Path, archive: Path, excluded: tuple[str, ...] = EXCLUDED
) -> None:
    """Package data/, optionally excluding known rebuildable outputs."""
    if data_dir.name != "data" or not data_dir.is_dir():
        raise ValueError("source must be an existing directory named data")
    raw = data_dir / "raw"
    if not raw.is_dir() or not any(raw.iterdir()):
        raise ValueError("data/raw is empty; refusing to publish an empty snapshot")
    _run(
        "tar", "-czf", str(archive),
        *(f"--exclude={item}" for item in excluded),
        "-C", str(data_dir.parent), "data",
    )


def validate_archive(
    archive: Path, excluded: tuple[str, ...] = EXCLUDED
) -> None:
    """Reject traversal, links and files forbidden by the snapshot policy."""
    has_raw = False
    with tarfile.open(archive, mode="r|gz") as stream:
        for member in stream:
            path = PurePosixPath(member.name)
            parts = path.parts
            if (
                member.name.startswith("/") or not parts or parts[0] != "data"
                or ".." in parts or not (member.isfile() or member.isdir())
            ):
                raise ValueError(f"unsafe archive member: {member.name!r}")
            if any(
                path == forbidden or forbidden in path.parents
                for forbidden in map(PurePosixPath, excluded)
            ):
                raise ValueError(f"derived file in source snapshot: {member.name!r}")
            has_raw |= len(parts) >= 3 and parts[1] == "raw" and member.isfile()
    if not has_raw:
        raise ValueError("archive has no data/raw files")


def publish(
    data_dir: Path, bucket: str, snapshot_id: str, *, full: bool = False
) -> str:
    bucket = _bucket(bucket)
    snapshot_id = _snapshot_id(snapshot_id)
    if shutil.which("gcloud") is None:
        raise RuntimeError("gcloud is not installed or not on PATH")
    prefix = f"{bucket}/snapshots/{snapshot_id}"
    excluded: tuple[str, ...] = () if full else EXCLUDED
    snapshot_type = "full" if full else "source"
    with tempfile.TemporaryDirectory(prefix="gcs-source-snapshot-") as temp:
        local = Path(temp)
        archive = local / ARCHIVE
        print(f"Packaging {snapshot_type} data from {data_dir}...", flush=True)
        make_archive(data_dir, archive, excluded)
        validate_archive(archive, excluded)
        digest = _sha256(archive)
        (local / CHECKSUM).write_text(f"{digest}  {ARCHIVE}\n", encoding="ascii")
        manifest = {
            "schema_version": 1,
            "snapshot_id": snapshot_id,
            "created_at_utc": datetime.now(timezone.utc).isoformat(),
            "git_commit": _git_commit(),
            "source": "data/",
            "snapshot_type": snapshot_type,
            "excluded": list(excluded),
            "archive_sha256": digest,
            "archive_bytes": archive.stat().st_size,
        }
        (local / MANIFEST).write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        # The manifest is the completion marker. A failed upload leaves an
        # incomplete prefix, never a snapshot that appears ready to restore.
        for name in (ARCHIVE, CHECKSUM, MANIFEST):
            print(f"Uploading {name} to {prefix}...", flush=True)
            _run("gcloud", "storage", "cp", str(local / name), f"{prefix}/{name}",
                 "--if-generation-match=0")
    return prefix


def restore(bucket: str, snapshot_id: str, destination: Path) -> Path:
    bucket = _bucket(bucket)
    snapshot_id = _snapshot_id(snapshot_id)
    if shutil.which("gcloud") is None:
        raise RuntimeError("gcloud is not installed or not on PATH")
    if destination.name == "data":
        raise ValueError("destination must be an empty parent directory, not data/ itself")
    if destination.exists() and (not destination.is_dir() or any(destination.iterdir())):
        raise ValueError(f"destination is not an empty directory: {destination}")
    prefix = f"{bucket}/snapshots/{snapshot_id}"
    with tempfile.TemporaryDirectory(prefix="gcs-source-snapshot-") as temp:
        local = Path(temp)
        for name in (MANIFEST, CHECKSUM, ARCHIVE):
            print(f"Downloading {name} from {prefix}...", flush=True)
            _run("gcloud", "storage", "cp", f"{prefix}/{name}", str(local / name))
        manifest = json.loads((local / MANIFEST).read_text(encoding="utf-8"))
        excluded_value = manifest.get("excluded")
        if excluded_value == list(EXCLUDED):
            excluded = EXCLUDED
            inferred_type = "source"
        elif excluded_value == []:
            excluded = ()
            inferred_type = "full"
        else:
            raise ValueError("snapshot manifest has an unsupported exclusion policy")
        if (
            manifest.get("schema_version") != 1
            or manifest.get("snapshot_id") != snapshot_id
            or manifest.get("snapshot_type", inferred_type) != inferred_type
        ):
            raise ValueError("snapshot manifest is incompatible with this data policy")
        digest = _sha256(local / ARCHIVE)
        if digest != manifest.get("archive_sha256"):
            raise ValueError("archive SHA-256 differs from manifest")
        if (local / CHECKSUM).read_text(encoding="ascii") != f"{digest}  {ARCHIVE}\n":
            raise ValueError("archive SHA-256 differs from checksum file")
        if (local / ARCHIVE).stat().st_size != manifest.get("archive_bytes"):
            raise ValueError("archive size differs from manifest")
        validate_archive(local / ARCHIVE, excluded)
        print(f"Verified SHA-256 {digest}; extracting into {destination}...", flush=True)
        destination.mkdir(parents=True, exist_ok=True)
        _run("tar", "-xzf", str(local / ARCHIVE), "--no-same-owner", "-C", str(destination))
    return destination / "data"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bucket", default=DEFAULT_BUCKET,
                        help=f"Cloud Storage bucket or prefix (default: {DEFAULT_BUCKET})")
    commands = parser.add_subparsers(dest="command", required=True)
    push = commands.add_parser("push", help="publish a new immutable data snapshot")
    push.add_argument("--data-dir", type=Path, default=Path(__file__).resolve().parent.parent / "data")
    push.add_argument("--snapshot-id", help="default: UTC timestamp followed by short Git commit")
    push.add_argument("--full", action="store_true",
                      help="include derived/, temporal.sqlite and expiry_targets.jsonl")
    pull = commands.add_parser("pull", help="restore a snapshot into an empty parent directory")
    pull.add_argument("snapshot_id")
    pull.add_argument("destination", type=Path)
    args = parser.parse_args()
    try:
        if args.command == "push":
            snapshot_id = args.snapshot_id or (
                datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + _git_commit()[:8]
                + ("-full" if args.full else "")
            )
            print("Published:", publish(args.data_dir, args.bucket, snapshot_id, full=args.full))
        else:
            print("Restored:", restore(args.bucket, args.snapshot_id, args.destination))
    except (ValueError, RuntimeError, subprocess.CalledProcessError) as exc:
        parser.exit(1, f"gcs snapshot: {exc}\n")


if __name__ == "__main__":
    main()

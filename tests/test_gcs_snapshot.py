"""Offline proof for the Cloud Storage source-snapshot transport."""

import io
import json
import shutil
import tarfile
from pathlib import Path

import pytest

from scripts import gcs_snapshot


def _source(tmp_path: Path) -> Path:
    data = tmp_path / "source" / "data"
    (data / "raw").mkdir(parents=True)
    (data / "raw" / "one.json").write_text('{"id":"one"}', encoding="utf-8")
    (data / "derived").mkdir()
    (data / "derived" / "versions.jsonl").write_text("generated", encoding="utf-8")
    (data / "temporal.sqlite").write_text("generated", encoding="utf-8")
    (data / "expiry_targets.jsonl").write_text("generated", encoding="utf-8")
    (data / "manifest.sqlite").write_text("crawl state", encoding="utf-8")
    (data / "edges.jsonl").write_text("source edge", encoding="utf-8")
    return data


def test_publish_and_restore_source_snapshot_without_derived(tmp_path, monkeypatch):
    data = _source(tmp_path)
    cloud = tmp_path / "cloud"
    actual_run = gcs_snapshot._run
    monkeypatch.setattr(gcs_snapshot.shutil, "which", lambda name: "/usr/bin/gcloud")
    monkeypatch.setattr(gcs_snapshot, "_git_commit", lambda: "deadbeef")

    def fake_run(*args, capture=False):
        if args[0] != "gcloud":
            return actual_run(*args, capture=capture)
        assert args[1:3] == ("storage", "cp")
        source, target = args[3:5]
        if source.startswith("gs://"):
            remote = cloud / source.removeprefix("gs://")
            shutil.copyfile(remote, target)
        else:
            assert args[5:] == ("--if-generation-match=0",)
            remote = cloud / target.removeprefix("gs://")
            remote.parent.mkdir(parents=True, exist_ok=True)
            assert not remote.exists(), "immutable snapshot must not overwrite an object"
            shutil.copyfile(source, remote)
        return ""

    monkeypatch.setattr(gcs_snapshot, "_run", fake_run)
    prefix = gcs_snapshot.publish(data, "gs://thesis-bucket", "test-01")
    assert prefix == "gs://thesis-bucket/snapshots/test-01"
    assert (cloud / "thesis-bucket/snapshots/test-01/manifest.json").is_file()

    restored = gcs_snapshot.restore("gs://thesis-bucket", "test-01", tmp_path / "restore")
    assert (restored / "raw/one.json").read_text(encoding="utf-8") == '{"id":"one"}'
    assert (restored / "manifest.sqlite").read_text(encoding="utf-8") == "crawl state"
    assert (restored / "edges.jsonl").read_text(encoding="utf-8") == "source edge"
    assert not (restored / "derived").exists()
    assert not (restored / "temporal.sqlite").exists()
    assert not (restored / "expiry_targets.jsonl").exists()

    remote_archive = cloud / "thesis-bucket/snapshots/test-01/data.tar.gz"
    with remote_archive.open("ab") as stream:
        stream.write(b"tampered")
    with pytest.raises(ValueError, match="SHA-256 differs"):
        gcs_snapshot.restore("gs://thesis-bucket", "test-01", tmp_path / "unsafe-restore")
    assert not (tmp_path / "unsafe-restore").exists()


def test_restore_refuses_nonempty_destination_before_download(tmp_path, monkeypatch):
    destination = tmp_path / "restore"
    destination.mkdir()
    (destination / "keep.txt").write_text("mine", encoding="utf-8")
    monkeypatch.setattr(gcs_snapshot.shutil, "which", lambda name: "/usr/bin/gcloud")
    monkeypatch.setattr(gcs_snapshot, "_run", lambda *args, **kwargs: pytest.fail("download attempted"))

    with pytest.raises(ValueError, match="not an empty directory"):
        gcs_snapshot.restore("gs://thesis-bucket", "test-01", destination)
    assert (destination / "keep.txt").read_text(encoding="utf-8") == "mine"


def test_full_snapshot_preserves_every_data_artifact(tmp_path, monkeypatch):
    data = _source(tmp_path)
    cloud = tmp_path / "cloud"
    actual_run = gcs_snapshot._run
    monkeypatch.setattr(gcs_snapshot.shutil, "which", lambda name: "/usr/bin/gcloud")
    monkeypatch.setattr(gcs_snapshot, "_git_commit", lambda: "deadbeef")

    def fake_run(*args, capture=False):
        if args[0] != "gcloud":
            return actual_run(*args, capture=capture)
        source, target = args[3:5]
        if source.startswith("gs://"):
            shutil.copyfile(cloud / source.removeprefix("gs://"), target)
        else:
            remote = cloud / target.removeprefix("gs://")
            remote.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, remote)
        return ""

    monkeypatch.setattr(gcs_snapshot, "_run", fake_run)
    gcs_snapshot.publish(data, "gs://thesis-bucket", "full-01", full=True)
    manifest = json.loads(
        (cloud / "thesis-bucket/snapshots/full-01/manifest.json").read_text(encoding="utf-8")
    )
    assert manifest["snapshot_type"] == "full"
    assert manifest["excluded"] == []

    restored = gcs_snapshot.restore("gs://thesis-bucket", "full-01", tmp_path / "full-restore")
    assert (restored / "derived/versions.jsonl").read_text(encoding="utf-8") == "generated"
    assert (restored / "temporal.sqlite").read_text(encoding="utf-8") == "generated"
    assert (restored / "expiry_targets.jsonl").read_text(encoding="utf-8") == "generated"


@pytest.mark.parametrize("name,kind", [
    ("data/../outside.txt", "file"),
    ("data/derived/versions.jsonl", "file"),
    ("data/raw/link", "symlink"),
])
def test_archive_validation_rejects_unsafe_members(tmp_path, name, kind):
    archive = tmp_path / "bad.tar.gz"
    with tarfile.open(archive, "w:gz") as stream:
        info = tarfile.TarInfo(name)
        if kind == "symlink":
            info.type = tarfile.SYMTYPE
            info.linkname = "../../outside"
            stream.addfile(info)
        else:
            payload = b"bad"
            info.size = len(payload)
            stream.addfile(info, io.BytesIO(payload))
    with pytest.raises(ValueError, match="unsafe archive member|derived file"):
        gcs_snapshot.validate_archive(archive)


def test_publish_refuses_empty_raw_and_invalid_snapshot_id(tmp_path, monkeypatch):
    data = tmp_path / "data"
    (data / "raw").mkdir(parents=True)
    monkeypatch.setattr(gcs_snapshot.shutil, "which", lambda name: "/usr/bin/gcloud")
    with pytest.raises(ValueError, match="data/raw is empty"):
        gcs_snapshot.publish(data, "gs://thesis-bucket", "test-01")
    with pytest.raises(ValueError, match="snapshot ID"):
        gcs_snapshot.publish(data, "gs://thesis-bucket", "../outside")

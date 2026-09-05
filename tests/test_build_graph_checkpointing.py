"""Covers the resumability guarantee: a doc already persisted on disk must
be served from cache (no network call), and a fresh fetch must be persisted
immediately — not only after the whole BFS finishes (see scripts/pipeline/build_graph.py).
"""

from pathlib import Path

from build_graph import make_checkpointing_fetcher
from legal_crawler.storage.manifest import CrawlManifest


class FakeApiClient:
    def __init__(self, documents: dict[str, dict]):
        self._documents = documents
        self.calls: list[str] = []

    def get_document(self, doc_id: str) -> dict:
        self.calls.append(doc_id)
        return self._documents[doc_id]


def test_fresh_fetch_is_persisted_immediately(tmp_path: Path):
    out_dir = tmp_path / "raw"
    out_dir.mkdir()
    client = FakeApiClient({"1": {"docNum": "1/2024", "effStatus": {"name": "Còn hiệu lực"}}})
    manifest = CrawlManifest(tmp_path / "manifest.sqlite")
    fetch = make_checkpointing_fetcher(out_dir, manifest, client, lastmod_by_id={"1": "2026-01-01"})

    fetch("1")

    assert (out_dir / "1.json").exists()
    assert manifest.get("1") is not None
    assert manifest.get("1").eff_status == "Còn hiệu lực"
    assert client.calls == ["1"]


def test_cached_doc_skips_network_call(tmp_path: Path):
    out_dir = tmp_path / "raw"
    out_dir.mkdir()
    (out_dir / "1.json").write_text('{"docNum": "1/2024"}', encoding="utf-8")
    client = FakeApiClient({})  # would KeyError if fetch() ever called get_document
    manifest = CrawlManifest(tmp_path / "manifest.sqlite")
    fetch = make_checkpointing_fetcher(out_dir, manifest, client, lastmod_by_id={})

    document = fetch("1")

    assert document == {"docNum": "1/2024"}
    assert client.calls == []  # resumed run must not re-hit the network
    assert manifest.get("1") is None  # not re-recorded; it was already there from before


def test_interrupted_then_resumed_run_only_fetches_the_gap(tmp_path: Path):
    """Simulates: run 1 fetches doc "1" then "crashes" before doc "2"; run 2
    (same call, fresh fetcher instance) must skip "1" and only fetch "2"."""
    out_dir = tmp_path / "raw"
    out_dir.mkdir()
    client = FakeApiClient({"1": {"docNum": "1"}, "2": {"docNum": "2"}})
    manifest = CrawlManifest(tmp_path / "manifest.sqlite")

    run_1 = make_checkpointing_fetcher(out_dir, manifest, client, lastmod_by_id={})
    run_1("1")  # "crash" happens here — doc "2" never fetched in run 1

    run_2 = make_checkpointing_fetcher(out_dir, manifest, client, lastmod_by_id={})
    run_2("1")
    run_2("2")

    assert client.calls == ["1", "2"]  # "1" fetched once total, across both runs

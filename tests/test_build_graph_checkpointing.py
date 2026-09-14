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


def test_edges_are_rebuilt_from_every_raw_file_not_from_one_run(tmp_path: Path):
    """edges.jsonl must not depend on which seeds a run started from: a document
    held on disk contributes its edges even if no BFS reached it this time, and a
    reference repeated with a different row id is written once."""
    import json

    from build_graph import write_edges
    from legal_crawler.vocab.reference_types import ReferenceTypeMap

    raw = tmp_path / "raw"
    raw.mkdir()

    def ref(target: str, code: int, row: str) -> dict:
        return {"id": row, "referenceType": code, "targetDocument": {"id": target}}

    (raw / "A.json").write_text(
        json.dumps({"references": [ref("B", 10, "r1"), ref("B", 10, "r2"), ref("C", 3, "r3")]}),
        encoding="utf-8",
    )
    (raw / "D.json").write_text(json.dumps({"references": [ref("A", 1, "r4")]}), encoding="utf-8")
    (raw / "E.json").write_text(json.dumps({"references": [{"referenceType": 1}]}), encoding="utf-8")

    out = tmp_path / "edges.jsonl"
    count = write_edges(raw, out, ReferenceTypeMap.load())

    rows = [json.loads(line) for line in out.read_text(encoding="utf-8").splitlines()]
    assert count == len(rows) == 3
    assert [(r["source_id"], r["target_id"], r["reference_type"]) for r in rows] == [
        ("A", "B", 10), ("A", "C", 3), ("D", "A", 1),
    ]
    assert write_edges(raw, out, ReferenceTypeMap.load()) == 3  # rerun is identical


def test_review_queue_is_rebuilt_from_the_whole_corpus(tmp_path: Path):
    """A run that processes one document must not shrink the queue to that one."""
    from attach_provision_text import write_review_queue
    from legal_crawler.storage.documents import DocumentStore

    store = DocumentStore(tmp_path)
    for doc_id, coverage in (("old-low", 0.1), ("fresh-low", 0.2), ("fine", 0.9)):
        store.save("provisions", doc_id, {
            "doc_id": doc_id, "method": "marker", "coverage": coverage,
            "total_nodes": 10, "nodes": {},
        })
    path = tmp_path / "provision_review.txt"
    assert write_review_queue(store, path) == 2
    ids = [line.split("\t")[0] for line in path.read_text(encoding="utf-8").splitlines()[1:]]
    assert ids == ["fresh-low", "old-low"]
    first = path.read_text(encoding="utf-8")
    write_review_queue(store, path)
    assert path.read_text(encoding="utf-8") == first

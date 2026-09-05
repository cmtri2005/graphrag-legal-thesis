import json

import pytest

from legal_crawler.storage.documents import (
    PER_DOCUMENT_DIRS,
    DocumentStore,
    load_permanent_failures,
    read_json,
    write_json,
)


def test_round_trip_keeps_vietnamese_text_readable(tmp_path):
    # ensure_ascii would turn every accented character into \uXXXX, making the
    # files unreadable with the plain shell tools this layout exists to allow.
    path = tmp_path / "a.json"
    written = write_json(path, {"title": "Nghị định về đất đai"})
    assert "Nghị định" in written
    assert path.read_text(encoding="utf-8") == written
    assert read_json(path)["title"] == "Nghị định về đất đai"


def test_written_text_is_what_the_caller_hashes(tmp_path):
    # build_graph stores a hash of the file; re-serialising to hash it would be
    # a second chance for the two to differ.
    doc = {"id": "1", "n": 1.0}
    assert write_json(tmp_path / "a.json", doc) == (tmp_path / "a.json").read_text(encoding="utf-8")


def test_ids_of_a_stage_that_was_never_run_is_empty_not_an_error(tmp_path):
    assert DocumentStore(tmp_path).ids("provisions") == set()


def test_save_creates_the_stage_directory(tmp_path):
    store = DocumentStore(tmp_path)
    store.save("trees", "42", [])
    assert store.load("trees", "42") == []


def test_drop_clears_every_cache_for_one_document(tmp_path):
    # This is the whole delta-crawl mechanism: the fetchers treat an existing
    # file as their checkpoint, so deleting it is how a document is re-fetched.
    store = DocumentStore(tmp_path)
    for stage in PER_DOCUMENT_DIRS:
        store.save(stage, "42", {"id": "42"})
    store.save("raw", "99", {"id": "99"})

    assert store.drop("42") == len(PER_DOCUMENT_DIRS)
    assert store.ids("raw") == {"99"}
    assert store.drop("42") == 0  # already gone, still not an error


def test_permanent_failures_are_read_per_stage(tmp_path):
    path = tmp_path / "fetch_failures.txt"
    path.write_text(
        "# stage\tdoc_id\ttitle\n"
        "tree\t121053\tThông tư số 28/2017/TT-BTC\n"
        "tree\t142847\tLuật Doanh nghiệp số 59/2020/QH14\n"
        "history\t142847\tLuật Doanh nghiệp số 59/2020/QH14\n",
        encoding="utf-8",
    )
    assert load_permanent_failures(path, "tree") == {"121053", "142847"}
    assert load_permanent_failures(path, "history") == {"142847"}


def test_a_missing_failure_list_skips_nothing(tmp_path):
    assert load_permanent_failures(tmp_path / "nope.txt", "tree") == set()


def test_malformed_json_raises_rather_than_returning_empty(tmp_path):
    (tmp_path / "a.json").write_text("{oops", encoding="utf-8")
    with pytest.raises(json.JSONDecodeError):
        read_json(tmp_path / "a.json")

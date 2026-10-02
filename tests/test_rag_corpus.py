"""The retrieval index: what it stores, and the two window kinds it keeps apart."""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest

from vilexgraph.framework.corpus import Corpus, _document_heading, _heading, build

DOC = "document:d1"
CHAPTER, ARTICLE, CLAUSE = "provision:c1", "provision:a1", "provision:k1"


def write(path: Path, rows) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows),
                    encoding="utf-8")


@pytest.fixture
def data(tmp_path: Path) -> Path:
    """A document whose Điều is repealed under a Khoản that never closed itself.

    That is the one shape the ladder has to tell apart: the clause's own window
    is open, while its propagated window ends when the ancestor is repealed.
    """
    root = tmp_path / "data"
    write(root / "derived/corpus/documents.jsonl", [
        {"document_id": DOC, "law_id": "11/2020/TT-X", "title": "Thông tư số 11/2020/TT-X Quy định mẫu",
         "rank": "Thông tư", "issued_on": "2019-12-01",
         "effective_from": "2020-01-01", "effective_to": None},
    ])
    write(root / "derived/corpus/asis.jsonl", [
        {"unit_id": f"asis:{CLAUSE}", "kind": "provision", "provision_id": CLAUSE,
         "document_id": DOC, "level": "Clause", "text": "1. Nội dung khoản một."},
        {"unit_id": "asis:event:e1", "kind": "instruction", "event_id": "event:e1",
         "operation": "repeal", "document_id": DOC, "target_provision_id": "None",
         "text": "Bãi bỏ Điều 1."},
    ])
    write(root / "derived/corpus/versions.jsonl", [
        # propagated: closed by the ancestor's repeal on 2022-01-01
        {"unit_id": f"version:{CLAUSE.split(':')[1]}:1", "provision_id": CLAUSE,
         "document_id": DOC, "level": "Clause", "ordinal": 1,
         "text": "1. Nội dung khoản một.",
         "effective_intervals": [{"start": "2020-01-01", "end": "2022-01-01"}]},
    ])
    write(root / "derived/versions.jsonl", [
        # local: the chain itself never closed
        {"id": f"version:{CLAUSE.split(':')[1]}:1", "provision_id": CLAUSE, "ordinal": 1,
         "text": "1. Nội dung khoản một.", "valid_from": "2020-01-01", "valid_to": None,
         "effective_intervals": [{"start": "2020-01-01", "end": "2022-01-01"}]},
    ])
    db = sqlite3.connect(root / "temporal.sqlite")
    db.executescript("""
        CREATE TABLE documents (id TEXT PRIMARY KEY, number TEXT, title TEXT, issued_on TEXT,
            effective_from TEXT, effective_to TEXT, issuer TEXT, rank TEXT, source_url TEXT,
            raw_status_code TEXT);
        CREATE TABLE provisions (id TEXT PRIMARY KEY, document_id TEXT, level TEXT, title TEXT,
            parent_id TEXT, order_index INTEGER, path TEXT);
        CREATE TABLE versions (id TEXT PRIMARY KEY, provision_id TEXT, ordinal INTEGER,
            text TEXT, valid_from TEXT, valid_to TEXT);
    """)
    db.execute("INSERT INTO documents VALUES (?,?,?,?,?,?,?,?,?,?)",
               (DOC, "11/2020/TT-X", "Thông tư số 11/2020/TT-X Quy định mẫu", "2019-12-01",
                "2020-01-01", None, "Bộ X", "Thông tư", None, None))
    db.executemany("INSERT INTO provisions VALUES (?,?,?,?,?,?,?)", [
        (CHAPTER, DOC, "Chapter", "Chương I", None, 0, f"/{CHAPTER}"),
        (ARTICLE, DOC, "Article", "Điều 1", CHAPTER, 0, f"/{CHAPTER}/{ARTICLE}"),
        (CLAUSE, DOC, "Clause", "Khoản 1", ARTICLE, 0, f"/{CHAPTER}/{ARTICLE}/{CLAUSE}"),
    ])
    db.executemany("INSERT INTO versions VALUES (?,?,?,?,?,?)", [
        (f"version:{CHAPTER.split(':')[1]}:1", CHAPTER, 1, "Chương I QUY ĐỊNH CHUNG", "2020-01-01", None),
        (f"version:{ARTICLE.split(':')[1]}:1", ARTICLE, 1, "Điều 1. Phạm vi\nthân điều", "2020-01-01", None),
        (f"version:{CLAUSE.split(':')[1]}:1", CLAUSE, 1, "1. Nội dung khoản một.", "2020-01-01", None),
    ])
    db.commit()
    db.close()
    return root


@pytest.fixture
def corpus(data: Path, tmp_path: Path) -> Corpus:
    build(data, tmp_path / "index.sqlite")
    return Corpus(tmp_path / "index.sqlite")


def test_counts_cover_both_layers(corpus: Corpus) -> None:
    counts = corpus.counts()
    assert counts["units_asis"] == 2
    assert counts["units_version"] == 1
    assert counts["instructions"] == 1
    assert counts["versions_with_local_window"] == 1


def test_local_and_propagated_windows_are_stored_apart(corpus: Corpus) -> None:
    """The distinction the main result rests on, asserted at the storage layer."""
    row = corpus.db.execute(
        "SELECT local_from, local_to FROM units WHERE layer='version'").fetchone()
    assert tuple(row) == ("2020-01-01", None), "local window must come from the version chain"
    windows = corpus.db.execute("SELECT start, end FROM prop_iv").fetchall()
    assert [tuple(w) for w in windows] == [("2020-01-01", "2022-01-01")], \
        "propagated window must come from effective_intervals"


def test_context_header_is_document_then_ancestors(corpus: Corpus) -> None:
    unit = corpus.unit(f"version:{CLAUSE.split(':')[1]}:1")
    assert unit is not None
    assert unit.context == (
        "Thông tư số 11/2020/TT-X Quy định mẫu › Chương I QUY ĐỊNH CHUNG › Điều 1. Phạm vi")
    assert "thân điều" not in unit.context, "an ancestor contributes its heading, not its body"


def test_retrieval_text_opt_in(corpus: Corpus) -> None:
    unit = corpus.unit(f"version:{CLAUSE.split(':')[1]}:1")
    assert unit.retrieval_text(False) == "1. Nội dung khoản một."
    assert unit.retrieval_text(True).endswith("1. Nội dung khoản một.")
    assert unit.retrieval_text(True).startswith("Thông tư số 11/2020/TT-X")


def test_units_keeps_the_ranking_order(corpus: Corpus) -> None:
    ids = [f"asis:{CLAUSE}", f"version:{CLAUSE.split(':')[1]}:1"]
    assert [u.unit_id for u in corpus.units(ids)] == ids
    assert [u.unit_id for u in corpus.units(ids[::-1])] == ids[::-1]
    assert corpus.units([]) == []


def test_unknown_unit_is_none_not_an_error(corpus: Corpus) -> None:
    assert corpus.unit("version:nope:9") is None


def test_build_resumes_without_duplicating(data: Path, tmp_path: Path) -> None:
    out = tmp_path / "index.sqlite"
    first = build(data, out)
    assert build(data, out) == first


def test_missing_index_says_how_to_build_it(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="index_corpus"):
        Corpus(tmp_path / "absent.sqlite")


def test_document_heading_does_not_repeat_the_number() -> None:
    assert _document_heading("23/2026/TT-BXD", "Thông tư số 23/2026/TT-BXD Quy định", "Thông tư") \
        == "Thông tư số 23/2026/TT-BXD Quy định"
    assert _document_heading("99/2020/QH14", "Luật Doanh nghiệp", "Luật") \
        == "Luật 99/2020/QH14 Luật Doanh nghiệp"
    assert _document_heading(None, "Không số", None) == "Không số"


def test_heading_is_the_first_line_only() -> None:
    assert _heading("Điều 1. Phạm vi\nthân điều dài") == "Điều 1. Phạm vi"
    assert _heading("") == ""

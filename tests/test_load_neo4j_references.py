"""D3 typed document references and explicit unresolved-target accounting."""

import hashlib
import json
import shutil

import pytest

from load_neo4j_references import (
    _query,
    _write_batch,
    plan_references,
    write_reports,
)
from legal_crawler.graph.neo4j_references import REFERENCE_RELATION_TYPES, relationship_type
from legal_crawler.storage.documents import REPO_DATA_DIR
from legal_crawler.temporal import RelationType
from legal_crawler.vocab.reference_types import ReferenceTypeMap, UnknownReferenceTypeError


def _fixture(tmp_path, edges, *, raw_ids=("1", "2")):
    raw = tmp_path / "raw"
    raw.mkdir()
    for doc_id in raw_ids:
        (raw / f"{doc_id}.json").write_text("{}", encoding="utf-8")
    shutil.copyfile(REPO_DATA_DIR / "reference_type_map.json", tmp_path / "reference_type_map.json")
    (tmp_path / "edges.jsonl").write_text(
        "".join(json.dumps(edge, ensure_ascii=False) + "\n" for edge in edges),
        encoding="utf-8",
    )
    return tmp_path


def _edge(source="1", target="2", code=1):
    info = ReferenceTypeMap.load().classify(code)
    return {
        "source_id": source,
        "target_id": target,
        "reference_type": code,
        "label_vi": info.label_vi,
        "group": info.group.value,
    }


def test_all_verified_codes_have_one_distinct_typed_relation():
    mapping = ReferenceTypeMap.load()
    assert mapping.codes == frozenset(REFERENCE_RELATION_TYPES)
    assert len(REFERENCE_RELATION_TYPES) == 13
    assert len(set(REFERENCE_RELATION_TYPES.values())) == 13
    assert relationship_type(1) is RelationType.REPEALS
    assert relationship_type(7) is RelationType.CONSOLIDATES
    assert relationship_type(14) is RelationType.INTERPRETS


def test_plan_deduplicates_triplets_and_reports_missing_targets(tmp_path):
    source = _fixture(tmp_path, [
        _edge(code=1), _edge(code=1),
        _edge(target="missing", code=3), _edge(code=4),
    ])

    plan = plan_references(source)
    report = plan.report()

    assert report["source_lines"] == 4
    assert report["distinct_edges"] == 3
    assert report["duplicate_lines"] == 1
    assert report["loaded_edges"] == 2
    assert report["unresolved_edges"] == 1
    assert report["unresolved_target_ids"] == 1
    assert report["source_sha256"] == hashlib.sha256((source / "edges.jsonl").read_bytes()).hexdigest()
    assert plan.rows_by_type[RelationType.REPEALS][0]["source_lines"] == [1, 2]
    assert plan.unresolved == [{
        "source_id": "document:1",
        "target_id": "document:missing",
        "reference_type": 3,
        "relation_type": "ISSUED_UNDER",
        "label_vi": "Căn cứ ban hành",
        "group": "open_citation",
        "source_lines": [3],
        "reason": "target_not_in_raw",
    }]
    assert report["by_type"]["ISSUED_UNDER"] == {
        "source_distinct": 1, "loaded": 0, "unresolved": 1,
    }


def test_reports_are_deterministic_and_contain_every_unresolved_edge(tmp_path):
    plan = plan_references(_fixture(tmp_path, [_edge(target="missing", code=3)]))
    report = plan.report()
    summary_path, unresolved_path = write_reports(tmp_path, plan, report)
    first = summary_path.read_bytes(), unresolved_path.read_bytes()
    write_reports(tmp_path, plan, report)
    assert first == (summary_path.read_bytes(), unresolved_path.read_bytes())
    assert json.loads(summary_path.read_text(encoding="utf-8")) == report
    assert [json.loads(line) for line in unresolved_path.read_text(encoding="utf-8").splitlines()] == plan.unresolved


def test_wrong_label_is_rejected_before_database_writes(tmp_path):
    edge = {**_edge(), "label_vi": "wrong"}
    with pytest.raises(ValueError, match="label/group disagree with verified"):
        plan_references(_fixture(tmp_path, [edge]))


def test_unknown_code_is_rejected_before_database_writes(tmp_path):
    edge = {**_edge(), "reference_type": 999}
    with pytest.raises(UnknownReferenceTypeError, match="referenceType=999"):
        plan_references(_fixture(tmp_path, [edge]))


def test_missing_source_is_error_not_unresolved_target(tmp_path):
    with pytest.raises(ValueError, match="source Document document:missing is absent"):
        plan_references(_fixture(tmp_path, [_edge(source="missing")]))


def test_query_uses_only_verified_static_relationship_types():
    assert "MERGE (source)-[r:REPEALS]->(target)" in _query(RelationType.REPEALS)
    with pytest.raises(ValueError, match="not a verified source reference type"):
        _query(RelationType.CONTAINS)


class _Result:
    def __init__(self, loaded):
        self.loaded = loaded

    def single(self):
        return {"loaded": self.loaded}


class _Transaction:
    def __init__(self, loaded):
        self.loaded = loaded

    def run(self, _query, **_params):
        return _Result(self.loaded)


def test_missing_neo4j_endpoint_rolls_back_batch():
    with pytest.raises(ValueError, match=r"D3 REPEALS: matched 0/1 edges.*Transaction rolled back"):
        _write_batch(_Transaction(0), _query(RelationType.REPEALS), [_edge()], RelationType.REPEALS)

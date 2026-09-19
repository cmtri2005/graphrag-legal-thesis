"""D2 source mapping and batch failure behavior without a running server."""

import json

import pytest

from load_neo4j import _batches, _version_rows, _write_batch, read_event_nodes
from legal_crawler.temporal import make_version_id


def _line(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")


def _event(event_id="event:one", *, reason=None):
    return {
        "id": event_id,
        "actor_id": "document:actor",
        "target_document_id": "document:target",
        "target_provision_id": "provision:article",
        "operation": "amend",
        "effective_on": "2025-01-01",
        "status": "auto_accepted",
        "status_reason": reason,
        "evidence": "Sửa đổi Điều 1.",
    }


def _audit(line, event_id="event:one", *, applied=True):
    return {
        "input_line": line,
        "event_id": event_id,
        "outcome": "applied" if applied else "rejected",
        "reason": None if applied else "not_applicable",
    }


def test_event_id_is_deduplicated_but_each_source_and_audit_line_is_preserved(tmp_path):
    _line(tmp_path / "derived/provision_events.jsonl", [
        _event(reason="first"), _event(reason="second")
    ])
    # Audit order need not match input order; input_line is authoritative.
    _line(tmp_path / "derived/event_log.jsonl", [_audit(2), _audit(1)])

    nodes = read_event_nodes(tmp_path)

    assert list(nodes) == ["event:one"]
    props = nodes["event:one"]["props"]
    assert props["input_lines"] == [1, 2]
    assert props["applied"] is True
    entries = json.loads(props["source_and_audit_json"])
    assert [item["source"]["status_reason"] for item in entries] == ["first", "second"]
    assert [item["audit"]["input_line"] for item in entries] == [1, 2]


def test_event_audit_mismatch_is_rejected_before_loading(tmp_path):
    _line(tmp_path / "derived/provision_events.jsonl", [_event()])
    _line(tmp_path / "derived/event_log.jsonl", [_audit(1, "event:wrong")])
    with pytest.raises(ValueError, match="different event_id"):
        read_event_nodes(tmp_path)


def test_same_event_id_with_conflicting_core_fields_is_rejected(tmp_path):
    other = {**_event(), "target_document_id": "document:other"}
    _line(tmp_path / "derived/provision_events.jsonl", [_event(), other])
    _line(tmp_path / "derived/event_log.jsonl", [_audit(1), _audit(2)])
    with pytest.raises(ValueError, match="conflicting core fields"):
        read_event_nodes(tmp_path)


def test_version_maps_local_and_effective_bounds_and_both_event_roles(tmp_path):
    provision_id = "provision:article"
    version_id = make_version_id(provision_id, 2)
    path = tmp_path / "versions.jsonl"
    _line(path, [{
        "id": version_id,
        "provision_id": provision_id,
        "ordinal": 2,
        "text": "Nội dung mới.",
        "valid_from": "2025-01-01",
        "valid_to": "2026-01-01",
        "effective_interval_count": 1,
        "effective_intervals": [{"start": "2025-01-01", "end": "2026-01-01"}],
        "effective_from": "2025-01-01",
        "effective_to": "2026-01-01",
        "created_by_event_id": "event:create",
        "ended_by_event_id": "event:end",
        "provenance": [],
    }])
    causal_edges = []

    rows = list(_version_rows(path, {"event:create", "event:end"}, causal_edges))

    assert len(rows) == 1
    assert rows[0]["id"] == version_id
    assert rows[0]["provision_id"] == provision_id
    assert rows[0]["props"]["valid_to"] == "2026-01-01"
    assert json.loads(rows[0]["props"]["effective_intervals_json"]) == [
        {"start": "2025-01-01", "end": "2026-01-01"}
    ]
    assert causal_edges == [
        {"version_id": version_id, "event_id": "event:create", "role": "created"},
        {"version_id": version_id, "event_id": "event:end", "role": "ended"},
    ]


def test_missing_causal_event_is_rejected(tmp_path):
    provision_id = "provision:article"
    path = tmp_path / "versions.jsonl"
    _line(path, [{
        "id": make_version_id(provision_id, 1), "provision_id": provision_id,
        "ordinal": 1, "text": "A", "effective_interval_count": 0,
        "effective_intervals": [], "created_by_event_id": "event:missing",
    }])
    with pytest.raises(ValueError, match="has no source event"):
        list(_version_rows(path, set(), []))


def test_batch_respects_text_budget_and_count():
    rows = [{"props": {"text": "é" * 3}}, {"props": {"text": "a" * 3}},
            {"props": {"text": "b" * 3}}]
    assert [len(batch) for batch in _batches(rows, 3, max_text_bytes=8)] == [1, 2]
    assert [len(batch) for batch in _batches(rows, 2)] == [2, 1]


class _Result:
    def __init__(self, count):
        self.count = count

    def single(self):
        return {"loaded": self.count}


class _Transaction:
    def __init__(self, count):
        self.count = count

    def run(self, _query, **_parameters):
        return _Result(self.count)


def test_missing_graph_endpoint_fails_batch_with_actionable_error():
    rows = [{"id": "provision:a"}, {"id": "provision:b"}]
    with pytest.raises(ValueError, match=r"D2 version_of: matched 1/2 rows.*Transaction rolled back"):
        _write_batch(_Transaction(1), "Cypher", rows, "version_of")

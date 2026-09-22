"""D5 graph read-model contract: positive and negative temporal cases."""
from datetime import date

import pytest

from legal_crawler.graph.neo4j_snapshot import (
    GraphSnapshotError, SNAPSHOT_CYPHER, graph_snapshot, snapshot_from_record,
)


AT = date(2025, 1, 1)


def version(version_id, intervals, text="legal text"):
    import json

    return {"id": version_id, "text": text,
            "effective_interval_count": len(intervals),
            "effective_intervals_json": json.dumps(intervals)}


def record(*versions):
    return {"provision_id": "provision:p", "versions": list(versions)}


def test_selects_half_open_interval_and_exact_version_text():
    first = version("version:p:1", [{"start": "2020-01-01", "end": "2025-01-01"}], "old")
    second = version("version:p:2", [{"start": "2025-01-01", "end": None}], "new")
    result = snapshot_from_record("provision:p", AT, record(second))
    assert (result.valid, result.version_id, result.text) == (True, "version:p:2", "new")
    before = snapshot_from_record("provision:p", date(2024, 12, 31), record(first))
    assert before.version_id == "version:p:1"


def test_zero_and_disjoint_effective_windows_never_invent_validity():
    no_window = version("version:p:1", [])
    windows = version("version:p:2", [
        {"start": "2020-01-01", "end": "2021-01-01"},
        {"start": "2025-01-01", "end": "2026-01-01"},
    ])
    assert snapshot_from_record("provision:p", date(2023, 1, 1), record()).text is None
    assert snapshot_from_record("provision:p", AT, record(windows)).version_id == "version:p:2"
    with pytest.raises(GraphSnapshotError, match="outside its effective intervals"):
        snapshot_from_record("provision:p", AT, record(no_window))


def test_unknown_provision_is_distinct_from_existing_inactive_provision():
    missing = snapshot_from_record("provision:p", AT, {"provision_id": None, "versions": []})
    inactive = snapshot_from_record("provision:p", AT, record())
    assert (missing.provision_exists, missing.valid) == (False, False)
    assert (inactive.provision_exists, inactive.valid) == (True, False)


@pytest.mark.parametrize("versions", [
    [version("version:p:1", [{"start": "2020-01-01", "end": None}]),
     version("version:p:2", [{"start": "2024-01-01", "end": None}])],
    [version("version:p:1", [{"start": "2020-01-01", "end": None}]),
     version("version:p:1", [{"start": "2020-01-01", "end": None}])],
    [{"id": "version:p:1", "text": "x", "effective_interval_count": 2,
      "effective_intervals_json": '[{"start":"2020-01-01","end":null}]'}],
    [version("version:p:1", [{"start": "2025-01-01", "end": "2025-01-01"}])],
])
def test_corrupt_or_ambiguous_graph_is_rejected(versions):
    with pytest.raises(GraphSnapshotError):
        snapshot_from_record("provision:p", AT, record(*versions))


def test_query_uses_only_derived_graph_and_binds_id():
    class Result:
        def single(self, *, strict):
            assert strict
            return record(version("version:p:1", [{"start": "2020-01-01", "end": None}]))

    class Session:
        def run(self, query, **parameters):
            assert query == SNAPSHOT_CYPHER
            assert "VERSION_OF" in query
            assert "apoc.convert.fromJsonList" in query
            assert parameters == {"provision_id": "provision:p", "at": "2025-01-01"}
            return Result()

    assert graph_snapshot(Session(), "provision:p", AT).valid

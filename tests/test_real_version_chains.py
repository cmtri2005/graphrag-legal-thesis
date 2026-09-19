"""C6 regression against the frozen snapshot v2, not synthetic fixtures.

The ordinary suite skips these tests when a clone has no downloaded corpus.
When ``data/raw`` exists, missing or changed derived inputs are failures.
"""
from __future__ import annotations

import hashlib
import json
from datetime import date, timedelta
from pathlib import Path

import pytest

from build_versions import build_version_files
from legal_crawler.index import TemporalIndex
from legal_crawler.temporal import (
    EventStatus,
    InvalidityReason,
    LegalEvent,
    LegalOperation,
    ProvisionLevel,
    ProvisionVersion,
    SnapshotService,
    TemporalInterval,
    TemporalState,
    ValidityService,
)


DATA = Path(__file__).resolve().parents[1] / "data"
CHAIN_DOCUMENT = "document:105518"  # 03/2014/TT-NHNN
CHAIN_PROVISION = "provision:6834edc0-df42-11f0-a8db-4162e9af2290%23k2"
CHAIN_EVENTS = (
    "event:document%3A122819:adbe8577ccdca0621bed67cc",
    "event:document%3A138969:480edd1803e0091360508085",
)
CHAIN_TEXT_SHA256 = (
    "fa484e9a88590f832de4ddc9c9ce8fcbd7e2350b770a6cfdd75771ead502278e",
    "86256c460569e3030bbf0eca5adcdf6b03702feaaed6526eed156e87778180c7",
    "277cc84c113c4db9f54421205a8a7ee64ac9c375cf57083309b724bdb6af4d37",
)
REPEAL_DOCUMENT = "document:178250"  # 144/2025/NĐ-CP
REPEALED_ARTICLE = "provision:02e81570-2c0c-11f1-be02-ef7b71d803d4"
REPEAL_EVENT = (
    "event:document%3A012c2440-6e5d-11f1-be32-359c7a7c0807:"
    "a0de3a1133f8bd081ecdc77f"
)
REPEAL_DATE = date(2026, 7, 1)
DOCUMENT_IDS = (CHAIN_DOCUMENT, REPEAL_DOCUMENT)
EVENT_IDS = frozenset((*CHAIN_EVENTS, REPEAL_EVENT))


def _jsonl(path: Path):
    with path.open(encoding="utf-8") as stream:
        for line in stream:
            if line.strip():
                yield json.loads(line)


def _version_from_row(row: dict) -> ProvisionVersion:
    start = row["valid_from"]
    assert start is not None, f"dated C6 document has undated version: {row['id']}"
    return ProvisionVersion(
        id=row["id"],
        provision_id=row["provision_id"],
        ordinal=row["ordinal"],
        text=row["text"],
        validity=TemporalInterval(
            date.fromisoformat(start),
            date.fromisoformat(row["valid_to"]) if row["valid_to"] else None,
        ),
        created_by_event_id=row["created_by_event_id"],
        ended_by_event_id=row["ended_by_event_id"],
    )


@pytest.fixture(scope="module")
def real_cases(tmp_path_factory):
    if not (DATA / "raw").is_dir():
        pytest.skip("snapshot v2 not downloaded; C6 requires data/raw")
    required = (
        DATA / "temporal.sqlite",
        DATA / "derived" / "versions.jsonl",
        DATA / "derived" / "event_log.jsonl",
        DATA / "derived" / "provision_events.jsonl",
    )
    for path in required:
        assert path.is_file(), f"snapshot v2 is incomplete: {path}"

    documents = {}
    provisions = {}
    with TemporalIndex(DATA / "temporal.sqlite") as index:
        for document_id in DOCUMENT_IDS:
            document = index.document(document_id)
            assert document is not None, f"missing frozen document: {document_id}"
            documents[document_id] = document
            provisions[document_id] = index.document_order(document_id)
        descendants = index.descendants_of(REPEALED_ARTICLE)

    provision_to_document = {
        item.id: document_id
        for document_id, items in provisions.items()
        for item in items
    }
    rows = {document_id: [] for document_id in DOCUMENT_IDS}
    marker = '"provision_id":"'
    with (DATA / "derived" / "versions.jsonl").open(encoding="utf-8") as stream:
        for line in stream:
            # The builder writes id and provision_id before the (often long)
            # text. Avoid JSON-decoding all 1.6M unrelated versions; fall back
            # to a full decode if a future writer changes JSON spacing/order.
            start = line.find(marker)
            if start < 0:
                provision_id = json.loads(line)["provision_id"]
            else:
                start += len(marker)
                provision_id = line[start:line.index('"', start)]
            document_id = provision_to_document.get(provision_id)
            if document_id is not None:
                rows[document_id].append(json.loads(line))

    # Rebuild the two pinned documents from raw snapshot + accepted events,
    # twice. Check both determinism and equality with the full-corpus artifact.
    output = tmp_path_factory.mktemp("real-version-chains")
    versions_path = output / "versions.jsonl"
    event_log_path = output / "event_log.jsonl"
    first = build_version_files(
        DATA, DATA / "temporal.sqlite", versions_path, event_log_path,
        target_document_ids=DOCUMENT_IDS,
    )
    second = build_version_files(
        DATA, DATA / "temporal.sqlite", versions_path, event_log_path,
        target_document_ids=DOCUMENT_IDS,
    )
    assert first["versions_sha256"] == second["versions_sha256"]
    assert first["event_log_sha256"] == second["event_log_sha256"]
    assert list(_jsonl(versions_path)) == [
        row for document_id in DOCUMENT_IDS for row in rows[document_id]
    ], "selected rebuild differs from full-corpus versions.jsonl"

    source_events = {
        row["id"]: row
        for row in _jsonl(DATA / "derived" / "provision_events.jsonl")
        if row["id"] in EVENT_IDS
    }
    outcomes = {
        row["event_id"]: row
        for row in _jsonl(DATA / "derived" / "event_log.jsonl")
        if row["event_id"] in EVENT_IDS
    }
    assert set(source_events) == EVENT_IDS
    assert set(outcomes) == EVENT_IDS

    states = {}
    for document_id in DOCUMENT_IDS:
        state = TemporalState()
        state.add_document(documents[document_id])
        for provision in provisions[document_id]:
            state.add_provision(provision)
        for row in rows[document_id]:
            state.add_version(_version_from_row(row))
        states[document_id] = state

    repeal = source_events[REPEAL_EVENT]
    states[REPEAL_DOCUMENT].record_applied_event(
        LegalEvent(
            id=REPEAL_EVENT,
            operation=LegalOperation.REPEAL,
            source_document_id=repeal["actor_id"],
            target_document_id=repeal["target_document_id"],
            effective_on=REPEAL_DATE,
            target_provision_ids=(REPEALED_ARTICLE,),
            status=EventStatus(repeal["status"]),
        )
    )
    return documents, descendants, rows, states, source_events, outcomes


def test_real_three_version_chain_crosses_both_amendment_boundaries(real_cases):
    documents, _, rows, states, sources, outcomes = real_cases
    assert documents[CHAIN_DOCUMENT].number == "03/2014/TT-NHNN"
    versions = sorted(
        (row for row in rows[CHAIN_DOCUMENT] if row["provision_id"] == CHAIN_PROVISION),
        key=lambda row: row["ordinal"],
    )
    assert [row["ordinal"] for row in versions] == [1, 2, 3]
    assert [row["valid_from"] for row in versions] == [
        "2014-03-15", "2017-09-01", "2020-01-01",
    ]
    assert [row["valid_to"] for row in versions] == [
        "2017-09-01", "2020-01-01", None,
    ]
    assert [row["effective_intervals"] for row in versions] == [
        [{"start": row["valid_from"], "end": row["valid_to"]}]
        for row in versions
    ]
    assert [hashlib.sha256(row["text"].encode()).hexdigest() for row in versions] == (
        list(CHAIN_TEXT_SHA256)
    )
    for older, newer, event_id in zip(versions, versions[1:], CHAIN_EVENTS):
        assert older["ended_by_event_id"] == newer["created_by_event_id"] == event_id
        assert outcomes[event_id]["outcome"] == "applied"
        assert outcomes[event_id]["input_status"] == sources[event_id]["status"] == (
            "auto_accepted"
        )
        assert outcomes[event_id]["operation"] == sources[event_id]["operation"] == "amend"
        assert outcomes[event_id]["created_version_ids"] == [newer["id"]]
        assert outcomes[event_id]["closed_version_ids"] == [older["id"]]
        assert sources[event_id]["target_provision_id"] == CHAIN_PROVISION
        assert any(
            update["target_provision_id"] == CHAIN_PROVISION
            and update["new_text"] == newer["text"]
            for update in sources[event_id]["text_updates"]
        )

    service = ValidityService(states[CHAIN_DOCUMENT])
    snapshots = SnapshotService(states[CHAIN_DOCUMENT])
    for query, ordinal in (
        ("2017-08-31", 1), ("2017-09-01", 2),
        ("2019-12-31", 2), ("2020-01-01", 3),
    ):
        at = date.fromisoformat(query)
        result = service.check(CHAIN_PROVISION, at)
        snapshot = snapshots.snapshot(CHAIN_PROVISION, at)
        assert result.valid and result.version.ordinal == ordinal
        assert snapshot.text == versions[ordinal - 1]["text"]
        assert any(
            date.fromisoformat(window["start"]) <= at
            and (window["end"] is None or at < date.fromisoformat(window["end"]))
            for window in versions[ordinal - 1]["effective_intervals"]
        )
    assert not service.is_valid(CHAIN_PROVISION, date(2014, 3, 14))


def test_real_article_repeal_invalidates_every_descendant(real_cases):
    documents, descendants, rows, states, sources, outcomes = real_cases
    assert documents[REPEAL_DOCUMENT].number == "144/2025/NĐ-CP"
    assert documents[REPEAL_DOCUMENT].effective_to > REPEAL_DATE
    assert len(descendants) == 5
    assert {item.level for item in descendants} == {
        ProvisionLevel.CLAUSE, ProvisionLevel.POINT,
    }
    event = sources[REPEAL_EVENT]
    assert event["operation"] == "repeal"
    assert event["target_provision_id"] == REPEALED_ARTICLE
    assert event["effective_on"] == REPEAL_DATE.isoformat()
    assert outcomes[REPEAL_EVENT]["outcome"] == "applied"
    assert outcomes[REPEAL_EVENT]["input_status"] == event["status"] == "auto_accepted"

    descendant_ids = {item.id for item in descendants}
    expected_ids = {REPEALED_ARTICLE, *descendant_ids}
    selected_rows = [
        row for row in rows[REPEAL_DOCUMENT] if row["provision_id"] in expected_ids
    ]
    assert len(selected_rows) == len(expected_ids)
    by_provision = {
        row["provision_id"]: row for row in selected_rows
    }
    assert set(by_provision) == expected_ids
    article = by_provision[REPEALED_ARTICLE]
    assert article["ended_by_event_id"] == REPEAL_EVENT
    assert article["valid_to"] == REPEAL_DATE.isoformat()
    assert outcomes[REPEAL_EVENT]["closed_version_ids"] == [article["id"]]

    state = states[REPEAL_DOCUMENT]
    service = ValidityService(state)
    snapshots = SnapshotService(state)
    assert service.is_valid(REPEALED_ARTICLE, REPEAL_DATE - timedelta(days=1))
    article_result = service.check(REPEALED_ARTICLE, REPEAL_DATE)
    assert article_result.reason is InvalidityReason.PROVISION_REPEALED
    assert article_result.caused_by_event_id == REPEAL_EVENT
    for child in descendants:
        row = by_provision[child.id]
        assert row["valid_to"] is None, f"{child.id} is locally closed"
        assert row["effective_intervals"] == [
            {"start": documents[REPEAL_DOCUMENT].effective_from.isoformat(),
             "end": REPEAL_DATE.isoformat()}
        ]
        assert service.is_valid(child.id, REPEAL_DATE - timedelta(days=1))
        result = service.check(child.id, REPEAL_DATE)
        assert not result.valid
        assert result.reason is InvalidityReason.PARENT_INVALID
        assert result.invalid_ancestor_id == REPEALED_ARTICLE
        assert result.caused_by_event_id == REPEAL_EVENT
        snapshot = snapshots.snapshot(child.id, REPEAL_DATE)
        assert snapshot.text is None
        assert snapshot.caused_by_event is not None
        assert snapshot.caused_by_event.id == REPEAL_EVENT

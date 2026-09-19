#!/usr/bin/env python3
"""D5: compare 200 Neo4j read-model snapshots with offline SnapshotService.

This is consistency testing, not the 100 manually judged legal answers in E2.
The sampled documents must already have structured provisions. D4 is separate.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import sqlite3
from collections import Counter
from datetime import date, timedelta
from pathlib import Path

from legal_crawler.graph.neo4j_snapshot import graph_snapshot
from legal_crawler.index import TemporalIndex
from legal_crawler.temporal import (
    EventStatus, LegalEvent, LegalOperation, ProvisionVersion, SnapshotService,
    TemporalInterval, TemporalState,
)


PINNED_DOCUMENTS = ("document:105518", "document:178250")
PINNED_PROVISIONS = (
    "provision:6834edc0-df42-11f0-a8db-4162e9af2290%23k2",
    "provision:02e81570-2c0c-11f1-be02-ef7b71d803d4",
)


def choose_documents(index_path: Path, seed: int, count: int) -> tuple[str, ...]:
    """Choose a reproducible spread of moderately sized, dated documents."""
    with sqlite3.connect(f"file:{index_path}?mode=ro", uri=True) as db:
        rows = db.execute(
            "SELECT p.document_id FROM provisions p "
            "JOIN documents d ON d.id = p.document_id "
            "WHERE d.effective_from IS NOT NULL "
            "GROUP BY p.document_id HAVING count(*) BETWEEN 10 AND 300 "
            "ORDER BY p.document_id"
        ).fetchall()
    eligible = [row[0] for row in rows if row[0] not in PINNED_DOCUMENTS]
    if len(eligible) < count:
        raise ValueError(f"only {len(eligible)} eligible documents; need {count}")
    return (*PINNED_DOCUMENTS, *random.Random(seed).sample(eligible, count))


def _parents_first(provisions):
    by_id = {item.id: item for item in provisions}
    remaining = set(by_id)
    while remaining:
        ready = sorted(
            (by_id[item_id] for item_id in remaining
             if by_id[item_id].parent_id not in remaining),
            key=lambda item: item.id,
        )
        if not ready:
            raise ValueError("cycle in indexed provision structure")
        for item in ready:
            yield item
            remaining.remove(item.id)


def _version(row: dict) -> ProvisionVersion:
    start = row["valid_from"]
    if start is None:
        raise ValueError("undated versions cannot enter TemporalState")
    return ProvisionVersion(
        id=row["id"], provision_id=row["provision_id"],
        ordinal=row["ordinal"], text=row["text"],
        validity=TemporalInterval(
            date.fromisoformat(start),
            date.fromisoformat(row["valid_to"]) if row["valid_to"] else None,
        ),
        created_by_event_id=row["created_by_event_id"],
        ended_by_event_id=row["ended_by_event_id"],
    )


def load_states(data_dir: Path, document_ids: tuple[str, ...]) -> dict[str, TemporalState]:
    """Read full derived version chains for selected docs in one artifact pass."""
    states: dict[str, TemporalState] = {}
    provision_to_document: dict[str, str] = {}
    with TemporalIndex(data_dir / "temporal.sqlite") as index:
        for document_id in document_ids:
            document = index.document(document_id)
            if document is None:
                raise ValueError(f"selected document is missing: {document_id}")
            state = TemporalState()
            state.add_document(document)
            for provision in _parents_first(index.document_order(document_id)):
                state.add_provision(provision)
                provision_to_document[provision.id] = document_id
            states[document_id] = state

    marker = '"provision_id":"'
    with (data_dir / "derived/versions.jsonl").open(encoding="utf-8") as stream:
        for line in stream:
            start = line.find(marker)
            if start >= 0:
                start += len(marker)
                provision_id = line[start:line.index('"', start)]
            else:
                provision_id = json.loads(line)["provision_id"]
            document_id = provision_to_document.get(provision_id)
            if document_id is None:
                continue
            row = json.loads(line)
            if row["valid_from"] is not None:
                states[document_id].add_version(_version(row))

    # ValidityService needs the authoritative source operation for an ended
    # version to distinguish repeal from a generic inactive gap. This does not
    # replay events or derive dates again; it only restores event identity.
    event_to_documents: dict[str, set[str]] = {}
    for document_id, state in states.items():
        for version in state.versions:
            for event_id in (version.created_by_event_id, version.ended_by_event_id):
                if event_id:
                    event_to_documents.setdefault(event_id, set()).add(document_id)
    pending = set(event_to_documents)
    with (data_dir / "derived/provision_events.jsonl").open(encoding="utf-8") as stream:
        for line in stream:
            row = json.loads(line)
            event_id = row["id"]
            if event_id not in pending:
                continue
            targets = tuple(dict.fromkeys(
                item for item in (
                    row.get("target_provision_id"),
                    *(update["target_provision_id"] for update in row.get("text_updates", ())),
                    *(insertion["provision_id"] for insertion in row.get("insertions", ())),
                ) if item
            ))
            event = LegalEvent(
                id=event_id, operation=LegalOperation(row["operation"]),
                source_document_id=row["actor_id"],
                target_document_id=row["target_document_id"],
                effective_on=date.fromisoformat(row["effective_on"]),
                target_provision_ids=targets, status=EventStatus(row["status"]),
            )
            for document_id in event_to_documents[event_id]:
                states[document_id].record_applied_event(event)
            pending.remove(event_id)
            if not pending:
                break
    if pending:
        raise ValueError(f"{len(pending)} version events absent from source event file")
    return states


def make_cases(states: dict[str, TemporalState], seed: int, count: int):
    rng = random.Random(seed)
    buckets: dict[str, list[tuple[str, date, str]]] = {
        key: [] for key in ("boundary", "parent_invalid", "document_bound", "inactive", "valid")
    }
    seen: set[tuple[str, date]] = set()
    mandatory_keys: set[tuple[str, date]] = set()

    def add(state: TemporalState, provision_id: str, at: date, boundary: bool = False):
        key = (provision_id, at)
        if key in seen:
            return
        seen.add(key)
        snapshot = SnapshotService(state).snapshot(provision_id, at)
        reason = snapshot.validity.reason.value if snapshot.validity.reason else None
        category = (
            "boundary" if boundary else
            "parent_invalid" if reason == "parent_invalid" else
            "document_bound" if reason in {"document_not_yet_effective", "document_expired"} else
            "valid" if snapshot.validity.valid else "inactive"
        )
        buckets[category].append((provision_id, at, category))

    for document_id, state in states.items():
        document = state.document(document_id)
        provisions = list(state.provisions)
        selected = rng.sample(provisions, min(30, len(provisions)))
        selected.extend(item for item in provisions if item.id in PINNED_PROVISIONS)
        if document_id == "document:178250":
            children = state.descendants_of(PINNED_PROVISIONS[1])
            selected.extend(children[:3])
            for provision in (next(item for item in provisions if item.id == PINNED_PROVISIONS[1]),
                              *children[:1]):
                for at in (date(2026, 6, 30), date(2026, 7, 1)):
                    add(state, provision.id, at, boundary=True)
                    mandatory_keys.add((provision.id, at))
        for provision in selected:
            chain = state.chain(provision.id)
            if document.effective_from:
                add(state, provision.id, document.effective_from - timedelta(days=1))
                add(state, provision.id, document.effective_from, boundary=True)
            if document.effective_to:
                add(state, provision.id, document.effective_to - timedelta(days=1))
                add(state, provision.id, document.effective_to, boundary=True)
            for version in chain.versions if chain else ():
                start = version.validity.start
                add(state, provision.id, start - timedelta(days=1))
                add(state, provision.id, start, boundary=True)
                if provision.id == PINNED_PROVISIONS[0]:
                    mandatory_keys.add((provision.id, start))
                if version.validity.end:
                    end = version.validity.end
                    add(state, provision.id, end - timedelta(days=1))
                    add(state, provision.id, end, boundary=True)
            add(state, provision.id, date(2026, 9, 19))

    quotas = {"boundary": 50, "parent_invalid": 25, "document_bound": 40,
              "inactive": 25, "valid": 60}
    mandatory = [case for bucket in buckets.values() for case in bucket
                 if (case[0], case[1]) in mandatory_keys]
    if len(mandatory) != len(mandatory_keys):
        raise ValueError("a pinned A→B→C or parent-repeal boundary is missing")
    if len(mandatory) > count:
        raise ValueError(f"{len(mandatory)} pinned cases exceed requested sample count {count}")
    cases: list[tuple[str, date, str]] = list(mandatory)
    mandatory_categories = Counter(case[2] for case in mandatory)
    for category, quota in quotas.items():
        rng.shuffle(buckets[category])
        available = [case for case in buckets[category]
                     if (case[0], case[1]) not in mandatory_keys]
        take = min(max(0, quota - mandatory_categories[category]), count - len(cases))
        cases.extend(available[:take])
        buckets[category] = available[take:]
    if len(cases) < count:
        remainder = [case for bucket in buckets.values() for case in bucket]
        rng.shuffle(remainder)
        cases.extend(remainder[:count - len(cases)])
    if len(cases) < count:
        raise ValueError(f"only {len(cases)} distinct sample pairs; need {count}")
    rng.shuffle(cases)
    return cases[:count]


def compare(data_dir: Path, uri: str, user: str, password: str, seed: int,
            documents: int, count: int) -> dict:
    from neo4j import GraphDatabase

    document_ids = choose_documents(data_dir / "temporal.sqlite", seed, documents)
    states = load_states(data_dir, document_ids)
    cases = make_cases(states, seed, count)
    by_provision = {item.id: state for state in states.values() for item in state.provisions}
    rows = []
    with GraphDatabase.driver(uri, auth=(user, password)) as driver:
        driver.verify_connectivity()
        with driver.session() as session:
            for provision_id, at, category in cases:
                offline = SnapshotService(by_provision[provision_id]).snapshot(provision_id, at)
                graph = graph_snapshot(session, provision_id, at)
                expected_version = offline.version.id if offline.version else None
                expected_text = offline.text
                match = (
                    graph.provision_exists and graph.valid == offline.validity.valid
                    and graph.version_id == expected_version and graph.text == expected_text
                )
                rows.append({
                    "provision_id": provision_id, "at": at.isoformat(), "category": category,
                    "match": match,
                    "offline": {"valid": offline.validity.valid, "version_id": expected_version,
                                "text_sha256": hashlib.sha256(expected_text.encode()).hexdigest()
                                if expected_text else None,
                                "reason": offline.validity.reason.value if offline.validity.reason else None},
                    "neo4j": {"valid": graph.valid, "version_id": graph.version_id,
                              "text_sha256": hashlib.sha256(graph.text.encode()).hexdigest()
                              if graph.text else None},
                })
    return {
        "check": "D5 Neo4j derived snapshot vs offline SnapshotService",
        "seed": seed, "document_count": len(document_ids), "sample_count": len(rows),
        "matched": sum(row["match"] for row in rows),
        "categories": dict(Counter(row["category"] for row in rows)),
        "documents": list(document_ids), "cases": rows,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=Path("data"))
    parser.add_argument("--uri", default=os.environ.get("NEO4J_URI", "bolt://127.0.0.1:7687"))
    parser.add_argument("--user", default=os.environ.get("NEO4J_USER", "neo4j"))
    parser.add_argument("--seed", type=int, default=20260919)
    parser.add_argument("--documents", type=int, default=30)
    parser.add_argument("--count", type=int, default=200)
    parser.add_argument("--report", type=Path,
                        default=Path("data/derived/neo4j_snapshot_parity_report.json"))
    args = parser.parse_args()
    password = os.environ.get("NEO4J_PASSWORD")
    if not password:
        parser.error("set NEO4J_PASSWORD; credentials are never stored in the report")
    report = compare(args.data, args.uri, args.user, password,
                     args.seed, args.documents, args.count)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n",
                           encoding="utf-8")
    print(f"D5: {report['matched']}/{report['sample_count']} snapshots match; "
          f"categories={report['categories']}; report={args.report}")
    for row in report["cases"]:
        if not row["match"]:
            print(f"MISMATCH {row['provision_id']} {row['at']}: "
                  f"offline={row['offline']} neo4j={row['neo4j']}")
    return 0 if report["matched"] == report["sample_count"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

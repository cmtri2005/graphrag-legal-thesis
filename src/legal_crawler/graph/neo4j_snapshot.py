"""Read a point-in-time provision snapshot from the derived Neo4j graph.

The offline pipeline owns legal validity. Each ``ProvisionVersion`` already
stores its effective intervals after intersection with the document and every
ancestor. This reader deliberately does not reimplement ``ValidityService``
in Cypher: it selects from those materialized intervals and can be checked
against the offline ``SnapshotService`` for loader/read-model parity.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date
from typing import Any


SNAPSHOT_CYPHER = """
OPTIONAL MATCH (p:Provision {id: $provision_id})
RETURN p.id AS provision_id,
       [(p)<-[:VERSION_OF]-(v:ProvisionVersion)
        WHERE any(window IN apoc.convert.fromJsonList(v.effective_intervals_json)
                  WHERE window.start <= $at
                    AND (window.end IS NULL OR $at < window.end)) |
        v {.id, .text, .effective_interval_count,
           .effective_intervals_json}] AS versions
"""


class GraphSnapshotError(ValueError):
    """The loaded graph violates the D2 snapshot read-model contract."""


@dataclass(frozen=True, slots=True)
class GraphSnapshot:
    provision_id: str
    at: date
    provision_exists: bool
    version_id: str | None
    text: str | None

    @property
    def valid(self) -> bool:
        return self.version_id is not None


def _contains(interval: dict[str, Any], at: date) -> bool:
    if not isinstance(interval, dict):
        raise GraphSnapshotError("effective interval must be an object")
    start, end = interval.get("start"), interval.get("end")
    if not isinstance(start, str) or not start:
        raise GraphSnapshotError("effective interval has no start")
    try:
        start_date = date.fromisoformat(start)
        end_date = date.fromisoformat(end) if end is not None else None
    except (TypeError, ValueError) as exc:
        raise GraphSnapshotError("effective interval has an invalid date") from exc
    if end_date is not None and end_date <= start_date:
        raise GraphSnapshotError("effective interval is not half-open and ordered")
    return start_date <= at and (end_date is None or at < end_date)


def snapshot_from_record(provision_id: str, at: date, record: Any) -> GraphSnapshot:
    """Decode one Cypher result; reject corrupt/ambiguous loaded versions."""
    if record is None:
        raise GraphSnapshotError("snapshot query returned no row")
    graph_id = record["provision_id"]
    if graph_id is None:
        return GraphSnapshot(provision_id, at, False, None, None)
    if graph_id != provision_id:
        raise GraphSnapshotError("snapshot query returned a different provision")
    versions = record["versions"]
    if not isinstance(versions, list):
        raise GraphSnapshotError("snapshot query did not return a version list")
    selected: dict[str, Any] | None = None
    seen_ids: set[str] = set()
    for version in versions:
        if not isinstance(version, dict) or not isinstance(version.get("id"), str):
            raise GraphSnapshotError("version has no stable ID")
        if version["id"] in seen_ids:
            raise GraphSnapshotError(f"duplicate graph version {version['id']}")
        seen_ids.add(version["id"])
        if not isinstance(version.get("text"), str) or not version["text"]:
            raise GraphSnapshotError(f"version {version['id']} has no text")
        try:
            intervals = json.loads(version["effective_intervals_json"])
        except (TypeError, ValueError) as exc:
            raise GraphSnapshotError(f"version {version['id']} has invalid intervals JSON") from exc
        if not isinstance(intervals, list) or version["effective_interval_count"] != len(intervals):
            raise GraphSnapshotError(f"version {version['id']} has inconsistent interval count")
        matches = sum(_contains(interval, at) for interval in intervals)
        if matches > 1:
            raise GraphSnapshotError(f"version {version['id']} has overlapping effective intervals")
        if not matches:
            raise GraphSnapshotError(
                f"Cypher returned version {version['id']} outside its effective intervals"
            )
        if selected is not None:
            raise GraphSnapshotError("multiple versions effective at the same date")
        selected = version
    return GraphSnapshot(
        provision_id, at, True,
        selected["id"] if selected else None,
        selected["text"] if selected else None,
    )


def graph_snapshot(session: Any, provision_id: str, at: date) -> GraphSnapshot:
    """Filter D2's precomputed windows in Cypher (APOC JSON), then validate."""
    record = session.run(
        SNAPSHOT_CYPHER, provision_id=provision_id, at=at.isoformat(),
    ).single(strict=True)
    return snapshot_from_record(provision_id, at, record)

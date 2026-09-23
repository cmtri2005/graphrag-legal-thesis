#!/usr/bin/env python3
"""Build deterministic provision-version chains from snapshot v2 and L2 events.

The SQLite index is an offline read model, not the owner of temporal history.
This command rebuilds that history from the snapshot plus
``data/derived/provision_events.jsonl`` and writes two disposable artifacts:

* ``versions.jsonl`` contains every initial textual version, including text
  split by subtree backfill, followed by versions created by accepted events;
* ``event_log.jsonl`` records an outcome for every event considered.  An event
  is never silently reordered, repaired or discarded.

Initial versions are deliberately open-ended. Document and ancestor bounds are
precomputed into separate effective intervals and remain independently checked
by ``ValidityService``; closing a local chain at the document's ``effective_to``
would prevent later historical events from being materialized.

A node we hold no text for is transparent to propagation, exactly as in
``ValidityService``: Chương and Mục are headings that carry no words of their
own, and an Điều the corpus lacks text for is missing data, not data to the
contrary (master plan §11).

Rejected events also go to the review queue (C3, decision Q2), which is *not*
disposable:

  data/review/provision_events.jsonl   one row per rejected event, with the
                                       text and the instruction sentence a
                                       reviewer needs to judge it

That file is reviewed by an LLM first and double-checked by a human, so this
script owns only the rows it wrote itself (``method: auto_rejected``). A row
another process decided (``llm_reviewed``, ``human_reviewed``) is read back
untouched and never recomputed: a verdict must not be silently reinstated as
"needs review" just because a re-run met the same event again. Only a full run
rewrites it — a partial run would be missing every document it did not build.
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import random
from dataclasses import dataclass, replace
from datetime import date, timedelta
from pathlib import Path
from typing import Any, Iterable

from legal_crawler.index import TemporalIndex
from legal_crawler.storage.documents import DocumentStore
from legal_crawler.temporal import (
    EventApplier,
    EventStatus,
    ExtractionMethod,
    LegalDocument,
    LegalEvent,
    LegalOperation,
    Provenance,
    Provision,
    ProvisionInsertion,
    ProvisionLevel,
    ProvisionVersion,
    TemporalInterval,
    TextUpdate,
    make_document_id,
    make_provision_id,
    make_version_id,
)
from legal_crawler.temporal.event_applier import EventApplicationError
from legal_crawler.temporal.effective_intervals import effective_intervals_by_version
from legal_crawler.temporal.state import TemporalState, TemporalStateError
from legal_crawler.temporal.validity import ValidityService


@dataclass(frozen=True, slots=True)
class EventEnvelope:
    """One input row plus a stable position for deterministic logging."""

    line_number: int
    row: dict[str, Any]

    @property
    def target_document_id(self) -> str | None:
        value = self.row.get("target_document_id")
        return make_document_id(value) if value else None

    @property
    def sort_key(self) -> tuple[str, str, str, str, int]:
        actor = self.row.get("actor_id")
        return (
            self.target_document_id or "",
            str(self.row.get("effective_on") or ""),
            make_document_id(actor) if actor else "",
            str(self.row.get("id") or ""),
            self.line_number,
        )

    @property
    def application_sort_key(self) -> tuple[str, str, int]:
        """Legal ordering from the plan, preserving source order for ties."""
        actor = self.row.get("actor_id")
        return (
            str(self.row.get("effective_on") or ""),
            make_document_id(actor) if actor else "",
            self.line_number,
        )


def build_version_files(
    data_dir: Path,
    index_path: Path,
    versions_path: Path,
    event_log_path: Path,
    *,
    review_path: Path | None = None,
    limit_documents: int | None = None,
    target_document_ids: Iterable[str] = (),
    verify_pairs: int = 0,
) -> dict[str, int | str]:
    """Build both artifacts atomically and return observable counters."""
    if limit_documents is not None and limit_documents < 1:
        raise ValueError("limit_documents must be at least 1")
    if verify_pairs < 0:
        raise ValueError("verify_pairs must not be negative")

    requested_documents = tuple(target_document_ids)
    source = DocumentStore(data_dir)
    source_ids = sorted(source.ids("raw"))
    source_id_by_domain = {make_document_id(item): item for item in source_ids}
    subtree_source_ids = set(source.ids("derived/subtrees"))
    events = _read_events(data_dir / "derived" / "provision_events.jsonl")

    versions_path.parent.mkdir(parents=True, exist_ok=True)
    event_log_path.parent.mkdir(parents=True, exist_ok=True)
    versions_tmp = versions_path.with_name(versions_path.name + ".tmp")
    event_log_tmp = event_log_path.with_name(event_log_path.name + ".tmp")
    versions_tmp.unlink(missing_ok=True)
    event_log_tmp.unlink(missing_ok=True)

    report: collections.Counter[str] = collections.Counter()
    outcomes: dict[int, dict[str, Any]] = {}
    review: list[dict[str, Any]] = []
    try:
        with TemporalIndex(index_path) as index:
            documents = {
                make_document_id(item.id): (item.id, _canonical_document(item))
                for item in index.documents()
            }
            selected = _select_documents(
                documents,
                limit_documents=limit_documents,
                target_document_ids=requested_documents,
            )
            selected_ids = {item.id for _, item in selected}
            full_run = limit_documents is None and not requested_documents
            rng = random.Random(20260919)
            dated_ids = [item.id for _, item in selected if item.effective_from is not None]
            verify_ids = set(rng.sample(dated_ids, min(len(dated_ids), verify_pairs * 2)))

            by_target: dict[str, list[EventEnvelope]] = collections.defaultdict(list)
            for envelope in events:
                target_id = envelope.target_document_id
                if target_id in selected_ids:
                    by_target[target_id].append(envelope)
                elif full_run:
                    outcomes[envelope.line_number] = _rejected_log(
                        envelope,
                        "missing_target_document"
                        if target_id is None
                        else "target_document_not_indexed",
                    )

            with versions_tmp.open("w", encoding="utf-8", newline="\n") as version_out:
                for position, (stored_document_id, document) in enumerate(selected, 1):
                    _build_document_versions(
                        index=index,
                        source=source,
                        source_document_id=source_id_by_domain.get(document.id),
                        subtree_source_ids=subtree_source_ids,
                        stored_document_id=stored_document_id,
                        document=document,
                        envelopes=by_target.get(document.id, ()),
                        documents=documents,
                        output=version_out,
                        outcomes=outcomes,
                        report=report,
                        review=review,
                        verify=(document.id in verify_ids),
                        rng=rng,
                    )
                    report["documents"] += 1
                    if position % 500 == 0:
                        print(f"  {position:,}/{len(selected):,} documents", flush=True)

            if report["verified_pairs"] < verify_pairs:
                raise ValueError(
                    f"only {report['verified_pairs']} of {verify_pairs} requested "
                    "(provision, date) comparisons were possible"
                )

            considered = [
                item
                for item in events
                if item.line_number in outcomes
            ]
            with event_log_tmp.open("w", encoding="utf-8", newline="\n") as log_out:
                for envelope in sorted(considered, key=lambda item: item.sort_key):
                    _write_json(log_out, outcomes[envelope.line_number])
                    report[f"events_{outcomes[envelope.line_number]['outcome']}"] += 1

        versions_tmp.replace(versions_path)
        event_log_tmp.replace(event_log_path)
        if review_path is not None and full_run:
            rows, decided = write_review_queue(review_path, review)
            report["review_rows"] = rows
            report["review_rows_already_decided"] = decided
        else:
            report["review_rows_not_written"] = len(review)
    finally:
        versions_tmp.unlink(missing_ok=True)
        event_log_tmp.unlink(missing_ok=True)

    result: dict[str, int | str] = dict(report)
    result["versions_sha256"] = _sha256(versions_path)
    result["event_log_sha256"] = _sha256(event_log_path)
    return result


def _select_documents(
    documents: dict[str, tuple[str, LegalDocument]],
    *,
    limit_documents: int | None,
    target_document_ids: Iterable[str],
) -> list[tuple[str, LegalDocument]]:
    requested = {make_document_id(item) for item in target_document_ids}
    missing = requested - set(documents)
    if missing:
        raise ValueError("target documents are not indexed: " + ", ".join(sorted(missing)))
    selected = [
        value
        for domain_id, value in sorted(documents.items())
        if not requested or domain_id in requested
    ]
    return selected[:limit_documents] if limit_documents else selected


def _build_document_versions(
    *,
    index: TemporalIndex,
    source: DocumentStore,
    source_document_id: str | None,
    subtree_source_ids: set[str],
    stored_document_id: str,
    document: LegalDocument,
    envelopes: Iterable[EventEnvelope],
    documents: dict[str, tuple[str, LegalDocument]],
    output,
    outcomes: dict[int, dict[str, Any]],
    report: collections.Counter[str],
    review: list[dict[str, Any]],
    verify: bool,
    rng: random.Random,
) -> None:
    stored_provisions = index.document_order(stored_document_id)
    provisions = tuple(_canonical_provision(item) for item in stored_provisions)
    stored_versions = index.versions_for_document(stored_document_id)
    text_by_provision = {
        make_provision_id(item.provision_id): item.text
        for item in stored_versions
        if item.ordinal == 1 and item.text
    }
    if source_document_id in subtree_source_ids:
        subtree = source.load("derived/subtrees", source_document_id)
        text_by_provision.update(
            {
                make_provision_id(node["id"]): node["text"]
                for node in subtree.get("nodes", ())
                if node.get("text")
            }
        )

    initial_versions = tuple(
        ProvisionVersion(
            id=make_version_id(provision.id, 1),
            provision_id=provision.id,
            ordinal=1,
            text=text_by_provision[provision.id],
            validity=(
                TemporalInterval(document.effective_from)
                if document.effective_from is not None
                else None
            ),
        )
        for provision in provisions
        if provision.id in text_by_provision
    )
    report["initial_versions"] += len(initial_versions)
    report["provisions_without_text"] += len(provisions) - len(initial_versions)

    if document.effective_from is None:
        for version in initial_versions:
            _write_json(output, _version_row(version, ()))
        report["undated_versions"] += len(initial_versions)
        for envelope in envelopes:
            row = envelope.row
            if row.get("status") not in {
                EventStatus.VERIFIED.value,
                EventStatus.AUTO_ACCEPTED.value,
            }:
                outcomes[envelope.line_number] = _rejected_log(
                    envelope,
                    "status_not_applicable",
                    detail=str(
                        row.get("status_reason") or row.get("status") or "unknown"
                    ),
                )
            else:
                outcomes[envelope.line_number] = _rejected_log(
                    envelope, "target_document_has_no_effective_from"
                )
        return

    state = TemporalState()
    state.add_document(document)
    for provision in provisions:
        state.add_provision(provision)
    for version in initial_versions:
        state.add_version(version)

    applier = EventApplier()
    for envelope in sorted(envelopes, key=lambda item: item.application_sort_key):
        row = envelope.row
        if row.get("status") not in {
            EventStatus.VERIFIED.value,
            EventStatus.AUTO_ACCEPTED.value,
        }:
            outcomes[envelope.line_number] = _rejected_log(
                envelope,
                "status_not_applicable",
                detail=str(row.get("status_reason") or row.get("status") or "unknown"),
            )
            continue
        actor_id = row.get("actor_id")
        actor = documents.get(make_document_id(actor_id)) if actor_id else None
        if actor is None:
            outcomes[envelope.line_number] = _rejected_log(
                envelope, "source_document_not_indexed"
            )
            continue
        state.add_document(actor[1])
        try:
            event = _event_from_row(row)
            result = applier.apply(event, state)
        except (EventApplicationError, TemporalStateError, ValueError) as exc:
            outcomes[envelope.line_number] = _rejected_log(
                envelope,
                _application_reason(exc),
                detail=str(exc),
            )
            review.append(_review_row(row, str(exc), state))
            continue
        outcomes[envelope.line_number] = {
            **_base_log(envelope),
            "outcome": "applied",
            "reason": None,
            "already_applied": result.already_applied,
            "created_provision_ids": list(result.created_provision_ids),
            "created_version_ids": list(result.created_version_ids),
            "closed_version_ids": list(result.closed_version_ids),
        }

    effective = effective_intervals_by_version(state, document.id)
    if verify:
        _verify_effective_intervals(state, effective, rng, report)
    for version in sorted(
        state.versions,
        key=lambda item: (item.provision_id, item.ordinal, item.id),
    ):
        intervals = effective[version.id]
        _write_json(output, _version_row(version, intervals))
        report["versions"] += 1
        if not intervals:
            report["effective_empty"] += 1
        elif len(intervals) > 1:
            report["effective_disjoint"] += 1


def _canonical_document(document: LegalDocument) -> LegalDocument:
    return replace(document, id=make_document_id(document.id))


def _canonical_provision(provision: Provision) -> Provision:
    return replace(
        provision,
        id=make_provision_id(provision.id),
        document_id=make_document_id(provision.document_id),
        parent_id=(make_provision_id(provision.parent_id) if provision.parent_id else None),
        inserted_after_id=(
            make_provision_id(provision.inserted_after_id)
            if provision.inserted_after_id
            else None
        ),
    )


def _event_from_row(row: dict[str, Any]) -> LegalEvent:
    actor_id = make_document_id(row["actor_id"])
    updates = tuple(
        TextUpdate(
            make_provision_id(item["target_provision_id"]),
            item["new_text"],
        )
        for item in row.get("text_updates", ())
    )
    insertions = tuple(
        ProvisionInsertion(
            provision_id=make_provision_id(item["provision_id"]),
            level=ProvisionLevel(item["level"]),
            title=item["title"],
            text=item["text"],
            parent_id=(make_provision_id(item["parent_id"]) if item.get("parent_id") else None),
            after_provision_id=(
                make_provision_id(item["after_provision_id"])
                if item.get("after_provision_id")
                else None
            ),
            order_index=item.get("order_index"),
        )
        for item in row.get("insertions", ())
    )
    target = row.get("target_provision_id")
    explicit_targets = () if updates else ((make_provision_id(target),) if target else ())
    return LegalEvent(
        id=str(row["id"]),
        operation=LegalOperation(row["operation"]),
        source_document_id=actor_id,
        target_document_id=make_document_id(row["target_document_id"]),
        effective_on=(date.fromisoformat(row["effective_on"]) if row.get("effective_on") else None),
        target_provision_ids=explicit_targets,
        text_updates=updates,
        insertions=insertions,
        status=EventStatus(row["status"]),
        provenance=(
            Provenance(
                actor_id,
                ExtractionMethod.RULE,
                evidence_text=row.get("evidence"),
            ),
        ),
    )


def _version_row(
    version: ProvisionVersion,
    effective_intervals: tuple[TemporalInterval, ...],
) -> dict[str, Any]:
    validity = version.validity
    single = effective_intervals[0] if len(effective_intervals) == 1 else None
    return {
        "id": version.id,
        "provision_id": version.provision_id,
        "ordinal": version.ordinal,
        "text": version.text,
        "valid_from": validity.start.isoformat() if validity else None,
        "valid_to": validity.end.isoformat() if validity and validity.end else None,
        # The array is authoritative. Null scalar bounds mean zero OR multiple
        # windows, never an open interval; inspect effective_interval_count.
        "effective_interval_count": len(effective_intervals),
        "effective_intervals": [
            {"start": item.start.isoformat(), "end": item.end.isoformat() if item.end else None}
            for item in effective_intervals
        ],
        "effective_from": single.start.isoformat() if single else None,
        "effective_to": single.end.isoformat() if single and single.end else None,
        "created_by_event_id": version.created_by_event_id,
        "ended_by_event_id": version.ended_by_event_id,
        "provenance": [
            {
                "source_document_id": item.source_document_id,
                "method": item.method.value,
                "source_provision_id": item.source_provision_id,
                "evidence_text": item.evidence_text,
                "source_url": item.source_url,
                "confidence": item.confidence,
                "details": dict(item.details),
            }
            for item in version.provenance
        ],
    }


def _review_row(row: dict[str, Any], reason: str, state: TemporalState) -> dict[str, Any]:
    """One rejected event, self-contained enough to judge without the corpus."""
    pid = row.get("target_provision_id") or next(
        (item["target_provision_id"] for item in row.get("text_updates") or ()), None
    )
    provision = state.provision(pid) if pid else None
    chain = state.chain(pid) if pid else None
    latest = chain.versions[-1] if chain and chain.versions else None
    return {
        "schema_version": 1,
        "event_id": row["id"],
        "decision": "needs_review",
        "method": "auto_rejected",
        "reason": reason,
        "actor_id": row["actor_id"],
        "actor_number": row.get("actor_number"),
        "operation": row["operation"],
        "effective_on": row["effective_on"],
        "target_document_id": row.get("target_document_id"),
        "target_provision_id": pid,
        "provision_title": provision.title if provision else None,
        "provision_level": provision.level.value if provision else None,
        "current_text": latest.text if latest else None,
        "current_valid_from": (
            latest.validity.start.isoformat() if latest and latest.validity else None
        ),
        "locator": row.get("locator"),
        "evidence": row.get("evidence"),
    }


def write_review_queue(path: Path, fresh: list[dict[str, Any]]) -> tuple[int, int]:
    """Merge newly rejected events into the queue, keeping every verdict."""
    kept = []
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                record = json.loads(line)
                if record.get("method") != "auto_rejected":
                    kept.append(record)
    decided = {record["event_id"] for record in kept}
    rows = kept + [row for row in fresh if row["event_id"] not in decided]
    rows.sort(key=lambda item: item["event_id"])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(item, ensure_ascii=False) + "\n" for item in rows),
        encoding="utf-8",
    )
    return len(rows), len(kept)


def _verify_effective_intervals(
    state: TemporalState,
    effective: dict[str, tuple[TemporalInterval, ...]],
    rng: random.Random,
    report: collections.Counter[str],
) -> None:
    """Compare precomputation against the independent point-in-time oracle."""
    versions = state.versions
    if not versions:
        return
    version = rng.choice(versions)
    assert version.validity is not None
    local = version.validity
    document = state.document(state.provision(version.provision_id).document_id)
    dates = {local.start}
    if local.start > date.min:
        dates.add(local.start - timedelta(days=1))
    if local.end is not None:
        dates.update((local.end - timedelta(days=1), local.end))
    if document.effective_to is not None:
        dates.add(document.effective_to)
    # Repealing an Điều ends its Khoản too, so a child's answer can only flip on
    # an ancestor's boundary. Sampling the version's own dates alone would never
    # reach the gap this precomputation exists to preserve.
    ancestor_id = state.provision(version.provision_id).parent_id
    while ancestor_id is not None:
        ancestor_chain = state.chain(ancestor_id)
        for item in ancestor_chain.versions if ancestor_chain else ():
            if item.validity is None:
                continue
            dates.add(item.validity.start)
            if item.validity.end is not None:
                dates.update((item.validity.end - timedelta(days=1), item.validity.end))
        ancestor = state.provision(ancestor_id)
        ancestor_id = ancestor.parent_id if ancestor else None
    lower = max(date.min.toordinal(), local.start.toordinal() - 365)
    upper = min(date.max.toordinal(), (local.end or local.start).toordinal() + 365)
    dates.add(date.fromordinal(rng.randint(lower, upper)))
    service = ValidityService(state)
    for at in sorted(dates):
        expected = any(item.contains(at) for item in effective[version.id])
        actual = service.check(version.provision_id, at)
        found = actual.valid and actual.version is not None and actual.version.id == version.id
        if expected != found:
            raise AssertionError(
                f"effective interval mismatch for {version.id} at {at}: "
                f"precomputed={expected}, ValidityService={found} ({actual.reason})"
            )
        report["verified_pairs"] += 1
    report["verified_documents"] += 1


def _read_events(path: Path) -> list[EventEnvelope]:
    if not path.exists():
        raise FileNotFoundError(f"event store does not exist: {path}")
    return [
        EventEnvelope(line_number, json.loads(line))
        for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1)
        if line.strip()
    ]


def _base_log(envelope: EventEnvelope) -> dict[str, Any]:
    row = envelope.row
    return {
        "event_id": row.get("id"),
        "input_line": envelope.line_number,
        "input_status": row.get("status"),
        "status_reason": row.get("status_reason"),
        "operation": row.get("operation"),
        "effective_on": row.get("effective_on"),
        "actor_id": make_document_id(row["actor_id"]) if row.get("actor_id") else None,
        "target_document_id": envelope.target_document_id,
    }


def _rejected_log(
    envelope: EventEnvelope,
    reason: str,
    *,
    detail: str | None = None,
) -> dict[str, Any]:
    return {
        **_base_log(envelope),
        "outcome": "rejected",
        "reason": reason,
        "detail": detail,
        "already_applied": False,
        "created_provision_ids": [],
        "created_version_ids": [],
        "closed_version_ids": [],
    }


def _application_reason(exc: Exception) -> str:
    message = str(exc)
    known = (
        ("must be later than current version start", "event_not_after_version_start"),
        ("target provision has no version", "target_provision_has_no_version"),
        ("target provision has no open version", "target_provision_has_no_open_version"),
        ("target provision does not exist", "target_provision_not_found"),
        ("source document does not exist", "source_document_not_found"),
        ("target document does not exist", "target_document_not_found"),
        ("was already applied with different content", "conflicting_duplicate_event_id"),
    )
    return next((code for fragment, code in known if fragment in message), type(exc).__name__)


def _write_json(stream, row: dict[str, Any]) -> None:
    stream.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=Path("data"))
    parser.add_argument("--index", type=Path, default=None)
    parser.add_argument("--out", type=Path, default=None)
    parser.add_argument("--event-log", type=Path, default=None)
    parser.add_argument(
        "--review", type=Path, default=None,
        help="review queue for rejected events; written on a full run only",
    )
    parser.add_argument("--limit-documents", type=int, default=None)
    parser.add_argument(
        "--verify-pairs", type=int, default=0,
        help="minimum random (provision, date) pairs checked against ValidityService",
    )
    parser.add_argument(
        "--target-document",
        action="append",
        default=[],
        help="build only this source/domain document ID; may be repeated",
    )
    args = parser.parse_args()
    index_path = args.index or args.data / "temporal.sqlite"
    versions_path = args.out or args.data / "derived" / "versions.jsonl"
    event_log_path = args.event_log or args.data / "derived" / "event_log.jsonl"
    review_path = args.review or args.data / "review" / "provision_events.jsonl"
    report = build_version_files(
        args.data,
        index_path,
        versions_path,
        event_log_path,
        review_path=review_path,
        limit_documents=args.limit_documents,
        target_document_ids=args.target_document,
        verify_pairs=args.verify_pairs,
    )
    version_count = int(report.get("versions", 0)) + int(report.get("undated_versions", 0))
    event_count = int(report.get("events_applied", 0)) + int(report.get("events_rejected", 0))
    print(f"wrote {version_count:,} versions -> {versions_path}")
    print(f"wrote {event_count:,} event outcomes -> {event_log_path}")
    print(f"  versions sha256: {report['versions_sha256']}")
    print(f"  event log sha256: {report['event_log_sha256']}")
    for key in sorted(report):
        if not key.endswith("sha256"):
            print(f"  {int(report[key]):>10,}  {key.replace('_', ' ')}")


if __name__ == "__main__":
    main()

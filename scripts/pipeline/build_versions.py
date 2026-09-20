#!/usr/bin/env python3
"""Build the version chain of every provision (plan phase-3, C2).

Per document: version 1 of each provision with text — the portal's text from
the index, or for the Khoản/Điểm split from article text (backfill T5) the
text in `data/derived/subtrees` — then the applicable L2 events on that
document (`verified`/`auto_accepted` in `data/derived/provision_events.jsonl`)
through the real `EventApplier`, oldest first by `(effective_on, actor)`.

Version 1 is open-ended on purpose: the document's own `effTo` bounds every
provision through formula (3) (`temporal/validity.py`), so closing the chain
there too would make every event on an expired document fail as "no open
version". A document with no `effFrom` keeps its versions undated, as
`ingest.py` stores them: no point-in-time query returns them.

An event that cannot be applied (out-of-order date, node already closed, no
text) is not applied and is logged with the reason — never reordered or forced.

Writes, whole and deterministic (delete and re-run):
  data/derived/versions.jsonl   every version of every provision
  data/derived/event_log.jsonl  every event: applied, rejected (why), or skipped
                                because it is `needs_review` (why)

Usage:
    python scripts/pipeline/build_versions.py [--limit N]   # first N documents
"""
from __future__ import annotations

import argparse
import collections
import json
import re
from datetime import date
from pathlib import Path

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
    ProvisionVersion,
    TemporalInterval,
    TextUpdate,
    make_document_id,
    make_provision_id,
    make_version_id,
)
from legal_crawler.temporal.event_applier import EventApplicationError
from legal_crawler.temporal.state import TemporalState

APPLICABLE = (EventStatus.VERIFIED.value, EventStatus.AUTO_ACCEPTED.value)


def build_document_versions(
    index: TemporalIndex,
    document: LegalDocument,
    subtree_text: dict[str, str | None],
    rows: list[dict],
    applier: EventApplier,
) -> tuple[list[ProvisionVersion], dict[str, str | None]]:
    """Versions of one document after its events, and per event id: None if applied, else why not."""
    state = TemporalState()
    state.add_document(document)
    undated: list[ProvisionVersion] = []
    for p in index.document_order(document.id):
        state.add_provision(p)
        stored = index.versions_of(p.id)
        text = stored[0].text if stored else subtree_text.get(p.id)
        if not text:
            continue
        version = ProvisionVersion(
            id=make_version_id(p.id, 1), provision_id=p.id, ordinal=1, text=text,
            validity=TemporalInterval(document.effective_from) if document.effective_from else None,
        )
        if version.validity:
            state.add_version(version)
        else:
            undated.append(version)  # a chain holds only dated versions

    outcomes: dict[str, str | None] = {}
    for row in sorted(rows, key=lambda r: (r["effective_on"], r["actor_id"])):
        if state.document(row["actor_id"]) is None:
            state.add_document(index.document(row["actor_id"]))
        try:
            applier.apply(_event(row), state)
            outcomes[row["id"]] = None
        except (EventApplicationError, ValueError) as exc:
            outcomes[row["id"]] = str(exc)
    return [*state.versions, *undated], outcomes


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--data", type=Path, default=Path("data"))
    parser.add_argument("--limit", type=int, default=None, help="only the first N documents (by id)")
    args = parser.parse_args()
    index = TemporalIndex(args.data / "temporal.sqlite")
    store = DocumentStore(args.data)
    subtree_of = {make_document_id(i): i for i in store.ids("derived/subtrees")}  # domain id -> portal id

    log: dict[str, dict] = {}
    by_target: dict[str, list[dict]] = collections.defaultdict(list)
    for line in (args.data / "derived/provision_events.jsonl").read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row["status"] in APPLICABLE:
            by_target[row["target_document_id"]].append(row)
        elif not args.limit:  # with --limit the rest belong to documents not built
            log[row["id"]] = {"event_id": row["id"], "status": row["status"],
                              "outcome": "skipped", "reason": row["status_reason"]}

    applier = EventApplier()
    documents = sorted(index.documents(), key=lambda d: d.id)[: args.limit]
    chains: collections.Counter[str] = collections.Counter()
    with (args.data / "derived/versions.jsonl").open("w", encoding="utf-8") as out:
        for n, document in enumerate(documents, 1):
            if n % 2000 == 0:
                print(f"  {n:,}/{len(documents):,} documents", flush=True)
            derived = ({make_provision_id(node["id"]): node.get("text")
                        for node in store.load("derived/subtrees", subtree_of[document.id])["nodes"]}
                       if document.id in subtree_of else {})
            rows = by_target.get(document.id, [])
            versions, outcomes = build_document_versions(index, document, derived, rows, applier)
            for version in versions:
                out.write(json.dumps(_version_row(version), ensure_ascii=False) + "\n")
            chains.update(["versions"] * len(versions))
            chains.update(["chains with 2+ versions"] * sum(v.ordinal == 2 for v in versions))
            for row in rows:
                reason = outcomes[row["id"]]
                log[row["id"]] = {"event_id": row["id"], "status": row["status"],
                                  "outcome": "applied" if reason is None else "rejected", "reason": reason}

    with (args.data / "derived/event_log.jsonl").open("w", encoding="utf-8") as out:
        for event_id in sorted(log):
            out.write(json.dumps(log[event_id], ensure_ascii=False) + "\n")

    print(f"{len(documents):,} documents -> {chains['versions']:,} versions, "
          f"{chains['chains with 2+ versions']:,} provisions with 2+ versions")
    outcome = collections.Counter(
        (e["outcome"], re.sub(r"[0-9a-f-]{8,}\S*|\d{4}-\d\d-\d\d|event:\S+", "…", e["reason"] or ""))
        for e in log.values())
    print(f"{len(log):,} events logged")
    for (kind, reason), count in sorted(outcome.items(), key=lambda kv: (kv[0][0], -kv[1])):
        print(f"  {count:>7,}  {kind:<9} {reason}")


def _version_row(v: ProvisionVersion) -> dict:
    return {
        "id": v.id, "provision_id": v.provision_id, "ordinal": v.ordinal, "text": v.text,
        "valid_from": v.validity.start.isoformat() if v.validity else None,
        "valid_to": v.validity.end.isoformat() if v.validity and v.validity.end else None,
        "created_by_event_id": v.created_by_event_id, "ended_by_event_id": v.ended_by_event_id,
    }


def _event(row: dict) -> LegalEvent:
    updates = tuple(TextUpdate(u["target_provision_id"], u["new_text"]) for u in row["text_updates"])
    return LegalEvent(
        id=row["id"],
        operation=LegalOperation(row["operation"]),
        source_document_id=row["actor_id"],
        target_document_id=row["target_document_id"],
        effective_on=date.fromisoformat(row["effective_on"]),
        target_provision_ids=() if updates else (row["target_provision_id"],),
        text_updates=updates,
        status=EventStatus(row["status"]),
        provenance=(Provenance(row["actor_id"], ExtractionMethod.RULE, evidence_text=row["evidence"]),),
    )


if __name__ == "__main__":
    main()

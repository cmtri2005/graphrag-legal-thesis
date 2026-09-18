#!/usr/bin/env python3
"""Do the applicable L2 events really apply? (plan l2-event-store, Validation)

For every target document with applicable events (`verified`/`auto_accepted`
in `data/derived/provision_events.jsonl`), build a `TemporalState` from the
index — its provisions, one version per provision with text, open-ended from
the document's `effFrom` — and run each event through the real
`EventApplier`, oldest first. Reports how many apply and why the rest do not;
that is the input P3.15 will actually get.

Version 1 is open-ended on purpose: the document's own `effTo` bounds every
provision through formula (3) (`temporal/validity.py`), so closing the chain
there too would make every event on an expired document fail as "no open
version".

Usage:
    python scripts/check/apply_provision_events.py [--limit N]
"""
from __future__ import annotations

import argparse
import collections
import json
import re
from dataclasses import replace
from datetime import date
from pathlib import Path

from legal_crawler.index import TemporalIndex
from legal_crawler.storage.documents import DocumentStore
from legal_crawler.temporal import (
    EventApplier,
    EventStatus,
    ExtractionMethod,
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


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--data", type=Path, default=Path("data"))
    parser.add_argument("--limit", type=int, default=None, help="only the first N target documents")
    args = parser.parse_args()
    index = TemporalIndex(args.data / "temporal.sqlite")
    store = DocumentStore(args.data)
    subtree_ids = set(store.ids("derived/subtrees"))
    source_id_by_domain = {
        make_document_id(source_id): source_id for source_id in store.ids("raw")
    }
    documents = {
        make_document_id(document.id): (
            document.id,
            replace(document, id=make_document_id(document.id)),
        )
        for document in index.documents()
    }

    by_target: dict[str, list[dict]] = collections.defaultdict(list)
    for line in (args.data / "derived/provision_events.jsonl").read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row["status"] in ("verified", "auto_accepted"):
            by_target[make_document_id(row["target_document_id"])].append(row)

    outcome: collections.Counter[str] = collections.Counter()
    applier = EventApplier()
    for n, (doc_id, rows) in enumerate(sorted(by_target.items())):
        if args.limit and n >= args.limit:
            break
        state = TemporalState()
        stored_document_id, target = documents[doc_id]
        state.add_document(target)
        source_document_id = source_id_by_domain.get(doc_id)
        derived = (
            {
                make_provision_id(node["id"]): node.get("text")
                for node in store.load("derived/subtrees", source_document_id)["nodes"]
            }
            if source_document_id in subtree_ids
            else {}
        )
        stored_versions = {
            make_provision_id(version.provision_id): version.text
            for version in index.versions_for_document(stored_document_id)
            if version.ordinal == 1
        }
        for stored_provision in index.document_order(stored_document_id):
            p = replace(
                stored_provision,
                id=make_provision_id(stored_provision.id),
                document_id=make_document_id(stored_provision.document_id),
                parent_id=(
                    make_provision_id(stored_provision.parent_id)
                    if stored_provision.parent_id
                    else None
                ),
            )
            state.add_provision(p)
            text = stored_versions.get(p.id) or derived.get(p.id)
            if text and target.effective_from:
                state.add_version(ProvisionVersion(id=make_version_id(p.id, 1), provision_id=p.id, ordinal=1, text=text,
                                                   validity=TemporalInterval(target.effective_from)))
        for row in sorted(rows, key=lambda r: (r["effective_on"], r["actor_id"])):
            actor_id = make_document_id(row["actor_id"])
            if state.document(actor_id) is None:
                state.add_document(documents[actor_id][1])
            try:
                applier.apply(_event(row), state)
                outcome["applied"] += 1
            except (EventApplicationError, ValueError) as exc:
                # One key per failure kind: drop the ids and dates from the message.
                outcome[re.sub(r"[0-9a-f-]{8,}\S*|\d{4}-\d\d-\d\d|event:\S+", "…", str(exc))] += 1

    total = sum(outcome.values())
    print(f"{total:,} applicable events on {min(len(by_target), args.limit or len(by_target)):,} target documents")
    for key, count in outcome.most_common():
        print(f"  {count:>7,} ({count / total:.1%})  {key}")


def _event(row: dict) -> LegalEvent:
    updates = tuple(
        TextUpdate(make_provision_id(u["target_provision_id"]), u["new_text"])
        for u in row["text_updates"]
    )
    actor_id = make_document_id(row["actor_id"])
    return LegalEvent(
        id=row["id"],
        operation=LegalOperation(row["operation"]),
        source_document_id=actor_id,
        target_document_id=make_document_id(row["target_document_id"]),
        effective_on=date.fromisoformat(row["effective_on"]),
        target_provision_ids=(
            ()
            if updates
            else (make_provision_id(row["target_provision_id"]),)
        ),
        text_updates=updates,
        status=EventStatus(row["status"]),
        provenance=(Provenance(actor_id, ExtractionMethod.RULE, evidence_text=row["evidence"]),),
    )


if __name__ == "__main__":
    main()

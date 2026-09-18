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

    by_target: dict[str, list[dict]] = collections.defaultdict(list)
    for line in (args.data / "derived/provision_events.jsonl").read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row["status"] in ("verified", "auto_accepted"):
            by_target[row["target_document_id"]].append(row)

    outcome: collections.Counter[str] = collections.Counter()
    applier = EventApplier()
    for n, (doc_id, rows) in enumerate(sorted(by_target.items())):
        if args.limit and n >= args.limit:
            break
        state = TemporalState()
        target = index.document(doc_id)
        state.add_document(target)
        derived = ({node["id"]: node.get("text") for node in store.load("derived/subtrees", doc_id)["nodes"]}
                   if doc_id in subtree_ids else {})
        for p in index.document_order(doc_id):
            state.add_provision(p)
            stored = index.versions_of(p.id)
            text = stored[0].text if stored else derived.get(p.id)
            if text and target.effective_from:
                state.add_version(ProvisionVersion(id=f"{p.id}:1", provision_id=p.id, ordinal=1, text=text,
                                                   validity=TemporalInterval(target.effective_from)))
        for row in sorted(rows, key=lambda r: (r["effective_on"], r["actor_id"])):
            if state.document(row["actor_id"]) is None:
                state.add_document(index.document(row["actor_id"]))
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

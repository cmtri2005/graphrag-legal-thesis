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

Each version also gets the window it is *really* in force (P3.16, formula (3)):
its own `[valid_from, valid_to)` intersected with its document's window and
with every ancestor's, because repealing an Điều ends its Khoản too. A node we
hold no text for is transparent here, exactly as in `ValidityService`. When the
intersection is empty the version was never in force and both fields are null.

Writes, whole and deterministic (delete and re-run):
  data/derived/versions.jsonl   every version of every provision
  data/derived/event_log.jsonl  every event: applied, rejected (why), or skipped
                                because it is `needs_review` (why)

And the review queue for what it refused (C3, decision Q2), which is *not*
disposable:
  data/review/provision_events.jsonl   one row per rejected event, with the
                                       text and the instruction sentence a
                                       reviewer needs to judge it

That file is reviewed by an LLM first and double-checked by a human, so this
script owns only the rows it wrote itself (`method: auto_rejected`). A row
another process decided (`llm_reviewed`, `human_reviewed`) is read back
untouched and never recomputed: a verdict must not be silently reinstated as
"needs review" just because a re-run met the same event again. Only a full run
rewrites it — with --limit the queue would be missing every document not built.

Usage:
    python scripts/pipeline/build_versions.py [--limit N]   # first N documents
"""
from __future__ import annotations

import argparse
import collections
import json
import pathlib
import random
import re
from datetime import date, timedelta
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
from legal_crawler.temporal.validity import ValidityService

APPLICABLE = (EventStatus.VERIFIED.value, EventStatus.AUTO_ACCEPTED.value)
ONE_DAY = timedelta(days=1)
Window = tuple[date | None, date | None]  # half-open [start, end); None is unbounded


def _clip(window: Window, other: Window) -> Window:
    """Intersect two half-open windows."""
    starts = [s for s in (window[0], other[0]) if s is not None]
    ends = [e for e in (window[1], other[1]) if e is not None]
    return (max(starts) if starts else None, min(ends) if ends else None)


def _empty(window: Window) -> bool:
    return window[0] is not None and window[1] is not None and window[0] >= window[1]


def _contains(window: Window | None, at: date) -> bool:
    if window is None or _empty(window):
        return False
    return (window[0] is None or window[0] <= at) and (window[1] is None or at < window[1])


def effective_intervals(
    document: LegalDocument, provisions: tuple, state: TemporalState
) -> dict[str, Window]:
    """The window each version is really in force — formula (3).

    `provisions` must list parents before children, which `document_order`
    guarantees, so one pass down the tree is enough.
    """
    doc_window: Window = (document.effective_from, document.effective_to)
    alive: dict[str, Window] = {}
    out: dict[str, Window] = {}
    for provision in provisions:
        inherited = alive.get(provision.parent_id, doc_window)
        chain = state.chain(provision.id)
        versions = chain.versions if chain else ()
        if not versions:
            # No text of its own: a heading, or an Điều the corpus lacks. It
            # constrains nothing, matching ValidityService.
            alive[provision.id] = inherited
            continue
        alive[provision.id] = _clip(
            (versions[0].validity.start, versions[-1].validity.end), inherited
        )
        for version in versions:
            out[version.id] = _clip(
                (version.validity.start, version.validity.end), inherited
            )
    return out


def verify_against_validity_service(
    state: TemporalState,
    document: LegalDocument,
    provisions: tuple,
    intervals: dict[str, Window],
    rng: random.Random,
    budget: int,
) -> tuple[int, int]:
    """Do the precomputed windows answer like `ValidityService`? (C4 acceptance)

    Queries the dates where an answer can flip — each version boundary and the
    day before it — rather than uniform random dates, which almost never land
    on one.
    """
    validity = ValidityService(state)
    checked = wrong = 0
    for provision in rng.sample(list(provisions), min(len(provisions), budget)):
        chain = state.chain(provision.id)
        versions = chain.versions if chain else ()
        dates: set[date] = set()
        for version in versions:
            dates.update({version.validity.start, version.validity.start - ONE_DAY})
            if version.validity.end:
                dates.update({version.validity.end, version.validity.end - ONE_DAY})
        if document.effective_from:
            dates.add(document.effective_from)
        for at in dates:
            ours = any(_contains(intervals.get(v.id), at) for v in versions)
            checked += 1
            wrong += ours != validity.check(provision.id, at).valid
    return checked, wrong


def build_document_versions(
    index: TemporalIndex,
    document: LegalDocument,
    subtree_text: dict[str, str | None],
    rows: list[dict],
    applier: EventApplier,
) -> tuple[list[ProvisionVersion], dict[str, str | None], TemporalState, tuple]:
    """Versions of one document after its events, and per event id: None if applied, else why not."""
    state = TemporalState()
    state.add_document(document)
    undated: list[ProvisionVersion] = []
    provisions = index.document_order(document.id)
    for p in provisions:
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
    return [*state.versions, *undated], outcomes, state, provisions


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--data", type=Path, default=Path("data"))
    parser.add_argument("--limit", type=int, default=None, help="only the first N documents (by id)")
    parser.add_argument("--verify", type=int, default=1000, metavar="N",
                        help="cross-check N (node, date) answers against ValidityService (0 to skip)")
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
    rng = random.Random(20260920)
    checked = wrong = 0
    review: list[dict] = []
    with (args.data / "derived/versions.jsonl").open("w", encoding="utf-8") as out:
        for n, document in enumerate(documents, 1):
            if n % 2000 == 0:
                print(f"  {n:,}/{len(documents):,} documents", flush=True)
            derived = ({make_provision_id(node["id"]): node.get("text")
                        for node in store.load("derived/subtrees", subtree_of[document.id])["nodes"]}
                       if document.id in subtree_of else {})
            rows = by_target.get(document.id, [])
            versions, outcomes, state, provisions = build_document_versions(
                index, document, derived, rows, applier)
            intervals = effective_intervals(document, provisions, state)
            for version in versions:
                out.write(json.dumps(_version_row(version, intervals.get(version.id)),
                                     ensure_ascii=False) + "\n")
            chains.update(["never in force"] * sum(
                _empty(w) for w in (intervals.get(v.id) for v in versions) if w is not None))
            if checked < args.verify:
                done, bad = verify_against_validity_service(
                    state, document, provisions, intervals, rng, budget=3)
                checked += done
                wrong += bad
            chains.update(["versions"] * len(versions))
            chains.update(["chains with 2+ versions"] * sum(v.ordinal == 2 for v in versions))
            for row in rows:
                reason = outcomes[row["id"]]
                log[row["id"]] = {"event_id": row["id"], "status": row["status"],
                                  "outcome": "applied" if reason is None else "rejected", "reason": reason}
                if reason is not None:
                    review.append(_review_row(row, reason, state))

    with (args.data / "derived/event_log.jsonl").open("w", encoding="utf-8") as out:
        for event_id in sorted(log):
            out.write(json.dumps(log[event_id], ensure_ascii=False) + "\n")

    if args.limit:
        print(f"{len(review):,} rejected events NOT written to the review queue (partial run)")
    else:
        total, verdicts = write_review_queue(args.data / "review/provision_events.jsonl", review)
        print(f"review queue: {total:,} rows ({verdicts:,} already decided by an LLM or a human)")

    print(f"{len(documents):,} documents -> {chains['versions']:,} versions, "
          f"{chains['chains with 2+ versions']:,} provisions with 2+ versions, "
          f"{chains['never in force']:,} never in force")
    if args.verify:
        print(f"effective windows vs ValidityService: {checked - wrong:,}/{checked:,} agree"
              + (f" — {wrong:,} DISAGREE" if wrong else ""))
    outcome = collections.Counter(
        (e["outcome"], re.sub(r"[0-9a-f-]{8,}\S*|\d{4}-\d\d-\d\d|event:\S+", "…", e["reason"] or ""))
        for e in log.values())
    print(f"{len(log):,} events logged")
    for (kind, reason), count in sorted(outcome.items(), key=lambda kv: (kv[0][0], -kv[1])):
        print(f"  {count:>7,}  {kind:<9} {reason}")


def _review_row(row: dict, reason: str, state: TemporalState) -> dict:
    """One rejected event, self-contained enough to judge without the corpus."""
    pid = row["target_provision_id"] or next(
        (u["target_provision_id"] for u in row["text_updates"]), None
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
        "actor_number": row["actor_number"],
        "operation": row["operation"],
        "effective_on": row["effective_on"],
        "target_document_id": row["target_document_id"],
        "target_provision_id": pid,
        "provision_title": provision.title if provision else None,
        "provision_level": provision.level.value if provision else None,
        "current_text": latest.text if latest else None,
        "current_valid_from": (
            latest.validity.start.isoformat() if latest and latest.validity else None
        ),
        "locator": row["locator"],
        "evidence": row["evidence"],
    }


def write_review_queue(path: pathlib.Path, fresh: list[dict]) -> tuple[int, int]:
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
    rows.sort(key=lambda r: r["event_id"])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8"
    )
    return len(rows), len(kept)


def _version_row(v: ProvisionVersion, effective: Window | None) -> dict:
    # An empty window means the version never stood: an ancestor had already
    # ended before it opened. Both fields are null, and valid_from stays set.
    usable = effective if effective and not _empty(effective) else None
    return {
        "id": v.id, "provision_id": v.provision_id, "ordinal": v.ordinal, "text": v.text,
        "valid_from": v.validity.start.isoformat() if v.validity else None,
        "valid_to": v.validity.end.isoformat() if v.validity and v.validity.end else None,
        "effective_from": usable[0].isoformat() if usable and usable[0] else None,
        "effective_to": usable[1].isoformat() if usable and usable[1] else None,
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

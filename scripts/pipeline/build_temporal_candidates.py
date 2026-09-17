#!/usr/bin/env python3
"""Backfill T4 — document-level temporal candidates, never written over raw.

Offline, a pure function of `data/` (run `build_eligibility.py` first). Writes
`data/derived/temporal_candidates.jsonl`, one record per in-scope document:

    effective_to        fully repealed ("HHL") with no effTo, and exactly one
                        held document repeals (code 1) or replaces (code 12) it,
                        with an effFrom later than the target's own. The
                        candidate is that actor's effFrom. status needs_review:
                        only a human decision in
                        data/review/temporal_candidates.jsonl can accept it.
    effective_from_lower_bound
                        no effFrom but an issueDate: a bound, never a date a
                        point-in-time query may use as exact.
    interval_check      effTo not after effFrom: the history's own dates
                        (normalised by `legal_date`) are attached as evidence
                        and the document stays unanchored.

Documents that fit none of these are counted by reason, not written.

Also writes `data/derived/temporal_candidates_review.tsv`: the effective_to
candidates with both documents' numbers, titles and vbpl links, for review.

Usage:
    python scripts/pipeline/build_temporal_candidates.py
"""
from __future__ import annotations

import argparse
import collections
import json
from pathlib import Path

from legal_crawler.storage.documents import DocumentStore
from legal_crawler.vocab.status_codes import (
    EMPTY_INTERVAL,
    NO_EFF_FROM,
    REPEALED_WITHOUT_EFF_TO,
    legal_date,
)

SCHEMA_VERSION = 1
ENDING_CODES = {1: "repeals", 12: "replaces"}
URL = "https://vbpl.vn/van-ban/chi-tiet/van-ban--{}"


def _day(value: str | None) -> str | None:
    return value[:10] if value else None


def _tsv_cell(value: str | None) -> str:
    """Collapse embedded tabs/newlines so one record can't span TSV rows.

    Titles scraped from the portal occasionally carry a literal newline; left
    alone it splits the TSV row across physical lines, silently corrupting
    every downstream reader (csv module, spreadsheet import, ...).
    """
    return " ".join((value or "").split())


def effective_to_candidate(target_id: str, target: dict, actors: dict[str, tuple[dict, set[int]]]) -> dict:
    """A candidate record, or a {"skip": reason} marker.

    `actors` maps each held document that repeals or replaces the target to
    (its raw record, the ending codes it uses on the target).
    """
    if len(actors) != 1:
        return {"skip": "no ending actor" if not actors else "several ending actors"}
    (actor_id, (actor, codes)), = actors.items()
    actor_from, target_from = _day(actor.get("effFrom")), _day(target.get("effFrom"))
    if not actor_from:
        return {"skip": "actor has no effFrom"}
    if actor_from <= target_from:
        return {"skip": "actor takes effect before the target"}
    return {
        "schema_version": SCHEMA_VERSION,
        "document_id": target_id,
        "field": "effective_to",
        "value": actor_from,
        "method": "unique_ending_actor_effective_from",
        "evidence_document_ids": [actor_id],
        "evidence_relation_codes": sorted(codes),
        "status": "needs_review",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=Path("data"))
    args = parser.parse_args()
    store = DocumentStore(args.data)
    derived = args.data / "derived"

    eligibility = [json.loads(line) for line in (derived / "eligibility.jsonl").read_text(encoding="utf-8").splitlines()]
    held = store.ids("raw")
    ending: dict[str, dict[str, set[int]]] = collections.defaultdict(lambda: collections.defaultdict(set))
    for line in (args.data / "edges.jsonl").read_text(encoding="utf-8").splitlines():
        edge = json.loads(line)
        if edge["reference_type"] in ENDING_CODES and edge["source_id"] in held:
            ending[edge["target_id"]][edge["source_id"]].add(edge["reference_type"])

    records, review_rows = [], []
    skipped: collections.Counter[str] = collections.Counter()
    for row in eligibility:
        if not row["in_scope"] or row["anchor_problem"] is None:
            continue
        doc_id = row["doc_id"]
        doc = store.load("raw", doc_id)
        if row["anchor_problem"] == REPEALED_WITHOUT_EFF_TO:
            actors = {a: (store.load("raw", a), codes) for a, codes in ending.get(doc_id, {}).items()}
            record = effective_to_candidate(doc_id, doc, actors)
            if "skip" in record:
                skipped[f"effective_to: {record['skip']}"] += 1
                continue
            records.append(record)
            actor_id = record["evidence_document_ids"][0]
            actor = actors[actor_id][0]
            review_rows.append([
                doc_id, doc.get("docNum"), _day(doc.get("effFrom")), record["value"],
                actor_id, actor.get("docNum"), ",".join(ENDING_CODES[c] for c in record["evidence_relation_codes"]),
                URL.format(doc_id), URL.format(actor_id),
                _tsv_cell(doc.get("title")), _tsv_cell(actor.get("title")),
            ])
        elif row["anchor_problem"] == NO_EFF_FROM:
            if not doc.get("issueDate"):
                skipped["effective_from_lower_bound: no issueDate"] += 1
                continue
            records.append({
                "schema_version": SCHEMA_VERSION, "document_id": doc_id,
                "field": "effective_from_lower_bound", "value": _day(doc["issueDate"]),
                "method": "issue_date", "evidence_document_ids": [doc_id],
                "evidence_relation_codes": [], "status": "lower_bound",
            })
        elif row["anchor_problem"] == EMPTY_INTERVAL:
            history = store.load("history", doc_id).get("history") or [] if doc_id in store.ids("history") else []
            dates = {
                r["content"]: str(d) for r in history
                if r.get("content") in {"DATE_HL", "DATE_HHL"} and (d := legal_date(r))
            }
            records.append({
                "schema_version": SCHEMA_VERSION, "document_id": doc_id, "field": "interval_check",
                "value": {"effFrom": _day(doc.get("effFrom")), "effTo": _day(doc.get("effTo")),
                          "history_DATE_HL": dates.get("DATE_HL"), "history_DATE_HHL": dates.get("DATE_HHL")},
                "method": "normalised_history_dates", "evidence_document_ids": [doc_id],
                "evidence_relation_codes": [], "status": "unresolved",
            })
        else:
            skipped[f"not handled: {row['anchor_problem']}"] += 1

    with (derived / "temporal_candidates.jsonl").open("w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    with (derived / "temporal_candidates_review.tsv").open("w", encoding="utf-8") as f:
        f.write("doc_id\tdoc_num\teffFrom\tcandidate_effTo\tactor_id\tactor_num\trelation\tdoc_url\tactor_url\tdoc_title\tactor_title\n")
        for cells in review_rows:
            f.write("\t".join(str(c) for c in cells) + "\n")

    fields = collections.Counter(r["field"] for r in records)
    print(f"{len(records):,} records -> {derived / 'temporal_candidates.jsonl'}")
    for name, count in fields.most_common():
        print(f"  {count:>6,}  {name}")
    print("not written:")
    for reason, count in skipped.most_common():
        print(f"  {count:>6,}  {reason}")


if __name__ == "__main__":
    main()

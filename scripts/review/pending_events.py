#!/usr/bin/env python3
"""ViLexTime — release rows whose gold may be stale because an event was not applied.

`build_versions.py` applies only `auto_accepted` and `verified` events; a
`needs_review` event is logged and left out (phase-3 decision Q2). When such an
event touches a row's provision **or one of its ancestors** on or before the
row's `as_of`, the gold may still show the text from before that change (pilot T6
row 9: 104/2022/NĐ-CP amended khoản 2 Điều 24 NĐ 19/2011 from 2023-01-01, gold kept
the old wording). Rule R6 of docs/vilextime-dinh-nghia.md: such a row stays out of
the test split until its line here has a decision.

Writes `data/review/pending_events.tsv`, one line per (row, event), with the
instruction sentence and empty `decision` / `note` columns. `decision` is one of:
  stale      the event did change this provision before as_of: gold is wrong
  no_effect  the event does not change this provision's content (wrong target,
             phrase edit elsewhere, document-level act already reflected)
It only reads; re-run after build_vilextime.py.

Usage:
    python scripts/review/pending_events.py
"""
from __future__ import annotations

import argparse
import collections
import csv
import json
import sqlite3
from pathlib import Path


def ancestors(lineage_id: str, parent_of: dict[str, str]) -> list[str]:
    """The lineage, then each node above it: derived "#k2#b" nodes first, then the tree."""
    out = [lineage_id]
    while "#" in out[-1]:
        out.append(out[-1].rsplit("#", 1)[0])
    while (up := parent_of.get(out[-1])) and up not in out:
        out.append(up)
    return out

COLUMNS = ("id", "group", "as_of", "valid_from", "question", "answer", "via", "event_id", "actor_number",
           "operation", "effective_on", "status_reason", "evidence", "after_valid_from", "decision", "note")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data", type=Path, default=Path("data"))
    args = ap.parse_args()

    pending: dict[str, list[dict]] = collections.defaultdict(list)
    for line in (args.data / "derived/provision_events.jsonl").open(encoding="utf-8"):
        ev = json.loads(line)
        if ev.get("status") == "needs_review" and ev.get("effective_on"):
            for pid in ev.get("affected_provision_ids") or ():
                pending[pid].append(ev)

    db = sqlite3.connect(f"file:{args.data / 'temporal.sqlite'}?mode=ro", uri=True)
    parent_of = {pid: parent for pid, parent in db.execute("SELECT id, parent_id FROM provisions") if parent}
    out = []
    for line in (args.data / "derived/vilextime/release.jsonl").open(encoding="utf-8"):
        r = json.loads(line)
        for node in ancestors(r["lineage_id"], parent_of):
            for ev in pending.get(node, ()):
                if ev["effective_on"] > r["as_of"]:
                    continue
                out.append({
                    "id": r["id"], "group": r["group"], "as_of": r["as_of"], "valid_from": r.get("valid_from") or "",
                    "question": r.get("question") or "", "answer": " ".join((r.get("answer") or "").split())[:300],
                    "via": "" if node == r["lineage_id"] else node,
                    "event_id": ev["id"], "actor_number": ev.get("actor_number") or "", "operation": ev["operation"],
                    "effective_on": ev["effective_on"], "status_reason": ev.get("status_reason") or "",
                    "evidence": " ".join((ev.get("evidence") or "").split()),
                    "after_valid_from": "x" if ev["effective_on"] > (r.get("valid_from") or "") else "",
                    "decision": "", "note": "",
                })
    out.sort(key=lambda o: (o["group"], o["id"], o["effective_on"]))

    path = args.data / "review/pending_events.tsv"
    # a re-run keeps what a person already typed
    typed = {(o["id"], o["event_id"]): o for o in csv.DictReader(path.open(encoding="utf-8"), delimiter="\t")
             if o.get("decision") or o.get("note")} if path.exists() else {}
    for o in out:
        if (k := (o["id"], o["event_id"])) in typed:
            o.update(decision=typed[k]["decision"], note=typed[k]["note"])
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS, delimiter="\t", lineterminator="\n")
        w.writeheader()
        w.writerows(out)
    rows = {o["id"]: o["group"] for o in out}
    print(f"{path}: {len(out)} (dòng, event) trên {len(rows)} dòng "
          f"{dict(collections.Counter(rows.values()))}; "
          f"{len({o['id'] for o in out if o['after_valid_from']})} dòng có event sau valid_from")
    print(f"  lý do: {dict(collections.Counter(o['status_reason'] for o in out).most_common())}")


if __name__ == "__main__":
    main()

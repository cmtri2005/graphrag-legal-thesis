#!/usr/bin/env python3
"""ViLexTime — release rows whose gold may be stale because an event was not applied.

`build_versions.py` applies only `auto_accepted` and `verified` events; a
`needs_review` event is logged and left out (phase-3 decision Q2). When such an
event touches a row's provision on or before the row's `as_of`, the gold may
still show the text from before that change (pilot T6 row 9: 104/2022/NĐ-CP
amended khoản 2 Điều 24 NĐ 19/2011 from 2023-01-01, gold kept the old wording).

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
from pathlib import Path

COLUMNS = ("id", "group", "as_of", "valid_from", "question", "answer", "event_id", "actor_number",
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

    out = []
    for line in (args.data / "derived/vilextime/release.jsonl").open(encoding="utf-8"):
        r = json.loads(line)
        for ev in pending.get(r["lineage_id"], ()):
            if ev["effective_on"] > r["as_of"]:
                continue
            out.append({
                "id": r["id"], "group": r["group"], "as_of": r["as_of"], "valid_from": r.get("valid_from") or "",
                "question": r.get("question") or "", "answer": " ".join((r.get("answer") or "").split())[:300],
                "event_id": ev["id"], "actor_number": ev.get("actor_number") or "", "operation": ev["operation"],
                "effective_on": ev["effective_on"], "status_reason": ev.get("status_reason") or "",
                "evidence": " ".join((ev.get("evidence") or "").split()),
                "after_valid_from": "x" if ev["effective_on"] > (r.get("valid_from") or "") else "",
                "decision": "", "note": "",
            })
    out.sort(key=lambda o: (o["group"], o["id"], o["effective_on"]))

    path = args.data / "review/pending_events.tsv"
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

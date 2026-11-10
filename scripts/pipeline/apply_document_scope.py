#!/usr/bin/env python3
"""H5 L2 — end the documents whose repeal the portal never dated (10/11/2026).

`extract_provision_events.py` marks a repeal or replacement of a whole document `auto_accepted`
(`locator` null) when the list's lead-in says the whole text goes and the portal left `effTo` empty
(TT 15/2012/TT-BNV, repealed by TT 12/2023/TT-BNV from 2023-10-01). Everything downstream reads a
document's end from `documents.effective_to` of `data/temporal.sqlite`, so this sets it there, where
it is still empty, to the earliest such date. Run after `extract_provision_events.py` and before
`build_versions.py`; `build_store.py` resets the column, so the order is fixed. Offline, idempotent.

Writes `data/derived/document_scope_applied.jsonl`, one line per document changed.

Usage:
    python scripts/pipeline/apply_document_scope.py
"""
from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path


def apply(events: Path, index: Path, out: Path) -> int:
    first: dict[str, dict] = {}
    for line in events.read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if (row["locator"] is None and row["status"] in ("auto_accepted", "verified") and row["effective_on"]
                and row["operation"] in ("repeal", "replace") and row["target_document_id"]):
            old = first.get(row["target_document_id"])
            if old is None or row["effective_on"] < old["effective_on"]:
                first[row["target_document_id"]] = row
    changed = []
    with sqlite3.connect(index) as db:
        for doc_id, row in sorted(first.items()):
            cur = db.execute("UPDATE documents SET effective_to = ? WHERE id = ? AND effective_to IS NULL "
                             "AND effective_from IS NOT NULL AND effective_from < ?",
                             (row["effective_on"], doc_id, row["effective_on"]))
            if cur.rowcount:
                changed.append({"document_id": doc_id, "effective_to": row["effective_on"], "event_id": row["id"],
                                "actor_id": row["actor_id"], "actor_number": row["actor_number"]})
    out.write_text("".join(json.dumps(c, ensure_ascii=False) + "\n" for c in changed), encoding="utf-8")
    return len(changed)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--data", type=Path, default=Path("data"))
    args = parser.parse_args()
    n = apply(args.data / "derived/provision_events.jsonl", args.data / "temporal.sqlite",
              args.data / "derived/document_scope_applied.jsonl")
    print(f"{n:,} documents ended -> {args.data / 'derived/document_scope_applied.jsonl'}")

#!/usr/bin/env python3
"""ViLexTime — the retrieval corpus every system in the experiments searches (plan phase-4, V2).

Two layers over the same benchmark-eligible documents (ADR 0002), decided 28/09:

  asis.jsonl       layer A, "as published" — what anyone building RAG over the
                   portal has. One unit per provision in its original wording
                   (`asis:<provision id>`), and one per amendment or repeal
                   instruction (`asis:<event id>`): the instruction followed by
                   the wording it quotes. Instructions are units of their own
                   because the provision tree of an amending document drops the
                   quoted wording in about a third of cases, and without them the
                   new wording would exist nowhere a flat baseline can look. An
                   instruction is kept when the document it amends is eligible,
                   even if the amending one is not (its body is missing on the
                   portal): its wording still made the versions of layer B.
                   Baselines B2–B6 and B7 (document-level date filter) use this.
  versions.jsonl   layer B, "by version" — the output of L2–L3: one unit per
                   provision version with its effective intervals. The proposed
                   system and B7+ (version-level date filter, no graph) use this.
  documents.jsonl  every document owning a unit, with its own dates, for
                   document-level filters.
  manifest.json    counts, sha256 of every output and input, the commit.

A release row's `accepted_evidence` names layer-A units; `evidence_set` names
layer-B versions. Offline, deterministic; the files are derived and not committed.

Usage:
    python scripts/pipeline/build_corpus.py
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
import subprocess
from pathlib import Path

BATCH = 5000


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def instruction_text(event: dict) -> str:
    """The instruction as published: its sentence, then each wording it quotes."""
    quoted = [u["new_text"] for u in event.get("text_updates") or [] if u.get("new_text")]
    return "\n".join([event["evidence"].strip(), *(q.strip() for q in quoted)])


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--data", type=Path, default=Path("data"))
    args = parser.parse_args()
    data = args.data
    out = data / "derived/corpus"
    out.mkdir(parents=True, exist_ok=True)

    eligible = {f"document:{r['doc_id']}" for r in map(json.loads, (data / "derived/eligibility.jsonl").open())
                if r["benchmark_eligible"]}
    db = sqlite3.connect(data / "temporal.sqlite")
    counts: dict[str, int] = {}
    events = [e for e in map(json.loads, (data / "derived/provision_events.jsonl").open(encoding="utf-8"))
              if (e["actor_id"] in eligible or e.get("target_document_id") in eligible)
              and (e.get("evidence") or "").strip()]
    owners_of_units = eligible | {e["actor_id"] for e in events}

    with (out / "documents.jsonl").open("w", encoding="utf-8") as f:
        n = 0
        for doc, number, title, issued, eff_from, eff_to, rank in db.execute(
                "SELECT id, number, title, issued_on, effective_from, effective_to, rank FROM documents ORDER BY id"):
            if doc in owners_of_units:
                f.write(json.dumps({"document_id": doc, "law_id": number, "title": title, "issued_on": issued,
                                    "effective_from": eff_from, "effective_to": eff_to, "rank": rank},
                                   ensure_ascii=False) + "\n")
                n += 1
        counts["documents"] = n

    def owners(ids: list[str]) -> dict[str, tuple[str, str]]:
        marks = ",".join("?" * len(ids))
        return {pid: (doc, level) for pid, doc, level
                in db.execute(f"SELECT id, document_id, level FROM provisions WHERE id IN ({marks})", ids)}

    asis_n = versions_n = skipped_added = 0
    with (out / "versions.jsonl").open("w", encoding="utf-8") as vb, \
         (out / "asis.jsonl").open("w", encoding="utf-8") as va:
        batch: list[dict] = []

        def flush() -> None:
            nonlocal asis_n, versions_n, skipped_added
            where = owners(sorted({v["provision_id"] for v in batch}))
            for v in batch:
                doc, level = where.get(v["provision_id"], (None, None))
                if doc not in eligible or not v["text"]:
                    continue
                vb.write(json.dumps({"unit_id": v["id"], "provision_id": v["provision_id"], "document_id": doc,
                                     "level": level, "ordinal": v["ordinal"], "text": v["text"],
                                     "effective_intervals": v["effective_intervals"]}, ensure_ascii=False) + "\n")
                versions_n += 1
                if v["ordinal"] != 1:
                    continue
                if v["created_by_event_id"]:     # inserted by an amendment: it is published in the instruction
                    skipped_added += 1
                    continue
                va.write(json.dumps({"unit_id": f"asis:{v['provision_id']}", "kind": "provision",
                                     "provision_id": v["provision_id"], "document_id": doc, "level": level,
                                     "text": v["text"]}, ensure_ascii=False) + "\n")
                asis_n += 1
            batch.clear()

        for line in (data / "derived/versions.jsonl").open(encoding="utf-8"):   # ~1 GB: stream it
            batch.append(json.loads(line))
            if len(batch) >= BATCH:
                flush()
        flush()

        instructions = 0
        for e in events:
            va.write(json.dumps({"unit_id": f"asis:{e['id']}", "kind": "instruction", "event_id": e["id"],
                                 "operation": e["operation"], "document_id": e["actor_id"],
                                 "target_provision_id": e.get("target_provision_id"),
                                 "text": instruction_text(e)}, ensure_ascii=False) + "\n")
            instructions += 1
    counts.update({"asis_provisions": asis_n, "asis_instructions": instructions,
                   "asis_skipped_inserted_by_amendment": skipped_added, "versions": versions_n})

    inputs = ["derived/versions.jsonl", "derived/provision_events.jsonl", "derived/eligibility.jsonl", "temporal.sqlite"]
    manifest = {
        "snapshot": "v2 (2026-09-17)",
        "commit": subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True).stdout.strip(),
        "counts": counts,
        "outputs": {p.name: sha256(p) for p in sorted(out.glob("*.jsonl"))},
        "inputs": {name: sha256(data / name) for name in inputs},
    }
    (out / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    for key, value in counts.items():
        print(f"  {key}: {value:,}")
    print(f"-> {out}/ (manifest.json)")


if __name__ == "__main__":
    main()

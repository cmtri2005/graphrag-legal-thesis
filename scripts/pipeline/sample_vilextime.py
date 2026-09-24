#!/usr/bin/env python3
"""ViLexTime — which lineages get a question generated (plan D3, decided 24/09).

The quota counts QA rows (ADR 0003 Follow-Up), and about half of what the model
writes fails `validate()`, so each group is sampled to twice its quota in rows
(T3, which keeps fewer, to three times).
Generating for all ~16,500 rows would spend ten thousand calls on a 1,150-row
release.

The order is the point: lineages are shuffled once with a fixed seed and written
ranked. The release later walks this order and keeps the first lineages whose
question passed, until the quota is met — so which lineage made it in is a
function of the seed and the validator, never of a person's pick.

Rules, in order:
* a lineage with any structural `flags` is skipped (ADR 0003 §9);
* at most `PER_DOCUMENT` lineages per document, so T3's 331 chains in 121
  documents do not collapse into a handful of decrees;
* a lineage is never cut between its dates.

T6 is sampled for 150 rows, not 100: its quota also absorbs whatever T5 falls
short of 50 once the legal advisor has ruled (plan, Q3).

Writes `data/derived/vilextime/sample.jsonl`. Offline and deterministic.

`--select` is the second half, run after `generate_questions.py --sample` and
`build_vilextime.py`: it walks the same ranks and writes the records of the
first lineages whose question is the model's (not the template) and whose rows
still fit, to exactly the release quota. T6 is selected at 100 until T5 exists;
its shortfall is added once the legal advisor rules.

Usage:
    python scripts/pipeline/sample_vilextime.py
    python scripts/pipeline/sample_vilextime.py --select
"""
from __future__ import annotations

import argparse
import collections
import json
import random
from pathlib import Path

QUOTA = {"T1": 250, "T2": 400, "T3": 200, "T4": 150, "T6": 150}
RELEASE = {**QUOTA, "T6": 100}   # T5 and T6's share of its shortfall wait for the legal advisor
OVERSAMPLE = {"T1": 2, "T2": 2, "T3": 3, "T4": 2, "T6": 2}   # T3 kept 9 of 22 in the first run
PER_DOCUMENT = 2
SEED = 20260924


def sample(records: list[dict], target: int, seed: int = SEED) -> list[dict]:
    """Ranked lineages whose rows add up to at least `target`."""
    lineages: dict[str, list[dict]] = collections.defaultdict(list)
    for record in records:
        lineages[record["lineage_id"]].append(record)
    order = sorted(lineages)
    random.Random(seed).shuffle(order)

    picked, per_doc, rows = [], collections.Counter(), 0
    for lid in order:
        if rows >= target:
            break
        recs = lineages[lid]
        doc = recs[0]["target"]["document_id"]
        if any(r["flags"] for r in recs) or per_doc[doc] >= PER_DOCUMENT:
            continue
        per_doc[doc] += 1
        rows += len(recs)
        picked.append({"rank": len(picked), "lineage_id": lid, "document_id": doc, "rows": len(recs)})
    return picked


def select(ranked: list[dict], passed: set[str], quota: int) -> list[str]:
    """Lineages in rank order that passed and still fit, until exactly `quota` rows."""
    chosen, left = [], quota
    for p in sorted(ranked, key=lambda p: p["rank"]):
        if left == 0:
            break
        if p["lineage_id"] in passed and p["rows"] <= left:
            chosen.append(p["lineage_id"])
            left -= p["rows"]
    return chosen


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--data", type=Path, default=Path("data"))
    parser.add_argument("--select", action="store_true", help="pick the release rows from sample.jsonl")
    args = parser.parse_args()

    base = args.data / "derived/vilextime"
    if args.select:
        ranked = [json.loads(line) for line in (base / "sample.jsonl").open(encoding="utf-8")]
        total = 0
        with (base / "selected.jsonl").open("w", encoding="utf-8") as out:
            for group, quota in RELEASE.items():
                records = collections.defaultdict(list)
                for line in (base / f"{group}.jsonl").open(encoding="utf-8"):
                    record = json.loads(line)
                    records[record["lineage_id"]].append(record)
                passed = {lid for lid, recs in records.items() if recs[0]["question_source"]["kind"] == "llm"}
                chosen = select([p for p in ranked if p["group"] == group], passed, quota)
                rows = [r for lid in chosen for r in sorted(records[lid], key=lambda r: r["as_of"])]
                total += len(rows)
                print(f"{group}: {len(rows):>4}/{quota} dòng · {len(chosen)} lineage"
                      + ("  << THIẾU, sinh thêm mẫu" if len(rows) < quota else ""))
                for record in rows:
                    out.write(json.dumps(record, ensure_ascii=False) + "\n")
        print(f"tổng {total:,} dòng -> {base / 'selected.jsonl'}")
        return

    with (base / "sample.jsonl").open("w", encoding="utf-8") as out:
        for group, quota in QUOTA.items():
            records = [json.loads(line) for line in (base / f"{group}.jsonl").open(encoding="utf-8")]
            need = quota * OVERSAMPLE[group]
            picked = sample(records, need)
            rows = sum(p["rows"] for p in picked)
            short = "  << THIẾU" if rows < need else ""
            print(f"{group}: {len(picked):>4} lineage · {rows:>4} dòng (cần {need})"
                  f" · {len({p['document_id'] for p in picked})} văn bản{short}")
            for p in picked:
                out.write(json.dumps({"group": group, **p}, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()

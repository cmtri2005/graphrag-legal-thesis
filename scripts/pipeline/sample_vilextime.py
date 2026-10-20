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

Writes `data/vilextime/sample.jsonl`, committed: it is the ranking of record, and
a re-run keeps it (see `sample`). Offline and deterministic given that file.

`--select` is the second half, run after `generate_questions.py --sample` and
`build_vilextime.py`: it walks the same ranks and writes the records of the
first lineages whose question is the model's (not the template) and whose rows
still fit, to exactly the release quota (`RELEASE`); T5 takes only the pairs the
lawyer confirmed. A lineage listed in
`data/vilextime/dropped.jsonl` (review found it unfixable: not a norm, a
truncated source, too few distinct answers) is skipped as if its question had
failed, so the next ranked lineage takes its rows; so is one rule R6 keeps out of test
(`pending_events.blocked`).

Usage:
    python scripts/pipeline/sample_vilextime.py
    python scripts/pipeline/sample_vilextime.py --select
"""
from __future__ import annotations

import argparse
import collections
import csv
import json
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "review"))
from pending_events import blocked  # noqa: E402  rule R6

# T4 merged into T2 (build_question_pool.QUOTA): the same 150 rows ship, told
# apart by the `near_identical` facet instead of by a quota of their own, so the
# release total is unchanged at 1,150.
QUOTA = {"T1": 250, "T2": 550, "T3": 200, "T5": 50, "T6": 150}
# Release rows per group, docs/vilextime-dinh-nghia.md §9 (20/10, CMT): T2 450 is 300 regular
# + T4's 150 near-identical; T6 350 is T6a 100 (direct) + T6b 250 (ancestor, H3). T5 has no
# number: T5a is every pair the lawyer confirmed in data/review/t5_items.tsv, nothing else.
RELEASE = {"T1": 150, "T2": 450, "T3": 150, "T5": None, "T6": 350}
OVERSAMPLE = {"T1": 2, "T2": 2, "T3": 3, "T5": 2, "T6": 2}   # T3 kept 9 of 22 in the first run
PER_DOCUMENT = 2
# T6 has two parts (decided 28/09): "ancestor" — lost force because its Điều,
# Khoản, Mục or Chương was repealed, the case H3 is about — is ranked on its own,
# so the "direct" ranking already on disk is untouched, and takes this many rows
# out of T6's release quota.
T6_ANCESTOR_ROWS = 250   # of RELEASE["T6"]: T6b
# T2 has two parts too (decided 11/10): "near" — a pair whose texts are near-identical
# (`near_identical`, the citation trap T4 was) — is ranked on its own and takes this
# many rows out of T2's quota. Merged into T2 on 07/10 without a quota of its own,
# it sat at the tail of T2's ranking and the release shipped none of it.
T2_NEAR_ROWS = 150       # of RELEASE["T2"]; 75 pairs, the proposal's T4 150
SEED = 20260924
# T5 kinds the adviser excluded on 20/09: corrections, and guidance taking effect
# with the act it details. They stay in the worksheet, not in the release.
EXCLUDED_T5 = {"correction", "guidance_in_sync"}


def sample(records: list[dict], target: int, seed: int = SEED, prior: list[str] = (),
           skip: set[str] = frozenset()) -> list[dict]:
    """Ranked lineages whose rows add up to at least `target`.

    `prior` is the ranking already on disk. It is kept: a lineage that left the
    group is skipped, and only what lies past it comes from the seeded shuffle.
    Reshuffling instead would reorder the whole group whenever one lineage
    moved, and orphan the questions already written for the old order. `skip`
    (dropped, or kept out of test by R6) is left out like a flagged lineage, so no
    question is written for a lineage `--select` would pass over.
    """
    lineages: dict[str, list[dict]] = collections.defaultdict(list)
    for record in records:
        lineages[record["lineage_id"]].append(record)
    kept = [lid for lid in prior if lid in lineages]
    rest = sorted(set(lineages) - set(kept))
    random.Random(seed).shuffle(rest)
    order = kept + rest

    picked, per_doc, rows = [], collections.Counter(), 0
    for lid in order:
        if rows >= target:
            break
        recs = lineages[lid]
        doc = recs[0]["target"]["document_id"]
        excluded = (recs[0].get("retroactive") or {}).get("kind") in EXCLUDED_T5
        if any(r["flags"] for r in recs) or excluded or lid in skip or per_doc[doc] >= PER_DOCUMENT:
            continue
        per_doc[doc] += 1
        rows += len(recs)
        picked.append({"rank": len(picked), "lineage_id": lid, "document_id": doc, "rows": len(recs)})
    return picked


def part_of(row: dict) -> str | None:
    """T6's and T2's two parts; every other group has one. Old ranking lines carry neither mark."""
    if row["group"] == "T6":
        return "ancestor" if row.get("repeal_mode") == "ancestor" else "direct"
    if row["group"] == "T2":
        return "near" if row.get("near_identical") else "regular"
    return None


def parts(group: str, records: list[dict], need: int,
          ancestor_rows: int = T6_ANCESTOR_ROWS) -> list[tuple[str | None, list[dict], int]]:
    if group == "T2":
        near = {r["lineage_id"] for r in records if r.get("near_identical")}
        return [("regular", [r for r in records if r["lineage_id"] not in near], need),
                ("near", [r for r in records if r["lineage_id"] in near], T2_NEAR_ROWS * OVERSAMPLE["T2"])]
    if group != "T6":
        return [(None, records, need)]
    anc = [r for r in records if r.get("repeal_mode") == "ancestor"]
    return [("direct", [r for r in records if r.get("repeal_mode") != "ancestor"], need),
            ("ancestor", anc, ancestor_rows * 2)]


def select(ranked: list[dict], passed: set[str], quota: int) -> list[str]:
    """Lineages in rank order that passed, summing to exactly `quota` rows.

    Taking whatever still fits stranded T3 at 198/200: chains are 3-5 rows, so
    two rows short nothing fits. A lineage is taken only if what is left of the
    quota can still be made exactly from the lineages ranked after it (subset
    sum), which keeps rank order wherever an exact total exists at all.
    """
    pool = [p for p in sorted(ranked, key=lambda p: p["rank"]) if p["lineage_id"] in passed]
    reachable = [set() for _ in range(len(pool) + 1)]
    reachable[-1] = {0}
    for i in range(len(pool) - 1, -1, -1):
        rows = pool[i]["rows"]
        reachable[i] = reachable[i + 1] | {t + rows for t in reachable[i + 1] if t + rows <= quota}
    if quota not in reachable[0]:              # no exact total: fall back to closest from below
        quota = max(reachable[0])
    chosen, left = [], quota
    for i, p in enumerate(pool):
        if left and p["rows"] <= left and left - p["rows"] in reachable[i + 1]:
            chosen.append(p["lineage_id"])
            left -= p["rows"]
    return chosen


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--data", type=Path, default=Path("data"))
    parser.add_argument("--select", action="store_true", help="pick the release rows from sample.jsonl")
    # H3 is the hypothesis T6 "ancestor" carries, and at 24 rows / 12 lineages its
    # interval is about +-25 pp, so it can only illustrate. The pool now holds
    # thousands of candidates (build_question_pool.py --ancestor-quota), so this is
    # the only number left between H3 and a testable hypothesis — but raising it
    # takes rows from T6 "direct" or past Bảng 1's T6 = 100, which is the team's
    # call (report decision 2), so the default is what the release already has.
    parser.add_argument("--ancestor-rows", type=int, default=T6_ANCESTOR_ROWS,
                        help=f"T6 'ancestor' rows in the release (default {T6_ANCESTOR_ROWS})")
    args = parser.parse_args()

    base = args.data / "derived/vilextime"
    ranking = args.data / "vilextime/sample.jsonl"
    dropfile = args.data / "vilextime/dropped.jsonl"
    dropped = ({json.loads(line)["lineage_id"] for line in dropfile.open(encoding="utf-8")}
               if dropfile.exists() else set())
    if args.select:
        ranked = [json.loads(line) for line in ranking.open(encoding="utf-8")]
        with (args.data / "review/t5_items.tsv").open(encoding="utf-8") as f:
            confirmed = {r["lineage_id"] for r in csv.DictReader(f, delimiter="\t")
                         if r["LUẬT SƯ: đáp án mốc sau đúng? (có/không)"].strip().lower() == "có"}
        by_group = {group: [json.loads(line) for line in (base / f"{group}.jsonl").open(encoding="utf-8")]
                    for group in RELEASE}
        stale = blocked([r for rows in by_group.values() for r in rows], args.data)
        total = 0
        with (base / "selected.jsonl").open("w", encoding="utf-8") as out:
            for group, quota in RELEASE.items():
                records = collections.defaultdict(list)
                for record in by_group[group]:
                    records[record["lineage_id"]].append(record)
                llm = {lid for lid, recs in records.items() if recs[0]["question_source"]["kind"] == "llm"}
                passed = llm - dropped - stale
                print(f"{group}: R6 bỏ {len(llm & stale)} lineage có sự kiện chưa áp")
                if group == "T5":
                    passed &= confirmed
                    quota = sum(len(records[lid]) for lid in passed)
                quotas = ({"ancestor": args.ancestor_rows, "direct": quota - args.ancestor_rows} if group == "T6"
                          else {"near": T2_NEAR_ROWS, "regular": quota - T2_NEAR_ROWS} if group == "T2"
                          else {None: quota})
                chosen = [lid for part, q in quotas.items()
                          for lid in select([p for p in ranked if p["group"] == group and part_of(p) == part],
                                            passed, q)]
                rows = [r for lid in chosen for r in sorted(records[lid], key=lambda r: r["as_of"])]
                total += len(rows)
                print(f"{group}: {len(rows):>4}/{quota} dòng · {len(chosen)} lineage"
                      + ("  << THIẾU, sinh thêm mẫu" if len(rows) < quota else ""))
                for record in rows:
                    out.write(json.dumps(record, ensure_ascii=False) + "\n")
        print(f"tổng {total:,} dòng -> {base / 'selected.jsonl'}")
        return

    prior: dict[tuple, list[str]] = collections.defaultdict(list)
    if ranking.exists():
        for line in ranking.open(encoding="utf-8"):
            r = json.loads(line)
            prior[(r["group"], part_of(r))].append(r["lineage_id"])
    lines = []
    by_group = {group: [json.loads(line) for line in (base / f"{group}.jsonl").open(encoding="utf-8")]
                for group in QUOTA}
    skip = dropped | blocked([r for rows in by_group.values() for r in rows], args.data)
    for group, quota in QUOTA.items():
        records = by_group[group]
        for part, part_records, need in parts(group, records, quota * OVERSAMPLE[group], args.ancestor_rows):
            picked = sample(part_records, need, prior=prior[(group, part)], skip=skip)
            rows = sum(p["rows"] for p in picked)
            short = "  << THIẾU" if rows < need else ""
            print(f"{group}{'/' + part if part else ''}: {len(picked):>4} lineage · {rows:>4} dòng (cần {need})"
                  f" · {len({p['document_id'] for p in picked})} văn bản{short}")
            mark = {"ancestor": {"repeal_mode": "ancestor"}, "near": {"near_identical": True}}.get(part, {})
            lines += [json.dumps({"group": group, **mark, **p},
                                 ensure_ascii=False) + "\n" for p in picked]
    ranking.parent.mkdir(parents=True, exist_ok=True)
    ranking.write_text("".join(lines), encoding="utf-8")

if __name__ == "__main__":
    main()

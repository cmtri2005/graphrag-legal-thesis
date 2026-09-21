#!/usr/bin/env python3
"""ViLexTime — candidate questions with their gold answers (plan phase-4, B1–B4).

Every candidate is derived from `data/derived/versions.jsonl`: the gold answer
at a date is the version whose *effective* window contains it, so the label is
a property of the data, not of any model. An LLM later phrases the question in
Vietnamese and never touches the answer (P4.4).

Groups, per the proposal's structure table. T5 is not built here: which
retroactive acts fall under Điều 152 is a legal judgement, and the 95
candidates are waiting on the adviser (plan phase-4, Q3).

  T1  one version, unambiguous in time            control
  T2  two versions: same question, two dates      core group
  T3  three or more versions: A -> B -> C         where the graph should pay
  T4  two versions whose texts are near-identical the citation trap
  T6  a Khoản/Điểm that ended inside a document still in force

A provision lands in exactly one group, scarcest first (T3, then T6, T4, T2,
T1), so no node — and so no text — can appear twice in the benchmark. The
dev/test split is by document for the same reason (Q6) and is left to P4.9.

A candidate must also have a *different* answer at each of its dates, which
11.1% of consecutive version pairs do not: their amendment left the text
character-for-character the same, either because the portal already carried
the amended wording or because the extracted block was that wording. Asking
"what did this say before and after" about those has one answer, so they are
dropped and counted rather than shipped as contrast pairs.

Writes `data/derived/vilextime_pool.jsonl`. Offline, deterministic: delete and
re-run for a byte-identical file.

Usage:
    python scripts/pipeline/build_question_pool.py [--per-group-cap 10]
"""
from __future__ import annotations

import argparse
import collections
import difflib
import json
import random
import sqlite3
from datetime import date, timedelta
from pathlib import Path

ONE_DAY = timedelta(days=1)
# Quota from the proposal; the pool keeps `cap` times as many candidates so the
# hand-check and the adviser can reject freely without starving a group.
QUOTA = {"T1": 250, "T2": 400, "T3": 200, "T4": 150, "T6": 100}
PRIORITY = ("T3", "T6", "T4", "T2", "T1")  # scarcest first
NEAR_IDENTICAL = 0.90
SEED = 20260920


def _d(value: str | None) -> date | None:
    return date.fromisoformat(value) if value else None


def in_force_at(versions: list[dict], at: date) -> dict | None:
    """The version whose effective window contains `at`, per [from, to)."""
    for v in versions:
        start, end = _d(v["effective_from"]), _d(v["effective_to"])
        if start and start <= at and (end is None or at < end):
            return v
    return None


def classify(versions: list[dict], document_ends: date | None, level: str, today: date) -> str | None:
    """Which group this provision's chain can serve, or None."""
    dated = [v for v in versions if v["effective_from"]]
    if len(dated) != len(versions) or not dated:
        return None  # an undated version can never be an answer
    # Scarcest group wins, so a chain that could serve two groups goes to the
    # one that cannot spare it: T3 has 2x its quota, T6 has 22x.
    if len(dated) >= 3:
        return "T3"
    last = dated[-1]
    if (
        last["effective_to"]
        and last["ended_by_event_id"]
        and level in ("Clause", "Point")
        and (document_ends is None or document_ends > today)
    ):
        return "T6"  # ended while its document still stands
    if len(dated) == 2:
        ratio = difflib.SequenceMatcher(None, dated[0]["text"], dated[1]["text"]).ratio()
        return "T4" if ratio >= NEAR_IDENTICAL else "T2"
    return "T1"


def ask_dates(group: str, versions: list[dict], today: date) -> list[date]:
    """The dates a question is asked at — chosen so the answers differ."""
    starts = [_d(v["effective_from"]) for v in versions]
    if group == "T1":
        return [starts[0] + ONE_DAY]
    if group == "T6":
        end = _d(versions[-1]["effective_to"])
        return [end - ONE_DAY, end]
    if group == "T3":
        return [s + ONE_DAY for s in starts]  # one date inside each version
    return [starts[1] - ONE_DAY, starts[1]]  # T2, T4: either side of the switch


def build_row(group: str, provision: dict, versions: list[dict], today: date,
              evidence: dict[str, dict]) -> dict:
    dates = ask_dates(group, versions, today)
    gold = []
    for at in dates:
        hit = in_force_at(versions, at)
        gold.append({
            "as_of": at.isoformat(),
            "in_force": hit is not None,
            "version_id": hit["id"] if hit else None,
            "text": hit["text"] if hit else None,
        })
    events = [v["created_by_event_id"] for v in versions if v["created_by_event_id"]]
    events += [v["ended_by_event_id"] for v in versions if v["ended_by_event_id"]]
    row = {
        "schema_version": 1,
        "id": f"vilextime:{group}:{provision['id']}",
        "group": group,
        "document_id": provision["document_id"],
        "provision_id": provision["id"],
        "level": provision["level"],
        "title": provision["title"],
        "transition_on": versions[-1]["effective_from"] if len(versions) > 1 else None,
        "gold": gold,
        "versions": [
            {k: v[k] for k in ("id", "ordinal", "text", "effective_from", "effective_to")}
            for v in versions
        ],
        "event_ids": sorted(set(events)),
        "evidence": [evidence[e]["evidence"] for e in sorted(set(events)) if e in evidence],
        "actor_numbers": sorted({evidence[e]["actor_number"] for e in set(events) if e in evidence}),
    }
    if group == "T4":
        row["similarity"] = round(
            difflib.SequenceMatcher(None, versions[0]["text"], versions[1]["text"]).ratio(), 4
        )
    return row


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--data", type=Path, default=Path("data"))
    parser.add_argument("--per-group-cap", type=int, default=10,
                        help="keep this many times each group's quota (default 10)")
    parser.add_argument("--today", type=date.fromisoformat, default=date(2026, 9, 20))
    args = parser.parse_args()
    data = args.data

    eligible = {
        f"document:{row['doc_id']}"
        for row in map(json.loads, (data / "derived/eligibility.jsonl").read_text(encoding="utf-8").splitlines())
        if row["benchmark_eligible"]
    }
    db = sqlite3.connect(data / "temporal.sqlite")
    provisions = {
        pid: {"id": pid, "document_id": doc, "level": lvl, "title": title}
        for pid, doc, lvl, title in db.execute("SELECT id, document_id, level, title FROM provisions")
    }
    document_ends = {doc: _d(end) for doc, end in db.execute("SELECT id, effective_to FROM documents")}
    evidence = {}
    for line in (data / "derived/provision_events.jsonl").read_text(encoding="utf-8").splitlines():
        e = json.loads(line)
        evidence[e["id"]] = {"evidence": e["evidence"], "actor_number": e["actor_number"]}

    # One streaming pass: every version of a provision is adjacent in the file.
    buckets: dict[str, list[dict]] = collections.defaultdict(list)
    counts: collections.Counter[str] = collections.Counter()
    current: list[dict] = []

    def flush(rows: list[dict]) -> None:
        if not rows:
            return
        provision = provisions.get(rows[0]["provision_id"])
        if provision is None or provision["document_id"] not in eligible:
            return
        rows.sort(key=lambda v: v["ordinal"])
        group = classify(rows, document_ends.get(provision["document_id"]), provision["level"], args.today)
        if group is None:
            counts["bỏ: phiên bản không có ngày"] += 1
            return
        row = build_row(group, provision, rows, args.today, evidence)
        answers = [(g["in_force"], g["text"]) for g in row["gold"]]
        if len(answers) > 1 and len(set(answers)) != len(answers):
            counts[f"bỏ {group}: đáp án trùng nhau ở các mốc"] += 1
            return
        counts[group] += 1
        buckets[group].append(row)

    for line in (data / "derived/versions.jsonl").read_text(encoding="utf-8").splitlines():
        v = json.loads(line)
        if current and v["provision_id"] != current[0]["provision_id"]:
            flush(current)
            current = []
        current.append(v)
    flush(current)

    out_path = data / "derived/vilextime_pool.jsonl"
    written: collections.Counter[str] = collections.Counter()
    documents: set[str] = set()
    with out_path.open("w", encoding="utf-8") as out:
        for group in PRIORITY:
            rows = sorted(buckets[group], key=lambda r: r["id"])
            cap = QUOTA[group] * args.per_group_cap
            if len(rows) > cap:
                rows = sorted(random.Random(SEED).sample(rows, cap), key=lambda r: r["id"])
            for row in rows:
                out.write(json.dumps(row, ensure_ascii=False) + "\n")
                documents.add(row["document_id"])
            written[group] = len(rows)

    print(f"{sum(written.values()):,} ứng viên -> {out_path}\n")
    print(f"  {'nhóm':<5} {'quota':>6} {'có':>9} {'giữ':>8}   dư")
    for group in ("T1", "T2", "T3", "T4", "T6"):
        have = counts[group]
        margin = have / QUOTA[group]
        print(f"  {group:<5} {QUOTA[group]:>6,} {have:>9,} {written[group]:>8,}   {margin:>5.1f}x")
    print(f"\n  T5: chưa dựng — chờ cố vấn luật xác nhận 95 ứng viên theo Điều 152")
    for key, value in counts.items():
        if key.startswith("bỏ"):
            print(f"  {value:,} {key}")
    print(f"\n  văn bản khác nhau trong pool đã ghi: {len(documents):,}")


if __name__ == "__main__":
    main()

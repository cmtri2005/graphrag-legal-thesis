#!/usr/bin/env python3
"""Fill test 2's short answers into a new release; every other field stays byte-for-byte the same.

`enrich_vilextime.py` reads only `short_answers.jsonl`, so `test2_release.jsonl` lost the short
answers written for test 2 and the scorer then accepted any answer on those rows (ADR 0005,
amendment 04/11). The old release stays: E1 and the Colab prompts name its sha256.

Usage:
    python scripts/review/test2_fill_shorts.py --release data/vilextime/test2_release.jsonl \\
        --shorts data/vilextime/short_answers_test2.jsonl --out data/vilextime/test2_release_v2.jsonl
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "pipeline"))
from enrich_vilextime import check_short_answer  # noqa: E402


def fill(rows: list[dict], shorts: dict[tuple[str, str], str | None]) -> tuple[list[dict], collections.Counter]:
    """New rows with the short answer from `shorts`; a row with an answer must get a valid one."""
    out, stats = [], collections.Counter()
    for row in rows:
        new = dict(row)
        if row["answerable"]:
            short = shorts.get((row["lineage_id"], row["version_id"]))
            if not short:
                raise SystemExit(f"{row['id']}: no short answer")
            if not check_short_answer(short, row["answer"], row["target"].get("lead_in")):
                raise SystemExit(f"{row['id']}: short answer is not a span of the answer or lead-in")
            new["short_answer"] = short
            stats["filled" if not row.get("short_answer") else
                  "same" if row["short_answer"] == short else "replaced"] += 1
        elif row.get("short_answer"):
            raise SystemExit(f"{row['id']}: an unanswerable row has a short answer")
        out.append(new)
    return out, stats


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--release", required=True, type=Path)
    ap.add_argument("--shorts", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    args = ap.parse_args()
    rows = [json.loads(line) for line in args.release.open(encoding="utf-8")]
    shorts = {}
    for line in args.shorts.open(encoding="utf-8"):
        s = json.loads(line)
        key = (s["lineage_id"], s["version_id"])
        if key in shorts and shorts[key] != s["short_answer"]:
            raise SystemExit(f"conflicting short answers for {key}")
        shorts[key] = s["short_answer"]
    out, stats = fill(rows, shorts)
    # the only field allowed to differ
    strip = lambda r: {k: v for k, v in r.items() if k != "short_answer"}  # noqa: E731
    if [strip(r) for r in rows] != [strip(r) for r in out]:
        raise SystemExit("a field other than short_answer changed")
    args.out.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in out), encoding="utf-8")
    print(f"{args.out}: {len(out)} rows, {dict(stats)}, sha256 {hashlib.sha256(args.out.read_bytes()).hexdigest()}")


if __name__ == "__main__":
    main()

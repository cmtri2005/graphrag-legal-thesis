#!/usr/bin/env python3
"""ADR 0006 §5b: how stable are two independent runs of the same generation prompts?

Run 1 is the main result; run 2 only measures stability. For F1–F7 a verdict is "ổn định" when both
confirm.json files give the same one; otherwise "không ổn định" and it counts as "không đủ bằng chứng".
Per system and slice: share of answers that changed, and how many went right→wrong / wrong→right.

    python scripts/eval/compare_runs.py --confirm1 runs/R1/confirm.json --confirm2 runs/R2/confirm.json \\
        --gen1 runs/R1/test --gen2 runs/R2/test --release data/vilextime_final/vilextime.jsonl --split test \\
        --out runs/compare_runs.json
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from confirm_vilextime import FINAL_SLICES
from score_vilextime import correct, load_rows

FAMILY = ("F1", "F2", "F3", "F4", "F5", "F6", "F7")
NOT_ENOUGH = "không đủ bằng chứng"


def stability(c1: dict, c2: dict) -> dict:
    out = {}
    for name in FAMILY:
        a, b = (c.get("results", {}).get(name, {}).get("verdict") for c in (c1, c2))
        same = a == b and a is not None
        out[name] = {"run1": a, "run2": b, "stable": same,
                     "final": a if same else (f"không ổn định, tính như {NOT_ENOUGH}" if a and b else "chưa đủ dữ liệu")}
    return out


def flips(rows: list[dict], p1: dict, p2: dict) -> dict:
    """Per slice: answers changed, and correctness changes between the two runs (run 1 → run 2)."""
    out = {}
    for name, keep in FINAL_SLICES.items():
        cut = [r for r in rows if keep(r) and r["id"] in p1 and r["id"] in p2]
        c1 = [correct(r, p1[r["id"]]) for r in cut]
        c2 = [correct(r, p2[r["id"]]) for r in cut]
        changed = sum(p1[r["id"]].get("answer") != p2[r["id"]].get("answer")
                      or p1[r["id"]].get("answerable") != p2[r["id"]].get("answerable") for r in cut)
        out[name] = {"rows": len(cut), "answer_changed": changed,
                     "right_to_wrong": sum(a and not b for a, b in zip(c1, c2)),
                     "wrong_to_right": sum(b and not a for a, b in zip(c1, c2)),
                     "rate_changed": changed / len(cut) if cut else None}
    return out


def systems_in(folder: Path) -> set[str]:
    return {p.stem for p in folder.glob("*.jsonl") if not p.name.endswith(".sample.jsonl")}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--confirm1", type=Path, required=True)
    ap.add_argument("--confirm2", type=Path, required=True)
    ap.add_argument("--gen1", type=Path, required=True, help="predictions of run 1, <system>.jsonl")
    ap.add_argument("--gen2", type=Path, required=True)
    ap.add_argument("--release", type=Path, required=True)
    ap.add_argument("--split", required=True, choices=("dev", "test"))
    ap.add_argument("--out", type=Path)
    args = ap.parse_args()

    c1, c2 = (json.loads(p.read_text(encoding="utf-8")) for p in (args.confirm1, args.confirm2))
    rows = [r for r in load_rows(args.release) if r.get("split") == args.split and r["as_of_strategy"] == "giua_khoang"]
    read = lambda folder, s: {p["id"]: p for p in map(json.loads, (folder / f"{s}.jsonl").open(encoding="utf-8"))}  # noqa: E731
    systems = sorted(systems_in(args.gen1) & systems_in(args.gen2))
    result = {"split": args.split, "stability": stability(c1, c2),
              "flips": {s: flips(rows, read(args.gen1, s), read(args.gen2, s)) for s in systems},
              "only_in_one_run": sorted(systems_in(args.gen1) ^ systems_in(args.gen2))}
    for name, v in result["stability"].items():
        print(f"{name}: lần 1 {v['run1']} · lần 2 {v['run2']} → {'ổn định' if v['stable'] else 'không ổn định'}: {v['final']}")
    for s in systems:
        f = result["flips"][s]["all"]
        print(f"{s:10} all: {f['answer_changed']}/{f['rows']} câu đổi ({f['rate_changed']:.3f}), "
              f"đúng→sai {f['right_to_wrong']}, sai→đúng {f['wrong_to_right']}")
    if args.out:
        args.out.write_text(json.dumps(result, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        print(f"-> {args.out}")


if __name__ == "__main__":
    main()

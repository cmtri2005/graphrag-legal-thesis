#!/usr/bin/env python3
"""Bảng T6 tách có/không đáp án (dev, chỉ đọc; không gọi API, không đổi scorer).

    python scripts/eval/t6_breakdown.py [--run runs/rebuild_20261110_dev] [--release data/vilextime_dataset_h6/vilextime.jsonl]

Điểm gọi thẳng score_vilextime.score (units_of đọc ~1 GB versions.jsonl theo luồng). Assert: Accuracy và
Recall@10 T6 gộp tính lại khớp all.score.json.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import score_vilextime as sv  # noqa: E402


def jl(path):
    return [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines() if line]


def event_rank(row: dict, prompt_ids: list[str]) -> int | None:
    """Hạng (từ 1) của lệnh bãi bỏ gold trong prompt `retrieved`; None nếu không có."""
    ev = row["accepted_evidence"][0]
    return prompt_ids.index(ev) + 1 if ev in prompt_ids else None


def breakdown(rows, preds, prompts, units) -> dict:
    """Điểm bằng chính `score_vilextime.score` trên từng vế; hạng lệnh bãi bỏ đọc từ prompt."""
    has = [r for r in rows if r["answerable"]]
    no = [r for r in rows if not r["answerable"]]
    co, kh, both = (sv.score(x, preds, units) for x in (has, no, rows))
    present = [x for x in (event_rank(r, prompts[r["id"]]["retrieved"]) for r in no) if x]
    return {"n_co": len(has), "acc_co": co["accuracy"], "r10_co": co["recall@10"],
            "n_khong": len(no), "acc_khong": kh["accuracy"], "r10_khong": kh["recall@10"],
            "all": both, "event_trong_prompt": len(present), "hang": sorted(set(present))}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", default="runs/rebuild_20261110_dev")
    ap.add_argument("--release", default="data/vilextime_dataset_h6/vilextime.jsonl")
    ap.add_argument("--data", default="data")
    a = ap.parse_args()
    run = Path(a.run)
    allrows = sv.load_rows(Path(a.release))
    extra = sv.distractors(allrows)
    for r in allrows:
        r["_distractors"] = extra.get(r["id"], [])
    rows = [r for r in allrows if r["group"] == "T6" and r["split"] == "dev" and r["as_of_strategy"] == "giua_khoang"]
    keep = {r["id"] for r in rows}
    score = json.load(open(run / "all.score.json"))
    runs = {p.stem: {x["id"]: x for x in jl(p) if x["id"] in keep}
            for p in sorted((run / "dev").glob("*.jsonl")) if not p.name.endswith(".sample.jsonl")}
    units, _, _ = sv.units_of(Path(a.data), runs)
    print("| Hệ | T6 có đáp án: n | Accuracy | R@10 | T6 không đáp án: n | Accuracy (nói không) | R@10 | lệnh bãi bỏ trong prompt | hạng |")
    print("|---|---|---|---|---|---|---|---|---|")
    for s, preds in runs.items():
        prompts = {x["id"]: x for x in jl(run / "prompts" / f"{s}.jsonl")}
        b = breakdown(rows, preds, prompts, units)
        t6 = score[s]["giua_khoang"]["T6"]
        for m in ("accuracy", "recall@10"):
            assert abs(b["all"][m] - t6[m]) < 1e-9, (s, m, b["all"][m], t6[m])
        c, k = round(b["acc_co"] * b["n_co"]), round(b["acc_khong"] * b["n_khong"])
        print(f"| {s} | {b['n_co']} | {b['acc_co']:.3f} ({c}/{b['n_co']}) | {b['r10_co']:.3f} | "
              f"{b['n_khong']} | {b['acc_khong']:.3f} ({k}/{b['n_khong']}) | {b['r10_khong']:.3f} | "
              f"{b['event_trong_prompt']}/{b['n_khong']} | {','.join(map(str, b['hang'])) or '-'} |")


if __name__ == "__main__":
    main()

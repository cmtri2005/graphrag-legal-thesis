#!/usr/bin/env python3
"""X8 mở rộng: so cũ / C0 / C1 trên 21 dòng T6 không đáp án dev (chẩn đoán dùng gold, không phải hệ).

    python scripts/eval/x8_t6_report.py [--out runs/x8_t6_dev_20261111]
Đúng = score_vilextime.correct (nói "HIỆU LỰC: không"). Bootstrap theo dòng (mỗi dòng một lineage), B=2000.
"""
from __future__ import annotations

import argparse
import json
import random
import sys
from math import comb
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import score_vilextime as sv  # noqa: E402

SEED, B = 20261111, 2000


def mcnemar_exact(b: int, c: int) -> float:
    """Hai phía, kiểm định nhị thức chính xác trên các cặp bất đồng."""
    n = b + c
    return min(1.0, 2 * sum(comb(n, k) for k in range(min(b, c) + 1)) / 2**n) if n else 1.0


def paired_ci(a: list[int], b: list[int]) -> tuple[float, float, float]:
    """Hiệu trung bình b - a và KTC bootstrap 95% (percentile)."""
    rng, n = random.Random(SEED), len(a)
    d = [y - x for x, y in zip(a, b)]
    diffs = sorted(sum(d[rng.randrange(n)] for _ in range(n)) / n for _ in range(B))
    return sum(d) / n, diffs[int(0.025 * B)], diffs[int(0.975 * B) - 1]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="runs/x8_t6_dev_20261111")
    ap.add_argument("--run", default="runs/rebuild_20261110_dev")
    ap.add_argument("--release", default="data/vilextime_dataset_h6/vilextime.jsonl")
    a = ap.parse_args()
    out = Path(a.out)
    rd = lambda p: {x["id"]: x for x in map(json.loads, open(p, encoding="utf-8"))}  # noqa: E731
    rows = [r for r in sv.load_rows(Path(a.release))
            if r["group"] == "T6" and r["split"] == "dev" and r["as_of_strategy"] == "giua_khoang" and not r["answerable"]]
    assert len(rows) == 21
    cond = {"cu": rd(f"{a.run}/dev/proposed2.jsonl"), "C0": rd(out / "dev_C0.jsonl"), "C1": rd(out / "dev_C1.jsonl")}
    change = {x["id"]: x for x in json.loads((out / "c1_changes.json").read_text(encoding="utf-8"))}
    ok = {k: [int(sv.correct(r, p[r["id"]])) for r in rows] for k, p in cond.items()}
    print("| dòng | thao tác C1 | cũ | C0 | C1 |\n|---|---|---|---|---|")
    for i, r in enumerate(rows):
        c = change[r["id"]]
        act = "chuyển (hạng %d)" % c["old_rank"] if c["action"] == "chuyen" else "chèn"
        print(f"| {r['id'].replace('vilextime:T6:provision:', '')[:8]}…{r['id'][-10:]} | {act} | "
              + " | ".join("đúng" if ok[k][i] else "sai" for k in ("cu", "C0", "C1")) + " |")
    print("tổng đúng:", {k: f"{sum(v)}/21" for k, v in ok.items()})
    print("C0 khác cũ (đúng/sai):", sum(x != y for x, y in zip(ok["cu"], ok["C0"])),
          "| câu trả lời khác chữ:", sum(cond["cu"][r["id"]]["answer"] != cond["C0"][r["id"]]["answer"] or
                                        cond["cu"][r["id"]]["answerable"] != cond["C0"][r["id"]]["answerable"] for r in rows))
    for x, y in (("C0", "C1"), ("cu", "C0"), ("cu", "C1")):
        b = sum(p == 1 and q == 0 for p, q in zip(ok[x], ok[y]))      # x đúng, y sai
        c = sum(p == 0 and q == 1 for p, q in zip(ok[x], ok[y]))      # x sai, y đúng
        d, lo, hi = paired_ci(ok[x], ok[y])
        print(f"{y} - {x}: +{c} -{b}, hiệu {d:+.3f} [{lo:+.3f}; {hi:+.3f}], McNemar chính xác p={mcnemar_exact(b, c):.3f}")
    for name in ("chuyen", "chen"):
        idx = [i for i, r in enumerate(rows) if change[r["id"]]["action"] == name]
        print(name, len(idx), {k: sum(ok[k][i] for i in idx) for k in ok})


if __name__ == "__main__":
    main()

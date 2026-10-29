#!/usr/bin/env python3
"""ViLexTime — mẫu 50 dòng nhãn agent cho luật sư kiểm (định nghĩa mục 6, điều 2).

    python scripts/review/agent_sample.py            # ghi data/review/luat_su_kiem_agent.xlsx
    python scripts/review/agent_sample.py --load data/review/luat_su_kiem_agent_da_chot.xlsx
                                                     # nạp phiếu đã điền -> luat_su_kiem_agent.tsv
    python scripts/review/agent_sample.py --q2       # ghi luat_su_kiem_q2.xlsx: mọi dòng A `dat` / agent
                                                     # `khong_dat` luật sư chưa xem (29/10, sau mẫu 50 dòng)

Rút ngẫu nhiên 50 dòng từ data/review/kiem_agent.tsv (seed cố định). Phiếu không cho thấy nhãn của A, để
luật sư đánh giá nhãn agent độc lập. Luật sư điền cột `dong_y` (dong_y / khong_dong_y) và `ly_do`.
"""
from __future__ import annotations

import argparse
import csv
import math
import random
import sys
from pathlib import Path

from openpyxl import Workbook, load_workbook

csv.field_size_limit(sys.maxsize)
SEED, N, CAP = "luat-su-agent-2710", 50, 3000
SHOW = ("id", "group", "question", "as_of", "answer", "short_answer", "citation", "trich_van_ban_goc",
        "trich_van_ban_tac_dong", "cac_phien_ban")


def read(p: Path) -> list[dict]:
    with p.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f, delimiter="\t"))


def sample(agent: list[dict], n: int = N) -> list[dict]:
    return random.Random(SEED).sample(sorted(agent, key=lambda r: r["id"]), min(n, len(agent)))


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    p, d = k / n, 1 + z * z / n
    c, h = (p + z * z / (2 * n)) / d, z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return c - h, c + h


def load(sheet: Path, out: Path) -> None:
    """Phiếu luật sư -> nhãn luật sư theo dòng (export_release.py đọc như hoa_giai_kiem.tsv), gộp theo id
    với các phiếu đã nạp trước.

    Lấy `ket_luan_chot`. Mã lý do của dòng `khong_dat` lấy của agent khi luật sư cũng `khong_dat`
    (lý do của luật sư là văn tự do), ngược lại là `other`."""
    rows = list(load_workbook(sheet, read_only=True)["kiem_agent"].iter_rows(values_only=True))
    rows = [dict(zip(rows[0], r)) for r in rows[1:]]
    if any(r["ket_luan_chot"] not in ("dat", "khong_dat") for r in rows):
        raise SystemExit("ket_luan_chot phải là dat hoặc khong_dat ở mọi dòng")
    head = ["id", "verdict", "reasons", "note", "adjudicator"]
    merged = {r["id"]: r for r in read(out)} if out.exists() else {}
    for r in rows:
        v = r["ket_luan_chot"]
        reasons = "" if v == "dat" else (r["agent_reasons"] if r["agent_verdict"] == v else "other")
        merged[r["id"]] = dict(zip(head, [r["id"], v, reasons, " ".join(str(r["ly_do"] or "").split()),
                                          "luật sư (mẫu agent)"]))
    with out.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, head, delimiter="\t")
        w.writeheader()
        w.writerows(merged[i] for i in sorted(merged))
    k = sum(r["ket_luan_chot"] == r["agent_verdict"] for r in rows)
    lo, hi = wilson(k, len(rows))
    print(f"luật sư đồng ý với agent {k}/{len(rows)}, Wilson 95% [{lo:.3f}; {hi:.3f}] -> {out}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--load", type=Path, help="phiếu luật sư đã điền")
    ap.add_argument("--q2", action="store_true", help="phiếu các dòng A và agent lệch, luật sư chưa xem")
    args = ap.parse_args()
    review = Path("data/review")
    if args.load:
        load(args.load, review / "luat_su_kiem_agent.tsv")
        return
    agent = read(review / "kiem_agent.tsv")
    a = {r["id"]: r for r in read(review / "kiem_A.tsv")}
    if args.q2:
        seen = {r["id"] for r in read(review / "luat_su_kiem_agent.tsv")}
        rows = sorted((r for r in agent if r["verdict"] == "khong_dat" and r["id"] not in seen
                       and a.get(r["id"], {}).get("verdict") == "dat"), key=lambda r: r["id"])
        out, extra = review / "luat_su_kiem_q2.xlsx", ["ket_luan_chot", "do_tin_cay"]
    else:
        rows, out, extra = sample(agent), review / "luat_su_kiem_agent.xlsx", []
    wb = Workbook()
    ws = wb.active
    ws.title = "kiem_agent"
    ws.append([*SHOW, "agent_verdict", "agent_reasons", "agent_note", "dong_y", "ly_do", *extra])
    for r in rows:
        src = a[r["id"]]
        ws.append([*(str(src.get(k, ""))[:CAP] for k in SHOW), r["verdict"], r["reasons"], r["note"],
                   "", "", *[""] * len(extra)])
    wb.save(out)
    print(f"{len(rows)} dòng -> {out}")


if __name__ == "__main__":
    main()

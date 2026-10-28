#!/usr/bin/env python3
"""ViLexTime — mẫu 50 dòng nhãn agent cho luật sư kiểm (định nghĩa mục 6, điều 2).

    python scripts/review/agent_sample.py            # ghi data/review/luat_su_kiem_agent.xlsx

Rút ngẫu nhiên 50 dòng từ data/review/kiem_agent.tsv (seed cố định). Phiếu không cho thấy nhãn của A, để
luật sư đánh giá nhãn agent độc lập. Luật sư điền cột `dong_y` (dong_y / khong_dong_y) và `ly_do`.
"""
from __future__ import annotations

import csv
import random
import sys
from pathlib import Path

from openpyxl import Workbook

csv.field_size_limit(sys.maxsize)
SEED, N, CAP = "luat-su-agent-2710", 50, 3000
SHOW = ("id", "group", "question", "as_of", "answer", "short_answer", "citation", "trich_van_ban_goc",
        "trich_van_ban_tac_dong", "cac_phien_ban")


def read(p: Path) -> list[dict]:
    with p.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f, delimiter="\t"))


def sample(agent: list[dict], n: int = N) -> list[dict]:
    return random.Random(SEED).sample(sorted(agent, key=lambda r: r["id"]), min(n, len(agent)))


def main() -> None:
    review = Path("data/review")
    agent = read(review / "kiem_agent.tsv")
    a = {r["id"]: r for r in read(review / "kiem_A.tsv")}
    rows = sample(agent)
    wb = Workbook()
    ws = wb.active
    ws.title = "kiem_agent"
    head = [*SHOW, "agent_verdict", "agent_reasons", "agent_note", "dong_y", "ly_do"]
    ws.append(head)
    for r in rows:
        src = a[r["id"]]
        ws.append([*(str(src.get(k, ""))[:CAP] for k in SHOW), r["verdict"], r["reasons"], r["note"], "", ""])
    out = review / "luat_su_kiem_agent.xlsx"
    wb.save(out)
    print(f"{len(rows)} dòng -> {out}")


if __name__ == "__main__":
    main()

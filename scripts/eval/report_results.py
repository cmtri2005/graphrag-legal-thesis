#!/usr/bin/env python3
"""Turn score files (score_vilextime.py --out) and confirm.json into the Markdown results table.

Plan codex-chot-du-lieu-va-thuc-nghiem B4. Per score file: the main table (`giua_khoang`, all main
groups), accuracy by group, and the paired differences the scorer already computed. Then XN1–XN9
with Holm. Nothing is recomputed: the numbers are the ones the scorer and confirm wrote.

Usage:
    python scripts/eval/report_results.py runs/E1_ladder/test/ladder.score.json ... \
        --confirm runs/confirm_test.json --out docs/reports/ket_qua_test.md
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from confirm_vilextime import FAMILY, TESTS

MODE = "giua_khoang"
GROUPS = ("T1", "T2", "T3", "T6")
MAIN = (("accuracy", "Acc"), ("accuracy_lenient", "Acc lỏng"), ("tv_recall@1", "TV-R@1"),
        ("recall@1", "R@1"), ("tver", "TVER"), ("wrong_version", "Sai phiên bản"),
        ("citation_coverage", "Phủ trích dẫn"))
DIFF = ("accuracy", "tv_recall@1", "tver")


def num(x: float | None, sign: bool = False) -> str:
    return "—" if x is None else (f"{x:+.3f}" if sign else f"{x:.3f}").replace(".", ",")


def ci(c: list[float] | None, sign: bool = False) -> str:
    return "" if not c else f" [{num(c[0], sign)}; {num(c[1], sign)}]"


def score_section(path: Path) -> list[str]:
    data = json.loads(path.read_text(encoding="utf-8"))
    systems = [k for k in data if " − " not in k]
    diffs = [k for k in data if " − " in k]
    rows = data[systems[0]][MODE]["all"]["rows"]
    out = [f"## `{path}`", "", f"Chế độ `{MODE}`, {rows} dòng (T1, T2, T3, T6). KTC 95% bootstrap theo lineage.",
           "", "| Hệ | " + " | ".join(h for _, h in MAIN) + " |", "|---" * (len(MAIN) + 1) + "|"]
    for s in systems:
        a = data[s][MODE]["all"]
        cells = [num(a[m]) + (ci(a["ci95"].get(m)) if m == "accuracy" else "") for m, _ in MAIN]
        out.append(f"| `{s}` | " + " | ".join(cells) + " |")
    out += ["", "Acc theo nhóm (số dòng trong ngoặc):", "",
            "| Hệ | " + " | ".join(f"{g} ({data[systems[0]][MODE][g]['rows']})" for g in GROUPS) + " |",
            "|---" * (len(GROUPS) + 1) + "|"]
    out += [f"| `{s}` | " + " | ".join(num(data[s][MODE][g]["accuracy"]) for g in GROUPS) + " |"
            for s in systems]
    if diffs:
        out += ["", "Hiệu ghép cặp với hệ đứng trước trong file (KTC 95%):", "",
                "| So sánh | " + " | ".join(DIFF) + " |", "|---" * (len(DIFF) + 1) + "|"]
        for k in diffs:
            d = data[k][MODE]["all"]
            out.append(f"| {k} | " + " | ".join(num(d[m], True) + ci(d["ci95"].get(m), True) for m in DIFF) + " |")
    return out + [""]


def confirm_section(path: Path) -> list[str]:
    data = json.loads(path.read_text(encoding="utf-8"))
    out = [f"## XN1–XN9 (`{path}`)", "",
           f"{data['draws']:,} lần lấy mẫu lại".replace(",", ".") + f", Holm trên {data['tests_run']}/{len(FAMILY)} kiểm định"
           + ("" if data["tests_run"] == len(FAMILY) else " (**chưa đủ họ**)")
           + "; XN5–XN7 là thăm dò, ngoài Holm (ADR 0005 §1).", "",
           "| XN | Giả thuyết | So sánh · thước đo · lát | Ước lượng [KTC 95%] | p | p Holm | Kết luận | Dòng/lineage |",
           "|---|---|---|---|---|---|---|---|"]
    for name, hypothesis, _, metric, slices, _, systems, _ in TESTS:
        what = f"{' − '.join(f'`{s}`' for s in reversed(systems))} · {metric} · {'/'.join(slices)}"
        r = data["results"].get(name)
        if r is None or r.get("p") is None:
            out.append(f"| {name} | {hypothesis} | {what} | chưa chạy | | | | |")
            continue
        size = ", ".join(f"{r['rows'][s]}/{r['lineages'][s]}" for s in slices)
        out.append(f"| {name} | {hypothesis} | {what} | {num(r['estimate'], True)}{ci(r['ci95'], True)} | "
                   f"{num(r['p'])} | {num(r.get('p_holm'))} | {r.get('verdict', '—')} | {size} |")
    return out + [""]


def render(scores: list[Path], confirm: Path | None) -> str:
    splits = {json.loads(confirm.read_text(encoding="utf-8"))["split"]} if confirm else set()
    splits |= {"dev" for p in scores if "/dev/" in str(p)}
    lines = ["# Kết quả ViLexTime", ""]
    if splits != {"test"}:
        lines += ["> **Số dev**, chỉ để kiểm đường ống. Không dùng để kết luận cho tới khi có số `test`.", ""]
    for p in scores:
        lines += score_section(p)
    if confirm:
        lines += confirm_section(confirm)
    return "\n".join(lines)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("scores", nargs="+", type=Path)
    ap.add_argument("--confirm", type=Path)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    args.out.write_text(render(args.scores, args.confirm), encoding="utf-8")
    print(f"-> {args.out}")


if __name__ == "__main__":
    main()

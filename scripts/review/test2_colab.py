#!/usr/bin/env python3
"""Đưa việc gọi model của test2 lên Colab; dựng gói và chấm vẫn ở máy (docs/plans/active/vilextime-test2.md).

    # máy: gói → một file đầu vào cho Colab
    test2_colab.py export filter   --packs ~/vilextime_loc/gan4/packs --guide ~/vilextime_loc/gan4/HUONG_DAN.md --out colab_in
    test2_colab.py export question --packs QPACKS --guide HUONG_DAN.md --out colab_in
    test2_colab.py export rewrite  --tasks rewrite/tasks.jsonl --guide HUONG_DAN.md --out colab_in   # có da_viet, ly_do
    # Colab: notebooks/colab_test2_llm.ipynb đọc inputs.jsonl, ghi raw.jsonl (mỗi dòng một mục, có checkpoint)
    # máy: raw → result.tsv (lọc) hoặc answers.jsonl (câu hỏi), kèm danh sách mục hỏng định dạng
    test2_colab.py import filter   --raw raw.jsonl --out result.tsv
    test2_colab.py import question --raw raw.jsonl --out answers.jsonl

Gói không có khóa, nhãn hay đáp án, nên Colab không thấy mục nào là hiệu chuẩn. Model nhỏ chỉ được dùng cho bộ lọc
nếu qua hiệu chuẩn: `test2_packs.py score` trên result.tsv (≥ 0,80 loại đúng, ≤ 0,30 loại nhầm). Không qua thì kết
quả không dùng, không chỉnh lời dặn để vừa số.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

CODES = {"reference_only", "gold_wrong", "superseded_by_other_norm", "restructuring_2025", "transitional_rule",
         "cosmetic_only", "rename_only", "auto_reference_update", "single_change", "relocated",
         "relocation_unclear", "other"}
TAIL = {"filter": "\n\nTrả lời đúng MỘT dòng, bốn cột cách nhau bằng ký tự TAB, không giải thích thêm:\n"
                  "quyet_dinh<TAB>ma<TAB>can_cu<TAB>ghi_chu\n(quyet_dinh là giu hoặc loai; ma trống khi giu.)",
        "question": "\n\nChỉ trả lời một dòng duy nhất: câu hỏi, kết thúc bằng dấu hỏi, hoặc KHONG_DU_NGU_CANH.",
        }
TAIL["rewrite"] = TAIL["question"]


def jsonl(path: Path) -> list[dict]:
    return [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]


def export(args) -> None:
    guide = args.guide.read_text(encoding="utf-8")
    if args.kind == "rewrite":
        rows = jsonl(args.tasks)
        user = lambda r: (r["dau_vao"] + f"\n\nCÂU ĐÃ VIẾT (bị loại): {r['da_viet']}\nLÝ DO BỊ LOẠI: {r['ly_do']}\n"
                          "Viết một câu mới khắc phục lý do trên.")
    else:
        rows = [r for p in sorted(args.packs.glob("pack_*.jsonl")) for r in jsonl(p)]
        user = (lambda r: json.dumps(r, ensure_ascii=False)) if args.kind == "filter" else (lambda r: r["dau_vao"])
    args.out.mkdir(parents=True, exist_ok=True)
    system = guide + TAIL[args.kind]
    with (args.out / "inputs.jsonl").open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps({"item": r["item"], "system": system, "user": user(r)}, ensure_ascii=False) + "\n")
    sha = hashlib.sha256((args.out / "inputs.jsonl").read_bytes()).hexdigest()
    (args.out / "manifest.json").write_text(json.dumps({"kind": args.kind, "n": len(rows), "guide_sha256": hashlib.sha256(
        guide.encode()).hexdigest(), "inputs_sha256": sha}, indent=1), encoding="utf-8")
    print(f"{len(rows)} mục -> {args.out}/inputs.jsonl (sha256 {sha[:12]}…)")


def parse_filter(text: str) -> tuple | None:
    line = next((l for l in text.strip().splitlines() if "\t" in l), "")
    cols = [c.strip() for c in line.split("\t")]
    cols += [""] * (4 - len(cols))
    dec, code, why, note = cols[:4]
    if dec == "giu" and not code or dec == "loai" and code in CODES and note:
        return dec, code, why, note
    return None


def parse_question(text: str) -> str | None:
    t = text.strip().strip('"').strip()
    t = re.sub(r"^(Câu hỏi|Question)\s*:\s*", "", t)
    if t == "KHONG_DU_NGU_CANH" or (t.endswith("?") and "\n" not in t):
        return t
    return None


def import_raw(args) -> None:
    raw = {r["item"]: r for r in jsonl(args.raw)}      # dòng sau đè dòng trước
    bad, ok = [], []
    for item, r in raw.items():
        v = parse_filter(r["output"]) if args.kind == "filter" else parse_question(r["output"])
        (ok if v else bad).append((item, v, r["output"]))
    if args.kind == "filter":
        lines = ["item\tquyet_dinh\tma\tcan_cu\tghi_chu"]
        lines += ["\t".join((i, *(c.replace("\t", " ").replace("\n", " ") for c in v))) for i, v, _ in ok]
        args.out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    else:
        args.out.write_text("".join(json.dumps({"item": i, "question": v}, ensure_ascii=False) + "\n"
                                    for i, v, _ in ok), encoding="utf-8")
    (args.out.parent / (args.out.stem + ".hong.jsonl")).write_text(
        "".join(json.dumps({"item": i, "output": o}, ensure_ascii=False) + "\n" for i, _, o in bad), encoding="utf-8")
    print(f"{len(ok)} hợp lệ -> {args.out}; {len(bad)} hỏng định dạng -> {args.out.stem}.hong.jsonl (chạy lại riêng, không tự sửa)")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    e = sub.add_parser("export")
    e.add_argument("kind", choices=("filter", "question", "rewrite"))
    e.add_argument("--packs", type=Path)
    e.add_argument("--tasks", type=Path)
    e.add_argument("--guide", type=Path, required=True)
    e.add_argument("--out", type=Path, required=True)
    i = sub.add_parser("import")
    i.add_argument("kind", choices=("filter", "question"))
    i.add_argument("--raw", type=Path, required=True)
    i.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()
    export(a) if a.cmd == "export" else import_raw(a)

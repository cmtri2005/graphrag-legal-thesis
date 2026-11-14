#!/usr/bin/env python3
"""REFACTOR_PLAN 1.5 nối tiếp: phiếu chấm lại sai phiên bản, CÓ hiện mọi phiên bản của điều khoản.

Phiếu 1.5 chỉ hiện bản tại mốc, nên người chấm không tách được sai phiên bản khỏi sai nội dung.
Phiếu này lấy lại từ phiếu đã chấm:
  - mọi dòng scorer gắn cờ `wrong_version`;
  - mọi dòng `b1` người gán `sai_noi_dung` mà điều khoản có hơn một phiên bản.
Ẩn tên hệ, cờ scorer và nhãn cũ; xáo thứ tự có seed. Không gọi model.

    PYTHONPATH=src .venv/bin/python scripts/review/version_recheck_sheet.py \\
        --g4 runs/final_g4_20261112/r1/test --release data/vilextime_final/vilextime.jsonl \\
        --versions data/derived/corpus/versions.jsonl \\
        --filled data/review/human_score_g4/phieu_cham_da_cham.xlsx \\
        --out data/review/human_score_g4/recheck_versions/
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "eval"))
import score_vilextime as sv  # noqa: E402
from human_answer_sheet import SYSTEMS  # noqa: E402

LABELS = "dung | sai_phien_ban | sai_noi_dung"
COLUMNS = ("stt", "cau_hoi", "moc", "cac_phien_ban", "tra_loi_cua_he", "nhan_nguoi", "ghi_chu")


def flagged(row: dict, pred: dict, distractors: list[str]) -> bool:
    said = f" {sv.norm(pred.get('answer') if pred.get('answerable') is not False else '')} "   # như row_scores
    return row["answerable"] and any(f" {d} " in said for d in distractors)


def show_versions(chain: list[dict], when: str) -> str:
    """Mọi phiên bản theo thứ tự, đánh dấu bản áp dụng tại mốc."""
    parts = []
    for v in sorted(chain, key=lambda v: int(v["ordinal"])):
        spans = "; ".join(f"{i['start']} → {i['end'] or 'nay'}" for i in v["effective_intervals"])
        here = sv.in_force([(i["start"], i["end"]) for i in v["effective_intervals"]], when)
        parts.append(f"[Bản {v['ordinal']}, hiệu lực {spans}{' — ÁP DỤNG TẠI MỐC' if here else ''}]\n{v['text']}")
    return "\n\n".join(parts)


def pick(sheet: list[tuple], key: list[dict], rows: dict, preds: dict, extra: dict, chains: dict) -> list[tuple[dict, str]]:
    out = []
    for line, k in zip(sheet, key):
        r, p = rows[k["id"]], preds[k["system"]][k["id"]]
        if flagged(r, p, extra.get(r["id"], [])):
            out.append((k, "wrong_version"))
        elif k["system"] == "b1" and line[6] == "sai_noi_dung" and len(chains.get(r["lineage_id"], [])) > 1:
            out.append((k, "b1_sai_noi_dung"))
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    for name in ("--g4", "--release", "--versions", "--filled", "--out"):
        ap.add_argument(name, type=Path, required=True)
    ap.add_argument("--seed", type=int, default=20261114)
    args = ap.parse_args()

    from openpyxl import Workbook, load_workbook
    from openpyxl.styles import Alignment, Font

    release = sv.load_rows(args.release)
    extra = sv.distractors(release)
    rows = {r["id"]: r for r in release}
    preds = {s: {p["id"]: p for p in map(json.loads, (args.g4 / f"{s}.jsonl").open(encoding="utf-8"))} for s in SYSTEMS}
    chains = collections.defaultdict(list)
    for line in args.versions.open(encoding="utf-8"):
        v = json.loads(line)
        chains[v["provision_id"]].append(v)
    key_path = args.filled.parent / "khoa.jsonl"
    key = [json.loads(line) for line in key_path.open(encoding="utf-8")]
    sheet = [r for r in load_workbook(args.filled, read_only=True)["Chấm"].iter_rows(min_row=2, values_only=True)
             if r and r[0] is not None]
    if len(sheet) != len(key):
        raise SystemExit(f"phiếu {len(sheet)} dòng, khóa {len(key)} dòng")

    picked = pick(sheet, key, rows, preds, extra, chains)
    random.Random(args.seed).shuffle(picked)

    wb = Workbook()
    ws = wb.active
    ws.title = "Chấm"
    ws.append(COLUMNS)
    new_key = []
    for i, (k, why) in enumerate(picked, 1):
        r, p = rows[k["id"]], preds[k["system"]][k["id"]]
        ws.append([i, r["question"], r["as_of"], show_versions(chains[r["lineage_id"]], r["as_of"]),
                   p.get("answer") or "", "", ""])
        new_key.append({"stt": i, "stt_1_5": k["stt"], "id": k["id"], "system": k["system"], "why": why,
                        "label_1_5": sheet[k["stt"] - 1][6]})
    for cell in ws[1]:
        cell.font = Font(bold=True)
    for col, width in zip("ABCDEFG", (6, 45, 12, 90, 70, 18, 30)):
        ws.column_dimensions[col].width = width
    for line in ws.iter_rows(min_row=2):
        for cell in line:
            cell.alignment = Alignment(wrap_text=True, vertical="top")
    guide = wb.create_sheet("Hướng dẫn")
    for text in (
            "Mỗi dòng: câu hỏi, mốc, MỌI phiên bản của điều khoản được hỏi (bản áp dụng tại mốc có đánh dấu), câu trả lời của một hệ.",
            "Không có tên hệ, không có điểm máy, không có nhãn cũ. Chấm độc lập.",
            f"Cột nhan_nguoi chọn đúng một nhãn: {LABELS}.",
            "dung: nêu đúng nội dung của bản ÁP DỤNG TẠI MỐC (được diễn đạt khác, được thừa ý nhưng không mâu thuẫn).",
            "sai_phien_ban: có nội dung (con số, điều kiện, chủ thể, thủ tục…) chỉ có ở một bản KHÁC của chính điều khoản này "
            "và mâu thuẫn với bản tại mốc. Trộn bản đúng với bản khác cũng tính là sai_phien_ban.",
            "sai_noi_dung: sai, nhưng phần sai không khớp bản nào của điều khoản này (lấy từ điều khác, hoặc bịa).",
            "Chữ giống nhau giữa các bản không làm câu trả lời thành sai_phien_ban; chỉ tính phần chỉ bản khác có.",
            "Phân vân thì vẫn chọn nhãn và ghi lý do ở ghi_chu."):
        guide.append([text])
    guide.column_dimensions["A"].width = 120

    args.out.mkdir(parents=True, exist_ok=True)
    wb.save(args.out / "phieu.xlsx")
    (args.out / "khoa.jsonl").write_text("".join(json.dumps(k, ensure_ascii=False) + "\n" for k in new_key), encoding="utf-8")
    manifest = {"seed": args.seed, "n": len(new_key), "labels": LABELS,
                "by_reason": dict(collections.Counter(k["why"] for k in new_key)),
                "excluded": "dòng b1 sai_noi_dung mà điều khoản chỉ có một phiên bản (không thể sai phiên bản)",
                "caveat": "Người chấm đã thấy các câu này ở phiếu 1.5 và đã thấy kết quả độ khớp; chỉ mù tên hệ, cờ scorer và nhãn cũ.",
                "inputs": {str(p): hashlib.sha256(p.read_bytes()).hexdigest()
                           for p in [args.release, args.versions, args.filled, key_path,
                                     *(args.g4 / f"{s}.jsonl" for s in SYSTEMS)]},
                "outputs": {n: hashlib.sha256((args.out / n).read_bytes()).hexdigest() for n in ("phieu.xlsx", "khoa.jsonl")}}
    (args.out / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"{args.out}/phieu.xlsx: {len(new_key)} câu {manifest['by_reason']}; khóa ở khoa.jsonl (không mở khi chấm)")


if __name__ == "__main__":
    main()

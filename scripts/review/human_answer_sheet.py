#!/usr/bin/env python3
"""REFACTOR_PLAN 1.5: phiếu người chấm câu trả lời G4, để đo độ khớp của scorer khớp chuỗi với người.

Rút có seed, phân tầng theo hệ x (có/không đáp án), từ dự đoán lần 1 của bộ cuối (lát `all`, 318 dòng).
Người chấm KHÔNG thấy tên hệ và điểm máy: hai cột đó chỉ nằm trong file khóa riêng.
Không gọi model; không sửa dự đoán hay scorer.

    PYTHONPATH=src .venv/bin/python scripts/review/human_answer_sheet.py \\
        --g4 runs/final_g4_20261112/r1/test --release data/vilextime_final/vilextime.jsonl \\
        --out data/review/human_score_g4/  --n 100 --seed 20261113
"""
from __future__ import annotations

import argparse
import hashlib
import json
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "eval"))
import score_vilextime as sv  # noqa: E402

SYSTEMS = ("b1", "b4", "proposed2")
LABELS = "dung | sai_phien_ban | sai_noi_dung | khong_tra_loi | tu_choi_dung | khang_dinh_bai_bo_sai"
COLUMNS = ("stt", "cau_hoi", "moc", "dap_an_dung_tai_moc", "tra_loi_cua_he", "he_noi_hieu_luc",
           "nhan_nguoi", "ghi_chu")


def sample(rows: list[dict], preds: dict[str, dict], n: int, seed: int) -> list[tuple[str, dict]]:
    """n câu chia đều cho các hệ; trong mỗi hệ, dòng không đáp án lấy đúng tỷ lệ của lát."""
    rng = random.Random(seed)
    per = n // len(SYSTEMS)
    share = sum(not r["answerable"] for r in rows) / len(rows)
    out = []
    for i, system in enumerate(SYSTEMS):
        k = per + (1 if i < n - per * len(SYSTEMS) else 0)
        no = [r for r in rows if not r["answerable"]]
        yes = [r for r in rows if r["answerable"]]
        k_no = round(k * share)
        out += [(system, r) for r in rng.sample(no, k_no) + rng.sample(yes, k - k_no)]
    rng.shuffle(out)
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--g4", type=Path, required=True)
    ap.add_argument("--release", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--n", type=int, default=100)
    ap.add_argument("--seed", type=int, default=20261113)
    args = ap.parse_args()

    release = sv.load_rows(args.release)
    extra = sv.distractors(release)
    rows = [{**r, "_distractors": extra.get(r["id"], [])} for r in release
            if r.get("split") == "test" and r["as_of_strategy"] == "giua_khoang" and r["group"] in ("T2", "T3", "T6")]
    preds = {s: {p["id"]: p for p in map(json.loads, (args.g4 / f"{s}.jsonl").open(encoding="utf-8"))} for s in SYSTEMS}
    picked = sample(rows, preds, args.n, args.seed)

    args.out.mkdir(parents=True, exist_ok=True)
    sheet, key = [], []
    for i, (system, r) in enumerate(picked, 1):
        p = preds[system][r["id"]]
        gold = r["answer"] if r["answerable"] else "(Đã hết hiệu lực tại mốc này; câu trả lời đúng là khẳng định hết hiệu lực)"
        said = "không" if p.get("answerable") is False else "còn / không rõ"
        sheet.append({"stt": i, "cau_hoi": r["question"], "moc": r["as_of"], "dap_an_dung_tai_moc": gold,
                      "tra_loi_cua_he": p.get("answer") or "", "he_noi_hieu_luc": said, "nhan_nguoi": "", "ghi_chu": ""})
        key.append({"stt": i, "id": r["id"], "system": system, "group": r["group"], "answerable": r["answerable"],
                    "scorer_accuracy": sv.correct(r, p)})

    from openpyxl import Workbook
    from openpyxl.styles import Alignment, Font
    wb = Workbook()
    ws = wb.active
    ws.title = "Chấm"
    ws.append(COLUMNS)
    for line in sheet:
        ws.append([line[c] for c in COLUMNS])
    for cell in ws[1]:
        cell.font = Font(bold=True)
    for col, width in zip("ABCDEFGH", (6, 50, 12, 70, 70, 14, 22, 30)):
        ws.column_dimensions[col].width = width
    for row in ws.iter_rows(min_row=2):
        for cell in row:
            cell.alignment = Alignment(wrap_text=True, vertical="top")
    guide = wb.create_sheet("Hướng dẫn")
    for text in (
            "Mỗi dòng: một câu hỏi, mốc thời gian, đáp án đúng tại mốc (lời văn điều khoản), và câu trả lời của một hệ.",
            "Không có tên hệ, không có điểm máy. Chấm độc lập, không tra lại hệ.",
            f"Cột nhan_nguoi chọn đúng một nhãn: {LABELS}.",
            "dung: câu trả lời nêu đúng nội dung quy định tại mốc (được diễn đạt khác, được thừa ý nhưng không mâu thuẫn).",
            "sai_phien_ban: nêu nội dung của phiên bản khác (trước hoặc sau mốc) của cùng điều khoản.",
            "sai_noi_dung: nêu nội dung khác, không phải phiên bản nào của điều khoản này.",
            "khong_tra_loi: để trống hoặc nói không rõ khi lẽ ra có đáp án.",
            "tu_choi_dung: dòng đáp án ghi 'Đã hết hiệu lực' và hệ nói HIỆU LỰC không.",
            "khang_dinh_bai_bo_sai: hệ nói HIỆU LỰC không khi điều khoản vẫn còn hiệu lực.",
            "Phân vân thì vẫn chọn nhãn và ghi lý do ở ghi_chu."):
        guide.append([text])
    guide.column_dimensions["A"].width = 120
    wb.save(args.out / "phieu_cham.xlsx")
    (args.out / "khoa.jsonl").write_text("".join(json.dumps(k, ensure_ascii=False) + "\n" for k in key), encoding="utf-8")
    manifest = {"seed": args.seed, "n": len(sheet), "systems": SYSTEMS, "labels": LABELS,
                "inputs": {str(p): hashlib.sha256(p.read_bytes()).hexdigest()
                           for p in [args.release, *(args.g4 / f"{s}.jsonl" for s in SYSTEMS)]},
                "outputs": {name: hashlib.sha256((args.out / name).read_bytes()).hexdigest()
                            for name in ("phieu_cham.xlsx", "khoa.jsonl")}}
    (args.out / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"{args.out}/phieu_cham.xlsx: {len(sheet)} câu; khóa riêng ở khoa.jsonl (không mở khi chấm)")


if __name__ == "__main__":
    main()

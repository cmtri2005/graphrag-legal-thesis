"""W2: phiếu chấm chất lượng câu hỏi (đăng ký trước §2).

Writes, in this directory:
  pilot_key.tsv, pilot_{A,B}.xlsx   10 câu chạy thử (lineage bị loại), cả lượt 1 và lượt 2
  pass1_key.tsv                     khoa -> nguồn câu (bộ / mốc), lineage, ai đã đọc lineage đó. KHÔNG đưa người chấm
  pass1_{A,B}.xlsx                  229 câu xáo trộn, chỉ có câu hỏi
Refuses to overwrite a workbook that already has scores. Run: python3 data/review/qa_v6/w2/build.py
"""
import csv
import json
import random
import sqlite3
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
REL = ROOT / "data/vilextime_dib"
sys.path.insert(0, str(HERE))
import moc_src  # noqa: E402

P1 = ["khoa", "cau_hoi", "ro_nghia", "tu_nhien", "da_gap", "ghi_chu"]
P2 = ["khoa", "cau_hoi", "ngay", "loi_van_dieu_khoan", "tra_loi_duy_nhat", "lo_dap_an", "ghi_chu"]
CHOICES = {"ro_nghia": "1,2,3,4,5", "tu_nhien": "1,2,3,4,5", "da_gap": "có,không",
           "tra_loi_duy_nhat": "có,không,không chắc", "lo_dap_an": "có,không"}
FILL = {c for c in CHOICES} | {"ghi_chu"}
GUIDE1 = [
    "W2 lượt 1 — chấm câu hỏi, chỉ đọc câu hỏi",
    "Mỗi dòng là một câu hỏi pháp luật. Có câu do người thật hỏi, có câu do máy viết; không cần đoán câu nào là câu nào.",
    "Không tra văn bản, không mở file nào khác của dự án. Chấm theo cảm nhận khi đọc câu hỏi. Không trao đổi với người chấm kia trước khi cả hai nộp.",
    "",
    "ro_nghia (rõ nghĩa): người đọc có hiểu câu hỏi đang hỏi gì không?",
    "   1 = không hiểu được câu hỏi hỏi gì;  3 = hiểu nhưng phải đoán một phần;  5 = rõ hoàn toàn.  (2 và 4 là mức giữa.)",
    "tu_nhien (tự nhiên): người thật có hỏi như vậy không?",
    "   1 = không ai hỏi như vậy;  3 = có thể có người hỏi nhưng gượng;  5 = giống người thật hỏi.  (2 và 4 là mức giữa.)",
    "   Câu dài hay ngắn không tự nó làm câu kém tự nhiên. Chấm cách hỏi, không chấm độ dài.",
    "da_gap: có = bạn nhớ đã gặp câu hỏi này (hoặc điều khoản nó hỏi) trong một đợt đọc trước; không = chưa gặp.",
    "ghi_chu: không bắt buộc. Ghi khi phân vân, hoặc thấy câu có lỗi chữ.",
    "",
    "Chỉ các cột màu xanh được điền. Xong thì lưu file, gửi lại nguyên file. Sau khi nộp, lượt 1 bị khóa và không sửa nữa.",
]
GUIDE2 = [
    "Lượt 2 — câu hỏi kèm lời văn điều khoản (chỉ mở SAU khi đã nộp lượt 1)",
    "Mỗi dòng có câu hỏi, một ngày, và lời văn điều khoản có hiệu lực tại ngày đó.",
    "tra_loi_duy_nhat: có = chỉ đọc lời văn này là trả lời được câu hỏi, và chỉ có một cách trả lời đúng;",
    "   không = lời văn không trả lời được, hoặc trả lời được nhiều cách;  không chắc = không quyết được (ghi lý do).",
    "lo_dap_an: có = câu hỏi đã chứa sẵn đáp án (chép gần nguyên lời văn phần trả lời); không = không lộ.",
]


def write_tsv(path, cols, rows):
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, cols, delimiter="\t", lineterminator="\n")
        w.writeheader()
        w.writerows(rows)


def has_scores(path):
    if not path.exists():
        return False
    from openpyxl import load_workbook
    for ws in load_workbook(path, read_only=True):
        head = [c.value for c in next(ws.iter_rows(max_row=1))]
        idx = [i for i, h in enumerate(head) if h in FILL]
        if idx and any(any(r[i] not in (None, "") for i in idx) for r in ws.iter_rows(min_row=2, values_only=True)):
            return True
    return False


def sheet(wb, title, cols, rows):
    from openpyxl.styles import Alignment, Font, PatternFill, Protection
    from openpyxl.utils import get_column_letter
    from openpyxl.worksheet.datavalidation import DataValidation
    widths = {"khoa": 8, "cau_hoi": 90, "ngay": 11, "loi_van_dieu_khoan": 90, "ghi_chu": 40}
    ws = wb.create_sheet(title)
    for j, name in enumerate(cols, 1):
        c = ws.cell(1, j, name)
        c.font = Font(bold=True, color="FFFFFF")
        c.fill = PatternFill("solid", fgColor="2F6B3A" if name in FILL else "44546A")
        ws.column_dimensions[get_column_letter(j)].width = widths.get(name, 14)
    for i, row in enumerate(rows, 2):
        for j, name in enumerate(cols, 1):
            c = ws.cell(i, j, row.get(name, ""))
            c.alignment = Alignment(vertical="top", wrap_text=name in ("cau_hoi", "loi_van_dieu_khoan", "ghi_chu"))
            c.protection = Protection(locked=name not in FILL)
            if name in FILL:
                c.fill = PatternFill("solid", fgColor="EAF3EC")
    for name, opts in CHOICES.items():
        if name in cols:
            dv = DataValidation(type="list", formula1=f'"{opts}"', allow_blank=True, showErrorMessage=True)
            ws.add_data_validation(dv)
            col = get_column_letter(cols.index(name) + 1)
            dv.add(f"{col}2:{col}{len(rows) + 1}")
    ws.freeze_panes = "C2"
    ws.protection.sheet = True  # guard against slips, not security


def workbook(path, parts):
    from openpyxl import Workbook
    from openpyxl.styles import Font
    if has_scores(path):
        raise SystemExit(f"{path} đã có điểm; không ghi đè")
    wb = Workbook()
    g = wb.active
    g.title = "Đọc trước"
    lines = [ln for guide, *_ in parts for ln in guide + [""]]
    for i, ln in enumerate(lines, 1):
        g.cell(i, 1, ln).font = Font(bold=ln in (parts[0][0][0], *(p[0][0] for p in parts)))
    g.column_dimensions["A"].width = 140
    for _, title, cols, rows in parts:
        sheet(wb, title, cols, rows)
    wb.save(path)
    print(path.relative_to(ROOT), sum(len(p[3]) for p in parts), "dòng")


def pilot():
    exc = [json.loads(x) for x in open(REL / "annotation/excluded_lineages.jsonl", encoding="utf-8")]
    exc.sort(key=lambda e: e["lineage_id"])
    picked = random.Random("20261122:w2:pilot").sample(exc, 10)
    db = sqlite3.connect(ROOT / "data/temporal.sqlite")
    rows, key = [], []
    for i, e in enumerate(picked, 1):
        # First version; clause lineages without own text fall back to the enclosing article. Pilot only tests
        # the scale wording, so the text need not be the as_of version.
        q = "select text, valid_from from versions where provision_id=? order by ordinal limit 1"
        text, day = db.execute(q, (e["lineage_id"],)).fetchone() or db.execute(q, (e["lineage_id"].split("#")[0],)).fetchone()
        k = f"T{i:02d}"
        rows.append({"khoa": k, "cau_hoi": e["question"], "ngay": day or "", "loi_van_dieu_khoan": text})
        key.append({"khoa": k, "lineage_id": e["lineage_id"], "group": e["group"],
                    "reason_codes": ",".join(e["reason_codes"])})
    write_tsv(HERE / "pilot_key.tsv", ["khoa", "lineage_id", "group", "reason_codes"], key)
    for who in "AB":
        workbook(HERE / f"pilot_{who}.xlsx", [(GUIDE1, "Lượt 1", P1, [{k: r[k] for k in ("khoa", "cau_hoi")} for r in rows]),
                                              (GUIDE2, "Lượt 2", P2, rows)])


def pass1():
    rows = [json.loads(x) for x in open(REL / "vilextime.jsonl", encoding="utf-8")]
    meta = [json.loads(x) for x in open(REL / "vilextime_meta.jsonl", encoding="utf-8")]
    items, readers = {}, {}
    for r, m in zip(rows, meta):
        items.setdefault(r["lineage_id"], {"source": "bo", "id": r["lineage_id"], "group": r["group"],
                                           "model": m["question_source"].get("model", ""), "cau_hoi": r["question"]})
        for b in m["review"]["blind_gold"]:
            readers.setdefault(r["lineage_id"], set()).add(b["reader"])
    pool = [items[k] for k in sorted(items)]
    assert len(pool) == 199
    moc_src.check()
    pool += [{"source": "moc", "id": m[0], "group": m[1], "model": "", "cau_hoi": m[5]} for m in moc_src.MOC]
    random.Random("20261122:w2:order").shuffle(pool)
    keys = [f"Q{i:03d}" for i in range(1, len(pool) + 1)]
    write_tsv(HERE / "pass1_key.tsv", ["khoa", "source", "id", "group", "question_model", "read_before_by"],
              [{"khoa": k, "source": p["source"], "id": p["id"], "group": p["group"], "question_model": p["model"],
                "read_before_by": ",".join(sorted(readers.get(p["id"], ())))} for k, p in zip(keys, pool)])
    sheet_rows = [{"khoa": k, "cau_hoi": p["cau_hoi"]} for k, p in zip(keys, pool)]
    for who in "AB":
        workbook(HERE / f"pass1_{who}.xlsx", [(GUIDE1, "Lượt 1", P1, sheet_rows)])


if __name__ == "__main__":
    pilot()
    pass1()

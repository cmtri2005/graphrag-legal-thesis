"""ViLexTime 7.0 — phiếu gán nhãn hai giai đoạn cho hai sinh viên luật (đăng ký trước §3).

Thứ tự gán: lineage có câu hỏi qua máy (questions.jsonl), xếp xen kẽ giữa các phần theo tỷ lệ quota bản phát hành
(định nghĩa §9), trong mỗi phần theo thứ hạng của sample.jsonl. Người gán làm lần lượt từng lô; khi mọi phần đủ quota
(tính sau hòa giải) thì dừng. Lô 00 là lô thử 20 dòng; các lô sau 50 dòng.

  python3 data/vilextime_v7/phieu/build.py gd1            # dựng Giai đoạn 1 cho mọi lô (chưa có lời văn kho)
  python3 data/vilextime_v7/phieu/build.py lock lo01 A.xlsx B.xlsx   # nhận phiếu GD1 đã gán, xuất GD1.tsv, khóa
  python3 data/vilextime_v7/phieu/build.py gd2 lo01       # dựng Giai đoạn 2 của một lô; cần lo01/GD1.locked

Mỗi lô: lo<NN>/GD1_A.xlsx, GD1_B.xlsx (giống nhau), lo<NN>/key.tsv (khoa -> id dòng, lineage; KHÔNG giao người gán).
Không ghi đè phiếu đã có chữ người gán.
"""
import collections
import csv
import json
import random
import re
import sys
from datetime import date
from pathlib import Path

HERE = Path(__file__).resolve().parent
V7 = HERE.parent
ROOT = V7.parents[1]
QUOTA = {"T1": 150, "T2": 300, "T4": 150, "T3": 150, "T5": 20, "T6a": 100, "T6b": 250}   # định nghĩa §9 (dòng)
PILOT_ROWS, BATCH_ROWS = 20, 50
SEED = "20261124:v7:phieu"
READERS = "AB"
# S2 (24/11): a target that is an amending instruction ("4. Sửa đổi, bổ sung khoản 3 Điều 9 như sau: …") is not a norm
# of its own; once in force its content lives in the amended document, so "no longer in force" at a later date may be
# wrong. base.md already tells the generator to decline these; the fast pipeline did not. Left out of the queue,
# code `other` (amending_instruction), listed in excluded_amending.tsv.
AMENDING = re.compile(r"(Sửa đổi|Bổ sung|Thay thế|Bãi bỏ|sửa đổi|bổ sung|thay thế|bãi bỏ)[^.:\n]{0,40}"
                      r"\b(điểm|khoản|Điều|Chương|Mục|Phụ lục|cụm từ)\b[^:\n]{0,120}(như sau|:\s*$)"
                      r"|được (sửa đổi|bổ sung|thay thế)[^.\n]{0,40}như sau", re.M)

CODES = [
    ("cosmetic_only", "Lần đổi chỉ đổi hình thức, câu chữ"),
    ("rename_only", "Lần đổi chỉ đổi tên cơ quan, đơn vị do sắp xếp bộ máy"),
    ("auto_reference_update", "Lần đổi chỉ cập nhật dẫn chiếu tự áp"),
    ("single_change", "Không đủ số đáp án khác nhau cho nhóm"),
    ("relocated", "Nội dung bị bãi bỏ đã chuyển sang chỗ khác"),
    ("relocation_unclear", "Không chắc có chuyển chỗ hay không"),
    ("superseded_by_other_norm", "Quy phạm khác đè lên đáp án"),
    ("restructuring_2025", "Vướng sắp xếp bộ máy 2025"),
    ("reference_only", "Đáp án chỉ là dẫn chiếu"),
    ("group_mismatch", "Câu hỏi không hỏi vào chỗ thay đổi"),
    ("question_ambiguous", "Câu hỏi khớp nhiều điều khoản hoặc nhiều đáp án"),
    ("question_leaks", "Câu hỏi để lộ đáp án, số hiệu, Điều, Khoản hoặc phiên bản"),
    ("unanswerable_as_asked", "Đáp án không trả lời đúng điều câu hỏi hỏi"),
    ("transitional_rule", "Đáp án phụ thuộc quy định chuyển tiếp"),
    ("other", "Lỗi khác, mô tả ở Ghi chú"),
]

# (header shown, key, width, input?, choices)
GD1 = [
    ("Mã", "khoa", 8, False, None),
    ("Câu hỏi", "cau_hoi", 46, False, None),
    ("Ngày áp dụng", "ngay", 12, False, None),
    ("Văn bản", "van_ban", 30, False, None),
    ("Điều khoản", "dieu_khoan", 19, False, None),
    ("Văn bản gốc", "link", 11, False, None),
    ("Hiệu lực tại ngày", "hieu_luc", 12, True, "Còn,Hết"),
    ("Lời văn đang áp dụng (dán nguyên văn)", "noi_dung", 52, True, None),
    ("Đáp án ngắn (trích từ lời văn)", "dap_an_ngan", 32, True, None),
    ("Văn bản tạo ra lời văn này (số hiệu)", "van_ban_ap_dung", 20, True, None),
    ("Nguồn đã tra", "nguon_tra", 22, True, None),
    ("Thời gian (phút)", "phut", 9, True, "whole"),
    ("Ghi chú", "ghi_chu", 28, True, None),
]
GD2 = [
    ("Mã", "khoa", 8, False, None),
    ("Câu hỏi", "cau_hoi", 44, False, None),
    ("Lời văn các phiên bản (theo thời gian)", "loi_van", 70, False, None),
    ("Hỏi vào chỗ thay đổi?", "hoi_vao_cho_doi", 13, True, "Có,Không,Không chắc,Không áp dụng"),
    ("Trả lời được duy nhất?", "tra_loi_duy_nhat", 13, True, "Có,Không,Không chắc"),
    ("Lộ đáp án?", "lo_dap_an", 10, True, "Có,Không"),
    ("Mã lý do (nếu Không)", "ma_ly_do", 22, True, "codes"),
    ("Thời gian (phút)", "phut", 9, True, "whole"),
    ("Ghi chú", "ghi_chu", 28, True, None),
]

GUIDE_GD1 = [
    ("h", "Giai đoạn 1 — Tra cứu độc lập (chưa xem đáp án của bộ dữ liệu)"),
    ("p", "Mỗi dòng là một câu hỏi pháp luật và một ngày áp dụng. Nhiệm vụ: tự tra văn bản gốc và các văn bản sửa đổi, "
          "bổ sung, bãi bỏ để xác định điều khoản được nêu có nội dung gì vào đúng ngày đó."),
    ("p", "Cùng một câu hỏi có thể xuất hiện ở vài ngày khác nhau. Tra riêng từng ngày; đáp án có thể giống hoặc khác."),
    ("h2", "Cách tra"),
    ("b", "Mở văn bản gốc (cột Văn bản gốc), tìm đúng Điều khoản."),
    ("b", "Kiểm tra mọi văn bản sửa đổi, bổ sung, thay thế, bãi bỏ có hiệu lực trước hoặc đúng ngày áp dụng: mục "
          "\"Văn bản liên quan\" trên vbpl.vn, văn bản hợp nhất (VBHN), Công báo, Lawgical."),
    ("b", "Lưu ý điều khoản có thể hết hiệu lực vì chính nó bị bãi bỏ, hoặc vì Điều, Chương, cả văn bản chứa nó bị "
          "bãi bỏ hay thay thế."),
    ("b", "Ngày có hiệu lực của văn bản sửa đổi là ngày ghi ở điều khoản thi hành của văn bản đó, không phải ngày ký."),
    ("h2", "Điền gì"),
    ("t", [("Cột", "Điền"),
           ("Hiệu lực tại ngày", "Còn: điều khoản đang áp dụng vào ngày đó. Hết: đã bị bãi bỏ, thay thế hoặc chưa có "
                                 "hiệu lực."),
           ("Lời văn đang áp dụng", "Dán NGUYÊN VĂN lời văn của điều khoản đang áp dụng vào ngày đó (kể cả ký hiệu "
                                    "đầu mục như \"a)\", \"2.\"). Để trống nếu Hết."),
           ("Đáp án ngắn", "Phần trong lời văn trả lời đúng câu hỏi, trích nguyên văn, ngắn nhất có thể. Để trống "
                           "nếu Hết."),
           ("Văn bản tạo ra lời văn này", "Số hiệu văn bản đã ban hành lời văn đang áp dụng: văn bản gốc, hoặc văn "
                                          "bản sửa đổi gần nhất. Nếu Hết: số hiệu văn bản bãi bỏ, thay thế."),
           ("Nguồn đã tra", "Đường dẫn hoặc tên nguồn đã dùng (vbpl, VBHN số…, Công báo, Lawgical)."),
           ("Thời gian (phút)", "Số phút cho dòng này. Bắt buộc."),
           ("Ghi chú", "Khi phân vân, khi nguồn mâu thuẫn, hoặc khi câu hỏi có vấn đề.")]),
    ("h2", "Quy tắc"),
    ("b", "Chỉ điền các cột nền xanh nhạt. Các cột khác bị khóa."),
    ("b", "Không trao đổi với người gán kia, không mở file nào khác của dự án, cho tới khi cả hai đã nộp lô."),
    ("b", "Nộp lại nguyên file. Sau khi nộp, lô bị khóa và không sửa nữa."),
]
GUIDE_GD2 = [
    ("h", "Giai đoạn 2 — Chấm câu hỏi (chỉ mở SAU khi đã nộp Giai đoạn 1 của lô này)"),
    ("p", "Mỗi dòng là một câu hỏi và lời văn MỌI phiên bản của điều khoản theo thời gian, kèm các ngày câu hỏi được "
          "hỏi ở phiên bản đó. Cùng một câu hỏi được hỏi ở mọi ngày; mỗi ngày áp dụng một phiên bản."),
    ("t", [("Cột", "Chấm"),
           ("Hỏi vào chỗ thay đổi?", "Có: câu trả lời đúng khác nhau giữa các phiên bản (từ ba phiên bản trở lên: ít "
                                     "nhất ba câu trả lời khác nhau). Không: các phiên bản trả lời như nhau, hoặc chỉ "
                                     "khác hình thức, tên gọi. Với điều khoản bị bãi bỏ: Không nếu câu chỉ hỏi "
                                     "\"còn áp dụng không\". Không áp dụng: chỉ có một phiên bản."),
           ("Trả lời được duy nhất?", "Có: ở MỖI phiên bản, chỉ điều khoản này trả lời được, theo một cách. Không: "
                                      "khoản, điểm khác cũng trả lời được, hoặc có phiên bản không trả lời được điều "
                                      "được hỏi."),
           ("Lộ đáp án?", "Có: câu hỏi chứa sẵn đáp án, hoặc nêu cụm từ chỉ một phiên bản có, hoặc nêu số hiệu, "
                          "Điều, Khoản, ngày."),
           ("Mã lý do", "Bắt buộc khi có một câu Không hoặc Lộ = Có. Chọn từ danh sách (bảng bên dưới)."),
           ("Thời gian (phút)", "Số phút cho dòng này. Bắt buộc.")]),
    ("codes", None),
]


def jl(p):
    return [json.loads(x) for x in open(p, encoding="utf-8")]


def part_of(s):
    g = s["group"]
    if g == "T2":
        return "T4" if s.get("near_identical") else "T2"
    if g == "T6":
        return "T6b" if s.get("repeal_mode") == "ancestor" else "T6a"
    return g


def amending(recs):
    first = recs[0]
    return bool(AMENDING.search(first["target"]["lead_in"] or "") or
                any(AMENDING.search(r["answer"] or "") for r in recs))


def queue(recs):
    """Passed lineages, interleaved across parts in proportion to the quota, rank order within each part."""
    sample = jl(V7 / "sample.jsonl")
    ok = {r["lineage_id"]: r["question"] for r in jl(V7 / "questions.jsonl") if r["question"]}
    out = [s for s in sample if s["lineage_id"] in ok and amending(recs[s["lineage_id"]])]
    with open(HERE / "excluded_amending.tsv", "w", encoding="utf-8", newline="") as f:
        f.write("lineage_id\tpart\tcode\n")
        f.writelines(f"{s['lineage_id']}\t{part_of(s)}\tother:amending_instruction\n" for s in out)
    for s in out:
        ok.pop(s["lineage_id"])
    parts = collections.defaultdict(list)
    for s in sorted(sample, key=lambda s: s["rank"]):
        if s["lineage_id"] in ok:
            parts[part_of(s)].append(s)
    taken = collections.Counter()
    order = []
    while any(parts.values()):
        p = min((p for p in parts if parts[p]), key=lambda p: taken[p] / QUOTA[p])
        s = parts[p].pop(0)
        taken[p] += s["rows"]
        order.append((p, s, ok[s["lineage_id"]]))
    return order


def records():
    recs = collections.defaultdict(list)
    for g in ("T1", "T2", "T3", "T5", "T6"):
        for r in jl(ROOT / f"data/derived/vilextime/{g}.jsonl"):
            recs[r["lineage_id"]].append(r)
    for v in recs.values():
        v.sort(key=lambda r: r["as_of"])
    return recs


def batches(order):
    out, cur, n = [], [], PILOT_ROWS
    for item in order:
        cur.append(item)
        if sum(s["rows"] for _, s, _ in cur) >= n:
            out.append(cur)
            cur, n = [], BATCH_ROWS
    if cur:
        out.append(cur)
    return out


def spread(rows, rng):
    """Shuffle so that two rows of one lineage are not next to each other (when possible)."""
    for _ in range(200):
        rng.shuffle(rows)
        if all(a["lineage_id"] != b["lineage_id"] for a, b in zip(rows, rows[1:])):
            return rows
    return rows


def vn_date(iso):
    y, m, d = iso.split("-")
    return f"{d}/{m}/{y}"


# ------------------------------------------------------------------ xlsx
def styles():
    from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
    thin = Side(style="thin", color="C9CED6")
    return {
        "font": "Calibri",
        "title": Font(name="Calibri", size=14, bold=True, color="1F3A5F"),
        "sub": Font(name="Calibri", size=10, italic=True, color="5B6472"),
        "head_ro": PatternFill("solid", fgColor="1F3A5F"),
        "head_in": PatternFill("solid", fgColor="0E7C66"),
        "head_font": Font(name="Calibri", size=10, bold=True, color="FFFFFF"),
        "cell": Font(name="Calibri", size=10, color="1F2328"),
        "in_fill": PatternFill("solid", fgColor="E8F5F1"),
        "band": PatternFill("solid", fgColor="F5F7FA"),
        "border": Border(left=thin, right=thin, top=thin, bottom=thin),
        "wrap": Alignment(wrap_text=True, vertical="top"),
        "center": Alignment(horizontal="center", vertical="top", wrap_text=True),
        "head_align": Alignment(horizontal="center", vertical="center", wrap_text=True),
        "link": Font(name="Calibri", size=10, color="0B57D0", underline="single"),
    }


def guide_sheet(wb, title, guide):
    from openpyxl.styles import Alignment, Font, PatternFill
    S = styles()
    ws = wb.active
    ws.title = "Hướng dẫn"
    ws.sheet_view.showGridLines = False
    ws.column_dimensions["A"].width = 2
    ws.column_dimensions["B"].width = 30
    ws.column_dimensions["C"].width = 100
    r = 2
    ws.cell(r, 2, title).font = S["title"]
    r += 2
    for kind, body in guide:
        if kind == "h":
            ws.cell(r, 2, body).font = Font(name="Calibri", size=12, bold=True, color="0E7C66")
            r += 1
        elif kind == "h2":
            r += 1
            ws.cell(r, 2, body).font = Font(name="Calibri", size=11, bold=True, color="1F3A5F")
            r += 1
        elif kind in ("p", "b"):
            c = ws.cell(r, 2, ("•  " if kind == "b" else "") + body)
            ws.merge_cells(start_row=r, start_column=2, end_row=r, end_column=3)
            c.font, c.alignment = S["cell"], Alignment(wrap_text=True, vertical="top")
            ws.row_dimensions[r].height = 15 * (1 + len(body) // 120)
            r += 1
        elif kind in ("t", "codes"):
            rows = body if kind == "t" else [("Mã lý do", "Khi nào dùng")] + CODES
            for i, (a, b) in enumerate(rows):
                ca, cb = ws.cell(r, 2, a), ws.cell(r, 3, b)
                for c in (ca, cb):
                    c.border, c.alignment = S["border"], Alignment(wrap_text=True, vertical="top")
                    c.font = S["head_font"] if i == 0 else S["cell"]
                    if i == 0:
                        c.fill = S["head_ro"]
                    elif i % 2 == 0:
                        c.fill = S["band"]
                ws.row_dimensions[r].height = 15 * (1 + len(b) // 95)
                r += 1
            r += 1
    ws.page_setup.orientation = "portrait"
    ws.page_setup.fitToWidth, ws.page_setup.fitToHeight = 1, 0
    ws.sheet_properties.pageSetUpPr.fitToPage = True
    ws.protection.sheet = True
    return ws


def form_sheet(wb, cols, rows, banner):
    from openpyxl.formatting.rule import FormulaRule
    from openpyxl.styles import Protection
    from openpyxl.utils import get_column_letter
    from openpyxl.worksheet.datavalidation import DataValidation
    S = styles()
    ws = wb.create_sheet("Phiếu")
    ws.sheet_view.showGridLines = False
    ws.sheet_view.zoomScale = 110
    last = get_column_letter(len(cols))
    n = len(rows)
    first_in = next(i for i, c in enumerate(cols, 1) if c[3])
    in_col = get_column_letter(first_in)
    ws["A1"] = banner
    ws["A1"].font = S["title"]
    ws.merge_cells(f"A1:{get_column_letter(len(cols) - 2)}1")
    tail = get_column_letter(len(cols) - 1)
    ws[f"{tail}1"] = f'=COUNTA({in_col}4:{in_col}{n + 3})&" / {n} dòng đã điền"'
    ws[f"{tail}1"].font = S["sub"]
    ws.merge_cells(f"{tail}1:{last}1")
    ws["A2"] = ("Chỉ điền các cột tiêu đề xanh lá (ô nền xanh nhạt). Đọc trang \"Hướng dẫn\" trước khi bắt đầu. "
                "Ô có danh sách thì chọn từ danh sách.")
    ws["A2"].font = S["sub"]
    ws.merge_cells(f"A2:{last}2")
    for j, (head, key, width, is_in, _) in enumerate(cols, 1):
        c = ws.cell(3, j, head)
        c.fill = S["head_in"] if is_in else S["head_ro"]
        c.font, c.alignment, c.border = S["head_font"], S["head_align"], S["border"]
        ws.column_dimensions[get_column_letter(j)].width = width
    ws.row_dimensions[3].height = 42
    prev, band = None, False
    for i, row in enumerate(rows, 4):
        band = not band
        longest = 0
        for j, (head, key, width, is_in, choice) in enumerate(cols, 1):
            v = row.get(key, "")
            c = ws.cell(i, j, v)
            c.font, c.border = S["cell"], S["border"]
            c.alignment = S["center"] if key in ("khoa", "ngay", "hieu_luc", "phut", "lo_dap_an", "hoi_vao_cho_doi",
                                                  "tra_loi_duy_nhat") else S["wrap"]
            c.protection = Protection(locked=not is_in)
            if is_in:
                c.fill = S["in_fill"]
            elif band:
                c.fill = S["band"]
            if key == "link" and v:
                c.value, c.hyperlink, c.font = "Mở văn bản ↗", v, S["link"]
            if not is_in and isinstance(v, str):   # wrapped lines, counting the text's own line breaks
                chars = max(width, 1) * 1.15
                longest = max(longest, sum(1 + int(len(seg) / chars) for seg in v.split("\n")))
        ws.row_dimensions[i].height = min(409, max(30, 13.5 * longest + 6))
    for j, (head, key, width, is_in, choice) in enumerate(cols, 1):
        if not choice:
            continue
        col = get_column_letter(j)
        if choice == "whole":
            dv = DataValidation(type="whole", operator="between", formula1="0", formula2="600", allow_blank=True,
                                showErrorMessage=True, errorTitle="Số phút", error="Nhập số phút (0–600).")
        else:
            opts = ",".join(k for k, _ in CODES) if choice == "codes" else choice
            dv = DataValidation(type="list", formula1=f'"{opts}"', allow_blank=True, showErrorMessage=True,
                                errorTitle="Giá trị không hợp lệ", error="Chọn một giá trị trong danh sách.")
        ws.add_data_validation(dv)
        dv.add(f"{col}4:{col}{n + 3}")
    # an input cell left empty turns amber once the row has been started
    from openpyxl.styles import PatternFill
    amber = PatternFill("solid", fgColor="FFF4CE")
    ins = [get_column_letter(j) for j, c in enumerate(cols, 1) if c[3] and c[1] not in ("ghi_chu", "nguon_tra",
                                                                                          "ma_ly_do")]
    for col in ins:
        rng = f"{col}4:{col}{n + 3}"
        any_filled = "+".join(f'(${c}4<>"")' for c in ins)
        ws.conditional_formatting.add(rng, FormulaRule(formula=[f'AND({col}4="",{any_filled}>0)'], fill=amber))
    ws.freeze_panes = "C4"
    ws.auto_filter.ref = f"A3:{last}{n + 3}"
    ws.print_title_rows = "3:3"
    ws.page_setup.orientation = "landscape"
    ws.page_setup.fitToWidth, ws.page_setup.fitToHeight = 1, 0
    ws.sheet_properties.pageSetUpPr.fitToPage = True
    ws.protection.sheet = True
    for k in ("formatColumns", "formatRows", "autoFilter", "sort"):
        setattr(ws.protection, k, False)
    wb.active = 1
    return ws


def has_answers(path, cols):
    if not path.exists():
        return False
    from openpyxl import load_workbook
    ws = load_workbook(path, read_only=True)["Phiếu"]
    idx = [j for j, c in enumerate(cols) if c[3]]
    return any(any(r[j] not in (None, "") for j in idx) for r in ws.iter_rows(min_row=4, values_only=True))


def write(path, guide_title, guide, cols, rows, banner):
    from openpyxl import Workbook
    if has_answers(path, cols):
        raise SystemExit(f"{path} đã có chữ người gán; không ghi đè")
    wb = Workbook()
    guide_sheet(wb, guide_title, guide)
    form_sheet(wb, cols, rows, banner)
    wb.properties.creator = "ViLexTime 7.0"
    wb.properties.title = banner
    wb.save(path)


def build_gd1():
    recs = records()
    order = queue(recs)
    plan = []
    for b, items in enumerate(batches(order)):
        name = f"lo{b:02d}"
        rng = random.Random(f"{SEED}:{name}")
        rows = []
        for part, s, question in items:
            for r in recs[s["lineage_id"]]:
                t = r["target"]
                rows.append({"id": r["id"], "lineage_id": r["lineage_id"], "part": part, "cau_hoi": question,
                             "ngay": vn_date(r["as_of"]), "van_ban": " ".join(t["document_title"].split()),
                             "dieu_khoan": t["citation"], "link": r["source_url"]})
        rows = spread(rows, rng)
        for i, row in enumerate(rows, 1):
            row["khoa"] = f"{b:02d}-{i:02d}"
        d = HERE / name
        d.mkdir(exist_ok=True)
        with open(d / "key.tsv", "w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, ["khoa", "id", "lineage_id", "part"], delimiter="\t", lineterminator="\n",
                               extrasaction="ignore")
            w.writeheader()
            w.writerows(rows)
        for who in READERS:
            label = "Lô thử" if b == 0 else f"Lô {b:02d}"
            write(d / f"GD1_{who}.xlsx", "ViLexTime 7.0 — Hướng dẫn gán nhãn, Giai đoạn 1", GUIDE_GD1, GD1, rows,
                  f"ViLexTime 7.0  ·  Giai đoạn 1  ·  {label}  ·  Người gán {who}")
        plan.append({"lo": name, "rows": len(rows), "lineages": len(items),
                     "parts": dict(collections.Counter(p for p, _, _ in items))})
    (HERE / "plan.json").write_text(json.dumps({"built": date.today().isoformat(), "quota_rows": QUOTA,
                                                "batches": plan}, ensure_ascii=False, indent=1) + "\n", "utf-8")
    print(f"{len(plan)} lô, {sum(p['rows'] for p in plan)} dòng -> {HERE.relative_to(ROOT)}/lo*/")


def build_gd2(name):
    d = HERE / name
    if not (d / "GD1.locked").exists():
        raise SystemExit(f"{name}: Giai đoạn 1 chưa khóa ({name}/GD1.locked); phiếu GD2 có lời văn kho")
    key = list(csv.DictReader(open(d / "key.tsv", encoding="utf-8"), delimiter="\t"))
    recs = records()
    q = {r["lineage_id"]: r["question"] for r in jl(V7 / "questions.jsonl")}
    lins = list(dict.fromkeys(k["lineage_id"] for k in key))
    random.Random(f"{SEED}:{name}:gd2").shuffle(lins)
    rows = []
    for i, lid in enumerate(lins, 1):
        states = collections.OrderedDict()
        for r in recs[lid]:
            states.setdefault(r["answer"] or "(Không còn hiệu lực)", []).append(vn_date(r["as_of"]))
        lead = recs[lid][0]["target"]["lead_in"] or ""
        body = (f"[Câu dẫn] {lead}\n\n" if lead else "") + "\n\n".join(
            f"[Phiên bản {n} — hỏi ở ngày {', '.join(days)}]\n{text}" for n, (text, days) in enumerate(states.items(), 1))
        rows.append({"khoa": f"{name[2:]}-{i:02d}", "lineage_id": lid, "cau_hoi": q[lid], "loi_van": body})
    with open(d / "key_gd2.tsv", "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, ["khoa", "lineage_id"], delimiter="\t", lineterminator="\n", extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
    for who in READERS:
        write(d / f"GD2_{who}.xlsx", "ViLexTime 7.0 — Hướng dẫn gán nhãn, Giai đoạn 2", GUIDE_GD2, GD2, rows,
              f"ViLexTime 7.0  ·  Giai đoạn 2  ·  {'Lô thử' if name == 'lo00' else 'Lô ' + name[2:]}  ·  Người gán {who}")
    print(f"{name}: GD2 {len(rows)} câu hỏi")


def read_form(path, cols, key):
    """Rows of a returned form as dicts; refuses a form whose read-only cells differ from the key's order."""
    from openpyxl import load_workbook
    ws = load_workbook(path)["Phiếu"]
    rows = []
    for r in ws.iter_rows(min_row=4, max_row=len(key) + 3, values_only=True):
        rows.append({c[1]: ("" if v is None else str(v).strip()) for c, v in zip(cols, r)})
    got = [r["khoa"] for r in rows]
    if got != [k["khoa"] for k in key]:
        raise SystemExit(f"{path}: cột Mã khác key.tsv")
    return rows


def lock_gd1(name, path_a, path_b):
    """Copy the returned forms into lo<NN>/, export GD1.tsv, flag A/B differences, write GD1.locked (sha256)."""
    import hashlib
    import shutil
    d = HERE / name
    if (d / "GD1.locked").exists():
        raise SystemExit(f"{name}: đã khóa")
    key = list(csv.DictReader(open(d / "key.tsv", encoding="utf-8"), delimiter="\t"))
    forms = {"A": read_form(path_a, GD1, key), "B": read_form(path_b, GD1, key)}
    inputs = [c[1] for c in GD1 if c[3]]
    out, issues = [], []
    for who, rows in forms.items():
        for k, r in zip(key, rows):
            out.append({"who": who, **k, **{f: r[f] for f in inputs}})
            if r["hieu_luc"] not in ("Còn", "Hết"):
                issues.append(f"{r['khoa']} {who}: thiếu Hiệu lực")
            if r["hieu_luc"] == "Còn" and not (r["noi_dung"] and r["dap_an_ngan"]):
                issues.append(f"{r['khoa']} {who}: Còn nhưng thiếu lời văn/đáp án ngắn")
            if not r["phut"]:
                issues.append(f"{r['khoa']} {who}: thiếu phút")
    norm = lambda s: " ".join(s.lower().split())
    diffs = []
    for a, b in zip(forms["A"], forms["B"]):
        fields = [f for f in ("hieu_luc", "noi_dung", "dap_an_ngan", "van_ban_ap_dung") if norm(a[f]) != norm(b[f])]
        if fields:
            diffs.append({"khoa": a["khoa"], "lech": ",".join(fields)})
    for who, p in (("A", path_a), ("B", path_b)):
        shutil.copyfile(p, d / f"GD1_{who}.xlsx")
    with open(d / "GD1.tsv", "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, list(out[0]), delimiter="\t", lineterminator="\n")
        w.writeheader()
        w.writerows(out)
    with open(d / "GD1_lech.tsv", "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, ["khoa", "lech"], delimiter="\t", lineterminator="\n")
        w.writeheader()
        w.writerows(diffs)
    sha = {f"GD1_{w}.xlsx": hashlib.sha256((d / f"GD1_{w}.xlsx").read_bytes()).hexdigest() for w in READERS}
    (d / "GD1.locked").write_text(json.dumps({"locked": date.today().isoformat(), "sha256": sha, "issues": issues},
                                             ensure_ascii=False, indent=1) + "\n", "utf-8")
    hl = sum(a["hieu_luc"] == b["hieu_luc"] for a, b in zip(forms["A"], forms["B"]))
    print(f"{name}: khóa {len(key)} dòng; Hiệu lực khớp {hl}/{len(key)}; dòng lệch {len(diffs)}; lỗi phiếu {len(issues)}")
    for x in issues:
        print("  ", x)


if __name__ == "__main__":
    if sys.argv[1:2] == ["gd1"]:
        build_gd1()
    elif sys.argv[1:2] == ["gd2"] and len(sys.argv) == 3:
        build_gd2(sys.argv[2])
    elif sys.argv[1:2] == ["lock"] and len(sys.argv) == 5:
        lock_gd1(*sys.argv[2:])
    else:
        raise SystemExit(__doc__)

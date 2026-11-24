"""ViLexTime 7.0 — phiếu gán nhãn hai giai đoạn cho hai sinh viên luật (đăng ký trước §3).

Thứ tự gán: lineage có câu hỏi qua máy (questions.jsonl), xếp xen kẽ giữa các phần theo tỷ lệ quota bản phát hành
(định nghĩa §9), trong mỗi phần theo thứ hạng của sample.jsonl. Người gán làm lần lượt từng lô; khi mọi phần đủ quota
(tính sau hòa giải) thì dừng. Lô 00 là lô thử 20 dòng; các lô sau 50 dòng.

  python3 data/vilextime_v7/phieu/build.py gd1            # dựng Giai đoạn 1 cho mọi lô (chưa có lời văn kho)
  python3 data/vilextime_v7/phieu/build.py lock GD1 lo01 A.xlsx B.xlsx   # nhận phiếu đã gán (GD1 hoặc GD2), xuất .tsv, khóa
  python3 data/vilextime_v7/phieu/build.py gd2 lo01       # dựng Giai đoạn 2 của một lô; cần lo01/GD1.locked
  python3 data/vilextime_v7/phieu/build.py hoa_giai lo01  # phiếu luật sư: đáp án ngắn dòng giữ, mã lý do lệch
  python3 data/vilextime_v7/phieu/build.py chot lo01 hoa_giai.xlsx   # nhận phiếu luật sư -> final.jsonl, khóa

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
           ("Đáp án ngắn", "Cụm mà một câu trả lời đúng BẮT BUỘC phải chứa. Xem mục \"Cách trích đáp án ngắn\". "
                           "Để trống nếu Hết."),
           ("Văn bản tạo ra lời văn này", "Số hiệu văn bản đã ban hành lời văn đang áp dụng: văn bản gốc, hoặc văn "
                                          "bản sửa đổi gần nhất. Nếu Hết: số hiệu văn bản bãi bỏ, thay thế."),
           ("Nguồn đã tra", "Đường dẫn hoặc tên nguồn đã dùng (vbpl, VBHN số…, Công báo, Lawgical)."),
           ("Thời gian (phút)", "Số phút thật cho dòng này, tính cả lúc tra văn bản. Số nguyên, làm tròn lên (dưới "
                                "1 phút ghi 1). Bắt buộc."),
           ("Ghi chú", "Khi phân vân, khi nguồn mâu thuẫn, hoặc khi câu hỏi có vấn đề.")]),
    ("h2", "Cách trích đáp án ngắn"),
    ("b", "Chép nguyên văn từ lời văn, không sửa chữ, không viết lại."),
    ("b", "Ngắn nhất nhưng đủ ý: giữ đủ con số, mức, thời hạn, chủ thể, điều kiện, phạm vi mà câu hỏi hỏi tới. "
          "Đây thường là phần thay đổi giữa các phiên bản, bỏ đi thì không chấm được."),
    ("b", "Bỏ ký hiệu đầu mục (\"a)\", \"2.\"), bỏ câu dẫn, bỏ phần lặp lại ý của câu hỏi."),
    ("b", "Câu hỏi hỏi một danh sách thì trích đủ cả danh sách."),
    ("b", "Cần hai đoạn không liền nhau thì nối bằng \" … \" (dấu ba chấm, cách hai bên)."),
    ("t", [("Ví dụ", "Đáp án ngắn"),
           ("Quê quán ghi thế nào? Lời văn: \"a) Quê quán: Ghi cấp xã, cấp tỉnh;\"", "cấp xã, cấp tỉnh"),
           ("Căn cứ quản lý là gì? Lời văn: \"2. Phạm vi quy hoạch trong nội dung của quy hoạch chung đô thị được "
            "phê duyệt là căn cứ…\"", "Phạm vi quy hoạch")]),
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
           ("Thời gian (phút)", "Số phút thật cho dòng này. Số nguyên, làm tròn lên (dưới 1 phút ghi 1). "
                                "Bắt buộc.")]),
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


def form_sheet(wb, cols, rows, banner, title="Phiếu"):
    from openpyxl.formatting.rule import FormulaRule
    from openpyxl.styles import Protection
    from openpyxl.utils import get_column_letter
    from openpyxl.worksheet.datavalidation import DataValidation
    S = styles()
    ws = wb.create_sheet(title)
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


HG_SA = [
    ("Mã", "khoa", 8, False, None),
    ("Câu hỏi", "cau_hoi", 36, False, None),
    ("Ngày", "ngay", 11, False, None),
    ("Lời văn đang áp dụng (A, B và kho khớp nhau)", "noi_dung", 44, False, None),
    ("Đáp án ngắn A", "sa_a", 26, False, None),
    ("Đáp án ngắn B", "sa_b", 26, False, None),
    ("Đề xuất theo quy tắc", "de_xuat", 26, False, None),
    ("Chọn", "chon", 10, True, "A,B,Đề xuất,Sửa"),
    ("Đáp án ngắn cuối (nếu Sửa)", "sa_cuoi", 30, True, None),
    ("Ghi chú", "ghi_chu", 24, True, None),
]
HG_CODE = [
    ("Mã GD2", "khoa", 8, False, None),
    ("Câu hỏi", "cau_hoi", 40, False, None),
    ("A: mã lý do và ghi chú", "a", 46, False, None),
    ("B: mã lý do và ghi chú", "b", 46, False, None),
    ("Mã lý do cuối", "ma_cuoi", 22, True, "codes"),
    ("Ghi chú", "ghi_chu", 24, True, None),
]
GUIDE_HG = [
    ("h", "Hòa giải lô — luật sư"),
    ("p", "Hai người gán đã nộp và khóa cả hai giai đoạn của lô. Chỉ còn các chỗ dưới đây cần một quyết định."),
    ("h2", "Trang \"Đáp án ngắn\""),
    ("p", "Các dòng sẽ vào bộ test. Hiệu lực và lời văn đã khớp; chỉ chốt đáp án ngắn: cụm mà một câu trả lời đúng "
          "BẮT BUỘC phải chứa, trích nguyên văn, ngắn nhất nhưng đủ ý (giữ số, mức, thời hạn, chủ thể, điều kiện, "
          "phạm vi), bỏ ký hiệu đầu mục và câu dẫn, hai đoạn rời nối bằng \" … \". Cột \"Đề xuất\" do máy chọn "
          "theo quy tắc (bỏ chữ đầu mục; khi một bản nằm trọn trong bản kia thì lấy bản ngắn), chỉ để tham khảo."),
    ("h2", "Trang \"Mã lý do\""),
    ("p", "Câu hỏi cả hai người đều loại nhưng chọn mã lý do khác nhau. Chọn một mã; không ảnh hưởng bộ test, chỉ "
          "ghi vào danh sách dòng bị loại."),
    ("codes", None),
]


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
        plan.append({"lo": name, "rows": len(rows), "lineages": len(items),
                     "parts": dict(collections.Counter(p for p, _, _ in items))})
        if (d / "GD1.locked").exists():   # already returned: keep forms and key as they were
            continue
        with open(d / "key.tsv", "w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, ["khoa", "id", "lineage_id", "part"], delimiter="\t", lineterminator="\n",
                               extrasaction="ignore")
            w.writeheader()
            w.writerows(rows)
        for who in READERS:
            label = "Lô thử" if b == 0 else f"Lô {b:02d}"
            write(d / f"GD1_{who}.xlsx", "ViLexTime 7.0 — Hướng dẫn gán nhãn, Giai đoạn 1", GUIDE_GD1, GD1, rows,
                  f"ViLexTime 7.0  ·  Giai đoạn 1  ·  {label}  ·  Người gán {who}")
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


def form_issues(stage, r):
    out = [] if r["phut"] else ["thiếu phút"]
    if stage == "GD1":
        if r["hieu_luc"] not in ("Còn", "Hết"):
            out.append("thiếu Hiệu lực")
        if r["hieu_luc"] == "Còn" and not (r["noi_dung"] and r["dap_an_ngan"]):
            out.append("Còn nhưng thiếu lời văn/đáp án ngắn")
    elif not passes(r) and not r["ma_ly_do"]:
        out.append("không đạt nhưng thiếu mã lý do")
    return out


def passes(r):
    """GD2 verdict: asks at the change (or single version), one answer per version, no leak."""
    return r["hoi_vao_cho_doi"] in ("Có", "Không áp dụng") and r["tra_loi_duy_nhat"] == "Có" and r["lo_dap_an"] == "Không"


COMPARE = {"GD1": ("hieu_luc", "noi_dung", "dap_an_ngan", "van_ban_ap_dung"),
           "GD2": ("hoi_vao_cho_doi", "tra_loi_duy_nhat", "lo_dap_an", "ma_ly_do")}


def lock(stage, name, path_a, path_b):
    """Copy returned forms into lo<NN>/, export <stage>.tsv, flag A/B differences, write <stage>.locked (sha256)."""
    import hashlib
    import shutil
    d = HERE / name
    if (d / f"{stage}.locked").exists():
        raise SystemExit(f"{name}: {stage} đã khóa")
    if stage == "GD2" and not (d / "GD1.locked").exists():
        raise SystemExit(f"{name}: GD1 chưa khóa")
    cols = GD1 if stage == "GD1" else GD2
    key = list(csv.DictReader(open(d / ("key.tsv" if stage == "GD1" else "key_gd2.tsv"), encoding="utf-8"),
                              delimiter="\t"))
    forms = {"A": read_form(path_a, cols, key), "B": read_form(path_b, cols, key)}
    inputs = [c[1] for c in cols if c[3]]
    out, issues = [], []
    for who, rows in forms.items():
        for k, r in zip(key, rows):
            out.append({"who": who, **k, **{f: r[f] for f in inputs}})
            issues += [f"{r['khoa']} {who}: {x}" for x in form_issues(stage, r)]
    norm = lambda s: " ".join(s.lower().split())
    diffs = []
    for a, b in zip(forms["A"], forms["B"]):
        fields = [f for f in COMPARE[stage] if norm(a[f]) != norm(b[f])]
        if stage == "GD2" and passes(a) != passes(b):
            fields.insert(0, "ket_luan")
        if fields:
            diffs.append({"khoa": a["khoa"], "lech": ",".join(fields)})
    for who, p in (("A", path_a), ("B", path_b)):
        shutil.copyfile(p, d / f"{stage}_{who}.xlsx")
    with open(d / f"{stage}.tsv", "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, list(out[0]), delimiter="\t", lineterminator="\n")
        w.writeheader()
        w.writerows(out)
    with open(d / f"{stage}_lech.tsv", "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, ["khoa", "lech"], delimiter="\t", lineterminator="\n")
        w.writeheader()
        w.writerows(diffs)
    sha = {f"{stage}_{w}.xlsx": hashlib.sha256((d / f"{stage}_{w}.xlsx").read_bytes()).hexdigest() for w in READERS}
    (d / f"{stage}.locked").write_text(json.dumps({"locked": date.today().isoformat(), "sha256": sha,
                                                   "issues": issues}, ensure_ascii=False, indent=1) + "\n", "utf-8")
    n = len(key)
    first = COMPARE[stage][0]
    same = sum(a[first] == b[first] for a, b in zip(forms["A"], forms["B"]))
    msg = f"{name} {stage}: khóa {n} dòng; {first} khớp {same}/{n}; dòng lệch {len(diffs)}; lỗi phiếu {len(issues)}"
    if stage == "GD2":
        pa, pb = ([passes(r) for r in forms[w]] for w in READERS)
        msg += (f"; đạt A {sum(pa)}, B {sum(pb)}, cả hai {sum(x and y for x, y in zip(pa, pb))}; "
                f"kết luận khớp {sum(x == y for x, y in zip(pa, pb))}/{n}")
    print(msg)
    for x in issues:
        print("  ", x)


def build_hoa_giai(name):
    """Lawyer form for a lot whose GD1 and GD2 are both locked: short answers of kept rows, drop codes in conflict."""
    d = HERE / name
    for st in ("GD1", "GD2"):
        if not (d / f"{st}.locked").exists():
            raise SystemExit(f"{name}: {st} chưa khóa")
    key = list(csv.DictReader(open(d / "key.tsv", encoding="utf-8"), delimiter="\t"))
    k2 = {r["lineage_id"]: r["khoa"] for r in csv.DictReader(open(d / "key_gd2.tsv", encoding="utf-8"), delimiter="\t")}
    g1, g2 = collections.defaultdict(dict), collections.defaultdict(dict)
    for st, g in (("GD1", g1), ("GD2", g2)):
        for r in csv.DictReader(open(d / f"{st}.tsv", encoding="utf-8"), delimiter="\t"):
            g[r["khoa"]][r["who"]] = r
    q = {r["lineage_id"]: r["question"] for r in jl(V7 / "questions.jsonl")}
    recs = records()
    by_id = {r["id"]: r for v in recs.values() for r in v}
    norm = lambda s: " ".join(s.lower().split())
    mark = re.compile(r"^\s*(?:\d+(?:\.\d+)*\.|[a-zđ]\))\s+|^\s*Ghi\s+")
    sa_rows, code_rows, problems = [], [], []
    keep_of = {lid: all(passes(g2[k][w]) for w in READERS) for lid, k in k2.items()}
    for k in key:
        if not keep_of[k["lineage_id"]]:
            continue
        a, b = g1[k["khoa"]]["A"], g1[k["khoa"]]["B"]
        if a["hieu_luc"] != b["hieu_luc"] or norm(a["noi_dung"]) != norm(b["noi_dung"]):
            problems.append(f"{k['khoa']}: dòng giữ nhưng hiệu lực/lời văn lệch, cần xem tay")
        sa = [mark.sub("", x["dap_an_ngan"]).strip() for x in (a, b)]
        prop = sa[0] if norm(sa[0]) == norm(sa[1]) else (
            min(sa, key=len) if norm(min(sa, key=len)) in norm(max(sa, key=len)) else "")
        sa_rows.append({"khoa": k["khoa"], "cau_hoi": q[k["lineage_id"]], "ngay": vn_date(by_id[k["id"]]["as_of"]),
                        "noi_dung": a["noi_dung"], "sa_a": a["dap_an_ngan"], "sa_b": b["dap_an_ngan"], "de_xuat": prop})
    for lid, kk in k2.items():
        a, b = g2[kk]["A"], g2[kk]["B"]
        if not keep_of[lid] and not passes(a) and not passes(b) and a["ma_ly_do"] != b["ma_ly_do"]:
            code_rows.append({"khoa": kk, "cau_hoi": q[lid], "a": f"{a['ma_ly_do']} — {a['ghi_chu']}",
                              "b": f"{b['ma_ly_do']} — {b['ghi_chu']}"})
        elif not keep_of[lid] and passes(a) != passes(b):
            problems.append(f"GD2 {kk}: một người đạt, một người không — cần thêm trang kết luận")
    sa_rows.sort(key=lambda r: r["khoa"])
    code_rows.sort(key=lambda r: r["khoa"])
    from openpyxl import Workbook
    path = d / "hoa_giai.xlsx"
    if has_answers(path, HG_SA):
        raise SystemExit(f"{path} đã có chữ; không ghi đè")
    wb = Workbook()
    guide_sheet(wb, "ViLexTime 7.0 — Hòa giải", GUIDE_HG)
    label = "Lô thử" if name == "lo00" else f"Lô {name[2:]}"
    form_sheet(wb, HG_SA, sa_rows, f"ViLexTime 7.0  ·  Hòa giải  ·  {label}  ·  Đáp án ngắn", "Phiếu")
    if code_rows:
        form_sheet(wb, HG_CODE, code_rows, f"ViLexTime 7.0  ·  Hòa giải  ·  {label}  ·  Mã lý do", "Mã lý do")
    wb.active = 1
    wb.save(path)
    print(f"{name}: hòa giải {len(sa_rows)} đáp án ngắn, {len(code_rows)} mã lý do -> {path.relative_to(ROOT)}")
    for x in problems:
        print("  ", x)


def chot(name, path):
    """Take the lawyer's form back: lo<NN>/final.jsonl (every row: kept with its final short answer, or dropped with
    its code) and hoa_giai.locked. Columns are read by header, so an older layout of the form still reads."""
    import hashlib
    import shutil
    from openpyxl import load_workbook
    d = HERE / name
    if (d / "hoa_giai.locked").exists():
        raise SystemExit(f"{name}: đã chốt")
    wb = load_workbook(path)

    def sheet(title):
        if title not in wb.sheetnames:
            return {}
        ws = wb[title]
        head = [c.value for c in ws[3]]
        return {r[0]: dict(zip(head, ("" if v is None else str(v).strip() for v in r)))
                for r in ws.iter_rows(min_row=4, values_only=True) if r[0]}
    sa, codes = sheet("Phiếu"), sheet("Mã lý do")
    key = list(csv.DictReader(open(d / "key.tsv", encoding="utf-8"), delimiter="\t"))
    k2 = {r["lineage_id"]: r["khoa"] for r in csv.DictReader(open(d / "key_gd2.tsv", encoding="utf-8"), delimiter="\t")}
    g1, g2 = collections.defaultdict(dict), collections.defaultdict(dict)
    for st, g in (("GD1", g1), ("GD2", g2)):
        for r in csv.DictReader(open(d / f"{st}.tsv", encoding="utf-8"), delimiter="\t"):
            g[r["khoa"]][r["who"]] = r
    out, missing = [], []
    for k in key:
        a, b = g1[k["khoa"]]["A"], g1[k["khoa"]]["B"]
        q2 = k2[k["lineage_id"]]
        row = {"khoa": k["khoa"], "id": k["id"], "lineage_id": k["lineage_id"], "part": k["part"], "gd2": q2}
        if all(passes(g2[q2][w]) for w in READERS):
            h = sa.get(k["khoa"], {})
            pick = h.get("Chọn", "")
            final = {"A": a["dap_an_ngan"], "B": b["dap_an_ngan"], "Đề xuất": h.get("Đề xuất theo quy tắc", ""),
                     "Sửa": h.get("Đáp án ngắn cuối (nếu Sửa)", "")}.get(pick, "")
            if not final:
                missing.append(f"{k['khoa']}: chưa chọn đáp án ngắn")
            row.update(keep=True, hieu_luc=a["hieu_luc"], answer=a["noi_dung"], short_answer=final,
                       van_ban_ap_dung=a["van_ban_ap_dung"], chon=pick, ghi_chu_luat_su=h.get("Ghi chú", ""))
        else:
            ca, cb = g2[q2]["A"]["ma_ly_do"], g2[q2]["B"]["ma_ly_do"]
            code = ca if ca == cb else codes.get(q2, {}).get("Mã lý do cuối", "")
            if not code:
                missing.append(f"GD2 {q2}: chưa có mã lý do")
            row.update(keep=False, drop_code=code, ghi_chu_luat_su="" if ca == cb else codes.get(q2, {}).get("Ghi chú", ""))
        out.append(row)
    if missing:
        raise SystemExit("Phiếu thiếu:\n  " + "\n  ".join(missing))
    shutil.copyfile(path, d / "hoa_giai.xlsx")
    with open(d / "final.jsonl", "w", encoding="utf-8") as f:
        f.writelines(json.dumps(r, ensure_ascii=False) + "\n" for r in out)
    sha = hashlib.sha256((d / "hoa_giai.xlsx").read_bytes()).hexdigest()
    (d / "hoa_giai.locked").write_text(json.dumps({"locked": date.today().isoformat(), "sha256": {"hoa_giai.xlsx": sha}},
                                                  indent=1) + "\n", "utf-8")
    kept = [r for r in out if r["keep"]]
    print(f"{name}: chốt {len(out)} dòng; giữ {len(kept)} ({dict(collections.Counter(r['part'] for r in kept))}); "
          f"loại {len(out) - len(kept)} ({dict(collections.Counter(r['drop_code'] for r in out if not r['keep']))})")


if __name__ == "__main__":
    if sys.argv[1:2] == ["gd1"]:
        build_gd1()
    elif sys.argv[1:2] == ["gd2"] and len(sys.argv) == 3:
        build_gd2(sys.argv[2])
    elif sys.argv[1:2] == ["lock"] and len(sys.argv) == 6 and sys.argv[2] in COMPARE:
        lock(*sys.argv[2:])
    elif sys.argv[1:2] == ["hoa_giai"] and len(sys.argv) == 3:
        build_hoa_giai(sys.argv[2])
    elif sys.argv[1:2] == ["chot"] and len(sys.argv) == 4:
        chot(*sys.argv[2:])
    else:
        raise SystemExit(__doc__)

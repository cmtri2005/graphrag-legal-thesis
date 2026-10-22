#!/usr/bin/env python3
"""ViLexTime D4 — bảng Excel cho người gán nhãn, và đường quay về TSV.

`crosscheck.py` giữ TSV làm bản ghi chính và tính κ từ đó. Script này chỉ lo
phần người: xuất ra Excel dễ đọc, rồi nạp nhãn ngược về TSV.

    export   -> data/review/crosscheck_{A,B}.xlsx, mỗi file ba trang tính:
               "Đọc trước"  hướng dẫn gán nhãn, rút từ docs/vilextime-annotation.md
               "Gán nhãn"   300 dòng; chỉ ba cột nhãn mở để sửa, phần còn lại khóa
               "Mã lý do"   bảy mã `reasons` và khi nào dùng
    import   đọc xlsx, kiểm từ vựng và kiểm dữ liệu chưa bị sửa, rồi ghi
             verdict/reasons/note vào TSV. Không ghi gì nếu còn một lỗi.

Ba chốt an toàn, vì gán nhãn 300 dòng xong mới phát hiện sai là mất cả buổi:

1. `verdict` là dropdown đóng. Không gõ được giá trị ngoài từ vựng, nên
   `crosscheck.py kappa` không thể từ chối sau khi đã làm xong.
2. Trang tính được bảo vệ, chỉ ba cột nhãn mở. Sửa nhầm câu hỏi hay đáp án thì
   Excel chặn ngay.
3. `import` đối chiếu lại từng ô dữ liệu với TSV và **từ chối toàn bộ** nếu có ô
   bị đổi — nhãn không bị nạp lên một nội dung đã khác.

Thứ tự dòng của B khác A (cùng 300 dòng, xáo theo lineage). `build` của
crosscheck.py ghi cùng một list cho cả hai file nên hai người đọc cùng thứ tự;
khi đó mệt mỏi và trôi dạt xảy ra ở cùng vị trí, làm κ bị thổi lên.

Usage:
    python scripts/review/crosscheck_xlsx.py export
    python scripts/review/crosscheck_xlsx.py import --who A
    python scripts/review/crosscheck_xlsx.py export --set pilot_T6     # pilot T6 (crosscheck.py pilot)
    python scripts/review/crosscheck_xlsx.py export --set kiem         # kiểm 100% (crosscheck.py kiem)
    python scripts/review/crosscheck_xlsx.py import --set kiem --who A

Phiếu `kiem` mở thêm bốn ô bắt buộc của hướng dẫn 3.0 (KIEM_FIELDS); `import` từ
chối một dòng vừa gán mà thiếu ô bắt buộc. Nhãn mang sang (D4, đợt trước) vẫn mở
để người kiểm xác nhận lại theo 3.0; giữ nguyên thì dòng giữ phiên bản cũ.
"""
from __future__ import annotations

import argparse
import collections
import csv
import difflib
import random
import re
import sys
from pathlib import Path

from openpyxl import Workbook, load_workbook
from openpyxl.cell.rich_text import CellRichText, TextBlock
from openpyxl.cell.text import InlineFont
from openpyxl.styles import Alignment, Font, PatternFill, Protection
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation

sys.path.insert(0, str(Path(__file__).resolve().parent))
from crosscheck import GUIDELINE, KIEM_FIELDS, REASONS, VERDICTS, read  # noqa: E402  một từ vựng cho cả hai

FONT = "Calibri"
SHEET = "Gán nhãn"
# `suggestion` là đề xuất, không phải bản sửa. Người gán nhãn đọc hết 300 dòng nên
# họ thấy được chỗ câu hỏi nên viết lại; giữ ý đó lại thì tiếc công, nhưng áp ngay
# thì vai trò tác giả lẫn vai trò người phán, và κ không còn đo cùng một item.
# Một lượt viết lại riêng sau D4 sẽ xử lý, kèm tăng phiên bản release.
LABEL_COLS = ("verdict", "reasons", "note", "suggestion")


def label_cols(name: str) -> tuple[str, ...]:
    return LABEL_COLS + tuple(KIEM_FIELDS) if name == "kiem" else LABEL_COLS


ORDER_SEED = 20261001          # chỉ xáo thứ tự hiển thị của B, không đổi tập dòng
WIDTHS = {"id": 34, "group": 7, "lineage_id": 30, "question": 62, "as_of": 11, "lead_in": 40,
          "answer": 62, "changed_span": 34, "citation": 20, "law_id": 16, "valid_from": 11,
          "valid_to": 11, "source_url": 30, "note_for_annotator": 30,
          "verdict": 13, "reasons": 26, "note": 34, "suggestion": 46, "adjudicated": 12,
          "lo": 5, "subgroup": 8, "short_answer": 34, "trich_van_ban_goc": 70, "trich_van_ban_tac_dong": 70,
          "da_xem_van_ban_tac_dong": 24, "cham_lan_sua": 18, "noi_dung_con_o_dau": 28, "phut": 7,
          "cac_phien_ban": 60, "goi_y_cho_moi": 80}
WRAP = {"question", "answer", "lead_in", "changed_span", "short_answer", "trich_van_ban_goc", "trich_van_ban_tac_dong",
        "cac_phien_ban", "goi_y_cho_moi", "note_for_annotator", "note", "reasons", "suggestion"}
CHANGED = InlineFont(rFont=FONT, sz=10, b=True, color="C00000")

REASON_HELP = [   # docs/vilextime-annotation.md §2, hướng dẫn 3.0
    ("question_ambiguous", "Câu hỏi khớp nhiều điều khoản hoặc nhiều mục trong danh sách; đáp án chuẩn chỉ là một trong số đó."),
    ("question_leaks", "Câu hỏi đã nói ra đáp án, nêu số hiệu/Điều/Khoản, ký hiệu mục (\"c)\"), hoặc để lộ phiên bản nào."),
    ("unanswerable_as_asked", "Đúng chủ đề nhưng đáp án không trả lời được điều câu hỏi hỏi: hỏi \"khi nào\" mà đáp án không có thời hạn, hỏi \"ai\" mà đáp án không nêu chủ thể."),
    ("group_mismatch", "Câu hỏi không làm được việc của nhóm: T2/T4 không chạm phần thay đổi; T3 không ra được 3 đáp án khác nhau; T6 CHỈ hỏi có/không; T5 hỏi vào phần không đổi."),
    ("gold_wrong", "Cột đáp án không phải phiên bản có hiệu lực tại as_of: sai phiên bản, lời văn thiếu hay thừa so với văn bản gốc, vế \"trước sửa đổi\" thực ra đã là bản sửa. Ghi note."),
    ("transitional_rule", "Điều khoản chuyển tiếp giữ bản cũ cho đúng quan hệ câu hỏi TỰ NÊU, hoặc buộc chính sự việc phát sinh tại as_of theo bản cũ. Chỉ giữ bản cũ cho việc đang thực hiện thì KHÔNG phải lỗi. Ghi Điều chuyển tiếp vào note."),
    ("relocated", "(T6) Nội dung bị bãi bỏ đã chuyển chỗ, đạt đủ 7 yếu tố. Ghi chỗ mới (văn bản, vị trí, trích đoạn) vào note."),
    ("relocation_unclear", "(T6) Không chắc có chuyển chỗ hay không. Ghi chỗ nghi vào note."),
    ("superseded_by_other_norm", "Văn bản cấp cao hơn, hoặc văn bản cùng cơ quan ban hành sau, quy định khác về cùng vấn đề mà không sửa điều khoản này. Ghi văn bản vào note."),
    ("restructuring_2025", "Ngày hỏi sau sắp xếp bộ máy (bộ: 01/03/2025; cấp huyện, tỉnh: 01/07/2025) mà đáp án vẫn nêu cơ quan, cấp, địa danh cũ chưa được sửa lời văn."),
    ("reference_only", "Đáp án chỉ là dẫn chiếu (\"thực hiện theo Thông tư X\"), không có nội dung pháp lý."),
    ("rename_only", "Lần đổi mà câu hỏi dựa vào chỉ là đổi tên cơ quan do sắp xếp bộ máy (Bộ GTVT → Bộ Xây dựng): hai mốc cùng một đáp án pháp lý."),
    ("cosmetic_only", "Lần đổi chỉ là hình thức: hoa thường, dấu câu, khoảng trắng, đánh số."),
    ("auto_reference_update", "Lần đổi chỉ cập nhật văn bản được dẫn chiếu, trong khi chính văn bản đã quy định tự áp văn bản thay thế."),
    ("other", "Lỗi khác. Bắt buộc mô tả ở cột note."),
]

# docs/vilextime-dinh-nghia.md §6: the eight checks a test row passes, in the order to make them, and the
# codes a failed check is written with (guideline 3.0 §2). The verdict is khong_dat as soon as one fails.
DECISION = [
    ("1", "Đáp án đúng là phiên bản có hiệu lực pháp lý tại as_of? Đối chiếu trich_van_ban_goc, trich_van_ban_tac_dong, "
          "cac_phien_ban: cả lời văn, cả câu dẫn lead_in.", "gold_wrong · transitional_rule"),
    ("2", "(T2, T4, T3) Câu hỏi chạm đúng chỗ đổi? Chữ đỏ trong answer và cac_phien_ban là chỗ đổi. Hai mốc phải ra hai "
          "đáp án khác nhau (T3: ít nhất ba). Ghi ngày chuyển câu hỏi chạm vào cham_lan_sua.",
     "group_mismatch · rename_only · cosmetic_only · auto_reference_update"),
    ("3", "Câu hỏi chỉ khớp MỘT điều khoản, trả lời được bằng đáp án này và chỉ một cách?",
     "question_ambiguous · unanswerable_as_asked"),
    ("4", "Câu hỏi không nêu ngày, số hiệu văn bản, Điều, Khoản, ký hiệu mục, không chép sẵn đáp án?", "question_leaks"),
    ("5", "Đáp án là nội dung pháp lý, không chỉ là \"thực hiện theo văn bản X\"?", "reference_only"),
    ("6", "Không có văn bản khác đè lên cùng vấn đề; không vướng sắp xếp bộ máy 2025?",
     "superseded_by_other_norm · restructuring_2025"),
    ("7", "(T6) Đã tìm nội dung còn ở đâu (goi_y_cho_moi là chỗ bắt đầu, không phải kết luận) và xét bảy yếu tố? "
          "Ghi kết quả vào noi_dung_con_o_dau.", "relocated · relocation_unclear"),
    ("8", "Đáp án ngắn (short_answer) đúng và đủ? Sai thì ghi đáp án ngắn đúng vào note.", "other"),
]

GROUP_HELP = [   # docs/vilextime-annotation.md §3
    ("T2/T4", "Cặp tương phản; T4 là cặp gần như y hệt. Hai dòng cùng câu hỏi, hai mốc, gán riêng từng dòng. Câu hỏi phải chạm đúng phần đổi. Đổi tên cơ quan do sắp xếp bộ máy thì rename_only. Câu hỏi chứa sẵn vế trước của đáp án: dòng ngày trước question_leaks."),
    ("T3", "Chuỗi nhiều bước. Câu hỏi phải ra ít nhất 3 đáp án khác nhau qua các mốc; chỉ tách được 2 trạng thái là group_mismatch."),
    ("T5a", "Hồi tố: văn bản sửa đổi có hiệu lực TRƯỚC ngày ký. Đáp án ở mốc trong khoảng hồi tố là nội dung MỚI. Kiểm câu hỏi có hỏi vào phần thực sự đổi."),
    ("T5b", "Đã ký, chưa có hiệu lực: mốc sau ngày ký, trước ngày hiệu lực của văn bản sửa đổi. Đáp án là nội dung CŨ."),
    ("T6a/T6b", "Bị bãi bỏ đích danh (T6a) hoặc mất hiệu lực vì điều khoản cấp trên bị bãi bỏ (T6b). Đáp án rỗng. Câu CHỈ hỏi có/không là group_mismatch. Tìm nội dung còn ở đâu: chuyển chỗ đủ 7 yếu tố thì relocated (ghi chỗ mới); không chắc thì relocation_unclear; văn bản cấp cao hơn quy định cùng vấn đề thì superseded_by_other_norm; không có kế thừa thì dat."),
]


def guide_lines(who: str, n: int, non_blind: list[str], name: str = "crosscheck") -> list[tuple[str, int, bool]]:
    """(text, cỡ chữ, in đậm) cho trang Đọc trước."""
    L: list[tuple[str, int, bool]] = []
    add = lambda t="", s=10, b=False: L.append((t, s, b))
    if name == "kiem":
        return kiem_guide(who, n, add, L)
    pilot = name == "pilot_T6"
    add(f"{'Pilot T6' if pilot else 'Kiểm chéo'} ViLexTime — người gán nhãn {who}", 15, True)
    if pilot:
        add("Gán thử T6 theo hướng dẫn 2.0 trước khi gán 92 dòng T6 của bộ kiểm chéo. Mọi dòng là T6:", 10, True)
        add("đọc kỹ quy trình bảy yếu tố chuyển chỗ ở trang này và ở docs/vilextime-annotation.md §3.", 10, True)
    add(f"Hướng dẫn phiên bản {GUIDELINE} · {n} dòng · bản đầy đủ: docs/vilextime-annotation.md", 9)
    add()
    add("Bạn đang kiểm cái gì", 12, True)
    add("Mỗi dòng là một câu hỏi pháp luật kèm MỘT MỐC THỜI GIAN (cột as_of) và đáp án chuẩn.", 10)
    add("Việc của bạn: đáp án đó có đúng là nội dung điều khoản CÓ HIỆU LỰC TẠI MỐC ĐÓ không,", 10)
    add("và câu hỏi có hỏi được bằng đáp án đó không.", 10)
    add("Bạn KHÔNG chấm câu hỏi hay hơn hoặc dở hơn. Chỉ đúng hay không đúng.", 10, True)
    add()
    add("Quy trình mỗi dòng", 12, True)
    add("1. Đọc câu hỏi, rồi mốc as_of, rồi đáp án.", 10)
    add("2. Nếu cần kiểm, mở link ở cột source_url (là văn bản BỊ sửa) và tìm tới citation.", 10)
    add("3. Điền verdict. Chọn từ dropdown, không gõ tay.", 10)
    add("4. Nếu khong_dat: điền reasons (xem trang \"Mã lý do\"), nhiều mã cách nhau bằng dấu phẩy.", 10)
    add("5. note bắt buộc khi reasons có gold_wrong hoặc other.", 10)
    add("6. Nếu bạn nghĩ câu hỏi nên viết lại cho tự nhiên hơn: ghi vào cột suggestion.", 10)
    add()
    add("Về cột suggestion — đọc kỹ chỗ này", 12, True)
    add("Bạn ĐỪNG sửa cột câu hỏi hay cột đáp án. Hai cột đó đã khóa, và đó là cố ý:", 10, True)
    add("· Cột đáp án không phải người viết. Nó là lời văn của đúng phiên bản điều khoản tại", 10)
    add("  mốc as_of, sinh ra từ đồ thị. Sửa tay thì nó không còn khớp phiên bản nào nữa.", 10)
    add("· Nếu bạn sửa câu hỏi rồi tự chấm, bạn đang chấm việc của chính mình.", 10)
    add("· Hai người sửa khác nhau thì Cohen κ không còn đo cùng một thứ.", 10)
    add("Thay vào đó, viết câu hỏi bạn cho là tốt hơn vào cột suggestion. Nó được giữ lại", 10)
    add("nguyên văn, và một lượt viết lại riêng sau đợt này sẽ xem xét áp dụng.", 10)
    add("Một dòng vẫn có thể là dat mà vẫn có suggestion — \"đúng\" và \"đã tự nhiên\" là hai việc.", 10)
    add()
    add("Hai nhãn", 12, True)
    add("dat         Đáp án đúng tại mốc, và câu hỏi hỏi được bằng đáp án đó.", 10)
    add("khong_dat   Có ít nhất một lỗi. Phải nêu reasons.", 10)
    add()
    add("Cách kiểm từng nhóm", 12, True)
    for g, h in GROUP_HELP:
        add(f"{g}   {h}", 10)
    add()
    add("Quy tắc của đợt kiểm chéo", 12, True)
    add("· Làm độc lập. KHÔNG trao đổi với người gán nhãn còn lại trong lúc làm.", 10, True)
    add(f"· Điền đủ cả {n} dòng. Bỏ trống dòng nào thì dòng đó không vào κ.", 10)
    add("· Chỉ ba cột verdict, reasons, note mở để sửa. Các cột khác đã khóa — nếu Excel", 10)
    add("  chặn bạn gõ vào đâu đó, đấy là cố ý, không phải lỗi file.", 10)
    add("· Đừng sắp xếp lại hay xóa dòng. Thứ tự hai file khác nhau là cố ý.", 10)
    add()
    add("Sau khi xong", 12, True)
    add("Gửi lại đúng file này. Hai bộ nhãn được nạp về TSV rồi tính Cohen κ và Gwet AC1.", 10)
    if pilot:
        add("Cổng pilot: hai người trùng ít nhất 17/20 dòng. Thấp hơn thì sửa hướng dẫn và thử thêm 10 dòng,", 10)
    else:
        add("Ngưỡng đăng ký trước là AC1 ≥ 0,80 và p_neg ≥ 0,60. Thấp hơn thì viết lại hướng dẫn và kiểm lại,", 10)
    add("nên nhãn trung thực quan trọng hơn nhãn đẹp.", 10)
    if non_blind:
        add()
        add("Ghi chú minh bạch", 12, True)
        add(f"{len(non_blind)} trong {n} dòng đã từng được gán nhãn ở một đợt khác. Chúng không được", 10)
        add("tách riêng ở đây để bạn làm việc như nhau trên mọi dòng; báo cáo κ sẽ liệt kê", 10)
        add("riêng các dòng đó vì chúng không còn \"mù\".", 10)
    return L


def kiem_guide(who: str, n: int, add, L: list) -> list[tuple[str, int, bool]]:
    add(f"Kiểm 100% tập test ViLexTime — người kiểm {who}", 15, True)
    add(f"Hướng dẫn phiên bản {GUIDELINE} · {n} dòng · bản đầy đủ: docs/vilextime-annotation.md · "
        "định nghĩa: docs/vilextime-dinh-nghia.md", 9)
    add()
    add("Bạn đang kiểm cái gì", 12, True)
    add("Mỗi dòng: một câu hỏi, một mốc as_of, một đáp án chuẩn. Chỉ dòng bạn kiểm xong mới vào tập test.", 10)
    add("Câu hỏi: một luật sư đọc câu hỏi, biết ngày as_of, tra đúng văn bản — có trả lời đúng bằng cột", 10)
    add("answer không, và chỉ một cách không? Có → dat. Không → khong_dat + mã lý do.", 10)
    add()
    add("Quy trình mỗi dòng", 12, True)
    add("1. Đọc câu hỏi, mốc as_of, đáp án (answer, cùng câu dẫn lead_in) và đáp án ngắn (short_answer).", 10)
    add("2. Đối chiếu với trich_van_ban_goc (văn bản bị sửa) và trich_van_ban_tac_dong (văn bản sửa, bãi bỏ:", 10)
    add("   đoạn tác động, điều khoản chuyển tiếp, điều hiệu lực). Thiếu thì mở source_url.", 10)
    add("   cac_phien_ban: mọi phiên bản của điều khoản, ngày hiệu lực, văn bản sửa, chỗ đổi; dòng này là bản ◀.", 10)
    add("   Chữ ĐỎ ĐẬM trong answer là chữ phiên bản khác của cùng điều khoản không có.", 10)
    add("   goi_y_cho_moi (T6): chỗ máy tìm thấy có thể chứa nội dung bị bãi bỏ. Chỉ là chỗ bắt đầu tìm:", 10)
    add("   bạn tự xét bảy yếu tố, máy có thể sai hoặc bỏ sót.", 10)
    add("3. Kiểm 8 điều theo trang \"Cách quyết\". Điền verdict (dropdown); khong_dat thì điền reasons", 10)
    add("   (trang \"Mã lý do\"), nhiều mã cách bằng dấu phẩy.", 10)
    add("4. Điền đủ ô bắt buộc (dưới đây). Thiếu thì file không nạp được.", 10)
    add("5. Đáp án ngắn sai hoặc thiếu: khong_dat, mã other, ghi đáp án ngắn đúng vào note.", 10)
    add()
    add("Ô bắt buộc", 12, True)
    add("da_xem_van_ban_tac_dong   Số hiệu các văn bản tác động bạn đã xem, hoặc \"không có\". Mọi dòng.", 10)
    add("cham_lan_sua              T2, T3: ngày chuyển mà câu hỏi chạm tới (vd 2019-12-01; 2024-06-01).", 10)
    add("noi_dung_con_o_dau        T6: \"không có\", hoặc chỗ mới (văn bản, Điều, Khoản), hoặc \"không chắc\".", 10)
    add("phut                      Số phút bạn dùng cho dòng này (số nguyên).", 10)
    add("note                      Bắt buộc khi có gold_wrong, relocated, superseded_by_other_norm hoặc other.", 10)
    add()
    add("Cách kiểm từng nhóm", 12, True)
    for g, h in GROUP_HELP:
        add(f"{g}   {h}", 10)
    add()
    add("Quy tắc", 12, True)
    add("· Làm độc lập, không trao đổi với người kiểm còn lại. Một phần dòng do cả hai người cùng kiểm để đo", 10, True)
    add("  đồng thuận (AC1 ≥ 0,80 và p_neg ≥ 0,60); bạn không biết là dòng nào, cứ làm như nhau.", 10, True)
    add("· Lô 0 (khoảng 20 dòng) là lô HIỆU CHUẨN: cả hai cùng làm, độc lập, gửi lại trước. Sau đó hai người cùng", 10, True)
    add("  luật sư xem các dòng lệch; kết luận ghi vào mục Hỏi đáp của hướng dẫn. Lô 0 không tính vào đồng thuận.", 10, True)
    add("· Từ lô 1, mỗi lô 40 dòng. Gửi lô 1 để đo phút mỗi dòng. Sau lô 3, 6, 9, 12, 15 đồng thuận được đo trên", 10)
    add("  các dòng chung đã làm; thấp thì hiệu chuẩn lại trên dòng mới, không sửa nhãn đã gán.", 10)
    add("· Phân vân: vẫn chọn một nhãn, ghi \"[phân vân] …\" ở note để đưa vào buổi hỏi luật sư.", 10)
    add("· Dòng đã có nhãn từ D4 (cột guideline_version 1.2 hoặc 2.0): xác nhận lại theo 3.0 và điền ô", 10)
    add("  bắt buộc. Để nguyên thì dòng vẫn tính là chưa kiểm theo 3.0.", 10)
    add("· Không sửa câu hỏi, đáp án; câu hỏi nên viết lại thì ghi vào suggestion. Đừng sắp xếp hay xóa dòng.", 10)
    add("· Máy chỉ đưa dẫn chứng (trich_..., cac_phien_ban, goi_y_cho_moi, note_for_annotator), không có nhãn nào", 10)
    add("  do máy gán trong phiếu.", 10)
    return L


def sheet_decision(wb: Workbook) -> None:
    ws = wb.create_sheet("Cách quyết")
    for col, (head, width) in enumerate((("#", 4), ("Kiểm theo thứ tự (định nghĩa §6)", 96), ("Không đạt → mã", 44)), 1):
        c = ws.cell(1, col, head)
        c.font = Font(name=FONT, bold=True, color="FFFFFF")
        c.fill = PatternFill("solid", fgColor="44546A")
        ws.column_dimensions[get_column_letter(col)].width = width
    for i, row in enumerate(DECISION, 2):
        for col, text in enumerate(row, 1):
            c = ws.cell(i, col, text)
            c.font = Font(name=FONT, size=10, bold=col == 1)
            c.alignment = Alignment(vertical="top", wrap_text=True)
        ws.row_dimensions[i].height = 44
    tail = len(DECISION) + 3
    for k, text in enumerate((
            "Đạt cả 8 → dat. Một ô không đạt → khong_dat, ghi mọi mã tương ứng ở reasons.",
            "Phân vân: vẫn chọn một nhãn theo câu hỏi nền (luật sư tra đúng văn bản có trả lời đúng bằng đáp án này, "
            "và chỉ một cách?), rồi ghi \"[phân vân] …\" ở note để đưa vào buổi hỏi luật sư.",
            "Gợi ý của máy (cac_phien_ban, goi_y_cho_moi, note_for_annotator) chỉ nói chỗ cần nhìn, không nói nhãn.")):
        ws.cell(tail + k, 2, text).font = Font(name=FONT, size=10, italic=True)
    ws.freeze_panes = "A2"


def changed_spans(text: str, others: list[str]) -> list[tuple[int, int]]:
    """Character spans of `text` whose words another version of the provision does not have."""
    tokens = [(m.start(), m.end(), m.group()) for m in re.finditer(r"\S+", text)]
    marked: set[int] = set()
    for other in others:
        ops = difflib.SequenceMatcher(a=[w for _, _, w in tokens], b=other.split(), autojunk=False).get_opcodes()
        marked.update(i for op, i1, i2, _, _ in ops if op in ("replace", "delete") for i in range(i1, i2))
    spans: list[tuple[int, int]] = []
    for i in sorted(marked):
        if spans and i - 1 in marked:
            spans[-1] = (spans[-1][0], tokens[i][1])
        else:
            spans.append((tokens[i][0], tokens[i][1]))
    return spans


def highlighted(text: str, spans: list[tuple[int, int]]) -> CellRichText | str:
    """`text` unchanged, its changed spans in bold red: the import still reads back the plain string."""
    if not spans:
        return text
    parts, at = [], 0
    for start, end in spans:
        parts += [text[at:start]] if start > at else []
        parts.append(TextBlock(CHANGED, text[start:end]))
        at = end
    parts += [text[at:]] if at < len(text) else []
    return CellRichText(parts)


def sheet_guide(wb: Workbook, who: str, n: int, non_blind: list[str], name: str = "crosscheck") -> None:
    ws = wb.active
    ws.title = "Đọc trước"
    for i, (text, size, bold) in enumerate(guide_lines(who, n, non_blind, name), 1):
        c = ws.cell(i, 1, text)
        c.font = Font(name=FONT, size=size, bold=bold)
        c.alignment = Alignment(vertical="top")
    ws.column_dimensions["A"].width = 112
    ws.sheet_view.showGridLines = False


def sheet_reasons(wb: Workbook) -> None:
    ws = wb.create_sheet("Mã lý do")
    for col, (name, width) in enumerate((("Mã", 24), ("Khi nào dùng", 104)), 1):
        c = ws.cell(1, col, name)
        c.font = Font(name=FONT, bold=True, color="FFFFFF")
        c.fill = PatternFill("solid", fgColor="44546A")
        ws.column_dimensions[get_column_letter(col)].width = width
    for i, (code, help_text) in enumerate(REASON_HELP, 2):
        ws.cell(i, 1, code).font = Font(name=FONT, size=10, bold=True)
        c = ws.cell(i, 2, help_text)
        c.font = Font(name=FONT, size=10)
        c.alignment = Alignment(vertical="top", wrap_text=True)
        ws.row_dimensions[i].height = 32
    ws.cell(len(REASON_HELP) + 3, 1, "Chỉ điền reasons khi verdict = khong_dat.").font = \
        Font(name=FONT, size=10, italic=True)
    ws.freeze_panes = "A2"


def sheet_labels(wb: Workbook, columns: list[str], rows: list[dict], set_name: str = "crosscheck") -> None:
    labels = label_cols(set_name)
    ws = wb.create_sheet(SHEET)
    for col, name in enumerate(columns, 1):
        c = ws.cell(1, col, name)
        c.font = Font(name=FONT, bold=True, color="FFFFFF")
        c.fill = PatternFill("solid", fgColor="44546A" if name not in labels else "2F6B3A")
        c.alignment = Alignment(vertical="center", wrap_text=True)
        ws.column_dimensions[get_column_letter(col)].width = WIDTHS.get(name, 18)
    editable = PatternFill("solid", fgColor="EAF3EC")
    reopen = labels != LABEL_COLS          # kiem: a carried label is re-confirmed under 3.0
    versions = collections.defaultdict(set)   # a lineage's rows sit in one file: its versions are all here
    for row in rows:
        if row.get("answer") and not row["answer"].startswith("(không có đáp án"):
            versions[row.get("lineage_id")].add(row["answer"])
    for r, row in enumerate(rows, 2):
        for col, field in enumerate(columns, 1):
            value = row.get(field) or ""
            if field == "answer" and value:
                value = highlighted(value, changed_spans(value, sorted(versions[row.get("lineage_id")] - {value})))
            c = ws.cell(r, col, value)
            c.font = Font(name=FONT, size=10)
            c.alignment = Alignment(vertical="top", wrap_text=field in WRAP)
            if field in labels and (reopen or not row.get("verdict")):   # a carried raw label stays as it was
                c.protection, c.fill = Protection(locked=False), editable
            else:
                c.protection = Protection(locked=True)
            if field == "source_url" and row.get(field):
                c.hyperlink = row[field]
                c.font = Font(name=FONT, size=10, color="0563C1", underline="single")
    verdict = DataValidation(type="list", formula1='"' + ",".join(sorted(VERDICTS)) + '"',
                             allow_blank=True, showErrorMessage=True)
    verdict.errorTitle, verdict.error = "Chỉ hai giá trị", f"verdict chỉ nhận: {', '.join(sorted(VERDICTS))}"
    ws.add_data_validation(verdict)
    letter = get_column_letter(columns.index("verdict") + 1)
    verdict.add(f"{letter}2:{letter}{len(rows) + 1}")
    ws.freeze_panes = ws.cell(2, columns.index("question") + 1).coordinate
    ws.auto_filter.ref = f"A1:{get_column_letter(len(columns))}{len(rows) + 1}"
    # Khóa trang, mở ba cột nhãn. Rào chắn chống sửa nhầm, không phải bảo mật.
    ws.protection.sheet = True
    ws.protection.enable()


def ordered(rows: list[dict], who: str, name: str = "crosscheck") -> list[dict]:
    """Thứ tự hiển thị. B xáo theo lineage; cùng tập dòng, khác thứ tự đọc. `kiem` đã xáo riêng từng file."""
    if who == "A" or name == "kiem":
        return list(rows)
    groups = collections.defaultdict(list)
    for r in rows:
        groups[r["lineage_id"]].append(r)
    lineages = sorted(groups)
    random.Random(ORDER_SEED).shuffle(lineages)
    return [r for lid in lineages for r in groups[lid]]


def export(data: Path, name: str = "crosscheck") -> None:
    labels = data / "review/labels.tsv"
    known = {r.get("id") for r in read(labels)} if labels.exists() else set()
    for who in ("A", "B"):
        tsv = data / f"review/{name}_{who}.tsv"
        rows = read(tsv)
        # TSV labels are fine (crosscheck.py build carries an earlier draw's labels over);
        # what must not be overwritten is labelling done in the workbook and not imported yet.
        xlsx = data / f"review/{name}_{who}.xlsx"
        if xlsx.exists():
            have = {r["id"]: (r.get("verdict") or "").strip() for r in rows}
            ws = load_workbook(xlsx, data_only=True)[SHEET]
            head = [c.value for c in ws[1]]
            pending = [row[head.index("id")] for row in ws.iter_rows(min_row=2, values_only=True)
                       if row[head.index("id")] and str(row[head.index("verdict")] or "").strip()
                       and have.get(row[head.index("id")]) != str(row[head.index("verdict")]).strip()]
            if pending:
                raise SystemExit(f"{xlsx} có {len(pending)} nhãn chưa nạp về TSV (chạy import trước); không xuất lại")
        with tsv.open(encoding="utf-8", newline="") as f:
            columns = next(csv.reader(f, delimiter="\t"))
        if name != "kiem" and "suggestion" not in columns:
            # Ngay sau `note`, để bốn cột người gán nhãn điền nằm liền nhau và
            # `adjudicated` (của bước hoà giải, không phải của họ) ở sau cùng.
            at = columns.index("note") + 1
            columns = columns[:at] + ["suggestion"] + columns[at:]
        non_blind = [r["id"] for r in rows if r["id"] in known]
        wb = Workbook()
        sheet_guide(wb, who, len(rows), non_blind, name)
        if name == "kiem":
            sheet_decision(wb)
        sheet_reasons(wb)
        sheet_labels(wb, columns, ordered(rows, who, name), name)
        out = data / f"review/{name}_{who}.xlsx"
        wb.save(out)
        print(f"{out}  {len(rows)} dòng · {len(non_blind)} dòng không còn mù · "
              f"thứ tự {'như TSV' if who == 'A' or name == 'kiem' else 'xáo theo lineage'}")


def missing_fields(group: str, cells: dict) -> list[str]:
    """Guideline 3.0 §5: what a row just labelled in a `kiem` sheet still lacks."""
    has = lambda c: str(cells.get(c) or "").strip()
    out = [] if has("da_xem_van_ban_tac_dong") else ["thiếu da_xem_van_ban_tac_dong"]
    if group in ("T2", "T3") and not has("cham_lan_sua"):
        out.append("T2/T3 thiếu cham_lan_sua")
    if group == "T6" and not has("noi_dung_con_o_dau"):
        out.append("T6 thiếu noi_dung_con_o_dau")
    if not has("phut").isdigit():
        out.append("phut phải là số phút (số nguyên)")
    return out


def ingest(data: Path, who: str, name: str = "crosscheck") -> None:
    xlsx, tsv = data / f"review/{name}_{who}.xlsx", data / f"review/{name}_{who}.tsv"
    ws = load_workbook(xlsx, data_only=True)[SHEET]
    head = [c.value for c in ws[1]]
    got = {}
    for row in ws.iter_rows(min_row=2, values_only=True):
        cells = dict(zip(head, row))
        if cells.get("id"):
            got[cells["id"]] = cells
    rows = read(tsv)
    labels = label_cols(name)
    errors: list[str] = []
    out_columns = list(head) + [c for c in ("guideline_version",) if c not in head]
    if len(got) != len(rows):
        errors.append(f"xlsx có {len(got)} dòng, tsv có {len(rows)}")
    for r in rows:
        src = got.get(r["id"])
        if src is None:
            errors.append(f"{r['id']}: thiếu trong xlsx")
            continue
        # Dữ liệu phải y nguyên: nhãn không được nạp lên một nội dung đã khác.
        for col in head:
            if col in labels or col == "adjudicated":
                continue
            if (str(src.get(col) or "").strip()) != (r.get(col) or "").strip():
                errors.append(f"{r['id']}: cột `{col}` đã bị sửa trong xlsx")
        verdict = str(src.get("verdict") or "").strip()
        if (r.get("verdict") or "").strip() and not verdict:
            # the TSV is the record: a label saved by label_ui.py after this xlsx was exported must not be blanked
            errors.append(f"{r['id']}: TSV có nhãn mà xlsx trống (xlsx cũ hơn TSV, vd nhãn lưu từ label_ui.py); xuất lại xlsx")
        if verdict and verdict not in VERDICTS:
            errors.append(f"{r['id']}: verdict `{verdict}` ngoài từ vựng")
        codes = [c.strip() for c in str(src.get("reasons") or "").split(",") if c.strip()]
        for code in codes:
            if code not in REASONS:
                errors.append(f"{r['id']}: reasons `{code}` ngoài từ vựng")
        note = str(src.get("note") or "").strip()
        if verdict == "khong_dat" and not codes:
            errors.append(f"{r['id']}: khong_dat nhưng thiếu reasons")
        if verdict == "dat" and codes:
            errors.append(f"{r['id']}: dat nhưng vẫn có reasons")
        needs_note = {"gold_wrong", "other"} | ({"relocated", "superseded_by_other_norm"} if name == "kiem" else set())
        if needs_note & set(codes) and not note:
            errors.append(f"{r['id']}: {'/'.join(sorted(needs_note & set(codes)))} bắt buộc có note")
        if name == "kiem" and verdict and any(str(src.get(c) or "").strip() != (r.get(c) or "").strip()
                                              for c in labels):
            errors += [f"{r['id']}: {m}" for m in missing_fields(r["group"], src)]
    if errors:
        print(f"{len(errors)} lỗi — KHÔNG ghi gì vào {tsv}:", file=sys.stderr)
        for e in errors[:40]:
            print(f"  {e}", file=sys.stderr)
        raise SystemExit(1)
    for r in rows:
        new = {col: str(got[r["id"]].get(col) or "").strip() for col in labels}
        # compared as the checks above compare: Excel drops a trailing space nobody typed
        if any(new[c] != (r.get(c) or "").strip() for c in labels):
            r["guideline_version"] = GUIDELINE if new["verdict"] else ""   # labelled now, under today's guide
        else:                                    # unchanged: keeps its version; no version means 1.2 (crosscheck.py)
            r["guideline_version"] = (r.get("guideline_version") or "1.2") if new["verdict"] else ""
        r.update(new)
    with tsv.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=out_columns, delimiter="\t", lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    filled = sum(1 for r in rows if r["verdict"])
    print(f"{tsv}: nạp {filled}/{len(rows)} nhãn "
          f"({dict(collections.Counter(r['verdict'] for r in rows if r['verdict']))})")
    print(f"tiếp: python scripts/review/crosscheck.py kappa --set {name}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("command", choices=("export", "import"))
    ap.add_argument("--data", type=Path, default=Path("data"))
    ap.add_argument("--who", choices=("A", "B"), help="bắt buộc với import")
    ap.add_argument("--set", default="crosscheck", choices=("crosscheck", "pilot_T6", "kiem"))
    args = ap.parse_args()
    if args.command == "export":
        export(args.data, args.set)
    else:
        if not args.who:
            ap.error("import cần --who A hoặc --who B")
        ingest(args.data, args.who, args.set)


if __name__ == "__main__":
    main()

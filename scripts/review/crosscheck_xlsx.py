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
"""
from __future__ import annotations

import argparse
import collections
import csv
import random
import sys
from pathlib import Path

from openpyxl import Workbook, load_workbook
from openpyxl.styles import Alignment, Font, PatternFill, Protection
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation

sys.path.insert(0, str(Path(__file__).resolve().parent))
from crosscheck import GUIDELINE, REASONS, VERDICTS, read  # noqa: E402  một từ vựng cho cả hai

FONT = "Calibri"
SHEET = "Gán nhãn"
# `suggestion` là đề xuất, không phải bản sửa. Người gán nhãn đọc hết 300 dòng nên
# họ thấy được chỗ câu hỏi nên viết lại; giữ ý đó lại thì tiếc công, nhưng áp ngay
# thì vai trò tác giả lẫn vai trò người phán, và κ không còn đo cùng một item.
# Một lượt viết lại riêng sau D4 sẽ xử lý, kèm tăng phiên bản release.
LABEL_COLS = ("verdict", "reasons", "note", "suggestion")
ORDER_SEED = 20261001          # chỉ xáo thứ tự hiển thị của B, không đổi tập dòng
WIDTHS = {"id": 34, "group": 7, "lineage_id": 30, "question": 62, "as_of": 11, "lead_in": 40,
          "answer": 62, "changed_span": 34, "citation": 20, "law_id": 16, "valid_from": 11,
          "valid_to": 11, "source_url": 30, "note_for_annotator": 30,
          "verdict": 13, "reasons": 26, "note": 34, "suggestion": 46, "adjudicated": 12}

REASON_HELP = [
    ("question_ambiguous", "Câu hỏi khớp nhiều điều khoản hoặc nhiều mục trong danh sách; đáp án chuẩn chỉ là một trong số đó."),
    ("question_leaks", "Câu hỏi đã nói ra đáp án, nêu số hiệu/Điều/Khoản, ký hiệu mục (\"c)\"), hoặc để lộ phiên bản nào."),
    ("gold_wrong", "Cột đáp án không đúng là điều khoản có hiệu lực tại as_of: sai phiên bản, vế \"trước sửa đổi\" thực ra đã là bản sửa, text bị cắt mất phần được hỏi, hoặc (T6) đáp án rỗng trong khi nội dung đã chuyển chỗ."),
    ("group_mismatch", "Câu hỏi không làm được việc của nhóm. T2 không chạm chỗ thay đổi (hai mốc trả lời như nhau); T3 chỉ chạm một lần sửa; T6 hỏi kiểu có/không; T5 hỏi vào phần không đổi."),
    ("unanswerable_as_asked", "Đúng chủ đề nhưng không thể trả lời bằng đáp án: hỏi \"khi nào\" mà đáp án không nói thời hạn, hỏi \"ai\" mà đáp án không nêu chủ thể."),
    ("transitional_rule", "Điều khoản chuyển tiếp giữ quy định cũ cho đúng quan hệ câu hỏi tự nêu (ví dụ hồ sơ nộp trước ngày hiệu lực), hoặc cho chính sự việc phát sinh tại as_of. Câu hỏi không nêu gì thì hiểu sự việc phát sinh tại as_of: điều khoản chỉ giữ bản cũ cho việc đang thực hiện KHÔNG phải lỗi. Ghi Điều chuyển tiếp vào note."),
    ("other", "Lỗi khác. Bắt buộc mô tả ở cột note."),
]

GROUP_HELP = [
    ("T2", "Cặp tương phản (gồm cả cặp gần giống). Hai dòng cùng lineage, hai mốc. Luật sư trả lời giống nhau ở cả hai ngày thì group_mismatch, kể cả khi chỉ đổi cách viết cùng một điều. Câu hỏi chứa sẵn vế trước của đáp án: dòng ngày trước question_leaks. Đổi chủ thể giữa hai mốc: dòng ngày sau gold_wrong, ghi note."),
    ("T3", "Chuỗi từ ba phiên bản. Câu hỏi phải chạm vào phần đổi qua NHIỀU lần sửa, không chỉ một lần."),
    ("T5", "Hiệu lực hồi tố: văn bản có hiệu lực TRƯỚC ngày ký. Cột note_for_annotator ghi ngày ký và ngày hiệu lực. Kiểm xem câu hỏi có hỏi vào phần thực sự thay đổi."),
    ("T6", "Hết hiệu lực một phần ở cấp Khoản/Điểm. Cột đáp án ghi \"(không có đáp án: ...)\". Câu hỏi không được là dạng có/không. Nếu nội dung đã CHUYỂN CHỖ (đạt đủ 7 yếu tố, hướng dẫn §3) thì đáp án rỗng là sai: khong_dat, gold_wrong, ghi chỗ mới vào note. Không chắc thì vẫn dat (nếu không có lỗi khác) và ghi \"unclear\" vào note."),
]


def guide_lines(who: str, n: int, non_blind: list[str], name: str = "crosscheck") -> list[tuple[str, int, bool]]:
    """(text, cỡ chữ, in đậm) cho trang Đọc trước."""
    L: list[tuple[str, int, bool]] = []
    add = lambda t="", s=10, b=False: L.append((t, s, b))
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


def sheet_labels(wb: Workbook, columns: list[str], rows: list[dict]) -> None:
    ws = wb.create_sheet(SHEET)
    for col, name in enumerate(columns, 1):
        c = ws.cell(1, col, name)
        c.font = Font(name=FONT, bold=True, color="FFFFFF")
        c.fill = PatternFill("solid", fgColor="44546A" if name not in LABEL_COLS else "2F6B3A")
        c.alignment = Alignment(vertical="center", wrap_text=True)
        ws.column_dimensions[get_column_letter(col)].width = WIDTHS.get(name, 18)
    editable = PatternFill("solid", fgColor="EAF3EC")
    for r, row in enumerate(rows, 2):
        for col, name in enumerate(columns, 1):
            c = ws.cell(r, col, row.get(name) or "")
            c.font = Font(name=FONT, size=10)
            c.alignment = Alignment(vertical="top", wrap_text=name in
                                    ("question", "answer", "lead_in", "changed_span",
                                     "note_for_annotator", "note", "reasons", "suggestion"))
            if name in LABEL_COLS and not row.get("verdict"):   # a carried raw label stays as it was
                c.protection, c.fill = Protection(locked=False), editable
            else:
                c.protection = Protection(locked=True)
            if name == "source_url" and row.get(name):
                c.hyperlink = row[name]
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


def ordered(rows: list[dict], who: str) -> list[dict]:
    """Thứ tự hiển thị. B xáo theo lineage; cùng tập dòng, khác thứ tự đọc."""
    if who == "A":
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
        if "suggestion" not in columns:
            # Ngay sau `note`, để bốn cột người gán nhãn điền nằm liền nhau và
            # `adjudicated` (của bước hoà giải, không phải của họ) ở sau cùng.
            at = columns.index("note") + 1
            columns = columns[:at] + ["suggestion"] + columns[at:]
        non_blind = [r["id"] for r in rows if r["id"] in known]
        wb = Workbook()
        sheet_guide(wb, who, len(rows), non_blind, name)
        sheet_reasons(wb)
        sheet_labels(wb, columns, ordered(rows, who))
        out = data / f"review/{name}_{who}.xlsx"
        wb.save(out)
        print(f"{out}  {len(rows)} dòng · {len(non_blind)} dòng không còn mù · "
              f"thứ tự {'như TSV' if who == 'A' else 'xáo theo lineage'}")


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
            if col in LABEL_COLS or col == "adjudicated":
                continue
            if (str(src.get(col) or "").strip()) != (r.get(col) or "").strip():
                errors.append(f"{r['id']}: cột `{col}` đã bị sửa trong xlsx")
        verdict = str(src.get("verdict") or "").strip()
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
        if {"gold_wrong", "other"} & set(codes) and not note:
            errors.append(f"{r['id']}: gold_wrong/other bắt buộc có note")
    if errors:
        print(f"{len(errors)} lỗi — KHÔNG ghi gì vào {tsv}:", file=sys.stderr)
        for e in errors[:40]:
            print(f"  {e}", file=sys.stderr)
        raise SystemExit(1)
    for r in rows:
        new = {col: str(got[r["id"]].get(col) or "").strip() for col in LABEL_COLS}
        if any(new[c] != (r.get(c) or "") for c in LABEL_COLS):
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
    ap.add_argument("--set", default="crosscheck", choices=("crosscheck", "pilot_T6"))
    args = ap.parse_args()
    if args.command == "export":
        export(args.data, args.set)
    else:
        if not args.who:
            ap.error("import cần --who A hoặc --who B")
        ingest(args.data, args.who, args.set)


if __name__ == "__main__":
    main()

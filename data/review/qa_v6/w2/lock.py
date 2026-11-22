"""Khóa phiếu W2 sau khi người chấm nộp: kiểm đủ ô, ghi TSV và sha256 của xlsx gốc.

python3 data/review/qa_v6/w2/lock.py pass1 A     (hoặc pilot A)
Ghi <phase>_<who>.tsv và một dòng vào SHA256SUMS. Từ chối nếu thiếu điểm, điểm ngoài thang, hoặc đã khóa.
"""
import csv
import hashlib
import sys
from pathlib import Path

from openpyxl import load_workbook

HERE = Path(__file__).resolve().parent
REQUIRED = {"ro_nghia": {"1", "2", "3", "4", "5"}, "tu_nhien": {"1", "2", "3", "4", "5"}, "da_gap": {"có", "không"},
            "tra_loi_duy_nhat": {"có", "không", "không chắc"}, "lo_dap_an": {"có", "không"}}


def cell(v):
    return "" if v is None else str(int(v) if isinstance(v, float) and v.is_integer() else v).strip()


def main(phase, who):
    src, out = HERE / f"{phase}_{who}.xlsx", HERE / f"{phase}_{who}.tsv"
    if out.exists() or (HERE / f"{phase}_{who}.1.tsv").exists():
        raise SystemExit(f"{out.name} đã khóa")
    wb, bad, sheets = load_workbook(src, data_only=True), [], []
    for ws in wb.worksheets[1:]:
        head = [c.value for c in ws[1]]
        rows = [dict(zip(head, map(cell, r))) for r in ws.iter_rows(min_row=2, values_only=True) if r[0]]
        bad += [f"{ws.title} {r['khoa']} {c}={r[c]!r}" for r in rows for c in REQUIRED if c in r and r[c] not in REQUIRED[c]]
        sheets.append((out if len(wb.worksheets) == 2 else HERE / f"{phase}_{who}.{ws.title[-1]}.tsv", head, rows))
    if bad:
        raise SystemExit("Trả lại phiếu, còn ô thiếu hoặc sai:\n" + "\n".join(bad[:40]))
    for path, head, rows in sheets:
        with path.open("w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, head, delimiter="\t", lineterminator="\n")
            w.writeheader()
            w.writerows(rows)
    digest = hashlib.sha256(src.read_bytes()).hexdigest()
    with (HERE / "SHA256SUMS").open("a", encoding="utf-8") as f:
        f.write(f"{digest}  {src.name}\n")
    print(f"khóa {src.name} sha256 {digest[:12]}")


if __name__ == "__main__":
    main(*sys.argv[1:3])

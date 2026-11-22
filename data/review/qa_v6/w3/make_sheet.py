"""Phiếu người xác nhận ứng viên W3 (đăng ký trước §3, S10).

Lấy mọi ứng viên có affects_rows = true từ các file *.candidates.jsonl, trừ 6 lỗi đã biết (đã sửa ở 5.x).
Ứng viên mà văn bản tác động có hiệu lực sau mọi dòng của lineage thì không đổi được đáp án nào, nên không đưa vào
phiếu (S10). Phiếu không có đáp án kho hay loại ứng viên; khóa -> loại nằm ở xac_nhan_key.tsv.
python3 data/review/qa_v6/w3/make_sheet.py
"""
import csv
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "w2"))
import build as w2  # noqa: E402  (reuse the xlsx sheet writer)

KNOWN = {"92/2017/NĐ-CP", "53/2012/NĐ-CP", "145/2020/NĐ-CP", "221/2013/NĐ-CP", "32/2016/TT-NHNN", "36/2026/TT-BXD"}
COLS = ["khoa", "van_ban", "dieu_khoan", "link", "van_ban_tac_dong", "quan_he", "ngay_hieu_luc_theo_agent",
        "nguon_agent", "trich_agent", "cham_dieu_khoan", "ngay_hieu_luc_dung", "can_cu", "phut", "ghi_chu"]
GUIDE = [
    "W3 — xác nhận văn bản tác động",
    "Mỗi dòng: một văn bản (cột van_ban_tac_dong) mà một agent AI cho là có thể đã sửa, thay thế hoặc bãi bỏ điều khoản ở cột dieu_khoan.",
    "AI có thể sai. Hãy tự mở văn bản tác động (Công báo, vbpl, VBHN) và đọc điều khoản sửa đổi, hiệu lực thi hành của nó.",
    "cham_dieu_khoan: có = văn bản này sửa, thay thế, bãi bỏ hoặc làm hết hiệu lực chính điều khoản đó (hoặc Điều, Chương, cả văn bản chứa nó);",
    "   không = không chạm;  không rõ = không quyết được (ghi lý do).",
    "ngay_hieu_luc_dung: ngày tác động có hiệu lực (YYYY-MM-DD), nếu cham_dieu_khoan = có.",
    "can_cu: điều, khoản của văn bản tác động làm căn cứ, kèm trích ngắn nguyên văn.",
    "phut: số phút cho dòng này. Không mở thư mục data/review/ của dự án.",
]


def main():
    cands = [c for f in sorted(HERE.glob("*.candidates.jsonl")) for c in map(json.loads, open(f, encoding="utf-8"))
             if c["affects_rows"] and c["actor_number"] not in KNOWN]
    meta = {json.loads(x)["lineage_id"]: json.loads(x) for f in HERE.glob("*_batch.jsonl") for x in open(f, encoding="utf-8")}
    rows, key = [], []
    for i, c in enumerate(cands, 1):
        k, t = f"X{i:02d}", meta[c["lineage_id"]]
        rows.append({"khoa": k, "van_ban": t["title"], "dieu_khoan": c["citation"], "link": t["source_url"],
                     "van_ban_tac_dong": c["actor_number"], "quan_he": c["relation"],
                     "ngay_hieu_luc_theo_agent": c["effective_on"] or "", "nguon_agent": c["source_url"] or "",
                     "trich_agent": c["quote"] or ""})
        key.append({"khoa": k, "batch_key": c["key"], "lineage_id": c["lineage_id"], "actor_number": c["actor_number"],
                    "candidate_kind": c["candidate_kind"]})
    with open(HERE / "xac_nhan_key.tsv", "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, list(key[0]), delimiter="\t", lineterminator="\n")
        w.writeheader()
        w.writerows(key)
    w2.FILL = {"cham_dieu_khoan", "ngay_hieu_luc_dung", "can_cu", "phut", "ghi_chu"}
    w2.CHOICES = {"cham_dieu_khoan": "có,không,không rõ"}
    w2.workbook(HERE / "xac_nhan.xlsx", [(GUIDE, "Xác nhận", COLS, rows)])


if __name__ == "__main__":
    main()

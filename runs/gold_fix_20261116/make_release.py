"""ADR 0006 §7: giữ dòng mà gold mù cho thấy gold sai, với gold đã sửa. Ghi bản release đã sửa vào OUT;
không sửa data/vilextime_final. Dùng: make_release.py OUT [SRC] [LINEAGES]
  SRC: thư mục có vilextime.jsonl + vilextime_meta.jsonl (mặc định data/vilextime_final)
  LINEAGES: chỉ giữ các lineage trong file này (một id mỗi dòng), cho phần có gold mù.
Ba lỗi kho do người đọc mù phát hiện (data/review/gold_final):
  F019 (luật sư 16/11): TT 36/2026/TT-BXD Điều 16 bãi bỏ TT 11/2021/TT-BXD từ 01/07/2026 -> không có đáp án.
  F060 (NMT 15/11): khoản 2 Điều 1 TT 32/2016/TT-NHNN sửa khoản 1 Điều 4 TT 23/2014/TT-NHNN từ 01/03/2017;
        lời văn mới trùng phiên bản 2 của kho (kho ghi từ 2019-03-01) -> các dòng 2017-03-01..2019-02-28 trỏ phiên bản 2.
  F016 (NMT 15/11): khoản 9 Điều 2 NĐ 92/2017/NĐ-CP sửa điểm b khoản 2 Điều 20 NĐ 20/2008/NĐ-CP từ 25/09/2017;
        kho không có phiên bản này. Đáp án ngắn "Phối hợp với Văn phòng Chính phủ" (trùng phiên bản 1); lời văn theo NMT.
"""
import json, sys
from pathlib import Path
OUT = Path(sys.argv[1]); SRC = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("data/vilextime_final")
KEEP = set(Path(sys.argv[3]).read_text().split()) if len(sys.argv) > 3 else None
P7, PA, PF = ("provision:7ba9e014-eb7b-11f0-954d-af330569649d", "provision:a16089ba-2d53-11f1-87d7-6598c119b283",
              "provision:4cee6a60-eb71-11f0-ac45-154b0d915a56")
F016_TEXT = ("2. Các Bộ, cơ quan ngang Bộ và Ủy ban nhân dân cấp tỉnh có trách nhiệm:\nb) Phối hợp với Văn phòng Chính phủ "
             "để kết nối, tích hợp, trao đổi dữ liệu điện tử các phản ánh, kiến nghị về quy định hành chính giữa Cổng thông tin "
             "điện tử các bộ, ngành, địa phương và Hệ thống thông tin tiếp nhận, xử lý phản ánh, kiến nghị về quy định hành chính; "
             "cập nhật tình hình, kết quả xử lý phản ánh, kiến nghị vào Hệ thống thông tin tiếp nhận, xử lý phản ánh, kiến nghị "
             "theo hướng dẫn của Văn phòng Chính phủ.")
rel = {r["id"]: r for r in map(json.loads, (SRC / "vilextime.jsonl").open(encoding="utf-8"))}
meta = {m["id"]: m for m in map(json.loads, (SRC / "vilextime_meta.jsonl").open(encoding="utf-8"))}
v2 = next(r for r in rel.values() if r["lineage_id"] == PA and r["version_id"] == f"version:{PA[len('provision:'):]}:2")
v1 = next(r for r in rel.values() if r["lineage_id"] == P7 and r["version_id"] == f"version:{P7[len('provision:'):]}:1")
fixed = []
for rid, r in rel.items():
    m, when = meta[rid], r["as_of"]
    if r["lineage_id"] == PF and when >= "2026-07-01":
        r.update(answerable=False, answer=None, context=None, version_id=None)
        m.update(no_answer_reason="provision_repealed", in_force=False, valid_to="2026-07-01")
    elif r["lineage_id"] == PA and "2017-03-01" <= when < "2019-03-01":
        r.update(answer=v2["answer"], context=v2["context"], version_id=v2["version_id"], accepted_evidence=v2["accepted_evidence"])
        m.update(valid_from="2017-03-01", valid_to=None, utilized_version_ids=[v2["version_id"]])
    elif r["lineage_id"] == P7 and when >= "2017-09-25":
        r.update(answer=v1["answer"], context=F016_TEXT, version_id=v1["version_id"])
        m.update(valid_from="2017-09-25", valid_to=None, utilized_version_ids=[v1["version_id"]])
    else:
        continue
    fixed.append(rid)
print("sửa", len(fixed), "dòng:", *sorted(fixed), sep="\n  ")
for name, rows in (("vilextime.jsonl", rel), ("vilextime_meta.jsonl", meta)):
    with (OUT / name).open("w", encoding="utf-8") as f:
        for rid, r in rows.items():
            if KEEP is None or (rel[rid]["lineage_id"] in KEEP):
                f.write(json.dumps(r, ensure_ascii=False) + "\n")

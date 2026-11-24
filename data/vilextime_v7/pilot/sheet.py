"""Phiếu chấm mù chạy thử: mỗi lineage hai câu hỏi (câu cũ Opus/DeepSeek, câu mới Qwen + prompt mới), xáo thứ tự.

Ghi pilot_cham.xlsx (cho người chấm) và pilot_cham_key.tsv (khoa -> model; KHÔNG đưa người chấm).
Tiêu chí theo hướng dẫn gán nhãn Q2, Q3 (docs/vilextime-annotation.md) và thang tự nhiên của W2.
python3 data/vilextime_v7/pilot/sheet.py
"""
import collections
import csv
import json
import random
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / "data/review/qa_v6/w2"))
import build as w2  # noqa: E402  (xlsx writer)

COLS = ["khoa", "loi_van_dieu_khoan", "cau_hoi", "hoi_vao_cho_doi", "tra_loi_duy_nhat", "lo_dap_an", "tu_nhien", "ghi_chu"]
GUIDE = [
    "Chạy thử viết câu hỏi — chấm từng câu hỏi",
    "Mỗi điều khoản có hai câu hỏi do hai cách viết khác nhau. Chấm từng câu độc lập, không đoán câu nào của cách nào.",
    "loi_van_dieu_khoan: lời văn mọi phiên bản của điều khoản, theo thứ tự thời gian.",
    "hoi_vao_cho_doi: có = câu trả lời đúng khác nhau giữa các phiên bản (T3: ít nhất 3 đáp án khác nhau);",
    "   không = các phiên bản trả lời như nhau, hoặc chỉ khác hình thức; với điều khoản bị bãi bỏ: không = chỉ hỏi có/không.",
    "tra_loi_duy_nhat: có = ở MỖI phiên bản, chỉ điều khoản này trả lời được, và một cách;",
    "   không = điều khoản khác (khoản, điểm bên cạnh) cũng trả lời được, hoặc có phiên bản không trả lời được ý được hỏi.",
    "lo_dap_an: có = câu hỏi chứa sẵn đáp án, hoặc nêu cụm từ chỉ một phiên bản có.",
    "tu_nhien: 1 = không ai hỏi như vậy; 3 = gượng; 5 = giống người thật hỏi.",
]


def main():
    pilot = [json.loads(x) for x in open(HERE / "pilot_sample.jsonl", encoding="utf-8")]
    new = {}
    for x in open(HERE / "questions.jsonl", encoding="utf-8"):
        r = json.loads(x)
        new[r["lineage_id"]] = r
    old = {}
    for x in open(ROOT / "data/vilextime/questions.jsonl", encoding="utf-8"):
        r = json.loads(x)
        if not r.get("rejected_reason"):
            old.setdefault(r["lineage_id"], r)
    recs = collections.defaultdict(list)
    for g in {p["group"] for p in pilot}:
        for x in open(ROOT / f"data/derived/vilextime/{g}.jsonl", encoding="utf-8"):
            r = json.loads(x)
            recs[r["lineage_id"]].append(r)
    rng = random.Random("20261124:v7:pilot:sheet")
    rows, key = [], []
    for i, p in enumerate(pilot, 1):
        lid = p["lineage_id"]
        texts = []
        for r in sorted(recs[lid], key=lambda r: r["as_of"]):
            t = r["answer"] or "(không còn hiệu lực)"
            if t not in texts:
                texts.append(t)
        loi_van = "\n\n".join(f"[Bản {n}] {t}" for n, t in enumerate(texts, 1))
        lead = recs[lid][0]["target"]["lead_in"] or ""
        pair = [("old", old[lid]["model"], old[lid]["question"]),
                ("new", new[lid]["model"] if lid in new else "", (new.get(lid) or {}).get("question")
                 or f"(bị bộ lọc loại: {(new.get(lid) or {}).get('rejected_reason')})")]
        rng.shuffle(pair)
        for j, (kind, model, q) in enumerate(pair):
            k = f"L{i:02d}{'ab'[j]}"
            rows.append({"khoa": k, "loi_van_dieu_khoan": (f"[Câu dẫn] {lead}\n\n" if lead else "") + loi_van, "cau_hoi": q})
            key.append({"khoa": k, "lineage_id": lid, "group": p["group"], "kind": kind, "model": model})
    with open(HERE / "pilot_cham_key.tsv", "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, list(key[0]), delimiter="\t", lineterminator="\n")
        w.writeheader()
        w.writerows(key)
    w2.FILL = {"hoi_vao_cho_doi", "tra_loi_duy_nhat", "lo_dap_an", "tu_nhien", "ghi_chu"}
    w2.CHOICES = {"hoi_vao_cho_doi": "có,không,không chắc", "tra_loi_duy_nhat": "có,không,không chắc",
                  "lo_dap_an": "có,không", "tu_nhien": "1,2,3,4,5"}
    w2.workbook(HERE / "pilot_cham.xlsx", [(GUIDE, "Chấm", COLS, rows)])


if __name__ == "__main__":
    main()

"""W3 bổ sung (S15): ứng viên do chính kho gợi ý, không qua agent.

Kho có lệnh sửa đổi/bãi bỏ nhắm đúng lineage (hoặc điều khoản cấp trên) nhưng TỪ CHỐI lệnh đó. compare.py chỉ xét văn
bản agent liệt kê, nên lệnh kho tự từ chối mà agent không nêu thì lọt. Một lệnh thành ứng viên khi:
  - hiệu lực không muộn hơn dòng muộn nhất của lineage (S10), và
  - kho không có ranh giới phiên bản nào của lineage hoặc Điều chứa nó đúng ngày đó (S7).
Đọc kho hiện tại (data/derived). Ghi store_rejected.candidates.jsonl; make_sheet.py nối vào phiếu sau các mã cũ.
python3 data/review/qa_v6/w3/store_check.py
"""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
D = ROOT / "data/derived"


def main():
    last = {}
    for line in open(ROOT / "data/vilextime_dib/vilextime.jsonl", encoding="utf-8"):
        r = json.loads(line)
        last[r["lineage_id"]] = max(last.get(r["lineage_id"], ""), r["as_of"])
    batch = {}
    for f in sorted(HERE.glob("*_batch.jsonl")):
        for t in map(json.loads, open(f, encoding="utf-8")):
            batch.setdefault(t["lineage_id"], t)
    rejected = {e["event_id"] for e in map(json.loads, open(D / "event_log.jsonl", encoding="utf-8")) if e["outcome"] == "rejected"}
    hits, seen = [], set()
    for p in map(json.loads, open(D / "provision_events.jsonl", encoding="utf-8")):
        if p["id"] not in rejected or not p.get("effective_on"):
            continue
        tgt = [x for x in [p.get("target_provision_id"), *p.get("affected_provision_ids", [])] if x]
        for lid, day in last.items():
            if p["effective_on"] <= day and (lid, p["actor_number"]) not in seen and \
                    any(lid == x or lid.startswith(x + "#") for x in tgt):
                seen.add((lid, p["actor_number"]))
                hits.append((lid, p))
    bounds = {lid: set() for lid, _ in hits}
    for v in map(json.loads, open(D / "versions.jsonl", encoding="utf-8")):
        for lid in bounds:
            if v["provision_id"] in (lid, lid.split("#")[0]):
                bounds[lid] |= {v["valid_from"], v["valid_to"]} | {x for i in v["effective_intervals"] for x in i.values()}
    out = []
    for lid, p in hits:
        if p["effective_on"] in bounds[lid]:
            continue  # S7: kho đã có thay đổi đúng ngày đó
        t = batch[lid]
        out.append({"key": t["key"], "lineage_id": lid, "document_id": t["document_id"], "law_id": t["law_id"],
                    "citation": t["citation"], "actor_number": p["actor_number"], "relation": p["operation"],
                    "effective_on": p["effective_on"], "touches_target": "store_rejected", "source_kind": "store_event",
                    "source_url": "", "quote": p.get("evidence", "")[:500],
                    "candidate_kind": "store_rejected:" + (p.get("status_reason") or ""), "affects_rows": True})
    with open(HERE / "store_rejected.candidates.jsonl", "w", encoding="utf-8") as f:
        f.writelines(json.dumps(o, ensure_ascii=False) + "\n" for o in out)
    for o in out:
        print(o["key"], o["law_id"], o["citation"], "<-", o["actor_number"], o["effective_on"], o["candidate_kind"])
    print(len(hits), "lệnh bị từ chối chạm dòng;", len(out), "ứng viên sau luật S7")


if __name__ == "__main__":
    main()

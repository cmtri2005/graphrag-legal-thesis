"""ViLexTime 7.0, khung mẫu (đăng ký trước §1, sửa theo S1 ngày 24/11).

Người gán là hai sinh viên luật chưa xem dữ liệu, nên chỉ loại lineage thuộc văn bản của tập dev (cấu hình hệ được
chọn trên dev; tách theo văn bản như final_run.validate_rows). Ghi frame_excluded.txt (mỗi dòng một lineage) và
frame.json (sha256 đầu vào, đếm theo nhóm).
python3 data/vilextime_v7/frame.py
"""
import collections
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
POOL = ROOT / "data/derived/vilextime_pool.jsonl"
DEV = ROOT / "data/vilextime_dataset_h6/vilextime_meta.jsonl"
DEV_ROWS = ROOT / "data/vilextime_dataset_h6/vilextime.jsonl"


def main():
    dev_ids = {json.loads(x)["id"] for x in open(DEV_ROWS, encoding="utf-8") if json.loads(x).get("split") == "dev"}
    dev_docs, dev_lins = set(), set()
    for line in open(DEV, encoding="utf-8"):
        m = json.loads(line)
        if m["id"] in dev_ids:
            dev_docs.add(m["target"]["document_id"])
            dev_lins.add(m["target"]["provision_id"])
    pool = {}
    for line in open(POOL, encoding="utf-8"):
        r = json.loads(line)
        pool[r["provision_id"]] = (r["group"], r["document_id"])
    out = sorted(p for p, (_, d) in pool.items() if d in dev_docs or p in dev_lins)
    (HERE / "frame_excluded.txt").write_text("".join(x + "\n" for x in out), encoding="utf-8")
    left = collections.Counter(g for p, (g, _) in pool.items() if p not in set(out))
    meta = {"pool": str(POOL.relative_to(ROOT)), "pool_sha256": hashlib.sha256(POOL.read_bytes()).hexdigest(),
            "dev": str(DEV_ROWS.relative_to(ROOT)), "dev_sha256": hashlib.sha256(DEV_ROWS.read_bytes()).hexdigest(),
            "dev_lineages": len(dev_lins), "dev_documents": len(dev_docs), "pool_lineages": len(pool),
            "excluded": len(out), "in_frame_by_group": dict(sorted(left.items()))}
    (HERE / "frame.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(meta, ensure_ascii=False))


if __name__ == "__main__":
    main()

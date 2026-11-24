"""ViLexTime 7.0, khung mẫu (đăng ký trước §1): lineage của kho ứng viên đã xuất hiện trong phiếu hay bản phát hành cũ.

Ghi frame_excluded.txt (mỗi dòng một lineage) và frame.json (sha256 đầu vào, đếm theo nhóm).
python3 data/vilextime_v7/frame.py
"""
import collections
import hashlib
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
POOL = ROOT / "data/derived/vilextime_pool.jsonl"
SEEN = ["data/review", "data/vilextime_dataset", "data/vilextime_dataset_h6", "data/vilextime_final",
        "data/vilextime_dib", "data/vilextime/test2_release.jsonl", "data/vilextime/test2_release_v2.jsonl"]
RX = re.compile(r"provision:[0-9a-f-]{36}(?:#[^\"\t\s,\]\\]*)?")


def files():
    for s in SEEN:
        p = ROOT / s
        yield from ([p] if p.is_file() else sorted(x for x in p.rglob("*") if x.is_file()))


def main():
    pool = {}
    for line in open(POOL, encoding="utf-8"):
        r = json.loads(line)
        pool[r["provision_id"]] = r["group"]
    seen = set()
    for f in files():
        if f.suffix in (".xlsx", ".sqlite", ".pyc") or f.stat().st_size > 300e6:
            continue  # xlsx sheets are built from the tsv/jsonl beside them
        seen |= set(RX.findall(f.read_text(encoding="utf-8", errors="ignore")))
    out = sorted(seen & set(pool))
    (HERE / "frame_excluded.txt").write_text("".join(x + "\n" for x in out), encoding="utf-8")
    left = collections.Counter(g for p, g in pool.items() if p not in seen)
    meta = {"pool": str(POOL.relative_to(ROOT)), "pool_sha256": hashlib.sha256(POOL.read_bytes()).hexdigest(),
            "seen_sources": SEEN, "pool_lineages": len(pool), "excluded": len(out),
            "in_frame_by_group": dict(sorted(left.items()))}
    (HERE / "frame.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(meta, ensure_ascii=False))


if __name__ == "__main__":
    main()

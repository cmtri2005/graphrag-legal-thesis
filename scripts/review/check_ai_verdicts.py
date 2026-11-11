"""Kiểm file nhãn AI-chốt (JSONL) theo miền giá trị và cách suy verdict của test2_labels.

    python scripts/review/check_ai_verdicts.py <input.jsonl> <out.jsonl>
"""
import json, sys
sys.path.insert(0, "scripts/review")
from test2_labels import GOOD, REASONS

def problems(r):
    p = []
    for q in ("q1", "q2", "q3", "q4"):
        v, rs = r[q], [x.strip() for x in (r.get(q + "_reason") or "").split(",") if x.strip()]
        if v == GOOD[q]:
            if rs: p.append(f"{q}={v} nhưng có reason")
        elif v not in REASONS[q]: p.append(f"{q}={v} ngoài miền")
        elif not rs or any(x not in REASONS[q][v] for x in rs): p.append(f"{q} reason {rs} sai")
    want = "dat" if all(r[q] == GOOD[q] for q in GOOD) else "khong_dat"
    if r["verdict"] != want: p.append(f"verdict {r['verdict']} != suy ra {want}")
    return p

if __name__ == "__main__":
    inp, out = sys.argv[1:3]
    ids = [json.loads(l)["lineage_id"] for l in open(inp, encoding="utf-8")]
    rows = [json.loads(l) for l in open(out, encoding="utf-8")]
    got = [r["lineage_id"] for r in rows]
    bad = {r["lineage_id"]: problems(r) for r in rows if problems(r)}
    print(json.dumps({"input": len(ids), "output": len(rows), "missing": sorted(set(ids) - set(got)),
                      "extra": sorted(set(got) - set(ids)), "duplicate": len(got) - len(set(got)),
                      "dat": sum(r["verdict"] == "dat" for r in rows), "problems": bad}, ensure_ascii=False, indent=1))
    sys.exit(1 if bad or set(ids) != set(got) or len(got) != len(set(got)) else 0)

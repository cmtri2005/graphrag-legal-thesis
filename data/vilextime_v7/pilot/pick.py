"""Chạy thử prompt mới + Qwen3.8-27B (Chutes) trước khi sinh câu hỏi cho mẫu 7.0.

30 lineage đã bị loại ở 6.0.0 (annotation/excluded_lineages.jsonl), có câu hỏi cũ hợp lệ, không nằm trong mẫu 7.0:
mọi T3 và T6, phần còn lại T2 rút có seed, ưu tiên ca bị loại vì `question_ambiguous`, chia đều câu cũ Opus/DeepSeek.
Ghi pilot_sample.jsonl (định dạng sample_vilextime). Sinh: generate_questions.py --sample ... --out pilot/questions.jsonl
python3 data/vilextime_v7/pilot/pick.py
"""
import collections
import json
import random
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
N = 30


def main():
    pool = {}
    for line in open(ROOT / "data/derived/vilextime_pool.jsonl", encoding="utf-8"):
        r = json.loads(line)
        pool[r["provision_id"]] = (r["group"], r["document_id"])
    sample = {json.loads(x)["lineage_id"] for x in open(ROOT / "data/vilextime_v7/sample.jsonl", encoding="utf-8")}
    model = {}
    for line in open(ROOT / "data/vilextime/questions.jsonl", encoding="utf-8"):
        r = json.loads(line)
        if not r.get("rejected_reason"):
            model.setdefault(r["lineage_id"], r["model"])
    exc = {json.loads(x)["lineage_id"]: json.loads(x)["reason_codes"]
           for x in open(ROOT / "data/vilextime_dib/annotation/excluded_lineages.jsonl", encoding="utf-8")}
    cand = sorted(l for l in exc if l not in sample and l in model)
    picked = [c for c in cand if pool[c][0] in ("T3", "T6")]
    rng = random.Random("20261124:v7:pilot")
    t2 = collections.defaultdict(list)
    for c in cand:
        if pool[c][0] == "T2":
            t2[model[c]].append(c)
    need = N - len(picked)
    for i, m in enumerate(sorted(t2)):
        rng.shuffle(t2[m])
        t2[m].sort(key=lambda c: "question_ambiguous" not in exc[c])   # stable: ambiguous first, seeded order kept
        picked += t2[m][: need // 2 + (need % 2 if i == 0 else 0)]
    rows = [{"group": pool[c][0], "rank": i, "lineage_id": c, "document_id": pool[c][1]} for i, c in enumerate(picked)]
    (HERE / "pilot_sample.jsonl").write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), "utf-8")
    print(len(rows), collections.Counter((r["group"], model[r["lineage_id"]],
                                          "ambiguous" in " ".join(exc[r["lineage_id"]])) for r in rows))


if __name__ == "__main__":
    main()

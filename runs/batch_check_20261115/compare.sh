#!/usr/bin/env bash
# Kiểm Batch API cho cùng chất lượng: b4 dev gửi qua batch, so với lần 1 và lần 2 (gửi từng request) của tập dượt G3.
# Tiêu chí đặt trước khi xem số: batch–r1 khác nhau không nhiều hơn r2–r1 (cả lời văn thô lẫn Accuracy).
set -euo pipefail
cd "$(dirname "$0")/../.."
export PYTHONPATH=src HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
PY=.venv/bin/python; O=runs/batch_check_20261115; G=runs/final_rehearsal_g3_20261112; DR=data/vilextime_dataset_h6/vilextime.jsonl
$PY scripts/eval/colab_b1.py import --prompts $G/r1/prompts/b4.jsonl --raw $O/raw/b4__*.r1.jsonl --out $O/b4_batch.jsonl
cp $G/r1/dev/b4.jsonl $O/b4_r1.jsonl; cp $G/r2/dev/b4.jsonl $O/b4_r2.jsonl
$PY scripts/eval/score_vilextime.py $O/b4_r1.jsonl $O/b4_r2.jsonl $O/b4_batch.jsonl --split dev --release $DR --data data --out $O/score.json > $O/score.txt
$PY - <<'PY'
import glob, json
def raw(pattern):
    return {r["id"]: r["raw"] for r in map(json.loads, open(glob.glob(pattern)[0], encoding="utf-8"))}
G = "runs/final_rehearsal_g3_20261112/raw"
r1, r2, b = raw(f"{G}/b4__*.r1.jsonl"), raw(f"{G}/b4__*.r2.jsonl"), raw("runs/batch_check_20261115/raw/b4__*.r1.jsonl")
same = lambda x, y: sum(x[i] == y[i] for i in x) 
out = {"rows": len(b), "raw_identical_r2_vs_r1": same(r1, r2), "raw_identical_batch_vs_r1": same(r1, b),
       "raw_identical_batch_vs_r2": same(r2, b)}
s = json.load(open("runs/batch_check_20261115/score.json"))
for name in s:
    if "−" not in name:
        out[f"accuracy_{name}"] = s[name]["giua_khoang"]["all"]["accuracy"]
json.dump(out, open("runs/batch_check_20261115/compare.json", "w"), indent=2); print(json.dumps(out, indent=1))
PY

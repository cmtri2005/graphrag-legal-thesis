#!/usr/bin/env bash
# Hậu nghiệm G4 (REFACTOR_PLAN nhóm 2), chạy sau run_b7v.sh.
#  1. attribution.json: quy kết từ dự đoán G4 đã lưu + nấc b7v (không gọi model).
#  2. Hai baseline mới bvnone, bvdate TRÊN DEV (REFACTOR_PLAN 2.6): xuất prompt, gọi API hai lần, chấm.
#     Không chạm test: phần test của 2.6 chờ amendment ADR 0006.
set -euo pipefail
cd "$(dirname "$0")/../.."
export PYTHONPATH=src HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
PY=.venv/bin/python; O=runs/posthoc_g4_20261113; G=runs/final_g4_20261112
R=data/vilextime_final/vilextime.jsonl; D=data/vilextime_final/internal
log() { echo "=== $* $(date -u +%FT%TZ)"; }
while pgrep -f "run_vilextime.py --system b7v" > /dev/null; do sleep 30; done
grep -q "^exit=0" $O/run_b7v.log || { echo "b7v did not finish"; exit 1; }

log attribution
git rev-parse HEAD > $O/head_attribution.txt; git status --porcelain > $O/git_status_attribution.txt
git diff HEAD -- src scripts tests | sha256sum > $O/code_diff.sha256
$PY scripts/eval/posthoc_g4.py --g4 $G --release $R --data $D --extra-retrieval $O/retrieval \
  --out $O/attribution.json > $O/attribution.txt

DR=data/vilextime_dataset_h6/vilextime.jsonl; DV=runs/final_rehearsal_g3_20261112; M=gpt-4o-mini-2024-07-18
mkdir -p $O/dev/prompts $O/dev/raw
for s in bvnone bvdate; do log export dev $s
  $PY scripts/eval/colab_b1.py export --release $DR --system $s --split dev --as-of-strategy giua_khoang --limit 0 \
    --b2 --hybrid --hits-cache $O/dev/retrieval.sqlite --out $O/dev/prompts/$s.jsonl
done
for t in r1 r2; do for s in bvnone bvdate; do log api dev $t $s
  $PY scripts/eval/api_generate.py --prompts $O/dev/prompts/$s.jsonl --provider openai --model $M --out-dir $O/dev/raw \
    --run-tag $t --temperature 0 --max-tokens 1024 --seed 20261109
done; done
for t in r1 r2; do log score dev $t
  for s in bvnone bvdate; do
    $PY scripts/eval/colab_b1.py import --prompts $O/dev/prompts/$s.jsonl --raw $O/dev/raw/${s}__*.$t.jsonl --out $O/dev/$t/$s.jsonl
  done
  $PY scripts/eval/score_vilextime.py $DV/$t/dev/b4.jsonl $O/dev/$t/bvnone.jsonl $O/dev/$t/bvdate.jsonl \
    $DV/$t/dev/b7plus.jsonl $DV/$t/dev/proposed2.jsonl --split dev --release $DR --data data --ci 10000 \
    --out $O/dev/$t/baselines.score.json > $O/dev/$t/baselines.txt
done
log DONE

#!/usr/bin/env bash
# LightRAG trên DEV: gọi API hai lần, nhập, chấm cạnh các hệ của tập dượt G3 (cùng prompt hệ thống, generator, seed).
# TỐN TIỀN (ước lượng 0,7 USD mỗi lần gọi, xem REFACTOR_PLAN 3.3): chỉ chạy khi CMT đồng ý. Không chạm bộ test cuối.
set -euo pipefail
cd "$(dirname "$0")/../.."
export PYTHONPATH=src HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
PY=.venv/bin/python; O=runs/lightrag_20261113/dev; DV=runs/final_rehearsal_g3_20261112
DR=data/vilextime_dataset_h6/vilextime.jsonl; M=gpt-4o-mini-2024-07-18
log() { echo "=== $* $(date -u +%FT%TZ)"; }
mkdir -p $O/raw
git rev-parse HEAD > $O/head.txt; git status --porcelain > $O/git_status_start.txt
for t in r1 r2; do log api dev $t
  $PY scripts/eval/api_generate.py --prompts $O/prompts/lightrag.jsonl --provider openai --model $M --out-dir $O/raw \
    --run-tag $t --temperature 0 --max-tokens 1024 --seed 20261109
done
for t in r1 r2; do log score dev $t; mkdir -p $O/$t
  $PY scripts/eval/colab_b1.py import --prompts $O/prompts/lightrag.jsonl --raw $O/raw/lightrag__*.$t.jsonl --out $O/$t/lightrag.jsonl
  # scorer so mỗi file với file đứng trước: lightrag − b4, proposed2 − lightrag; rồi lightrag − b5, b7plus − lightrag
  $PY scripts/eval/score_vilextime.py $DV/$t/dev/b4.jsonl $O/$t/lightrag.jsonl $DV/$t/dev/proposed2.jsonl \
    --split dev --release $DR --data data --ci 10000 --out $O/$t/lightrag_vs_b4_p.score.json > $O/$t/lightrag_vs_b4_p.txt
  $PY scripts/eval/score_vilextime.py $DV/$t/dev/b5.jsonl $O/$t/lightrag.jsonl $DV/$t/dev/b7plus.jsonl \
    --split dev --release $DR --data data --ci 10000 --out $O/$t/lightrag_vs_b5_b7plus.score.json > $O/$t/lightrag_vs_b5_b7plus.txt
done
log DONE

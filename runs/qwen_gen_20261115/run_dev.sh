#!/usr/bin/env bash
# PLAN_PAPER_GAP B1 (dev): Qwen3.8-27B (vLLM, Colab A100) trên đúng các prompt dev mà GPT-4o mini đã chạy
# (prompt khớp sha256 với rebuild_20261110_dev, repeal_persist_dev_20261112, lightrag_20261113, posthoc_g4_20261113).
# Không gọi model ở đây: chỉ nhập raw và chấm. KHÔNG chạm bộ test cuối.
set -euo pipefail
cd "$(dirname "$0")/../.."
O=runs/qwen_gen_20261115/dev; R=data/vilextime_dataset_h6/vilextime.jsonl
export PYTHONPATH=src HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
git rev-parse HEAD > $O/head.txt; date -u +%FT%TZ > $O/started_utc.txt
for tag in r1 r2; do
  mkdir -p $O/$tag; done=()
  for p in $O/prompts/*.jsonl; do
    s=$(basename $p .jsonl); raw=$(ls $O/raw/${s}__*.$tag.jsonl 2>/dev/null || true)
    [ -n "$raw" ] || { echo "skip $s $tag: no raw"; continue; }
    .venv/bin/python scripts/eval/colab_b1.py import --prompts $p --raw $raw --out $O/$tag/$s.jsonl
    done+=($O/$tag/$s.jsonl)
  done
  .venv/bin/python scripts/eval/score_vilextime.py "${done[@]}" --split dev --release $R --data data \
    --ci 10000 --out $O/$tag/all.score.json
done
echo "exit=0 done $(date -u +%FT%TZ)"

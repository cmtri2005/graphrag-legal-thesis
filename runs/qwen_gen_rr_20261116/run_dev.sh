#!/usr/bin/env bash
# B2 bước 4 (DEV): Qwen3.8-27B sinh câu trả lời cho 4 ô reranker (AITeamVN/Vietnamese_Reranker). Chỉ nhập raw và chấm. KHÔNG chạm test.
# Điền raw từ Colab vào dev/raw/ (gói colab_upload/qwen_gen_rr/) rồi chạy. Chấm kèm 3 hệ không reranker để so cùng bảng.
set -euo pipefail
cd "$(dirname "$0")/../.."
O=runs/qwen_gen_rr_20261116/dev; B=runs/qwen_gen_20261115/dev; R=data/vilextime_dataset_h6/vilextime.jsonl
export PYTHONPATH=src HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
git rev-parse HEAD > $O/head.txt; date -u +%FT%TZ > $O/started_utc.txt
for tag in r1 r2; do
  mkdir -p $O/$tag; done=()
  for s in b4-rr b7-rr b7plus-rr bvnone-rr; do
    raw=$(ls $O/raw/${s}__*.$tag.jsonl)
    .venv/bin/python scripts/eval/colab_b1.py import --prompts $O/prompts/$s.jsonl --raw $raw --out $O/$tag/$s.jsonl
    done+=($O/$tag/$s.jsonl)
  done
  for s in b4 b7 b7plus bvnone proposed2; do done+=($B/$tag/$s.jsonl); done
  .venv/bin/python scripts/eval/score_vilextime.py "${done[@]}" --split dev --release $R --data data \
    --ci 10000 --out $O/$tag/all.score.json
done
echo "exit=0 done $(date -u +%FT%TZ)"

#!/usr/bin/env bash
# PLAN_PAPER_GAP A2: F1–F7 trên phần bộ cuối có gold mù người = 24 lineage đợt 1 + 79 lineage NMT (gold_final),
# bỏ 2 lineage mà gold người nói kho sai (kg_missed_amendment). Chỉ chấm lại dự đoán G4, không gọi model.
# Mô tả, không thay phán quyết bộ cuối (cùng cách với posthoc_g4_20261113/gold_subset).
set -euo pipefail
cd "$(dirname "$0")/../.."
export PYTHONPATH=src
O=runs/gold_final_subset_20261115; G=runs/final_g4_20261112; D=data/vilextime_final/internal
git rev-parse HEAD > $O/head.txt
sha256sum data/review/gold_sample.tsv data/review/gold_final/gold_sample.tsv data/review/gold_final/gold_A.reveal.tsv \
  $O/lineages.txt $O/vilextime.jsonl $O/vilextime_meta.jsonl > $O/inputs.sha256
for t in r1 r2; do
  .venv/bin/python scripts/eval/confirm_vilextime.py --family final --retrieval $G/retrieval --generation $G/$t/test \
    --split test --release $O/vilextime.jsonl --data $D --draws 10000 --out $O/confirm_$t.json > $O/confirm_$t.txt
done
echo "exit=0 done $(date -u +%FT%TZ)"

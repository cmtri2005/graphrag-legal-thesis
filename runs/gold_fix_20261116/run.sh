#!/usr/bin/env bash
# ADR 0006 §7: chấm lại F1–F7 trên bộ cuối với gold đã sửa (F019 luật sư; F016, F060 NMT). Chỉ chấm lại dự đoán đã lưu, không gọi model.
set -euo pipefail
cd "$(dirname "$0")/../.."
export PYTHONPATH=src
O=runs/gold_fix_20261116; G=runs/final_g4_20261112; Q=runs/qwen_chutes_20261116/test; D=data/vilextime_final/internal
git rev-parse HEAD > $O/head.txt
.venv/bin/python $O/make_release.py $O
sha256sum data/vilextime_final/vilextime.jsonl data/vilextime_final/vilextime_meta.jsonl $O/vilextime.jsonl $O/vilextime_meta.jsonl > $O/inputs.sha256
for t in r1 r2; do
  .venv/bin/python scripts/eval/confirm_vilextime.py --family final --retrieval $G/retrieval --generation $G/$t/test \
    --split test --release $O/vilextime.jsonl --data $D --draws 10000 --out $O/gpt_confirm_$t.json > $O/gpt_confirm_$t.txt
  .venv/bin/python scripts/eval/confirm_vilextime.py --family final --retrieval $G/retrieval --generation $Q/$t \
    --split test --release $O/vilextime.jsonl --data $D --draws 10000 --out $O/qwen_confirm_$t.json > $O/qwen_confirm_$t.txt
done
echo "exit=0 done $(date -u +%FT%TZ)"
# Phần có gold mù người: 103 lineage của gold_final_subset + 2 lineage kho sai nay đã sửa gold = 105 lineage
mkdir -p $O/subset; cat runs/gold_final_subset_20261115/lineages.txt runs/gold_final_subset_20261115/excluded_kg_wrong.txt > $O/subset/lineages.txt
.venv/bin/python $O/make_release.py $O/subset data/vilextime_final $O/subset/lineages.txt
for t in r1 r2; do
  .venv/bin/python scripts/eval/confirm_vilextime.py --family final --retrieval $G/retrieval --generation $G/$t/test \
    --split test --release $O/subset/vilextime.jsonl --data $D --draws 10000 --out $O/subset/confirm_$t.json > $O/subset/confirm_$t.txt
done

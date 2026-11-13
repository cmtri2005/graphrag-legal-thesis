#!/usr/bin/env bash
# ADR 0006 §7 "báo song song F1–F6 trên phần gold mù": 24 lineage bộ cuối có trong gold mù người đợt 1
# (data/review/gold_sample.tsv; 119/120 khớp, CMT xác nhận 10/11). Chỉ chấm lại dự đoán G4, không gọi model.
# Họ F7 không có dòng (0 T6 trong phần này). Mẫu nhỏ: chỉ mô tả, không thay phán quyết bộ cuối.
set -euo pipefail
cd "$(dirname "$0")/../../.."
export PYTHONPATH=src
O=runs/posthoc_g4_20261113/gold_subset; G=runs/final_g4_20261112; D=data/vilextime_final/internal
sha256sum data/review/gold_sample.tsv data/review/gold_A.reveal.tsv data/review/gold_B.reveal.tsv $O/vilextime.jsonl $O/vilextime_meta.jsonl > $O/inputs.sha256
for t in r1 r2; do
  .venv/bin/python scripts/eval/confirm_vilextime.py --family final --retrieval $G/retrieval --generation $G/$t/test \
    --split test --release $O/vilextime.jsonl --data $D --draws 10000 --out $O/confirm_$t.json > $O/confirm_$t.txt
done

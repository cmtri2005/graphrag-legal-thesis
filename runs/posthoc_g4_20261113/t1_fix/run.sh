#!/usr/bin/env bash
# ADR 0006 Amendment 2026-11-19: rescore saved G4 predictions (r1, r2) against the T1-fixed release. No model calls.
set -euo pipefail
cd "$(dirname "$0")/../../.."
export PYTHONPATH=src HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
PY=.venv/bin/python; G=runs/final_g4_20261112; O=runs/posthoc_g4_20261113/t1_fix; D=data/vilextime_final/internal
$PY scripts/eval/fix_t1_short_answers.py --release data/vilextime_final/vilextime.jsonl --out $O/release
for t in r1 r2; do
  mkdir -p $O/$t
  P=$(ls $G/$t/test/*.jsonl | grep -v sample)
  $PY scripts/eval/score_vilextime.py $P --split test --release $O/release/vilextime.jsonl --data $D \
    --ci 10000 --out $O/$t/all.score.json > $O/$t/score.txt
  $PY scripts/eval/confirm_vilextime.py --family final --proposed proposed2 --retrieval $G/retrieval \
    --generation $G/$t/test --split test --release $O/release/vilextime.jsonl --data $D \
    --draws 10000 --out $O/$t/confirm.json > $O/$t/confirm.txt
done

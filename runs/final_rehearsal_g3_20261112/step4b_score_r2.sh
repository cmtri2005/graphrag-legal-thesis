#!/usr/bin/env bash
# resume step4 from r2 (r1 import/score/confirm/report finished 13:29 UTC; previous session ended during r2)
set -eu; source "$(dirname "$0")/common.sh"
$FR --step check --run-tag r2 --source-prompts $O/r1/prompts --out $O/r2
for st in export import score confirm report; do $FR --step $st --run-tag r2 --source-prompts $O/r1/prompts --out $O/r2; done
$PY scripts/eval/compare_runs.py --confirm1 $O/r1/confirm.json --confirm2 $O/r2/confirm.json \
  --gen1 $O/r1/dev --gen2 $O/r2/dev --release $R --split dev --out $O/compare_runs.json
echo "DONE $(date -u +%T)"

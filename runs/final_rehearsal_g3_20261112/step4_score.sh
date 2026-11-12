#!/usr/bin/env bash
# import, score, confirm, report for r1 and r2, then compare (dev rehearsal of the G4 steps 4-5)
set -eu; source "$(dirname "$0")/common.sh"
$FR --step check --run-tag r1 --out $O/r1
for st in import score confirm report; do $FR --step $st --run-tag r1 --out $O/r1; done
$FR --step check --run-tag r2 --source-prompts $O/r1/prompts --out $O/r2
for st in export import score confirm report; do $FR --step $st --run-tag r2 --source-prompts $O/r1/prompts --out $O/r2; done
$PY scripts/eval/compare_runs.py --confirm1 $O/r1/confirm.json --confirm2 $O/r2/confirm.json \
  --gen1 $O/r1/dev --gen2 $O/r2/dev --release $R --split dev --out $O/compare_runs.json

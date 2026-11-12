#!/usr/bin/env bash
# G4: final run on the locked test set, exactly the commands of data/vilextime_final/README.md "Chạy G4".
# Commits after each step whose output a later step reads (guard_test needs clean inputs). Run once.
set -euo pipefail
cd "$(dirname "$0")/../.."
export PYTHONPATH=src HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
PY=.venv/bin/python; R=data/vilextime_final/vilextime.jsonl; D=data/vilextime_final/internal; O=runs/final_g4_20261112
M=gpt-4o-mini-2024-07-18
FR="$PY scripts/eval/final_run.py --split test --release $R --data $D --raw $O/raw --retrieval $O/retrieval"
mkdir -p $O/raw $O/retrieval
commit() { git add -- "$@"; git commit -q -m "G4 test: $MSG" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>" -- "$@" || true; }
log() { echo "=== $* $(date -u +%T)"; }

if [ ! -f $O/retrieval/b7pp.run.json ]; then
  for s in b2ctx b7 b7plus b7pp; do log retrieval $s
    $PY scripts/eval/run_vilextime.py --system $s --no-dense --retrieval-only --split test --as-of-strategy giua_khoang \
      --release $R --hits-cache $O/retrieval.sqlite --out $O/retrieval/$s.jsonl
  done
  MSG="bước 1 truy xuất từ vựng F4-F6 (k=20)"; commit $O/retrieval $O/run_g4.sh $O/head.txt $O/git_status_start.txt $O/started_utc.txt
fi

if [ ! -f $O/r1/prompts/proposed2.jsonl ]; then
  log check; $FR --step check --out $O/r1
  log export; $FR --step export --out $O/r1
  MSG="bước 2 kiểm và xuất prompt"; commit $O/r1
fi

for t in r1 r2; do
  for p in $O/r1/prompts/*.jsonl; do log api $t $(basename $p .jsonl)
    $PY scripts/eval/api_generate.py --prompts $p --provider openai --model $M --out-dir $O/raw --run-tag $t \
      --temperature 0 --max-tokens 1024 --seed 20261109
  done
  MSG="bước 3 gọi API lần $t"; commit $O/raw
done

log score r1
$FR --step check --run-tag r1 --out $O/r1
for st in import score confirm report; do $FR --step $st --run-tag r1 --out $O/r1; done
log score r2
$FR --step check --run-tag r2 --source-prompts $O/r1/prompts --out $O/r2
for st in export import score confirm report; do $FR --step $st --run-tag r2 --source-prompts $O/r1/prompts --out $O/r2; done
log compare
$PY scripts/eval/compare_runs.py --confirm1 $O/r1/confirm.json --confirm2 $O/r2/confirm.json \
  --gen1 $O/r1/test --gen2 $O/r2/test --release $R --split test --out $O/compare_runs.json
log DONE

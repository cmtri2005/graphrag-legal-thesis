#!/usr/bin/env bash
# r1: seed raw from byte-identical old prompts, request only the rest. r2: request every row (no seed).
set -u; source "$(dirname "$0")/common.sh"
[ -f $O/raw/seed.json ] || $PY $O/seed_raw.py $O/r1/prompts $O/raw runs/rebuild_20261110_dev/raw runs/repeal_persist_dev_20261112/raw
for t in r1 r2; do
  for p in $O/r1/prompts/*.jsonl; do
    echo "=== $t $(basename $p .jsonl) $(date -u +%T)"
    $PY scripts/eval/api_generate.py --prompts $p --provider openai --model $M --out-dir $O/raw --run-tag $t \
      --temperature 0 --max-tokens 1024 --seed 20261109 || echo "FAILED $t $p"
  done
done
echo "DONE $(date -u +%T)"

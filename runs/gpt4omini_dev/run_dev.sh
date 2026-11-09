#!/usr/bin/env bash
# Dev run of the ADR 0006 system list with GPT-4o mini. Rerunnable: finished steps are skipped.
set -u
O=runs/gpt4omini_dev; R=data/vilextime_dataset/vilextime.jsonl; M=gpt-4o-mini-2024-07-18; PY=.venv/bin/python
SYSTEMS=$(PYTHONPATH=src $PY -c "from vilexgraph.framework import systems as s; print(*s.FINAL_GENERATION, *s.DEV_ONLY)")
failed=""
for s in $SYSTEMS; do
  echo "=== $s $(date +%T)"
  [ -f "$O/prompts/$s.jsonl" ] || $PY scripts/eval/colab_b1.py export --release "$R" --system "$s" --split dev \
      --as-of-strategy giua_khoang --limit 0 --b2 --hybrid --out "$O/prompts/$s.jsonl" \
      || { failed="$failed $s:export"; rm -f "$O/prompts/$s.jsonl"; continue; }
  sha=$(sha256sum "$O/prompts/$s.jsonl" | cut -c1-12)
  $PY scripts/eval/api_generate.py --prompts "$O/prompts/$s.jsonl" --provider openai --model "$M" --out-dir "$O/raw" \
      || { failed="$failed $s:api"; continue; }
  $PY scripts/eval/colab_b1.py import --prompts "$O/prompts/$s.jsonl" --raw "$O/raw/${s}__${M}__${sha}.jsonl" \
      --out "$O/dev/$s.jsonl" || failed="$failed $s:import"
done
$PY scripts/eval/score_vilextime.py $(ls "$O"/dev/*.jsonl | grep -v "\.sample\.jsonl$") --split dev --release "$R" --ci 2000 --out "$O/all.score.json" | tail -40
echo "DONE $(date +%T) failed:[$failed]"

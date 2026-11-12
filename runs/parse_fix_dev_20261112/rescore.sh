#!/usr/bin/env bash
# Re-import the 15 dev systems of runs/rebuild_20261110_dev from their saved raw completions with the fixed parser
# (generate.py, one-line labels). No API call. Then score with the same command as run_dev.sh.
set -eu
cd "$(dirname "$0")/../.."
S=runs/rebuild_20261110_dev; O=runs/parse_fix_dev_20261112; R=data/vilextime_dataset_h6/vilextime.jsonl; PY=.venv/bin/python
export PYTHONPATH=src
mkdir -p $O/dev
for p in $S/prompts/*.jsonl; do
  s=$(basename $p .jsonl); sha=$(sha256sum $p | cut -c1-12)
  $PY scripts/eval/colab_b1.py import --prompts $p --raw $S/raw/${s}__gpt-4o-mini-2024-07-18__${sha}.jsonl --out $O/dev/$s.jsonl
done
$PY scripts/eval/score_vilextime.py $(ls $O/dev/*.jsonl | grep -v "\.sample\.jsonl$") --split dev --release $R --ci 2000 --out $O/all.score.json | tail -40

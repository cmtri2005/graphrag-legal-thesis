#!/usr/bin/env bash
# F4-F6 retrieval-only, lexical (--no-dense), k from the system spec (20). Dev rehearsal; same flags as for test.
set -eu
cd "$(dirname "$0")/../.."
O=runs/final_rehearsal_g3_20261112; R=data/vilextime_dataset_h6/vilextime.jsonl
export PYTHONPATH=src HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
for s in b2ctx b7 b7plus b7pp; do
  echo "=== $s $(date -u +%T)"
  .venv/bin/python scripts/eval/run_vilextime.py --system $s --no-dense --retrieval-only --split dev --as-of-strategy giua_khoang \
    --release $R --hits-cache $O/retrieval.sqlite --out $O/retrieval/$s.jsonl
done
echo "DONE $(date -u +%T)"

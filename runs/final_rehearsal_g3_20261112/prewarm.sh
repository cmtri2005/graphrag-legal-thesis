#!/usr/bin/env bash
# Speed only: fills r1/retrieval.sqlite for later systems in a second process (same flags as final_run export); scratch prompts are discarded.
set -u; source "$(dirname "$0")/common.sh"
for s in proposed2 b7pp b7plus; do
  $PY scripts/eval/colab_b1.py export --release $R --system $s --split dev --as-of-strategy giua_khoang --limit 0 --b2 --hybrid \
    --hits-cache $O/r1/retrieval.sqlite --out $O/prewarm/$s.jsonl || echo "FAILED $s"
done

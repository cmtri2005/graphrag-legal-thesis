#!/usr/bin/env bash
# ADR 0006 amendment 2026-11-15 (CMT): LightRAG trên bộ test cuối. THĂM DÒ, sau khi đã thấy test.
# Cùng đường với run_test_baselines.sh: dựng prompt → commit → API hai lần (gửi thường) → nhập → chấm cạnh hệ G4.
set -euo pipefail
cd "$(dirname "$0")/../.."
export PYTHONPATH=src HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
PY=.venv/bin/python; O=runs/lightrag_20261113/test; G=runs/final_g4_20261112
R=data/vilextime_final/vilextime.jsonl; D=data/vilextime_final/internal; M=gpt-4o-mini-2024-07-18
commit() { git add -- "$@"; git commit -q -m "LightRAG test: $MSG" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>" -- "$@" || true; }
log() { echo "=== $* $(date -u +%FT%TZ)"; }
mkdir -p $O/prompts $O/raw
git rev-parse HEAD > $O/head.txt; git status --porcelain > $O/git_status_start.txt
if [ ! -f $O/prompts/lightrag.jsonl ]; then log prompts test
  $PY scripts/eval/lightrag_package.py prompts --contexts runs/lightrag_20261113/colab/contexts.jsonl --split test --out $O/prompts/lightrag.jsonl
  MSG="dựng prompt"; commit $O/prompts $O/head.txt $O/git_status_start.txt runs/lightrag_20261113/run_test.sh
fi
for t in r1 r2; do log api test $t
  $PY scripts/eval/api_generate.py --prompts $O/prompts/lightrag.jsonl --provider openai --model $M --out-dir $O/raw \
    --run-tag $t --temperature 0 --max-tokens 1024 --seed 20261109
  MSG="gọi API lần $t"; commit $O/raw
done
for t in r1 r2; do log score test $t; mkdir -p $O/$t
  $PY scripts/eval/colab_b1.py import --prompts $O/prompts/lightrag.jsonl --raw $O/raw/lightrag__*.$t.jsonl --out $O/$t/lightrag.jsonl
  $PY scripts/eval/score_vilextime.py $G/$t/test/b4.jsonl $O/$t/lightrag.jsonl $G/$t/test/proposed2.jsonl \
    --split test --release $R --data $D --ci 10000 --out $O/$t/lightrag_vs_b4_p.score.json > $O/$t/lightrag_vs_b4_p.txt
  $PY scripts/eval/score_vilextime.py $G/$t/test/b5.jsonl $O/$t/lightrag.jsonl $G/$t/test/b7plus.jsonl \
    --split test --release $R --data $D --ci 10000 --out $O/$t/lightrag_vs_b5_b7plus.score.json > $O/$t/lightrag_vs_b5_b7plus.txt
done
MSG="chấm"; commit $O
log DONE

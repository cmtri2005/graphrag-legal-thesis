#!/usr/bin/env bash
# ADR 0006 amendment 2026-11-13 (CMT duyệt): bvnone, bvdate trên bộ test cuối. THĂM DÒ, sau khi đã thấy test.
# Cùng đường với dev (run_after_b7v.sh) và G4 (run_g4.sh): export (cổng ADR Accepted) → API hai lần → import → chấm.
# Commit sau mỗi bước sinh file mà bước sau đọc, như run_g4.sh.
set -euo pipefail
cd "$(dirname "$0")/../.."
export PYTHONPATH=src HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
PY=.venv/bin/python; O=runs/posthoc_g4_20261113; G=runs/final_g4_20261112; T=$O/test
R=data/vilextime_final/vilextime.jsonl; D=data/vilextime_final/internal; M=gpt-4o-mini-2024-07-18
commit() { git add -- "$@"; git commit -q -m "Hậu nghiệm G4 test: $MSG" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>" -- "$@" || true; }
log() { echo "=== $* $(date -u +%FT%TZ)"; }
mkdir -p $T/prompts $T/raw
git rev-parse HEAD > $T/head.txt; git status --porcelain > $T/git_status_start.txt
if [ ! -f $T/prompts/bvdate.jsonl ]; then
  for s in bvnone bvdate; do log export test $s
    $PY scripts/eval/colab_b1.py export --release $R --index $D/derived/corpus/index.sqlite --system $s --split test \
      --as-of-strategy giua_khoang --limit 0 --b2 --hybrid --hits-cache $O/test_retrieval.sqlite --out $T/prompts/$s.jsonl
  done
  MSG="xuất prompt bvnone, bvdate"; commit $T/prompts $T/head.txt $T/git_status_start.txt $O/run_test_baselines.sh
fi
for t in r1 r2; do for s in bvnone bvdate; do log api test $t $s
  $PY scripts/eval/api_generate.py --prompts $T/prompts/$s.jsonl --provider openai --model $M --out-dir $T/raw \
    --run-tag $t --temperature 0 --max-tokens 1024 --seed 20261109
done; MSG="gọi API lần $t"; commit $T/raw; done
for t in r1 r2; do log score test $t
  mkdir -p $T/$t
  for s in bvnone bvdate; do
    $PY scripts/eval/colab_b1.py import --prompts $T/prompts/$s.jsonl --raw $T/raw/${s}__*.$t.jsonl --index $D/derived/corpus/index.sqlite --out $T/$t/$s.jsonl
  done
  $PY scripts/eval/score_vilextime.py $G/$t/test/b4.jsonl $T/$t/bvnone.jsonl $T/$t/bvdate.jsonl $G/$t/test/b7plus.jsonl \
    $G/$t/test/proposed2.jsonl --split test --release $R --data $D --ci 10000 --out $T/$t/baselines.score.json > $T/$t/baselines.txt
  $PY scripts/eval/score_vilextime.py $T/$t/bvdate.jsonl $G/$t/test/proposed2.jsonl --split test --release $R --data $D \
    --ci 10000 --out $T/$t/proposed2_vs_bvdate.score.json > $T/$t/proposed2_vs_bvdate.txt
done
log DONE

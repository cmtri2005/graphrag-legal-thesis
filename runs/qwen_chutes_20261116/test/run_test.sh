#!/usr/bin/env bash
# ADR 0006 amendment 2026-11-16 (b): Qwen3.8-27B (Chutes, TEE, fp8) trên bộ test cuối, 15 hệ × 2 lần. THĂM DÒ, hậu nghiệm.
# Dùng nguyên prompt đã khóa của G4, bvnone/bvdate và lightrag (kiểm hash khi gọi). Bị ngắt thì chạy lại: dòng đã xong được bỏ qua.
set -euo pipefail
cd "$(dirname "$0")/../../.."
export PYTHONPATH=src HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
PY=.venv/bin/python; O=runs/qwen_chutes_20261116/test; M=Qwen/Qwen3.8-27B-TEE
R=data/vilextime_final/vilextime.jsonl; D=data/vilextime_final/internal
P=(runs/final_g4_20261112/r1/prompts/*.jsonl runs/posthoc_g4_20261113/test/prompts/{bvnone,bvdate}.jsonl runs/lightrag_20261113/test/prompts/lightrag.jsonl)
mkdir -p $O/raw; git rev-parse HEAD > $O/head.txt; date -u +%FT%TZ > $O/started_utc.txt
for t in r1 r2; do for p in "${P[@]}"; do echo "=== api $t $(basename $p .jsonl) $(date -u +%T)"
  $PY scripts/eval/api_generate.py --prompts $p --provider chutes --model $M --out-dir $O/raw --run-tag $t \
    --temperature 0 --max-tokens 1024 --seed 20261109 --workers 4
done; done
for t in r1 r2; do mkdir -p $O/$t; done_=()
  for p in "${P[@]}"; do s=$(basename $p .jsonl)
    $PY scripts/eval/colab_b1.py import --prompts $p --raw $O/raw/${s}__*.$t.jsonl --out $O/$t/$s.jsonl; done_+=($O/$t/$s.jsonl); done
  $PY scripts/eval/score_vilextime.py "${done_[@]}" --split test --release $R --data $D --ci 10000 --out $O/$t/all.score.json > $O/$t/all.score.txt
done
echo "exit=0 done $(date -u +%FT%TZ)"

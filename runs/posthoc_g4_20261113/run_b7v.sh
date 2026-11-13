#!/usr/bin/env bash
# Hậu nghiệm G4 (REFACTOR_PLAN 2.2): nấc b7v của thang ADR 0006 §2, chưa chạy ở G4.
# Đúng lệnh bước 1 của runs/final_g4_20261112/run_g4.sh, chỉ đổi hệ. Chỉ truy xuất từ vựng, không gọi model.
# CHẠY SAU KHI ĐÃ THẤY KẾT QUẢ TEST: báo là việc đã khai nhưng chạy muộn.
set -euo pipefail
cd "$(dirname "$0")/../.."
export PYTHONPATH=src HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
PY=.venv/bin/python; R=data/vilextime_final/vilextime.jsonl; O=runs/posthoc_g4_20261113
git rev-parse HEAD > $O/head.txt; git status --porcelain > $O/git_status_start.txt; date -u +%FT%TZ > $O/started_utc.txt
sha256sum $R data/vilextime_final/vilextime_meta.jsonl > $O/inputs.sha256
$PY scripts/eval/run_vilextime.py --system b7v --no-dense --retrieval-only --split test --as-of-strategy giua_khoang \
  --release $R --hits-cache $O/retrieval.sqlite --out $O/retrieval/b7v.jsonl
echo "exit=$? done $(date -u +%FT%TZ)"

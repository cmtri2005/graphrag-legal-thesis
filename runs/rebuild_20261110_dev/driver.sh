#!/usr/bin/env bash
# Waits for embed steps 17/18 of runs/rebuild_20261110, then runs the dev generation (run_dev.sh) and select_p.
set -u
cd "$(dirname "$0")/../.."
until ! pgrep -f embed_corpus.py >/dev/null; do sleep 30; done
echo "EMBED_FINISHED $(date -u +%FT%TZ)"
export PYTHONPATH=src HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
set -a; . ./.env; set +a
bash runs/rebuild_20261110_dev/run_dev.sh > runs/rebuild_20261110_dev/run_dev.log 2>&1
echo "RUN_DEV_EXIT=$? $(date -u +%FT%TZ)"
.venv/bin/python runs/rebuild_20261110_dev/select_p.py > runs/rebuild_20261110_dev/select_p.out 2>&1
echo "SELECT_P_EXIT=$? $(date -u +%FT%TZ)"

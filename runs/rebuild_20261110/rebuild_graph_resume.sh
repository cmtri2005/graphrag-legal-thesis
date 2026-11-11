#!/usr/bin/env bash
# Rerun of steps 05-06 after attempt 1 failed in 06 (apply_document_scope.py set effective_to <= effective_from on
# 13 documents; see logs/06_build_versions.failed1.log). The 276 values set by attempt 1 were reset to NULL first.
set -euo pipefail
cd "$(dirname "$0")/../.."
export PYTHONPATH=src
PY=.venv/bin/python
L=runs/rebuild_20261110/logs
step() { name=$1; shift; echo "=== $name $(date -u +%FT%TZ)"; "$@" > "$L/$name.log" 2>&1; echo "    exit=$? $(date -u +%FT%TZ)"; }
step 05_apply_document_scope $PY scripts/pipeline/apply_document_scope.py
step 06_build_versions       $PY scripts/pipeline/build_versions.py
echo "GRAPH_DONE $(date -u +%FT%TZ)"

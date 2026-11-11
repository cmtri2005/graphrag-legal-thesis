#!/usr/bin/env bash
# H6 step 2a: raw -> provisions -> temporal.sqlite -> events -> versions. Offline; no network.
# Order from docs/crawling-plan.md "Running the pipeline" (Stage 5b, Stage 6) plus apply_document_scope.py (H5 L2).
set -euo pipefail
cd "$(dirname "$0")/../.."
export PYTHONPATH=src
PY=.venv/bin/python
L=runs/rebuild_20261110/logs; mkdir -p "$L"
step() { name=$1; shift; echo "=== $name $(date -u +%FT%TZ)"; "$@" > "$L/$name.log" 2>&1; echo "    exit=$? $(date -u +%FT%TZ)"; }
step 01_attach_provision_text   $PY scripts/pipeline/attach_provision_text.py --force
step 02_build_store             $PY scripts/pipeline/build_store.py --with-subtrees
step 03_resolve_expiry_targets  $PY scripts/pipeline/resolve_expiry_targets.py
step 04_extract_provision_events $PY scripts/pipeline/extract_provision_events.py
step 05_apply_document_scope    $PY scripts/pipeline/apply_document_scope.py
step 06_build_versions          $PY scripts/pipeline/build_versions.py
echo "GRAPH_DONE $(date -u +%FT%TZ)"

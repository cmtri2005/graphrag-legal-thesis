#!/usr/bin/env bash
# Rerun of steps 16-18 after attempt 2 failed in 16 (final_labels raised KeyError on a label whose row the rebuilt
# release no longer ships; see logs/16_export_release.failed1.log). export_release.final_labels now ignores such labels.
set -euo pipefail
cd "$(dirname "$0")/../.."
export PYTHONPATH=src HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 OMP_NUM_THREADS=4 MKL_NUM_THREADS=4 CUDA_VISIBLE_DEVICES=
PY=.venv/bin/python
L=runs/rebuild_20261110/logs
step() { name=$1; shift; echo "=== $name $(date -u +%FT%TZ)"; "$@" > "$L/$name.log" 2>&1; echo "    exit=$? $(date -u +%FT%TZ)"; }
M=dangvantuan/vietnamese-embedding
step 16_export_release    $PY scripts/pipeline/export_release.py --final --out data/vilextime_dataset_h6
echo "RELEASE_DONE $(date -u +%FT%TZ)"
step 17_embed_asis        $PY scripts/eval/embed_corpus.py --layer asis --max-seq-length 256 --model $M --rescan
step 18_embed_version     $PY scripts/eval/embed_corpus.py --layer version --max-seq-length 256 --model $M --rescan
echo "EMBED_DONE $(date -u +%FT%TZ)"

#!/usr/bin/env bash
# H6 step 2b: versions.jsonl -> corpus -> retrieval index -> embeddings (only new texts) -> question pool -> release.
# Offline; no network. Run after rebuild_graph.sh. The rebuilt release goes to data/vilextime_dataset_h6/ so the
# sealed data/vilextime_dataset/ (v1.0, sha256 7cf51ee6...) is not overwritten.
set -euo pipefail
cd "$(dirname "$0")/../.."
export PYTHONPATH=src HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 OMP_NUM_THREADS=4 MKL_NUM_THREADS=4 CUDA_VISIBLE_DEVICES=
PY=.venv/bin/python
L=runs/rebuild_20261110/logs; mkdir -p "$L"
step() { name=$1; shift; echo "=== $name $(date -u +%FT%TZ)"; "$@" > "$L/$name.log" 2>&1; echo "    exit=$? $(date -u +%FT%TZ)"; }
M=dangvantuan/vietnamese-embedding
# step 07_build_corpus done in attempt 1 (exit=0 17:39:01Z); rerun from 08

rm -f data/derived/corpus/index.sqlite data/derived/corpus/index.sqlite-shm data/derived/corpus/index.sqlite-wal   # index_corpus resumes by stage: a stale file is kept as is (attempt 1 reused it)
step 08_index_corpus      $PY scripts/eval/index_corpus.py
step 09_index_lexical     $PY scripts/eval/index_corpus.py --lexical
step 10_build_pool        $PY scripts/pipeline/build_question_pool.py
step 11_build_vilextime   $PY scripts/pipeline/build_vilextime.py
step 12_select            $PY scripts/pipeline/sample_vilextime.py --select
step 13_enrich            $PY scripts/pipeline/enrich_vilextime.py
step 14_pending_events    $PY scripts/review/pending_events.py
step 15_check_release     $PY scripts/check/check_release.py
step 16_export_release    $PY scripts/pipeline/export_release.py --final --out data/vilextime_dataset_h6
echo "RELEASE_DONE $(date -u +%FT%TZ)"
# embeddings: new texts only (hours on 4 CPU cores); dense systems need them, lexical ones do not
step 17_embed_asis        $PY scripts/eval/embed_corpus.py --layer asis --max-seq-length 256 --model $M --rescan
step 18_embed_version     $PY scripts/eval/embed_corpus.py --layer version --max-seq-length 256 --model $M --rescan
echo "EMBED_DONE $(date -u +%FT%TZ)"

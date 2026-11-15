#!/usr/bin/env bash
# LightRAG (REFACTOR_PLAN 3.3): nhập kết quả Colab, kiểm toàn vẹn, dựng prompt DEV, đo độ phủ căn cứ trên DEV.
# Không gọi model. Không chạm bộ test cuối: prompt và điểm test chờ amendment ADR 0006 (CMT duyệt).
#   bash runs/lightrag_20261113/run_intake.sh <thư mục lightrag_work tải từ Drive>
set -euo pipefail
SRC=$(realpath "$1"); cd "$(dirname "$0")/../.."
export PYTHONPATH=src
PY=.venv/bin/python; O=runs/lightrag_20261113; DV=runs/final_rehearsal_g3_20261112/r1/prompts; PH=runs/posthoc_g4_20261113/dev/prompts
log() { echo "=== $* $(date -u +%FT%TZ)"; }
mkdir -p $O/colab $O/dev/prompts
date -u +%FT%TZ > $O/started_utc.txt; git rev-parse HEAD > $O/head.txt; git status --porcelain > $O/git_status_start.txt
git diff HEAD -- src scripts tests | sha256sum > $O/code_diff.sha256

log copy; cp "$SRC/contexts.jsonl" "$SRC/build_done.json" $O/colab/
log intake
$PY -I - "$SRC" $O <<'PY'
import collections, hashlib, json, re, sys
from pathlib import Path
src, out = Path(sys.argv[1]), Path(sys.argv[2])
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
load = lambda p: [json.loads(line) for line in Path(p).open(encoding="utf-8")]
queries, contexts, corpus = load("colab_upload/lightrag/queries.jsonl"), load(out / "colab/contexts.jsonl"), load("colab_upload/lightrag/corpus.jsonl")
assert sha(src / "contexts.jsonl") == sha(out / "colab/contexts.jsonl")
ids = [c["id"] for c in contexts]
status = json.loads((src / "kv_store_doc_status.json").read_text(encoding="utf-8"))
corpus_ids = {d["id"] for d in corpus}
dup = {v["file_path"]: v["metadata"]["original_doc_id"] for v in status.values()
       if str(v.get("status")).endswith("failed") and v.get("metadata", {}).get("is_duplicate")}
other_failed = [k for k, v in status.items() if str(v.get("status")).endswith("failed") and not v.get("metadata", {}).get("is_duplicate")]
graph = (src / "graph_chunk_entity_relation.graphml.xml").read_text(encoding="utf-8")
lengths = sorted(len(c["context"]) for c in contexts)
record = {
    "source_dir": src.name, "build_done": json.loads((out / "colab/build_done.json").read_text()),
    "sha256": {"contexts.jsonl": sha(out / "colab/contexts.jsonl"), "build_done.json": sha(out / "colab/build_done.json"),
               "kv_store_doc_status.json": sha(src / "kv_store_doc_status.json"),
               "corpus.jsonl": sha("colab_upload/lightrag/corpus.jsonl"), "queries.jsonl": sha("colab_upload/lightrag/queries.jsonl")},
    "queries": len(queries), "contexts": len(contexts), "unique_context_ids": len(set(ids)),
    "missing_ids": sorted({q["id"] for q in queries} - set(ids)), "extra_ids": sorted(set(ids) - {q["id"] for q in queries}),
    "by_split": dict(collections.Counter(c["split"] for c in contexts)), "modes": dict(collections.Counter(c["mode"] for c in contexts)),
    "empty_contexts": sum(not c["context"].strip() for c in contexts),
    "context_chars": {"min": lengths[0], "median": lengths[len(lengths) // 2], "max": lengths[-1], "total": sum(lengths)},
    "corpus_docs": len(corpus), "docs_processed": sum(k in corpus_ids and v.get("status") == "processed" for k, v in status.items()),
    "docs_skipped_as_duplicate_content": dup, "docs_failed_other": other_failed,
    "chunks": sum(int(v.get("chunks_count") or 0) for k, v in status.items() if k in corpus_ids),
    "graph_nodes": len(re.findall(r"<node ", graph)), "graph_edges": len(re.findall(r"<edge ", graph)),
    "not_in_upload": ["vllm.log", "pip freeze (phiên bản lightrag-hku, vllm, sentence-transformers)", "revision của model"],
}
assert not record["missing_ids"] and not record["extra_ids"] and not record["empty_contexts"] and not other_failed
assert record["docs_processed"] + len(dup) == len(corpus)
(out / "intake.json").write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps({k: v for k, v in record.items() if k not in ("sha256",)}, ensure_ascii=False, indent=1))
PY

log prompts dev
$PY scripts/eval/lightrag_package.py prompts --contexts $O/colab/contexts.jsonl --split dev --out $O/dev/prompts/lightrag.jsonl
log diag dev
$PY scripts/eval/lightrag_package.py diag --out $O/dev/coverage.json \
  --prompts $O/dev/prompts/lightrag.jsonl $DV/b4.jsonl $DV/b5.jsonl $DV/b7.jsonl $DV/b7plus.jsonl $DV/proposed2.jsonl $PH/bvnone.jsonl
log DONE

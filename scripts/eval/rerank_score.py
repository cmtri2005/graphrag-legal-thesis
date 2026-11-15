#!/usr/bin/env python3
"""Cross-encoder scores for the reranker's candidate pool: computed on a GPU (Colab), read back locally.

This machine has no GPU, and 100 candidates per question is too slow on CPU. So the work is split:

    pairs  (local)  pool files of `run_vilextime.py --hybrid --retrieval-only --k 100`, each named
                    <system>.jsonl  ->  pairs.jsonl, one line per distinct (question, unit text)
    score  (Colab)  pairs.jsonl + a cross-encoder  ->  scores__<model>.jsonl and a .meta.json beside it

`--rerank MODEL --rerank-scores FILE` (run_vilextime.py, colab_b1.py export) then reorders the same pool
from that file. A pair without a score is an error there, never a silent CPU fallback.
`score` is resumable: keys already in the output are skipped.

    python scripts/eval/rerank_score.py pairs runs/X/pool/b4.jsonl runs/X/pool/b7plus.jsonl \\
        --release data/vilextime_dataset_h6/vilextime.jsonl --out colab_upload/rerank/dev/pairs.jsonl
    python rerank_score.py score dev/pairs.jsonl --model BAAI/bge-reranker-v2-m3 --out-dir scores_dev
"""
from __future__ import annotations

import argparse
import hashlib
import json
import time
from datetime import datetime, timezone
from pathlib import Path

MAX_LENGTH = 512     # = retrieve.Reranker.MAX_LENGTH; test_rerank_score keeps the two equal


def pair_key(question: str, text: str) -> str:      # copy of retrieve.pair_key (Colab has no repo); same test
    return hashlib.sha256(f"{question}\x00{text}".encode()).hexdigest()


def pairs(args) -> None:
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
    from vilexgraph.framework import systems
    from vilexgraph.framework.corpus import Corpus

    question = {r["id"]: r["question"] for r in map(json.loads, args.release.open(encoding="utf-8"))}
    corpus, seen, rows = Corpus(args.index), set(), 0
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", encoding="utf-8") as sink:
        for path in args.pools:
            context = systems.get(path.stem).context
            for pred in map(json.loads, path.open(encoding="utf-8")):
                rows += 1
                text = {u.unit_id: u.retrieval_text(context) for u in corpus.units(pred["retrieved"])}
                for unit_id in pred["retrieved"]:       # a unit gone from the corpus scores as "", as Reranker does
                    q, t = question[pred["id"]], text.get(unit_id, "")
                    key = pair_key(q, t)
                    if key not in seen:
                        seen.add(key)
                        sink.write(json.dumps({"key": key, "q": q, "t": t}, ensure_ascii=False) + "\n")
    print(f"{args.out}: {len(seen)} distinct pairs from {rows} rows of {len(args.pools)} pools, "
          f"sha256={hashlib.sha256(args.out.read_bytes()).hexdigest()}")


def score(args) -> None:
    import sentence_transformers
    import torch
    import transformers
    from huggingface_hub import HfApi

    todo = [json.loads(line) for line in args.pairs.open(encoding="utf-8")]
    bad = [r["key"] for r in todo if pair_key(r["q"], r["t"]) != r["key"]]
    if bad:
        raise SystemExit(f"{args.pairs}: {len(bad)} pairs do not match their key, first {bad[0]}")
    args.out_dir.mkdir(parents=True, exist_ok=True)
    out = args.out_dir / f"scores__{args.model.replace('/', '__')}.jsonl"
    done = {json.loads(line)["key"] for line in out.open(encoding="utf-8")} if out.exists() else set()
    todo = [r for r in todo if r["key"] not in done]
    print(f"{args.model}: {len(done)} already scored, {len(todo)} to score")
    revision = HfApi().model_info(args.model).sha
    encoder = sentence_transformers.CrossEncoder(args.model, revision=revision, max_length=MAX_LENGTH)
    started = time.monotonic()
    with out.open("a", encoding="utf-8") as sink:
        for i in range(0, len(todo), args.chunk):
            chunk = todo[i:i + args.chunk]
            values = encoder.predict([(r["q"], r["t"]) for r in chunk], batch_size=args.batch, show_progress_bar=False)
            for r, value in zip(chunk, values.tolist()):
                sink.write(json.dumps({"key": r["key"], "score": float(value), "model": args.model}) + "\n")
            sink.flush()
            print(f"  {min(i + args.chunk, len(todo))}/{len(todo)} · {time.monotonic() - started:.0f}s")
    meta = {"model": args.model, "revision": revision, "max_length": MAX_LENGTH, "batch": args.batch,
            "pairs_file": args.pairs.name, "pairs_sha256": hashlib.sha256(args.pairs.read_bytes()).hexdigest(),
            "scores_sha256": hashlib.sha256(out.read_bytes()).hexdigest(),
            "rows": sum(1 for _ in out.open(encoding="utf-8")), "scored_this_call": len(todo),
            "gpu": torch.cuda.get_device_name(0) if torch.cuda.is_available() else "cpu",
            "torch": torch.__version__, "transformers": transformers.__version__,
            "sentence_transformers": sentence_transformers.__version__,
            "finished_utc": datetime.now(timezone.utc).isoformat(timespec="seconds")}
    out.with_suffix(".meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"-> {out} ({meta['rows']} rows, {meta['gpu']})")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="command", required=True)
    p = sub.add_parser("pairs")
    p.add_argument("pools", type=Path, nargs="+")
    p.add_argument("--release", type=Path, required=True)
    p.add_argument("--index", type=Path, default=Path("data/derived/corpus/index.sqlite"))
    p.add_argument("--out", type=Path, required=True)
    s = sub.add_parser("score")
    s.add_argument("pairs", type=Path)
    s.add_argument("--model", required=True)
    s.add_argument("--out-dir", type=Path, required=True)
    s.add_argument("--batch", type=int, default=64)
    s.add_argument("--chunk", type=int, default=2048, help="pairs per flush to disk")
    args = ap.parse_args()
    {"pairs": pairs, "score": score}[args.command](args)


if __name__ == "__main__":
    main()

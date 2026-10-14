#!/usr/bin/env python3
"""Check an embedding run brought back from another machine (docs/plans/active/embed-gpu.md).

    1. it was built from this index: every unit of the layer has a row, and the sha of a
       sample of units recomputed here matches the stored one;
    2. it is whole: every unit's sha has a vector, every (shard, row) exists, no NaN,
       every vector has norm 1 (fp16 tolerance);
    3. it is the same model: a sample re-embedded here on CPU has cosine >= MIN_COS with
       the stored vector (GPU and CPU differ only by rounding).

Usage:
    python scripts/eval/verify_embed.py --layer asis
    python scripts/eval/verify_embed.py --layer asis --sample 0     # skip the CPU re-embed
"""
from __future__ import annotations

import argparse
import hashlib
import random
import sqlite3
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from embed_corpus import MODEL, default_out, prepare  # noqa: E402
from vilexgraph.framework.corpus import Corpus, Unit  # noqa: E402

MIN_COS = 0.99


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--layer", choices=("asis", "version"), required=True)
    ap.add_argument("--index", type=Path, default=Path("data/derived/corpus/index.sqlite"))
    ap.add_argument("--out", type=Path, help="default: as embed_corpus.py for --model")
    ap.add_argument("--model", default=MODEL, help="only picks the default --out")
    ap.add_argument("--sample", type=int, default=100, help="units re-embedded on CPU")
    args = ap.parse_args()
    out = args.out or default_out(args.layer, args.model)
    db = sqlite3.connect(out / "texts.sqlite")
    corpus = Corpus(args.index)
    errors = []

    meta = dict(db.execute("SELECT key, value FROM meta"))
    print("meta", meta)
    want = corpus.db.execute("SELECT COUNT(*) FROM units WHERE layer = ?", (args.layer,)).fetchone()[0]
    have = db.execute("SELECT COUNT(*) FROM unit").fetchone()[0]
    if have != want:
        errors.append(f"{have:,} units embedded, the index has {want:,}")
    orphan = db.execute("SELECT COUNT(*) FROM unit u LEFT JOIN text t ON t.sha = u.sha WHERE t.sha IS NULL").fetchone()[0]
    if orphan:
        errors.append(f"{orphan:,} units point at a sha with no vector")

    rows = dict(db.execute("SELECT shard, COUNT(*) FROM text GROUP BY shard"))
    vectors = {}
    for shard, n in sorted(rows.items()):
        v = np.load(out / f"shard-{shard:05d}.npy", mmap_mode="r")
        if v.shape[0] != n:
            errors.append(f"shard {shard}: {v.shape[0]} vectors, {n} texts")
        norms = np.linalg.norm(np.asarray(v, dtype=np.float32), axis=1)
        if not np.isfinite(norms).all() or np.abs(norms - 1).max() > 1e-2:
            errors.append(f"shard {shard}: NaN or norm off 1 (max |n-1| {np.nanmax(np.abs(norms - 1)):.3g})")
        vectors[shard] = v
    print(f"{have:,} units · {sum(rows.values()):,} texts · {len(rows)} shards")

    if args.sample:
        ids = [r[0] for r in db.execute("SELECT unit_id FROM unit")]
        pick = random.Random(0).sample(ids, min(args.sample, len(ids)))
        texts, stored = [], []
        for uid in pick:
            row = corpus.db.execute(Corpus._SELECT + " WHERE u.unit_id = ?", (uid,)).fetchone()
            text = Unit(**dict(row)).retrieval_text(True)
            sha = hashlib.sha256(text.encode()).hexdigest()
            want_sha = db.execute("SELECT sha FROM unit WHERE unit_id = ?", (uid,)).fetchone()[0]
            if sha != want_sha:
                errors.append(f"{uid}: text here differs from the one embedded (another index?)")
                continue
            shard, i = db.execute("SELECT shard, row FROM text WHERE sha = ?", (sha,)).fetchone()
            texts.append(prepare(meta["model"], text))
            stored.append(np.asarray(vectors[shard][i], dtype=np.float32))
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer(meta["model"], device="cpu")
        model.max_seq_length = int(meta["max_seq_length"])
        here = model.encode(texts, normalize_embeddings=True, convert_to_numpy=True)
        cos = (here * np.stack(stored)).sum(axis=1)
        print(f"CPU vs stored cosine over {len(cos)}: min {cos.min():.4f} · mean {cos.mean():.4f}")
        if cos.min() < MIN_COS:
            errors.append(f"cosine {cos.min():.4f} < {MIN_COS}: not the same model or config")

    if errors:
        raise SystemExit("FAIL\n" + "\n".join(errors))
    print("OK")


if __name__ == "__main__":
    main()

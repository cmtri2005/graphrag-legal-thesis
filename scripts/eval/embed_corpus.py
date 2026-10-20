#!/usr/bin/env python3
"""Embed the corpus for dense retrieval (ADR 0004 §4; MASTER_RESEARCH_GUIDE K-09, W1-08).

What is embedded is what a system reads: `Unit.retrieval_text(True)`, the hierarchy
header and the unit's text, for one layer (B3 and B4 read layer A). A text is embedded
once however many units carry it, keyed by sha256: 1,455,372 layer-A units carry
1,247,953 distinct texts before the header is added.

The run is meant to take days on a CPU, so it can be killed and restarted at any point:
units are read in rowid order, and each shard records the last rowid it covers. After the
corpus is rebuilt, `--rescan` reads every unit again: a text already embedded is skipped by
its sha, so only new wording reaches the model, and each unit is re-pointed at its text.

    <out>/texts.sqlite       unit_id -> sha256; sha256 -> (shard, row); meta
    <out>/shard-00000.npy    float16, L2-normalised, one row per distinct text

Usage:
    python scripts/eval/embed_corpus.py --layer asis --max-seq-length 512
    python scripts/eval/embed_corpus.py --layer asis --limit 2000 --out /tmp/embed-test   # timing
    python scripts/eval/embed_corpus.py --layer asis --max-seq-length 256 \
        --model dangvantuan/vietnamese-embedding      # -> data/derived/embed/asis-vietnamese-embedding
    python scripts/eval/embed_corpus.py --layer asis --max-seq-length 256 \
        --model dangvantuan/vietnamese-embedding --rescan   # after build_corpus + index_corpus
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from vilexgraph.framework.corpus import Corpus, Unit  # noqa: E402

MODEL = "AITeamVN/Vietnamese_Embedding"     # ADR 0004 §4
# PhoBERT-base (docs/plans/active/embed-phobert-cpu.md): reads word-segmented text, 256 positions
PHOBERT = "dangvantuan/vietnamese-embedding"
INDEX = Path("data/derived/corpus/index.sqlite")
READ = 5_000


def prepare(model: str, text: str) -> str:
    """What the model is fed. The sha (and dedup) stays on the unsegmented text."""
    if model == PHOBERT:
        from pyvi.ViTokenizer import tokenize
        return tokenize(text)
    return text


def default_out(layer: str, model: str) -> Path:
    return Path("data/derived/embed") / (layer if model == MODEL else f"{layer}-{model.split('/')[-1]}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--layer", choices=("asis", "version"), required=True)
    ap.add_argument("--max-seq-length", type=int, required=True, help="tokens; longer texts are truncated")
    ap.add_argument("--index", type=Path, default=INDEX)
    ap.add_argument("--out", type=Path, help="default: data/derived/embed/<layer>")
    ap.add_argument("--shard", type=int, default=20_000, help="distinct texts per shard")
    ap.add_argument("--batch", type=int, default=16)
    ap.add_argument("--limit", type=int, help="stop after this many units (a timing run)")
    ap.add_argument("--model", choices=(MODEL, PHOBERT), default=MODEL)
    ap.add_argument("--rescan", action="store_true", help="read every unit again after the corpus is rebuilt")
    args = ap.parse_args()
    if args.model == PHOBERT and args.max_seq_length > 256:
        raise SystemExit(f"{PHOBERT} has 258 positions: --max-seq-length must be <= 256")
    out = args.out or default_out(args.layer, args.model)
    out.mkdir(parents=True, exist_ok=True)

    db = sqlite3.connect(out / "texts.sqlite")
    db.executescript("""
        CREATE TABLE IF NOT EXISTS unit (unit_id TEXT PRIMARY KEY, sha TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS text (sha TEXT PRIMARY KEY, shard INTEGER NOT NULL, row INTEGER NOT NULL);
        CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT NOT NULL);""")
    want = {"model": args.model, "layer": args.layer, "max_seq_length": str(args.max_seq_length),
            "text": "pyvi(Unit.retrieval_text(True))" if args.model == PHOBERT else "Unit.retrieval_text(True)"}
    have = dict(db.execute("SELECT key, value FROM meta WHERE key IN (?,?,?,?)", list(want)))
    if have and have != want:
        raise SystemExit(f"{out} was built with {have}; this run asks for {want}. Use another --out.")
    db.executemany("INSERT OR REPLACE INTO meta VALUES (?,?)", want.items())
    db.commit()
    if args.rescan:   # units the rebuilt corpus dropped must not keep a vector; the scan re-adds the rest
        db.execute("DELETE FROM unit")
        db.commit()
    last = 0 if args.rescan else int((db.execute("SELECT value FROM meta WHERE key='last_rowid'").fetchone() or ["0"])[0])
    shard = db.execute("SELECT COALESCE(MAX(shard) + 1, 0) FROM text").fetchone()[0]

    import numpy as np
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer(args.model)     # CUDA when present, else CPU
    model.max_seq_length = args.max_seq_length
    print(f"device {model.device}", flush=True)

    corpus = Corpus(args.index)
    select = Corpus._SELECT.replace("SELECT ", "SELECT u.rowid AS rid, ", 1) + \
        " WHERE u.layer = ? AND u.rowid > ? ORDER BY u.rowid LIMIT ?"
    pending: dict[str, str] = {}
    owners: list[tuple[str, str]] = []
    units = embedded = 0
    started = time.monotonic()

    def flush(upto: int) -> None:
        nonlocal shard, pending, owners, embedded
        order = sorted(pending, key=lambda sha: len(pending[sha]))    # less padding per batch
        if order:
            vectors = model.encode([prepare(args.model, pending[sha]) for sha in order], batch_size=args.batch,
                                   normalize_embeddings=True, convert_to_numpy=True)
            np.save(out / f"shard-{shard:05d}.npy", vectors.astype(np.float16))
            db.executemany("INSERT INTO text VALUES (?,?,?)", [(sha, shard, i) for i, sha in enumerate(order)])
            shard += 1
            embedded += len(order)
        db.executemany("INSERT OR REPLACE INTO unit VALUES (?,?)", owners)   # a reworded unit takes its new text
        db.execute("INSERT OR REPLACE INTO meta VALUES ('last_rowid', ?)", (str(upto),))
        db.commit()
        rate = embedded / max(time.monotonic() - started, 1e-9)
        print(f"  rowid {upto:,} · {units:,} units · {embedded:,} texts embedded · {rate:.1f} texts/s", flush=True)
        pending, owners = {}, []

    while args.limit is None or units < args.limit:
        take = READ if args.limit is None else min(READ, args.limit - units)
        rows = corpus.db.execute(select, (args.layer, last, take)).fetchall()
        if not rows:
            break
        for row in rows:
            fields = dict(row)
            last = fields.pop("rid")
            text = Unit(**fields).retrieval_text(True)
            sha = hashlib.sha256(text.encode()).hexdigest()
            owners.append((fields["unit_id"], sha))
            units += 1
            if sha not in pending and not db.execute("SELECT 1 FROM text WHERE sha=?", (sha,)).fetchone():
                pending[sha] = text
        if len(pending) >= args.shard or (args.limit is not None and units >= args.limit):
            flush(last)
    if pending or owners:
        flush(last)
    distinct = db.execute("SELECT COUNT(*) FROM text").fetchone()[0]
    print(json.dumps({"units": units, "distinct_texts": distinct, "shards": shard,
                      "seconds": round(time.monotonic() - started)}))


if __name__ == "__main__":
    main()

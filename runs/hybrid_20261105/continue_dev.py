"""Finish this dev experiment after the separately running embedding job commits.

Run from the repository root. Commands are resumable and never select test rows.
See docs/plans/active/lai-ghep-va-vbhn.md for scope and authority.
"""
import hashlib
import json
from pathlib import Path
import sqlite3
import subprocess
import sys
import time

OUT = Path("runs/hybrid_20261105")
EMBED = Path("data/derived/embed/version-vietnamese-embedding")
RELEASE = Path("data/vilextime_dataset/vilextime.jsonl")
PYTHON = sys.executable


def run(*args):
    command = [str(a) for a in args]
    print("RUN", " ".join(command), flush=True)
    subprocess.run(command, check=True)


def read_only(path):
    return sqlite3.connect(f"file:{path}?mode=ro", uri=True)


def main():
    # Refuse to mix changed inputs into this experiment.
    for line in (OUT / "inputs.sha256").read_text().splitlines():
        digest, name = line.split("  ", 1)
        if hashlib.sha256(Path(name).read_bytes()).hexdigest() != digest:
            raise RuntimeError(f"Input changed since experiment start: {name}")
    rows = [json.loads(line) for line in RELEASE.open()]
    expected = {r["id"] for r in rows
                if r["split"] == "dev" and r["as_of_strategy"] == "giua_khoang"}
    if len(expected) != 151:
        raise RuntimeError(f"Expected the frozen 151 dev IDs, got {len(expected)}")
    ids = OUT / "dev_ids.txt"
    ids.write_text("\n".join(sorted(expected)) + "\n")
    with read_only("data/derived/corpus/index.sqlite") as db:
        want, last = db.execute(
            "SELECT COUNT(*), MAX(rowid) FROM units WHERE layer='version'").fetchone()
    while True:
        with read_only(EMBED / "texts.sqlite") as db:
            have = db.execute("SELECT COUNT(*) FROM unit").fetchone()[0]
            checkpoint = db.execute("SELECT value FROM meta WHERE key='last_rowid'").fetchone()
        print(f"Embedding checkpoint: {have:,}/{want:,} units; rowid {checkpoint}", flush=True)
        if have == want and checkpoint and int(checkpoint[0]) == last:
            break
        time.sleep(30)

    run(PYTHON, "scripts/eval/verify_embed.py", "--layer", "version",
        "--model", "dangvantuan/vietnamese-embedding", "--out", EMBED)
    paths = []
    for system in ("b7pp", "proposed"):
        for variant, flag in (("lex", "--no-dense"), ("hyb", "--hybrid")):
            path = OUT / "dev" / f"{system}-{variant}.jsonl"
            run(PYTHON, "scripts/eval/run_vilextime.py", "--system", system, flag,
                "--retrieval-only", "--release", RELEASE, "--split", "dev",
                "--as-of-strategy", "giua_khoang", "--embed", EMBED, "--out", path)
            predictions = [json.loads(line) for line in path.open()]
            if len(predictions) != len(expected) or {p["id"] for p in predictions} != expected:
                raise RuntimeError(f"Missing, duplicated or extra dev predictions: {path}")
            paths.append(path)
    run(PYTHON, "scripts/eval/score_vilextime.py", *paths, "--release", RELEASE,
        "--split", "dev", "--ids", ids, "--ci", "2000",
        "--out", OUT / "dev" / "retrieval.score.json")
    print("DONE: vectors verified; four complete dev files and retrieval.score.json.", flush=True)
    print("Retrieval-only: answer metrics are placeholders; no test or generation was run.", flush=True)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        import traceback
        traceback.print_exc()
        sys.exit(1)

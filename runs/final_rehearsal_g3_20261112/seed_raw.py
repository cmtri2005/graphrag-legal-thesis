#!/usr/bin/env python3
"""Run r1 only: copy an old completion line into the r1 raw file when (id, prompt_sha256) is byte-identical to the
new prompt (no API call, same model/settings: checked against each old meta). api_generate then requests only the rest.
Usage: seed_raw.py PROMPTS_DIR RAW_DIR OLD_RAW_DIR... ; writes RAW_DIR/seed.json."""
import hashlib, json, sys
from pathlib import Path

prompts_dir, raw_dir, olds = Path(sys.argv[1]), Path(sys.argv[2]), [Path(p) for p in sys.argv[3:]]
LOCK = dict(provider="openai", model="gpt-4o-mini-2024-07-18", temperature=0.0, max_tokens=1024, seed=20261109)
M = LOCK["model"]
index = {}   # (system, id, prompt_sha256) -> (line, source); later dirs win only if the key is new (same bytes anyway)
for d in olds:
    for meta in sorted(d.glob("*.meta.json")):
        m = json.loads(meta.read_text())
        assert {k: m[k] for k in LOCK} == LOCK, (meta, "settings differ")
        raw = meta.with_name(meta.name[:-len(".meta.json")] + ".jsonl")
        for line in raw.read_text(encoding="utf-8").splitlines():
            it = json.loads(line)
            index.setdefault((m["system"], it["id"], it["prompt_sha256"]), (line, str(raw)))
report = {}
for p in sorted(prompts_dir.glob("*.jsonl")):
    rows = [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines()]
    system = rows[0]["system_name"]
    sha = hashlib.sha256(p.read_bytes()).hexdigest()
    dest = raw_dir / f"{system}__{M}__{sha[:12]}.r1.jsonl"
    assert not dest.exists(), dest
    hit = [index[(system, r["id"], r["prompt_sha256"])] for r in rows if (system, r["id"], r["prompt_sha256"]) in index]
    # keep prompt order
    lines = [index[k][0] for k in ((system, r["id"], r["prompt_sha256"]) for r in rows) if k in index]
    dest.write_text("".join(l + "\n" for l in lines), encoding="utf-8")
    report[system] = dict(rows=len(rows), seeded=len(lines), to_request=len(rows) - len(lines),
                          sources=sorted({s for _, s in hit}), raw=str(dest))
(raw_dir / "seed.json").write_text(json.dumps(report, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
print(json.dumps({k: (v["seeded"], v["to_request"]) for k, v in report.items()}))

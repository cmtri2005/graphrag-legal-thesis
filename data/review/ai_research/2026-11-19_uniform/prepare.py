"""Make every released lineage labelled by one Claude agent and one Codex agent (CMT 19/11/2026).

- round2_codex (both sides were Codex): new AI-A by Claude for its released lineages.
- silver01 (both sides were Claude): new AI-B by Codex for its released lineages.
The worksheet records are copied unchanged from the original input chunks, so worksheet_sha256 binds.
The new labeller never sees the old labels. Prompt = supp18 template with paths, hashes and counts replaced.
Run from repo root: python3 data/review/ai_research/2026-11-19_uniform/prepare.py
"""
import hashlib
import json
from pathlib import Path

AI = Path("data/review/ai_research")
RUN = AI / "2026-11-19_uniform"
FINAL = set(Path("data/vilextime_final/lineages_199.txt").read_text().split())
TEMPLATE = (AI / "2026-11-08_supp18/prompts/chunk01_ai-a.md").read_text()
JOBS = [  # (name, old run dir with a.jsonl, original input chunks, side to relabel)
    ("r2codex", AI / "2026-11-06_silver/round2_codex", AI / "2026-11-06_silver/round2_codex/input", "a"),
    ("silver01", AI / "2026-11-07_adjudication_all/snapshots/silver01", AI / "2026-11-06_silver/input", "b"),
]
CHUNK = 10


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    (RUN / "input").mkdir(parents=True, exist_ok=True)
    (RUN / "prompts").mkdir(exist_ok=True)
    plan = []
    for name, old, inp, side in JOBS:
        want = {json.loads(x)["lineage_id"] for x in open(old / "a.jsonl")} & FINAL
        recs = {}
        for f in sorted(inp.glob("chunk*.jsonl")):
            for line in open(f):
                r = json.loads(line)
                if r["record"]["lineage_id"] in want:
                    recs.setdefault(r["record"]["lineage_id"], line)
        assert set(recs) == want, (name, want - set(recs))
        ids = sorted(recs)
        for i in range(0, len(ids), CHUNK):
            n = i // CHUNK + 1
            chunk = RUN / "input" / f"{name}_chunk{n:02}.jsonl"
            chunk.write_text("".join(recs[x] for x in ids[i:i + CHUNK]))
            labeler = f"ai-{side}"
            p = (TEMPLATE
                 .replace("labeler = `ai-a`", f"labeler = `{labeler}`")
                 .replace('`labeler`="ai-a"', f'`labeler`="{labeler}"')
                 .replace("2026-11-08_supp18/chunk01.jsonl/ai-a", f"2026-11-19_uniform/{chunk.name}/{labeler}")
                 .replace("data/review/ai_research/2026-11-08_supp18/input/chunk01.jsonl", str(chunk))
                 .replace("164460cc81e2223b840207b60355d619f68f5492337d7c4b8781693afc7aa9d8", sha(chunk))
                 .replace("b92275cdfeb8c194d9a1c8e275c7fbfa80c06d4bc6b75a1a22f69cd81e25a72a",
                          sha(Path("docs/vilextime-annotation.md")))
                 .replace("9 dòng", f"{len(ids[i:i + CHUNK])} dòng"))
            assert str(chunk) in p and labeler in p
            out = RUN / "prompts" / f"{name}_chunk{n:02}_{labeler}.md"
            out.write_text(p)
            plan.append({"job": name, "side": side, "chunk": chunk.name, "rows": len(ids[i:i + CHUNK]), "prompt": out.name})
    (RUN / "plan.json").write_text(json.dumps(plan, ensure_ascii=False, indent=1) + "\n")
    print(json.dumps(plan, ensure_ascii=False))


if __name__ == "__main__":
    main()

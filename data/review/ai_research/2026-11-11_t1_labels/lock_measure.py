"""Lock complete cross-model labels and run the native agreement measurement.

Original replies stay untouched. Run with .venv/bin/python from repo root.
The temporary native lock receives canonical A schema and original B replies.
"""
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

RUN = Path(__file__).resolve().parent
ROOT = RUN.parents[3]
sys.path.insert(0, str(ROOT / "scripts/review"))
from ai_labels import load_inputs, lock, measure, read_labels, review_export


def main():
    chunks = sorted((RUN / "input").glob("chunk*.jsonl"))
    missing = [f"{who}_{c.stem}.md" for c in chunks for who in ("a", "b")
               if not (RUN / "raw" / f"{who}_{c.stem}.md").exists()]
    if len(chunks) != 2 or missing:
        raise ValueError(f"Incomplete raw replies; no labels locked: {missing}")
    for name in ("validate_b.py", "normalize_a.py", "locate_a_evidence.py"):
        subprocess.run([sys.executable, str(RUN / name)], check=True)
    records = load_inputs(RUN)
    assert len(records) == 60
    with tempfile.TemporaryDirectory() as td:
        stage = Path(td)
        (stage / "input").symlink_to(RUN / "input", target_is_directory=True)
        (stage / "raw").mkdir()
        for chunk in chunks:
            expected = {r["record"]["lineage_id"] for r in map(json.loads, chunk.read_text().splitlines())}
            for who in ("a", "b"):
                name = f"{who}_{chunk.stem}.md"
                content = (RUN / "raw" / name).read_text()
                blocks = list(re.finditer(r"```jsonl\s*\n(.*?)```", content, re.S))
                assert len(blocks) == 1, name
                if who == "a":
                    block = blocks[0]
                    canonical = (RUN / "canonical_a" / f"a_{chunk.stem}.jsonl").read_text()
                    content = content[:block.start(1)] + canonical + content[block.end(1):]
                raw = stage / "raw" / name
                raw.write_text(content)
                lines = re.findall(r"```jsonl\s*\n(.*?)```", content, re.S)[0]
                temp = stage / "check.jsonl"
                temp.write_text(lines.strip() + "\n")
                labels, rejected = read_labels(temp, who, records)
                assert not rejected and set(labels) == expected, (name, rejected)
        lock(stage)
        targets = [(RUN / f"{who}.jsonl").exists() for who in ("a", "b")]
        if any(targets) and not all(targets):
            raise ValueError("Partial existing lock; preserve it and inspect before proceeding")
        for who in ("a", "b"):
            out, source = RUN / f"{who}.jsonl", stage / f"{who}.jsonl"
            if out.exists():
                assert out.read_bytes() == source.read_bytes(), f"Frozen {who} labels differ"
            else:
                with out.open("xb") as f:
                    f.write(source.read_bytes())
    result = measure(RUN)
    result["kind"] = "AI–AI cross-model: A Claude, B Codex; actual model details in raw provenance/Claude metadata; not human agreement or legal accuracy"
    result["batch_note"] = "T1 đối chứng, 60 lineages (guideline 4.0 §3 T1); pre-adjudication. No source-insufficient valid labels filtered."
    (RUN / "metrics.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    assert result["coverage"]["paired"] == 60 and all(not result["coverage"]["rejected"][w] for w in ("a", "b"))
    review = RUN / "duyet_CMT.xlsx"
    if not review.exists():
        review_export(RUN, review, {})
    print(json.dumps({"paired": 60, "disagreements": len(result["disagreements"]),
                      "metrics": result["metrics"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

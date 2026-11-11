"""Validate all two blinded Codex replies with the native label validator."""
import collections
import hashlib
import json
import re
import sys
import tempfile
from pathlib import Path

RUN = Path(__file__).resolve().parent
ROOT = RUN.parents[3]
sys.path.insert(0, str(ROOT / "scripts/review"))
from ai_labels import load_inputs, read_labels


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    manifest = json.loads((RUN / "input/manifest.json").read_text())
    assert sha(ROOT / manifest["worksheet"]) == manifest["worksheet_file_sha256"]
    records = load_inputs(RUN)
    seen, chunks, statuses = set(), [], collections.Counter()
    for name, info in sorted(manifest["chunks"].items()):
        inp = RUN / "input" / name
        assert sha(inp) == info["sha256"]
        raw = RUN / "raw" / ("b_" + inp.stem + ".md")
        content = raw.read_text()
        blocks = re.findall(r"```jsonl\s*\n(.*?)```", content, re.S)
        provenance = re.findall(r"```json\s*\n(.*?)```", content, re.S)
        assert len(blocks) == len(provenance) == 1, raw
        json.loads(provenance[0])
        with tempfile.TemporaryDirectory() as td:
            temp = Path(td) / "b.jsonl"
            temp.write_text(blocks[0].strip() + "\n")
            labels, rejected = read_labels(temp, "b", records)
        assert not rejected, (raw, rejected)
        assert set(labels) == set(info["lineage_ids"]) and len(labels) == info["n"]
        assert not seen.intersection(labels), raw
        seen.update(labels)
        for lid, label in labels.items():
            assert label.get("evidence_status") in ("sufficient", "insufficient", "unavailable"), lid
            evidence = label.get("evidence", [])
            assert 1 <= len(evidence) <= 2, lid
            assert all(e.get("url") and e.get("quote") and e.get("source_tier") in
                       ("official", "worksheet", "secondary", "snippet") for e in evidence), lid
        count = collections.Counter(label["evidence_status"] for label in labels.values())
        statuses.update(count)
        chunks.append({"raw": raw.name, "raw_sha256": sha(raw), "input_sha256": sha(inp),
                       "prompt_sha256": sha(RUN / "prompts" / (inp.stem + "_ai-b.md")),
                       "valid": len(labels), "evidence_status": dict(count)})
    assert len(chunks) == 2 and seen == set(records) and len(seen) == 60
    result = {"validator": "scripts/review/ai_labels.py:read_labels + exact manifest coverage and structured evidence checks",
              "requested": 60, "valid": len(seen), "missing": [], "duplicates": [], "rejected": [],
              "evidence_status": dict(statuses), "chunks": chunks,
              "limits": "AI labels, not_verified; source sufficiency and blinding are worker reports, not legal accuracy or human acceptance. No paired lock or agreement measurement while AI-A is incomplete."}
    out = RUN / "b_raw_validation.json"
    if out.exists():
        assert json.loads(out.read_text()) == result, "Frozen B receipt differs; inspect before continuing"
    else:
        out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({k: result[k] for k in ("requested", "valid", "evidence_status")}, ensure_ascii=False))


if __name__ == "__main__":
    main()

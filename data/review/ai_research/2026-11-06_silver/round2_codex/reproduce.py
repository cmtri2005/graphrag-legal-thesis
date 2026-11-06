"""Validate six independent raw replies, lock them once, and measure Codex round 2.

Run from the repository root with .venv/bin/python <this file>.
Uses the existing AI-label owner; excludes Claude chunk01 and unrun chunk05–11.
"""
import hashlib
import json
import re
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(ROOT / "scripts/review"))
from ai_labels import load_inputs, lock, measure, read_labels

RUN = Path(__file__).resolve().parent
provenance = json.loads((RUN / "provenance.json").read_text())
for name, digest in provenance["inputs"].items():
    if hashlib.sha256((RUN / "input" / name).read_bytes()).hexdigest() != digest:
        raise ValueError(f"{name}: input hash changed")
for name, digest in provenance["source_sha256"].items():
    if hashlib.sha256((ROOT / name).read_bytes()).hexdigest() != digest:
        raise ValueError(f"{name}: source/guideline changed since this labeling round")
records = load_inputs(RUN)
if len(records) != 44:
    raise ValueError(f"Expected 44 unique silver records, got {len(records)}")
raw_files = []
for chunk in sorted((RUN / "input").glob("chunk*.jsonl")):
    expected = {json.loads(s)["record"]["lineage_id"] for s in chunk.read_text().splitlines() if s.strip()}
    for who in ("a", "b"):
        raw = RUN / "raw" / f"{who}_{chunk.stem}.md"
        content = raw.read_text(encoding="utf-8")
        blocks = re.findall(r"```jsonl\s*\n(.*?)```", content, re.S)
        if len(blocks) != 1:
            raise ValueError(f"{raw}: expected exactly one JSONL block")
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "labels.jsonl"
            path.write_text(blocks[0], encoding="utf-8")
            labels, rejected = read_labels(path, who, records)
        if rejected or set(labels) != expected:
            raise ValueError(f"{raw}: invalid labels: {rejected}; missing={expected-set(labels)}; extra={set(labels)-expected}")
        for lid, label in labels.items():
            if label.get("evidence_status") not in ("sufficient", "insufficient", "unavailable"):
                raise ValueError(f"{raw}, {lid}: invalid evidence_status")
            evidence = label.get("evidence", [])
            if not 1 <= len(evidence) <= 2 or any(
                    not e.get("quote") or not e.get("url") or
                    e.get("source_tier") not in ("official", "worksheet", "secondary", "snippet")
                    for e in evidence):
                raise ValueError(f"{raw}, {lid}: expected 1–2 source-tiered evidence entries with quote and URL")
        metadata = re.findall(r"```json\s*\n(.*?)```", content, re.S)
        if len(metadata) != 1:
            raise ValueError(f"{raw}: expected exactly one provenance block")
        json.loads(metadata[0])
        raw_files.append(raw)

locked = [(RUN / f"{w}.jsonl").exists() for w in ("a", "b")]
if any(locked) and not all(locked):
    raise ValueError("Partial lock: preserve existing labels and inspect before continuing")
if not any(locked):
    lock(RUN)
else:
    # Never silently accept frozen labels that differ from the raw replies.
    for who in ("a", "b"):
        lines = []
        for chunk in sorted((RUN / "input").glob("chunk*.jsonl")):
            text = (RUN / "raw" / f"{who}_{chunk.stem}.md").read_text()
            block = re.findall(r"```jsonl\s*\n(.*?)```", text, re.S)[0]
            lines += [s for s in block.splitlines() if s.strip()]
        if (RUN / f"{who}.jsonl").read_text() != "\n".join(lines) + "\n":
            raise ValueError(f"{who}: frozen labels differ from raw replies")
result = measure(RUN)
result["batch_note"] = "Silver chunk02–04, Codex continuation; pre-adjudication; excludes Claude chunk01"
result["kind"] = "AI–AI, Codex inherited model (exact identifier unavailable); not human agreement or legal accuracy"
(RUN / "metrics.json").write_text(json.dumps(result, ensure_ascii=False, indent=1) + "\n")
paths = [*sorted((RUN / "input").glob("*.jsonl")), *raw_files,
         RUN / "a.jsonl", RUN / "b.jsonl", RUN / "metrics.json", RUN / "provenance.json",
         Path(__file__).resolve()]
if (RUN / "duyet_CMT.xlsx").exists():
    paths.append(RUN / "duyet_CMT.xlsx")
(RUN / "SHA256SUMS").write_text("".join(
    f"{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.relative_to(RUN)}\n" for p in paths))
print(json.dumps({"coverage": result["coverage"], "metrics": result["metrics"],
                  "disagreements": len(result["disagreements"])}, ensure_ascii=False, indent=1))

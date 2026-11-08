"""Freeze all paired-label conflicts plus previously unresolved adjudications."""
import hashlib
import json
import re
import shutil
import sys
from pathlib import Path

WORK = Path(__file__).resolve().parent
ROOT = WORK.parents[3]
sys.path.insert(0, str(ROOT / "scripts/review"))
from ai_labels import LABEL_KEYS, read_labels


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rows(path):
    return [json.loads(s) for s in path.read_text().splitlines() if s.strip()]


def write_rows(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x") as out:
        out.write("".join(json.dumps(x, ensure_ascii=False) + "\n" for x in data))


assert not (WORK / "scope.json").exists(), "Preserve existing scope"
base = ROOT / "data/review/ai_research"
run_paths = {
    "pilot0": base / "2026-11-06_lo0",
    "silver01": base / "2026-11-06_silver",
    **{name: base / "2026-11-06_silver" / name for name in
       ("round2_codex", "round2_claude", "round3_mixed")},
}
frozen = {}
cases = []
run_info = {}
for run_id, run in run_paths.items():
    snap = WORK / "snapshots" / run_id
    (snap / "input").mkdir(parents=True)
    chunks = sorted((run / "input").glob("chunk*.jsonl"))
    if run_id == "silver01":
        chunks = [run / "input/chunk01.jsonl"]
    packets = {}
    for chunk in chunks:
        frozen[str(chunk.relative_to(ROOT))] = sha(chunk)
        shutil.copyfile(chunk, snap / "input" / chunk.name)
        for item in rows(chunk):
            lid = item["record"]["lineage_id"]
            assert lid not in packets
            packets[lid] = item
    labels = {}
    for who in ("a", "b"):
        source = run / f"{who}.jsonl"
        if source.exists():
            data = source.read_text()
        else:
            source = run / "raw" / f"{who}_chunk01.md"
            blocks = re.findall(r"```jsonl\s*\n(.*?)```", source.read_text(), re.S)
            assert len(blocks) == 1
            data = "\n".join(s for s in blocks[0].splitlines() if s.strip()) + "\n"
        frozen[str(source.relative_to(ROOT))] = sha(source)
        (snap / f"{who}.jsonl").write_text(data)
        labels[who], rejected = read_labels(snap / f"{who}.jsonl", who,
                                           {lid: item["record"] for lid, item in packets.items()})
        assert not rejected, rejected
        assert set(labels[who]) == set(packets)
    for pattern in ("*.xlsx", "metrics.json", "provenance.json", "SHA256SUMS",
                    "adjudication*.jsonl", "raw/*.md"):
        for path in run.glob(pattern):
            frozen[str(path.relative_to(ROOT))] = sha(path)
    old = run / "adjudication_report.jsonl"
    previous = {item["lineage_id"]: item for item in rows(old)} if old.exists() else {}
    count = 0
    for lid, packet in packets.items():
        a, b = labels["a"][lid], labels["b"][lid]
        disputed = [key for key in LABEL_KEYS if a.get(key, "") != b.get(key, "")]
        if not disputed and previous.get(lid, {}).get("disposition") != "unresolved":
            continue
        row = {**packet, "run_id": run_id, "case_id": run_id + "::" + lid,
               "lineage_id": lid, "a": a, "b": b, "disputed_fields": disputed,
               "raw_a_sha256": hashlib.sha256(json.dumps(a, sort_keys=True, ensure_ascii=False).encode()).hexdigest(),
               "raw_b_sha256": hashlib.sha256(json.dumps(b, sort_keys=True, ensure_ascii=False).encode()).hexdigest()}
        if lid in previous:
            row["prior_proposal"] = previous[lid]
        cases.append(row)
        count += 1
    run_info[run_id] = {"records": len(packets), "cases": count,
                        "original_run": str(run.relative_to(ROOT))}
for name in ("docs/vilextime-dinh-nghia.md", "docs/vilextime-annotation.md",
             ".claude/agents/legal-adjudicator.md", ".claude/skills/vn-legal-research/SKILL.md",
             ".claude/skills/vilextime-ai-labeling/SKILL.md", "scripts/review/ai_labels.py",
             "scripts/review/test2_labels.py"):
    frozen[name] = sha(ROOT / name)
for batch, start in enumerate(range(0, len(cases), 5), 1):
    write_rows(WORK / "input" / f"batch{batch:02}.jsonl", cases[start:start + 5])
scope = {"authority": "CMT user request 2026-11-07: use legal-adjudicator for all conflicts",
         "frozen_files": frozen, "runs": run_info,
         "expected_case_ids": [item["case_id"] for item in cases],
         "human_verification": "not_verified; CMT review required",
         "selection": "All Q1–Q4 or reason differences in all paired runs, plus prior unresolved cases"}
(WORK / "scope.json").write_text(json.dumps(scope, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"cases": len(cases), "runs": run_info}, ensure_ascii=False, indent=2))

"""Include disagreements hidden by within-model consensus on the same 44 inputs."""
import hashlib
import json
import shutil
import sys
from pathlib import Path

WORK = Path(__file__).resolve().parent
ROOT = WORK.parents[3]
sys.path.insert(0, str(ROOT / "scripts/review"))
from ai_labels import LABEL_KEYS, load_inputs, read_labels

scope = json.loads((WORK / "scope.json").read_text())
assert "round2_cross_model" not in scope["runs"]
old = [json.loads(s) for f in sorted((WORK / "input").glob("*.jsonl")) for s in f.read_text().splitlines()]
covered = {x["lineage_id"] for x in old}
run_id = "round2_cross_model"
snap = WORK / "snapshots" / run_id
shutil.copytree(WORK / "snapshots/round2_claude/input", snap / "input")
shutil.copyfile(WORK / "snapshots/round2_claude/a.jsonl", snap / "a.jsonl")
shutil.copyfile(WORK / "snapshots/round2_codex/b.jsonl", snap / "b.jsonl")
records = load_inputs(snap)
labels = {}
for who in ("a", "b"):
    labels[who], rejected = read_labels(snap / f"{who}.jsonl", who, records)
    assert not rejected
packets = {x["record"]["lineage_id"]: x for f in sorted((snap / "input").glob("*.jsonl"))
           for x in map(json.loads, f.read_text().splitlines())}
added = []
for lid, packet in packets.items():
    a, b = labels["a"][lid], labels["b"][lid]
    disputed = [key for key in LABEL_KEYS if a.get(key, "") != b.get(key, "")]
    if not disputed or lid in covered:
        continue
    added.append({**packet, "run_id": run_id, "case_id": run_id + "::" + lid,
                  "lineage_id": lid, "a": a, "b": b, "disputed_fields": disputed,
                  **{f"raw_{who}_sha256": hashlib.sha256(json.dumps(label, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
                     for who, label in (("a", a), ("b", b))}})
assert len(added) == 3
with (WORK / "input/batch12.jsonl").open("x") as out:
    out.write("".join(json.dumps(x, ensure_ascii=False) + "\n" for x in added))
scope["runs"][run_id] = {"records": 44, "cases": len(added),
    "original_run": "Claude AI-A vs Codex AI-B on identical round2 input; only conflicts absent from other packets"}
scope["expected_case_ids"] += [x["case_id"] for x in added]
scope["unique_lineages"] = len({x["lineage_id"] for x in old + added})
scope["selection"] += "; plus cross-model-only conflicts not present in within-model conflicts"
(WORK / "scope.json").write_text(json.dumps(scope, ensure_ascii=False, indent=2) + "\n")
print("Added 3 cross-model-only conflicts; 58 run-cases / 55 unique lineages")

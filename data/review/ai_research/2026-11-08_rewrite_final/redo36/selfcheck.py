"""Read-only native qcheck feedback on this writer's drafts."""
import json, sys
from pathlib import Path
sys.dont_write_bytecode = True
sys.path[:0] = ["/home/trica/UIT_Thesis/graphrag-legal-thesis/scripts/review", "/home/trica/UIT_Thesis/graphrag-legal-thesis/scripts/pipeline"]
from test2_packs import judge_question, copy_share
p = Path(__file__).resolve().parent
checks = json.loads((p / "check_inputs.json").read_text())
rows = [json.loads(l) for l in (p / "answers_3.jsonl").read_text().splitlines()]
assert len(rows) == len(checks) and {r["item"] for r in rows} == set(checks)
for r in rows:
    c = checks[r["item"]]
    print(json.dumps({"item": r["item"], "reason": judge_question(r["question"], c["context"], c["versions"]), "copy_share": round(copy_share(r["question"], c["versions"]), 3)}, ensure_ascii=False))

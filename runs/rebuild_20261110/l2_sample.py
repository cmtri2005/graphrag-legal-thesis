#!/usr/bin/env python3
"""H6 L2: 20 of the events the rule now applies on its own, with the lead-in it read, for a person to check.

Population: events whose status went needs_review/document_scope (before) -> auto_accepted (after).
Sample: random.Random(20261111).sample(sorted ids, 20). No legal conclusion is drawn here.
Usage: PYTHONPATH=src .venv/bin/python runs/rebuild_20261110/l2_sample.py
"""
import json, random, sys, collections
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts/pipeline"))
from extract_provision_events import lead_in, effective_clause_dates  # noqa: E402
from vilexgraph.build.provisions.text import parse_paragraphs  # noqa: E402

old = {}
for line in open(ROOT / "runs/rebuild_20261110/before/provision_events.jsonl", encoding="utf-8"):
    e = json.loads(line)
    if e["locator"] is None:
        old[e["id"]] = (e["status"], e["status_reason"])
new = [json.loads(l) for l in open(ROOT / "data/derived/provision_events.jsonl", encoding="utf-8")]
moved = {e["id"]: e for e in new if e["locator"] is None and e["status"] == "auto_accepted"
         and old.get(e["id"]) == ("needs_review", "document_scope")}
other = collections.Counter((old.get(e["id"], ("absent",))[0], e["status"], e["status_reason"]) for e in new if e["locator"] is None and e["id"] in old and old[e["id"]] != (e["status"], e["status_reason"]))
ids = random.Random(20261111).sample(sorted(moved), min(20, len(moved)))
out, md = [], [f"# H6 L2: mẫu 20 sự kiện được tự áp (NHÁP, chưa kiểm)", "",
               f"Nhóm: {len(moved)} sự kiện cấp văn bản chuyển needs_review/document_scope -> auto_accepted. Seed 20261111. Chỉ in câu dẫn, không kết luận pháp lý.",
               f"Mọi chuyển trạng thái cấp văn bản: {dict(other)}", ""]
for k, i in enumerate(ids, 1):
    e = moved[i]
    pid = e["actor_id"].split(":")[1]
    raw = json.loads((ROOT / f"data/raw/{pid}.json").read_text(encoding="utf-8"))
    ps = [p.text for p in parse_paragraphs(raw["documentContent"]["content"])]
    lead = lead_in(ps, e["evidence"])
    out.append({"id": i, "actor": e["actor_number"], "target": e["document_number"], "effective_on": e["effective_on"],
                "evidence": e["evidence"], "lead_in": lead[0] if lead else None, "same_paragraph": lead[1] if lead else None,
                "effect_dates": sorted(effective_clause_dates(ps))})
    md += [f"## {k}. {e['actor_number']} -> {e['document_number']}, hiệu lực {e['effective_on']}", f"- id: `{i}`",
           f"- evidence: {e['evidence'][:260]}", f"- câu dẫn đọc được ({'cùng đoạn' if lead and lead[1] else 'đoạn dẫn phía trên'}): {(lead[0] if lead else '')[:300]}",
           f"- ngày nêu trong điều khoản hiệu lực của văn bản tác động: {sorted(effective_clause_dates(ps))}", ""]
(Path(__file__).parent / "l2_sample.json").write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
(Path(__file__).parent / "l2_sample.md").write_text("\n".join(md) + "\n", encoding="utf-8")
print(len(moved), dict(other))

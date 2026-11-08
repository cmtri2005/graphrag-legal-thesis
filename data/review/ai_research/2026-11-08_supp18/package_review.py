"""Validate supplementary adjudication and export CMT review; never accept labels."""
import collections
import hashlib
import importlib.util
import json
import re
import sys
from pathlib import Path

RUN = Path(__file__).resolve().parent
ROOT = RUN.parents[3]
sys.path.insert(0, str(ROOT / "scripts/review"))
from ai_labels import load_inputs, read_labels, review_export
from test2_labels import GOOD


def main():
    owner = RUN.parent / "2026-11-07_adjudication_all/package_review.py"
    spec = importlib.util.spec_from_file_location("supp_validator", owner)
    validator = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(validator)
    validator.HERE, validator.ROOT = RUN / "adjudication", ROOT
    scope, inputs, outputs = validator.load_validate()
    for path in sorted((RUN / "adjudication/results").glob("batch*.jsonl")):
        raw = (RUN / "adjudication/raw" / (path.stem + ".md")).read_text()
        blocks = re.findall(r"```jsonl\s*\n(.*?)```", raw, re.S)
        provenance = re.findall(r"```json\s*\n(.*?)```", raw, re.S)
        assert len(blocks) == len(provenance) == 1, path
        json.loads(provenance[0])
        assert [json.loads(l) for l in blocks[0].splitlines() if l.strip()] == [json.loads(l) for l in path.read_text().splitlines()]
    records = load_inputs(RUN)
    labels = {}
    for who in ("a", "b"):
        labels[who], errors = read_labels(RUN / f"{who}.jsonl", who, records)
        assert not errors and len(labels[who]) == 18
    proposals = [{"lineage_id": r["lineage_id"], **r["proposed_label"]}
                 for r in outputs.values() if r["disposition"] != "unresolved"]
    content = "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in proposals)
    out = RUN / "adjudication.jsonl"
    if out.exists():
        assert out.read_text() == content
    else:
        with out.open("x") as f:
            f.write(content)
    review = RUN / "duyet_CMT_after_adjudication.xlsx"
    if not review.exists():
        review_export(RUN, review, {})
        from openpyxl import load_workbook
        from openpyxl.styles import Alignment
        wb = load_workbook(review)
        ws = wb.create_sheet("Hòa giải")
        ws.append(["case_id", "lineage_id", "disposition", "lập luận", "nguồn", "câu hỏi còn mở"])
        for cid in scope["expected_case_ids"]:
            r = outputs[cid]
            ws.append([cid, r["lineage_id"], r["disposition"], r["reasoning"],
                       "\n".join(str(e.get("url", "")) + "\n" + str(e.get("quote", "")) for e in r["evidence"]),
                       "\n".join(map(str, r["open_questions"]))])
        for col, width in zip("ABCDEF", (18, 35, 18, 75, 75, 65)):
            ws.column_dimensions[col].width = width
        for row in ws:
            for cell in row:
                if isinstance(cell.value, str):
                    cell.data_type = "s"
                cell.alignment = Alignment(wrap_text=True, vertical="top")
        ws.freeze_panes = "A2"
        wb["Đọc trước"].append(["Lô bổ sung chưa được CMT duyệt; đồng thuận trước hòa giải chưa đạt. Xem sheet Hòa giải cho các nguồn và câu hỏi chưa giải quyết."])
        wb.save(review)
    keys = [k for q in GOOD for k in (q, q + "_reason")]
    adj = {r["lineage_id"]: r for r in outputs.values()}
    counts = collections.Counter()
    for lid in records:
        a, b = labels["a"][lid], labels["b"][lid]
        if all(a[k] == b[k] for k in keys):
            verdict = a["verdict"]
        else:
            r = adj[lid]
            verdict = "unresolved" if r["disposition"] == "unresolved" else r["proposed_label"]["verdict"]
        counts[verdict] += 1
    summary = validator.summary_data(scope, inputs, outputs)
    summary.update(candidate_labels=dict(counts), requested=18,
                   human_acceptance="pending; prior silver acceptance does not cover this batch",
                   review=str(review.relative_to(ROOT)), agreement="pre-adjudication metrics unchanged; verdict gate not_met")
    (RUN / "adjudication/validation_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n")
    paths = sorted(p for p in RUN.rglob("*") if p.is_file() and "__pycache__" not in p.parts and p.name != "SHA256SUMS")
    (RUN / "SHA256SUMS").write_text("".join(f"{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.relative_to(RUN)}\n" for p in paths))
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

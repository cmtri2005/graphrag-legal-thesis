"""Package supplementary research without changing the frozen independent labels.

Run from the repo root using .venv/bin/python <this file>. Refuses to overwrite
the new review workbook, which may subsequently contain CMT's own work.
"""
import collections
import hashlib
import json
import sys
from pathlib import Path

WORK = Path(__file__).resolve().parent
RUN = WORK.parent
ROOT = WORK.parents[5]
sys.path.insert(0, str(ROOT / "scripts/review"))
from ai_labels import LABEL_KEYS, compact, review_export
from test2_labels import validate_label
from openpyxl import load_workbook
from openpyxl.styles import Alignment, Font


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rows(path):
    return [json.loads(s) for s in path.read_text(encoding="utf-8").splitlines() if s.strip()]


def display(value):
    text = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False)
    return text if len(text) <= 30000 else text[:29950] + " …[xem JSON đầy đủ]"


prov = json.loads((WORK / "provenance.json").read_text())
for name, digest in prov["frozen_original_sha256"].items():
    if sha(RUN / name) != digest:
        raise ValueError(f"Frozen original changed: {name}")
packets = {}
for path in sorted((WORK / "input").glob("*.jsonl")):
    if sha(path) != prov["input_sha256"][path.name]:
        raise ValueError(f"Research packet changed: {path}")
    for packet in rows(path):
        lid = packet["record"]["lineage_id"]
        if lid in packets:
            raise ValueError(f"Duplicate research input: {lid}")
        packets[lid] = packet
results = {}
for path in sorted((WORK / "input").glob("*.jsonl")):
    for item in rows(WORK / "results" / path.name):
        lid = item["lineage_id"]
        if lid not in packets or lid in results:
            raise ValueError(f"Foreign or duplicate research result: {lid}")
        packet = packets[lid]
        for key in ("worksheet_sha256", "raw_a_sha256", "raw_b_sha256"):
            if item.get(key) != packet[key]:
                raise ValueError(f"{lid}: stale {key}")
        if item.get("disposition") not in ("prefer_a", "prefer_b", "both_wrong", "confirm_both", "unresolved"):
            raise ValueError(f"{lid}: invalid disposition")
        if item.get("label_origin") != "ai" or item.get("verification_status") != "not_verified" or item.get("human_adjudication_required") is not True:
            raise ValueError(f"{lid}: research must remain an AI proposal awaiting human review")
        proposal = item.get("proposed_label")
        if proposal is not None:
            normalized, errors = validate_label(packet["record"], proposal)
            if errors or normalized["verdict"] != proposal.get("verdict"):
                raise ValueError(f"{lid}: invalid proposed label: {errors}")
        elif item["disposition"] != "unresolved":
            raise ValueError(f"{lid}: a resolved disposition needs a proposed label")
        if not item.get("reasoning"):
            raise ValueError(f"{lid}: missing reasoning")
        results[lid] = item
if set(results) != set(packets) or len(results) != 26:
    raise ValueError(f"Research coverage incomplete: {len(results)}/26")

out = RUN / "duyet_CMT_bo_sung.xlsx"
report = RUN / "adjudication_report.jsonl"
compatible = RUN / "adjudication.jsonl"
if any(p.exists() for p in (out, report, compatible)):
    raise FileExistsError("Preserve existing research/review artifacts; inspect before creating a new version")
ordered = [results[lid] for lid in packets]
report.write_text("".join(json.dumps(item, ensure_ascii=False) + "\n" for item in ordered))
# The existing export owner consumes flat labels. Unresolved cases stay in the
# complete report, not in this resolved-proposal adapter.
flat = []
for item in ordered:
    if item["proposed_label"] is not None and item["disposition"] != "unresolved":
        flat.append({**item, **item["proposed_label"], "proposed_label": item["proposed_label"]})
compatible.write_text("".join(json.dumps(item, ensure_ascii=False) + "\n" for item in flat))
review_export(RUN, out, {})
wb = load_workbook(out)
ws = wb["Duyệt"]
columns = {cell.value: i for i, cell in enumerate(ws[1], 1)}
detail = wb.create_sheet("Tra cứu bổ sung")
headers = ["lineage_id", "disposition", "đề xuất Q1–Q4", "mức đủ căn cứ", "lập luận", "nguồn", "câu hỏi còn mở"]
detail.append(headers)
for row in range(2, ws.max_row + 1):
    lid = ws.cell(row, columns["lineage_id"]).value
    if lid not in results:
        continue
    item = results[lid]
    proposal = item["proposed_label"]
    resolved = proposal is not None and item["disposition"] != "unresolved"
    explanation = (compact(proposal) if proposal else "Chưa đề xuất được nhãn đầy đủ")
    explanation += "\n\nĐỀ XUẤT AI, CHỜ CMT DUYỆT\n" + item["disposition"]
    explanation += "\n" + display(item["reasoning"]) + "\nCòn mở: " + display(item.get("open_questions", []))
    ws.cell(row, columns["de_xuat_hoa_giai"], display(explanation))
    # Native review_rows prioritizes raw A/B agreement. This task overlay also
    # exposes corrections to agreeing-but-insufficient labels; it never confirms them.
    for key in LABEL_KEYS:
        ws.cell(row, columns["chot_" + key], proposal.get(key, "") if resolved else "")
    ws.cell(row, columns["xac_nhan"], "")
    detail.append([lid, item["disposition"], compact(proposal) if proposal else "Chưa chốt",
                   (proposal or {}).get("evidence_status", "insufficient"), display(item["reasoning"]),
                   display(item.get("evidence", [])), display(item.get("open_questions", []))])
for sheet in (ws, detail):
    for row in sheet:
        for cell in row:
            if isinstance(cell.value, str):
                cell.data_type = "s"
                cell.alignment = Alignment(wrap_text=True, vertical="top")
detail.freeze_panes = "C2"
detail.auto_filter.ref = detail.dimensions
for col in "ABCDEFG":
    detail.column_dimensions[col].width = 42 if col not in "EFG" else 75
for cell in detail[1]:
    cell.font = Font(bold=True)
assert ws.max_row == 45 and detail.max_row == 27
assert all(ws.cell(row, columns["xac_nhan"]).value in (None, "") for row in range(2, 46))
wb.save(out)
summary = {"researched": len(results), "disposition": dict(collections.Counter(i["disposition"] for i in ordered)),
           "resolved_proposals": len(flat), "unresolved": sum(i["disposition"] == "unresolved" for i in ordered),
           "human_confirmations": 0, "original_labels_metrics_workbook_preserved": True,
           "workbook": out.name, "report": report.name}
(WORK / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n")
print(json.dumps(summary, ensure_ascii=False, indent=2))

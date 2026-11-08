"""Validate Codex legal-adjudicator results and export the concrete CMT sheet."""
import collections
import hashlib
import importlib.util
import json
import re
import sys
from pathlib import Path

RUN = Path(__file__).resolve().parent
ROOT = RUN.parents[3]
CANON = RUN / "schema_validated"
WORK = CANON / "adjudication_native"
sys.path.insert(0, str(ROOT / "scripts/review"))
from ai_labels import load_inputs, read_labels, review_export
from test2_labels import GOOD


def main():
    normalization = json.loads((CANON / "metadata_normalization.json").read_text())
    assert hashlib.sha256((RUN / "a.jsonl").read_bytes()).hexdigest() == normalization["source_a_sha256"]
    assert hashlib.sha256((CANON / "a.jsonl").read_bytes()).hexdigest() == normalization["canonical_a_sha256"]
    original = [json.loads(l) for l in (RUN / "a.jsonl").read_text().splitlines()]
    canonical = [json.loads(l) for l in (CANON / "a.jsonl").read_text().splitlines()]
    assert len(original) == len(canonical) == 128
    for a, b in zip(original, canonical):
        expected = a | {"original_evidence_status": "partial", "evidence_status": "insufficient"} if a["evidence_status"] == "partial" else a
        assert b == expected, a["lineage_id"]
    assert (RUN / "b.jsonl").read_bytes() == (CANON / "b.jsonl").read_bytes()
    old_metrics = json.loads((RUN / "metrics.json").read_text())
    new_metrics = json.loads((CANON / "metrics.json").read_text())
    assert old_metrics["metrics"] == new_metrics["metrics"] and old_metrics["by_group"] == new_metrics["by_group"]
    owner = ROOT / "data/review/ai_research/2026-11-07_adjudication_all/package_review.py"
    spec = importlib.util.spec_from_file_location("lo2_native_validator", owner)
    validator = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(validator)
    validator.HERE, validator.ROOT = WORK, ROOT
    scope, inputs, outputs = validator.load_validate()
    for path in sorted((WORK / "results").glob("batch*.jsonl")):
        raw = (WORK / "raw" / (path.stem + ".md")).read_text()
        blocks = re.findall(r"```jsonl\s*\n(.*?)```", raw, re.S)
        provenance = re.findall(r"```json\s*\n(.*?)```", raw, re.S)
        assert len(blocks) == len(provenance) == 1, path
        json.loads(provenance[0])
        assert [json.loads(l) for l in blocks[0].splitlines() if l.strip()] == [json.loads(l) for l in path.read_text().splitlines()]
    records = load_inputs(CANON)
    sides = {}
    for who in ("a", "b"):
        sides[who], errors = read_labels(CANON / f"{who}.jsonl", who, records)
        assert not errors and len(sides[who]) == 128
        assert all(r["evidence_status"] in ("sufficient", "insufficient", "unavailable") for r in sides[who].values())
    proposals = [{"lineage_id": r["lineage_id"], **r["proposed_label"],
                  "labeler": "ai-adjudicator", "label_origin": "ai", "verification_status": "not_verified"}
                 for r in outputs.values() if r["disposition"] != "unresolved"]
    content = "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in proposals)
    path = CANON / "adjudication.jsonl"
    if path.exists():
        assert path.read_text() == content
    else:
        with path.open("x") as f:
            f.write(content)
    review = RUN / "duyet_CMT_after_adjudication.xlsx"
    if not review.exists():
        review_export(CANON, review, {})
        from openpyxl import load_workbook
        from openpyxl.styles import Alignment, Font
        workbook = load_workbook(review)
        sheet = workbook.create_sheet("Hòa giải")
        sheet.append(["case_id", "lineage_id", "disposition", "lập luận", "nguồn", "câu hỏi còn mở"])
        for cid in scope["expected_case_ids"]:
            result = outputs[cid]
            sources = "\n".join(str(e.get("url", "")) + "\n" + str(e.get("quote", ""))
                                for e in result["evidence"])
            if len(sources) > 32767:
                sources = ("Trích nguồn vượt giới hạn ô Excel; dưới đây là phần xem trước. "
                           "Toàn bộ evidence giữ trong JSONL của ca " + cid + " tại " + str(WORK / "results") + ".\n\n" +
                           "\n\n".join(str(e.get("url", "")) + "\n" + str(e.get("quote", ""))[:1500]
                                        + (" … [xem JSONL đầy đủ]" if len(str(e.get("quote", ""))) > 1500 else "")
                                        for e in result["evidence"]))
                assert len(sources) <= 32767, cid
            sheet.append([cid, result["lineage_id"], result["disposition"], result["reasoning"],
                          sources, "\n".join(map(str, result["open_questions"]))])
        for column, width in zip("ABCDEF", (16, 35, 18, 75, 75, 65)):
            sheet.column_dimensions[column].width = width
        for row in sheet:
            for cell in row:
                if isinstance(cell.value, str):
                    cell.data_type = "s"
                cell.alignment = Alignment(wrap_text=True, vertical="top")
        for cell in sheet[1]:
            cell.font = Font(bold=True)
        sheet.freeze_panes = "A2"
        sheet.auto_filter.ref = sheet.dimensions
        workbook["Đọc trước"].append(["Lô mới chưa được CMT chấp nhận. Xem sheet Hòa giải cho lập luận, nguồn và ca unresolved. Trọng tài chạy Codex native; kết quả vẫn là đề xuất AI, không phải nhãn người."])
        workbook.save(review)
    keys = [k for q in GOOD for k in (q, q + "_reason")]
    adjudicated = {r["lineage_id"]: r for r in outputs.values()}
    proposed, groups = collections.Counter(), collections.defaultdict(collections.Counter)
    for lid, record in records.items():
        a, b = sides["a"][lid], sides["b"][lid]
        if all(a[k] == b[k] for k in keys):
            verdict = a["verdict"]
        else:
            r = adjudicated[lid]
            verdict = "unresolved" if r["disposition"] == "unresolved" else r["proposed_label"]["verdict"]
        proposed[verdict] += 1
        groups[record["group"]][verdict] += 1
    acceptance_path = ROOT / "data/review/ai_research/2026-11-08_adjudication_final/cmt_acceptance.json"
    acceptance = json.loads(acceptance_path.read_text())
    silver = acceptance_path.parent / acceptance["scope"]["file"]
    assert hashlib.sha256(silver.read_bytes()).hexdigest() == acceptance["scope"]["sha256"]
    accepted = acceptance["scope"]["dat"]
    summary = {**validator.summary_data(scope, inputs, outputs),
               "runtime": "Mixed legal-adjudicator execution: Codex native and resumed Claude CLI; per-packet raw provenance/metadata is authoritative. Failed quota attempts retained separately.",
               "candidate_labels": dict(proposed), "by_group": {g: dict(c) for g, c in groups.items()},
               "human_acceptance_new_batch": "pending; silver bulk acceptance does not cover these 128",
               "review": str(review.relative_to(ROOT)),
               "G2_quantity": {"required": 130, "accepted_silver": accepted,
                               "accepted_new": 0, "accepted_total": accepted,
                               "pending_ai_proposed_dat": proposed["dat"],
                               "conditional_total_if_CMT_accepts_all_proposed_dat": accepted + proposed["dat"],
                               "quantity_pass_now": accepted >= 130,
                               "note": "Quantity only; pending proposals and supplementary batch are not human-accepted labels. See supplementary summary for its completed AI adjudication. Agreement gate remains failed."}}
    (WORK / "validation_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n")
    files = [p for p in RUN.rglob("*") if p.is_file() and "__pycache__" not in p.parts and p.name != "SHA256SUMS"]
    (RUN / "SHA256SUMS").write_text("".join(f"{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.relative_to(RUN)}\n" for p in sorted(files)))
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

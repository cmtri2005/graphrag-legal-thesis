"""AI–AI label lock and measurement: invalid or mislabelled rows are rejected, never counted."""
import json

import pytest

import ai_labels
from test2_labels import worksheet_sha256


def test_lock_then_measure(tmp_path):
    records = [{"lineage_id": f"p{i}", "group": "T2", "batch": 0, "question": "Q?",
                "rows": [{"as_of": "2020-01-01", "answer": "x"}],
                "sources": {"actors": [{"passage": "Sửa Điều 2."}]}} for i in range(3)]
    (tmp_path / "input").mkdir()
    (tmp_path / "input" / "chunk1.jsonl").write_text(
        "".join(json.dumps({"worksheet_sha256": worksheet_sha256(r), "record": r}) + "\n" for r in records))

    def label(r, who, **kw):
        return json.dumps({"lineage_id": r["lineage_id"], "labeler": f"ai-{who}", "label_origin": "ai",
                           "verification_status": "not_verified", "guideline_version": "4.0",
                           "worksheet_sha256": worksheet_sha256(r), "q1": "dung", "q1_reason": "", "q2": "co",
                           "q2_reason": "", "q3": "co", "q3_reason": "", "q4": "khong", "q4_reason": "",
                           "verdict": "dat", "quote": "Sửa Điều 2.", **kw})

    (tmp_path / "raw").mkdir()
    a = [label(r, "a") for r in records]
    b = [label(records[0], "b"), label(records[1], "a"),  # wrong labeler -> rejected
         label(records[2], "b", q2="khong", q2_reason="cosmetic_only", verdict="khong_dat")]
    (tmp_path / "raw" / "a_chunk1.md").write_text("x\n```jsonl\n" + "\n".join(a) + "\n```\n")
    (tmp_path / "raw" / "b_chunk1.md").write_text("```jsonl\n" + "\n".join(b) + "\n```")
    ai_labels.lock(tmp_path)
    with pytest.raises(ValueError):
        ai_labels.lock(tmp_path)
    r = ai_labels.measure(tmp_path)
    assert r["coverage"]["paired"] == 2 and r["coverage"]["missing"]["b"] == ["p1"]
    assert r["disagreements"] == ["p2"]
    assert r["metrics"]["q2"]["adverse_labels"] == 1 and r["metrics"]["q2"]["gate"] == "not_evaluable"
    assert r["metrics"]["q1"]["ac1"] == 1.0


def test_review_roundtrip(tmp_path):
    from openpyxl import load_workbook
    test_lock_then_measure(tmp_path)  # p0 agreed, p1 B invalid, p2 disagree
    ai_labels.review_export(tmp_path, tmp_path / "r.xlsx", {})
    wb = load_workbook(tmp_path / "r.xlsx")
    ws = wb["Duyệt"]
    head = [c.value for c in ws[1]]
    col = lambda n: head.index(n) + 1
    assert ws.cell(2, col("chot_q1")).value == "dung" and not ws.cell(4, col("chot_q1")).value
    for r in (2, 3, 4):
        ws.cell(r, col("xac_nhan")).value = "dong_y"
    for r in (3, 4):
        for q, v in (("q1", "dung"), ("q2", "co"), ("q3", "co"), ("q4", "khong")):
            ws.cell(r, col("chot_" + q)).value = v
    wb.save(tmp_path / "r2.xlsx")
    r = ai_labels.review_import(tmp_path, tmp_path / "r2.xlsx", "CMT", tmp_path / "r.tsv")
    assert r == {"rows": 3, "phan_van": 0, "prefilled_confirmed": 1, "cmt_changed_ai_label": 0, "dat": 3}
    ws.cell(2, col("chot_q2")).value = "khong"  # edited an agreed row but kept dong_y
    wb.save(tmp_path / "r3.xlsx")
    with pytest.raises(ValueError, match="chọn sua"):
        ai_labels.review_import(tmp_path, tmp_path / "r3.xlsx", "CMT", tmp_path / "r.tsv")

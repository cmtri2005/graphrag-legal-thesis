"""Approved card 4.0 validation, independent labels and agreement reporting."""
import io
import json

import pytest

import test2_labels as labels


@pytest.fixture
def record():
    return {"lineage_id": "provision:p", "group": "T6", "stratum": "T6 cấp trên", "batch": 1,
            "question": "Thời hạn gửi hồ sơ là bao lâu?",
            "rows": [{"as_of": "2020-01-01", "answer": "Thời hạn là 30 ngày.", "short_answer": "30 ngày"},
                     {"as_of": "2021-01-01", "answer": "", "short_answer": ""}],
            "sources": {"actors": [{"text": "Bãi bỏ Điều 2 của Nghị định này.", "source_url": "https://example.org/law"}]}}


@pytest.fixture
def valid():
    return {"q1": "dung", "q2": "co", "q3": "co", "q4": "khong",
            "quote": "Bãi bỏ Điều 2 của Nghị định này.", "search_log": "Đã đọc văn bản bãi bỏ và khoản anh em."}


def test_required_evidence_and_derived_verdict(record, valid):
    result, errors = labels.validate_label(record, {**valid, "verdict": "khong_dat"})
    assert errors == []
    assert result["verdict"] == "dat"
    assert "quote:" in " ".join(labels.validate_label(record, {**valid, "quote": ""})[1])
    assert "search_log:" in " ".join(labels.validate_label(record, {**valid, "search_log": ""})[1])
    outside, errors = labels.validate_label(record, {**valid, "quote": "Câu trích từ phần khác của bản gốc."})
    assert not errors and outside["quote_in_provided_sources"] is False
    # Only whitespace differs after copying a sentence from its source.
    assert not labels.validate_label(record, {**valid, "quote": "Bãi bỏ Điều 2\ncủa Nghị định này."})[1]


def test_reasons_are_per_question_and_adverse_answer(record, valid):
    bad = {**valid, "q2": "khong", "q2_reason": "relocated"}
    assert "Q2:" in " ".join(labels.validate_label(record, bad)[1])
    accepted = {**valid, "q2": "khong", "q2_reason": "cosmetic_only"}
    result, errors = labels.validate_label(record, accepted)
    assert not errors and result["verdict"] == "khong_dat"
    assert "Q1:" in " ".join(labels.validate_label(record, {**valid, "q1_reason": "gold_wrong"})[1])
    unclear = {**valid, "q4": "khong_chac", "q4_reason": "relocation_unclear"}
    assert "note:" in " ".join(labels.validate_label(record, unclear)[1])
    assert not labels.validate_label(record, {**unclear, "note": "Nghi ở Điều 3 văn bản mới."})[1]


def test_save_and_state_read_only_own_labels(tmp_path, record, valid):
    a, b = tmp_path / "test2_A.tsv", tmp_path / "test2_B.tsv"
    assert labels.save_label(a, [record], "A", "absent", valid)["errors"]
    assert not a.exists()
    assert not labels.save_label(a, [record], "A", record["lineage_id"], valid)["errors"]
    b.write_text("THIS MUST NOT BE READ", encoding="utf-8")
    h = labels.handler([record], a, "A").__new__(labels.handler([record], a, "A"))
    h.path = "/api/state"
    got = []
    h.send = lambda value, *args, **kwargs: got.append(value)
    h.do_GET()
    assert got[0]["who"] == "A"
    assert got[0]["questions"][0]["label"]["labeler"] == "A"
    assert "THIS MUST NOT" not in json.dumps(got)
    # Query strings cannot switch the selected person's sheet.
    h.path = "/api/state?who=B"
    h.do_GET()
    assert got[-1]["errors"]


def test_http_rejects_foreign_origin_and_unknown_routes(tmp_path, record, valid):
    cls = labels.handler([record], tmp_path / "test2_A.tsv", "A")
    h = cls.__new__(cls)
    h.path = "/api/save"
    body = json.dumps({"lineage_id": record["lineage_id"], "label": valid}).encode()
    h.rfile = io.BytesIO(body)
    h.headers = {"Origin": "https://foreign.invalid", "Host": "127.0.0.1:8775", "Content-Length": str(len(body))}
    got = []
    h.send = lambda value, *args, **kwargs: got.append((value, args))
    h.do_POST()
    assert got[0][1] == (403,)
    assert not (tmp_path / "test2_A.tsv").exists()
    h.headers.pop("Origin")
    h.do_POST()
    assert not got[-1][0]["errors"]
    assert labels.read_labels(tmp_path / "test2_A.tsv")[record["lineage_id"]]["verdict"] == "dat"
    override = json.dumps({"who": "B", "lineage_id": record["lineage_id"], "label": valid}).encode()
    h.rfile = io.BytesIO(override)
    h.headers["Content-Length"] = str(len(override))
    h.do_POST()
    assert got[-1][1] == (403,)
    assert not (tmp_path / "test2_B.tsv").exists()


def test_raw_text_escaped_before_diff_and_short_answer_marks():
    marked = labels.marked_text("<script>30 ngày", "<script>20 ngày", "30 ngày")
    assert "<script>" not in marked
    assert "&lt;script&gt;" in marked
    assert "<mark>" in marked and "<strong>" in marked


def test_every_short_span_is_highlighted_and_lead_in_and_repeal_shown(tmp_path, record):
    text = "Phạt tiền 30 ngày, nghỉ 30 ngày, rồi nộp hồ sơ."
    marked = labels.marked_text(text, "", "30 ngày … nộp hồ sơ")
    assert marked.count("<strong>") == 3
    # The accepted short-answer syntax allows spans taken from the parent's lead-in.
    record["rows"][0].update(target={"lead_in": "Phạt tiền từ 10 đến 20 triệu đồng."},
                             short_answer="20 triệu đồng … 30 ngày")
    record["rows"][1].update(answer=None, answerable=False)
    rows = labels.state([record], tmp_path / "empty.tsv", "A")["questions"][0]["rows"]
    assert "<strong>20 triệu đồng</strong>" in rows[0]["marked_lead_in"]
    assert "<strong>" in rows[0]["marked_answer"]
    assert rows[1]["answer_status"] == "no_answer"


def test_report_excludes_pilot_and_preserves_undefined_negative_agreement(record, valid):
    pilot = {**record, "lineage_id": "pilot", "batch": 0}
    row, errors = labels.validate_label(record, valid)
    row.update(labeler="A", guideline_version="4.0", worksheet_sha256=labels.worksheet_sha256(record))
    assert not errors
    a = {record["lineage_id"]: row, "pilot": row}
    b = {k: {**r, "labeler": "B"} for k, r in a.items()}
    report = labels.agreement_report([pilot, record], a, b)
    assert report["selected"] == report["paired"] == 1
    assert report["metrics"]["q1"]["ac1"] == 1
    assert report["metrics"]["q1"]["p_neg"] is None
    assert report["metrics"]["q1"]["gate"] == "not_met"
    assert report["metrics"]["q4"]["gate"] == "unresolved_q4_categories"
    limited = labels.agreement_report([pilot, record], a, b, limit=50)
    assert limited["sample_completeness"]["status"] == "insufficient_selected"
    assert limited["sample_completeness"]["paired"] == 1
    assert not limited["sample_completeness"]["requested_sample_available"]
    missing = labels.agreement_report([pilot, record], a, {})
    assert missing["sample_completeness"]["status"] == "missing_pairs"
    pilot_a = {**row, "worksheet_sha256": labels.worksheet_sha256(pilot)}
    assert labels.agreement_report([pilot, record], {**a, "pilot": pilot_a},
                                   {**b, "pilot": {**pilot_a, "labeler": "B"}}, batch=0)["selected"] == 1
    with pytest.raises(ValueError, match="không hợp lệ"):
        labels.agreement_report([record], {record["lineage_id"]: {**row, "verdict": "khong_dat"}},
                                {record["lineage_id"]: {**row, "labeler": "B"}})


def test_report_adverse_agreement_and_disagreements(record, valid):
    records = [{**record, "lineage_id": str(i)} for i in range(3)]
    good, _ = labels.validate_label(record, valid)
    bad, _ = labels.validate_label(record, {**valid, "q2": "khong", "q2_reason": "cosmetic_only"})
    a = {str(i): {**(bad if i < 2 else good), "labeler": "A", "guideline_version": "4.0",
                  "worksheet_sha256": labels.worksheet_sha256(records[i])} for i in range(3)}
    b = {str(i): {**(bad if i == 0 else good), "labeler": "B", "guideline_version": "4.0",
                  "worksheet_sha256": labels.worksheet_sha256(records[i])} for i in range(3)}
    report = labels.agreement_report(records, a, b)
    assert report["metrics"]["q2"]["p_neg"] == pytest.approx(2 / 3)
    assert report["metrics"]["verdict"]["p_neg"] == pytest.approx(2 / 3)
    assert report["disagreements"] == ["1"]
    assert labels.agreement_report(records, a, b, limit=1)["paired"] == 1


def test_worksheet_rejects_duplicates_and_missing_question(tmp_path, record):
    f = tmp_path / "worksheet.jsonl"
    f.write_text(json.dumps(record) + "\n" + json.dumps(record), encoding="utf-8")
    with pytest.raises(ValueError, match="trùng"):
        labels.load_worksheet(f)
    f.write_text(json.dumps({**record, "question": None}), encoding="utf-8")
    with pytest.raises(ValueError, match="thiếu"):
        labels.load_worksheet(f)


def test_changed_question_rejects_stale_labels_on_read_save_and_report(tmp_path, record, valid):
    path = tmp_path / "test2_A.tsv"
    assert not labels.save_label(path, [record], "A", record["lineage_id"], valid)["errors"]
    changed = {**record, "question": "Cơ quan nào được phép tiếp nhận hồ sơ?"}
    with pytest.raises(ValueError, match="không khớp"):
        labels.state([changed], path, "A")
    result = labels.save_label(path, [changed], "A", changed["lineage_id"], valid)
    assert "không khớp" in " ".join(result["errors"])
    own = labels.read_labels(path)
    with pytest.raises(ValueError, match="không khớp"):
        labels.agreement_report([changed], own, {})
    assert own[record["lineage_id"]]["worksheet_sha256"] == labels.worksheet_sha256(record)

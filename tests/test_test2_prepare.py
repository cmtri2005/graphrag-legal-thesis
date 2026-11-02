import json
import sqlite3

import pytest

from test2_prepare import contrast_audit, contrast_problems, inputs, jsonl, shortpack, worksheet, write_new


def fixture(tmp_path):
    data = tmp_path / "data"
    pub = data / "vilextime_dataset"
    pub.mkdir(parents=True)
    with sqlite3.connect(data / "temporal.sqlite") as db:
        db.execute("CREATE TABLE documents (id TEXT, number TEXT, title TEXT, issued_on TEXT, source_url TEXT)")
        db.execute("INSERT INTO documents VALUES ('actor','VB1','Văn bản tác động','2020-01-01','https://example.org/actor')")
    write_new(pub / "vilextime.jsonl", [{"id": "old", "lineage_id": "old", "split": "dev"}])
    write_new(pub / "vilextime_meta.jsonl", [{"id": "old", "target": {"document_id": "dev-doc"}}])
    groups = data / "derived/vilextime"
    groups.mkdir(parents=True)
    rows = [{"id": f"r{n}", "lineage_id": "new", "group": "T2", "as_of": f"2020-01-0{n}",
             "answer": f"Phí đăng ký là {fee} nghìn đồng.", "answerable": True, "version_id": f"v{n}",
             "target": {"document_id": "new-doc", "document_title": "Phí đăng ký", "lead_in": ""},
             "review": {"verdict": "dat", "labeler": "old-model"}}
            for n, fee in [(1, 30), (2, 40)]]
    write_new(groups / "T2.jsonl", rows)
    for g in ["T3", "T6"]:
        write_new(groups / f"{g}.jsonl", [])
    questions = tmp_path / "questions.jsonl"
    write_new(questions, [{"lineage_id": "new", "group": "T2",
                          "question": "Một công ty cần trả bao nhiêu tiền khi xin làm thủ tục này?",
                          "provider": "fixture", "model": "fixture-model", "prompt_sha": "abc"}])
    shorts = tmp_path / "shorts.jsonl"
    write_new(shorts, [{"lineage_id": "new", "version_id": f"v{n}", "short_answer": f"{fee} nghìn đồng",
                       "by": "fixture-model", "at": "2026-11-02"} for n, fee in [(1, 30), (2, 40)]])
    evidence = tmp_path / "evidence.jsonl"
    write_new(evidence, [{"id": r["id"], "base": {"passage": "Văn bản gốc"},
                          "actors": [{"document": "VB1", "passage": "Sửa mức phí"}], "missing": []} for r in rows])
    return data, questions, shorts, evidence


def test_shortpack_uses_new_question_and_every_version_without_old_labels(tmp_path):
    data, questions, _, _ = fixture(tmp_path)
    out = tmp_path / "shortpack"
    assert shortpack(data, questions, out) == {"questions": 1, "versions": 2}
    tasks = jsonl(out / "tasks.jsonl")
    assert [v["version_id"] for v in tasks[0]["versions"]] == ["v1", "v2"]
    assert tasks[0]["question"] == jsonl(questions)[0]["question"]
    assert "old-model" not in (out / "tasks.jsonl").read_text()
    with pytest.raises(FileExistsError):
        shortpack(data, questions, out)


def test_worksheet_keeps_all_dates_and_provenance_but_no_old_labels(tmp_path):
    data, questions, shorts, evidence = fixture(tmp_path)
    before = (data / "vilextime_dataset/vilextime.jsonl").read_bytes()
    out = tmp_path / "worksheet.jsonl"
    report = worksheet(data, questions, [shorts], [evidence], out)
    assert report["questions"] == 1 and report["boundary_rows"] == 2
    assert report["status"] == "unlabelled_candidates"
    rows = jsonl(out)[0]["rows"]
    assert [r["short_answer"] for r in rows] == ["30 nghìn đồng", "40 nghìn đồng"]
    assert all("review" not in r for r in rows)
    assert all(r["question_source"]["model"] == "fixture-model" for r in rows)
    assert jsonl(out)[0]["sources"]["actors"][0]["source_url"] == "https://example.org/actor"
    assert (data / "vilextime_dataset/vilextime.jsonl").read_bytes() == before
    with pytest.raises(FileExistsError, match="giữ nguyên phiếu"):
        worksheet(data, questions, [shorts], [evidence], out)


def test_worksheet_refuses_missing_or_nonextractive_short_answer_and_missing_sources(tmp_path):
    data, questions, shorts, evidence = fixture(tmp_path)
    with pytest.raises(ValueError, match="thiếu đáp án ngắn có nguồn"):
        worksheet(data, questions, [], [evidence], tmp_path / "missing.jsonl")
    rows = jsonl(shorts)
    rows[0]["short_answer"] = "999 triệu đồng"
    shorts.write_text("".join(json.dumps(r) + "\n" for r in rows))
    with pytest.raises(ValueError, match="không là trích đoạn"):
        worksheet(data, questions, [shorts], [evidence], tmp_path / "bad.jsonl")
    assert not (tmp_path / "bad.jsonl").exists()
    rows[0]["short_answer"] = "30 nghìn đồng"
    shorts.write_text("".join(json.dumps(r) + "\n" for r in rows))
    with pytest.raises(ValueError, match="thiếu trích văn bản gốc/tác động"):
        worksheet(data, questions, [shorts], [], tmp_path / "no-source.jsonl")


def test_worksheet_refuses_actor_link_that_cannot_be_resolved(tmp_path):
    data, questions, shorts, evidence = fixture(tmp_path)
    rows = jsonl(evidence)
    rows[0]["actors"][0]["document"] = "unknown-document"
    evidence.write_text("".join(json.dumps(r) + "\n" for r in rows))
    with pytest.raises(ValueError, match="chưa xác định duy nhất link văn bản tác động.*bổ sung source_url"):
        worksheet(data, questions, [shorts], [evidence], tmp_path / "bad-link.jsonl")
    assert not (tmp_path / "bad-link.jsonl").exists()


def test_prepare_refuses_t1_dev_document_in_test2(tmp_path):
    data, questions, _, _ = fixture(tmp_path)
    group = data / "derived/vilextime/T2.jsonl"
    rows = jsonl(group)
    for r in rows:
        r["target"]["document_id"] = "dev-doc"
    group.write_text("".join(json.dumps(r) + "\n" for r in rows))
    with pytest.raises(ValueError, match="văn bản dev.*không cho vào test2"):
        inputs(data, questions)


def test_prepared_worksheet_is_accepted_by_annotation_ui_without_existing_labels(tmp_path):
    from test2_labels import load_worksheet

    data, questions, shorts, evidence = fixture(tmp_path)
    out = tmp_path / "worksheet.jsonl"
    worksheet(data, questions, [shorts], [evidence], out)
    loaded = load_worksheet(out)
    assert len(loaded) == 1


def test_t2_contrast_rejects_shared_span_even_when_each_short_is_extractive(tmp_path):
    data, questions, shorts, evidence = fixture(tmp_path)
    values = jsonl(shorts)
    values[0]["short_answer"] = "nghìn đồng"
    shorts.write_text("".join(json.dumps(r) + "\n" for r in values))
    out = tmp_path / "worksheet.jsonl"
    with pytest.raises(ValueError, match="đáp án ngắn cũng nằm trong.*định nghĩa §4 T2"):
        worksheet(data, questions, [shorts], [evidence], out)
    assert not out.exists()
    report = contrast_audit(data, questions, [shorts], tmp_path / "audit.json")
    assert report["needs_review"] == 1 and report["without_detected_problem"] == 0


def test_t3_requires_three_distinct_short_answers_without_claiming_semantic_validation():
    rows = [{"lineage_id": "p", "version_id": f"v{i}", "answerable": True,
             "answer": f"Mức {i} đồng; thủ tục chung.", "target": {"lead_in": ""}} for i in (1, 2, 3)]
    shorts = {("p", f"v{i}"): {"short_answer": f"{i} đồng"} for i in (1, 2, 3)}
    assert contrast_problems("T3", rows, shorts) == []
    assert any("đúng 2 đáp án ngắn khác nhau" in p for p in contrast_problems("T2", rows, shorts))
    shorts[("p", "v2")]["short_answer"] = "thủ tục chung"
    shorts[("p", "v3")]["short_answer"] = "thủ tục chung"
    assert any("ít nhất 3 đáp án ngắn khác nhau" in p for p in contrast_problems("T3", rows, shorts))

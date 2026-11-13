import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts" / "eval"))
from posthoc_g4 import bucket, call, gold_rank, repeal_claims, writer  # noqa: E402


def test_call_reads_the_interval_not_the_estimate():
    assert call({"ci95": [0.01, 0.2]}) == "+"
    assert call({"ci95": [-0.2, -0.01]}) == "-"
    assert call({"ci95": [-0.01, 0.2]}) == "0"
    assert call({"ci95": [0.0, 0.2]}) == "0"      # chạm 0 chưa phải loại 0


def test_gold_rank_and_bucket():
    row = {"accepted_evidence": ["asis:provision:p"], "version_id": "version:p:2"}
    assert gold_rank(row, {"retrieved": ["x", "version:p:2"]}) == 2
    assert gold_rank(row, {"retrieved": ["version:p:1", "asis:provision:p"]}) == 2   # bản 1 không phải gold
    assert gold_rank(row, {"retrieved": ["x"]}) is None
    assert gold_rank({"accepted_evidence": ["asis:event:e"], "version_id": None}, {"retrieved": [None, "asis:event:e"]}) == 2
    assert [bucket(k) for k in (None, 1, 5, 6, 10, 11, 20, 21)] == ["không có", "1", "2-5", "6-10", "6-10", "11-20", "11-20", ">20"]


def test_repeal_claims_counts_true_and_false_claims():
    rows = [
        {"id": "a", "answerable": False, "accepted_evidence": ["asis:event:e"], "version_id": None},
        {"id": "b", "answerable": False, "accepted_evidence": ["asis:event:f"], "version_id": None},
        {"id": "c", "answerable": True, "accepted_evidence": [], "version_id": "version:p:1", "short_answer": "x"},
    ]
    preds = {"a": {"answerable": False, "retrieved": ["asis:event:e"]},      # đúng, lệnh có trong prompt
             "b": {"answerable": True, "answer": "y", "retrieved": ["z"]},   # bỏ sót, lệnh không có
             "c": {"answerable": False, "retrieved": []}}                    # khẳng định sai
    got = repeal_claims(rows, preds)
    assert (got["claims"], got["true"], got["false"]) == (2, 1, 1)
    assert got["precision"] == 0.5 and got["recall"] == 0.5
    assert (got["repeal_in_prompt"], got["correct_given_in_prompt"], got["correct_given_absent"]) == (1, 1, 0)


def test_writer_family():
    assert writer({"question_source": {"model": "gpt-6.1-sol (cấu hình Codex)"}}) == "codex"
    assert writer({"question_source": {"model": "claude-opus-5-5"}}) == "claude"
    assert writer({"question_source": {"model": "deepseek-flash"}}) == "deepseek"
    assert writer({}) == "?"

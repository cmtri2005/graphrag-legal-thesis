"""Sending a rejected question back with its reason, instead of losing the lineage."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts" / "pipeline"))
from generate_questions import RETRY_HINTS, retry_message, validate  # noqa: E402


def test_a_decline_is_never_retried():
    # base.md tells the model to print KHONG_DU_NGU_CANH for a bare list item, and
    # 123 of 129 declines measured on 05/10 already had every bit of context there
    # is, so asking again only argues with a correct judgement.
    assert retry_message("input", "KHONG_DU_NGU_CANH", "insufficient_context") is None
    assert "insufficient_context" not in RETRY_HINTS


def test_a_mechanical_rejection_goes_back_with_the_reason_and_the_text():
    again = retry_message("ĐÁP ÁN: x", "Khoản 1 Điều 3 quy định gì?", "cites_a_provision")
    assert again is not None
    assert "ĐÁP ÁN: x" in again, "the original input must still be there"
    assert "Khoản 1 Điều 3 quy định gì?" in again, "the model has to see what it wrote"
    assert RETRY_HINTS["cites_a_provision"] in again


def test_every_reason_validate_can_return_is_either_retriable_or_a_decline():
    # a reason with no hint and no decision is a silent dead end
    reasons = {
        "not_one_line": ("a\nb", "", "x"),
        "not_a_question": ("Quy định nội dung gì", "", "x"),
        "conversational_filler": ("Cho em hỏi quy định thế nào về việc này ạ?", "", "x"),
        "presumes_the_present": ("Pháp luật hiện hành quy định thế nào về việc này?", "", "x"),
        "cites_a_provision": ("Khoản 1 Điều 3 quy định nội dung gì về việc này?", "", "x"),
        "mentions_a_date": ("Năm 2016 quy định thế nào về trình tự thủ tục này?", "", "x"),
        "too_short": ("Sao vậy?", "", "x"),
    }
    for expected, (question, context, answer) in reasons.items():
        got = validate(question, context, answer)
        assert got is not None and got.split(":")[0] == expected, (question, got, expected)
        assert retry_message("in", question, got) is not None, f"{expected} has no hint"


def test_an_unsourced_number_is_retriable_by_its_prefix():
    got = validate("Mức phạt 99 triệu đồng áp dụng cho hành vi nào trong lĩnh vực này?", "", "x")
    assert got.startswith("unsourced_number:"), got
    assert retry_message("in", "q", got) is not None, "the prefix must still find the hint"

"""The judge's parse and its rule path — no model is called."""
from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location(
    "judge", Path(__file__).resolve().parents[1] / "scripts/eval/judge_vilextime.py")
judge = importlib.util.module_from_spec(spec)
spec.loader.exec_module(judge)


@pytest.mark.parametrize("raw,expected", [
    ("ĐÚNG: có\nRÀO ĐÓN: không", (True, False)),
    ("ĐÚNG: không\nRÀO ĐÓN: không", (False, False)),
    ("ĐÚNG: có\nRÀO ĐÓN: có", (False, True)),     # a hedged answer is never correct
    ("không rõ", (False, False)),                  # unreadable earns nothing
])
def test_parse(raw, expected) -> None:
    assert judge.parse(raw) == expected


class Boom:
    def get(self, _k): raise AssertionError("no model call expected")


def test_unanswerable_rows_use_the_scorer_rule_without_a_call() -> None:
    row = {"id": "r", "answerable": False}
    assert judge.judge_one(row, {"answerable": False}, Boom(), None, None)["correct"] is True
    assert judge.judge_one(row, {"answerable": True, "answer": "x"}, Boom(), None, None)["correct"] is False


def test_an_empty_prediction_is_wrong_without_a_call() -> None:
    row = {"id": "r", "answerable": True}
    assert judge.judge_one(row, {"answerable": True, "answer": " "}, Boom(), None, None)["correct"] is False

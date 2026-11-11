import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts" / "eval"))
from t6_breakdown import event_rank  # noqa: E402


def test_event_rank_present_and_absent():
    row = {"accepted_evidence": ["asis:event:x"]}
    assert event_rank(row, ["a", "b", "asis:event:x"]) == 3
    assert event_rank(row, ["a", "b"]) is None

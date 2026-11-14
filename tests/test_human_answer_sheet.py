import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts" / "review"))
from human_answer_sheet import agreement, kappa, wilson  # noqa: E402


def test_agreement_counts_and_wrong_version():
    labels = ["dung", "sai_noi_dung", "tu_choi_dung", "dung", "sai_phien_ban"]
    key = [{"stt": i, "system": s, "group": "T2", "scorer_accuracy": ok}
           for i, (s, ok) in enumerate([("b1", True), ("b1", False), ("b4", True), ("b4", False), ("proposed2", False)], 1)]
    out = agreement(labels, key, [False, True, None, False, True])
    assert (out["agree"], out["human_ok_scorer_wrong"], out["human_wrong_scorer_ok"]) == (4, 1, 0)
    assert out["disagreements"] == [{"stt": 4, "system": "b4", "group": "T2", "human": "dung", "scorer_accuracy": False}]
    assert out["per_system"]["b4"]["human_correct"] == 2 and out["per_system"]["b4"]["scorer_correct"] == 1
    assert out["wrong_version_vs_human"]["flagged"] == 2
    assert out["wrong_version_vs_human"]["flagged_human_sai_phien_ban"] == 1


def test_stats():
    assert kappa([(True, True), (False, False)]) == 1.0
    assert wilson(95, 100) == [0.8882, 0.9785]


def test_unknown_label_stops():
    import pytest
    with pytest.raises(SystemExit):
        agreement(["đúng"], [{"stt": 1, "system": "b1", "group": "T2", "scorer_accuracy": True}], [None])

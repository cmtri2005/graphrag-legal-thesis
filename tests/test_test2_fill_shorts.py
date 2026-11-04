import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts/review"))
from test2_fill_shorts import fill


def row(**kw):
    return {"id": "r", "lineage_id": "l", "version_id": "v", "answerable": True, "answer": "phạt tiền 5 triệu đồng",
            "short_answer": None, "target": {"lead_in": None}, **kw}


def test_fills_and_replaces():
    out, stats = fill([row(), row(short_answer="phạt tiền")], {("l", "v"): "5 triệu đồng"})
    assert [r["short_answer"] for r in out] == ["5 triệu đồng"] * 2
    assert stats == {"filled": 1, "replaced": 1}


@pytest.mark.parametrize("shorts", [{}, {("l", "v"): None}, {("l", "v"): "không có trong lời văn"}])
def test_answerable_row_needs_a_valid_short_answer(shorts):
    with pytest.raises(SystemExit):
        fill([row()], shorts)


def test_unanswerable_row_stays_empty():
    out, _ = fill([row(answerable=False, version_id=None)], {})
    assert out[0]["short_answer"] is None

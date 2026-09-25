"""E1 before-side check: text matching survives portal formatting."""
import sys
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts" / "check"))
from check_before_side import added_phrases, norm  # noqa: E402


def test_norm_ignores_unicode_form_markup_and_space_before_punctuation():
    raw = unicodedata.normalize("NFD", "<p>Nghị định số 108/2013/NĐ-CP ,&nbsp;thời hiệu</p>")
    assert norm(raw) == norm("Nghị định số 108/2013/NĐ-CP, thời hiệu")


def test_added_phrases_keeps_only_real_insertions():
    before = "phạt tiền đến 25.000.000 đồng trong lĩnh vực văn hóa"
    after = "phạt tiền đến 25.000.000 đồng đối với hành vi vi phạm trong lĩnh vực văn hóa"
    assert added_phrases(before, after) == ["đối với hành vi vi phạm"]
    assert added_phrases("a b c d", "a b c") == []

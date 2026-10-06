"""Cutting the source passages behind a D4 row."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts" / "review"))
from crosscheck_evidence import actor_passage, base_passage, lines  # noqa: E402


def test_base_passage_finds_the_clause_in_the_right_chapter():
    ls = lines("<p>Điều 5. Ban hành</p><p>Chương II</p><p>Điều 5. Hồ sơ</p><p>1. Một</p>"
               "<p>a) điểm</p><p>2. Hai</p><p>Điều 6. Khác</p>")
    got = base_passage(ls, {"article_id": "5", "clause_id": "1", "provision_path": "Chương II › Điều 5 › Khoản 1"})
    assert got == "Điều 5. Hồ sơ\n1. Một\na) điểm"


def test_actor_passage_keeps_the_items_of_a_numbered_instruction():
    ls = lines("<p>24. Sửa đổi, bổ sung Điều 33 như sau:</p><p>a) Sửa đổi khoản 13 Điều 33 như sau:</p>"
               "<p>“13. Mới.”</p><p>b) Sửa đổi khoản 14 Điều 33 như sau:</p><p>25. Bãi bỏ Điều 40.</p>")
    got = actor_passage(ls, "Sửa đổi, bổ sung Điều 33 như sau", "12/2017/TT-BGTVT", "33")
    assert got.splitlines()[-1] == "b) Sửa đổi khoản 14 Điều 33 như sau:"
    assert actor_passage(ls, "a) Sửa đổi khoản 13", "x", "33").splitlines()[-1] == "“13. Mới.”"


def test_actor_passage_does_not_take_article_60_for_article_6():
    ls = lines("<p>d) Sửa đổi điểm đ khoản 4 Điều 60 như sau:</p><p>b) Bãi bỏ điểm i khoản 2; điểm đ khoản 4 Điều 6;</p>")
    assert actor_passage(ls, "điểm đ khoản 4 Điều 6", "100/2019/NĐ-CP", "6") == "b) Bãi bỏ điểm i khoản 2; điểm đ khoản 4 Điều 6;"

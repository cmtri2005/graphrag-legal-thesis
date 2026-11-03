import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts/review"))
from test2_colab import parse_filter, parse_question


def test_parse_filter():
    assert parse_filter("giu\t\tcăn cứ\tghi") == ("giu", "", "căn cứ", "ghi")
    assert parse_filter("loai\tother\tx\tlý do")[1] == "other"
    assert parse_filter("loai\tbịa\tx\tlý do") is None      # mã lạ
    assert parse_filter("loai\tother\tx\t") is None         # loại phải có ghi chú
    assert parse_filter("giu\tother\tx\ty") is None         # giữ không có mã
    assert parse_filter("không có tab") is None


def test_parse_question():
    assert parse_question('Câu hỏi: "Hồ sơ gồm gì?"'.replace('"', "")) == "Hồ sơ gồm gì?"
    assert parse_question("KHONG_DU_NGU_CANH") == "KHONG_DU_NGU_CANH"
    assert parse_question("Hai dòng?\nthêm") is None
    assert parse_question("không phải câu hỏi") is None

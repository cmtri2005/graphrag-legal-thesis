"""Closing-article pick must skip articles quoted inside an amending document."""
from official_text import closing_articles


def test_last_in_force_article_wins_over_quoted_one():
    text = ("Điều 1. Sửa đổi\n1. Sửa Điều 3 như sau:\nĐiều 3. Hiệu lực của quy chế cũ\nQuy chế có hiệu lực từ năm 2010.\n"
            "Điều 2. Điều khoản chuyển tiếp\nHồ sơ đã nộp giữ nguyên.\nĐiều 3. Hiệu lực thi hành\n"
            "Nghị định này có hiệu lực từ ngày 01 tháng 01 năm 2022.")
    got = closing_articles(text)
    assert "01 tháng 01 năm 2022" in got and "năm 2010" not in got and "Hồ sơ đã nộp" in got

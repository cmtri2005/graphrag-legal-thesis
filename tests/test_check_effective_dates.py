"""In-force clause parsing used to catch worksheet effective_from errors."""
from check_effective_dates import clause_date


def test_clause_shapes():
    assert clause_date("1. Thông tư này có hiệu lực kể từ ngày 15 tháng 02 năm 2023.", "2022-12-30") == ("2023-02-15", "date")
    assert clause_date("Nghị định này có hiệu lực thi hành sau 15 ngày, kể từ ngày ký.", "2002-02-08") == ("2002-02-23", "signed+15")
    assert clause_date("Thông tư này có hiệu lực sau 45 ngày kể từ ngày ban hành.", "2020-06-10") == ("2020-07-25", "signed+45")
    assert clause_date("có hiệu lực thi hành kể từ ngày ký ban hành, trừ trường hợp quy định tại khoản 2", "2026-03-31") == ("2026-03-31", "signed+except")
    assert clause_date("Nghị định này có hiệu lực từ năm ngân sách 1999.", None) == ("1999-01-01", "budget_year")
    assert clause_date("có hiệu lực thi hành sau 15 ngày, kể từ ngày đăng Công báo.", "2008-01-11") == (None, "unparsed")

import pytest

from legal_crawler.vocab.status_codes import (
    StatusCodeMap,
    UnknownStatusCodeError,
    is_legal_date,
    parse_transition,
)


def test_base_codes_carry_the_api_s_own_labels():
    m = StatusCodeMap.load()
    assert m.classify("CHL").label_vi == "Còn hiệu lực"
    assert m.classify("HHL").label_vi == "Hết hiệu lực toàn bộ"
    assert m.classify("HHL1P").label_vi == "Hết hiệu lực một phần"


def test_suffixed_codes_collapse_to_their_verified_prefix():
    # The digit's meaning is unresolved and the source's own UI never renders
    # it, so every HHL1P* means "partly expired" and nothing more.
    m = StatusCodeMap.load()
    effects = {m.classify(c).effect for c in ("HHL1P", "HHL1P1", "HHL1P2", "HHL1P3", "HHL1P4")}
    assert effects == {"expired_partial"}


def test_dates_and_statuses_are_distinguishable():
    m = StatusCodeMap.load()
    assert m.classify("DATE_HL").kind == "date"
    assert m.classify("CHL").kind == "status"


def test_unknown_code_raises_instead_of_defaulting():
    with pytest.raises(UnknownStatusCodeError):
        StatusCodeMap.load().classify("HHL1P9")


def test_free_text_rows_are_parsed_not_treated_as_codes():
    # These rows are how several codes got corroborated: the same transition
    # shows up written either way.
    assert parse_transition("Cập nhật trạng thái hiệu lực từ CHL sang HHL1P.") == ("CHL", "HHL1P")
    assert parse_transition(
        "Cập nhật trạng thái hiệu lực từ Hết hiệu lực một phần sang Còn hiệu lực."
    ) == ("Hết hiệu lực một phần", "Còn hiệu lực")
    assert parse_transition("CHL") is None


def test_only_job_rows_date_a_legal_event():
    # An Admin row's createdDate is when a clerk typed it — one 2006 law has a
    # DATE_BH row stamped 2025.
    assert is_legal_date({"createdBy": "Job", "createdDate": "2011-01-20T00:00:00"})
    assert not is_legal_date({"createdBy": "Admin", "createdDate": "2025-12-26T01:41:21"})
    assert not is_legal_date({"createdBy": "System Scheduler"})
    assert not is_legal_date({})


def test_job_dates_are_normalised_by_their_clock_time():
    from datetime import date

    from legal_crawler.vocab.status_codes import legal_date

    job = {"createdBy": "Job", "content": "DATE_HL"}
    # T00:00 rows are one day late; T07:00 rows are the date itself.
    assert legal_date({**job, "createdDate": "2020-01-02T00:00:00"}) == date(2020, 1, 1)
    assert legal_date({**job, "createdDate": "2016-12-01T07:00:00"}) == date(2016, 12, 1)
    # The offset belongs to the code: issue dates at midnight are not shifted.
    assert legal_date({**job, "content": "DATE_BH", "createdDate": "2019-12-30T00:00:00"}) == date(2019, 12, 30)
    # An unexplained clock time is not guessed at, and Admin rows are never dates.
    assert legal_date({**job, "createdDate": "2016-12-01T01:00:00"}) is None
    assert legal_date({**job, "content": "DATE_BH", "createdDate": "2019-12-30T07:00:00"}) is None
    assert legal_date({"createdBy": "Admin", "createdDate": "2026-01-10T00:00:00"}) is None


def test_anchor_problem_counts_an_empty_interval():
    from datetime import date

    from legal_crawler.vocab.status_codes import (
        EMPTY_INTERVAL, IN_FORCE_PAST_EFF_TO, NO_EFF_FROM, NO_STATUS,
        REPEALED_WITHOUT_EFF_TO, anchor_problem,
    )

    today = date(2026, 9, 12)
    in_force = {"name": "Còn hiệu lực"}
    repealed = {"name": "Hết hiệu lực toàn bộ"}
    assert anchor_problem({"effStatus": in_force}, today) == NO_EFF_FROM
    assert anchor_problem({"effFrom": "2020-01-01T00:00:00", "effStatus": repealed}, today) == REPEALED_WITHOUT_EFF_TO
    # [d, d) holds no day: equal dates are as broken as inverted ones.
    same = {"effFrom": "2015-08-01T00:00:00", "effTo": "2015-08-01T00:00:00", "effStatus": repealed}
    assert anchor_problem(same, today) == EMPTY_INTERVAL
    assert anchor_problem({**same, "effTo": "2014-08-01T00:00:00"}, today) == EMPTY_INTERVAL
    assert anchor_problem({"effFrom": "2020-01-01T00:00:00"}, today) == NO_STATUS
    assert anchor_problem({"effFrom": "2020-01-01T00:00:00", "effTo": "2025-01-01T00:00:00",
                           "effStatus": in_force}, today) == IN_FORCE_PAST_EFF_TO
    assert anchor_problem({"effFrom": "2020-01-01T00:00:00", "effStatus": in_force}, today) is None

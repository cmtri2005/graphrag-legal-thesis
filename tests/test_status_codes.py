import pytest

from legal_crawler.status_codes import (
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

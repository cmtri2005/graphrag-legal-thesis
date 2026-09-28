"""The release file: mid-interval twins and the schema 1.1 fields (plan phase-4, 28/09)."""
from datetime import date

from enrich_vilextime import MARGIN, changed_span, check_short_answer, mid_date, references, twin_of
from legal_crawler.temporal.models import ProvisionLevel as L

VERSIONS = [
    {"id": "version:p:1", "ordinal": 1, "text": "Bộ Tài nguyên và Môi trường cấp phép.",
     "effective_from": "2020-01-01", "effective_to": "2025-03-01"},
    {"id": "version:p:2", "ordinal": 2, "text": "Bộ Nông nghiệp và Môi trường cấp phép.",
     "effective_from": "2025-03-01", "effective_to": None},
]


def _row(as_of, version_id, **extra):
    return {"id": f"vilextime:T4:provision:p:{as_of}", "lineage_id": "provision:p", "as_of": as_of,
            "version_id": version_id, "derivation": {"transitions": [], "query": ""}, **extra}


def test_a_mid_interval_date_keeps_its_distance_and_is_reproducible():
    start, end = date(2020, 1, 1), date(2025, 3, 1)
    at = mid_date(start, end, "k")
    assert (at - start).days >= MARGIN and (end - at).days > MARGIN
    assert at == mid_date(start, end, "k") != mid_date(start, end, "another key")
    assert mid_date(date(2026, 1, 1), date(2026, 1, 21), "k") == date(2026, 1, 11)   # short: midpoint
    assert mid_date(date(2027, 1, 1), None, "k") is None                               # opens after the snapshot


def test_the_twin_keeps_the_gold_version_and_says_whose_twin_it_is():
    before = _row("2025-02-28", "version:p:1")
    twin = twin_of(before, VERSIONS, None)
    assert twin["version_id"] == "version:p:1" and twin["twin_of"] == before["id"]
    assert date(2020, 1, 31) <= date.fromisoformat(twin["as_of"]) < date(2025, 1, 30)
    assert twin["id"].endswith(twin["as_of"]) and twin["as_of_strategy"] == "giua_khoang"


def test_a_twin_the_chain_disagrees_with_is_not_made():
    # Version 1 never closed, so inside version 2's window the chain answers version 1.
    overlapping = [dict(VERSIONS[0], effective_to=None), VERSIONS[1]]
    assert twin_of(_row("2025-03-01", "version:p:2"), overlapping, None) is None
    assert twin_of(_row("2025-03-01", "version:p:2"), VERSIONS, None)["version_id"] == "version:p:2"


def test_retroactive_and_repealed_twins_stay_in_their_windows():
    retro = _row("2025-03-01", "version:p:2", retroactive={"effective_from": "2025-03-01", "issued_on": "2025-03-20"})
    twin = twin_of(retro, VERSIONS, None)
    assert date(2025, 3, 1) <= date.fromisoformat(twin["as_of"]) < date(2025, 3, 20)
    repealed = [dict(VERSIONS[0], effective_to="2024-01-01")]
    gone = twin_of(_row("2024-01-01", None), repealed, date(2026, 1, 1))
    assert gone["version_id"] is None and date(2024, 1, 1) <= date.fromisoformat(gone["as_of"]) < date(2026, 1, 1)


def test_changed_span_is_what_this_version_says_and_its_neighbour_does_not():
    texts = [v["text"] for v in VERSIONS]
    assert changed_span(texts, 0) == "Tài nguyên"
    assert changed_span(texts, 1) == "Nông nghiệp"
    assert changed_span(texts[:1], 0) is None


def test_references_fill_the_relative_parts_and_skip_other_documents():
    target = {"article_id": "17", "clause_id": "5", "point_id": "b"}
    assert references("đối với hành vi vi phạm quy định tại Khoản 3 Điều này.", target) == [
        {L.ARTICLE: "17", L.CLAUSE: "3"}]
    assert references("theo quy định tại điểm a, d khoản này", target) == [
        {L.ARTICLE: "17", L.CLAUSE: "5", L.POINT: "a"}, {L.ARTICLE: "17", L.CLAUSE: "5", L.POINT: "d"}]
    assert references("không được quy định tại Điều 4; khoản 1 Điều 7 Thông tư này.", target) == [
        {L.ARTICLE: "4"}, {L.ARTICLE: "7", L.CLAUSE: "1"}]
    assert references("có đủ điều kiện quy định tại Điều 9 Nghị định số 18/2015/NĐ-CP.", target) == []
    assert references("Điểm b khoản 5 Điều này", {"article_id": "17", "clause_id": None, "point_id": None}) == [
        {L.ARTICLE: "17", L.CLAUSE: "5", L.POINT: "b"}]


def test_a_short_answer_must_be_a_span_of_the_answer_or_the_lead_in():
    answer, lead = "đ) Từ 15.000.000 đồng đến 20.000.000 đồng, khi vi phạm", "3. Phạt tiền đối với hành vi:"
    assert check_short_answer("từ 15.000.000 đồng đến 20.000.000 đồng", answer, lead)
    assert check_short_answer("phạt tiền", answer, lead)
    assert not check_short_answer("30.000.000 đồng", answer, lead)
    assert check_short_answer("phạt tiền … từ 15.000.000 đồng", answer, lead)       # two spans
    assert not check_short_answer("iền đối", answer, lead)                            # whole words only
    assert not check_short_answer("vi phạm 3 phạt tiền", answer, lead)                # never across the two

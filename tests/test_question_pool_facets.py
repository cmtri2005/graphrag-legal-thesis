"""The pool's difficulty covariates, and the dates a one-version lineage is asked at."""
import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts" / "pipeline"))
from build_question_pool import (  # noqa: E402
    MARGIN, SNAPSHOT, ask_dates, facets_of, pending_version, spread_as_of, why_no_answer,
)


def version(ordinal, effective_from, effective_to=None, created_by=None, text="x"):
    return {"id": f"v{ordinal}", "ordinal": ordinal, "text": text, "valid_to": None,
            "effective_from": effective_from, "effective_to": effective_to,
            "created_by_event_id": created_by, "ended_by_event_id": None, "provision_id": "p"}


def test_similarity_is_written_for_a_pair_and_a_list_for_a_chain():
    pair = facets_of([version(1, "2020-01-01", text="a b c"), version(2, "2021-01-01", text="a b d")])
    assert pair["n_versions"] == 2 and pair["similarity"] == pair["similarities"][0]

    chain = facets_of([version(1, "2020-01-01", text="a"), version(2, "2021-01-01", text="b"),
                       version(3, "2022-01-01", text="c")])
    assert chain["similarity"] is None, "only a two-version chain has one ratio"
    assert len(chain["similarities"]) == 2


def test_a_transition_that_only_changes_case_or_punctuation_is_not_substantive():
    # the 2025 agency renames and "hành." -> "hành;" are 18.4% of T3's transitions
    cosmetic = facets_of([version(1, "2020-01-01", text="Trung ương."),
                          version(2, "2021-01-01", text="trung ương;")])
    assert cosmetic["substantive_transitions"] == 0

    real = facets_of([version(1, "2020-01-01", text="năm triệu đồng"),
                      version(2, "2021-01-01", text="mười triệu đồng"),
                      version(3, "2022-01-01", text="hai mươi triệu đồng")])
    assert real["substantive_transitions"] == 2, "R2 needs two changes that carry a question"


def test_the_one_version_as_of_is_spread_but_stays_a_boundary_row():
    start = date(2020, 1, 1)
    asked = {spread_as_of(f"provision:{i}", start, date(2029, 12, 31)) for i in range(200)}
    assert len(asked) > 10, "every lineage asked on the same offset leaks through the margin"
    assert all(start < day <= start + timedelta(days=MARGIN) for day in asked), (
        "past MARGIN it would collide with the mid-interval twin enrich builds")


def test_the_spread_is_seeded_so_a_rebuild_reproduces_it():
    args = ("provision:abc", date(2020, 1, 1), date(2029, 12, 31))
    assert spread_as_of(*args) == spread_as_of(*args)
    assert spread_as_of("p", date(2020, 1, 1), date(2020, 1, 1)) == date(2020, 1, 1)


def test_a_one_version_row_is_never_asked_after_the_corpus_snapshot():
    (asked,) = ask_dates("T1", [version(1, "2026-09-10")], date(2026, 9, 20), "p", None)
    assert asked <= SNAPSHOT


def test_a_one_version_row_stops_at_the_document_end_not_only_the_version_end():
    # effective_to null inside a document that already ended is JUDGE C1's gap
    (asked,) = ask_dates("T1", [version(1, "2020-01-01")], date(2026, 9, 20), "p", date(2020, 1, 10))
    assert date(2020, 1, 1) < asked <= date(2020, 1, 9)


def test_pending_names_a_version_already_signed_but_not_yet_in_force():
    versions = [version(1, "2020-01-01", "2026-01-01"),
                version(2, "2026-01-01", created_by="event:9:aa")]
    signed_early = {"document:9": "2025-03-01"}

    got = pending_version(versions, date(2025, 6, 1), signed_early)
    assert got["actor_document_id"] == "document:9" and got["days_until_effect"] == 214

    assert pending_version(versions, date(2025, 6, 1), {"document:9": "2025-12-01"}) is None, (
        "not signed yet at as_of, so nothing points at the wrong answer")
    assert pending_version(versions, date(2026, 6, 1), signed_early) is None, "already in force"


def test_the_two_kinds_of_missing_answer_are_told_apart():
    versions = [version(1, "2020-01-01", "2021-01-01")]
    assert why_no_answer(versions, date(2019, 1, 1)) == "not_yet_in_force"
    assert why_no_answer(versions, date(2022, 1, 1)) == "provision_repealed"


def test_a_one_version_row_is_not_always_asked_the_day_after_its_version_opens():
    """JUDGE N3's leak, the marginal kind: fix T3's and T1 keeps it.

    Asking every one-version lineage at start + 1 teaches the release that
    `as_of - 1` is a version boundary, which a system can then apply to the groups
    that do have a choice without reading anything — the probe scored 1.000 on
    every T1 row. The guard is on the spread, not on any single date.
    """
    start, after = date(2020, 1, 1), date(2020, 1, 2)
    asked = {ask_dates("T1", [version(1, start.isoformat())], date(2026, 9, 20), f"p{i}", None)[0]
             for i in range(40)}

    assert len(asked) > 1, "mọi lineage T1 vẫn bị hỏi ở cùng một khoảng cách so với mốc bắt đầu"
    assert asked != {after}
    assert all(start < at <= start + timedelta(days=MARGIN) for at in asked)


def test_chance_accuracy_separates_a_pair_from_a_three_step_chain():
    """Why T2's 0.500 and T3's 0.325 were never comparable: the chance level differs."""
    pair = facets_of([version(1, "2020-01-01"), version(2, "2021-01-01")])
    chain = facets_of([version(1, "2020-01-01"), version(2, "2021-01-01"), version(3, "2022-01-01")])

    assert pair["chance_accuracy"] == 0.5
    assert chain["chance_accuracy"] == round(1 / 3, 4)


def test_near_identical_keeps_the_old_T4_cut_as_a_facet():
    same = facets_of([version(1, "2020-01-01", text="a b c d e"), version(2, "2021-01-01", text="a b c d e")])
    differs = facets_of([version(1, "2020-01-01", text="a b c"), version(2, "2021-01-01", text="x y z")])

    assert same["near_identical"] is True and differs["near_identical"] is False


def test_r1_tells_a_rename_or_a_reformat_from_a_change_of_content():
    """docs/vilextime-dinh-nghia.md R1; the cases are the D4 rows checked on 19–20/10."""
    from build_question_pool import transition_kind

    # TT 52/2022/TT-BGTVT k2 Đ4, rewritten by k1 Đ29 TT 09/2025/TT-BXD
    assert transition_kind("do Bộ trưởng Bộ Giao thông vận tải ban hành.",
                           "do Bộ trưởng Bộ Xây dựng ban hành.") == "rename_only"
    assert transition_kind("Ngân hàng Nhà nước chi nhánh", "Ngân hàng Nhà nước Khu vực") == "rename_only"
    assert transition_kind("Trung ương hoá.", "trung ương hóa;") == "cosmetic_only"
    # NĐ 355/2025 điểm n k1 Đ30, by k5 Đ43 NĐ 170/2026: a number is content
    assert transition_kind("n) 800 ml dầu gội đầu/năm;", "n) 1000 ml dầu gội đầu/năm;") == "substantive"
    # a rename plus a real change is a real change
    assert transition_kind("Bộ Giao thông vận tải cấp trong 05 ngày",
                           "Bộ Xây dựng cấp trong 03 ngày") == "substantive"
    # TT 84/2018/TT-BTC k2 Đ3: only the cited act changed, and the circular applies successors itself
    before = "thực hiện theo Thông tư 74/2018/TT-BTC ngày 16/8/2018 hướng dẫn chế độ kế toán"
    after = "thực hiện theo Thông tư số 99/2021/TT-BTC ngày 15 tháng 11 năm 2021 hướng dẫn chế độ kế toán"
    assert transition_kind(before, after, auto_update=True) == "auto_reference_update"
    assert transition_kind(before, after, auto_update=False) == "substantive"


def test_r1_groups_count_legal_states_not_versions():
    from build_question_pool import classify, legal_states

    chain = [version(1, "2020-01-01", text="Bộ Giao thông vận tải cấp trong 05 ngày"),
             version(2, "2022-01-01", text="Bộ Giao thông vận tải cấp trong 03 ngày"),
             version(3, "2025-07-01", text="Bộ Xây dựng cấp trong 03 ngày")]
    assert legal_states(chain) == [0, 1]
    assert classify(chain, None, "Clause", date(2026, 9, 20), states=legal_states(chain)) == "T2"
    # asked around the real change, never around the rename
    assert ask_dates("T2", chain, date(2026, 9, 20), "p", None, legal_states(chain)) == \
        [date(2021, 12, 31), date(2022, 1, 1)]
    only_renamed = chain[1:]
    assert classify(only_renamed, None, "Clause", date(2026, 9, 20), states=legal_states(only_renamed)) is None


def test_r1_finds_the_clause_that_applies_a_replaced_act():
    from build_question_pool import _AUTO_UPDATE

    # k3 Đ7 TT 84/2018/TT-BTC and k2 Đ27 TT 241/2017/TT-BQP, verbatim
    assert _AUTO_UPDATE.search("3. Trường hợp các văn bản quy phạm pháp luật trích dẫn tại Thông tư này được sửa đổi, "
                               "bổ sung hoặc thay thế bằng văn bản quy phạm pháp luật khác thì áp dụng quy định tại "
                               "văn bản sửa đổi, bổ sung hoặc thay thế.")
    assert _AUTO_UPDATE.search("2. Trường hợp văn bản được dẫn chiếu trong Thông tư này được sửa đổi, bổ sung, thay thế "
                               "hoặc ban hành mới thì những nội dung liên quan đến Thông tư này cũng được thay đổi theo "
                               "các văn bản sửa đổi, bổ sung, thay thế hoặc ban hành mới đó.")
    assert not _AUTO_UPDATE.search("Thông tư này thay thế Thông tư số 74/2018/TT-BTC.")

"""The J2 validity detectors on hand-made rows and events."""
from check_validity import locator_fits, missed_events, reference_only, sentence_endings

TARGET = {"document_id": "document:D", "article_id": "24", "clause_id": "1", "point_id": "b"}


def _row(**kw):
    return {"id": "r", "lineage_id": "provision:b", "answerable": True, "valid_from": "2020-01-01",
            "as_of": "2025-08-30", "target": TARGET, "derivation": {"transitions": []}, **kw}


def _event(**kw):
    return {"id": "event:E", "operation": "amend", "effective_on": "2025-04-19", "target_document_id": "document:D",
            "candidate_document_ids": [], "target_provision_id": None, "affected_provision_ids": [], "locator": None, **kw}


def test_a_locator_fits_the_target_or_an_ancestor_only():
    assert locator_fits([["Article", "24"], ["Clause", "1"]], TARGET)
    assert locator_fits([["Clause", "1"]], TARGET)                    # ambiguous, still a candidate
    assert not locator_fits([["Article", "24"], ["Clause", "2"]], TARGET)
    assert not locator_fits([], TARGET)


def test_an_event_on_an_ancestor_inside_the_window_and_outside_the_chain_is_flagged():
    nodes = {"provision:b": {"provision:A24", "provision:K1", "provision:b"}}
    by_id = _event(target_provision_id="provision:K1")
    by_locator = _event(id="event:L", locator=[["Article", "24"], ["Clause", "1"]])
    sibling = _event(id="event:S", target_provision_id="provision:K2")
    too_late = _event(id="event:T", target_provision_id="provision:K1", effective_on="2025-09-01")
    supplement = _event(id="event:U", target_provision_id="provision:K1", operation="supplement")
    flagged = missed_events([_row()], [by_id, by_locator, sibling, too_late, supplement], nodes)
    assert [e["id"] for _, e in flagged] == ["event:E", "event:L"]
    in_chain = _row(derivation={"transitions": [{"event_id": "event:E"}]})
    assert [e["id"] for _, e in missed_events([in_chain], [by_id], nodes)] == []


def test_a_sentence_ends_the_whole_document_not_one_article():
    text = ("3. Nghị định số 176/2013/NĐ-CP ngày 14 tháng 11 năm 2013 của Chính phủ hết hiệu lực toàn bộ "
            "kể từ ngày 15 tháng 11 năm 2020. 4. Bãi bỏ Điều 5 Nghị định số 176/2013/NĐ-CP.")
    [(sentence, day)] = sentence_endings(text, "176/2013/NĐ-CP")
    assert "hết hiệu lực toàn bộ" in sentence and day == "2020-11-15"   # "kể từ ngày", not the issue date
    assert sentence_endings("Nghị định 176/2013/NĐ-CP hết hiệu lực.", "176/2013/NĐ-CP") == [
        ("Nghị định 176/2013/NĐ-CP hết hiệu lực.", None)]            # no date: the actor's effective_from
    assert sentence_endings("Thay thế cụm từ “Bộ” bằng “Cục” tại Nghị định 176/2013/NĐ-CP.", "176/2013/NĐ-CP") == []
    assert sentence_endings("Thông tư này thay thế Thông tư 81-CP.", "81/CP")


def test_a_partial_repeal_named_before_the_number_is_not_the_whole_document():
    assert sentence_endings("Các điều 5, 6, 7 của Nghị định số 176/2013/NĐ-CP hết hiệu lực.", "176/2013/NĐ-CP") == []
    assert sentence_endings("Bãi bỏ một số quy định của Nghị định số 78/2021/NĐ-CP.", "78/2021/NĐ-CP") == []


def test_an_appendix_or_a_word_is_not_the_document():
    assert sentence_endings("Thay thế Phụ lục II ban hành kèm theo Thông tư số 39/2019/TT-BGTVT bằng Phụ lục II.",
                            "39/2019/TT-BGTVT") == []
    assert sentence_endings("điều trị bằng thuốc thay thế theo quy định tại Nghị định 116/2021/NĐ-CP.",
                            "116/2021/NĐ-CP") == []
    assert sentence_endings("Nghị định này thay thế Nghị định số 87/CP ngày 23 tháng 11 năm 1993.", "87-CP")


def test_r4_names_a_reorganised_agency_or_province_only_after_its_date():
    from check_validity import restructured

    # TT 52/2022/TT-BGTVT k2 Đ4 before k1 Đ29 TT 09/2025/TT-BXD rewrote it (01/07/2025)
    text = "do Bộ trưởng Bộ Giao thông vận tải ban hành."
    assert restructured(text, "2025-02-28") is None
    assert restructured(text, "2025-05-01") == "bộ giao thông vận tải"
    assert restructured("Tổng cục Thuế hướng dẫn", "2025-04-01") == "tổng cục"
    assert restructured("Tổng cục Chính trị Quân đội nhân dân", "2025-04-01") is None
    # TT 03/2022/TT-BGTVT k2 Đ2: "vùng nước cảng biển ... tỉnh Bến Tre"
    assert restructured("vùng nước cảng biển Bến Tre", "2025-06-30") is None
    assert restructured("vùng nước cảng biển Bến Tre", "2025-07-01") == "bến tre"


def test_r5_an_answer_that_only_points_elsewhere():
    assert reference_only("a) Hồ sơ bao gồm: tài liệu quy định tại điểm a khoản 1 Điều này;")
    assert reference_only("đ) Áp dụng các biện pháp khắc phục hậu quả quy định tại các điểm a, b, d và e "
                          "khoản 3 Điều 4 của Nghị định này.")
    assert not reference_only("a) Hồ sơ bao gồm: tài liệu quy định tại điểm a khoản 1 Điều này và 01 ảnh màu "
                              "chân dung kích thước 3 cm x 4 cm. Ảnh chụp không quá 06 tháng kể từ ngày chụp;")
    assert not reference_only("Phạt tiền từ 2.000.000 đồng đến 4.000.000 đồng đối với hành vi không mang giấy phép.")

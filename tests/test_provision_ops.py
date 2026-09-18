from legal_crawler.extraction.provision_ops import (
    extract_mentions,
    normalize_number,
    parse_locators,
    title_document,
)
from legal_crawler.temporal.models import LegalOperation as Op
from legal_crawler.temporal.models import ProvisionLevel as L


def paths(mention):
    return [tuple((p.level.value, p.label) for p in loc.parts) for loc in mention.locators]


def summary(paragraphs, title_doc=None):
    return [
        (m.operation, normalize_number(m.document_number), paths(m), m.method)
        for m in extract_mentions(paragraphs, title_doc)
    ]


def test_locator_lists_paths_and_qualifiers():
    assert parse_locators("khoản 2 Điều 11") == [{L.CLAUSE: "2", L.ARTICLE: "11"}]
    assert parse_locators("điểm b khoản 1, khoản 2 Điều 5") == [
        {L.POINT: "b", L.CLAUSE: "1", L.ARTICLE: "5"}, {L.CLAUSE: "2", L.ARTICLE: "5"}]
    assert parse_locators("Điều 2, khoản 2 Điều 3, Điều 6") == [
        {L.ARTICLE: "2"}, {L.CLAUSE: "2", L.ARTICLE: "3"}, {L.ARTICLE: "6"}]
    # Mục/Chương right after an article list qualify it; a second Chương is its own item.
    assert parse_locators("Điều 20, 21 và 27 Mục 2 Chương IV, Chương V") == [
        {L.ARTICLE: "20"}, {L.ARTICLE: "21"}, {L.ARTICLE: "27"}, {L.CHAPTER: "V"}]
    # The portal's own comma-separated path style.
    assert parse_locators("Khoản 3, Điều 9, Mục 3, Chương II") == [{L.CLAUSE: "3", L.ARTICLE: "9"}]
    assert parse_locators("từ Điều 5 đến Điều 7") == [{L.ARTICLE: "5"}, {L.ARTICLE: "6"}, {L.ARTICLE: "7"}]
    assert parse_locators("một số điều của") == []


def test_explicit_partial_repeal():
    got = summary(["2. Bãi bỏ khoản 2 Điều 11 Nghị định số 78/2016/NĐ-CP ngày 01 tháng 7 năm 2016."])
    assert got == [(Op.REPEAL, "78/2016/nd/cp", [(("Article", "11"), ("Clause", "2"))], "explicit")]


def test_amending_article_items_inherit_the_heading_document():
    got = summary([
        "Điều 1. Sửa đổi, bổ sung một số điều của Nghị định số 21/2016/NĐ-CP như sau:",
        "1. Sửa đổi khoản 2 Điều 5 như sau:",
        "“2. Nội dung mới có Điều 9 và khoản 3.”",
        "2. Bãi bỏ khoản 3 Điều 7.",
        "3. Thay thế cụm từ “A” bằng cụm từ “B” tại khoản 1 Điều 9.",
        "Điều 2. Hiệu lực thi hành",
        "Nghị định này có hiệu lực từ ngày 01 tháng 01 năm 2018.",
    ])
    assert got == [
        (Op.AMEND, "21/2016/nd/cp", [(("Article", "5"), ("Clause", "2"))], "intro"),
        (Op.REPEAL, "21/2016/nd/cp", [(("Article", "7"), ("Clause", "3"))], "intro"),
        (Op.AMEND, "21/2016/nd/cp", [(("Article", "9"), ("Clause", "1"))], "intro"),
    ]


def test_sub_items_inherit_the_parent_items_article():
    got = summary([
        "Điều 1. Sửa đổi, bổ sung một số điều của Thông tư số 12/2018/TT-BGDĐT như sau:",
        "1. Sửa đổi, bổ sung Điều 5 như sau:",
        "a) Sửa đổi khoản 2 như sau:",
        "“2. mới”",
        "b) Bãi bỏ điểm c khoản 3.",
    ])
    assert [(op, p) for op, _, p, _ in got] == [
        (Op.AMEND, [(("Article", "5"),)]),
        (Op.AMEND, [(("Article", "5"), ("Clause", "2"))]),
        (Op.REPEAL, [(("Article", "5"), ("Clause", "3"), ("Point", "c"))]),
    ]


def test_passive_expiry_after_the_citation():
    got = summary([
        "2. Điều 20, 21 và 27 Mục 2 Chương IV, Chương V của Nghị định số 79/2006/NĐ-CP ngày 09 tháng 8 "
        "năm 2006 của Chính phủ quy định chi tiết thi hành một số điều của Luật dược hết hiệu lực kể từ "
        "ngày Nghị định này có hiệu lực thi hành.",
    ])
    assert got == [(Op.REPEAL, "79/2006/nd/cp",
                    [(("Article", "20"),), (("Article", "21"),), (("Article", "27"),), (("Chapter", "V"),)],
                    "explicit")]


def test_inline_list_after_colon_one_target_per_statement():
    got = summary([
        "2. Bãi bỏ: Điều 2, khoản 2 Điều 3, Điều 6 Nghị định số 141/2013/NĐ-CP ngày 24 tháng 10 năm 2013; "
        "Nghị định số 73/2015/NĐ-CP ngày 08 tháng 9 năm 2015; Quyết định số 70/2014/QĐ-TTg.",
    ])
    assert got == [
        (Op.REPEAL, "141/2013/nd/cp", [(("Article", "2"),), (("Article", "3"), ("Clause", "2")), (("Article", "6"),)], "explicit"),
        (Op.REPEAL, "73/2015/nd/cp", [], "explicit"),
        (Op.REPEAL, "70/2014/qd/ttg", [], "explicit"),
    ]


def test_a_documents_title_is_not_an_instruction():
    # "…09/2001/NĐ-CP … sửa đổi Điều 21 Nghị định số 05-CP" describes 09/2001; 05-CP is untouched here.
    got = summary([
        "Điều 1. Bãi bỏ các văn bản quy phạm pháp luật sau đây:",
        "6. Nghị định số 09/2001/NĐ-CP ngày 02 tháng 3 năm 2001 của Chính phủ sửa đổi Điều 21 "
        "Nghị định số 05-CP ngày 20 tháng 01 năm 1995 của Chính phủ.",
    ])
    assert got == [(Op.REPEAL, "9/2001/nd/cp", [], "explicit")]


def test_references_to_the_acting_document_itself_are_skipped():
    got = summary([
        "Điều 1. Sửa đổi, bổ sung một số điều của Thông tư số 01/2020/TT-BTC như sau:",
        "3. Bãi bỏ khoản 4 Điều này.",
        "Điều 3. Hiệu lực thi hành",
        "Quy định tại Điều 24 của Nghị định này có hiệu lực thi hành từ ngày 01 tháng 01 năm 2028.",
        "Các quy định trước đây trái với Thông tư này đều bãi bỏ.",
    ])
    assert got == []


def test_citation_only_at_the_end_of_a_letter_list():
    got = summary([
        "Điều 16. Hiệu lực thi hành",
        "2. Bãi bỏ các quy định sau đây:",
        "a) Mục 3 Chương II; Điều 21; khoản 1, khoản 2 Điều 43 Thông tư số 06/2010/TT-NHNN.",
    ])
    assert got == [(Op.REPEAL, "6/2010/tt/nhnn",
                    [(("Chapter", "II"), ("Section", "3"))], "forward"),
                   (Op.REPEAL, "6/2010/tt/nhnn", [(("Article", "21"),)], "forward"),
                   (Op.REPEAL, "6/2010/tt/nhnn",
                    [(("Article", "43"), ("Clause", "1")), (("Article", "43"), ("Clause", "2"))], "explicit")]


def test_a_documents_amendment_history_is_not_the_current_act():
    # Hand-check sample row 9: the list header says "Bãi bỏ"; "được sửa đổi, bổ sung tại …
    # Nghị định số 35/2023" only recounts who amended 11/2013 before.
    got = summary([
        "2. Bãi bỏ các quy định sau đây:",
        "a) Khoản 9, 10 Điều 2, Điều 4 của Nghị định số 11/2013/NĐ-CP ngày 14 tháng 01 năm 2013 "
        "được sửa đổi, bổ sung tại Điều 4 của Nghị định số 35/2023/NĐ-CP;",
    ])
    assert got == [(Op.REPEAL, "11/2013/nd/cp",
                    [(("Article", "2"), ("Clause", "9")), (("Article", "2"), ("Clause", "10")), (("Article", "4"),)],
                    "explicit")]


def test_parenthetical_history_is_not_a_target():
    # Sample row 31: the target is khoản 1 Điều 9 of the heading's circular, not 38/2015.
    got = summary([
        "Điều 1. Sửa đổi, bổ sung một số điều của Thông tư số 22/2018/TT-NHNN như sau:",
        "1. Sửa đổi, bổ sung khoản 1 Điều 9 (đã được sửa đổi, bổ sung bởi khoản 16 Điều 1 "
        "Thông tư 38/2015/TT-NHNN) như sau:",
    ])
    assert got == [(Op.AMEND, "22/2018/tt/nhnn", [(("Article", "9"), ("Clause", "1"))], "intro")]


def test_phrase_and_subject_edits_rewrite_a_provision_they_do_not_remove_it():
    got = summary([
        "Điều 1. Sửa đổi, bổ sung một số điều của Nghị định số 139/2021/NĐ-CP như sau:",
        "3. Bãi bỏ cụm từ “ủy quyền” tại Điều 41.",
        "4. Thay cụm từ “A” bằng cụm từ “B” tại khoản 2 Điều 16.",
        "Điều 2. Hiệu lực thi hành",
        "6. Bãi bỏ quy định tại Điều 5 Nghị định số 61/2006/NĐ-CP.",
        "7. Bãi bỏ quy định về phụ cấp đặc thù quy định tại Điều 4, Điều 5 Nghị định số 113/2015/NĐ-CP.",
    ])
    assert [(op, n, p) for op, n, p, _ in got] == [
        (Op.AMEND, "139/2021/nd/cp", [(("Article", "41"),)]),
        (Op.AMEND, "139/2021/nd/cp", [(("Article", "16"), ("Clause", "2"))]),
        (Op.REPEAL, "61/2006/nd/cp", [(("Article", "5"),)]),
        (Op.AMEND, "113/2015/nd/cp", [(("Article", "4"),), (("Article", "5"),)]),
    ]


def test_number_normalisation_and_title_document():
    assert normalize_number("14-CP") == normalize_number("14/CP")
    assert normalize_number("64 TC/TCT") == normalize_number("64/TC-TCT")
    assert normalize_number("47/2000/QĐ-BGD&ĐT") == normalize_number("47/2000/QĐ-BGDĐT")
    assert normalize_number("33/2018/TT- BGTVT") == normalize_number("33/2018/TT-BGTVT")
    # Look-alikes found in the portal's own docNum fields.
    assert normalize_number("89/2015/NÐ-CP") == normalize_number("89/2015/NĐ-CP")  # Latin Eth
    assert normalize_number("51/2025/TT-BTС") == normalize_number("51/2025/TT-BTC")  # Cyrillic Es
    assert normalize_number("9/2019/TT-BTC") == normalize_number("09/2019/TT-BTC")
    assert normalize_number("22/2021/QD-TTg") == normalize_number("22/2021/QĐ-TTg")
    assert title_document("Nghị định số 161/2017/NĐ-CP Sửa đổi Điều 12 Nghị định số 21/2016/NĐ-CP") == "21/2016/NĐ-CP"
    assert title_document("Nghị định số 42/2018/NĐ-CP Bãi bỏ một số Nghị định của Chính phủ") is None


def test_second_hand_check_error_classes():
    # Row 23: numbers after "Phụ lục" are not articles.
    assert parse_locators("khoản 2 Điều 12, Điều 19, Phụ lục 1, 2 và 3 ban hành kèm theo") == [
        {L.CLAUSE: "2", L.ARTICLE: "12"}, {L.ARTICLE: "19"}]
    # Row 2: an unbalanced quote leaves a citation inside the replaced phrase; the edit acts "tại".
    got = summary([
        "Điều 1. Sửa đổi, bổ sung một số điều của Nghị định số 108/2024/NĐ-CP như sau:",
        "5. Thay thế cụm từ “các khoản 3 và 9 Điều 26 Nghị định số 151/2017/NĐ-CP bằng cụm từ X tại khoản 4 Điều 16.",
    ])
    assert got == [(Op.AMEND, "108/2024/nd/cp", [(("Article", "16"), ("Clause", "4"))], "intro")]
    # Row 30: repealing the guidance of Điều 41 inside another circular does not touch Điều 41.
    assert summary(["Bãi bỏ những quy định hướng dẫn thực hiện Điều 41 Nghị định số 197/2004/NĐ-CP "
                    "tại Thông tư số 116/2004/TT-BTC."]) == []
    # Row 51: a quoted paragraph's leftover "." must not drop the parent item's article.
    got = summary([
        "Điều 1. Sửa đổi, bổ sung một số điều của Thông tư số 25/2022/TT-BNNPTNT như sau:",
        "2. Sửa đổi, bổ sung khoản 1 và điểm b khoản 8 Điều 3 như sau:",
        "a) Sửa đổi, bổ sung khoản 1 như sau:",
        "“1. mới”.",
        "b) Sửa đổi, bổ sung điểm b khoản 8 như sau:",
    ])
    assert got[-1][2] == [(("Article", "3"), ("Clause", "8"), ("Point", "b"))]
    # Sample row 17: "Ðiều" spelled with the Latin Eth is still an article.
    got = summary(["Bãi bỏ khoản 3 Ðiều 28 của Luật Thương mại số 36/2005/QH11."])
    assert got == [(Op.REPEAL, "36/2005/qh11", [(("Article", "28"), ("Clause", "3"))], "explicit")]


def test_third_hand_check_error_classes():
    # Row 5: the phrase edit acts at the first "tại"; "được bổ sung tại … 129/2021" is history.
    got = summary(["Bãi bỏ cụm từ “x” tại khoản 2 Điều 11 Nghị định số 38/2021/NĐ-CP, điểm e khoản 10 Điều 11 "
                   "Nghị định số 38/2021/NĐ-CP được bổ sung tại khoản 4 Điều 4 Nghị định số 129/2021/NĐ-CP."])
    assert got == [(Op.AMEND, "38/2021/nd/cp", [(("Article", "11"), ("Clause", "2"))], "explicit")]
    # Row 9: "vào sau Điều 5" is where Điều 5a goes, not a provision being changed.
    got = summary(["Bổ sung Điều 5a vào sau Điều 5 Thông tư số 22/2018/TT-NHNN như sau:"])
    assert got == [(Op.SUPPLEMENT, "22/2018/tt/nhnn", [(("Article", "5a"),)], "explicit")]
    # Rows 18, 22: a neutral list header ("một số nội dung … sau", "nội dung quy định tại") repeals its items whole.
    for header in ("5. Bãi bỏ một số nội dung của các Thông tư sau:", "2. Bãi bỏ các nội dung quy định tại:"):
        got = summary([header, "h) Khoản 2 Điều 4 Thông tư số 08/2014/TT-BNV."])
        assert got == [(Op.REPEAL, "8/2014/tt/bnv", [(("Article", "4"), ("Clause", "2"))], "explicit")]
    # Row 50: an unmarked line under a numbered header belongs to that header's document.
    got = summary([
        "Điều 1. Sửa đổi, bổ sung một số điều của Thông tư số 24/2013/TT-BKHCN như sau:",
        "2. Thay thế một số cụm từ tại Thông tư số 23/2013/TT-BKHCN như sau:",
        "Thay thế cụm từ “Tổng cục” bằng cụm từ “Ủy ban” tại khoản 2 Điều 7.",
    ])
    assert got == [(Op.AMEND, "23/2013/tt/bkhcn", [(("Article", "7"), ("Clause", "2"))], "intro")]

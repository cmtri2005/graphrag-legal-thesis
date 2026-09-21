from legal_crawler.graph.consolidation_validation import (
    normalized_text, select_base_target, source_units, target_units,
)
from legal_crawler.provisions.text import Paragraph
from legal_crawler.temporal import Provision, ProvisionLevel


def test_source_alignment_keeps_article_and_nested_clause_separate():
    paragraphs = [
        Paragraph(None, "Thông tư số 01/2020/TT-A"),
        Paragraph("article", "Điều 01. Phạm vi"),
        Paragraph("article", "Thông tư này quy định A."),
        Paragraph("clause", "1. Nội dung khoản một"),
        Paragraph("clause", "Tiếp theo khoản một."),
        Paragraph(None, "a) Điểm không nhập vào Khoản."),
        Paragraph("next", "Điều 2. Quy định khác"),
    ]
    units, counts = source_units(paragraphs)
    assert [(item.key, item.text) for item in units] == [
        (("Article", "1", None), "Điều 01. Phạm vi Thông tư này quy định A."),
        (("Clause", "1", "1"), "1. Nội dung khoản một Tiếp theo khoản một."),
        (("Article", "2", None), "Điều 2. Quy định khác"),
    ]
    assert units[0].body_text == "Thông tư này quy định A."
    assert units[1].body_text is None
    assert counts["article_markers"] == 2
    assert counts["clause_markers"] == 1


def test_duplicate_source_article_is_excluded_not_silently_overwritten():
    units, counts = source_units([
        Paragraph(None, "Điều 1. Bản thứ nhất"),
        Paragraph(None, "Điều 1. Bản thứ hai"),
    ])
    assert units == []
    assert counts["duplicate_unit_keys"] == 1


def test_numbered_footnote_markers_and_duplicate_clauses_are_conservative():
    units, counts = source_units([
        Paragraph(None, "Điều 1[3]. Phạm vi"),
        Paragraph(None, "1[4]. Khoản đầu"),
        Paragraph(None, "1. Khoản trùng từ chú thích"),
        Paragraph(None, "Chương II"),
        Paragraph(None, "Điều 2. Quy định mới"),
        Paragraph(None, "Phụ lục ban hành kèm theo"),
        Paragraph(None, "Điều 3. Không thuộc phép đối chiếu"),
    ])
    assert [unit.key for unit in units] == [
        ("Article", "1", None), ("Article", "2", None),
    ]
    assert counts["duplicate_unit_keys"] == 1


def test_target_keys_require_direct_parent_and_unique_number():
    provisions = [
        Provision("a1", "d", ProvisionLevel.ARTICLE, "Điều 1", None),
        Provision("c1", "d", ProvisionLevel.CLAUSE, "Khoản 1", "a1"),
        Provision("p1", "d", ProvisionLevel.POINT, "Điểm a", "c1"),
        Provision("nested", "d", ProvisionLevel.CLAUSE, "Khoản 2", "p1"),
        Provision("a1again", "d", ProvisionLevel.ARTICLE, "Điều 01", None),
        Provision("a2", "d", ProvisionLevel.ARTICLE, "Điều 2", None),
    ]
    keys, ambiguous = target_units(provisions)
    assert ("Article", "1", None) in ambiguous
    assert keys[("Clause", "1", "1")] == "c1"
    assert ("Clause", "1", "2") not in keys
    assert keys[("Article", "2", None)] == "a2"


def test_base_selection_uses_first_explicit_target_citation():
    numbers = {"amendment": "136/2025/TT-BTC", "base": "98/2020/TT-BTC"}
    preamble = (
        "Thông tư số 98 / 2020 / TT-BTC được sửa đổi bởi "
        "Thông tư số 136/2025/TT-BTC."
    )
    assert select_base_target(numbers, preamble) == ("base", "first_target_cited")
    assert select_base_target(numbers, "không dẫn số nào") == (
        None, "no_target_number_in_preamble",
    )
    assert select_base_target(
        {"copy_a": "01/2020/TT-X", "copy_b": "01/2020/TT-X"},
        "Thông tư số 01/2020/TT-X",
    ) == (None, "ambiguous_first_citation")
    assert select_base_target(
        {"amendment": "13/2025/QĐ-TTg", "base": "22/2021/QD-TTg"},
        "Quyết định 22/2021/QĐ-TTg được sửa đổi bởi 13/2025/QĐ-TTg",
    ) == ("base", "first_target_cited")


def test_text_normalization_does_not_rewrite_legal_content():
    assert normalized_text("Điều 1.\n  Có hiệu lực") == "Điều 1. Có hiệu lực"
    assert normalized_text("Điều 1. Có hiệu lực") != "Điều 1: Có hiệu lực"

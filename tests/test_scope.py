from build_eligibility import manual_text_priority
from legal_crawler.vocab.scope import (
    CONSOLIDATED,
    LOCAL,
    NON_NORMATIVE,
    QPPL,
    TRANSLATION,
    document_class,
)


def doc(name, parent="VBQPPL", agency="Bộ Tài chính", **extra):
    return {"docType": {"name": name, "parentCode": parent}, "agencyName": agency, **extra}


def test_central_qppl_is_in_scope_even_when_org_type_says_local():
    # 75/2010/NĐ-CP carries orgType "1"; the issuer's name is what decides.
    assert document_class(doc("Nghị định", agency="Chính phủ", organization={"orgType": "1"})) == QPPL
    assert document_class(doc("Sắc lệnh", parent=None, agency="Chủ tịch nước")) == QPPL


def test_local_documents_are_caught_by_agency_or_number():
    assert document_class(doc("Quyết định", agency="UBND Tỉnh Lào Cai")) == LOCAL
    assert document_class(doc("Nghị quyết", agency="HĐND Tỉnh Cà Mau")) == LOCAL
    assert document_class(doc("Nghị quyết", agency="", docNum="06/2010/NQ-HĐND7")) == LOCAL


def test_everything_else_is_kept_out_of_evidence():
    assert document_class(doc("Văn bản hợp nhất", parent="VBHN")) == CONSOLIDATED
    assert document_class(doc("Công văn", parent=None)) == NON_NORMATIVE
    assert document_class(doc("Thông tư", isTranslationDoc=True)) == TRANSLATION
    assert document_class(doc("Bản dịch văn bản", parent="")) == TRANSLATION


def test_manual_text_priority():
    # No text and still (partly) in force: always typed in first.
    assert manual_text_priority(True, False, "CHL", False, False) == 1
    assert manual_text_priority(True, False, "HHL1P", False, False) == 1
    # Fully repealed: only when it is a seed on a genealogy path.
    assert manual_text_priority(True, False, "HHL", True, True) == 2
    assert manual_text_priority(True, False, "HHL", True, False) is None
    # Out of scope or already has text: never queued.
    assert manual_text_priority(False, False, "CHL", True, True) is None
    assert manual_text_priority(True, True, "CHL", True, True) is None

from verify_temporal_candidates import text_confirms

ACTOR_HTML = "<p>Điều 1. Bãi bỏ Thông tư số 14/TTLB ngày 19/9/1994.</p>"


def test_citation_next_to_keyword_confirms():
    evidence = text_confirms("14/TTLB", ACTOR_HTML)
    assert evidence is not None
    assert evidence["keyword"] == "bãi bỏ"


def test_citation_without_a_keyword_nearby_is_inconclusive():
    far = "<p>Điều 1. Ban hành kèm quy chế mới.</p>" + "x" * 400 + "<p>xem thêm 14/TTLB</p>"
    assert text_confirms("14/TTLB", far) is None


def test_no_citation_at_all_is_inconclusive():
    assert text_confirms("14/TTLB", "<p>Điều 1. Bãi bỏ văn bản trước đây.</p>") is None


def test_missing_inputs_are_inconclusive():
    assert text_confirms("", ACTOR_HTML) is None
    assert text_confirms("14/TTLB", "") is None


def test_citation_far_down_a_numbered_repeal_list_still_confirms():
    # A citation can sit well past a 300-char window when it's item c) of a
    # long "Điều N. Hiệu lực thi hành ... bãi bỏ: a) ... b) ... c) <cite>" list.
    filler = "Quy định khác không liên quan. " * 30
    html = (
        f"<p>Điều 33. Hiệu lực thi hành</p><p>1. Có hiệu lực từ 01/7/2024.</p>"
        f"<p>2. Bãi bỏ: a) {filler} b) {filler} c) Thông tư số 03/2014/TT-NHNN.</p>"
    )
    evidence = text_confirms("03/2014/TT-NHNN", html)
    assert evidence is not None


def test_separator_variants_between_docnum_and_text_still_match():
    # docNum field says "191/CP"; pre-2000 documents often write it "191-CP".
    html = "<p>Điều 1. Bãi bỏ: 1. Quyết định số 191-CP ngày 23/6/1980.</p>"
    assert text_confirms("191/CP", html) is not None
    # docNum "64/TC-TCT" written in prose as "64 TC/TCT" (space, then slash).
    html2 = "<p>Điều 2. Những quy định tại thông tư số 64 TC/TCT đều bãi bỏ.</p>"
    assert text_confirms("64/TC-TCT", html2) is not None


def test_html_entities_are_decoded_before_matching():
    # docNum field has a plain "&"; the raw HTML payload keeps it escaped.
    html_src = "<p>Điều 1. Bãi bỏ Quyết định số 47/2000/QĐ-BGD&amp;ĐT ngày 08/11/2000.</p>"
    assert text_confirms("47/2000/QĐ-BGD&ĐT", html_src) is not None


def test_a_citation_scoped_to_one_provision_of_the_target_does_not_confirm():
    # "Bãi bỏ khoản 2 Điều 11 Nghị định số X" repeals one clause of X, not X.
    html = "<p>Điều 1. Bãi bỏ khoản 2 Điều 11 Nghị định số 78/2016/NĐ-CP ngày 01/7/2016.</p>"
    assert text_confirms("78/2016/NĐ-CP", html) is None


def test_a_plain_whole_document_citation_after_a_scoped_one_still_confirms():
    # A partial repeal of ONE document earlier in a list must not block a
    # later, unscoped, whole-document citation of a DIFFERENT target.
    html = (
        "<p>Điều 1. Bãi bỏ: 1. Điều 4, Điều 5 của Thông tư số 11/2011/TT-ABC "
        "ngày 01/01/2011. 2. Thông tư số 22/2012/TT-XYZ ngày 02/02/2012 "
        "quy định về việc khác.</p>"
    )
    assert text_confirms("22/2012/TT-XYZ", html) is not None
    assert text_confirms("11/2011/TT-ABC", html) is None


def test_an_earlier_mid_document_mention_of_the_heading_is_not_the_anchor():
    # Only the LAST "hiệu lực thi hành" occurrence is the closing article; an
    # earlier one (e.g. quoting another document's heading) must not anchor.
    html = (
        "<p>Căn cứ Thông tư số 14/TTLB có Điều 5. Hiệu lực thi hành riêng.</p>"
        + "x" * 400
        + "<p>Điều 9. Hiệu lực thi hành. Văn bản này có hiệu lực từ 2020.</p>"
    )
    assert text_confirms("14/TTLB", html) is None

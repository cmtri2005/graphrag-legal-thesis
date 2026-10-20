from vilexgraph.build.extraction.provision_ops import extract_mentions
from vilexgraph.build.extraction.wording import fit, parse_items, wording_blocks
from vilexgraph.build.temporal.models import Provision
from vilexgraph.build.temporal.models import ProvisionLevel as L

AMEND = [
    "Điều 1. Sửa đổi, bổ sung một số điều của Thông tư số 23/2021/TT-BTC như sau:",
    "1. Sửa đổi, bổ sung điểm a, điểm b khoản 4 Điều 3 như sau:",
    '"4. Đơn vị thực hiện dán tem điện tử',
    'a) Doanh nghiệp thay cụm từ "tem giấy" bằng "tem điện tử".',
    "Nội dung tiếp của điểm a.",
    'b) Trường hợp nhập khẩu thì dán tại nước ngoài.".',
    "2. Bãi bỏ Điều 7.",
]


def test_blocks_close_on_their_own_quote_and_nothing_else():
    blocks = wording_blocks(AMEND)
    assert list(blocks) == [1]
    assert (blocks[1].start, blocks[1].end) == (2, 5)
    assert blocks[1].lines[0] == "4. Đơn vị thực hiện dán tem điện tử"
    assert blocks[1].lines[-1] == "b) Trường hợp nhập khẩu thì dán tại nước ngoài."
    curly = ["a) Sửa đổi khoản 2 như sau: “2. Mức phạt “cao” hơn.”", "“3. Không đóng"]
    assert wording_blocks(curly)[0].lines == ("2. Mức phạt “cao” hơn.",)
    assert wording_blocks(curly)[0].inline_at == len("a) Sửa đổi khoản 2 như sau: ")
    assert 1 not in wording_blocks(curly)  # never closes: not a block
    # The instruction goes on after the quote: the parser keeps it, not this module.
    assert wording_blocks(["Sửa đổi như sau: “a”; bổ sung khoản 3"]) == {}


def test_quoted_wording_is_never_read_as_an_instruction():
    # Straight quotes are not balanced by `_drop_quotes`; "a) … thay cụm từ" inside
    # the block used to inherit the item's operation.
    mentions = extract_mentions(AMEND)
    assert [(m.operation.value, m.paragraph) for m in mentions] == [("amend", 1), ("repeal", 6)]


def node(id, level, title, parent):
    return Provision(id=id, document_id="d", level=level, title=title, parent_id=parent)


TREE = (
    node("k4", L.CLAUSE, "Khoản 4", "d3"),
    node("a", L.POINT, "Điểm a", "k4"),
    node("b", L.POINT, "Điểm b", "k4"),
)


def test_fit_lays_each_item_on_its_node():
    items = parse_items(wording_blocks(AMEND)[1].lines)
    assert [(i.level, i.label, [c.label for c in i.children]) for i in items] == [(L.CLAUSE, "4", ["a", "b"])]
    point_a = fit(items, {L.ARTICLE: "3", L.CLAUSE: "4", L.POINT: "a"}, TREE[1], ())
    assert point_a == {"a": 'a) Doanh nghiệp thay cụm từ "tem giấy" bằng "tem điện tử". Nội dung tiếp của điểm a.'}
    whole = fit(items, {L.ARTICLE: "3", L.CLAUSE: "4"}, TREE[0], TREE[1:])
    assert set(whole) == {"k4", "a", "b"}


def test_fit_refuses_a_structure_change():
    items = parse_items(("4. Đơn vị", "a) Một", "b) Hai", "c) Ba mới"))
    assert fit(items, {L.ARTICLE: "3", L.CLAUSE: "4"}, TREE[0], TREE[1:]) is None  # adds điểm c
    assert fit(items, {L.ARTICLE: "3", L.CLAUSE: "5"}, TREE[0], TREE[1:]) is None  # not in the block
    assert parse_items(("Đoạn không có số", "4. Đơn vị")) is None


def test_a_leaf_takes_the_whole_item_as_its_text():
    # The tree stops at Khoản 2, so its stored text already runs through its points.
    items = parse_items(("2. Điều kiện:", "a) Có chứng chỉ;", "b) Kinh nghiệm."))
    leaf = node("k2", L.CLAUSE, "Khoản 2", "d4")
    assert fit(items, {L.ARTICLE: "4", L.CLAUSE: "2"}, leaf, ()) == {"k2": "2. Điều kiện: a) Có chứng chỉ; b) Kinh nghiệm."}
    assert [i.label for i in parse_items(("Điều 11", "Phạm vi", "1. Một"))] == ["11"]


def test_phrase_edit_reads_a_replacement_either_side_of_the_locators():
    from vilexgraph.build.extraction.wording import phrase_edits

    assert phrase_edits('Thay thế cụm từ "Cục Con nuôi" bằng cụm từ "Bộ Tư pháp" tại khoản 3 Điều 30.') == [
        ("Cục Con nuôi", "Bộ Tư pháp")
    ]
    assert phrase_edits('Thay thế cụm từ “A” tại khoản 1 Điều 2, khoản 4 Điều 4 thành cụm từ “B”.') == [("A", "B")]
    assert phrase_edits('Bãi bỏ cụm từ "thi hoặc" tại khoản 4 Điều 4.') == [("thi hoặc", "")]


def test_phrase_edit_refuses_what_it_cannot_read_without_guessing():
    from vilexgraph.build.extraction.wording import phrase_edits

    assert phrase_edits("Sửa đổi, bổ sung khoản 2 Điều 17 như sau:") == []
    # three quoted runs: which one replaces which is not determined
    assert phrase_edits('Thay thế cụm từ "A" bằng cụm từ "B" và cụm từ "C".') == []
    assert phrase_edits('Bãi bỏ cụm từ "A" và cụm từ "B".') == []


def test_apply_phrase_demands_the_phrase_be_present_verbatim():
    from vilexgraph.build.extraction.wording import apply_phrase

    assert apply_phrase("Do Cục Con nuôi quyết định.", [("Cục Con nuôi", "Bộ Tư pháp")]) == "Do Bộ Tư pháp quyết định."
    assert apply_phrase("Do Bộ Tư pháp quyết định.", [("Cục Con nuôi", "Bộ Tư pháp")]) is None
    # a deletion that would leave "Cấm  kiểm tra." is refused, see the test below
    assert apply_phrase("Cấm thi hoặc kiểm tra.", [("thi hoặc", "")]) is None


def test_apply_phrase_matches_a_phrase_whatever_its_case():
    from vilexgraph.build.extraction.wording import apply_phrase

    # 104/2022/NĐ-CP quotes "trong giai đoạn…" where 123/2015/NĐ-CP opens a sentence with it
    assert apply_phrase("1. Trong giai đoạn chuyển tiếp, cơ quan cấp giấy.", [("trong giai đoạn chuyển tiếp, ", "")]) \
        == "1. cơ quan cấp giấy."
    assert apply_phrase("Tổng cục Đường bộ; tổng cục đường bộ.", [("Tổng cục Đường bộ", "Cục Đường bộ")]) \
        == "Cục Đường bộ; tổng cục đường bộ."            # a verbatim match wins over the folded one
    assert apply_phrase("Giấy chứng nhận quyền sử dụng đất.", [("giấy chứng nhận quyền sử dụng đất", "giấy chứng nhận")]) \
        == "Giấy chứng nhận."                              # the capital stays where the sentence opens
    assert apply_phrase("Do Bộ Tư pháp quyết định.", [("cục con nuôi", "Bộ Tư pháp")]) is None


def test_apply_phrase_refuses_a_deletion_that_strands_punctuation():
    from vilexgraph.build.extraction.wording import apply_phrase

    # "… cấp tỉnh, <phrase>; tổ chức …" would be left as "cấp tỉnh, ; tổ chức"
    assert apply_phrase("Đại hội cấp tỉnh, cấp huyện; tổ chức hoạt động.",
                        [("cấp huyện", "")]) is None
    # a clean deletion still goes through
    assert apply_phrase("Cấm thi hoặc kiểm tra.", [("thi hoặc ", "")]) == "Cấm kiểm tra."


def test_an_omnibus_heading_without_nhu_sau_opens_its_wording():
    # NĐ 14/2026/NĐ-CP Điều 123: the heading is the instruction.
    paragraphs = [
        "Điều 123. Sửa đổi, bổ sung khoản 2 Điều 43",
        "“2. Thủ tục đóng tạm thời cảng hàng không, sân bay:",
        "a) Cục Hàng không Việt Nam thẩm định.”.",
        "Điều 124. Hiệu lực thi hành",
        "“Ghi chú” không phải lời văn mới.",
    ]
    blocks = wording_blocks(paragraphs)
    assert list(blocks) == [0] and blocks[0].lines[-1] == "a) Cục Hàng không Việt Nam thẩm định."

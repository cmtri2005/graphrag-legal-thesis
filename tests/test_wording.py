from legal_crawler.extraction.provision_ops import extract_mentions
from legal_crawler.extraction.wording import fit, parse_items, wording_blocks
from legal_crawler.temporal.models import Provision
from legal_crawler.temporal.models import ProvisionLevel as L

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

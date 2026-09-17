from legal_crawler.provisions.subtree import split_document

ARTICLE_ONLY_TREE = [
    {"id": "a1", "title": "Điều 1", "level": "Article"},
    {"id": "a2", "title": "Điều 2", "level": "Article"},
]


def by_title(split):
    return {(n["parent_id"], n["title"]): n for n in split.nodes}


def test_clauses_and_points_are_split_from_an_undeclared_article():
    html = (
        "<body><p id='a1'>Điều 1. Phạm vi</p>"
        "<p>1. Khoản một, mức phạt 1.000.000 đồng.</p>"
        "<p>a) Điểm a;</p><p>b) Điểm b;</p><p>tiếp nối điểm b.</p>"
        "<p>2. Khoản hai.</p>"
        "<p id='a2'>Điều 2. Hiệu lực</p><p>1. Không thuộc Điều 1.</p></body>"
    )
    nodes = by_title(split_document(ARTICLE_ONLY_TREE, html))
    assert nodes[("a1", "Khoản 1")]["id"] == "a1#k1"
    # A clause's own text stops at its first point; the point keeps its continuation.
    assert nodes[("a1", "Khoản 1")]["text"] == "1. Khoản một, mức phạt 1.000.000 đồng."
    assert nodes[("a1#k1", "Điểm b")]["text"] == "b) Điểm b; tiếp nối điểm b."
    assert nodes[("a1", "Khoản 2")]["text"] == "2. Khoản hai."
    # Điều 2's "1." is Điều 2's, never Điều 1's third clause.
    assert ("a1", "Khoản 3") not in nodes
    assert nodes[("a2", "Khoản 1")]["text"] == "1. Không thuộc Điều 1."


def test_quoted_amendment_text_is_not_split():
    html = (
        "<body><p id='a1'>Điều 1. Sửa đổi Nghị định số 100</p>"
        "<p>1. Sửa đổi khoản 2 Điều 5 như sau:</p>"
        "<p>“2. Phạt tiền từ 200.000 đồng:</p>"
        "<p>a) Hành vi thứ nhất;</p>"
        "<p>b) Hành vi thứ hai.”</p>"
        "<p>2. Bãi bỏ khoản 4 Điều 7.</p>"
        "<p id='a2'>Điều 2. Hiệu lực</p></body>"
    )
    split = split_document(ARTICLE_ONLY_TREE, html)
    titles = sorted(n["id"] for n in split.nodes)
    assert titles == ["a1#k1", "a1#k2"]
    # The quoted provision is carried inside the amending clause's text.
    assert "“2. Phạt tiền" in by_title(split)[("a1", "Khoản 1")]["text"]


def test_broken_numbering_refuses_instead_of_guessing():
    html = (
        "<body><p id='a1'>Điều 1. Danh mục</p>"
        "<p>1. Mục một.</p><p>3. Mục ba.</p>"
        "<p id='a2'>Điều 2. Khác</p></body>"
    )
    split = split_document(ARTICLE_ONLY_TREE, html)
    assert not [n for n in split.nodes if n["parent_id"] == "a1"]
    assert split.skipped[0]["node_id"] == "a1"


def test_text_before_the_first_marker_is_a_preamble_not_lost_or_misattributed():
    html = (
        "<body><p id='a1'>Điều 1. Điều kiện</p>"
        "<p>Học sinh phải có đủ các điều kiện sau:</p>"
        "<p>1. Điều kiện một.</p><p>2. Điều kiện hai.</p>"
        "<p id='a2'>Điều 2. Hiệu lực</p></body>"
    )
    split = split_document(ARTICLE_ONLY_TREE, html)
    assert split.preambles == [{"parent_id": "a1", "text": "Học sinh phải có đủ các điều kiện sau:"}]
    # The preamble sentence must not leak into Khoản 1's own text.
    assert by_title(split)[("a1", "Khoản 1")]["text"] == "1. Điều kiện một."


def test_no_preamble_recorded_when_the_marker_comes_first():
    html = (
        "<body><p id='a1'>Điều 1. Tên</p>"
        "<p>1. Khoản một ngay từ đầu.</p>"
        "<p id='a2'>Điều 2. Khác</p></body>"
    )
    split = split_document(ARTICLE_ONLY_TREE, html)
    assert split.preambles == []


def test_declared_children_are_never_second_guessed_and_markers_anchor_old_html():
    tree = [
        {"id": "a1", "title": "Điều 1", "level": "Article",
         "children": [{"id": "k1", "title": "Khoản 1", "level": "Clause"}]},
    ]
    html = "<body><div>Điều 1. Tên</div><div>1. Khoản đã khai báo.</div><div>a) Điểm chưa khai báo.</div></body>"
    split = split_document(tree, html)
    assert [n["id"] for n in split.nodes] == ["k1#a"]
    assert split.nodes[0]["title"] == "Điểm a"

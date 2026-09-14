from legal_crawler.provisions.text import align, align_by_marker, flatten, parse_paragraphs

# Shape of a modern record: the server tags each paragraph with the tree node's
# own uuid, so the join is exact rather than inferred.
TAGGED_HTML = """<html><body>
  <p style="text-align:center">THÔNG TƯ</p>
  <p id="c1" class="prov-chapter">Chương I</p>
  <p id="a1" class="prov-article">Điều 1. Phạm vi điều chỉnh</p>
  <p id="k1" class="prov-clause">1. Thông tư này quy định&nbsp;giá dịch vụ.</p>
  <p>Nội dung nối tiếp của khoản 1.</p>
  <p id="p1" class="prov-item">a) Tổ chức, cá nhân kinh doanh;</p>
</body></html>"""

TREE = [
    {
        "id": "c1", "title": "Chương I", "level": "Chapter", "orderIndex": 1,
        "children": [
            {
                "id": "a1", "title": "Điều 1", "level": "Article", "orderIndex": 2,
                "children": [
                    {
                        "id": "k1", "title": "Khoản 1", "level": "Clause", "orderIndex": 3,
                        "children": [
                            {"id": "p1", "title": "Điểm a", "level": "Point", "orderIndex": 4},
                        ],
                    }
                ],
            }
        ],
    }
]

# Older records: no ids anywhere, and paragraphs wrapped in <div>, not <p>.
UNTAGGED_HTML = """<!DOCTYPE html><html><head><style>p{margin:0}</style></head><body>
  <div align="center"><b>QUYẾT ĐỊNH</b></div>
  <div>Căn cứ Nghị định số 71/2006/NĐ-CP;</div>
  <div><strong>Điều 1.</strong> Nay công bố vùng nước các cảng biển.</div>
  <div>1. Vùng nước trước cầu cảng;</div>
  <div>a) Vùng đón trả hoa tiêu;</div>
  <div><strong>Điều 2.</strong> Quyết định này có hiệu lực sau 15 ngày.</div>
</body></html>"""


def test_flatten_is_document_order_and_records_parents():
    nodes = flatten(TREE)
    assert [n["id"] for n in nodes] == ["c1", "a1", "k1", "p1"]
    assert [n["parent_id"] for n in nodes] == [None, "c1", "a1", "k1"]


def test_tagged_html_joins_exactly_and_absorbs_continuations():
    result = align(TREE, TAGGED_HTML)
    assert result.method == "id"
    assert result.coverage == 1.0
    assert result.texts["a1"] == "Điều 1. Phạm vi điều chỉnh"
    # The untagged paragraph after Khoản 1 belongs to it, not to Điểm a.
    assert result.texts["k1"] == "1. Thông tư này quy định giá dịch vụ. Nội dung nối tiếp của khoản 1."
    assert result.texts["p1"] == "a) Tổ chức, cá nhân kinh doanh;"


def test_preamble_is_not_attached_to_any_node():
    assert "THÔNG TƯ" not in "".join(align(TREE, TAGGED_HTML).texts.values())


def test_untagged_html_falls_back_to_markers():
    # <div>-only bodies used to parse to nothing at all; this is the regression.
    assert parse_paragraphs(UNTAGGED_HTML)
    tree = [
        {"id": "a1", "title": "Điều 1", "level": "Article", "orderIndex": 1,
         "children": [
             {"id": "k1", "title": "Khoản 1", "level": "Clause", "orderIndex": 2,
              "children": [{"id": "p1", "title": "Điểm a", "level": "Point", "orderIndex": 3}]},
         ]},
        {"id": "a2", "title": "Điều 2", "level": "Article", "orderIndex": 4},
    ]
    result = align(tree, UNTAGGED_HTML)
    assert result.method == "marker"
    assert result.coverage == 1.0
    assert result.texts["a1"].startswith("Điều 1.")
    assert result.texts["a2"].startswith("Điều 2.")
    assert result.texts["p1"].startswith("a)")


def test_marker_match_only_ever_scans_forward():
    # "Điều 1" appears again inside Điều 2's body; a backward or global search
    # would re-assign it and shift every later node.
    paragraphs = parse_paragraphs(
        "<body><div>Điều 1. Đầu tiên.</div>"
        "<div>Điều 2. Sửa đổi Điều 1 của Quyết định trên.</div></body>"
    )
    nodes = [
        {"id": "a1", "title": "Điều 1", "level": "Article"},
        {"id": "a2", "title": "Điều 2", "level": "Article"},
    ]
    texts = align_by_marker(nodes, paragraphs)
    assert texts["a1"] == "Điều 1. Đầu tiên."
    assert texts["a2"].startswith("Điều 2.")


def test_unnumbered_nodes_are_left_out_rather_than_guessed():
    # Old trees carry bare "Điều"/"Phần" titles, and several siblings all titled
    # "Khoản 1". Matching those to whatever comes next would be a fabrication.
    nodes = [
        {"id": "x", "title": "Điều", "level": "Article"},
        {"id": "y", "title": "Phần", "level": "Part"},
    ]
    assert align_by_marker(nodes, parse_paragraphs(UNTAGGED_HTML)) == {}


def test_ids_that_are_not_tree_nodes_do_not_force_the_id_join():
    # Some bodies tag paragraphs with presentation ids of their own. Choosing the
    # id join on "any id present" used to write these out with zero nodes.
    html = (
        "<body><p id='layout-1'>QUYẾT ĐỊNH</p>"
        "<p id='layout-2'>Điều 1. Phạm vi.</p><p id='layout-3'>1. Khoản một.</p>"
        "<p id='layout-4'>Điều 2. Hiệu lực.</p></body>"
    )
    tree = [
        {"id": "a1", "title": "Điều 1", "level": "Article",
         "children": [{"id": "k1", "title": "Khoản 1", "level": "Clause"}]},
        {"id": "a2", "title": "Điều 2", "level": "Article"},
    ]
    result = align(tree, html)
    assert result.method == "marker"
    assert set(result.texts) == {"a1", "k1", "a2"}


def test_low_id_coverage_is_topped_up_by_markers_without_replacing_joined_text():
    # Điều 1 and Điều 3 are tagged; Điều 2 and its clause are not. Markers fill
    # only the gap, and only between the two anchors.
    html = (
        "<body><p id='a1'>Điều 1. Có id.</p><p>1. Khoản của Điều 1 không id.</p>"
        "<p>Điều 2. Không id.</p><p>1. Khoản của Điều 2.</p>"
        "<p id='a3'>Điều 3. Có id.</p></body>"
    )
    tree = [
        {"id": "a1", "title": "Điều 1", "level": "Article"},
        {"id": "a2", "title": "Điều 2", "level": "Article",
         "children": [{"id": "k21", "title": "Khoản 1", "level": "Clause"}]},
        {"id": "a3", "title": "Điều 3", "level": "Article"},
        {"id": "a4", "title": "Điều 4", "level": "Article",
         "children": [{"id": "k41", "title": "Khoản 1", "level": "Clause"}]},
        {"id": "a5", "title": "Điều 5", "level": "Article"},
    ]
    result = align(tree, html)
    assert result.method == "id+marker"
    # Joined text (with its untagged continuation) is kept verbatim.
    assert result.texts["a1"] == "Điều 1. Có id. 1. Khoản của Điều 1 không id."
    assert result.texts["a2"] == "Điều 2. Không id."
    # Khoản 1 of Điều 2 comes from Điều 2's paragraphs, not Điều 1's "1.".
    assert result.texts["k21"] == "1. Khoản của Điều 2."
    # Nothing past the last anchor matches Điều 4/5, and nothing is invented.
    assert "a4" not in result.texts and "k41" not in result.texts
    assert len(result.texts) <= result.total_nodes


def test_good_id_coverage_is_left_alone():
    assert align(TREE, TAGGED_HTML).method == "id"


def test_visible_text_ignores_shells_and_entities():
    from legal_crawler.provisions.text import has_visible_text

    assert not has_visible_text("")
    assert not has_visible_text("<html><head><title>x</title><style>p{}</style></head><body>&nbsp; </body></html>")
    assert has_visible_text("<body>Điều 1. Có chữ ngoài thẻ khối</body>")

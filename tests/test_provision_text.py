from legal_crawler.provision_text import align, align_by_marker, flatten, parse_paragraphs

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

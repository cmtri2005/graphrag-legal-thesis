import json

import pytest

from legal_crawler.provision_tree import (
    MissingPayloadRowError,
    count_by_level,
    parse_flight_payload,
)

# Shape copied from a real response for doc 187835 (Nghị định 135/2026/NĐ-CP),
# trimmed to two articles.
_TREE = [
    {
        "key": "chap-1",
        "id": "chap-1",
        "title": "Chương I",
        "ptype": 2,
        "level": "Chapter",
        "orderIndex": 1,
        "isLeaf": False,
        "children": [
            {
                "id": "art-1",
                "title": "Điều 1",
                "level": "Article",
                "isLeaf": False,
                "children": [
                    {"id": "cl-1", "title": "Khoản 1", "level": "Clause", "children": []},
                    {
                        "id": "cl-2",
                        "title": "Khoản 2",
                        "level": "Clause",
                        "children": [
                            {"id": "pt-a", "title": "Điểm a", "level": "Point", "children": []}
                        ],
                    },
                ],
            },
            {"id": "art-2", "title": "Điều 2", "level": "Article", "children": []},
        ],
    }
]

_FLIGHT_BODY = (
    '0:["$@1",["lXFAMWsOsqymc2MSVq31c",null]]\n'
    f"1:{json.dumps(_TREE, ensure_ascii=False)}\n"
)


def test_parses_payload_row_and_ignores_routing_row():
    assert parse_flight_payload(_FLIGHT_BODY) == _TREE


def test_counts_every_level_through_nesting():
    assert count_by_level(_TREE) == {"Chapter": 1, "Article": 2, "Clause": 2, "Point": 1}


def test_null_tree_is_an_empty_list_not_an_error():
    # Documents with no article structure (Công văn, Bản dịch, old Sắc lệnh)
    # legitimately come back like this — it must not raise.
    assert parse_flight_payload('0:["$@1",[]]\n1:null\n') == []
    assert parse_flight_payload('0:["$@1",[]]\n1:[]\n') == []


def test_missing_payload_row_raises_instead_of_looking_empty():
    # A rotated Next.js build id drops the row entirely. Returning [] here
    # would silently overwrite the corpus with empty trees.
    with pytest.raises(MissingPayloadRowError):
        parse_flight_payload('0:["$@1",["build",null]]\n')

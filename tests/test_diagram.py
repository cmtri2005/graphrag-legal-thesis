from legal_crawler.graph.diagram import (
    REVERSE_EXPANDABLE,
    expandable_targets,
    parse_reverse_edges,
)
from legal_crawler.models import Edge

# Shape from a real /doc/133959/diagram response, trimmed.
_DIAGRAM = {
    "documentNamesByType": {
        "3": [{"id": "126306", "name": "Luật Lâm nghiệp số 16/2017/QH14"}],
    },
    "documentNamesBySource": {
        "10": [{"id": "164789", "name": "Thông tư 22/2023 Sửa đổi, bổ sung..."}],
        "9": [{"id": "173187", "name": "Thông tư 23/2024 Quy định định mức..."}],
        "7": [{"id": "166597", "name": "Văn bản hợp nhất số 08/VBHN-BNNPTNT"}],
    },
}


def test_reverse_edge_points_from_the_acting_document():
    # The amender is the source, matching how references[] would record it
    # from the amender's own side — downstream code sees one edge shape.
    edges = parse_reverse_edges("133959", _DIAGRAM)
    assert Edge(source_id="164789", target_id="133959", reference_type=10) in edges


def test_outbound_half_is_ignored():
    # documentNamesByType duplicates references[], which Stage 2 already has.
    edges = parse_reverse_edges("133959", _DIAGRAM)
    assert all(e.source_id != "126306" for e in edges)
    assert len(edges) == 3


def test_only_expandable_relations_pull_in_new_documents():
    edges = parse_reverse_edges("133959", _DIAGRAM)
    assert expandable_targets(edges, held=set()) == {"164789"}


def test_documents_already_held_are_not_refetched():
    edges = parse_reverse_edges("133959", _DIAGRAM)
    assert expandable_targets(edges, held={"164789"}) == set()


def test_implementing_documents_are_never_followed():
    # Inbound code 9 means "everything implementing me" — following it would
    # drag the crawl across the whole database (see graph/diagram.py).
    assert 9 not in REVERSE_EXPANDABLE
    assert 7 not in REVERSE_EXPANDABLE


def test_missing_id_is_skipped_not_crashed():
    assert parse_reverse_edges("1", {"documentNamesBySource": {"10": [{"name": "no id"}]}}) == []
    assert parse_reverse_edges("1", {}) == []

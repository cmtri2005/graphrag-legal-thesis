import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from legal_crawler.graph.expand import expand
from legal_crawler.models import Edge
from legal_crawler.vocab.reference_types import ReferenceTypeMap, UnknownReferenceTypeError

MAP_JSON = {
    "codes": {
        "10": {"label_vi": "Sửa đổi bổ sung", "group": "genealogy", "verified": True},
        "3": {"label_vi": "Căn cứ ban hành", "group": "open_citation", "verified": True},
    }
}


def ref(target_id: str, reference_type: int) -> dict:
    return {"referenceType": reference_type, "targetDocument": {"id": target_id}}


@pytest.fixture
def ref_map(tmp_path: Path) -> ReferenceTypeMap:
    path = tmp_path / "reference_type_map.json"
    path.write_text(json.dumps(MAP_JSON), encoding="utf-8")
    return ReferenceTypeMap.load(path)


def test_expands_through_genealogy_edge(ref_map: ReferenceTypeMap):
    docs = {
        "A": {"references": [ref("B", 10)]},  # 10 = genealogy, sửa đổi bổ sung
        "B": {"references": []},
    }
    result = expand(["A"], docs.__getitem__, ref_map)
    assert set(result.documents) == {"A", "B"}
    assert result.edges == [Edge("A", "B", 10)]


def test_does_not_expand_through_open_citation_edge(ref_map: ReferenceTypeMap):
    docs = {
        "A": {"references": [ref("B", 3)]},  # 3 = open_citation, căn cứ ban hành
        "B": {"references": [ref("C", 10)]},  # never reached: B is never fetched
    }
    result = expand(["A"], docs.__getitem__, ref_map)
    assert set(result.documents) == {"A"}  # B recorded as an edge target, not fetched
    assert len(result.edges) == 1
    assert result.edges[0].target_id == "B"


def test_cycle_does_not_infinite_loop(ref_map: ReferenceTypeMap):
    docs = {
        "A": {"references": [ref("B", 10)]},
        "B": {"references": [ref("A", 10)]},
    }
    result = expand(["A"], docs.__getitem__, ref_map)
    assert set(result.documents) == {"A", "B"}


def test_circuit_breaker_truncates(ref_map: ReferenceTypeMap):
    # A -> B -> C, chain of genealogy edges, but cap at 2 documents.
    docs = {
        "A": {"references": [ref("B", 10)]},
        "B": {"references": [ref("C", 10)]},
        "C": {"references": []},
    }
    result = expand(["A"], docs.__getitem__, ref_map, max_documents=2)
    assert result.truncated is True
    assert len(result.documents) == 2


def test_unverified_reference_type_fails_loud(ref_map: ReferenceTypeMap):
    docs = {"A": {"references": [ref("B", 999)]}}
    with pytest.raises(UnknownReferenceTypeError):
        expand(["A"], docs.__getitem__, ref_map)


def test_fetch_failure_is_recorded_and_bfs_continues(ref_map: ReferenceTypeMap):
    """A single dangling/unreachable id (network error, removed document —
    expected on a live external site) must not abort the whole crawl."""
    docs = {
        "A": {"references": [ref("BROKEN", 10), ref("C", 10)]},
        "C": {"references": []},
    }

    def fetch(doc_id: str) -> dict:
        if doc_id == "BROKEN":
            raise RuntimeError("400 Bad Request")
        return docs[doc_id]

    result = expand(["A"], fetch, ref_map)

    assert set(result.documents) == {"A", "C"}  # BROKEN skipped, C still reached
    assert result.failed == {"BROKEN": "400 Bad Request"}

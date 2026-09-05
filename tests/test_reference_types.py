import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from legal_crawler.reference_types import EdgeGroup, ReferenceTypeMap, UnknownReferenceTypeError

MAP_JSON = {
    "codes": {
        "3": {"label_vi": "Sửa đổi bổ sung", "group": "genealogy", "verified": True},
        "10": {"label_vi": "Văn bản dẫn chiếu", "group": "open_citation", "verified": True},
        "99": {"label_vi": None, "group": None, "verified": False},
    }
}


@pytest.fixture
def loaded_map(tmp_path: Path) -> ReferenceTypeMap:
    path = tmp_path / "reference_type_map.json"
    path.write_text(json.dumps(MAP_JSON), encoding="utf-8")
    return ReferenceTypeMap.load(path)


def test_verified_codes_classify(loaded_map: ReferenceTypeMap):
    assert loaded_map.classify(3).group is EdgeGroup.GENEALOGY
    assert loaded_map.classify(10).group is EdgeGroup.OPEN_CITATION


def test_is_expandable_follows_genealogy_only(loaded_map: ReferenceTypeMap):
    assert loaded_map.is_expandable(3) is True
    assert loaded_map.is_expandable(10) is False


def test_unverified_code_is_not_loaded(loaded_map: ReferenceTypeMap):
    with pytest.raises(UnknownReferenceTypeError):
        loaded_map.classify(99)


def test_unknown_code_raises_instead_of_defaulting(loaded_map: ReferenceTypeMap):
    with pytest.raises(UnknownReferenceTypeError):
        loaded_map.classify(12345)

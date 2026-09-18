from datetime import date

import pytest

from legal_crawler.temporal.ids import (
    make_document_id,
    make_edge_id,
    make_event_id,
    make_provision_id,
    make_version_id,
)
from legal_crawler.temporal.models import LegalOperation, RelationType


def test_source_ids_are_stable_and_delimiter_safe():
    assert make_document_id(" 7804 ") == "document:7804"
    assert make_document_id("59cf7800-985f-11f1-a7b9-e38443dbc2e1") == (
        "document:59cf7800-985f-11f1-a7b9-e38443dbc2e1"
    )
    assert make_document_id("100/2019/NĐ-CP") == "document:100%2F2019%2FN%C4%90-CP"
    assert make_provision_id("node:article/6") == "provision:node%3Aarticle%2F6"


def test_domain_id_normalization_is_idempotent():
    assert make_document_id(make_document_id("7804")) == "document:7804"
    assert make_provision_id(make_provision_id("article-6")) == "provision:article-6"


def test_version_id_is_deterministic_and_validates_ordinal():
    provision_id = make_provision_id("article-6")
    assert make_version_id(provision_id, 2) == make_version_id(provision_id, 2)
    assert make_version_id(provision_id, 2).endswith(":2")

    with pytest.raises(ValueError, match="starts at 1"):
        make_version_id(provision_id, 0)


def test_event_id_ignores_target_order_and_duplicate_targets():
    common = {
        "source_document_id": "document-b",
        "operation": LegalOperation.AMEND,
        "effective_on": date(2025, 1, 1),
        "target_document_id": "document-a",
        "evidence_text": "Sửa đổi  Khoản 1\nĐiều 6.",
    }
    first = make_event_id(
        target_provision_ids=["clause-1", "article-6"],
        **common,
    )
    reordered = make_event_id(
        target_provision_ids=["article-6", "clause-1", "article-6"],
        **{**common, "evidence_text": "Sửa đổi Khoản 1 Điều 6."},
    )

    assert first == reordered


def test_distinct_event_inputs_produce_distinct_ids():
    first = make_event_id(
        "document-b",
        LegalOperation.AMEND,
        ["article-6"],
        date(2025, 1, 1),
    )
    second = make_event_id(
        "document-b",
        LegalOperation.REPEAL,
        ["article-6"],
        date(2025, 1, 1),
    )
    third = make_event_id(
        "document-b",
        LegalOperation.AMEND,
        ["article-7"],
        date(2025, 1, 1),
    )

    assert len({first, second, third}) == 3


def test_edge_id_includes_relation_and_validity_start():
    base = make_edge_id("document-b", RelationType.AMENDS, "document-a")
    another_relation = make_edge_id(
        "document-b", RelationType.REPEALS, "document-a"
    )
    dated = make_edge_id(
        "document-b", RelationType.AMENDS, "document-a", date(2025, 1, 1)
    )

    assert len({base, another_relation, dated}) == 3


@pytest.mark.parametrize(
    "factory,args",
    [
        (make_document_id, ("",)),
        (make_provision_id, (" ",)),
        (make_version_id, ("", 1)),
        (make_edge_id, ("", RelationType.AMENDS, "target")),
    ],
)
def test_empty_required_identifier_is_rejected(factory, args):
    with pytest.raises(ValueError, match="must not be empty"):
        factory(*args)

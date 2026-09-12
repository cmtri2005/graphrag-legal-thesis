import math
from dataclasses import replace
from datetime import date

import pytest

from legal_crawler.adapters.neo4j import (
    Neo4jCodecError,
    Neo4jEdgeRecord,
    Neo4jNodeRecord,
    decode_edge,
    decode_node,
    encode_edge,
    encode_node,
)
from legal_crawler.temporal import (
    EventStatus,
    ExtractionMethod,
    GraphEdge,
    LegalDocument,
    LegalEvent,
    LegalOperation,
    NodeKind,
    Provenance,
    Provision,
    ProvisionLevel,
    ProvisionVersion,
    RelationType,
    TemporalInterval,
)


def provenance() -> tuple[Provenance, ...]:
    return (
        Provenance(
            "document:source",
            ExtractionMethod.RULE,
            source_provision_id="provision:source:2",
            evidence_text="Khoản 2 Điều 6 được sửa đổi như sau...",
            confidence=0.98,
        ),
    )


def node_models():
    document = LegalDocument(
        "document:law",
        "01/2020/QH",
        "Luật kiểm thử tiếng Việt",
        issued_on=date(2019, 12, 1),
        effective_from=date(2020, 1, 1),
        issuer="Quốc hội",
        rank="Luật",
        raw_status_code="HHL1P",
    )
    provision = Provision(
        "provision:clause-2",
        document.id,
        ProvisionLevel.CLAUSE,
        "Khoản 2",
        "provision:article-6",
        order_index=2,
    )
    version = ProvisionVersion(
        "version:clause-2:1",
        provision.id,
        1,
        "Nội dung có hiệu lực.",
        TemporalInterval(date(2020, 1, 1), date(2024, 7, 1)),
        ended_by_event_id="event:amend",
        provenance=provenance(),
    )
    event = LegalEvent(
        "event:amend",
        LegalOperation.AMEND,
        "document:source",
        document.id,
        date(2024, 7, 1),
        (provision.id,),
        new_text="Nội dung mới.",
        status=EventStatus.VERIFIED,
        provenance=provenance(),
    )
    return document, provision, version, event


@pytest.mark.parametrize("value", node_models())
def test_node_codec_round_trips_authoritative_domain_payload(value):
    record = encode_node(value)

    restored = decode_node(record.parameters(), expected_type=type(value))

    assert restored == value
    assert record.id == value.id
    assert record.kind is value.kind
    assert "schema_version" in record.payload
    assert "Luật kiểm thử tiếng Việt" in encode_node(node_models()[0]).payload


def test_node_codec_projects_only_query_and_index_properties():
    document, provision, version, event = node_models()

    assert encode_node(document).indexed_properties["eff_from"] == "2020-01-01"
    assert encode_node(provision).indexed_properties["document_id"] == document.id
    assert encode_node(version).indexed_properties["eff_to"] == "2024-07-01"
    assert encode_node(event).indexed_properties["resolved_target_ids"] == [
        provision.id
    ]
    assert encode_node(event).indexed_properties["applied"] is False


def test_node_record_copies_properties_and_protects_reserved_keys():
    source = {"title": "Ban đầu"}
    record = Neo4jNodeRecord(
        "document:1",
        NodeKind.DOCUMENT,
        '{"schema_version": 1}',
        source,
    )
    source["title"] = "Đã sửa"

    assert record.indexed_properties["title"] == "Ban đầu"
    with pytest.raises(TypeError):
        record.indexed_properties["title"] = "Không được sửa"
    with pytest.raises(Neo4jCodecError, match="reserved"):
        replace(record, indexed_properties={"id": "other"})


def test_decode_node_rejects_tampered_identity_kind_and_expected_type():
    document, provision, _, _ = node_models()
    encoded = encode_node(document).parameters()

    with pytest.raises(Neo4jCodecError, match="id does not match"):
        decode_node({**encoded, "id": "document:other"})
    with pytest.raises(Neo4jCodecError, match="kind does not match"):
        decode_node({**encoded, "kind": NodeKind.PROVISION.value})
    with pytest.raises(Neo4jCodecError, match="expected Provision"):
        decode_node(encoded, expected_type=Provision)
    with pytest.raises(Neo4jCodecError, match="invalid node payload"):
        decode_node({**encoded, "payload": "not-json"})
    with pytest.raises(TypeError, match="supported temporal graph node"):
        encode_node(provenance()[0])
    assert encode_node(provision).kind is NodeKind.PROVISION


def test_edge_codec_round_trips_temporal_relation_and_provenance():
    edge = GraphEdge(
        "event:amend",
        "document:law",
        RelationType.AMENDS,
        TemporalInterval(date(2024, 7, 1)),
        provenance=provenance(),
        properties={"confidence_band": "verified"},
    )

    record = encode_edge(edge)
    restored = decode_edge(record.parameters())

    assert restored == edge
    assert record.relation == "AMENDS"
    assert record.indexed_properties == {
        "eff_from": "2024-07-01",
        "eff_to": None,
    }


def test_decode_edge_rejects_tampered_id_endpoint_or_relation():
    edge = GraphEdge("a", "b", RelationType.REFERS_TO)
    encoded = encode_edge(edge).parameters()

    with pytest.raises(Neo4jCodecError, match="id does not match"):
        decode_edge({**encoded, "id": "edge:wrong"})
    with pytest.raises(Neo4jCodecError, match="endpoints or relation"):
        decode_edge({**encoded, "source_id": "other"})
    with pytest.raises(Neo4jCodecError, match="endpoints or relation"):
        decode_edge({**encoded, "relation": RelationType.AMENDS.value})


def test_edge_record_rejects_nested_index_property_values():
    with pytest.raises(Neo4jCodecError, match="unsupported list"):
        Neo4jEdgeRecord(
            "edge:1",
            "source",
            "target",
            "AMENDS",
            "payload",
            {"bad": [{"nested": True}]},
        )
    with pytest.raises(Neo4jCodecError, match="non-finite"):
        Neo4jEdgeRecord(
            "edge:1",
            "source",
            "target",
            "AMENDS",
            "payload",
            {"bad": [math.inf]},
        )
    with pytest.raises(Neo4jCodecError, match="one scalar type"):
        Neo4jEdgeRecord(
            "edge:1",
            "source",
            "target",
            "AMENDS",
            "payload",
            {"bad": [1, "1"]},
        )

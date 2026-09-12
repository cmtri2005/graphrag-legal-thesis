import json
from datetime import date

import pytest

from legal_crawler.temporal import (
    SCHEMA_VERSION,
    EventStatus,
    ExtractionMethod,
    GraphEdge,
    InvalidRecordError,
    LegalDocument,
    LegalEvent,
    LegalOperation,
    Provenance,
    Provision,
    ProvisionInsertion,
    ProvisionLevel,
    ProvisionVersion,
    RelationType,
    SerializationError,
    TemporalInterval,
    TextUpdate,
    UnknownRecordTypeError,
    UnsupportedSchemaVersionError,
    dumps,
    from_record,
    loads,
    to_record,
)


def provenance() -> Provenance:
    return Provenance(
        source_document_id="document:02/2024/QH15",
        method=ExtractionMethod.RULE,
        source_provision_id="provision:article-1",
        evidence_text="Khoản 3 Điều 6 được sửa đổi như sau…",
        source_url="https://example.test/văn-bản",
        confidence=0.97,
        details={
            "resolver": "exact_tree_node",
            "candidate_count": 1,
            "reviewed": True,
            "warnings": [],
            "note": None,
        },
    )


def all_domain_models():
    source = provenance()
    interval = TemporalInterval(date(2024, 7, 1), date(2025, 1, 1))
    update = TextUpdate("provision:clause-3", "Nội dung Khoản 3 sau sửa đổi.")
    insertion = ProvisionInsertion(
        provision_id="provision:point-dd",
        level=ProvisionLevel.POINT,
        title="Điểm đ",
        text="Nội dung Điểm đ được bổ sung.",
        parent_id="provision:clause-3",
        after_provision_id="provision:point-d",
        order_index=5,
    )
    return (
        interval,
        source,
        LegalDocument(
            id="document:01/2020/QH14",
            number="01/2020/QH14",
            title="Luật thử nghiệm tiếng Việt",
            issued_on=date(2020, 1, 1),
            effective_from=date(2020, 7, 1),
            effective_to=date(2030, 1, 1),
            issuer="Quốc hội",
            rank="Luật",
            source_url="https://example.test/document/1",
            raw_status_code="Còn hiệu lực một phần",
        ),
        Provision(
            id="provision:clause-3",
            document_id="document:01/2020/QH14",
            level=ProvisionLevel.CLAUSE,
            title="Khoản 3",
            parent_id="provision:article-6",
            order_index=3,
            inserted_after_id="provision:clause-2",
        ),
        ProvisionVersion(
            id="version:provision%3Aclause-3:2",
            provision_id="provision:clause-3",
            ordinal=2,
            text="Nội dung Khoản 3 sau sửa đổi.",
            validity=interval,
            created_by_event_id="event:amend",
            ended_by_event_id="event:replace",
            provenance=(source,),
        ),
        update,
        insertion,
        LegalEvent(
            id="event:supplement",
            operation=LegalOperation.SUPPLEMENT,
            source_document_id="document:02/2024/QH15",
            target_document_id="document:01/2020/QH14",
            effective_on=date(2024, 7, 1),
            target_provision_ids=("provision:clause-3",),
            text_updates=(update,),
            insertions=(insertion,),
            status=EventStatus.VERIFIED,
            provenance=(source,),
        ),
        GraphEdge(
            source_id="event:supplement",
            target_id="provision:clause-3",
            relation=RelationType.SUPPLEMENTS,
            validity=TemporalInterval(date(2024, 7, 1)),
            provenance=(source,),
            properties={
                "direct": True,
                "labels": ["bổ sung", "đã kiểm tra"],
                "source_status": "Còn hiệu lực",
            },
        ),
    )


@pytest.mark.parametrize("model", all_domain_models(), ids=lambda item: type(item).__name__)
def test_every_domain_model_round_trips_through_record_and_json(model):
    record = to_record(model)

    assert record["schema_version"] == SCHEMA_VERSION
    assert record["type"] == type(model).__name__
    assert from_record(record) == model
    assert loads(dumps(model)) == model


def test_json_output_is_deterministic_and_keeps_vietnamese_unicode():
    document = all_domain_models()[2]

    first = dumps(document)
    second = dumps(document)

    assert first == second
    assert "Luật thử nghiệm tiếng Việt" in first
    assert "Quốc hội" in first
    assert "\\u" not in first
    assert json.loads(first)["data"]["raw_status_code"] == "Còn hiệu lực một phần"


def test_nested_model_arrays_are_restored_as_tuples():
    event = all_domain_models()[7]
    restored = loads(dumps(event))

    assert isinstance(restored.target_provision_ids, tuple)
    assert isinstance(restored.text_updates, tuple)
    assert isinstance(restored.insertions, tuple)
    assert isinstance(restored.provenance, tuple)
    assert isinstance(restored.provenance[0].details, dict)


def test_optional_fields_may_be_omitted_and_receive_domain_defaults():
    record = {
        "schema_version": SCHEMA_VERSION,
        "type": "Provenance",
        "data": {
            "source_document_id": "document:source",
            "method": "manual",
        },
    }

    restored = from_record(record)

    assert restored == Provenance(
        source_document_id="document:source",
        method=ExtractionMethod.MANUAL,
    )


@pytest.mark.parametrize("schema_version", [0, 2, 999])
def test_unsupported_schema_version_is_rejected(schema_version):
    record = to_record(TemporalInterval(date(2024, 1, 1)))
    record["schema_version"] = schema_version

    with pytest.raises(UnsupportedSchemaVersionError, match="unsupported"):
        from_record(record)


@pytest.mark.parametrize("schema_version", [True, "1", 1.0, None])
def test_schema_version_must_be_an_integer(schema_version):
    record = to_record(TemporalInterval(date(2024, 1, 1)))
    record["schema_version"] = schema_version

    with pytest.raises(InvalidRecordError, match="must be an integer"):
        from_record(record)


def test_unknown_record_type_and_unknown_fields_are_rejected():
    unknown_type = {
        "schema_version": SCHEMA_VERSION,
        "type": "FutureModel",
        "data": {},
    }
    extra_field = to_record(TemporalInterval(date(2024, 1, 1)))
    extra_field["data"]["silent_new_meaning"] = True

    with pytest.raises(UnknownRecordTypeError, match="FutureModel"):
        from_record(unknown_type)
    with pytest.raises(InvalidRecordError, match="unknown fields"):
        from_record(extra_field)


def test_missing_field_invalid_date_and_invalid_enum_have_contextual_errors():
    missing = to_record(TemporalInterval(date(2024, 1, 1)))
    del missing["data"]["start"]
    invalid_date = to_record(TemporalInterval(date(2024, 1, 1)))
    invalid_date["data"]["start"] = "01/01/2024"
    invalid_enum = to_record(all_domain_models()[3])
    invalid_enum["data"]["level"] = "Paragraph"

    with pytest.raises(InvalidRecordError, match="missing fields: start"):
        from_record(missing)
    with pytest.raises(InvalidRecordError, match="ISO 8601"):
        from_record(invalid_date)
    with pytest.raises(InvalidRecordError, match="Provision.level must be one of"):
        from_record(invalid_enum)


def test_decoder_rejects_ambiguous_json_and_non_json_metadata():
    duplicate_key = (
        '{"schema_version":1,"schema_version":1,'
        '"type":"TemporalInterval","data":{"start":"2024-01-01"}}'
    )
    edge = all_domain_models()[-1]
    invalid_properties = GraphEdge(
        source_id=edge.source_id,
        target_id=edge.target_id,
        relation=edge.relation,
        properties={"not_json": date(2024, 1, 1)},
    )

    with pytest.raises(InvalidRecordError, match="duplicate JSON object key"):
        loads(duplicate_key)
    with pytest.raises(SerializationError, match="non-JSON value"):
        to_record(invalid_properties)


def test_numeric_booleans_and_non_finite_values_are_rejected():
    version = to_record(all_domain_models()[4])
    version["data"]["ordinal"] = True
    non_finite = to_record(provenance())
    non_finite["data"]["details"] = {"score": float("inf")}

    with pytest.raises(InvalidRecordError, match="ordinal must be an integer"):
        from_record(version)
    with pytest.raises(SerializationError, match="NaN or infinity"):
        from_record(non_finite)


def test_invalid_json_and_non_object_root_are_rejected_cleanly():
    with pytest.raises(InvalidRecordError, match="invalid JSON"):
        loads("{")
    with pytest.raises(InvalidRecordError, match="JSON root must be an object"):
        loads("[]")


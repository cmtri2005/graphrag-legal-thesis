import json
from copy import deepcopy
from datetime import date

import pytest

from legal_crawler.query import (
    QUERY_SCHEMA_VERSION,
    AnswerClaim,
    AnswerResult,
    AnswerStatus,
    Citation,
    CitationLevel,
    GraphTraversalStep,
    InvalidQueryRecordError,
    QuerySerializationError,
    RetrievedEvidence,
    RetrievalMethod,
    RetrievalSignal,
    TemporalQuery,
    TemporalResolution,
    UnknownQueryRecordTypeError,
    UnsupportedQuerySchemaVersionError,
    VerificationDecision,
    VerificationIssue,
    VerificationIssueCode,
    VerificationResult,
    VerificationSeverity,
    dumps,
    from_record,
    loads,
    to_record,
)
from legal_crawler.temporal import (
    SCHEMA_VERSION as TEMPORAL_SCHEMA_VERSION,
    EventStatus,
    ExtractionMethod,
    LegalEvent,
    LegalOperation,
    Provenance,
    Provision,
    ProvisionLevel,
    ProvisionVersion,
    RelationType,
    SnapshotResult,
    TemporalInterval,
    ValidityResult,
)


AT = date(2024, 7, 1)


def all_query_artifacts():
    provenance = Provenance(
        "document:amending-law",
        ExtractionMethod.RULE,
        source_provision_id="provision:source-article",
        evidence_text="Khoản 3 Điều 6 được sửa đổi như sau…",
        source_url="https://example.test/văn-bản",
        confidence=0.97,
        details={"reviewed": True, "candidate_count": 1},
    )
    event = LegalEvent(
        "event:amend",
        LegalOperation.AMEND,
        "document:amending-law",
        "document:law",
        AT,
        target_provision_ids=("provision:clause-3",),
        status=EventStatus.VERIFIED,
        provenance=(provenance,),
    )
    provision = Provision(
        "provision:clause-3",
        "document:law",
        ProvisionLevel.CLAUSE,
        "Khoản 3 Điều 6",
        "provision:article-6",
        order_index=3,
    )
    version = ProvisionVersion(
        "version:clause-3:2",
        provision.id,
        2,
        "Nội dung Khoản 3 sau sửa đổi.",
        TemporalInterval(AT),
        created_by_event_id=event.id,
        provenance=(provenance,),
    )
    validity = ValidityResult(provision.id, AT, True, version=version)
    snapshot = SnapshotResult(
        provision,
        AT,
        validity,
        version=version,
        created_by_event=event,
        provenance=(provenance,),
        warnings=("fixture_verified",),
    )
    query = TemporalQuery(
        "query:1",
        "Khoản 3 Điều 6 có hiệu lực vào tháng 7 năm 2024 không?",
        AT,
        TemporalResolution.INFERRED,
        temporal_expression="tháng 7 năm 2024",
        temporal_confidence=0.96,
        document_ids=("document:law",),
        levels=frozenset({ProvisionLevel.ARTICLE, ProvisionLevel.CLAUSE}),
    )
    signal = RetrievalSignal(RetrievalMethod.DENSE, 0.84, rank=1)
    graph_step = GraphTraversalStep(
        "edge:amends",
        "event:amend",
        RelationType.AMENDS,
        provision.id,
    )
    evidence = RetrievedEvidence(
        "evidence:1",
        query.id,
        snapshot,
        (
            signal,
            RetrievalSignal(RetrievalMethod.GRAPH, 0.72, rank=1),
            RetrievalSignal(RetrievalMethod.RERANK, 0.93, rank=1),
        ),
        rank=1,
        final_score=0.93,
        graph_path=(graph_step,),
    )
    citation = Citation(
        "citation:1",
        evidence.id,
        provision.document_id,
        CitationLevel.CLAUSE,
        "Khoản 3 Điều 6",
        provision.id,
        version.id,
        supporting_text="Nội dung Khoản 3 sau sửa đổi.",
    )
    claim = AnswerClaim(
        "claim:1",
        "Khoản 3 Điều 6 có hiệu lực tại thời điểm được hỏi.",
        (citation.id,),
    )
    issue = VerificationIssue(
        VerificationIssueCode.CITATION_TEXT_UNSUPPORTED,
        VerificationSeverity.WARNING,
        "Trích đoạn cần được kiểm tra thêm nếu dùng cho kết luận khác.",
        claim_id=claim.id,
        citation_id=citation.id,
        evidence_id=evidence.id,
    )
    verification = VerificationResult(
        query.id,
        VerificationDecision.PASSED,
        issues=(issue,),
        verified_evidence_ids=(evidence.id,),
        verified_citation_ids=(citation.id,),
    )
    answer = AnswerResult(
        "answer:1",
        query,
        "Khoản 3 Điều 6 có hiệu lực tại thời điểm tháng 7 năm 2024.",
        AnswerStatus.ANSWERED,
        (evidence,),
        (citation,),
        (claim,),
        verification,
    )
    return (
        query,
        signal,
        graph_step,
        evidence,
        citation,
        claim,
        issue,
        verification,
        answer,
    )


@pytest.mark.parametrize(
    "artifact", all_query_artifacts(), ids=lambda item: type(item).__name__
)
def test_every_query_artifact_round_trips_through_record_and_json(artifact):
    record = to_record(artifact)

    assert record["schema_version"] == QUERY_SCHEMA_VERSION
    assert record["type"] == type(artifact).__name__
    assert from_record(record) == artifact
    assert loads(dumps(artifact)) == artifact


def test_answer_round_trip_preserves_nested_types_and_order():
    restored = loads(dumps(all_query_artifacts()[-1]))

    assert isinstance(restored, AnswerResult)
    assert isinstance(restored.query.levels, frozenset)
    assert isinstance(restored.evidence, tuple)
    assert isinstance(restored.evidence[0].snapshot, SnapshotResult)
    assert isinstance(restored.evidence[0].snapshot.validity, ValidityResult)
    assert isinstance(restored.evidence[0].snapshot.provision, Provision)
    assert isinstance(restored.evidence[0].snapshot.version, ProvisionVersion)
    assert isinstance(restored.evidence[0].snapshot.created_by_event, LegalEvent)
    assert restored.evidence[0].snapshot.at == AT
    assert restored.evidence[0].signals[0].method is RetrievalMethod.DENSE
    assert restored.citations[0].supporting_text == "Nội dung Khoản 3 sau sửa đổi."
    assert (
        restored.verification.issues[0].code
        is VerificationIssueCode.CITATION_TEXT_UNSUPPORTED
    )


def test_query_and_nested_temporal_records_keep_independent_schema_versions():
    record = to_record(all_query_artifacts()[3])
    snapshot = record["data"]["snapshot"]

    assert record["schema_version"] == QUERY_SCHEMA_VERSION
    assert snapshot["provision"]["schema_version"] == TEMPORAL_SCHEMA_VERSION
    assert snapshot["version"]["schema_version"] == TEMPORAL_SCHEMA_VERSION
    assert snapshot["created_by_event"]["schema_version"] == TEMPORAL_SCHEMA_VERSION
    assert snapshot["provenance"][0]["schema_version"] == TEMPORAL_SCHEMA_VERSION


def test_json_is_deterministic_canonical_and_preserves_vietnamese_unicode():
    answer = all_query_artifacts()[-1]

    compact = dumps(answer)
    pretty = dumps(answer, indent=2)

    assert compact == dumps(answer)
    assert "Khoản 3 Điều 6" in compact
    assert "\\u" not in compact
    assert "\n" not in compact
    assert "\n" in pretty
    assert json.loads(compact)["data"]["query"]["at"] == "2024-07-01"


def test_frozenset_is_serialized_in_deterministic_enum_order():
    record = to_record(all_query_artifacts()[0])

    assert record["data"]["levels"] == ["Article", "Clause"]


@pytest.mark.parametrize("schema_version", (0, 2, 999))
def test_unsupported_query_schema_version_is_rejected(schema_version):
    record = to_record(all_query_artifacts()[0])
    record["schema_version"] = schema_version

    with pytest.raises(UnsupportedQuerySchemaVersionError, match="unsupported"):
        from_record(record)


@pytest.mark.parametrize("schema_version", (True, "1", 1.0, None))
def test_query_schema_version_must_be_an_integer(schema_version):
    record = to_record(all_query_artifacts()[0])
    record["schema_version"] = schema_version

    with pytest.raises(InvalidQueryRecordError, match="must be an integer"):
        from_record(record)


def test_unknown_type_and_unknown_envelope_or_data_fields_are_rejected():
    unknown_type = {
        "schema_version": QUERY_SCHEMA_VERSION,
        "type": "FutureArtifact",
        "data": {},
    }
    unknown_envelope = to_record(all_query_artifacts()[0])
    unknown_envelope["silent"] = True
    unknown_data = to_record(all_query_artifacts()[0])
    unknown_data["data"]["silent"] = True

    with pytest.raises(UnknownQueryRecordTypeError, match="FutureArtifact"):
        from_record(unknown_type)
    with pytest.raises(InvalidQueryRecordError, match="record has unknown fields"):
        from_record(unknown_envelope)
    with pytest.raises(
        InvalidQueryRecordError, match="TemporalQuery has unknown fields"
    ):
        from_record(unknown_data)


def test_missing_required_field_and_wrong_container_type_are_rejected():
    missing = to_record(all_query_artifacts()[0])
    del missing["data"]["at"]
    wrong_array = to_record(all_query_artifacts()[0])
    wrong_array["data"]["document_ids"] = "document:law"

    with pytest.raises(InvalidQueryRecordError, match="missing fields: at"):
        from_record(missing)
    with pytest.raises(InvalidQueryRecordError, match="must be an array"):
        from_record(wrong_array)


def test_invalid_date_enum_boolean_and_integer_have_contextual_errors():
    invalid_date = to_record(all_query_artifacts()[0])
    invalid_date["data"]["at"] = "01/07/2024"
    invalid_enum = to_record(all_query_artifacts()[0])
    invalid_enum["data"]["temporal_resolution"] = "guessed"
    invalid_boolean = to_record(all_query_artifacts()[3])
    invalid_boolean["data"]["snapshot"]["validity"]["valid"] = 1
    invalid_rank = to_record(all_query_artifacts()[1])
    invalid_rank["data"]["rank"] = True

    with pytest.raises(InvalidQueryRecordError, match="ISO 8601"):
        from_record(invalid_date)
    with pytest.raises(InvalidQueryRecordError, match="must be one of"):
        from_record(invalid_enum)
    with pytest.raises(InvalidQueryRecordError, match="must be a boolean"):
        from_record(invalid_boolean)
    with pytest.raises(InvalidQueryRecordError, match="must be an integer"):
        from_record(invalid_rank)


def test_duplicate_query_filters_are_rejected_instead_of_silently_collapsed():
    duplicate_levels = to_record(all_query_artifacts()[0])
    duplicate_levels["data"]["levels"] = ["Clause", "Clause"]
    duplicate_documents = to_record(all_query_artifacts()[0])
    duplicate_documents["data"]["document_ids"] = ["document:law", "document:law"]

    with pytest.raises(InvalidQueryRecordError, match="duplicates"):
        from_record(duplicate_levels)
    with pytest.raises(InvalidQueryRecordError, match="duplicates"):
        from_record(duplicate_documents)


def test_nested_temporal_type_and_schema_errors_are_wrapped_with_context():
    wrong_type = to_record(all_query_artifacts()[3])
    wrong_type["data"]["snapshot"]["provision"] = wrong_type["data"][
        "snapshot"
    ]["version"]
    future_temporal = to_record(all_query_artifacts()[3])
    future_temporal["data"]["snapshot"]["version"]["schema_version"] = 999

    with pytest.raises(InvalidQueryRecordError, match="must contain a Provision"):
        from_record(wrong_type)
    with pytest.raises(InvalidQueryRecordError, match="unsupported schema_version"):
        from_record(future_temporal)


def test_corrupt_snapshot_date_or_provenance_is_rejected():
    wrong_date = to_record(all_query_artifacts()[3])
    wrong_date["data"]["snapshot"]["validity"]["at"] = "2024-07-02"
    wrong_provenance = to_record(all_query_artifacts()[3])
    wrong_provenance["data"]["snapshot"]["provenance"] = []

    with pytest.raises(InvalidQueryRecordError, match="date must match"):
        from_record(wrong_date)
    with pytest.raises(InvalidQueryRecordError, match="provenance"):
        from_record(wrong_provenance)


def test_corrupt_answer_references_and_false_passed_citation_are_rejected():
    missing_evidence = to_record(all_query_artifacts()[-1])
    missing_evidence["data"]["citations"][0]["evidence_id"] = "evidence:missing"
    wrong_version = to_record(all_query_artifacts()[-1])
    wrong_version["data"]["citations"][0]["version_id"] = "version:wrong"

    with pytest.raises(InvalidQueryRecordError, match="unknown evidence"):
        from_record(missing_evidence)
    with pytest.raises(InvalidQueryRecordError, match="evidence version"):
        from_record(wrong_version)


def test_duplicate_json_keys_non_finite_numbers_and_invalid_json_are_rejected():
    duplicate = (
        '{"schema_version":1,"schema_version":1,'
        '"type":"TemporalQuery","data":{}}'
    )
    non_finite_json = (
        '{"schema_version":1,"type":"RetrievalSignal",'
        '"data":{"method":"dense","score":NaN,"rank":1}}'
    )

    with pytest.raises(InvalidQueryRecordError, match="duplicate JSON object key"):
        loads(duplicate)
    with pytest.raises(InvalidQueryRecordError, match="not finite"):
        loads(non_finite_json)
    with pytest.raises(InvalidQueryRecordError, match="invalid JSON"):
        loads("{")
    with pytest.raises(InvalidQueryRecordError, match="JSON root must be an object"):
        loads("[]")


def test_non_finite_record_number_is_rejected():
    record = to_record(all_query_artifacts()[1])
    record["data"]["score"] = float("inf")

    with pytest.raises(InvalidQueryRecordError, match="must be finite"):
        from_record(record)


def test_unresolved_query_round_trip_keeps_at_none_and_review_state():
    query = TemporalQuery(
        "query:unresolved",
        "Quy định này còn hiệu lực không?",
        None,
        TemporalResolution.UNRESOLVED,
        temporal_expression="còn hiệu lực",
    )

    restored = loads(dumps(query))

    assert restored == query
    assert restored.at is None
    assert restored.temporal_resolution is TemporalResolution.UNRESOLVED


def test_unsupported_artifact_and_non_text_payload_fail_cleanly():
    with pytest.raises(QuerySerializationError, match="unsupported"):
        to_record(object())
    with pytest.raises(InvalidQueryRecordError, match="must be text"):
        loads(b"{}")


def test_record_input_is_not_mutated_during_decoding():
    record = to_record(all_query_artifacts()[-1])
    original = deepcopy(record)

    from_record(record)

    assert record == original

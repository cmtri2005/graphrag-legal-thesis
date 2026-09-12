from dataclasses import replace
from datetime import date

import pytest

from legal_crawler.adapters.milvus import (
    EMBEDDING_SCHEMA_VERSION,
    OPEN_END_ORDINAL,
    MilvusCodecError,
    decode_embedding,
    encode_embedding,
)
from legal_crawler.ports import VersionEmbedding
from legal_crawler.temporal import (
    ExtractionMethod,
    Provenance,
    ProvisionLevel,
    TemporalInterval,
)


def embedding() -> VersionEmbedding:
    return VersionEmbedding(
        id="embedding:article-1:model-a",
        version_id="version:article-1:1",
        provision_id="provision:article-1",
        document_id="document:law",
        model="model-a",
        vector=(0.25, -0.5, 0.75),
        validity=TemporalInterval(date(2020, 1, 1)),
        level=ProvisionLevel.ARTICLE,
        provenance=(
            Provenance(
                "document:law",
                ExtractionMethod.SOURCE_METADATA,
                evidence_text="Điều 1. Phạm vi điều chỉnh",
                details={"language": "vi"},
            ),
        ),
        metadata={"chunk": 0, "labels": ["pháp luật", "thời gian"]},
    )


def test_milvus_codec_round_trips_authoritative_embedding_payload():
    value = embedding()

    record = encode_embedding(value)
    restored = decode_embedding(record.fields())

    assert restored == value
    assert record.eff_from == date(2020, 1, 1).toordinal()
    assert record.eff_to == OPEN_END_ORDINAL
    assert record.schema_version == EMBEDDING_SCHEMA_VERSION
    assert record.payload["data"]["metadata"]["labels"][0] == "pháp luật"


def test_milvus_codec_uses_closed_half_open_end_projection():
    value = replace(
        embedding(),
        validity=TemporalInterval(date(2020, 1, 1), date(2024, 7, 1)),
    )

    record = encode_embedding(value)

    assert record.eff_to == date(2024, 7, 1).toordinal()
    assert decode_embedding(record.fields()) == value


@pytest.mark.parametrize(
    ("field", "replacement"),
    (
        ("id", "embedding:tampered"),
        ("version_id", "version:tampered"),
        ("model", "model-tampered"),
        ("eff_from", 1),
        ("eff_to", 2),
        ("schema_version", 99),
    ),
)
def test_milvus_codec_rejects_tampered_filter_projection(field, replacement):
    fields = encode_embedding(embedding()).fields()
    fields[field] = replacement

    with pytest.raises(MilvusCodecError, match=field):
        decode_embedding(fields)


def test_milvus_codec_rejects_non_json_metadata_and_payload_shape():
    with pytest.raises(MilvusCodecError, match="JSON-compatible"):
        encode_embedding(replace(embedding(), metadata={"bad": object()}))

    fields = encode_embedding(embedding()).fields()
    fields["payload"] = {"schema_version": 1}
    with pytest.raises(MilvusCodecError, match="envelope"):
        decode_embedding(fields)

    with pytest.raises(MilvusCodecError, match="65536 UTF-8 bytes"):
        encode_embedding(replace(embedding(), metadata={"large": "x" * 70_000}))


def test_milvus_codec_allows_float32_rounding_but_rejects_vector_tampering():
    fields = encode_embedding(embedding()).fields()
    fields["vector"] = [0.25000001, -0.5, 0.75]
    assert decode_embedding(fields) == embedding()

    fields["vector"] = [0.9, -0.5, 0.75]
    with pytest.raises(MilvusCodecError, match="vector does not match"):
        decode_embedding(fields)

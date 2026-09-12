"""Opt-in integration contract against a local Milvus Lite database."""
import os
from dataclasses import replace
from datetime import date

import pytest

from legal_crawler.adapters.milvus import MilvusVectorRepository
from legal_crawler.ports import VectorSearchQuery, VersionEmbedding
from legal_crawler.temporal import ProvisionLevel, TemporalInterval

RUN_INTEGRATION = os.environ.get("RUN_MILVUS_LITE_INTEGRATION") == "1"

pytestmark = pytest.mark.skipif(
    not RUN_INTEGRATION,
    reason="set RUN_MILVUS_LITE_INTEGRATION=1 to run Milvus Lite integration",
)

if RUN_INTEGRATION:
    pytest.importorskip("pymilvus")
    pytest.importorskip("milvus_lite")


def test_milvus_lite_crud_and_half_open_search(tmp_path):
    repository = MilvusVectorRepository.from_uri(
        str(tmp_path / "legal-vectors.db"),
        "legal_versions",
        "model_a",
        3,
    )
    record = VersionEmbedding(
        "embedding_article_1",
        "version_article_1_1",
        "provision_article_1",
        "document_law",
        "model_a",
        (1.0, 0.0, 0.0),
        TemporalInterval(date(2020, 1, 1)),
        ProvisionLevel.ARTICLE,
    )
    query = VectorSearchQuery(
        (1.0, 0.0, 0.0),
        date(2024, 7, 1),
        "model_a",
        document_ids=("document_law",),
        levels=frozenset({ProvisionLevel.ARTICLE}),
    )
    try:
        assert repository.put(record).created
        assert not repository.put(record).created
        assert repository.get(record.id) == record
        assert repository.search(query)[0].record == record

        closed = replace(
            record,
            validity=TemporalInterval(date(2020, 1, 1), date(2024, 7, 1)),
        )
        assert repository.delete(record.id)
        assert repository.put(closed).created
        assert repository.search(query) == ()
    finally:
        repository.close()

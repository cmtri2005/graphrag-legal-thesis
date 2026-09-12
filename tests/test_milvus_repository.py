import math
import json
import re
from copy import deepcopy
from dataclasses import dataclass, field, replace
from datetime import date

import pytest

from legal_crawler.adapters.milvus import (
    COLLECTION_FIELDS,
    MilvusVectorRepository,
    initialize_collection,
)
from legal_crawler.ports import (
    RepositoryConflictError,
    RepositoryError,
    RepositoryIntegrityError,
    VectorRepository,
    VectorSearchQuery,
    VersionEmbedding,
    WriteDisposition,
)
from legal_crawler.temporal import ProvisionLevel, TemporalInterval


class FakeDataType:
    VARCHAR = "VARCHAR"
    FLOAT_VECTOR = "FLOAT_VECTOR"
    JSON = "JSON"
    INT64 = "INT64"
    INT16 = "INT16"


@dataclass
class FakeSchema:
    fields: list[dict] = field(default_factory=list)

    def add_field(self, **options):
        self.fields.append(options)


@dataclass
class FakeIndexes:
    indexes: list[dict] = field(default_factory=list)

    def add_index(self, **options):
        self.indexes.append(options)


class FakeMilvusClient:
    def __init__(self):
        self.rows = {}
        self.collection_exists = False
        self.schema = None
        self.indexes = None
        self.create_options = None
        self.last_search = None
        self.closed = False
        self.flush_count = 0
        self.fail_operation = None

    def has_collection(self, *, collection_name):
        self._fail("has_collection")
        return self.collection_exists

    def create_schema(self, **options):
        assert options == {"auto_id": False, "enable_dynamic_field": False}
        self.schema = FakeSchema()
        return self.schema

    def prepare_index_params(self):
        self.indexes = FakeIndexes()
        return self.indexes

    def create_collection(self, **options):
        self._fail("create_collection")
        self.collection_exists = True
        self.create_options = options

    def describe_collection(self, *, collection_name):
        self._fail("describe_collection")
        fields = []
        for item in self.schema.fields:
            description = {
                "name": item["field_name"],
                "type": item["datatype"],
                "is_primary": item.get("is_primary", False),
                "params": {},
            }
            if item["field_name"] == "vector":
                description["params"] = {"dim": str(item["dim"])}
            fields.append(description)
        return {"fields": fields}

    def insert(self, *, collection_name, data):
        self._fail("insert")
        duplicate = next((item["id"] for item in data if item["id"] in self.rows), None)
        if duplicate:
            raise RuntimeError(f"duplicate primary key: {duplicate}")
        for item in data:
            self.rows[item["id"]] = deepcopy(item)
        return {"insert_count": len(data)}

    def get(self, *, collection_name, ids, output_fields, **kwargs):
        self._fail("get")
        return [
            {
                name: deepcopy(self.rows[identifier][name])
                for name in output_fields
            }
            for identifier in ids
            if identifier in self.rows
        ]

    def delete(self, *, collection_name, ids):
        self._fail("delete")
        count = 0
        for identifier in ids:
            count += self.rows.pop(identifier, None) is not None
        return {"delete_count": count}

    def search(self, **options):
        self._fail("search")
        self.last_search = deepcopy(options)
        expression = options["filter"]
        model = json.loads(
            expression.split("model == ", 1)[1].split(" && ", 1)[0]
        )
        at = int(re.search(r"eff_from <= (\d+)", expression).group(1))
        document_match = re.search(r"document_id in (\[[^]]*\])", expression)
        level_match = re.search(r"level in (\[[^]]*\])", expression)
        document_ids = json.loads(document_match.group(1)) if document_match else []
        levels = json.loads(level_match.group(1)) if level_match else []
        candidates = [
            row
            for row in self.rows.values()
            if row["model"] == model
            and row["eff_from"] <= at < row["eff_to"]
            and (
                not document_ids or row["document_id"] in document_ids
            )
            and (not levels or row["level"] in levels)
        ]
        query_vector = options["data"][0]
        hits = []
        for row in reversed(candidates):
            entity = {
                name: deepcopy(row[name]) for name in options["output_fields"]
            }
            hits.append(
                {
                    "id": row["id"],
                    "distance": _cosine(query_vector, row["vector"]),
                    "entity": entity,
                }
            )
        hits.sort(key=lambda item: item["distance"], reverse=True)
        return [hits[: options["limit"]]]

    def flush(self, *, collection_name):
        self._fail("flush")
        self.flush_count += 1
        return {"flushed": [collection_name]}

    def close(self):
        self._fail("close")
        self.closed = True

    def _fail(self, operation):
        if self.fail_operation == operation:
            raise RuntimeError(f"{operation} unavailable")


def _cosine(left, right):
    return sum(a * b for a, b in zip(left, right)) / (
        math.sqrt(sum(item * item for item in left))
        * math.sqrt(sum(item * item for item in right))
    )


def embedding(
    identifier,
    vector=(1.0, 0.0, 0.0),
    *,
    document_id="document:law",
    level=ProvisionLevel.ARTICLE,
    start=date(2020, 1, 1),
    end=None,
):
    return VersionEmbedding(
        identifier,
        f"version:{identifier}",
        f"provision:{identifier}",
        document_id,
        "model-a",
        vector,
        TemporalInterval(start, end),
        level,
    )


def query(**changes):
    values = {
        "vector": (1.0, 0.0, 0.0),
        "at": date(2024, 1, 1),
        "model": "model-a",
    }
    values.update(changes)
    return VectorSearchQuery(**values)


@pytest.fixture
def client():
    return FakeMilvusClient()


@pytest.fixture
def repository(client):
    value = MilvusVectorRepository(client, "legal_versions", "model-a", 3)
    value.initialize(data_type=FakeDataType)
    return value


def test_collection_initialization_builds_static_schema_cosine_index_and_is_idempotent(client):
    created = initialize_collection(
        client,
        "legal_versions",
        3,
        data_type=FakeDataType,
    )

    assert created
    assert {item["field_name"] for item in client.schema.fields} == set(
        COLLECTION_FIELDS
    )
    assert client.indexes.indexes == [
        {
            "field_name": "vector",
            "index_type": "AUTOINDEX",
            "metric_type": "COSINE",
        }
    ]
    assert client.create_options["consistency_level"] == "Strong"
    assert not initialize_collection(
        client,
        "legal_versions",
        3,
        data_type=FakeDataType,
    )


def test_collection_initialization_rejects_incompatible_existing_dimension(client):
    initialize_collection(client, "legal_versions", 3, data_type=FakeDataType)

    with pytest.raises(RepositoryIntegrityError, match="dimension"):
        initialize_collection(
            client,
            "legal_versions",
            4,
            data_type=FakeDataType,
        )


@pytest.mark.parametrize("name", ("", "1_invalid", "invalid-name", "x" * 256))
def test_collection_initialization_rejects_invalid_resource_names(client, name):
    with pytest.raises(ValueError, match="collection name"):
        initialize_collection(client, name, 3, data_type=FakeDataType)


def test_milvus_repository_satisfies_port_idempotency_conflict_and_delete(
    repository,
    client,
):
    record = embedding("embedding:a")

    assert isinstance(repository, VectorRepository)
    assert repository.put(record).disposition is WriteDisposition.CREATED
    assert repository.put(record).disposition is WriteDisposition.UNCHANGED
    assert repository.get_many((record.id, "missing")) == {record.id: record}
    with pytest.raises(RepositoryConflictError):
        repository.put(replace(record, metadata={"changed": True}))
    assert repository.delete(record.id)
    assert client.flush_count == 1
    assert not repository.delete(record.id)


def test_milvus_batch_preflight_prevents_partial_writes(repository):
    valid = embedding("embedding:valid")
    invalid = replace(
        embedding("embedding:invalid"),
        vector=(1.0, 0.0, 0.0, 0.0),
    )

    with pytest.raises(RepositoryIntegrityError, match="dimension"):
        repository.put_many((valid, invalid))
    assert repository.get(valid.id) is None

    repository.put(valid)
    with pytest.raises(RepositoryConflictError):
        repository.put_many(
            (
                embedding("embedding:new"),
                replace(valid, metadata={"changed": True}),
            )
        )
    assert repository.get("embedding:new") is None


def test_milvus_search_pushes_temporal_document_and_level_filters(repository, client):
    expected = embedding("embedding:b")
    same_score = embedding("embedding:a")
    repository.put_many(
        (
            expected,
            same_score,
            embedding("embedding:expired", end=date(2024, 1, 1)),
            embedding("embedding:other", document_id="document:other"),
            embedding("embedding:clause", level=ProvisionLevel.CLAUSE),
        )
    )

    matches = repository.search(
        query(
            document_ids=("document:law",),
            levels=frozenset({ProvisionLevel.ARTICLE}),
            limit=2,
        )
    )

    assert tuple(item.record.id for item in matches) == (
        "embedding:a",
        "embedding:b",
    )
    assert all(item.score == pytest.approx(1.0) for item in matches)
    expression = client.last_search["filter"]
    assert f"eff_from <= {date(2024, 1, 1).toordinal()}" in expression
    assert f"eff_to > {date(2024, 1, 1).toordinal()}" in expression
    assert 'model == "model-a"' in expression
    assert 'document_id in ["document:law"]' in expression
    assert 'level in ["Article"]' in expression
    assert "filter_params" not in client.last_search


def test_milvus_filter_literals_escape_model_and_document_values(client):
    model = 'model"quoted'
    document_id = 'document"quoted'
    repository = MilvusVectorRepository(client, "legal_versions", model, 3)
    repository.initialize(data_type=FakeDataType)
    record = replace(
        embedding("embedding:quoted", document_id=document_id),
        model=model,
    )
    repository.put(record)

    matches = repository.search(
        VectorSearchQuery(
            (1.0, 0.0, 0.0),
            date(2024, 1, 1),
            model,
            document_ids=(document_id,),
        )
    )

    assert matches[0].record == record
    assert 'model == "model\\"quoted"' in client.last_search["filter"]
    assert 'document_id in ["document\\"quoted"]' in client.last_search["filter"]


def test_delete_then_put_rebuilds_a_closed_version_embedding(repository):
    current = embedding("embedding:a")
    repository.put(current)
    closed = replace(
        current,
        validity=TemporalInterval(date(2020, 1, 1), date(2024, 7, 1)),
    )

    assert repository.delete(current.id)
    assert repository.put(closed).created
    assert repository.get(current.id) == closed


def test_repository_rejects_model_dimension_and_backend_failures(repository, client):
    with pytest.raises(RepositoryIntegrityError, match="configured for model"):
        repository.search(query(model="model-b"))
    with pytest.raises(RepositoryIntegrityError, match="dimension"):
        repository.search(query(vector=(1.0, 0.0)))

    client.fail_operation = "search"
    with pytest.raises(RepositoryError, match="Milvus search failed"):
        repository.search(query())


def test_search_fails_loudly_when_backend_ignores_temporal_filter(repository, client):
    expired = embedding("embedding:expired", end=date(2024, 1, 1))
    repository.put(expired)

    def invalid_search(**options):
        row = client.rows[expired.id]
        entity = {
            name: deepcopy(row[name]) for name in options["output_fields"]
        }
        return [[{"id": expired.id, "distance": 1.0, "entity": entity}]]

    client.search = invalid_search
    with pytest.raises(RepositoryIntegrityError, match="temporally invalid"):
        repository.search(query())


def test_repository_close_delegates_to_client(repository, client):
    repository.close()
    assert client.closed

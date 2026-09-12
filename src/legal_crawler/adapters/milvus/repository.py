"""Milvus implementation of version-aware temporal vector storage."""
from __future__ import annotations

import json
import math
from collections.abc import Iterable, Mapping, Sequence
from typing import Any

from legal_crawler.ports import (
    BatchWriteResult,
    RepositoryConflictError,
    RepositoryError,
    RepositoryIntegrityError,
    VectorMatch,
    VectorSearchQuery,
    VersionEmbedding,
    WriteDisposition,
    WriteResult,
)

from .codec import decode_embedding, encode_embedding
from .schema import (
    COLLECTION_FIELDS,
    MilvusDependencyError,
    initialize_collection,
    validate_collection_config,
)

READ_OUTPUT_FIELDS = tuple(field for field in COLLECTION_FIELDS if field != "vector")
SEARCH_OUTPUT_FIELDS = READ_OUTPUT_FIELDS


class MilvusVectorRepository:
    """One collection dedicated to a single embedding model and dimension."""

    def __init__(
        self,
        client: object,
        collection_name: str,
        model: str,
        dimension: int,
    ) -> None:
        validate_collection_config(collection_name, dimension)
        _required_text(model, "embedding model")
        if len(model.encode("utf-8")) > 512:
            raise ValueError("embedding model exceeds 512 UTF-8 bytes")
        for method in ("get", "insert", "delete", "flush", "search", "close"):
            _method(client, method)
        self._client = client
        self.collection_name = collection_name
        self.model = model
        self.dimension = dimension

    @classmethod
    def from_uri(
        cls,
        uri: str,
        collection_name: str,
        model: str,
        dimension: int,
        *,
        token: str | None = None,
        database: str | None = None,
        initialize: bool = True,
    ) -> "MilvusVectorRepository":
        """Build the official client lazily and optionally ensure its schema."""
        try:
            from pymilvus import MilvusClient
        except ImportError as exc:
            raise MilvusDependencyError(
                "install the 'milvus' project extra to use Milvus storage"
            ) from exc
        options: dict[str, Any] = {"uri": uri}
        if token is not None:
            options["token"] = token
        if database is not None:
            options["db_name"] = database
        repository = cls(
            MilvusClient(**options),
            collection_name,
            model,
            dimension,
        )
        if initialize:
            try:
                repository.initialize()
            except BaseException:
                try:
                    repository.close()
                except Exception:
                    pass
                raise
        return repository

    def initialize(self, *, data_type: object | None = None) -> bool:
        return initialize_collection(
            self._client,
            self.collection_name,
            self.dimension,
            data_type=data_type,
        )

    def get(self, embedding_id: str) -> VersionEmbedding | None:
        found = self.get_many((_required_text(embedding_id, "embedding id"),))
        return found.get(embedding_id)

    def get_many(
        self,
        embedding_ids: Sequence[str],
    ) -> dict[str, VersionEmbedding]:
        ids = _ids(embedding_ids)
        if not ids:
            return {}
        rows = self._call(
            "get",
            collection_name=self.collection_name,
            ids=list(ids),
            output_fields=list(READ_OUTPUT_FIELDS),
            consistency_level="Strong",
        )
        result: dict[str, VersionEmbedding] = {}
        for raw in _rows(rows, "Milvus get"):
            value = _decode(raw)
            self._validate_record(value)
            if value.id in result:
                raise RepositoryIntegrityError(
                    f"duplicate Milvus embedding ID: {value.id}"
                )
            if value.id not in ids:
                raise RepositoryIntegrityError(
                    f"Milvus returned an unrequested embedding: {value.id}"
                )
            result[value.id] = value
        return result

    def put(self, record: VersionEmbedding) -> WriteResult:
        self._validate_record(record)
        existing = self.get(record.id)
        if existing is not None:
            return _existing(record, existing)
        try:
            self._client.insert(
                collection_name=self.collection_name,
                data=[encode_embedding(record).fields()],
            )
        except Exception as exc:
            concurrent = self.get(record.id)
            if concurrent is not None:
                return _existing(record, concurrent)
            raise RepositoryError("could not insert Milvus embedding") from exc
        persisted = self.get(record.id)
        if persisted != record:
            raise RepositoryIntegrityError(
                f"Milvus did not persist embedding exactly: {record.id}"
            )
        return WriteResult(record.id, WriteDisposition.CREATED)

    def put_many(
        self,
        records: Iterable[VersionEmbedding],
    ) -> BatchWriteResult:
        if isinstance(records, (str, bytes)):
            raise TypeError("embedding batch must contain VersionEmbedding values")
        items = tuple(records)
        for item in items:
            self._validate_record(item)
        ids = tuple(item.id for item in items)
        if len(ids) != len(set(ids)):
            raise RepositoryIntegrityError(
                "embedding batch contains duplicate deterministic IDs"
            )
        if not items:
            return BatchWriteResult(())
        existing = self.get_many(ids)
        for item in items:
            if item.id in existing:
                _existing(item, existing[item.id])
        new_items = tuple(item for item in items if item.id not in existing)
        if new_items:
            try:
                self._client.insert(
                    collection_name=self.collection_name,
                    data=[encode_embedding(item).fields() for item in new_items],
                )
            except Exception as exc:
                raise RepositoryError("could not insert Milvus embedding batch") from exc
            persisted = self.get_many(tuple(item.id for item in new_items))
            if any(persisted.get(item.id) != item for item in new_items):
                raise RepositoryIntegrityError(
                    "Milvus did not persist the complete embedding batch"
                )
        return BatchWriteResult(
            tuple(
                WriteResult(
                    item.id,
                    (
                        WriteDisposition.UNCHANGED
                        if item.id in existing
                        else WriteDisposition.CREATED
                    ),
                )
                for item in items
            )
        )

    def delete(self, embedding_id: str) -> bool:
        identifier = _required_text(embedding_id, "embedding id")
        if self.get(identifier) is None:
            return False
        self._call(
            "delete",
            collection_name=self.collection_name,
            ids=[identifier],
        )
        self._call("flush", collection_name=self.collection_name)
        if self.get(identifier) is not None:
            raise RepositoryIntegrityError(
                f"Milvus embedding is still visible after deletion: {identifier}"
            )
        return True

    def search(self, query: VectorSearchQuery) -> tuple[VectorMatch, ...]:
        if not isinstance(query, VectorSearchQuery):
            raise TypeError("query must be a VectorSearchQuery")
        if query.model != self.model:
            raise RepositoryIntegrityError(
                f"repository is configured for model {self.model}, got {query.model}"
            )
        if len(query.vector) != self.dimension:
            raise RepositoryIntegrityError(
                f"embedding model {self.model} expects dimension {self.dimension}, "
                f"got {len(query.vector)}"
            )
        expression = _temporal_filter(query)
        raw = self._call(
            "search",
            collection_name=self.collection_name,
            data=[list(float(item) for item in query.vector)],
            anns_field="vector",
            filter=expression,
            limit=query.limit,
            output_fields=list(SEARCH_OUTPUT_FIELDS),
            search_params={"metric_type": "COSINE", "params": {}},
            consistency_level="Strong",
        )
        groups = _rows(raw, "Milvus search")
        if len(groups) != 1 or not isinstance(groups[0], list):
            raise RepositoryIntegrityError(
                "Milvus search must return one result group per query vector"
            )
        matches = tuple(self._match(hit, query) for hit in groups[0])
        ordered = tuple(
            sorted(matches, key=lambda item: (-item.score, item.record.id))
        )
        return ordered[: query.limit]

    def close(self) -> None:
        self._call("close")

    def _match(
        self,
        raw: object,
        query: VectorSearchQuery,
    ) -> VectorMatch:
        hit = _mapping(raw, "Milvus search hit")
        entity = _mapping(hit.get("entity"), "Milvus search entity")
        fields = dict(entity)
        fields.setdefault("id", hit.get("id"))
        value = _decode(fields)
        self._validate_record(value)
        if not value.validity.contains(query.at):
            raise RepositoryIntegrityError(
                f"Milvus returned a temporally invalid embedding: {value.id}"
            )
        if query.document_ids and value.document_id not in query.document_ids:
            raise RepositoryIntegrityError(
                f"Milvus ignored the document filter for embedding: {value.id}"
            )
        if query.levels and value.level not in query.levels:
            raise RepositoryIntegrityError(
                f"Milvus ignored the level filter for embedding: {value.id}"
            )
        score = hit.get("distance", hit.get("score"))
        if isinstance(score, bool) or not isinstance(score, (int, float)):
            raise RepositoryIntegrityError("Milvus search score must be numeric")
        if not math.isfinite(float(score)):
            raise RepositoryIntegrityError("Milvus search score must be finite")
        return VectorMatch(value, float(score))

    def _validate_record(self, value: object) -> None:
        if not isinstance(value, VersionEmbedding):
            raise TypeError("record must be a VersionEmbedding")
        if value.model != self.model:
            raise RepositoryIntegrityError(
                f"repository is configured for model {self.model}, got {value.model}"
            )
        if len(value.vector) != self.dimension:
            raise RepositoryIntegrityError(
                f"embedding model {self.model} expects dimension {self.dimension}, "
                f"got {len(value.vector)}"
            )

    def _call(self, operation: str, **kwargs):
        try:
            return _method(self._client, operation)(**kwargs)
        except RepositoryError:
            raise
        except Exception as exc:
            raise RepositoryError(f"Milvus {operation} failed") from exc


def _temporal_filter(query: VectorSearchQuery) -> str:
    at = query.at.toordinal()
    clauses = [
        f"model == {_text_literal(query.model)}",
        f"eff_from <= {at}",
        f"eff_to > {at}",
    ]
    if query.document_ids:
        clauses.append(
            "document_id in "
            + json.dumps(list(query.document_ids), ensure_ascii=False)
        )
    if query.levels:
        clauses.append(
            "level in "
            + json.dumps(
                sorted(level.value for level in query.levels),
                ensure_ascii=False,
            )
        )
    return " && ".join(clauses)


def _text_literal(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def _existing(
    requested: VersionEmbedding,
    persisted: VersionEmbedding,
) -> WriteResult:
    if persisted != requested:
        raise RepositoryConflictError(
            f"embedding id {requested.id} already has different content"
        )
    return WriteResult(requested.id, WriteDisposition.UNCHANGED)


def _decode(value: Mapping[str, Any]) -> VersionEmbedding:
    fields = dict(value)
    if "vector" not in fields:
        payload = fields.get("payload")
        if isinstance(payload, Mapping):
            data = payload.get("data")
            if isinstance(data, Mapping):
                fields["vector"] = data.get("vector")
    try:
        return decode_embedding(fields)
    except (TypeError, ValueError) as exc:
        raise RepositoryIntegrityError(str(exc)) from exc


def _rows(value: object, context: str) -> list[Any]:
    if not isinstance(value, list):
        raise RepositoryIntegrityError(f"{context} result must be a list")
    return value


def _mapping(value: object, context: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise RepositoryIntegrityError(f"{context} must be a mapping")
    return value


def _ids(values: Sequence[str]) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)) or not isinstance(values, Sequence):
        raise TypeError("embedding IDs must be a sequence")
    ids = tuple(_required_text(value, "embedding id") for value in values)
    if len(ids) != len(set(ids)):
        raise ValueError("embedding IDs must not contain duplicates")
    return ids


def _required_text(value: object, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must not be empty")
    return value


def _method(value: object, name: str):
    method = getattr(value, name, None)
    if not callable(method):
        raise TypeError(f"Milvus client must provide {name}()")
    return method

"""Collection schema and compatibility checks for version embeddings."""
from __future__ import annotations

import re
from collections.abc import Mapping

from legal_crawler.ports import RepositoryIntegrityError, RepositoryError

COLLECTION_FIELDS = (
    "id",
    "vector",
    "payload",
    "version_id",
    "provision_id",
    "document_id",
    "model",
    "level",
    "eff_from",
    "eff_to",
    "schema_version",
)


class MilvusDependencyError(RuntimeError):
    """The optional official Milvus client is unavailable."""


def initialize_collection(
    client: object,
    collection_name: str,
    dimension: int,
    *,
    data_type: object | None = None,
) -> bool:
    """Create a strict COSINE collection or validate an existing one.

    Returns ``True`` when a collection was created and ``False`` when a
    compatible collection already existed.
    """
    validate_collection_config(collection_name, dimension)
    types = data_type if data_type is not None else _official_data_type()
    _validate_data_types(types)
    has_collection = _method(client, "has_collection")
    try:
        exists = has_collection(collection_name=collection_name)
    except Exception as exc:
        raise RepositoryError("could not inspect Milvus collection") from exc
    if not isinstance(exists, bool):
        raise RepositoryIntegrityError("Milvus has_collection must return bool")
    if exists:
        _validate_existing(client, collection_name, dimension, types)
        return False

    create_schema = _method(client, "create_schema")
    prepare_indexes = _method(client, "prepare_index_params")
    create_collection = _method(client, "create_collection")
    try:
        schema = create_schema(auto_id=False, enable_dynamic_field=False)
        _add_fields(schema, types, dimension)
        indexes = prepare_indexes()
        indexes.add_index(
            field_name="vector",
            index_type="AUTOINDEX",
            metric_type="COSINE",
        )
        create_collection(
            collection_name=collection_name,
            schema=schema,
            index_params=indexes,
            consistency_level="Strong",
        )
    except RepositoryIntegrityError:
        raise
    except Exception as exc:
        raise RepositoryError("could not initialize Milvus collection") from exc
    return True


def validate_collection_config(collection_name: str, dimension: int) -> None:
    """Validate stable Milvus resource and vector limits before I/O."""
    _collection_name(collection_name)
    _dimension(dimension)


def _validate_data_types(types: object) -> None:
    required_types = (
        "VARCHAR",
        "FLOAT_VECTOR",
        "JSON",
        "INT64",
        "INT16",
    )
    if any(not hasattr(types, name) for name in required_types):
        raise RepositoryIntegrityError("Milvus DataType vocabulary is incomplete")


def _add_fields(schema: object, types: object, dimension: int) -> None:
    add_field = _method(schema, "add_field")
    add_field(
        field_name="id",
        datatype=types.VARCHAR,
        is_primary=True,
        max_length=512,
    )
    add_field(
        field_name="vector",
        datatype=types.FLOAT_VECTOR,
        dim=dimension,
    )
    add_field(field_name="payload", datatype=types.JSON)
    for name in (
        "version_id",
        "provision_id",
        "document_id",
        "model",
        "level",
    ):
        add_field(
            field_name=name,
            datatype=types.VARCHAR,
            max_length=512,
        )
    add_field(field_name="eff_from", datatype=types.INT64)
    add_field(field_name="eff_to", datatype=types.INT64)
    add_field(field_name="schema_version", datatype=types.INT16)


def _validate_existing(
    client: object,
    collection_name: str,
    dimension: int,
    types: object,
) -> None:
    describe = _method(client, "describe_collection")
    try:
        description = describe(collection_name=collection_name)
    except Exception as exc:
        raise RepositoryError("could not describe Milvus collection") from exc
    if not isinstance(description, Mapping):
        raise RepositoryIntegrityError("Milvus collection description is invalid")
    fields = description.get("fields")
    if not isinstance(fields, list) or any(
        not isinstance(item, Mapping) for item in fields
    ):
        raise RepositoryIntegrityError("Milvus collection fields are invalid")
    by_name = {item.get("name"): item for item in fields}
    missing = set(COLLECTION_FIELDS).difference(by_name)
    if missing:
        raise RepositoryIntegrityError(
            "Milvus collection is missing fields: " + ", ".join(sorted(missing))
        )
    expected_types = {
        "id": types.VARCHAR,
        "vector": types.FLOAT_VECTOR,
        "payload": types.JSON,
        "version_id": types.VARCHAR,
        "provision_id": types.VARCHAR,
        "document_id": types.VARCHAR,
        "model": types.VARCHAR,
        "level": types.VARCHAR,
        "eff_from": types.INT64,
        "eff_to": types.INT64,
        "schema_version": types.INT16,
    }
    incompatible = sorted(
        name
        for name, expected in expected_types.items()
        if by_name[name].get("type") != expected
    )
    if incompatible:
        raise RepositoryIntegrityError(
            "Milvus collection has incompatible field types: "
            + ", ".join(incompatible)
        )
    vector_params = by_name["vector"].get("params")
    raw_dimension = (
        vector_params.get("dim") if isinstance(vector_params, Mapping) else None
    )
    try:
        actual_dimension = int(raw_dimension)
    except (TypeError, ValueError) as exc:
        raise RepositoryIntegrityError(
            "Milvus vector field has no valid dimension"
        ) from exc
    if actual_dimension != dimension:
        raise RepositoryIntegrityError(
            f"Milvus collection expects dimension {actual_dimension}, "
            f"configured {dimension}"
        )
    if by_name["id"].get("is_primary") is not True:
        raise RepositoryIntegrityError("Milvus id field must be primary")
    if description.get("enable_dynamic_field") is True:
        raise RepositoryIntegrityError(
            "Milvus embedding collection must disable dynamic fields"
        )


def _official_data_type():
    try:
        from pymilvus import DataType
    except ImportError as exc:
        raise MilvusDependencyError(
            "install the 'milvus' project extra to initialize Milvus storage"
        ) from exc
    return DataType


def _method(value: object, name: str):
    method = getattr(value, name, None)
    if not callable(method):
        raise TypeError(f"Milvus client must provide {name}()")
    return method


def _collection_name(value: object) -> str:
    if not isinstance(value, str) or not re.fullmatch(
        r"[A-Za-z_][A-Za-z0-9_]{0,254}", value
    ):
        raise ValueError(
            "Milvus collection name must start with a letter or underscore, "
            "contain only letters, numbers and underscores, and be at most "
            "255 characters"
        )
    return value


def _dimension(value: object) -> int:
    if (
        isinstance(value, bool)
        or not isinstance(value, int)
        or not 2 <= value <= 32_768
    ):
        raise ValueError("Milvus vector dimension must be between 2 and 32768")
    return value

"""Milvus adapter for version-aware temporal vector search."""

from .codec import (
    EMBEDDING_SCHEMA_VERSION,
    MAX_FILTER_TEXT_BYTES,
    MAX_JSON_BYTES,
    OPEN_END_ORDINAL,
    MilvusCodecError,
    MilvusEmbeddingRecord,
    decode_embedding,
    encode_embedding,
)
from .repository import MilvusVectorRepository
from .schema import (
    COLLECTION_FIELDS,
    MilvusDependencyError,
    initialize_collection,
    validate_collection_config,
)

__all__ = [
    "COLLECTION_FIELDS",
    "EMBEDDING_SCHEMA_VERSION",
    "MAX_FILTER_TEXT_BYTES",
    "MAX_JSON_BYTES",
    "MilvusCodecError",
    "MilvusDependencyError",
    "MilvusEmbeddingRecord",
    "MilvusVectorRepository",
    "OPEN_END_ORDINAL",
    "decode_embedding",
    "encode_embedding",
    "initialize_collection",
    "validate_collection_config",
]

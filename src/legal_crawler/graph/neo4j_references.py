"""D3 mapping from verified vbpl.vn reference codes to graph edge types.

The numeric code/label/group authority is ``data/reference_type_map.json``;
``RelationType`` supplies the project's typed Neo4j vocabulary. This table
binds the two without interpreting Vietnamese labels at load time.
"""
from __future__ import annotations

from legal_crawler.temporal import RelationType


REFERENCE_RELATION_TYPES: dict[int, RelationType] = {
    1: RelationType.REPEALS,
    2: RelationType.ANNOUNCES,
    3: RelationType.ISSUED_UNDER,
    4: RelationType.REFERS_TO,
    5: RelationType.HALTS_ENFORCEMENT,
    6: RelationType.CORRECTS,
    7: RelationType.CONSOLIDATES,
    8: RelationType.GUIDES,
    9: RelationType.DETAILS,
    10: RelationType.AMENDS,
    11: RelationType.SUSPENDS,
    12: RelationType.REPLACES,
    14: RelationType.INTERPRETS,
}


def relationship_type(reference_type: int) -> RelationType:
    """Reject unmapped source codes instead of inventing a graph type."""
    try:
        return REFERENCE_RELATION_TYPES[reference_type]
    except KeyError as exc:
        raise ValueError(
            f"referenceType={reference_type!r} has no D3 RelationType mapping; "
            "verify data/reference_type_map.json and update neo4j_references.py"
        ) from exc

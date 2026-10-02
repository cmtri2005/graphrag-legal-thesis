"""The effectivity filter, as four tiers of one ladder (plan phase-5-6, P2).

Formula (4) narrows the search space to 𝒰ₜ = {u | valid(u,t)} *before* ranking.
What a system can compute about `valid(u,t)` depends on what its representation
ρ(u) carries, and `docs/graph_justification.md` §3 Mệnh đề 1 says ρ is
insufficient as soon as two units share a representation but not a validity.
These four tiers are that proposition turned into four measurable points, each
adding exactly one of the information kinds I1–I3 named in §3:

    none         ρ = text                                   B2/B3/B4
    document     + the document's own dates                 B7
    version      + I1, the version chain's own window       B7+
    propagated   + I2, every ancestor's coverage, (3)        the proposed system

Each tier intersects strictly more than the tier above, so

    𝒰ₜ(propagated) ⊆ 𝒰ₜ(version) ⊆ 𝒰ₜ(document) ⊆ 𝒰ₜ(none)

which `assert_monotone` checks on real rows. That ordering is the reason
`version` carries the document predicate too: the chain's own window alone is
not a superset of the document tier, and a non-monotone ladder would confound
"more information" with "different information".

The windows themselves are precomputed (ADR 0001 §3, method A), so a tier is a
SQL predicate rather than a traversal — filtering and ranking happen in one
query, which is what formula (4) asks for. Half-open `[start, end)` throughout
(invariant D1).

Tiers `version` and `propagated` describe a *version*, so they are only
meaningful over corpus layer B; `SystemSpec` rejects the other pairing.
"""
from __future__ import annotations

TIERS = ("none", "document", "version", "propagated")
LAYER_B_ONLY = ("version", "propagated")

# `u` is the units row, `d` the joined documents row — see retrieve.py's base query.
_DOCUMENT = ("d.effective_from IS NOT NULL AND d.effective_from <= ?"
             " AND (d.effective_to IS NULL OR ? < d.effective_to)")
_LOCAL = ("u.local_from IS NOT NULL AND u.local_from <= ?"
          " AND (u.local_to IS NULL OR ? < u.local_to)")
_PROPAGATED = ("EXISTS (SELECT 1 FROM prop_iv p WHERE p.unit_id = u.unit_id"
               " AND p.start <= ? AND (p.end IS NULL OR ? < p.end))")


class TierError(ValueError):
    """A tier that cannot mean anything for the layer it was asked for."""


def predicate(tier: str, as_of: str) -> tuple[str, list[str]]:
    """The SQL restricting `units u` to 𝒰ₜ at `as_of`, and its parameters.

    An empty fragment means no restriction, which is tier `none` — the caller
    must treat it as "no WHERE clause", not as "match nothing".
    """
    if tier not in TIERS:
        raise TierError(f"unknown tier {tier!r}; known: {', '.join(TIERS)}")
    if tier == "none":
        return "", []
    parts, params = [_DOCUMENT], [as_of, as_of]
    if tier == "version":
        parts.append(_LOCAL)
        params += [as_of, as_of]
    elif tier == "propagated":
        parts.append(_PROPAGATED)
        params += [as_of, as_of]
    return " AND ".join(f"({p})" for p in parts), params


def in_force(windows, as_of: str) -> bool:
    """Half-open containment over `[(start, end), ...]` — invariant D1.

    Same reading as the scorer's own `in_force`, deliberately: a system must not
    be judged valid by a rule the metric does not use.
    """
    return any(start is not None and start <= as_of and (end is None or as_of < end)
               for start, end in windows)


def windows_for(corpus, unit_id: str, tier: str) -> list[tuple[str | None, str | None]]:
    """The windows `tier` would consult for one unit — for the Verifier and for tests."""
    if tier not in TIERS:
        raise TierError(f"unknown tier {tier!r}; known: {', '.join(TIERS)}")
    if tier == "none":
        return [(None, None)]
    row = corpus.db.execute(
        "SELECT u.local_from, u.local_to, d.effective_from, d.effective_to"
        " FROM units u LEFT JOIN documents d ON d.document_id = u.document_id"
        " WHERE u.unit_id = ?", (unit_id,)).fetchone()
    if row is None:
        return []
    local_from, local_to, doc_from, doc_to = tuple(row)
    if tier == "document":
        return [(doc_from, doc_to)]
    if tier == "version":
        return _intersect([(doc_from, doc_to)], [(local_from, local_to)])
    rows = corpus.db.execute("SELECT start, end FROM prop_iv WHERE unit_id = ?", (unit_id,)).fetchall()
    return [tuple(r) for r in rows]


def _intersect(left, right):
    """Pairwise intersection of two half-open window lists."""
    out = []
    for a_start, a_end in left:
        for b_start, b_end in right:
            if a_start is None or b_start is None:
                continue
            start = max(a_start, b_start)
            end = min([e for e in (a_end, b_end) if e is not None], default=None)
            if end is None or start < end:
                out.append((start, end))
    return out


def assert_monotone(corpus, as_of: str, *, layer: str = "version", sample: int = 2000) -> dict:
    """Prove 𝒰ₜ(propagated) ⊆ 𝒰ₜ(version) ⊆ 𝒰ₜ(document) on real rows.

    A violation means the two window kinds were crossed somewhere — the one
    failure in this package that would otherwise be silent, because the ladder
    would still produce numbers, just not comparable ones.

    All three tiers are evaluated over the *same* rows, and those rows are spread
    across the table by a rowid stride. Two earlier versions of this check were
    weaker: one put a LIMIT on each tier's own query, so the three sets sampled
    different rows and containment meant nothing; the next took the first N
    rowids, which all sat inside one 2026 document and so passed trivially for
    every earlier date.
    """
    total = corpus.db.execute("SELECT COUNT(*) FROM units WHERE layer=?", (layer,)).fetchone()[0]
    if not total:
        raise AssertionError(f"no units in layer {layer!r} to check")
    stride = max(1, total // max(sample, 1))
    kept: dict[str, set[str]] = {}
    for tier in ("document", "version", "propagated"):
        clause, params = predicate(tier, as_of)
        kept[tier] = {r[0] for r in corpus.db.execute(
            "SELECT u.unit_id FROM units u"
            " LEFT JOIN documents d ON d.document_id = u.document_id"
            " WHERE u.layer = ? AND (u.rowid % ?) = 0"
            f" AND {clause}", [layer, stride, *params])}
    for tighter, looser in (("propagated", "version"), ("version", "document")):
        extra = kept[tighter] - kept[looser]
        if extra:
            raise AssertionError(
                f"{len(extra)} units pass `{tighter}` but fail `{looser}` at {as_of} "
                f"(e.g. {sorted(extra)[0]}). The ladder must be nested: check that "
                f"units.local_from came from data/derived/versions.jsonl (valid_from/valid_to) "
                f"and prop_iv from corpus/versions.jsonl (effective_intervals) — crossing the "
                f"two window kinds collapses tiers 3 and 4 and the main result with them.")
    return {tier: len(ids) for tier, ids in kept.items()}

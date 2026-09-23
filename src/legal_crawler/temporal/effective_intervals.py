"""Precompute provision-version validity after document and ancestor bounds.

The local version chain remains untouched.  An ancestor amendment does not
invalidate a child; only a gap or repeal in the ancestor's *coverage* does.
The result may contain several disjoint half-open intervals if future events
introduce gaps, so callers must not collapse it to one broad range.
"""
from __future__ import annotations

from .models import TemporalInterval
from .state import TemporalState


def effective_intervals_by_version(
    state: TemporalState,
    document_id: str,
) -> dict[str, tuple[TemporalInterval, ...]]:
    """Return exact effective intervals for every dated version in a document."""
    document = state.document(document_id)
    if document is None:
        raise ValueError(f"unknown document: {document_id}")
    if document.effective_from is None:
        return {}

    document_window = (TemporalInterval(document.effective_from, document.effective_to),)
    coverage: dict[str, tuple[TemporalInterval, ...]] = {}
    result: dict[str, tuple[TemporalInterval, ...]] = {}
    visiting: set[str] = set()

    def resolve(provision_id: str) -> tuple[TemporalInterval, ...]:
        if provision_id in coverage:
            return coverage[provision_id]
        if provision_id in visiting:
            raise ValueError(f"cycle in provision ancestry: {provision_id}")
        provision = state.provision(provision_id)
        if provision is None or provision.document_id != document_id:
            raise ValueError(f"unknown provision in document: {provision_id}")
        visiting.add(provision_id)
        try:
            parent_windows = (
                resolve(provision.parent_id)
                if provision.parent_id is not None
                else document_window
            )
            chain = state.chain(provision_id)
            versions = chain.versions if chain else ()
            if not versions:
                # A node we hold no text for says nothing about its children:
                # a Chương/Mục heading carries no words of its own, and an Điều
                # the corpus lacks text for is missing data, not data to the
                # contrary (master plan §11). It is transparent to propagation,
                # exactly as in ``ValidityService``.
                coverage[provision_id] = parent_windows
                return coverage[provision_id]
            windows: list[TemporalInterval] = []
            for version in versions:
                intervals = (
                    _intersect((version.validity,), parent_windows)
                    if version.validity is not None
                    else ()
                )
                result[version.id] = intervals
                windows.extend(intervals)
            coverage[provision_id] = _merge(windows)
            return coverage[provision_id]
        finally:
            visiting.remove(provision_id)

    for provision in state.provisions_for_document(document_id):
        resolve(provision.id)
    return result


def _intersect(
    left: tuple[TemporalInterval, ...],
    right: tuple[TemporalInterval, ...],
) -> tuple[TemporalInterval, ...]:
    out: list[TemporalInterval] = []
    for first in left:
        for second in right:
            start = max(first.start, second.start)
            ends = [end for end in (first.end, second.end) if end is not None]
            end = min(ends) if ends else None
            if end is None or start < end:
                out.append(TemporalInterval(start, end))
    return tuple(out)


def _merge(intervals: list[TemporalInterval]) -> tuple[TemporalInterval, ...]:
    """Union adjacent/overlapping active windows, retaining actual gaps."""
    if not intervals:
        return ()
    ordered = sorted(intervals, key=lambda item: item.start)
    merged = [ordered[0]]
    for item in ordered[1:]:
        previous = merged[-1]
        if previous.end is None or item.start <= previous.end:
            end = (
                None
                if previous.end is None or item.end is None
                else max(previous.end, item.end)
            )
            merged[-1] = TemporalInterval(previous.start, end)
        else:
            merged.append(item)
    return tuple(merged)

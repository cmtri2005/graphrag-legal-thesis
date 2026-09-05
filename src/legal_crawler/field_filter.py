"""Stage 4 — field-based filtering (docs/crawling-plan.md §3/§4).

Keyword-based seeding (Stage 1) lets in false positives: a document whose
slug happens to contain a domain keyword but whose actual `documentFields`/
`documentMajors` put it in an unrelated ministry. This module classifies a
document as "foreign" using a hand-reviewed blocklist of major/field names
that have no plausible overlap with the 3 target domains — never a guess
made from the majors/fields seen at runtime. See `data/field_filter_map.json`
for what's on the list and why it's deliberately conservative.

Unlike `reference_types.ReferenceTypeMap`, this is not fail-loud on unknown
values: the default for anything not on the blocklist (including the very
common "Chưa phân loại" / no classification at all) is to keep the document.
Under-filtering here just means Stage 5/6 processes a few extra documents;
over-filtering silently deletes a real one — the cheaper mistake is clear.

A document is flagged only when EVERY major and EVERY field it has is on the
blocklist. A single on-topic major (e.g. "Tài chính" alongside "Công an" on a
jointly-issued circular) is enough to keep it — see field_filter_map.json's
note for the false positive that made this necessary. This output is a
review candidate list, not something to delete on: run it past a human
before excluding anything from later stages.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

DEFAULT_MAP_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "field_filter_map.json"

JsonDict = dict[str, Any]


@dataclass(frozen=True, slots=True)
class FieldFilterVerdict:
    is_foreign: bool
    matched_names: tuple[str, ...]


class FieldFilterMap:
    """Loaded blocklist of off-topic documentMajors/documentFields names."""

    def __init__(self, foreign_majors: set[str], foreign_fields: set[str]) -> None:
        self._foreign_majors = foreign_majors
        self._foreign_fields = foreign_fields

    @classmethod
    def load(cls, path: Path = DEFAULT_MAP_PATH) -> "FieldFilterMap":
        raw = json.loads(path.read_text(encoding="utf-8"))
        return cls(
            foreign_majors=set(raw.get("foreign_majors", [])),
            foreign_fields=set(raw.get("foreign_fields", [])),
        )

    def classify(self, document: JsonDict) -> FieldFilterVerdict:
        major_names = {m.get("name") for m in document.get("documentMajors") or []}
        field_names = {f.get("name") for f in document.get("documentFields") or []}
        names = major_names | field_names
        # Foreign only if every tag the doc has is on the blocklist — a single
        # on-topic major/field among several is enough to keep it (see module
        # docstring: multi-major docs were false-positiving on an ANY match).
        is_foreign = bool(names) and names.issubset(self._foreign_majors | self._foreign_fields)
        matched = names & (self._foreign_majors | self._foreign_fields)
        return FieldFilterVerdict(is_foreign=is_foreign, matched_names=tuple(sorted(matched)))

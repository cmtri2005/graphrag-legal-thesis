"""Ground-truth mapping for `history[].content` (docs/plans/completed/2026-09-04-truoc-stage-6.md §A).

Loads and enforces `data/eff_status_map.json`; it never invents a label, the
same rule `vocab/reference_types.py` follows. Read that JSON's `_readme` for how
each entry was established and what is still unknown about the numeric
suffixes.

Two things about `history` rows that will silently corrupt Stage 6 if missed:

1. **`createdDate` is a legal date only on `createdBy == "Job"` rows.** `Admin`
   rows carry the timestamp of the data-entry edit — one 2006 law has a
   `DATE_BH` row dated 2025. Use `is_legal_date` before treating any date as
   the moment a legal event happened.
2. **`content` is sometimes a sentence, not a code** ("Cập nhật trạng thái hiệu
   lực từ X sang Y."). `parse_transition` extracts those; they are useful as
   corroboration and must not be fed to `classify` as codes.
"""
from __future__ import annotations
import re
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path

from ..storage.documents import REPO_DATA_DIR, read_json

DEFAULT_MAP_PATH = REPO_DATA_DIR / "eff_status_map.json"

# Free-text rows the data-entry system writes instead of a code. Both halves
# appear as either a code ("CHL") or a Vietnamese label ("Còn hiệu lực"),
# which is exactly what confirmed several codes in the first place.
FREE_TEXT_PATTERN = r"^Cập nhật trạng thái hiệu lực từ (.+?) sang (.+?)\.?$"

# The only author whose createdDate is the date of the legal event itself.
_LEGAL_DATE_AUTHOR = "Job"


class UnknownStatusCodeError(RuntimeError):
    """A `content` code with no entry in the mapping table.

    Raised rather than defaulting, so an unrecognised effectivity event can
    never be silently folded into the wrong one — a mis-read transition
    corrupts every point-in-time answer that depends on it.
    """


@dataclass(frozen=True, slots=True)
class StatusCodeInfo:
    code: str
    label_vi: str
    kind: str  # "status" | "date"
    effect: str
    source: str


class StatusCodeMap:
    """Loaded, verified `content` -> meaning table."""

    def __init__(self, entries: dict[str, StatusCodeInfo]) -> None:
        self._entries = entries

    @classmethod
    def load(cls, path: Path = DEFAULT_MAP_PATH) -> "StatusCodeMap":
        raw = read_json(path)
        entries = {
            code: StatusCodeInfo(
                code=code,
                label_vi=info["label_vi"],
                kind=info["kind"],
                effect=info["effect"],
                source=info["source"],
            )
            for code, info in raw.get("codes", {}).items()
            if info.get("verified")
        }
        return cls(entries)

    @property
    def codes(self) -> frozenset[str]:
        return frozenset(self._entries)

    def knows(self, code: str) -> bool:
        return code in self._entries

    def classify(self, code: str) -> StatusCodeInfo:
        try:
            return self._entries[code]
        except KeyError:
            raise UnknownStatusCodeError(
                f"content={code!r} has no verified entry in {DEFAULT_MAP_PATH.name}; "
                "run scripts/explore/collect_status_codes.py and establish its meaning "
                "before letting Stage 6 read it."
            ) from None


def parse_transition(content: str) -> tuple[str, str] | None:
    """`(before, after)` for a free-text row, else None."""
    match = re.match(FREE_TEXT_PATTERN, content)
    return (match.group(1).strip(), match.group(2).strip()) if match else None


def is_legal_date(row: dict) -> bool:
    """Whether this row's `createdDate` is the date of the legal event.

    False for data-entry rows, whose timestamp says when a clerk typed the
    record — not when the law changed.
    """
    return row.get("createdBy") == _LEGAL_DATE_AUTHOR


# Effectivity dates on Job rows are a day late when stamped at midnight.
# Measured 2026-09-14 against the document's own field: `DATE_HL` at T00:00
# is exactly +1 day on 13,424 rows while every T07:00 row agrees; `DATE_HHL`
# behaves the same. The document side is the right one — NĐ 100/2019 and
# NĐ 168/2024 carry their real effective dates, and on the +1 rows `effFrom`
# falls on the 1st of a month 21% of the time against 3% for the history date.
# `DATE_BH` is NOT shifted: all 11,033 midnight rows equal `issueDate` as-is,
# so the offset belongs to the code, not the clock alone. After this table:
# 99.76% of DATE_HL, 99.92% of DATE_HHL, 100% of DATE_BH agree. Any other
# (code, clock) pair is not mapped: an unexplained stamp is not a date.
_LEGAL_DATE_SHIFT = {
    ("DATE_HL", "00:00:00"): -1,
    ("DATE_HL", "07:00:00"): 0,
    ("DATE_HHL", "00:00:00"): -1,
    ("DATE_HHL", "07:00:00"): 0,
    ("DATE_BH", "00:00:00"): 0,
}


def legal_date(row: dict) -> date | None:
    """The legal date a history row records, or None if it records none.

    Only for corroboration: never copy it over a document's own `effFrom`,
    `effTo` or `issueDate` (ADR 0002).
    """
    if not is_legal_date(row):
        return None
    stamp = str(row.get("createdDate") or "")
    shift = _LEGAL_DATE_SHIFT.get((row.get("content"), stamp[11:19]))
    if shift is None:
        return None
    return date.fromisoformat(stamp[:10]) + timedelta(days=shift)


# Why a document cannot be placed on the timeline. One definition, shared by
# `scripts/check/data_status.py` and `ingest.py`, checked in this order.
NO_EFF_FROM = "no effFrom — cannot place on the timeline at all"
REPEALED_WITHOUT_EFF_TO = "repealed in full, but no effTo says when"
EMPTY_INTERVAL = "effTo not after effFrom — portal data error"
NO_STATUS = "no effStatus"
IN_FORCE_PAST_EFF_TO = "still marked in force with a past effTo"


def anchor_problem(document: dict, today: date) -> str | None:
    """The first reason `document` cannot be placed in time, else None.

    `effTo == effFrom` counts: the half-open interval [d, d) is empty, so the
    document is in force on no day at all (74 documents on 2026-09-12, which a
    strict `<` used to leave out of the count).
    """
    eff_from = (document.get("effFrom") or "")[:10]
    eff_to = (document.get("effTo") or "")[:10]
    status = (document.get("effStatus") or {}).get("name")
    if not eff_from:
        return NO_EFF_FROM
    if status and status.startswith("Hết hiệu lực toàn bộ") and not eff_to:
        return REPEALED_WITHOUT_EFF_TO
    if eff_to and eff_to <= eff_from:
        return EMPTY_INTERVAL
    if not status:
        return NO_STATUS
    if status == "Còn hiệu lực" and eff_to and eff_to < today.isoformat():
        return IN_FORCE_PAST_EFF_TO
    return None

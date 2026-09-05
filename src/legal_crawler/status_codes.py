"""Ground-truth mapping for `history[].content` (docs/execution-plan.md §A).

Loads and enforces `data/eff_status_map.json`; it never invents a label, the
same rule `reference_types.py` follows. Read that JSON's `_readme` for how
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
from pathlib import Path

from .store import read_json

DEFAULT_MAP_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "eff_status_map.json"

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
                "run scripts/collect_status_codes.py and establish its meaning "
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

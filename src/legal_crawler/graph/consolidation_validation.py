"""Conservative article/clause alignment for consolidated-text validation.

E1 compares a dated consolidation with the graph's point-in-time text.  The
consolidation has its own paragraph UUIDs (or none), so UUID equality is not
evidence of identity.  Only an unambiguous Article number, or a Clause number
under an unambiguous Article, is accepted.  No fuzzy text matching selects a
target, and normalization is limited to Unicode NFC plus whitespace.
"""
from __future__ import annotations

import re
import unicodedata
from collections import Counter
from dataclasses import dataclass
from typing import Iterable

from legal_crawler.provisions.text import Paragraph
from legal_crawler.temporal import Provision, ProvisionLevel


_ARTICLE = re.compile(
    r"^Điều\s+(\d+[a-zđ]?)(?:\[\d+\])?\s*(?:[.:–—-]|$)", re.IGNORECASE,
)
_CLAUSE = re.compile(r"^(\d+[a-zđ]?)(?:\[\d+\])?\s*[.)]\s*", re.IGNORECASE)
_POINT = re.compile(r"^[a-zđ]\s*[.)]\s+", re.IGNORECASE)
_SECTION = re.compile(
    r"^(?:Phần|Chương|Tiểu\s+mục|Mục)\s+(?:\d+[a-zđ]?|[ivxlcdm]+)\b",
    re.IGNORECASE,
)
_FOOTER = re.compile(r"^(?:Nơi nhận\s*:|Phụ lục\b)", re.IGNORECASE)
_TITLE_ARTICLE = re.compile(r"^Điều\s+(\d+[a-zđ]?)\s*$", re.IGNORECASE)
_TITLE_CLAUSE = re.compile(r"^Khoản\s+(\d+[a-zđ]?)\s*$", re.IGNORECASE)
_SPACE = re.compile(r"\s+")


@dataclass(frozen=True, slots=True)
class TextUnit:
    level: str
    article: str
    clause: str | None
    text: str
    body_text: str | None = None

    @property
    def key(self) -> tuple[str, str, str | None]:
        return (self.level, self.article, self.clause)


def normalized_text(value: str) -> str:
    """Ignore formatting whitespace, but never rewrite legal words/punctuation."""
    return _SPACE.sub(" ", unicodedata.normalize("NFC", value)).strip()


def _number(value: str) -> str:
    value = unicodedata.normalize("NFC", value).casefold()
    match = re.fullmatch(r"(\d+)([a-zđ]?)", value)
    if match is None:
        raise ValueError(f"unsupported article/clause number: {value!r}")
    return f"{int(match.group(1))}{match.group(2)}"


def article_marker(text: str) -> str | None:
    match = _ARTICLE.match(normalized_text(text))
    return _number(match.group(1)) if match else None


def source_units(paragraphs: Iterable[Paragraph]) -> tuple[list[TextUnit], Counter[str]]:
    """Read numbered units from body paragraphs, retaining duplicate counts.

    A run ends at the next Article/Clause or an explicit different paragraph
    UUID.  This intentionally excludes nested Points from a Clause comparison:
    their own words are not part of that Clause's stored version text.
    """
    units: list[TextUnit] = []
    stats: Counter[str] = Counter()
    current_article: str | None = None
    current: TextUnit | None = None
    parts: list[str] = []
    current_id: str | None = None

    def flush() -> None:
        nonlocal current, parts, current_id
        if current is not None:
            text = normalized_text(" ".join(parts))
            if text:
                body = (
                    normalized_text(" ".join(parts[1:]))
                    if current.level == "Article" and len(parts) > 1 else None
                )
                units.append(TextUnit(
                    current.level, current.article, current.clause, text, body,
                ))
        current, parts, current_id = None, [], None

    for paragraph in paragraphs:
        value = normalized_text(paragraph.text)
        if not value:
            continue
        if _FOOTER.match(value):
            flush()
            break  # annexes and signature/recipient sections are out of E1 scope
        if _SECTION.match(value):
            flush()
            continue
        article = article_marker(value)
        if article is not None:
            flush()
            current_article = article
            current = TextUnit("Article", article, None, "")
            parts = [value]
            current_id = paragraph.node_id
            stats["article_markers"] += 1
            continue
        if current_article is None:
            continue
        clause_match = _CLAUSE.match(value)
        if clause_match is not None:
            clause = _number(clause_match.group(1))
            # Repeated numbers remain duplicate keys and are excluded below;
            # a numbered note must not be silently appended to a legal clause.
            flush()
            current = TextUnit("Clause", current_article, clause, "")
            parts = [value]
            current_id = paragraph.node_id
            stats["clause_markers"] += 1
            continue
        if _POINT.match(value):
            # A Point is a child of the current Clause.  Its text must not be
            # appended to the parent's version, even when HTML has no UUIDs.
            flush()
            continue
        if current is not None and (
            paragraph.node_id is None or paragraph.node_id == current_id
        ):
            parts.append(value)
        else:
            flush()
    flush()
    counts = Counter(unit.key for unit in units)
    duplicates = {key for key, count in counts.items() if count > 1}
    if duplicates:
        stats["duplicate_unit_keys"] = len(duplicates)
    return [unit for unit in units if unit.key not in duplicates], stats


def target_units(provisions: Iterable[Provision]) -> tuple[dict[tuple[str, str, str | None], str], set[tuple[str, str, str | None]]]:
    """Map only uniquely numbered Articles and their directly nested Clauses."""
    items = tuple(provisions)
    by_id = {item.id: item for item in items}
    candidates: dict[tuple[str, str, str | None], list[str]] = {}
    for item in items:
        if item.level is ProvisionLevel.ARTICLE:
            match = _TITLE_ARTICLE.match(item.title.strip())
            if match:
                key = ("Article", _number(match.group(1)), None)
                candidates.setdefault(key, []).append(item.id)
        elif item.level is ProvisionLevel.CLAUSE and item.parent_id in by_id:
            parent = by_id[item.parent_id]
            if parent.level is not ProvisionLevel.ARTICLE:
                continue
            article = _TITLE_ARTICLE.match(parent.title.strip())
            clause = _TITLE_CLAUSE.match(item.title.strip())
            if article and clause:
                key = ("Clause", _number(article.group(1)), _number(clause.group(1)))
                candidates.setdefault(key, []).append(item.id)
    unique = {key: ids[0] for key, ids in candidates.items() if len(ids) == 1}
    ambiguous = {key for key, ids in candidates.items() if len(ids) > 1}
    return unique, ambiguous


def select_base_target(
    target_numbers: dict[str, str], preamble: str,
) -> tuple[str | None, str]:
    """Pick the first cited CONSOLIDATES target, never a date-based guess."""
    if not target_numbers:
        return None, "no_consolidates_target"
    if len(target_numbers) == 1:
        return next(iter(target_numbers)), "single_target"
    compact = re.sub(
        r"\s*([/-])\s*", r"\1", normalized_text(preamble).casefold().replace("đ", "d"),
    )
    positions: list[tuple[int, str]] = []
    for target_id, number in target_numbers.items():
        normalized = re.sub(
            r"\s*([/-])\s*", r"\1", normalized_text(number).casefold().replace("đ", "d"),
        )
        if not normalized:
            continue
        pattern = re.compile(rf"(?<![\w]){re.escape(normalized)}(?![\w])")
        match = pattern.search(compact)
        if match:
            positions.append((match.start(), target_id))
    if not positions:
        return None, "no_target_number_in_preamble"
    positions.sort()
    earliest = positions[0][0]
    if sum(position == earliest for position, _ in positions) != 1:
        return None, "ambiguous_first_citation"
    return positions[0][1], "first_target_cited"

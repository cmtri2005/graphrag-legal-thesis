"""Pure, auditable implementations of the thesis evaluation metrics."""
from __future__ import annotations

import re
import unicodedata
from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Hashable, Iterable, Sequence


class MetricInputError(ValueError):
    """A metric would be undefined or its judgments are inconsistent."""


@dataclass(frozen=True, slots=True)
class TemporalCitationJudgment:
    answer_id: str
    citation_id: str
    valid_at_query_time: bool

    def __post_init__(self) -> None:
        _text(self.answer_id, "answer_id")
        _text(self.citation_id, "citation_id")
        _boolean(self.valid_at_query_time, "valid_at_query_time")


@dataclass(frozen=True, slots=True)
class VersionCitationJudgment:
    citation_id: str
    correct_provision: bool
    correct_version: bool

    def __post_init__(self) -> None:
        _text(self.citation_id, "citation_id")
        _boolean(self.correct_provision, "correct_provision")
        _boolean(self.correct_version, "correct_version")
        if self.correct_version and not self.correct_provision:
            raise MetricInputError("a correct version implies a correct provision")


@dataclass(frozen=True, slots=True)
class ContrastPairJudgment:
    pair_id: str
    first_correct: bool
    second_correct: bool

    def __post_init__(self) -> None:
        _text(self.pair_id, "pair_id")
        _boolean(self.first_correct, "first_correct")
        _boolean(self.second_correct, "second_correct")


def recall_at_k(
    retrieved_ids: Sequence[str], relevant_ids: Iterable[str], k: int
) -> float:
    """Fraction of unique gold units present in the first ``k`` results."""
    _positive_k(k)
    gold = _non_empty_unique(relevant_ids, "relevant_ids")
    retrieved = _ranked_ids(retrieved_ids)
    return len(set(retrieved[:k]) & gold) / len(gold)


def temporally_valid_recall_at_k(
    retrieved_ids: Sequence[str],
    relevant_ids: Iterable[str],
    valid_at_query_time_ids: Iterable[str],
    k: int,
) -> float:
    """Recall over gold units that are also valid at the requested time."""
    _positive_k(k)
    relevant = _non_empty_unique(relevant_ids, "relevant_ids")
    valid = set(valid_at_query_time_ids)
    valid_gold = relevant & valid
    if not valid_gold:
        raise MetricInputError("no relevant unit is valid at the query time")
    retrieved = _ranked_ids(retrieved_ids)
    return len(set(retrieved[:k]) & valid_gold) / len(valid_gold)


def reciprocal_rank(retrieved_ids: Sequence[str], relevant_ids: Iterable[str]) -> float:
    gold = _non_empty_unique(relevant_ids, "relevant_ids")
    for rank, identifier in enumerate(_ranked_ids(retrieved_ids), 1):
        if identifier in gold:
            return 1.0 / rank
    return 0.0


def mean_reciprocal_rank(
    ranked_results: Iterable[Sequence[str]],
    relevant_sets: Iterable[Iterable[str]],
) -> float:
    results = tuple(ranked_results)
    gold = tuple(relevant_sets)
    if not results or len(results) != len(gold):
        raise MetricInputError("MRR requires equally sized non-empty query and gold sets")
    return sum(reciprocal_rank(items, relevant) for items, relevant in zip(results, gold)) / len(results)


def temporal_validity_error_rate(
    judgments: Iterable[TemporalCitationJudgment],
) -> float:
    """Share of cited answers containing at least one temporally invalid citation."""
    items = tuple(judgments)
    _unique_key(items, lambda item: item.citation_id, "citation_id")
    by_answer: dict[str, list[TemporalCitationJudgment]] = defaultdict(list)
    for item in items:
        by_answer[item.answer_id].append(item)
    if not by_answer:
        raise MetricInputError("TVER requires at least one answer with a citation")
    erroneous = sum(
        any(not citation.valid_at_query_time for citation in citations)
        for citations in by_answer.values()
    )
    return erroneous / len(by_answer)


def version_confusion_rate(judgments: Iterable[VersionCitationJudgment]) -> float:
    """Wrong-version rate among citations that identify the correct legal unit."""
    items = tuple(judgments)
    _unique_key(items, lambda item: item.citation_id, "citation_id")
    eligible = tuple(item for item in items if item.correct_provision)
    if not eligible:
        raise MetricInputError("VCR requires a citation to a correct provision")
    return sum(not item.correct_version for item in eligible) / len(eligible)


def temporal_consistency_score(judgments: Iterable[ContrastPairJudgment]) -> float:
    """Share of T2 contrast pairs answered correctly at both time points."""
    items = tuple(judgments)
    _unique_key(items, lambda item: item.pair_id, "pair_id")
    if not items:
        raise MetricInputError("TCS requires at least one contrast pair")
    return sum(item.first_correct and item.second_correct for item in items) / len(items)


def accuracy(correctness: Iterable[bool]) -> float:
    items = tuple(correctness)
    if not items:
        raise MetricInputError("accuracy requires at least one judgment")
    for item in items:
        _boolean(item, "accuracy judgment")
    return sum(items) / len(items)


def exact_match(prediction: str, reference: str) -> float:
    return float(_normalize_text(prediction) == _normalize_text(reference))


def token_f1(prediction: str, reference: str) -> float:
    predicted = _tokens(prediction)
    expected = _tokens(reference)
    if not predicted and not expected:
        return 1.0
    if not predicted or not expected:
        return 0.0
    common = sum((Counter(predicted) & Counter(expected)).values())
    if not common:
        return 0.0
    precision = common / len(predicted)
    recall = common / len(expected)
    return 2 * precision * recall / (precision + recall)


def cohen_kappa(first: Sequence[Hashable], second: Sequence[Hashable]) -> float:
    """Cohen's kappa for two complete categorical annotation sequences."""
    if not first or len(first) != len(second):
        raise MetricInputError("kappa requires equally sized non-empty annotations")
    size = len(first)
    observed = sum(left == right for left, right in zip(first, second)) / size
    first_counts = Counter(first)
    second_counts = Counter(second)
    labels = first_counts.keys() | second_counts.keys()
    expected = sum(first_counts[label] * second_counts[label] for label in labels) / (size * size)
    if expected == 1.0:
        if observed == 1.0:
            return 1.0
        raise MetricInputError("kappa is undefined when expected agreement is one")
    return (observed - expected) / (1 - expected)


def _normalize_text(value: str) -> str:
    if not isinstance(value, str):
        raise MetricInputError("text metric inputs must be strings")
    value = unicodedata.normalize("NFC", value).casefold()
    value = re.sub(r"[^\w\s]", " ", value, flags=re.UNICODE)
    return re.sub(r"\s+", " ", value).strip()


def _tokens(value: str) -> tuple[str, ...]:
    normalized = _normalize_text(value)
    return tuple(normalized.split()) if normalized else ()


def _ranked_ids(values: Sequence[str]) -> tuple[str, ...]:
    result = tuple(values)
    for item in result:
        _text(item, "retrieved id")
    if len(result) != len(set(result)):
        raise MetricInputError("retrieved IDs must be unique")
    return result


def _non_empty_unique(values: Iterable[str], name: str) -> set[str]:
    items = tuple(values)
    if not items:
        raise MetricInputError(f"{name} must not be empty")
    for item in items:
        _text(item, name)
    if len(items) != len(set(items)):
        raise MetricInputError(f"{name} must contain unique IDs")
    return set(items)


def _unique_key(items: tuple[object, ...], key, name: str) -> None:
    values = tuple(key(item) for item in items)
    if len(values) != len(set(values)):
        raise MetricInputError(f"{name} values must be unique")


def _positive_k(k: int) -> None:
    if isinstance(k, bool) or not isinstance(k, int) or k < 1:
        raise MetricInputError("k must be a positive integer")


def _text(value: object, name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise MetricInputError(f"{name} must not be empty")


def _boolean(value: object, name: str) -> None:
    if type(value) is not bool:
        raise MetricInputError(f"{name} must be a boolean")

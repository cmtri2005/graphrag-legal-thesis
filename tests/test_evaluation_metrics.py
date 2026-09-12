import pytest

from legal_crawler.evaluation import (
    ContrastPairJudgment,
    MetricInputError,
    TemporalCitationJudgment,
    VersionCitationJudgment,
    accuracy,
    cohen_kappa,
    exact_match,
    mean_reciprocal_rank,
    recall_at_k,
    reciprocal_rank,
    temporal_consistency_score,
    temporal_validity_error_rate,
    temporally_valid_recall_at_k,
    token_f1,
    version_confusion_rate,
)


def test_standard_retrieval_metrics_use_rank_and_unique_gold_units():
    retrieved = ("x", "b", "a")

    assert recall_at_k(retrieved, ("a", "b"), 2) == pytest.approx(0.5)
    assert reciprocal_rank(retrieved, ("a", "b")) == pytest.approx(0.5)
    assert mean_reciprocal_rank((retrieved, ("none",)), (("a", "b"), ("gold",))) == pytest.approx(0.25)


def test_temporally_valid_recall_requires_relevance_and_validity():
    score = temporally_valid_recall_at_k(
        ("old-version", "valid-b"),
        ("old-version", "valid-a", "valid-b"),
        ("valid-a", "valid-b"),
        2,
    )
    assert score == pytest.approx(0.5)


def test_tver_counts_answers_with_any_invalid_citation():
    judgments = (
        TemporalCitationJudgment("a1", "c1", True),
        TemporalCitationJudgment("a1", "c2", False),
        TemporalCitationJudgment("a2", "c3", True),
    )
    assert temporal_validity_error_rate(judgments) == pytest.approx(0.5)


def test_vcr_only_uses_citations_to_the_correct_provision():
    judgments = (
        VersionCitationJudgment("c1", True, False),
        VersionCitationJudgment("c2", True, True),
        VersionCitationJudgment("c3", False, False),
    )
    assert version_confusion_rate(judgments) == pytest.approx(0.5)


def test_tcs_requires_both_members_of_each_contrast_pair_to_be_correct():
    pairs = (
        ContrastPairJudgment("p1", True, True),
        ContrastPairJudgment("p2", True, False),
        ContrastPairJudgment("p3", False, False),
    )
    assert temporal_consistency_score(pairs) == pytest.approx(1 / 3)


def test_answer_metrics_normalize_unicode_case_spacing_and_punctuation():
    assert accuracy((True, False, True)) == pytest.approx(2 / 3)
    assert exact_match("  Điều  1! ", "điều 1") == 1.0
    assert token_f1("thuế giá trị", "thuế giá trị gia tăng") == pytest.approx(0.75)
    assert token_f1("", "") == 1.0


def test_cohen_kappa_handles_agreement_and_chance_correction():
    assert cohen_kappa(("yes", "yes", "no", "no"), ("yes", "yes", "no", "no")) == 1.0
    assert cohen_kappa(("yes", "yes", "no", "no"), ("yes", "no", "yes", "no")) == 0.0


@pytest.mark.parametrize(
    "call",
    (
        lambda: recall_at_k((), (), 1),
        lambda: recall_at_k(("a", "a"), ("a",), 1),
        lambda: temporally_valid_recall_at_k(("a",), ("a",), (), 1),
        lambda: temporal_validity_error_rate(()),
        lambda: version_confusion_rate((VersionCitationJudgment("c", False, False),)),
        lambda: temporal_consistency_score(()),
        lambda: accuracy(()),
        lambda: cohen_kappa((), ()),
    ),
)
def test_metrics_fail_loudly_when_their_denominator_is_undefined(call):
    with pytest.raises(MetricInputError):
        call()


def test_metric_judgments_reject_logical_or_type_errors():
    with pytest.raises(MetricInputError, match="implies"):
        VersionCitationJudgment("c", False, True)
    with pytest.raises(MetricInputError, match="boolean"):
        ContrastPairJudgment("p", 1, True)

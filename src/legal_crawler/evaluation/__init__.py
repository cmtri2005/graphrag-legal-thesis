"""Evaluation metrics for temporal legal retrieval and answers."""

from .metrics import (
    ContrastPairJudgment,
    MetricInputError,
    TemporalCitationJudgment,
    VersionCitationJudgment,
    accuracy,
    cohen_kappa,
    exact_match,
    mean_reciprocal_rank,
    reciprocal_rank,
    recall_at_k,
    temporal_consistency_score,
    temporal_validity_error_rate,
    temporally_valid_recall_at_k,
    token_f1,
    version_confusion_rate,
)

__all__ = [
    "ContrastPairJudgment",
    "MetricInputError",
    "TemporalCitationJudgment",
    "VersionCitationJudgment",
    "accuracy",
    "cohen_kappa",
    "exact_match",
    "mean_reciprocal_rank",
    "reciprocal_rank",
    "recall_at_k",
    "temporal_consistency_score",
    "temporal_validity_error_rate",
    "temporally_valid_recall_at_k",
    "token_f1",
    "version_confusion_rate",
]

"""Typed contracts between amendment extraction, resolution and application."""

from .models import (
    EventMaterializationError,
    ExtractionModelError,
    ExtractionResult,
    ExtractionStatus,
    ExtractionWarning,
    PhraseReplacement,
    ProvisionLocator,
    ProvisionReferencePart,
    RawAmendmentMention,
    ResolutionStatus,
    ResolvedTarget,
    SourceSpan,
    TargetReference,
    TargetScope,
    WarningCode,
    WarningSeverity,
)
from .target_resolver import (
    TargetResolution,
    TargetResolutionCode,
    TargetResolutionError,
    TargetResolver,
)

__all__ = [
    "EventMaterializationError",
    "ExtractionModelError",
    "ExtractionResult",
    "ExtractionStatus",
    "ExtractionWarning",
    "PhraseReplacement",
    "ProvisionLocator",
    "ProvisionReferencePart",
    "RawAmendmentMention",
    "ResolutionStatus",
    "ResolvedTarget",
    "SourceSpan",
    "TargetReference",
    "TargetResolution",
    "TargetResolutionCode",
    "TargetResolutionError",
    "TargetResolver",
    "TargetScope",
    "WarningCode",
    "WarningSeverity",
]

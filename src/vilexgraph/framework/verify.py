"""The Temporal Verifier (plan phase-5-6, P3; ADR 0004 §5).

Formula (4) narrows retrieval to 𝒰ₜ, but an answer can still cite a unit that
is not in it: a model may cite a label it was shown for context, and a system
verified against a stricter tier than it retrieved with is shown units that
tier would refuse. The Verifier is the
last line — it re-reads the units an answer cites against the system's own tier
and acts on any that fail.

Three modes, one decision per ADR 0004 §5 (accepted 02/10 — `reject` is the
main configuration, `off` is ablation A3):

    off      leave the answer alone
    warn     leave the answer alone, record what would have been rejected
    reject   drop the answer's invalid citations and regenerate once from the
             valid evidence; if nothing valid remains, or the second answer
             still cites an invalid unit, abstain

**Abstention is "I did not answer", never "it is not in force".** It returns
`answerable=True` with an empty text and the cause on the `Verdict`. Claiming
`answerable=False` from a refusal would be scored correct on every genuinely
unanswerable row for the wrong reason (ADR 0003 §3; generate.py).

Retrieval and expansion (`graphx.py`) both apply the system's own tier, and the
Verifier uses that same tier, so for the proposed system nothing shown can be
invalid and the Verifier is a no-op by construction. That is a property of the
design, not a defect: it is a safety net, and it only bites when the two tiers
differ (an ablation, or a hand-built system). `Verdict.checked` makes the no-op
visible, and the report must say so rather than credit the Verifier with a gain.
"""
from __future__ import annotations

from dataclasses import dataclass

from .generate import Answer
from .temporal import in_force, windows_for


@dataclass(frozen=True, slots=True)
class Verdict:
    """What the Verifier did to one answer."""

    mode: str
    action: str                      # off | pass | flagged | regenerated | abstained
    checked: int = 0                 # citations examined
    invalid: tuple[str, ...] = ()    # cited units outside 𝒰ₜ in the first answer
    cause: str | None = None         # set when action == abstained

    def as_dict(self) -> dict:
        return {"mode": self.mode, "action": self.action, "checked": self.checked,
                "invalid": list(self.invalid), "cause": self.cause}


def invalid_units(corpus, tier: str, as_of: str, unit_ids) -> tuple[str, ...]:
    """Those of `unit_ids` that are not in force at `as_of` under `tier`.

    Tier `none` has no windows to consult, so it admits everything — it must not
    fall through to `in_force`, which reads the absent window as "never in force".
    """
    if tier == "none":
        return ()
    return tuple(u for u in unit_ids if not in_force(windows_for(corpus, u, tier), as_of))


def verify(corpus, *, mode: str, tier: str, as_of: str, units, answer: Answer,
           regenerate) -> tuple[Answer, Verdict]:
    """Apply `mode` to `answer`.

    `units` is the evidence the answer was generated from; `regenerate(units)`
    produces a new `Answer` from a (smaller) evidence list. Only the answer's own
    citations are judged: an invalid unit that was shown but not cited is not
    something the answer asserts.
    """
    if mode == "off":
        return answer, Verdict("off", "off")
    bad = invalid_units(corpus, tier, as_of, answer.citations)
    checked = len(answer.citations)
    if not bad:
        return answer, Verdict(mode, "pass", checked)
    if mode == "warn":
        return answer, Verdict(mode, "flagged", checked, bad)

    # reject: one retry on the evidence that survives the tier.
    shown = [u.unit_id for u in units]
    refused = set(invalid_units(corpus, tier, as_of, shown))
    kept = [u for u in units if u.unit_id not in refused]
    if not kept:
        return _abstain(answer, mode, checked, bad, "no_valid_evidence")
    second = regenerate(kept)
    if invalid_units(corpus, tier, as_of, second.citations):
        return _abstain(second, mode, checked, bad, "invalid_after_regeneration")
    return second, Verdict(mode, "regenerated", checked, bad)


def _abstain(answer: Answer, mode: str, checked: int, bad, cause: str):
    empty = Answer("", True, (), answer.raw, answer.provider, answer.model, answer.cached)
    return empty, Verdict(mode, "abstained", checked, bad, cause)

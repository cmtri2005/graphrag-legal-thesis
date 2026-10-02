"""The Verifier: a citation outside 𝒰ₜ is dropped, retried once, or abstained from."""
from __future__ import annotations

from vilexgraph.framework.generate import Answer
from vilexgraph.framework.verify import verify
from test_rag_corpus import CLAUSE, corpus, data  # noqa: F401  (fixtures)

UNIT = f"version:{CLAUSE.split(':')[1]}:1"   # in force until its Điều is repealed (2022)
BAD, AFTER = "2023-01-01", "2021-01-01"


def ans(text: str, *cites: str) -> Answer:
    return Answer(text, True, tuple(cites), "raw", "p", "m")


def run(corpus, mode, as_of, answer, regen, tier="propagated"):
    units = corpus.units([UNIT])
    return verify(corpus, mode=mode, tier=tier, as_of=as_of, units=units, answer=answer,
                  regenerate=regen)


def test_off_does_nothing(corpus) -> None:
    got, v = run(corpus, "off", BAD, ans("x", UNIT), lambda _u: 1 / 0)
    assert got.text == "x" and v.action == "off"


def test_valid_citation_passes_without_a_second_call(corpus) -> None:
    got, v = run(corpus, "reject", AFTER, ans("x", UNIT), lambda _u: 1 / 0)
    assert v.action == "pass" and v.checked == 1 and got.citations == (UNIT,)


def test_warn_flags_but_keeps_the_answer(corpus) -> None:
    got, v = run(corpus, "warn", BAD, ans("x", UNIT), lambda _u: 1 / 0)
    assert got.text == "x" and v.action == "flagged" and v.invalid == (UNIT,)


def test_reject_with_no_valid_evidence_abstains_without_calling_the_model(corpus) -> None:
    got, v = run(corpus, "reject", BAD, ans("x", UNIT), lambda _u: 1 / 0)
    assert (v.action, v.cause) == ("abstained", "no_valid_evidence")
    assert got.text == "" and got.answerable is True, "abstaining is not a claim of expiry"


def test_tier_none_admits_everything(corpus) -> None:
    got, v = run(corpus, "reject", BAD, ans("x", UNIT), lambda _u: 1 / 0, tier="none")
    assert v.action == "pass"


def fake_invalid(*refused):
    return lambda _c, _t, _a, ids: tuple(i for i in ids if i in refused)


def test_reject_regenerates_once_from_the_valid_evidence(corpus, monkeypatch) -> None:
    other = "asis:" + CLAUSE
    monkeypatch.setattr("vilexgraph.framework.verify.invalid_units", fake_invalid(UNIT))
    seen = []

    def regen(kept):
        seen.append([u.unit_id for u in kept])
        return ans("fixed", other)

    units = corpus.units([UNIT, other])
    got, v = verify(corpus, mode="reject", tier="propagated", as_of=BAD, units=units,
                    answer=ans("x", UNIT), regenerate=regen)
    assert (v.action, v.invalid) == ("regenerated", (UNIT,))
    assert seen == [[other]] and got.text == "fixed"


def test_second_answer_still_invalid_abstains(corpus, monkeypatch) -> None:
    other = "asis:" + CLAUSE
    monkeypatch.setattr("vilexgraph.framework.verify.invalid_units", fake_invalid(UNIT))
    units = corpus.units([UNIT, other])
    got, v = verify(corpus, mode="reject", tier="propagated", as_of=BAD, units=units,
                    answer=ans("x", UNIT), regenerate=lambda _k: ans("y", UNIT))
    assert (v.action, v.cause) == ("abstained", "invalid_after_regeneration")
    assert got.text == "" and got.answerable is True

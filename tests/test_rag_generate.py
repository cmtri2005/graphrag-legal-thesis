"""Prompt, answer parsing, and the guarantee that no gold field reaches a prompt."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

from vilexgraph import llm
from vilexgraph.framework import generate
from vilexgraph.framework.corpus import Unit

import run_vilextime  # scripts/eval, put on the path by conftest

SENTINEL = "ZZQQ-gold-must-never-be-prompted-7f3a"


def unit(n: int) -> Unit:
    return Unit(f"version:p{n}:1", "version", "version", f"provision:p{n}", "document:d",
                "Clause", 1, f"nội dung {n}", "Thông tư X › Điều 2. Giải thích")


def test_prompt_labels_units_and_maps_tags_back() -> None:
    _, user, ids = generate.build_prompt("Hỏi gì?", "2024-05-01", [unit(1), unit(2)],
                                         with_context=True)
    assert "MỐC THỜI GIAN: 2024-05-01" in user
    assert "[1]" in user and "[2]" in user
    assert ids == ["version:p1:1", "version:p2:1"]


def test_context_is_opt_in() -> None:
    _, with_ctx, _ = generate.build_prompt("q", "2024-05-01", [unit(1)], with_context=True)
    _, without, _ = generate.build_prompt("q", "2024-05-01", [unit(1)], with_context=False)
    assert "Điều 2. Giải thích" in with_ctx
    assert "Điều 2. Giải thích" not in without


def test_no_evidence_overrides_the_abstention_rule() -> None:
    """B1 must not abstain merely because it was handed nothing to read."""
    _, user, ids = generate.build_prompt("q", "2024-05-01", [], with_context=True)
    assert ids == []
    assert "không rõ" in user


@pytest.mark.parametrize("raw, answerable, text, cites", [
    ("TRẢ LỜI: nội dung A\nHIỆU LỰC: còn\nCĂN CỨ: [2]", True, "nội dung A", ("version:p2:1",)),
    ("TRẢ LỜI:\nHIỆU LỰC: không\nCĂN CỨ: [1]", False, "", ("version:p1:1",)),
    ("TRẢ LỜI: x\nHIỆU LỰC:  KHÔNG \nCĂN CỨ:", False, "", ()),
    ("TRẢ LỜI: a\nHIỆU LỰC: [2], [2], [9]\nCĂN CỨ: [2], [2], [9]", True, "a", ("version:p2:1",)),
])
def test_parse(raw, answerable, text, cites) -> None:
    ids = ["version:p1:1", "version:p2:1"]
    assert generate.parse(raw, ids) == (text, answerable, cites)


def test_declining_is_not_a_claim_that_the_unit_expired() -> None:
    """"không rõ" must stay answerable, or a model that shrugs scores correct
    on every genuinely unanswerable row and the reason stops being measured."""
    _, answerable, _ = generate.parse("TRẢ LỜI:\nHIỆU LỰC: không rõ\nCĂN CỨ:", [])
    assert answerable is True
    _, claimed, _ = generate.parse("TRẢ LỜI:\nHIỆU LỰC: không\nCĂN CỨ:", [])
    assert claimed is False


def test_a_mistyped_label_does_not_become_the_answer() -> None:
    text, answerable, _ = generate.parse("TRẢ LỜI:\nHIỆU LỰNG: không\nCĂN CỨ:", [])
    assert text == ""
    assert answerable is True, "a typo must not be read as a legal claim"


def test_unformatted_output_is_kept_not_silently_scored_empty() -> None:
    text, _, _ = generate.parse("mô hình phớt lờ định dạng", [])
    assert text == "mô hình phớt lờ định dạng"


def test_cache_round_trip(tmp_path: Path) -> None:
    cache = generate.Cache(tmp_path / "c.sqlite")
    key = generate.Cache.key("sys", "usr", "groq", "m")
    assert cache.get(key) is None
    cache.put(key, "groq", "m", "TRẢ LỜI: x\nHIỆU LỰC: còn\nCĂN CỨ:")
    assert tuple(cache.get(key))[:2] == ("groq", "m")
    assert generate.Cache.key("sys", "usr", "groq", "other") != key
    cache.close()
    assert generate.Cache(None).get(key) is None


def test_no_gold_field_can_reach_the_prompt(tmp_path: Path, monkeypatch) -> None:
    """The most load-bearing test here: a leak would show up as a good score.

    A whole run is driven over a release row whose every gold field carries a
    sentinel, and the captured prompt is checked for it.
    """
    release = tmp_path / "release.jsonl"
    release.write_text(json.dumps({
        "id": "vilextime:T1:provision:x:2024-05-01", "split": "dev", "group": "T1",
        "question": "Quy định nói gì?", "as_of": "2024-05-01",
        "as_of_strategy": "giua_khoang", "lineage_id": "provision:x",
        # everything below is gold and must not be prompted
        "answer": SENTINEL, "short_answer": SENTINEL, "answerable": True,
        "version_id": f"version:{SENTINEL}:1", "no_answer_reason": None,
        "evidence_set": [{"provision_id": SENTINEL, "version_id": SENTINEL, "role": "gold"}],
        "accepted_evidence": [f"asis:provision:{SENTINEL}"],
        "derivation": {"transitions": [{"evidence": SENTINEL}]},
        "target": {"lead_in": SENTINEL, "citation": SENTINEL},
    }, ensure_ascii=False) + "\n", encoding="utf-8")

    seen: list[str] = []

    def capture(system, user, **kwargs):
        seen.append(system + "\n" + user)
        return llm.Completion("TRẢ LỜI: gì đó\nHIỆU LỰC: còn\nCĂN CỨ:", "fake", "fake", 0.0)

    monkeypatch.setattr(llm, "complete", capture)
    out = tmp_path / "preds.jsonl"
    monkeypatch.setattr(sys, "argv", ["run_vilextime.py", "--system", "b1", "--split", "dev",
                                      "--release", str(release), "--out", str(out), "--no-cache"])
    run_vilextime.main()

    assert seen, "the generator was never called"
    for prompt in seen:
        assert SENTINEL not in prompt, "a gold field reached the prompt"
    written = [json.loads(line) for line in out.read_text(encoding="utf-8").splitlines() if line]
    assert [r["id"] for r in written] == ["vilextime:T1:provision:x:2024-05-01"]
    assert written[0]["answer"] == "gì đó"


def test_query_exposes_only_three_fields() -> None:
    assert list(run_vilextime.Query.__slots__) == ["id", "question", "as_of"]

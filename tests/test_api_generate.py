"""The API runtime writes what `colab_b1 import` accepts, and never pays for a row twice."""
from __future__ import annotations

import json
import sys
from types import SimpleNamespace

import pytest

import api_generate
from colab_b1 import digest, import_completions
from vilexgraph import llm

ANSWER = "TRẢ LỜI: Văn bản.\nHIỆU LỰC: còn\nCĂN CỨ: [1]"


def done(text=ANSWER, finish="stop", served="m-2024"):
    return llm.Completion(text, "openai", "m", 0.0, 10, 5, finish, served, "fp")


@pytest.fixture
def run(tmp_path, monkeypatch):
    rows = []
    for n in range(3):
        row = {"id": f"dev-{n}", "system": "s", "user": f"u{n}", "ids": ["unit-1"], "retrieved": ["unit-1"]}
        row["prompt_sha256"] = digest(row)
        rows.append(row)
    prompts = tmp_path / "prompts.jsonl"
    prompts.write_text("".join(json.dumps(r) + "\n" for r in rows))
    out = tmp_path / "raw"

    def go(*extra, model="m"):
        monkeypatch.setattr(sys, "argv", ["api_generate.py", "--prompts", str(prompts), "--out-dir", str(out),
                                          "--provider", "openai", "--model", model, "--workers", "1", *extra])
        api_generate.main()
        return next(p for p in out.glob("*.jsonl"))

    return SimpleNamespace(go=go, prompts=prompts, tmp=tmp_path, rows=rows)


def test_output_is_accepted_by_import(run, monkeypatch):
    monkeypatch.setattr(llm, "complete", lambda *a, **k: done())
    raw = run.go()
    out = run.tmp / "pred.jsonl"
    import_completions(SimpleNamespace(prompts=run.prompts, raw=raw, out=out))
    assert [json.loads(line)["format_ok"] for line in out.read_text().splitlines()] == [True] * 3


def test_limit_then_full_never_requests_a_row_twice(run, monkeypatch):
    calls = []
    monkeypatch.setattr(llm, "complete", lambda s, user, **k: calls.append(user) or done())
    run.go("--limit", "1")
    run.go()
    assert sorted(calls) == ["u0", "u1", "u2"]


def test_settings_cannot_change_inside_one_file(run, monkeypatch):
    monkeypatch.setattr(llm, "complete", lambda *a, **k: done())
    run.go("--limit", "1")
    with pytest.raises(SystemExit, match="one configuration"):
        run.go("--max-tokens", "512")


def test_provider_error_stops_and_the_same_command_finishes(run, monkeypatch):
    def boom(s, user, **k):
        if user == "u1":
            raise llm.LLMError("429")
        return done()

    monkeypatch.setattr(llm, "complete", boom)
    with pytest.raises(SystemExit, match="continues"):
        run.go()
    monkeypatch.setattr(llm, "complete", lambda *a, **k: done())
    raw = run.go()
    assert sorted(json.loads(line)["id"] for line in raw.read_text().splitlines()) == ["dev-0", "dev-1", "dev-2"]


def test_truncated_answer_is_recorded_not_lost(run, monkeypatch):
    def cut(*a, **k):
        raise llm.Truncated("cut", "TRẢ LỜI: dở", done("TRẢ LỜI: dở", "length"))

    monkeypatch.setattr(llm, "complete", cut)
    raw = run.go("--limit", "1")
    item = json.loads(raw.read_text().splitlines()[0])
    assert (item["finish_reason"], item["raw"]) == ("length", "TRẢ LỜI: dở")


def test_refusal_stops_rather_than_scoring_empty(run, monkeypatch):
    monkeypatch.setattr(llm, "complete", lambda *a, **k: done("", "content_filter"))
    with pytest.raises(SystemExit, match="content_filter"):
        run.go()


def test_crash_cut_last_line_is_dropped_and_rerequested(run, monkeypatch):
    calls = []
    monkeypatch.setattr(llm, "complete", lambda s, user, **k: calls.append(user) or done())
    raw = run.go("--limit", "1")
    with raw.open("a") as sink:
        sink.write('{"id": "dev-1", "pro')
    run.go("--limit", "2")
    assert calls == ["u0", "u1"]
    assert len(raw.read_text().splitlines()) == 2


def test_test_split_needs_the_amendment_commit(run, monkeypatch):
    called = []
    monkeypatch.setattr(llm, "complete", lambda *a, **k: called.append(1) or done())
    rows = [{**r, "system_name": "b2ctx", "split": "test", "as_of": "2024-01-01", "signals": {}} for r in run.rows]
    for row in rows:
        row["prompt_sha256"] = digest(row)
    run.prompts.write_text("".join(json.dumps(r) + "\n" for r in rows))
    with pytest.raises(SystemExit, match="amendment"):
        run.go()
    assert not called


def test_seed_is_sent_only_when_given(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "k")
    sent = []

    class Reply:
        ok, status_code, headers, text = True, 200, {}, ""

        @staticmethod
        def json():
            return {"model": "m-2024", "choices": [{"finish_reason": "stop", "message": {"content": "x"}}],
                    "usage": {"prompt_tokens": 1, "completion_tokens": 1}}

    session = SimpleNamespace(post=lambda url, json, **k: sent.append(json) or Reply())
    got = llm.complete("s", "u", provider="openai", model="m", seed=7, session=session)
    llm.complete("s", "u", provider="openai", model="m", session=session)
    assert sent[0]["seed"] == 7 and "seed" not in sent[1]
    assert (got.served_model, got.finish_reason) == ("m-2024", "stop")

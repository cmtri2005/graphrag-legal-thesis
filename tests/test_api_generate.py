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


def test_run_tag_keeps_runs_apart(run, monkeypatch):
    calls = []
    monkeypatch.setattr(llm, "complete", lambda s, user, **k: calls.append(user) or done())
    run.go("--run-tag", "r1")
    run.go("--run-tag", "r2")                      # the second run is not "already answered"
    assert len(calls) == 6
    names = sorted(p.name for p in (run.tmp / "raw").glob("*.jsonl"))
    assert [n.split(".")[-2] for n in names] == ["r1", "r2"]
    with pytest.raises(SystemExit, match="run-tag"):
        run.go("--run-tag", "second")


def test_test_split_needs_accepted_adr_0006(run, monkeypatch):
    import colab_b1
    monkeypatch.setattr(colab_b1, "adr_accepted", lambda *a: False)
    called = []
    monkeypatch.setattr(llm, "complete", lambda *a, **k: called.append(1) or done())
    rows = [{**r, "system_name": "b2ctx", "split": "test", "as_of": "2024-01-01", "signals": {}} for r in run.rows]
    for row in rows:
        row["prompt_sha256"] = digest(row)
    run.prompts.write_text("".join(json.dumps(r) + "\n" for r in rows))
    with pytest.raises(SystemExit, match="ADR 0006"):
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


def test_batch_submits_then_collects_the_same_raw_shape(run, monkeypatch):
    calls, state = [], {}

    class R:
        def __init__(self, data=None, text=""):
            self.data, self.text = data, text

        def json(self):
            return self.data

    def fake(method, path, **kw):
        calls.append((method, path))
        if path == "/files":
            state["input"] = kw["files"]["file"][1].decode()
            return R({"id": "file-in"})
        if path == "/batches":
            return R({"id": "batch-1"})
        if path == "/batches/batch-1":
            return R({"status": state.get("status", "in_progress"), "output_file_id": "file-out"})
        body = {"model": "m-2024", "system_fingerprint": "fp", "usage": {"prompt_tokens": 10, "completion_tokens": 5},
                "choices": [{"finish_reason": "stop", "message": {"content": ANSWER}}]}
        lines = [{"custom_id": f"dev-{n}", "response": {"status_code": 200, "body": body}} for n in (0, 2)]
        lines.append({"custom_id": "dev-1", "response": {"status_code": 500, "body": {}}})
        return R(text="\n".join(json.dumps(x) for x in lines))

    monkeypatch.setattr(api_generate, "openai_request", fake)
    monkeypatch.setattr(llm, "complete", lambda *a, **k: pytest.fail("batch must not call the direct API"))
    raw = run.go("--batch")
    sent = [json.loads(line) for line in state["input"].splitlines()]
    assert [x["custom_id"] for x in sent] == ["dev-0", "dev-1", "dev-2"]
    assert sent[0]["body"]["seed"] == 20261109 and sent[0]["body"]["messages"][1]["content"] == "u0"
    run.go("--batch")                                   # still running: nothing written
    assert raw.read_text() == ""
    state["status"] = "completed"
    run.go("--batch")
    assert sorted(json.loads(line)["id"] for line in raw.read_text().splitlines()) == ["dev-0", "dev-2"]
    run.go("--batch")                                   # the failed row goes into a new batch
    assert calls.count(("POST", "/batches")) == 2
    with pytest.raises(SystemExit, match="transport"):
        run.go()                                        # one raw file, one transport

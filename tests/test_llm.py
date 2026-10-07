"""The provider table and the .env fallback — no network in any of these."""
import os

import pytest

from vilexgraph.llm import (LLMError, PROVIDERS, Truncated, _load_env_file, complete,
                            configured, model_for, pick)


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch):
    for _, key, model in PROVIDERS.values():
        monkeypatch.delenv(key, raising=False)
        monkeypatch.delenv(model, raising=False)
    # `.env` is read at import, so a pinned provider there would decide these tests
    monkeypatch.delenv("LLM_PROVIDER", raising=False)


def test_groq_is_preferred_when_several_keys_are_present(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "x")
    monkeypatch.setenv("GROQ_API_KEY", "x")

    assert configured()[0] == "groq"
    assert pick() == "groq"
    assert pick("openai") == "openai"      # an explicit choice still wins


def test_llm_provider_pins_the_choice_over_the_table_order(monkeypatch):
    """Which model wrote a question is published, so a leftover key must not decide it."""
    monkeypatch.setenv("GROQ_API_KEY", "x")
    monkeypatch.setenv("DEEPSEEK_API_KEY", "x")
    assert pick() == "groq", "the table order is still the fallback"

    monkeypatch.setenv("LLM_PROVIDER", "deepseek")
    assert pick() == "deepseek"
    assert pick("groq") == "groq", "an explicit argument still wins"

    monkeypatch.setenv("LLM_PROVIDER", "deepseek")
    monkeypatch.delenv("DEEPSEEK_API_KEY")
    with pytest.raises(LLMError, match="DEEPSEEK_API_KEY"):
        pick()                             # pinned but unusable is an error, not a silent fallback


def test_a_missing_key_says_which_variable_to_set(monkeypatch):
    with pytest.raises(LLMError, match="GROQ_API_KEY"):
        pick("groq")
    with pytest.raises(LLMError, match="no provider configured"):
        pick()
    with pytest.raises(LLMError, match="unknown provider"):
        pick("anthropic")                  # deliberately absent: different API shape


def test_no_model_is_ever_guessed(monkeypatch):
    """Ids move faster than this file, so a wrong default would fail obscurely."""
    monkeypatch.setenv("GROQ_API_KEY", "x")
    with pytest.raises(LLMError, match="list_models"):
        model_for("groq")

    monkeypatch.setenv("GROQ_MODEL", "from-env")
    assert model_for("groq") == "from-env"
    assert model_for("groq", "explicit") == "explicit"


def test_the_env_file_fills_gaps_but_never_overrides(monkeypatch, tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text('# comment\n\nGROQ_API_KEY="from-file"\nGROQ_MODEL=also-from-file\nmalformed\n',
                        encoding="utf-8")
    monkeypatch.setattr("vilexgraph.llm._ENV_FILE", env_file)
    monkeypatch.setenv("GROQ_MODEL", "from-environment")

    _load_env_file()

    assert os.environ["GROQ_API_KEY"] == "from-file"        # gap filled, quotes stripped
    assert os.environ["GROQ_MODEL"] == "from-environment"   # real variable wins


def test_a_missing_env_file_is_not_an_error(monkeypatch, tmp_path):
    monkeypatch.setattr("vilexgraph.llm._ENV_FILE", tmp_path / "nope")
    _load_env_file()          # must not raise; the file is a convenience


def test_a_truncated_answer_is_an_error_not_a_bad_question(monkeypatch):
    """gpt-oss spends max_tokens thinking; a cut-off reply must not be scored as the model's question."""
    from vilexgraph.llm import complete

    class Cut:
        ok, status_code, headers = True, 200, {}

        def json(self):
            return {"choices": [{"finish_reason": "length", "message": {"content": "Trong lĩnh vực"}}]}

    class Session:
        def post(self, *args, **kwargs):
            return Cut()

    monkeypatch.setenv("GROQ_API_KEY", "x")
    with pytest.raises(LLMError, match="truncated"):
        complete("s", "u", provider="groq", model="m", session=Session())


class _Reply:
    """Just enough of requests.Response for `complete` — no network in this file."""

    def __init__(self, payload):
        self.status_code, self._payload, self.headers, self.text = 200, payload, {}, ""
        self.ok = True

    def json(self):
        return self._payload


class _Session:
    """Records the payload `complete` posts and replies with `finish_reason`."""

    def __init__(self, finish_reason="stop"):
        self.sent, self._finish = [], finish_reason

    def post(self, url, json, timeout, headers):
        self.sent.append(json)
        return _Reply({"choices": [{"message": {"content": "Quy định về X là gì?"},
                                    "finish_reason": self._finish}]})


def test_effort_is_sent_only_when_asked_for(monkeypatch):
    """DeepSeek served only reasoning models on 07/10/2026, both defaulting to "high".

    Writing one question needs no reasoning, and "high" spends max_tokens on hidden
    thinking and then truncates — so the lever is effort, not a bigger budget. The
    field is omitted entirely when unset, so a provider that does not know it never
    sees it.
    """
    monkeypatch.setenv("DEEPSEEK_API_KEY", "k")

    plain = _Session()
    complete("s", "u", provider="deepseek", model="deepseek-flash", session=plain)
    assert "effort" not in plain.sent[-1]

    low = _Session()
    complete("s", "u", provider="deepseek", model="deepseek-flash", effort="low", session=low)
    assert low.sent[-1]["effort"] == "low"


def test_a_truncated_reply_names_effort_as_the_fix_when_none_was_set(monkeypatch):
    monkeypatch.setenv("DEEPSEEK_API_KEY", "k")

    with pytest.raises(LLMError, match="effort='low'"):
        complete("s", "u", provider="deepseek", model="deepseek-flash",
                 session=_Session(finish_reason="length"))
    with pytest.raises(LLMError) as caught:
        complete("s", "u", provider="deepseek", model="deepseek-flash", effort="low",
                 session=_Session(finish_reason="length"))
    assert "effort" not in str(caught.value)      # already set: the hint would be noise


def test_truncated_is_an_llm_error_that_still_carries_the_fragment(monkeypatch):
    """The contract generate_questions depends on to keep a batch moving.

    It must stay catchable as LLMError, so callers that do not care keep working,
    while a caller walking a batch can catch it on its own and record the item
    instead of stalling on the same one at every rerun. The fragment comes with it
    because the model's text is kept whether or not it passed.
    """
    monkeypatch.setenv("DEEPSEEK_API_KEY", "k")

    with pytest.raises(Truncated) as caught:
        complete("s", "u", provider="deepseek", model="deepseek-flash",
                 session=_Session(finish_reason="length"))
    assert isinstance(caught.value, LLMError)
    assert caught.value.text == "Quy định về X là gì?"

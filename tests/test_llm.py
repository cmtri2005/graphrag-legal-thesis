"""The provider table and the .env fallback — no network in any of these."""
import os

import pytest

from legal_crawler.llm import (LLMError, PROVIDERS, _load_env_file, configured, model_for, pick)


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch):
    for _, key, model in PROVIDERS.values():
        monkeypatch.delenv(key, raising=False)
        monkeypatch.delenv(model, raising=False)


def test_groq_is_preferred_when_several_keys_are_present(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "x")
    monkeypatch.setenv("GROQ_API_KEY", "x")

    assert configured()[0] == "groq"
    assert pick() == "groq"
    assert pick("openai") == "openai"      # an explicit choice still wins


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
    monkeypatch.setattr("legal_crawler.llm._ENV_FILE", env_file)
    monkeypatch.setenv("GROQ_MODEL", "from-environment")

    _load_env_file()

    assert os.environ["GROQ_API_KEY"] == "from-file"        # gap filled, quotes stripped
    assert os.environ["GROQ_MODEL"] == "from-environment"   # real variable wins


def test_a_missing_env_file_is_not_an_error(monkeypatch, tmp_path):
    monkeypatch.setattr("legal_crawler.llm._ENV_FILE", tmp_path / "nope")
    _load_env_file()          # must not raise; the file is a convenience

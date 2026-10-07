"""One chat completion, from whichever provider is configured (Groq first).

Every provider here speaks the OpenAI `chat/completions` shape, so the client
is a POST and a table — no SDK and no new dependency. `requests` is already
this project's only runtime dependency and it is enough. Anthropic is absent
on purpose: its API is a different shape, and adding a second code path for a
provider nobody asked for is weight without a use.

A provider is usable when its key is in the environment. `pick()` takes the
first configured one in `PROVIDERS` order, so Groq wins when its key is set:
generating a question for every candidate is thousands of calls, and Groq is
the one whose throughput makes that affordable.

`$LLM_PROVIDER` pins which one is used, so a second key left in `.env` cannot
quietly move generation somewhere else — the provider and model are published
per row, so that choice is data, not a convenience.

Model ids move faster than this file, so none is guessed: pass `--model`, or
set `<PROVIDER>_MODEL`. `list_models()` asks the provider what it currently
serves, which is quicker than reading a changelog.

    export DEEPSEEK_API_KEY=...
    python -c "from vilexgraph.llm import list_models; print(list_models('deepseek'))"

A reasoning model spends `max_tokens` on hidden thinking before it answers, and
a one-line question does not need any — it just truncates, which arrives as
"hit max_tokens". Where a provider offers a plain chat model, prefer it. Where it
does not — DeepSeek served only `deepseek-flash` and `deepseek-v4-pro` on
07/10/2026, both reasoning, both defaulting to effort "high" — pass
`effort="low"` instead of raising `max_tokens`, so the budget is not spent to be
thrown away.
"""
from __future__ import annotations

import os
import random
import time
from dataclasses import dataclass
from pathlib import Path

import requests

# name -> (base URL, env var holding the key, env var holding the model)
PROVIDERS: dict[str, tuple[str, str, str]] = {
    "groq": ("https://api.groq.com/openai/v1", "GROQ_API_KEY", "GROQ_MODEL"),
    "openai": ("https://api.openai.com/v1", "OPENAI_API_KEY", "OPENAI_MODEL"),
    "openrouter": ("https://openrouter.ai/api/v1", "OPENROUTER_API_KEY", "OPENROUTER_MODEL"),
    "together": ("https://api.together.xyz/v1", "TOGETHER_API_KEY", "TOGETHER_MODEL"),
    "deepseek": ("https://api.deepseek.com/v1", "DEEPSEEK_API_KEY", "DEEPSEEK_MODEL"),
    "gemini": ("https://generativelanguage.googleapis.com/v1beta/openai",
               "GEMINI_API_KEY", "GEMINI_MODEL"),
}
_RETRIABLE = (408, 409, 425, 429, 500, 502, 503, 504)
_ENV_FILE = Path(__file__).resolve().parents[2] / ".env"


def _load_env_file() -> None:
    """Read `.env` for keys the environment does not already set.

    The repo already keeps secrets there for docker-compose and git already
    ignores it, so it is where someone puts an API key. A real environment
    variable always wins, and a missing or unreadable file is not an error —
    this is a convenience, never a requirement.
    """
    try:
        lines = _ENV_FILE.read_text(encoding="utf-8").splitlines()
    except OSError:
        return
    for line in lines:
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        name, _, value = line.partition("=")
        name = name.strip()
        if name and name not in os.environ:
            os.environ[name] = value.strip().strip("\"'")


_load_env_file()


class LLMError(RuntimeError):
    """The provider refused, and the caller should see why verbatim."""



class Truncated(LLMError):
    """The reply was cut off at `max_tokens`, so what came back is a fragment.

    Separate from every other LLMError because the cause is this *one* request —
    its input, the model's effort level — not the provider being down or rate
    limiting. A caller walking a batch can record the item and keep going, where
    stopping would mean stalling on the same item on every rerun. The fragment is
    carried along: nothing the model writes is trusted, and nothing is thrown away.
    """

    def __init__(self, message: str, text: str = ""):
        super().__init__(message)
        self.text = text

@dataclass(frozen=True, slots=True)
class Completion:
    """The text, plus what produced it — C1 requires both on every row."""

    text: str
    provider: str
    model: str
    temperature: float


def configured() -> list[str]:
    """Providers whose key is in the environment, in preference order."""
    return [name for name, (_, key, _) in PROVIDERS.items() if os.environ.get(key)]


def pick(provider: str | None = None) -> str:
    """The provider to call: the argument, else `$LLM_PROVIDER`, else the first keyed one.

    `$LLM_PROVIDER` exists because which model wrote a question is published data
    (the datasheet names it per row), and "whichever key happens to be set, in
    this file's order" is the wrong way to decide that. Keeping a second key in
    `.env` must not silently move generation to another provider.
    """
    provider = provider or os.environ.get("LLM_PROVIDER") or None
    if provider:
        if provider not in PROVIDERS:
            raise LLMError(f"unknown provider {provider!r}; known: {', '.join(PROVIDERS)}")
        if not os.environ.get(PROVIDERS[provider][1]):
            raise LLMError(f"{provider} needs {PROVIDERS[provider][1]} in the environment")
        return provider
    available = configured()
    if not available:
        raise LLMError("no provider configured; set one of: "
                       + ", ".join(key for _, key, _ in PROVIDERS.values()))
    return available[0]


def model_for(provider: str, model: str | None = None) -> str:
    chosen = model or os.environ.get(PROVIDERS[provider][2])
    if not chosen:
        raise LLMError(
            f"no model for {provider}: pass --model or set {PROVIDERS[provider][2]}. "
            f"`list_models({provider!r})` prints what it serves right now.")
    return chosen


def list_models(provider: str | None = None) -> list[str]:
    provider = pick(provider)
    base, key, _ = PROVIDERS[provider]
    response = requests.get(f"{base}/models",
                            headers={"Authorization": f"Bearer {os.environ[key]}"}, timeout=30)
    response.raise_for_status()
    return sorted(m["id"] for m in response.json().get("data", []))


def complete(system: str, user: str, *, provider: str | None = None, model: str | None = None,
             temperature: float = 0.0, max_tokens: int = 4096, timeout: int = 90,
             retries: int = 5, session: requests.Session | None = None,
             effort: str | None = None) -> Completion:
    """One completion, retrying only what is worth retrying.

    Temperature defaults to 0: a benchmark whose questions cannot be
    regenerated is a benchmark whose questions cannot be audited.

    `effort` is sent only when given, so a provider that does not know the field
    never sees it. It is the lever for a reasoning model on a task that needs no
    reasoning: the models list reports which levels a model takes.
    """
    provider = pick(provider)
    base, key, _ = PROVIDERS[provider]
    model = model_for(provider, model)
    post = (session or requests).post
    payload = {"model": model, "temperature": temperature, "max_tokens": max_tokens,
               "messages": [{"role": "system", "content": system},
                            {"role": "user", "content": user}]}
    if effort:
        payload["effort"] = effort

    for attempt in range(retries):
        response = post(f"{base}/chat/completions", json=payload, timeout=timeout,
                        headers={"Authorization": f"Bearer {os.environ[key]}",
                                 "Content-Type": "application/json"})
        if response.status_code in _RETRIABLE and attempt < retries - 1:
            # Honour the provider's own pacing when it sends one; free tiers do.
            after = response.headers.get("Retry-After")
            delay = float(after) if after and after.replace(".", "", 1).isdigit() else 2.0 ** attempt
            time.sleep(min(delay, 60) + random.random())
            continue
        if not response.ok:
            raise LLMError(f"{provider} {response.status_code}: {response.text[:400]}")
        choices = response.json().get("choices") or []
        if not choices:
            raise LLMError(f"{provider} returned no choice: {response.text[:400]}")
        # Reasoning models (gpt-oss, qwen3) spend max_tokens on hidden thinking
        # first, so a cut-off answer looks like a bad one. Never pass it on.
        if choices[0].get("finish_reason") == "length":
            raise Truncated(f"{provider} {model}: hit max_tokens={max_tokens}; the answer is truncated"
                            + ("" if effort else " (a reasoning model? try effort='low')"),
                            (choices[0]["message"].get("content") or "").strip())
        return Completion((choices[0]["message"]["content"] or "").strip(), provider, model, temperature)
    raise LLMError(f"{provider} still failing after {retries} attempts")

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

Model ids move faster than this file, so none is guessed: pass `--model`, or
set `<PROVIDER>_MODEL`. `list_models()` asks the provider what it currently
serves, which is quicker than reading a changelog.

    export GROQ_API_KEY=...
    python -c "from legal_crawler.llm import list_models; print(list_models())"
"""
from __future__ import annotations

import os
import random
import time
from dataclasses import dataclass

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


class LLMError(RuntimeError):
    """The provider refused, and the caller should see why verbatim."""


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
             temperature: float = 0.0, max_tokens: int = 512, timeout: int = 90,
             retries: int = 5, session: requests.Session | None = None) -> Completion:
    """One completion, retrying only what is worth retrying.

    Temperature defaults to 0: a benchmark whose questions cannot be
    regenerated is a benchmark whose questions cannot be audited.
    """
    provider = pick(provider)
    base, key, _ = PROVIDERS[provider]
    model = model_for(provider, model)
    post = (session or requests).post
    payload = {"model": model, "temperature": temperature, "max_tokens": max_tokens,
               "messages": [{"role": "system", "content": system},
                            {"role": "user", "content": user}]}

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
        return Completion(choices[0]["message"]["content"].strip(), provider, model, temperature)
    raise LLMError(f"{provider} still failing after {retries} attempts")

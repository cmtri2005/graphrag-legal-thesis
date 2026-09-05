"""Thin client for the vbpl-bientap-gateway public document API."""
from __future__ import annotations

import time
from typing import Any

import requests

from .config import API_BASE, REQUEST_HEADERS

JsonDict = dict[str, Any]


class ApiClientError(RuntimeError):
    """Raised when the gateway returns a non-2xx or an unexpected payload."""


class DocumentNotFoundError(ApiClientError):
    """Raised for a 4xx response — permanent (dangling reference), not transient.
    Never retried: retrying a client error just wastes 3x the requests."""


class ApiClient:
    """Fetches document data, with basic retry/backoff and pacing.

    ponytail: single fixed delay + linear backoff, no adaptive rate control.
    Revisit if the gateway starts returning 429s under real load.
    """

    def __init__(
        self,
        session: requests.Session | None = None,
        *,
        min_interval_seconds: float = 0.3,
        max_retries: int = 3,
    ) -> None:
        self._session = session or requests.Session()
        self._min_interval = min_interval_seconds
        self._max_retries = max_retries
        self._last_request_at = 0.0

    def get_document(self, doc_id: str) -> JsonDict:
        return self._get(f"/qtdc/public/doc/{doc_id}")

    def get_history(self, doc_id: str) -> JsonDict:
        """Effective-date timeline — the core input for Stage 6 (point-in-time).

        NOT wired into build_graph.py yet: the Stage 2-3 crawl only persisted
        /doc/{id}. Stage 6 needs this for every document, so it still has to be
        backfilled — see docs/crawling-plan.md §7.
        """
        return self._get(f"/qtdc/public/doc/{doc_id}/history")

    def get_diagram(self, doc_id: str) -> JsonDict:
        """Relations in BOTH directions — see diagram.py for why this matters.

        `references[]` on /doc/{id} only records relations pointing *outward*.
        This endpoint's `documentNamesBySource` is the only place the inbound
        ones appear ("who amended me"), which Stage 2's forward-only BFS
        cannot discover on its own.
        """
        return self._get(f"/qtdc/public/doc/{doc_id}/diagram")

    def _get(self, path: str) -> JsonDict:
        last_error: Exception | None = None
        for attempt in range(self._max_retries):
            self._respect_pacing()
            try:
                response = self._session.get(
                    f"{API_BASE}{path}", headers=REQUEST_HEADERS, timeout=30
                )
                if 400 <= response.status_code < 500:
                    try:
                        message = response.json().get("message")
                    except ValueError:
                        message = response.text
                    raise DocumentNotFoundError(f"{path}: {message}")
                response.raise_for_status()
                body = response.json()
            except (requests.RequestException, ValueError) as exc:
                last_error = exc
                time.sleep(1.0 * (attempt + 1))
                continue
            if not body.get("success"):
                raise ApiClientError(f"{path}: {body.get('message')}")
            return body["data"]
        raise ApiClientError(f"{path}: exhausted retries") from last_error

    def _respect_pacing(self) -> None:
        elapsed = time.monotonic() - self._last_request_at
        if elapsed < self._min_interval:
            time.sleep(self._min_interval - elapsed)
        self._last_request_at = time.monotonic()

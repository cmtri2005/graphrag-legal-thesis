"""Stage 5 — fetch the Chương/Điều/Khoản/Điểm tree for a document.

The JSON gateway does NOT carry this: `/doc/{id}`'s own `provisionTree` field
is null on every document we've crawled (checked across 1500 raw files, 0 had
it). The structure only comes from vbpl.vn's Next.js **server action**, which
returns a React Flight payload rather than plain JSON.

That gives us the article hierarchy as server-side ground truth instead of
something a regex over `documentContent.content` guessed at:

    Part -> Chapter -> Section -> Article -> Clause -> Point
    Phần -> Chương  -> Mục     -> Điều    -> Khoản  -> Điểm

Levels above Article are all optional and appear in whatever combination a
given document happens to use, so treat the hierarchy as "whatever nesting
came back", never as a fixed six-layer shape. Don't hard-code a depth.

Each node carries a stable UUID, so the tree doubles as a validation oracle
for whatever eventually splits the HTML body into text: parse the body, then
assert the shape matches this tree.

Note the tree has titles and ids but no body text — mapping text onto these
nodes is still Stage 5's job. This module only gets the skeleton.

Two things that look like bugs but aren't:

- **An empty tree is a legitimate answer.** Sắc lệnh from 1946, Công văn,
  Văn bản hợp nhất and Bản dịch typically return `[]` — those documents have
  no article structure recorded upstream. Record the empty result and move
  on; do not retry it.
- **The root level varies.** Some documents start at Part or Chapter, others
  go straight to Article. Don't assume any particular layer exists.
"""
from __future__ import annotations

import json
import time
from typing import Any

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Identifies the server action to invoke. This is a Next.js BUILD ID: it
# changes whenever vbpl.vn redeploys their frontend, and when it does every
# request starts coming back without a payload line. That's why
# `parse_flight_payload` raises instead of returning empty — a stale id must
# look like a broken crawler, not like "no document has any articles".
# To refresh: open a document page in a browser, watch the Network tab for the
# POST to the same URL, and copy its `next-action` request header.
NEXT_ACTION_ID = "94635012466e8fede44782d4237c10fe75501920"

# The server keys off the trailing `--{id}` only; the slug in front of it is
# never validated (verified against numeric, UUID and legacy `vbpqta_*` ids).
# So we skip reconstructing the real slug from the title entirely.
PAGE_URL_TEMPLATE = "https://vbpl.vn/van-ban/chi-tiet/x--{doc_id}"

REQUEST_HEADERS = {
    "accept": "text/x-component",
    "content-type": "text/plain;charset=UTF-8",
    "next-action": NEXT_ACTION_ID,
    "Referer": "https://vbpl.vn/",
    "User-Agent": "Mozilla/5.0 (compatible; legal-crawler/0.1)",
}

# React Flight streams numbered rows; row `1` holds the server action's return
# value. Row `0` is the routing envelope and is of no interest.
_PAYLOAD_ROW_PREFIX = "1:"

JsonList = list[dict[str, Any]]


class MissingPayloadRowError(RuntimeError):
    """The response carried no payload row. Two very different causes:

    1. **One bad document.** Observed on doc 142709: the stream comes back
       with rows `0` and `2` but row `1` never arrives, reproducibly. Rare —
       roughly 1 in 4000 — and permanent for that document, so retrying it
       forever is pointless. Log it and move on.
    2. **A rotated Next.js build id**, which breaks *every* document.

    Never treated as "this document has no articles": that would write empty
    trees over documents that really do have a structure. The caller tells the
    two causes apart by counting consecutive occurrences (see
    scripts/fetch_provision_trees.py) — a run of them means cause 2.
    """


def make_session() -> requests.Session:
    """Session that retries transient failures at the adapter level.

    urllib3's Retry already does backoff correctly, so there's no hand-rolled
    retry loop here. 4xx is deliberately absent from `status_forcelist` —
    same rule as `api_client.py`: client errors are permanent, retrying them
    just triples the request count.
    """
    session = requests.Session()
    retry = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["POST"],
    )
    session.mount("https://", HTTPAdapter(max_retries=retry))
    return session


def parse_flight_payload(text: str) -> JsonList:
    """Pull the provision tree out of a React Flight response body."""
    for line in text.splitlines():
        if line.startswith(_PAYLOAD_ROW_PREFIX):
            tree = json.loads(line[len(_PAYLOAD_ROW_PREFIX) :])
            return tree or []
    raise MissingPayloadRowError(
        f"no '{_PAYLOAD_ROW_PREFIX}' row in response "
        f"(rows present: {sorted({l.split(':', 1)[0] for l in text.splitlines() if ':' in l})})"
    )


def fetch_tree(session: requests.Session, doc_id: str, *, attempts: int = 3) -> JsonList:
    """Fetch one document's provision tree. `[]` means genuinely no structure.

    A missing payload row is retried before it's believed, since a transient
    blip and a permanently broken document look identical on one attempt.
    Retries do NOT rescue a document like 142709, which fails every time —
    that one is reported to the caller, which logs it and keeps going rather
    than killing the run (an earlier version aborted on the spot and lost
    hours of progress to a single document).
    """
    for attempt in range(1, attempts + 1):
        response = session.post(
            PAGE_URL_TEMPLATE.format(doc_id=doc_id),
            headers=REQUEST_HEADERS,
            data=json.dumps([doc_id]),
            timeout=30,
        )
        response.encoding = "utf-8"
        response.raise_for_status()
        try:
            return parse_flight_payload(response.text)
        except MissingPayloadRowError:
            if attempt == attempts:
                raise
            time.sleep(2.0 * attempt)
    raise AssertionError("unreachable")  # pragma: no cover


def count_by_level(tree: JsonList) -> dict[str, int]:
    """Node counts per level, for progress reporting and sanity checks."""
    counts: dict[str, int] = {}
    stack = list(tree)
    while stack:
        node = stack.pop()
        level = node.get("level") or "Unknown"
        counts[level] = counts.get(level, 0) + 1
        stack.extend(node.get("children") or [])
    return counts

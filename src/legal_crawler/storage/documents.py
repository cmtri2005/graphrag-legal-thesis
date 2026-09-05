"""Where crawl output lives on disk, and how it is read and written.

Every stage writes one JSON file per document under a `data/<stage>/` directory
keyed by doc_id, and every script had been spelling that out itself — the same
`json.loads(path.read_text(encoding="utf-8"))` in a dozen files and the same
`data / "trees" / f"{doc_id}.json"` in fifteen places. Getting the encoding
wrong in one of them corrupts Vietnamese text silently, so it is worth having
exactly one copy.

This is deliberately a few functions over a `Path`, not a storage abstraction:
the layout is plain files on purpose, so `ls` and `grep` still work on it.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

DEFAULT_DATA_DIR = Path("data")

# The repo's own data/ directory, for the verified code tables in `vocab` that
# ship with the source rather than being crawl output. Resolved here, once:
# three modules used to count `parent` levels themselves, which silently breaks
# the moment a file moves into a subpackage.
REPO_DATA_DIR = Path(__file__).resolve().parents[3] / "data"

# One directory per stage, all keyed by doc_id. A delta run drops a document's
# entry from each of these to make the ordinary scripts re-fetch it, so this
# tuple is also the definition of "everything cached about one document".
PER_DOCUMENT_DIRS = ("raw", "trees", "history", "diagrams", "provisions")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: Any) -> str:
    """Write `value` as UTF-8 JSON and return the exact text written.

    Returning the text is what lets callers hash precisely what landed on disk
    (`build_graph.py` stores that hash in the manifest); re-serialising to hash
    it would be a second chance to differ.
    """
    text = json.dumps(value, ensure_ascii=False)
    path.write_text(text, encoding="utf-8")
    return text


class DocumentStore:
    """The `data/` directory, addressed by stage and doc_id."""

    def __init__(self, root: Path = DEFAULT_DATA_DIR) -> None:
        self.root = root

    def dir(self, stage: str) -> Path:
        return self.root / stage

    def path(self, stage: str, doc_id: str) -> Path:
        return self.root / stage / f"{doc_id}.json"

    def ids(self, stage: str) -> set[str]:
        """doc_ids present for a stage. Absent directory means none, not an
        error — stages run in sequence and the later ones legitimately don't
        exist yet on a fresh checkout."""
        return {p.stem for p in self.dir(stage).glob("*.json")}

    def load(self, stage: str, doc_id: str) -> Any:
        return read_json(self.path(stage, doc_id))

    def save(self, stage: str, doc_id: str, value: Any) -> str:
        directory = self.dir(stage)
        directory.mkdir(parents=True, exist_ok=True)
        return write_json(directory / f"{doc_id}.json", value)

    def drop(self, doc_id: str) -> int:
        """Delete every cached file for one document; returns how many went.

        This is the whole mechanism behind delta crawling: the fetching scripts
        treat an existing file as their checkpoint, so removing it is how a
        document gets re-fetched.
        """
        removed = 0
        for stage in PER_DOCUMENT_DIRS:
            path = self.path(stage, doc_id)
            if path.exists():
                path.unlink()
                removed += 1
        return removed


def load_permanent_failures(path: Path, stage: str) -> set[str]:
    """doc_ids recorded in `data/fetch_failures.txt` as unfetchable for `stage`.

    These fail every time — HTTP 500 from vbpl.vn itself, or a response with no
    payload row — so retrying them costs a request each and buys nothing. Worse,
    a re-run consisting only of known-bad documents looks exactly like a rotated
    build id to `fetch_provision_trees.py`'s abort heuristic.
    """
    if not path.exists():
        return set()
    ids: set[str] = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("#") or not line.strip():
            continue
        fields = line.split("\t")
        if len(fields) >= 2 and fields[0] == stage:
            ids.add(fields[1])
    return ids

#!/usr/bin/env python3
"""ViLexTime E1 — is the "before" side of a released T2/T4 pair the original wording?

The risk (plan phase-4, Risks): the portal may serve an amended document with
the amendment already folded into its text, which would make every "before"
answer really an "after". The consolidated-text comparison
(compare_consolidated_snapshots.py) cannot see before-sides, so this checks
each released pair directly:

  before_in_base   the before answer occurs in the base document's raw text
  after_in_base    the whole after answer occurs there too (suspicious unless it
                   is a prefix of the before text or a sibling's wording)
  new_in_actor     the phrases the after answer adds (≥3 words) occur in the
                   amending document, i.e. the change has a source

Read-only. Prints counts and lists every pair that is not clean.

Usage:
    python scripts/check/check_before_side.py
"""
from __future__ import annotations

import argparse
import collections
import difflib
import html
import json
import re
import unicodedata
from functools import lru_cache
from pathlib import Path


def norm(text: str | None) -> str:
    text = unicodedata.normalize("NFC", html.unescape(re.sub(r"<[^>]+>", " ", text or "")))
    return " ".join(re.sub(r"\s+([,.;:])", r"\1", text).split()).lower()


def added_phrases(before: str, after: str) -> list[str]:
    b, a = before.split(), after.split()
    ops = difflib.SequenceMatcher(None, b, a, autojunk=False).get_opcodes()
    return [" ".join(a[j1:j2]) for tag, _, _, j1, j2 in ops if tag in ("insert", "replace") and j2 - j1 >= 3]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data", type=Path, default=Path("data"))
    d = ap.parse_args().data

    @lru_cache(maxsize=64)
    def raw(document_id: str) -> str | None:
        path = d / "raw" / f"{document_id.split(':', 1)[1]}.json"
        return norm((json.loads(path.read_text(encoding="utf-8")).get("documentContent") or {}).get("content")) \
            if path.exists() else None

    pairs: dict[str, list[dict]] = collections.defaultdict(list)
    for line in (d / "derived/vilextime/selected.jsonl").open(encoding="utf-8"):
        r = json.loads(line)
        if r["group"] in ("T2", "T4"):
            pairs[r["lineage_id"]].append(r)

    counts, flagged = collections.Counter(), []
    for lid, rs in sorted(pairs.items()):
        before, after = sorted(rs, key=lambda r: r["as_of"])
        actor = before["derivation"]["transitions"][0]["actor"]
        base, source = raw(before["target"]["document_id"]), raw(actor["document_id"]) or ""
        nb, na = norm(before["answer"]), norm(after["answer"])
        new = added_phrases(nb, na)
        facts = {
            "original_version": before["version_id"].endswith(":1"),
            "before_in_base": base is not None and nb in base,
            "after_in_base": base is not None and na in base and not nb.startswith(na),
            "new_in_actor": all(p in source for p in new),
        }
        counts["pairs"] += 1
        counts.update(k for k, v in facts.items() if v)
        if not facts["before_in_base"] or facts["after_in_base"] or not facts["original_version"]:
            flagged.append((before["group"], before["target"]["law_id"], before["target"]["citation"],
                            actor["law_id"], {k: v for k, v in facts.items() if k != "new_in_actor"}))
    print(dict(counts))
    for row in flagged:
        print("  kiểm tay:", *row)


if __name__ == "__main__":
    main()

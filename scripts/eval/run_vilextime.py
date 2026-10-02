#!/usr/bin/env python3
"""Run one system over ViLexTime and write the file the scorer reads (plan phase-5-6, P1).

    python scripts/eval/run_vilextime.py --system b1 --split dev --out preds.jsonl
    python scripts/eval/score_vilextime.py preds.jsonl --split dev

Output is the scorer's contract, one line per release row:

    {"id": ..., "answer": ..., "answerable": ..., "citations": [...], "retrieved": [...]}

**The runner sees three fields of each row and nothing else.** `Query` carries
`id`, `question` and `as_of`; no code downstream is handed the release row, so
`answer`, `short_answer`, `evidence_set` and `accepted_evidence` cannot reach a
prompt. That is enforced by structure rather than by care, because a leak would
not show up as an error — it would show up as a good score.

A run resumes by default: ids already present in `--out` are skipped, which is
what a rate-limited provider and a 2.481-row split require. `--restart` forgets
them.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from vilexgraph.llm import LLMError  # noqa: E402
from vilexgraph.framework import generate, systems, verify  # noqa: E402
from vilexgraph.framework.corpus import Corpus  # noqa: E402

RELEASE = Path("data/derived/vilextime/release.jsonl")
INDEX = Path("data/derived/corpus/index.sqlite")
CACHE = Path("data/derived/rag/completions.sqlite")
HITS = Path("data/derived/rag/retrieval.sqlite")


@dataclass(frozen=True, slots=True)
class Query:
    """Everything a system is allowed to know about a row."""

    id: str
    question: str
    as_of: str


def queries(release: Path, split: str | None, limit: int | None) -> list[Query]:
    rows = [json.loads(line) for line in release.open(encoding="utf-8")]
    chosen = "test" if split is None and any(r.get("split") for r in rows) else split
    kept = [r for r in rows
            if r.get("split") != "excluded" and (chosen is None or r.get("split") == chosen)]
    out = [Query(r["id"], r["question"], r["as_of"]) for r in kept]
    return out[:limit] if limit else out


def done_ids(out: Path) -> set[str]:
    if not out.exists():
        return set()
    found = set()
    for line in out.open(encoding="utf-8"):
        line = line.strip()
        if not line:
            continue
        try:
            found.add(json.loads(line)["id"])
        except (json.JSONDecodeError, KeyError):
            continue
    return found


def retriever(spec: systems.SystemSpec, corpus: Corpus | None, hits: Path | None,
              fast: bool = False):
    """The search callable for this system, or None when it does not retrieve."""
    if not spec.retrieves:
        return None
    from vilexgraph.framework import retrieve  # imported late: P1 ships without it
    return retrieve.searcher(corpus, spec, retrieve.RetrievalCache(hits), fast=fast)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--system", required=True, help=f"one of: {', '.join(sorted(systems.REGISTRY))}")
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--release", type=Path, default=RELEASE)
    ap.add_argument("--index", type=Path, default=INDEX)
    ap.add_argument("--split", help="default: test once the release is split")
    ap.add_argument("--limit", type=int)
    ap.add_argument("--k", type=int, help="override the system's retrieval depth")
    ap.add_argument("--provider")
    ap.add_argument("--model")
    ap.add_argument("--no-dense", action="store_true",
                    help="run a dense-capable system on lexical retrieval alone")
    ap.add_argument("--cache", type=Path, default=CACHE)
    ap.add_argument("--hits-cache", type=Path, default=HITS,
                    help="cache of ranked retrieval results, keyed by configuration")
    ap.add_argument("--no-cache", action="store_true")
    ap.add_argument("--restart", action="store_true", help="ignore rows already in --out")
    ap.add_argument("--fast-retrieval", action="store_true",
                    help="trade recall for speed on long questions (dev iteration only; "
                         "measured R@1 0.400 vs 0.440 — never for a reported result)")
    ap.add_argument("--retrieval-only", action="store_true",
                    help="skip generation: fill `retrieved` and leave the answer empty. "
                         "Recall@k, TV-Recall@k and MRR depend only on retrieval, so the "
                         "ladder's retrieval table costs no LLM calls")
    args = ap.parse_args()

    spec = systems.get(args.system)
    if args.no_dense and spec.dense:
        spec = spec.variant(f"{spec.name}-lex", dense=False, rerank=False)
    if args.k:
        spec = spec.variant(spec.name, k=args.k)

    rows = queries(args.release, args.split, args.limit)
    skip = set() if args.restart else done_ids(args.out)
    todo = [q for q in rows if q.id not in skip]
    print(f"system {spec.name} · {len(rows)} rows · {len(skip)} already done · {len(todo)} to run",
          file=sys.stderr)
    if spec.note:
        print(f"  {spec.note}", file=sys.stderr)

    corpus = Corpus(args.index) if spec.retrieves else None
    search = retriever(spec, corpus, None if args.no_cache else args.hits_cache,
                       fast=args.fast_retrieval)
    cache = generate.Cache(None if args.no_cache else args.cache)
    args.out.parent.mkdir(parents=True, exist_ok=True)

    written = failed = cached = 0
    started = time.monotonic()
    with args.out.open("a" if skip and not args.restart else "w", encoding="utf-8") as sink:
        for n, q in enumerate(todo, 1):
            try:
                hits = search(q.question, q.as_of) if search else []
                verdict = None
                if args.retrieval_only:
                    got = generate.Answer("", True, (), "", "none", "none")
                else:
                    units = corpus.units([h.unit_id for h in hits]) if corpus and hits else []
                    ask = lambda evidence: generate.answer(  # noqa: E731
                        q.question, q.as_of, evidence, with_context=spec.context,
                        provider=args.provider, model=args.model, cache=cache)
                    got = ask(units)
                    if corpus and spec.verify != "off":
                        got, verdict = verify.verify(
                            corpus, mode=spec.verify, tier=spec.temporal, as_of=q.as_of,
                            units=units, answer=got, regenerate=ask)
            except LLMError as exc:
                # A missing key or a dead model must not look like 2.000 wrong answers.
                if written == 0:
                    raise SystemExit(f"first row failed, stopping: {exc}") from None
                failed += 1
                print(f"  row {q.id} failed: {exc}", file=sys.stderr)
                continue
            cached += got.cached
            line = {"id": q.id, "answer": got.text, "answerable": got.answerable,
                    "citations": list(got.citations),
                    "retrieved": [h.unit_id for h in hits]}
            if verdict is not None:
                line["verification"] = verdict.as_dict()
            if hits:
                # Kept per candidate so A1–A4 can be re-read without re-running the grid
                # (plan: store each signal separately). The scorer ignores extra keys.
                line["signals"] = {h.unit_id: h.signals for h in hits}
            sink.write(json.dumps(line, ensure_ascii=False) + "\n")
            sink.flush()
            written += 1
            if n % 50 == 0:
                rate = n / max(time.monotonic() - started, 1e-9)
                print(f"  {n}/{len(todo)} · {rate:.1f} rows/s · {cached} cached · {failed} failed",
                      file=sys.stderr)

    print(f"\n{args.out}: {written} written, {cached} from cache, {failed} failed "
          f"in {time.monotonic() - started:.1f}s", file=sys.stderr)
    print(f"score it:\n  python scripts/eval/score_vilextime.py {args.out}"
          + (f" --split {args.split}" if args.split else ""), file=sys.stderr)


if __name__ == "__main__":
    main()

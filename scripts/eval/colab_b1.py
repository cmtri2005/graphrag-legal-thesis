#!/usr/bin/env python3
"""Export gold-free B1 prompts and import raw Colab completions for local scoring."""
from __future__ import annotations

import argparse
import hashlib
import json
import random
import subprocess
import sys
from dataclasses import asdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from vilexgraph.framework import generate, systems, verify  # noqa: E402
from vilexgraph.framework.corpus import Corpus  # noqa: E402
from run_vilextime import EMBED, INDEX, RELEASE, queries, retriever  # noqa: E402


ORACLE = "oracle"
SPLITS = ("dev", "test")
ADR = Path(__file__).resolve().parents[2] / "docs/decisions/0005-ke-hoach-phan-tich.md"


def adr_accepted(path: Path = ADR) -> bool:
    """ADR 0005 §Status reads Accepted in the committed file, not only in the working tree."""
    text = subprocess.run(["git", "show", f"HEAD:{path.relative_to(path.parents[2])}"],
                          cwd=path.parents[2], capture_output=True, text=True).stdout
    status = text.split("## Status", 1)[-1].split("##", 1)[0]
    return status.strip().startswith("Accepted")


def digest(row: dict) -> str:
    fields = [row["id"], row["system"], row["user"], row["ids"], row["retrieved"]]
    if "system_name" in row:
        fields += [row["system_name"], row["split"], row["as_of"], row["signals"]]
    payload = json.dumps(fields,
                         ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(payload.encode()).hexdigest()


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def export_prompts(args) -> None:
    if args.split not in SPLITS or args.as_of_strategy != "giua_khoang":
        raise SystemExit("Colab export requires --split dev|test --as-of-strategy giua_khoang")
    if args.split == "test" and not adr_accepted():
        raise SystemExit(f"test prompts need {ADR} Accepted and committed first (plan, gate G)")
    name = getattr(args, "system", "b2ctx")
    # B5 oracle context: the gold unit alone (the version in force, or for a repealed row the
    # repeal), an upper bound kept out of the runner, which never sees gold. Adding the repealed
    # row's last version was tried on dev and scored lower (runs/README.md, 29/10).
    oracle = name == ORACLE
    spec = systems.get("b2ctx" if oracle else name)
    if getattr(args, "no_dense", False) and spec.dense:
        spec = spec.variant(f"{spec.name}-lex", dense=False, rerank=False)
    embed = getattr(args, "embed", EMBED) if spec.dense and not oracle else None
    corpus = Corpus(args.index) if spec.retrieves else None
    search = None if oracle else retriever(spec, corpus, args.hits_cache, embed=embed)
    gold = {r["id"]: [r["version_id"]] if r["version_id"] else r["accepted_evidence"]
            for r in read_jsonl(args.release)} if oracle else {}
    rows = []
    limit = args.limit if args.limit > 0 else None
    for q in queries(args.release, args.split, limit, args.as_of_strategy):
        hits = search(q.question, q.as_of) if search else []
        retrieved = gold[q.id] if oracle else [h.unit_id for h in hits]
        units = corpus.units(retrieved) if corpus and retrieved else []
        if oracle and len(units) != len(retrieved):
            raise SystemExit(f"{q.id}: gold unit not in the corpus: {retrieved}")
        system, user, ids = generate.build_prompt(q.question, q.as_of, units,
                                                   with_context=spec.context)
        row = {"id": q.id, "system": system, "user": user, "ids": ids,
               "retrieved": retrieved}
        if name != "b2ctx" or getattr(args, "b2", False):
            row.update({"system_name": name, "split": args.split, "as_of": q.as_of,
                        "signals": {u: {} for u in retrieved} if oracle else
                                   {h.unit_id: h.signals for h in hits}})
        row["prompt_sha256"] = digest(row)
        rows.append(row)
    if (not rows or (limit and len(rows) != limit) or len({r["id"] for r in rows}) != len(rows)):
        raise SystemExit(f"expected {limit or 'all'} unique dev rows; found {len(rows)}")
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")
    if getattr(args, "b2", False):
        manifest = args.index.parent / "manifest.json"
        export_record = {"system": name, "spec": None if oracle else asdict(spec), "split": args.split,
                         "as_of_strategy": "giua_khoang", "no_dense": bool(getattr(args, "no_dense", False)),
                         "embed": str(embed) if embed else None,
                         "embed_sha256": hashlib.sha256(embed.with_suffix(".sha256").read_bytes()).hexdigest()
                         if embed and embed.with_suffix(".sha256").exists() else None,
                         "rows": len(rows), "release_sha256": hashlib.sha256(args.release.read_bytes()).hexdigest(),
                         "corpus_manifest_sha256": hashlib.sha256(manifest.read_bytes()).hexdigest()
                         if manifest.exists() else None,
                         "prompt_file_sha256": hashlib.sha256(args.out.read_bytes()).hexdigest()}
        args.out.with_suffix(".export.json").write_text(
            json.dumps(export_record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"{args.out}: {len(rows)} gold-free {name} prompts, "
          f"sha256={hashlib.sha256(args.out.read_bytes()).hexdigest()}")


def import_completions(args) -> None:
    prompts = read_jsonl(args.prompts)
    by_id = {r["id"]: r for r in prompts}
    if len(by_id) != len(prompts):
        raise SystemExit("duplicate prompt id")
    names = {r.get("system_name", "b2ctx") for r in prompts}
    if len(names) != 1:
        raise SystemExit(f"mixed systems in prompts: {names}")
    system_name = next(iter(names))
    splits = {r.get("split", "dev") for r in prompts}
    if len(splits) != 1 or not splits <= set(SPLITS):
        raise SystemExit(f"B2 import requires one split, dev or test; found {splits}")
    export_record = None
    if "system_name" in prompts[0]:
        record_path = args.prompts.with_suffix(".export.json")
        if not record_path.exists():
            raise SystemExit("B2 prompt export record is missing")
        export_record = json.loads(record_path.read_text(encoding="utf-8"))
        if (export_record["system"] != system_name or export_record["rows"] != len(prompts)
                or export_record["prompt_file_sha256"] != hashlib.sha256(args.prompts.read_bytes()).hexdigest()):
            raise SystemExit("B2 prompt export record mismatch")
    spec = None if system_name == ORACLE else systems.get(system_name)
    corpus = Corpus(getattr(args, "index", INDEX)) if spec and spec.verify != "off" else None
    completions = read_jsonl(args.raw)
    seen, models, predictions = set(), set(), []
    for item in completions:
        row_id = item["id"]
        if row_id not in by_id or row_id in seen:
            raise SystemExit(f"unknown or duplicate completion id: {row_id}")
        prompt = by_id[row_id]
        if item.get("prompt_sha256") != prompt["prompt_sha256"] or digest(prompt) != prompt["prompt_sha256"]:
            raise SystemExit(f"prompt mismatch for {row_id}")
        if not isinstance(item.get("raw"), str):
            raise SystemExit(f"missing raw completion for {row_id}")
        if item.get("finish_reason") not in ("eos", "stop", "length"):
            raise SystemExit(f"unknown finish_reason for {row_id}")
        if not all(isinstance(item.get(key), (int, float)) and item[key] >= 0
                   for key in ("prompt_tokens", "completion_tokens", "elapsed_s")):
            raise SystemExit(f"missing token/time measurement for {row_id}")
        seen.add(row_id)
        models.add((item["model"], item["revision"]))
        answer, answerable, citations = generate.parse(item["raw"], prompt["ids"])
        prediction = {"id": row_id, "answer": answer, "answerable": answerable,
                            "citations": list(citations), "retrieved": prompt["retrieved"],
                            "format_ok": generate.format_ok(item["raw"], citations,
                                                            has_evidence=bool(prompt["ids"])),
                            "truncated": item["finish_reason"] == "length",
                            "prompt_tokens": item["prompt_tokens"],
                            "completion_tokens": item["completion_tokens"]}
        if "system_name" in prompt:
            prediction["signals"] = prompt["signals"]
        if corpus:
            bad = verify.invalid_units(corpus, spec.temporal, prompt["as_of"], citations)
            if bad:
                raise SystemExit(f"{row_id}: verifier needs regeneration for {bad}")
            prediction["verification"] = {"mode": spec.verify, "action": "pass",
                                          "checked": len(citations), "invalid": [], "cause": None}
        predictions.append(prediction)
    if len(models) != 1 or not models:
        raise SystemExit(f"expected one model/revision, found {models}")
    if len(predictions) != len(prompts):
        raise SystemExit(f"incomplete B1 result: {len(predictions)}/{len(prompts)} rows")
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in predictions), encoding="utf-8")
    picked = random.Random("vilextime-colab-b1-2710").sample(completions, min(20, len(completions)))
    sample = args.out.with_suffix(".sample.jsonl")
    sample.write_text("".join(json.dumps({"id": r["id"], "raw": r["raw"]}, ensure_ascii=False) + "\n"
                              for r in picked), encoding="utf-8")
    good = sum(r["format_ok"] for r in predictions)
    cut = sum(r["truncated"] for r in predictions)
    n = len(predictions)
    record = {"system": system_name, "split": next(iter(splits)), "as_of_strategy": "giua_khoang",
              "prompt_file_sha256": hashlib.sha256(args.prompts.read_bytes()).hexdigest(),
              "raw_file_sha256": hashlib.sha256(args.raw.read_bytes()).hexdigest(),
              "model": next(iter(models))[0], "revision": next(iter(models))[1],
              # Later runtimes write the GPU list per row instead of a joined string.
              "gpu": sorted({" + ".join(g) if isinstance(g, list) else g
                             for g in (r.get("gpu", "unknown") for r in completions)}),
              "rows": n, "format_ok": good, "truncated": cut,
              "prompt_tokens_mean": sum(r["prompt_tokens"] for r in predictions) / n,
              "completion_tokens_mean": sum(r["completion_tokens"] for r in predictions) / n,
              "generation_seconds": sum(r["elapsed_s"] for r in completions)}
    if export_record:
        record["export"] = export_record
    args.out.with_suffix(".run.json").write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n",
                                                     encoding="utf-8")
    print(f"{args.out}: {n} rows, format {good}/{n} ({good/n:.1%}), truncated {cut}; "
          f"mean input/output tokens {sum(r['prompt_tokens'] for r in predictions)/n:.0f}/"
          f"{sum(r['completion_tokens'] for r in predictions)/n:.0f}; "
          f"generation {record['generation_seconds']:.0f}s; model {next(iter(models))}")
    print(f"20-answer review sample: {sample}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)
    ex = sub.add_parser("export")
    ex.add_argument("--release", type=Path, default=RELEASE)
    ex.add_argument("--index", type=Path, default=INDEX)
    ex.add_argument("--hits-cache", type=Path, default=Path("data/derived/rag/retrieval.sqlite"))
    ex.add_argument("--split", required=True)
    ex.add_argument("--as-of-strategy", required=True)
    ex.add_argument("--limit", type=int, default=100, help="0 exports every dev giua_khoang row")
    ex.add_argument("--system", choices=sorted(systems.REGISTRY) + [ORACLE], default="b2ctx")
    ex.add_argument("--no-dense", action="store_true")
    ex.add_argument("--embed", type=Path, default=EMBED, help="embeddings for dense systems (b3, b4)")
    ex.add_argument("--b2", action="store_true", help="include B2 metadata for b2ctx prompts")
    ex.add_argument("--out", required=True, type=Path)
    im = sub.add_parser("import")
    im.add_argument("--prompts", required=True, type=Path)
    im.add_argument("--raw", required=True, type=Path)
    im.add_argument("--out", required=True, type=Path)
    im.add_argument("--index", type=Path, default=INDEX)
    args = ap.parse_args()
    (export_prompts if args.cmd == "export" else import_completions)(args)


if __name__ == "__main__":
    main()

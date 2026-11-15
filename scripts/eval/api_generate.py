#!/usr/bin/env python3
"""Answer an exported prompt file through a chat API, writing the raw file `colab_b1 import` reads.

One path for every generator: `colab_b1.py export` builds gold-free prompts with a hash per row,
a runtime turns them into raw completions (this script, or `colab_b1_runtime.py` on a GPU), and
import checks the hashes. A closed model cannot be re-run later, so the raw text is the evidence.

Spending is resumable: rows already in the raw file are never requested again, so `--limit 3`,
then `--limit 100`, then the whole file extend one run. Any provider error stops the run rather
than leaving a gap, and the same command continues it. A truncated answer is recorded, because
stopping would stall on that row at every rerun.

`--batch` (OpenAI only) sends the same request bodies through the Batch API at half the price and
returns within 24 hours. One command submits the rows still unanswered as one batch; rerunning the
same command polls it, and once it is finished writes the answers into the same raw file in the same
shape, so import, scoring and the hash checks do not change. Rows the batch did not answer are sent
again by the next run. Use `--limit` to keep one batch under the account's enqueued-token limit.

Example, dev only:
    python scripts/eval/colab_b1.py export --system b2ctx --split dev \
        --as-of-strategy giua_khoang --limit 0 --b2 --out runs/G_dev/prompts/b2ctx.jsonl
    python scripts/eval/api_generate.py --prompts runs/G_dev/prompts/b2ctx.jsonl \
        --provider openai --model gpt-4o-mini-2024-07-18 --out-dir runs/G_dev/raw --limit 3
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from colab_b1 import digest, read_jsonl  # noqa: E402
from final_run import guard_test  # noqa: E402
from vilexgraph import llm  # noqa: E402

SETTINGS = ("provider", "model", "temperature", "max_tokens", "seed")


def git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True).stdout.strip()


def load_done(raw: Path, prompts: dict[str, dict]) -> set[str]:
    """Ids already paid for. A line cut by a crash is dropped; a changed prompt stops the run."""
    if not raw.exists():
        return set()
    data = raw.read_bytes()
    if data and not data.endswith(b"\n"):
        data = data[:data.rfind(b"\n") + 1]
        raw.write_bytes(data)
    done = set()
    for item in map(json.loads, data.decode("utf-8").splitlines()):
        if prompts.get(item["id"], {}).get("prompt_sha256") != item["prompt_sha256"]:
            raise SystemExit(f"{raw}: {item['id']} was answered from a different prompt")
        done.add(item["id"])
    return done


def call(row: dict, args: argparse.Namespace) -> dict:
    started = time.perf_counter()
    try:
        done = llm.complete(row["system"], row["user"], provider=args.provider, model=args.model,
                            temperature=args.temperature, max_tokens=args.max_tokens, seed=args.seed)
    except llm.Truncated as cut:
        if cut.completion is None:
            raise
        done = cut.completion
    if done.finish_reason not in ("stop", "length"):
        raise llm.LLMError(f"{row['id']}: finish_reason {done.finish_reason!r}, content not usable")
    if done.prompt_tokens is None or done.completion_tokens is None:
        raise llm.LLMError(f"{row['id']}: provider sent no token usage")
    return {"id": row["id"], "prompt_sha256": row["prompt_sha256"], "model": args.model,
            # Import requires one (model, revision) pair, so a drifting alias stops it there.
            "revision": done.served_model or args.model, "raw": done.text,
            "finish_reason": done.finish_reason, "prompt_tokens": done.prompt_tokens,
            "completion_tokens": done.completion_tokens,
            "elapsed_s": time.perf_counter() - started, "gpu": "api", "provider": args.provider,
            "system_fingerprint": done.system_fingerprint}


BATCH_ENDPOINT = "/v1/chat/completions"


def openai_request(method: str, path: str, **kwargs) -> requests.Response:
    """One call to the OpenAI files/batches API (the only place the batch path touches the network)."""
    base, key, _ = llm.PROVIDERS["openai"]
    response = requests.request(method, f"{base}{path}", timeout=120,
                                headers={"Authorization": f"Bearer {os.environ[key]}"}, **kwargs)
    if not response.ok:
        raise SystemExit(f"openai {method} {path}: {response.status_code} {response.text[:400]}")
    return response


def batch_submit(todo: list[dict], args: argparse.Namespace, state_path: Path) -> None:
    lines = [json.dumps({"custom_id": r["id"], "method": "POST", "url": BATCH_ENDPOINT,
                         "body": llm.chat_payload(r["system"], r["user"], model=args.model,
                                                  temperature=args.temperature, max_tokens=args.max_tokens,
                                                  seed=args.seed)}, ensure_ascii=False) for r in todo]
    body = ("\n".join(lines) + "\n").encode("utf-8")
    upload = openai_request("POST", "/files", data={"purpose": "batch"},
                            files={"file": (state_path.stem + ".input.jsonl", body)}).json()
    batch = openai_request("POST", "/batches", json={"input_file_id": upload["id"], "endpoint": BATCH_ENDPOINT,
                                                     "completion_window": "24h"}).json()
    state_path.write_text(json.dumps({
        "batch_id": batch["id"], "input_file_id": upload["id"], "input_sha256": hashlib.sha256(body).hexdigest(),
        "rows": len(todo), "submitted": datetime.now(timezone.utc).isoformat(timespec="seconds")},
        indent=2) + "\n", encoding="utf-8")
    print(f"submitted batch {batch['id']} with {len(todo)} rows; rerun the same command to collect", file=sys.stderr)


def batch_collect(state_path: Path, args: argparse.Namespace, by_id: dict, keep, skip: set[str]) -> bool:
    """Write what a finished batch answered. False while it is still running."""
    state = json.loads(state_path.read_text(encoding="utf-8"))
    batch = openai_request("GET", f"/batches/{state['batch_id']}").json()
    status = batch["status"]
    if status not in ("completed", "failed", "expired", "cancelled"):
        print(f"batch {state['batch_id']}: {status} {batch.get('request_counts')}; rerun later", file=sys.stderr)
        return False
    refused = []
    if batch.get("output_file_id"):
        text = openai_request("GET", f"/files/{batch['output_file_id']}/content").text
        for line in filter(None, text.splitlines()):
            item = json.loads(line)
            row_id, response = item["custom_id"], item.get("response") or {}
            if row_id not in by_id or row_id in skip or response.get("status_code") != 200:
                continue                      # unanswered: the next run sends it again
            done = llm.read_completion(response["body"], "openai", args.model, args.temperature)
            if done.finish_reason not in ("stop", "length") or done.prompt_tokens is None:
                refused.append(row_id)
                continue
            keep({"id": row_id, "prompt_sha256": by_id[row_id]["prompt_sha256"], "model": args.model,
                  "revision": done.served_model or args.model, "raw": done.text,
                  "finish_reason": done.finish_reason, "prompt_tokens": done.prompt_tokens,
                  "completion_tokens": done.completion_tokens, "elapsed_s": 0.0, "gpu": "api-batch",
                  "provider": "openai", "system_fingerprint": done.system_fingerprint,
                  "batch_id": state["batch_id"]})
    history = state_path.with_suffix(".done.jsonl")
    with history.open("a", encoding="utf-8") as sink:
        sink.write(json.dumps({**state, "status": status, "request_counts": batch.get("request_counts"),
                               "refused": refused}) + "\n")
    state_path.unlink()
    print(f"batch {state['batch_id']}: {status}; {len(refused)} refused rows left for the next run", file=sys.stderr)
    return True


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--prompts", type=Path, required=True)
    ap.add_argument("--out-dir", type=Path, required=True)
    ap.add_argument("--provider", required=True, choices=sorted(llm.PROVIDERS))
    ap.add_argument("--model", required=True, help="a dated id, so the run names one snapshot")
    ap.add_argument("--temperature", type=float, default=0.0)
    ap.add_argument("--max-tokens", type=int, default=1024)
    ap.add_argument("--seed", type=int, default=20261109, help="best effort on providers that take one")
    ap.add_argument("--run-tag", help="r1, r2, ...: a separate raw file per independent run of the same prompts "
                                      "(ADR 0006 5b); a tagged run never counts the other run's rows as answered")
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--limit", type=int, help="stop after this many rows of the file are answered")
    ap.add_argument("--ids", type=Path, help="only these row ids, one per line, for a targeted probe")
    ap.add_argument("--batch", action="store_true", help="OpenAI Batch API: half price, answers within 24 h")
    args = ap.parse_args()
    if args.batch and args.provider != "openai":
        raise SystemExit("--batch is OpenAI only")

    rows = read_jsonl(args.prompts)
    by_id = {r["id"]: r for r in rows}
    if len(by_id) != len(rows):
        raise SystemExit("duplicate prompt id")
    bad = [r["id"] for r in rows if digest(r) != r["prompt_sha256"]]
    if bad:
        raise SystemExit(f"{len(bad)} prompts do not match their hash, first {bad[0]}")
    if args.run_tag and not re.fullmatch(r"r\d+", args.run_tag):
        raise SystemExit("--run-tag must look like r1, r2")
    splits = {r.get("split", "dev") for r in rows}
    if len(splits) != 1:
        raise SystemExit(f"mixed splits: {splits}")
    split = splits.pop()
    guard_test(split, [args.prompts], root=ROOT)

    names = {r.get("system_name", "b2ctx") for r in rows}
    if len(names) != 1:
        raise SystemExit(f"mixed systems: {names}")
    system = names.pop()
    file_sha = hashlib.sha256(args.prompts.read_bytes()).hexdigest()
    args.out_dir.mkdir(parents=True, exist_ok=True)
    raw = args.out_dir / f"{system}__{args.model.replace('/', '__')}__{file_sha[:12]}{'.' + args.run_tag if args.run_tag else ''}.jsonl"
    meta_path = raw.with_suffix(".meta.json")

    settings = {k: getattr(args, k) for k in SETTINGS}
    if meta_path.exists():
        before = json.loads(meta_path.read_text(encoding="utf-8"))
        if {k: before[k] for k in SETTINGS} != settings:
            raise SystemExit(f"{raw.name} was started with {before}; one file holds one configuration")
        if before.get("transport", "direct") != ("batch" if args.batch else "direct"):
            raise SystemExit(f"{raw.name} was started with transport {before.get('transport', 'direct')}; "
                             "one file holds one transport")
    else:
        meta_path.write_text(json.dumps({
            **settings, "transport": "batch" if args.batch else "direct",
            "system": system, "split": split, "prompt_file_sha256": file_sha,
            "run_tag": args.run_tag, "commit": git("rev-parse", "HEAD"),
            "uncommitted": bool(git("status", "--porcelain", "--untracked-files=no")),
            "started": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    done = load_done(raw, by_id)
    chosen = rows
    if args.ids:
        wanted = set(args.ids.read_text(encoding="utf-8").split())
        if wanted - set(by_id):
            raise SystemExit(f"{len(wanted - set(by_id))} ids are not in {args.prompts}")
        chosen = [r for r in rows if r["id"] in wanted]
    if args.limit is not None:
        chosen = chosen[:args.limit]
    todo = [r for r in chosen if r["id"] not in done]
    print(f"{system} {split}: {len(rows)} prompts, {len(done)} already answered, {len(todo)} to request",
          file=sys.stderr)

    written: set[str] = set()
    error: Exception | None = None
    tokens = [0, 0]
    with raw.open("a", encoding="utf-8") as sink:
        def keep(item: dict) -> None:
            sink.write(json.dumps(item, ensure_ascii=False) + "\n")
            sink.flush()
            os.fsync(sink.fileno())
            written.add(item["id"])
            tokens[0] += item["prompt_tokens"]
            tokens[1] += item["completion_tokens"]
            if len(written) % 50 == 0:
                print(f"  {len(written)}/{len(todo)}", file=sys.stderr)

        if args.batch:
            state_path = raw.with_suffix(".batch.json")
            if state_path.exists():
                if not batch_collect(state_path, args, by_id, keep, done):
                    return
            else:
                if todo:
                    batch_submit(todo, args, state_path)
                return
            todo = []
        pool = ThreadPoolExecutor(args.workers)
        futures = [pool.submit(call, row, args) for row in todo]
        try:
            for future in as_completed(futures):
                keep(future.result())
        except (llm.LLMError, requests.RequestException) as exc:
            error = exc
        pool.shutdown(wait=True, cancel_futures=True)
        # Calls in flight when the run stopped were paid for.
        for future in futures:
            if future.done() and not future.cancelled() and future.exception() is None \
                    and future.result()["id"] not in written:
                keep(future.result())

    print(f"{raw}: {len(written)} written, {len(done) + len(written)}/{len(rows)} answered, "
          f"{tokens[0]} input and {tokens[1]} output tokens this run", file=sys.stderr)
    if error:
        raise SystemExit(f"stopped: {error}\nThe same command continues without paying twice.")


if __name__ == "__main__":
    main()

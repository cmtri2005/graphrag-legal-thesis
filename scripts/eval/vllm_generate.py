#!/usr/bin/env python3
"""Answer exported prompt files with an open-weight model through vLLM (Colab GPU), the second generator column.

Writes the same raw file as `api_generate.py` (one line per row, `prompt_sha256` checked by `colab_b1 import`),
so import, scoring and confirm do not change. Settings mirror the locked GPT-4o mini column (ADR 0006 §2):
temperature 0, max_tokens 1024, seed 20261109. Thinking is switched off through the chat template, because a
thinking model spends the token budget before it answers.

Resumable: rows already in the raw file are skipped. Each prompt file and run tag gets its own raw file.

    python vllm_generate.py --model Qwen/Qwen3.8-27B --out-dir raw --run-tag r1 prompts/b4.jsonl prompts/b7plus.jsonl
"""
from __future__ import annotations

import argparse
import hashlib
import json
import time
from datetime import datetime, timezone
from pathlib import Path


def digest(row: dict) -> str:       # copy of colab_b1.digest (Colab has no repo); test_vllm_generate keeps them equal
    fields = [row["id"], row["system"], row["user"], row["ids"], row["retrieved"]]
    if "system_name" in row:
        fields += [row["system_name"], row["split"], row["as_of"], row["signals"]]
    return hashlib.sha256(json.dumps(fields, ensure_ascii=False, separators=(",", ":")).encode()).hexdigest()


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("prompts", type=Path, nargs="+")
    ap.add_argument("--model", required=True)
    ap.add_argument("--out-dir", type=Path, required=True)
    ap.add_argument("--run-tag", required=True, choices=("r1", "r2"))
    ap.add_argument("--max-tokens", type=int, default=1024)
    ap.add_argument("--seed", type=int, default=20261109)
    ap.add_argument("--max-model-len", type=int, default=40960, help="LightRAG prompts are about 32k tokens")
    ap.add_argument("--chunk", type=int, default=64, help="rows per generate call; each chunk is flushed to disk")
    ap.add_argument("--allow-test", action="store_true", help="test prompts need an accepted ADR 0006 amendment")
    args = ap.parse_args()

    from huggingface_hub import HfApi
    from vllm import LLM, SamplingParams
    import torch

    revision = HfApi().model_info(args.model).sha
    gpu = torch.cuda.get_device_name(0)
    llm = LLM(model=args.model, revision=revision, max_model_len=args.max_model_len, seed=args.seed,
              gpu_memory_utilization=0.92, enable_prefix_caching=True)
    params = SamplingParams(temperature=0.0, max_tokens=args.max_tokens, seed=args.seed)
    args.out_dir.mkdir(parents=True, exist_ok=True)

    for path in args.prompts:
        rows = [json.loads(line) for line in path.open(encoding="utf-8")]
        bad = [r["id"] for r in rows if digest(r) != r["prompt_sha256"]]
        if bad:
            raise SystemExit(f"{path}: {len(bad)} prompts do not match their hash, first {bad[0]}")
        splits, names = {r.get("split", "dev") for r in rows}, {r.get("system_name", "b2ctx") for r in rows}
        if len(splits) != 1 or len(names) != 1:
            raise SystemExit(f"{path}: one split and one system per file, found {splits} {names}")
        split, system = splits.pop(), names.pop()
        if split == "test" and not args.allow_test:
            raise SystemExit(f"{path}: test prompts need --allow-test (accepted ADR 0006 amendment)")
        file_sha = hashlib.sha256(path.read_bytes()).hexdigest()
        raw = args.out_dir / f"{system}__{args.model.replace('/', '__')}__{file_sha[:12]}.{args.run_tag}.jsonl"
        meta = raw.with_suffix(".meta.json")
        settings = {"provider": "vllm", "model": args.model, "revision": revision, "temperature": 0.0,
                    "max_tokens": args.max_tokens, "seed": args.seed, "transport": "local",
                    "thinking": False, "max_model_len": args.max_model_len}
        if meta.exists():
            before = json.loads(meta.read_text())
            if {k: before.get(k) for k in settings} != settings:
                raise SystemExit(f"{raw.name} was started with {before}; one file holds one configuration")
        else:
            import vllm
            meta.write_text(json.dumps({**settings, "system": system, "split": split, "prompt_file_sha256": file_sha,
                                        "run_tag": args.run_tag, "gpu": gpu, "vllm": vllm.__version__,
                                        "started": datetime.now(timezone.utc).isoformat(timespec="seconds")},
                                       indent=2) + "\n")
        done = set()
        if raw.exists():
            data = raw.read_bytes()
            if data and not data.endswith(b"\n"):          # a line cut by a crash
                raw.write_bytes(data[:data.rfind(b"\n") + 1])
            done = {json.loads(line)["id"] for line in raw.open(encoding="utf-8")}
        todo = [r for r in rows if r["id"] not in done]
        print(f"{system} {split} {args.run_tag}: {len(rows)} prompts, {len(done)} done, {len(todo)} to generate", flush=True)
        with raw.open("a", encoding="utf-8") as sink:
            for i in range(0, len(todo), args.chunk):
                part = todo[i:i + args.chunk]
                started = time.perf_counter()
                outs = llm.chat([[{"role": "system", "content": r["system"]}, {"role": "user", "content": r["user"]}]
                                 for r in part], params, use_tqdm=False,
                                chat_template_kwargs={"enable_thinking": False})
                each = (time.perf_counter() - started) / len(part)
                for r, out in zip(part, outs):
                    gen = out.outputs[0]
                    sink.write(json.dumps({
                        "id": r["id"], "prompt_sha256": r["prompt_sha256"], "model": args.model, "revision": revision,
                        "raw": gen.text.strip(), "finish_reason": gen.finish_reason,
                        "prompt_tokens": len(out.prompt_token_ids), "completion_tokens": len(gen.token_ids),
                        "elapsed_s": each, "gpu": gpu, "provider": "vllm", "system_fingerprint": None},
                        ensure_ascii=False) + "\n")
                sink.flush()
                print(f"  {min(i + args.chunk, len(todo))}/{len(todo)}", flush=True)
        print(f"-> {raw}", flush=True)


if __name__ == "__main__":
    main()

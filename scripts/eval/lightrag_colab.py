#!/usr/bin/env python3
"""LightRAG trên Colab Pro (REFACTOR_PLAN 3.3): dựng đồ thị bằng Qwen qua vLLM, rồi chỉ lấy ngữ cảnh.

Chạy trên Colab (A100), từng bước, mọi trạng thái lưu ở --work trên Google Drive nên ngắt phiên vẫn chạy tiếp:

    !pip install -q "lightrag-hku" vllm sentence-transformers
    # 1. bật vLLM (ô riêng, chạy nền):
    !nohup python -m vllm.entrypoints.openai.api_server --model $MODEL --served-model-name qwen \\
        --max-model-len 32768 --gpu-memory-utilization 0.80 --port 8000 > vllm.log 2>&1 &
    # 2. chạy thử trên vài văn bản, xem log định dạng trích xuất:
    !python lightrag_colab.py build  --work /content/drive/MyDrive/lightrag --corpus corpus.jsonl --limit 5
    # 3. dựng toàn bộ (chạy lại cùng lệnh nếu bị ngắt; văn bản đã xử lý được bỏ qua):
    !python lightrag_colab.py build  --work /content/drive/MyDrive/lightrag --corpus corpus.jsonl
    # 4. lấy ngữ cảnh cho mọi truy vấn (chạy tiếp được):
    !python lightrag_colab.py query  --work /content/drive/MyDrive/lightrag --queries queries.jsonl

Không gọi OpenAI ở đây: câu trả lời được sinh ở máy dự án bằng prompt và generator chung
(`scripts/eval/lightrag_package.py prompts`). LLM ở đây chỉ dùng để trích thực thể và tách từ khóa truy vấn.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import time
from pathlib import Path

LLM_BASE = os.environ.get("LLM_BASE", "http://127.0.0.1:8000/v1")
LLM_NAME = os.environ.get("LLM_NAME", "qwen")          # --served-model-name of vLLM
EMBED_MODEL = os.environ.get("EMBED_MODEL", "AITeamVN/Vietnamese_Embedding")   # bge-m3, 1024 chiều
MODE = "mix"     # mặc định của LightRAG: local + global + naive


def make_rag(work: Path):
    import numpy as np
    from lightrag import LightRAG
    from lightrag.llm.openai import openai_complete_if_cache
    from lightrag.utils import wrap_embedding_func_with_attrs
    from sentence_transformers import SentenceTransformer

    encoder = SentenceTransformer(EMBED_MODEL, device="cuda")
    encoder.max_seq_length = 8192

    async def llm(prompt, system_prompt=None, history_messages=[], **kwargs):
        return await openai_complete_if_cache(LLM_NAME, prompt, system_prompt=system_prompt,
                                              history_messages=history_messages, api_key="local",
                                              base_url=LLM_BASE, **kwargs)

    @wrap_embedding_func_with_attrs(embedding_dim=1024, max_token_size=8192, model_name=EMBED_MODEL)
    async def embed(texts: list[str]) -> np.ndarray:
        return encoder.encode(texts, normalize_embeddings=True, batch_size=32, convert_to_numpy=True)

    return LightRAG(working_dir=str(work), llm_model_func=llm, embedding_func=embed,
                    llm_model_max_async=int(os.environ.get("MAX_ASYNC", "16")),
                    addon_params={"language": "Vietnamese"})


async def ready(rag):
    await rag.initialize_storages()
    try:     # cần ở một số phiên bản LightRAG, không có ở bản khác
        from lightrag.kg.shared_storage import initialize_pipeline_status
        await initialize_pipeline_status()
    except ImportError:
        pass


async def build(args) -> None:
    docs = [json.loads(line) for line in args.corpus.open(encoding="utf-8")]
    if args.limit:
        docs = sorted(docs, key=lambda d: len(d["text"]))[:args.limit]     # chạy thử: văn bản ngắn nhất
    rag = make_rag(args.work)
    await ready(rag)
    started = time.time()
    for i in range(0, len(docs), args.batch):
        part = docs[i:i + args.batch]
        await rag.ainsert([d["text"] for d in part], ids=[d["id"] for d in part],
                          file_paths=[d["id"] for d in part])
        print(f"{min(i + args.batch, len(docs))}/{len(docs)} văn bản · {time.time() - started:.0f}s", flush=True)
    await rag.finalize_storages()
    (args.work / "build_done.json").write_text(json.dumps(
        {"docs": len(docs), "limit": args.limit, "llm": LLM_NAME, "model_env": os.environ.get("MODEL"),
         "embed": EMBED_MODEL, "seconds": time.time() - started}, ensure_ascii=False) + "\n")


async def query(args) -> None:
    from lightrag import QueryParam
    out = args.work / "contexts.jsonl"
    done = {json.loads(line)["id"] for line in out.open(encoding="utf-8")} if out.exists() else set()
    todo = [q for q in map(json.loads, args.queries.open(encoding="utf-8")) if q["id"] not in done]
    rag = make_rag(args.work)
    await ready(rag)
    with out.open("a", encoding="utf-8") as sink:
        for n, q in enumerate(todo, 1):
            context = await rag.aquery(q["query"], param=QueryParam(mode=MODE, only_need_context=True))
            sink.write(json.dumps({"id": q["id"], "split": q["split"], "mode": MODE,
                                   "context": context if isinstance(context, str) else json.dumps(context, ensure_ascii=False)},
                                  ensure_ascii=False) + "\n")
            sink.flush()
            if n % 25 == 0:
                print(f"{n}/{len(todo)} truy vấn", flush=True)
    await rag.finalize_storages()
    print(f"-> {out}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build")
    b.add_argument("--work", type=Path, required=True)
    b.add_argument("--corpus", type=Path, required=True)
    b.add_argument("--limit", type=int, default=0, help="chạy thử trên N văn bản ngắn nhất")
    b.add_argument("--batch", type=int, default=10)
    q = sub.add_parser("query")
    q.add_argument("--work", type=Path, required=True)
    q.add_argument("--queries", type=Path, required=True)
    args = ap.parse_args()
    args.work.mkdir(parents=True, exist_ok=True)
    asyncio.run({"build": build, "query": query}[args.cmd](args))


if __name__ == "__main__":
    main()

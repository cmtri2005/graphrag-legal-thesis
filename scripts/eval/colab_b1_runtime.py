"""Colab runtime for B1 or the seven B2 dev prompt files.

In a preceding Colab cell:
    %pip -q install -U 'transformers>=4.54,<5' accelerate bitsandbytes

Select a GPU, then upload one B1 file or one to seven B2 files together.
The model loads once and each prompt file has its own checkpoint.
"""
import hashlib
import json
import os
import time
from pathlib import Path

import torch
from google.colab import drive, files
import torch.nn.functional as F
from torch.nn.attention import SDPBackend, sdpa_kernel
from transformers import (AttentionInterface, AutoModelForCausalLM, AutoTokenizer,
                          BitsAndBytesConfig)
from transformers.masking_utils import AttentionMaskInterface, sdpa_mask

MODEL_ID = "Qwen/Qwen3-4B-Instruct-2507"
# For the second B1 candidate, use "microsoft/Phi-3.5-mini-instruct".
MAX_NEW_TOKENS = 512
MODELS = {"Qwen/Qwen3-4B-Instruct-2507", "microsoft/Phi-3.5-mini-instruct"}
B2_SYSTEMS = {"b1", "b2ctx", "b3", "b4", "b7", "b7v", "b7plus", "b7pp", "proposed",
              "b5", "b6", "a1", "a2", "a3", "a4", "oracle", "b2"}
BASE_FIELDS = {"id", "system", "user", "ids", "retrieved", "prompt_sha256"}
B2_FIELDS = BASE_FIELDS | {"system_name", "split", "as_of", "signals"}
assert MODEL_ID in MODELS
assert torch.cuda.is_available(), "Select a GPU runtime in Colab"
gpu_name = torch.cuda.get_device_name(0)
print("GPU:", gpu_name)

drive.mount("/content/drive")
uploaded = files.upload()
assert 1 <= len(uploaded) <= 7, "Upload one B1 or one to seven B2 prompt JSONLs"
assert all(name.endswith(".jsonl") for name in uploaded), "Only prompt JSONLs are accepted"
batches = []
for filename, prompt_bytes in sorted(uploaded.items()):
    prompt_sha256 = hashlib.sha256(prompt_bytes).hexdigest()
    prompts = [json.loads(line) for line in prompt_bytes.decode("utf-8").splitlines() if line]
    assert prompts and len({r["id"] for r in prompts}) == len(prompts), filename
    fields = {frozenset(r) for r in prompts}
    assert fields in ({frozenset(BASE_FIELDS)}, {frozenset(B2_FIELDS)}), filename
    is_b2 = "system_name" in prompts[0]
    system_names = {r.get("system_name", "b2ctx") for r in prompts}
    assert len(system_names) == 1, filename
    system_name = next(iter(system_names))
    if is_b2:
        assert system_name in B2_SYSTEMS and all(r["split"] == "dev" for r in prompts), filename
    batches.append((filename, prompt_sha256, prompts, is_b2, system_name))
if len(batches) > 1:
    assert all(batch[3] for batch in batches), "Multiple-file upload requires B2 prompts"
    assert len({batch[4] for batch in batches}) == len(batches), "Duplicate B2 system"

ATTENTION = "t4_sdpa_repeat_kv"


def t4_sdpa_repeat_kv(module, query, key, value, attention_mask, dropout=0.0, scaling=None,
                      **kwargs):
    """SDPA on the memory-efficient kernel. T4 has no flash kernel and the efficient one
    rejects grouped KV heads, so plain sdpa falls back to the math kernel, which builds
    the whole heads x L x L matrix: 29 GiB for a 22k-token prompt. Repeating the KV heads
    keeps memory linear in L. The KV cache itself stays unrepeated."""
    groups = query.shape[1] // key.shape[1]
    key = key.repeat_interleave(groups, dim=1)
    value = value.repeat_interleave(groups, dim=1)
    mask = None if attention_mask is None else attention_mask[:, :, :, :key.shape[-2]]
    with sdpa_kernel([SDPBackend.EFFICIENT_ATTENTION]):
        out = F.scaled_dot_product_attention(
            query, key, value, attn_mask=mask, scale=scaling,
            is_causal=mask is None and query.shape[2] > 1)
    return out.transpose(1, 2).contiguous(), None


AttentionInterface.register(ATTENTION, t4_sdpa_repeat_kv)
AttentionMaskInterface.register(ATTENTION, sdpa_mask)

quantization = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4",
                                  bnb_4bit_compute_dtype=torch.float16)
tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)
model = AutoModelForCausalLM.from_pretrained(
    MODEL_ID, device_map="auto", quantization_config=quantization,
    torch_dtype=torch.float16, attn_implementation=ATTENTION).eval()
revision = model.config._commit_hash
assert revision, "Missing Hugging Face model revision"
print("Model revision:", revision)
eos = model.generation_config.eos_token_id or tokenizer.eos_token_id
eos_ids = set(eos if isinstance(eos, list) else [eos])

for filename, prompt_sha256, prompts, is_b2, system_name in batches:
    output_dir = Path("/content/drive/MyDrive/vilextime_b2" if is_b2
                      else "/content/drive/MyDrive/vilextime_b1")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_name = (f"{system_name}__{MODEL_ID.replace('/', '__')}__{prompt_sha256[:12]}"
                   if is_b2 else MODEL_ID.replace("/", "__"))
    output_path = output_dir / (output_name + ".jsonl")
    meta_path = output_path.with_suffix(".meta.json")
    metadata = {"prompt_sha256": prompt_sha256, "model": MODEL_ID,
                "max_new_tokens": MAX_NEW_TOKENS, "decoding": "greedy",
                "quantization": "nf4", "gpu": gpu_name,
                "attention_backend": ATTENTION}
    if is_b2:
        metadata["system_name"] = system_name
    if meta_path.exists():
        assert json.loads(meta_path.read_text(encoding="utf-8")) == metadata, (
            f"{filename}: run configuration changed")
    else:
        assert not output_path.exists(), f"{filename}: raw output exists without metadata"
        meta_path.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")

    done = {}
    if output_path.exists():
        for line in output_path.read_text(encoding="utf-8").splitlines():
            item = json.loads(line)
            assert item["model"] == MODEL_ID and item["revision"] == revision, (
                f"{filename}: model revision changed")
            assert item["id"] not in done, f"{filename}: duplicate checkpoint ID"
            done[item["id"]] = item["prompt_sha256"]
    assert all(r["id"] not in done or done[r["id"]] == r["prompt_sha256"] for r in prompts), (
        f"{filename}: prompt changed")
    print(f"{filename}: {len(done)}/{len(prompts)} checkpointed")

    for n, row in enumerate(prompts, 1):
        if row["id"] in done:
            continue
        messages = [{"role": "system", "content": row["system"]},
                    {"role": "user", "content": row["user"]}]
        inputs = tokenizer.apply_chat_template(messages, add_generation_prompt=True,
                                               return_tensors="pt", return_dict=True)
        prompt_tokens = inputs["input_ids"].shape[-1]
        assert prompt_tokens + MAX_NEW_TOKENS <= model.config.max_position_embeddings, (
            f"Context too long: {row['id']} ({prompt_tokens})")
        started = time.perf_counter()
        with torch.inference_mode():
            output = model.generate(**inputs.to(model.device), max_new_tokens=MAX_NEW_TOKENS,
                                    do_sample=False, pad_token_id=tokenizer.eos_token_id)
        elapsed_s = time.perf_counter() - started
        new = output[0, prompt_tokens:]
        finish = "eos" if int(new[-1]) in eos_ids else "length"
        item = {"id": row["id"], "prompt_sha256": row["prompt_sha256"],
                "model": MODEL_ID, "revision": revision,
                "raw": tokenizer.decode(new, skip_special_tokens=True),
                "finish_reason": finish, "prompt_tokens": int(prompt_tokens),
                "completion_tokens": int(len(new)), "elapsed_s": elapsed_s, "gpu": gpu_name,
                "attention_backend": ATTENTION}
        with output_path.open("a", encoding="utf-8") as sink:
            sink.write(json.dumps(item, ensure_ascii=False) + "\n")
            sink.flush()
            os.fsync(sink.fileno())
        done[row["id"]] = row["prompt_sha256"]
        print(f"{system_name} {n}/{len(prompts)} {row['id']}: {finish}, {len(new)} output tokens")
    print(f"Completed {system_name}: {len(done)}/{len(prompts)}. Download {output_path}")

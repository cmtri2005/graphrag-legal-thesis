import json
import hashlib
from types import SimpleNamespace

import pytest

from colab_b1 import digest, import_completions


def test_import_requires_matching_prompt_and_writes_scorer_contract(tmp_path):
    prompt = {"id": "dev-1", "system": "s", "user": "u", "ids": ["unit-1"],
              "retrieved": ["unit-1"]}
    prompt["prompt_sha256"] = digest(prompt)
    prompts = tmp_path / "prompts.jsonl"
    prompts.write_text(json.dumps(prompt) + "\n")
    raw = tmp_path / "raw.jsonl"
    completion = {"id": "dev-1", "prompt_sha256": prompt["prompt_sha256"],
                  "model": "Qwen/Qwen3-4B-Instruct-2507", "revision": "abc",
                  "raw": "TRẢ LỜI: Văn bản.\nHIỆU LỰC: còn\nCĂN CỨ: [1]",
                  "finish_reason": "eos", "prompt_tokens": 10, "completion_tokens": 12,
                  "elapsed_s": 1.5, "gpu": "T4"}
    raw.write_text(json.dumps(completion) + "\n")
    out = tmp_path / "predictions.jsonl"
    args = SimpleNamespace(prompts=prompts, raw=raw, out=out)

    import_completions(args)
    pred = json.loads(out.read_text())
    assert pred["citations"] == ["unit-1"]
    assert pred["format_ok"] is True
    assert pred["truncated"] is False
    assert json.loads(out.with_suffix(".run.json").read_text())["generation_seconds"] == 1.5
    assert len(out.with_suffix(".sample.jsonl").read_text().splitlines()) == 1

    completion["prompt_sha256"] = "wrong"
    raw.write_text(json.dumps(completion) + "\n")
    with pytest.raises(SystemExit, match="prompt mismatch"):
        import_completions(args)


def test_b2_import_is_dev_only_and_keeps_system_metadata(tmp_path):
    prompt = {"id": "dev-1", "system": "s", "user": "u", "ids": [], "retrieved": [],
              "system_name": "b1", "split": "dev", "as_of": "2026-01-01", "signals": {}}
    prompt["prompt_sha256"] = digest(prompt)
    prompts = tmp_path / "b1-prompts.jsonl"
    prompts.write_text(json.dumps(prompt) + "\n")
    export = {"system": "b1", "rows": 1,
              "prompt_file_sha256": hashlib.sha256(prompts.read_bytes()).hexdigest()}
    prompts.with_suffix(".export.json").write_text(json.dumps(export))
    raw = tmp_path / "raw.jsonl"
    raw.write_text(json.dumps({"id": "dev-1", "prompt_sha256": prompt["prompt_sha256"],
                               "model": "Qwen/Qwen3-4B-Instruct-2507", "revision": "abc",
                               "raw": "TRẢ LỜI: X\nHIỆU LỰC: còn\nCĂN CỨ:",
                               "finish_reason": "eos", "prompt_tokens": 10,
                               "completion_tokens": 10, "elapsed_s": 1, "gpu": "T4"}) + "\n")
    out = tmp_path / "b1.jsonl"
    import_completions(SimpleNamespace(prompts=prompts, raw=raw, out=out))
    assert json.loads(out.read_text())["signals"] == {}
    assert json.loads(out.with_suffix(".run.json").read_text())["system"] == "b1"
    assert json.loads(out.with_suffix(".run.json").read_text())["export"] == export
    prompt["split"] = "train"
    prompt["prompt_sha256"] = digest(prompt)
    prompts.write_text(json.dumps(prompt) + "\n")
    with pytest.raises(SystemExit, match="dev or test"):
        import_completions(SimpleNamespace(prompts=prompts, raw=raw, out=out))


def test_test_split_export_waits_for_a_committed_accepted_adr(tmp_path):
    import subprocess
    from colab_b1 import adr_accepted
    adr = tmp_path / "docs/decisions/0005.md"
    adr.parent.mkdir(parents=True)
    git = lambda *a: subprocess.run(["git", *a], cwd=tmp_path, check=True, capture_output=True)
    git("init", "-q")
    adr.write_text("# 0005\n\n## Status\n\nProposed.\n\n## Context\n\nAccepted later.\n")
    git("add", "."), git("-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "p")
    adr.write_text("# 0005\n\n## Status\n\nAccepted (CMT).\n")
    assert not adr_accepted(adr)          # the working tree alone does not count
    git("-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qam", "a")
    assert adr_accepted(adr)

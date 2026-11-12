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
                               "completion_tokens": 10, "elapsed_s": 1, "gpu": "T4",
                               "system_fingerprint": "fp_1"}) + "\n")
    out = tmp_path / "b1.jsonl"
    import_completions(SimpleNamespace(prompts=prompts, raw=raw, out=out, run_tag="r2"))
    run = json.loads(out.with_suffix(".run.json").read_text())
    assert (run["run_tag"], run["system_fingerprints"], run["served_models"]) == ("r2", {"fp_1": 1}, {"abc": 1})
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


@pytest.mark.parametrize('versions, expected', [(1, True), (2, False)])
def test_oracle_now_uses_same_template_and_latest_exact_provision(corpus, tmp_path, versions, expected):
    import colab_b1
    from test_rag_corpus import CLAUSE, DOC

    uid = f'version:{CLAUSE.split(":")[1]}:1'
    if versions == 2:
        import sqlite3
        with sqlite3.connect(corpus.path) as db:
            db.execute("INSERT INTO units (unit_id,layer,kind,provision_id,document_id,ordinal,text) "
                       "VALUES (?,?,?,?,?,?,?)", ('version:k1:2', 'version', 'version', CLAUSE, DOC, 2, 'Lời văn mới.'))
    release = tmp_path / 'release.jsonl'
    release.write_text(json.dumps(dict(id='old', group='T1' if versions == 1 else 'T2', split='dev',
        as_of_strategy='giua_khoang', question='Nội dung là gì?', as_of='2021-01-01', lineage_id=CLAUSE,
        version_id=uid, accepted_evidence=[], short_answer='SECRET GOLD', answer='SECRET GOLD')) + '\n')
    prompts = []
    for system in ('oracle', 'oracle_now'):
        dest = tmp_path / f'{system}.jsonl'
        colab_b1.export_prompts(SimpleNamespace(system=system, split='dev', as_of_strategy='giua_khoang',
            release=release, index=corpus.path, limit=0, out=dest, hits_cache=None, b2=True))
        prompt = json.loads(dest.read_text())
        assert 'SECRET GOLD' not in json.dumps(prompt)
        prompts.append(prompt)
    assert prompts[0]['system'] == prompts[1]['system']
    assert (prompts[0]['user'] == prompts[1]['user']) is expected
    assert prompts[1]['retrieved'] == [uid if versions == 1 else 'version:k1:2']


def test_oracle_now_repealed_row_supplies_last_wording_without_instruction(corpus, tmp_path):
    import colab_b1
    from test_rag_corpus import CLAUSE
    release = tmp_path / 'release.jsonl'
    release.write_text(json.dumps(dict(id='repealed', split='dev', as_of_strategy='giua_khoang',
        question='Nội dung là gì?', as_of='2023-01-01', lineage_id=CLAUSE, version_id=None,
        accepted_evidence=['asis:event:e1'])) + '\n')
    dest = tmp_path / 'oracle_now.jsonl'
    colab_b1.export_prompts(SimpleNamespace(system='oracle_now', split='dev', as_of_strategy='giua_khoang',
        release=release, index=corpus.path, limit=0, out=dest, hits_cache=None, b2=True))
    prompt = json.loads(dest.read_text())
    assert prompt['retrieved'] == ['version:k1:1']
    assert 'Bãi bỏ Điều 1.' not in prompt['user']


from test_rag_corpus import corpus, data  # noqa: E402,F401

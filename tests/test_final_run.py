import json
from types import SimpleNamespace

import pytest

import final_run


def row(**updates):
    return dict(id='a', split='dev', as_of_strategy='giua_khoang', answerable=True,
                short_answer='đúng', lineage_id='L', target={'document_id': 'D'}, **updates)


def test_final_release_allows_complete_dev():
    assert final_run.validate_rows([row()], 'dev', []) == [row()]


@pytest.mark.parametrize('gold', [None, '', ' … ', '!!!'])
def test_final_release_refuses_missing_short_answer(gold):
    r = row()
    r['short_answer'] = gold
    with pytest.raises(SystemExit, match='missing short_answer'):
        final_run.validate_rows([r], 'dev', [])


def adr_repo(tmp_path):
    """A throwaway git repo holding a Proposed ADR 0006, an old ADR 0005 amendment and one input file."""
    import subprocess

    import colab_b1
    git = lambda *a: subprocess.run(['git', '-c', 'user.name=t', '-c', 'user.email=t@t', *a], cwd=tmp_path,
                                    check=True, capture_output=True)
    adr = tmp_path / colab_b1.ADR.relative_to(final_run.ROOT)
    adr.parent.mkdir(parents=True)
    git('init', '-q')
    adr.write_text('# 0006\n\n## Status\n\n**Proposed, bản nháp.**\n\n## Context\n\nAccepted later.\n')
    (adr.parent / '0005-ke-hoach-phan-tich.md').write_text('# 0005\n\n## Status\n\nAccepted\n\n## Amendment 2026-11-05\n')
    (tmp_path / 'input').write_text('x')
    git('add', '.')
    git('commit', '-qm', 'proposed')
    return adr, git


def test_final_test_gate_needs_committed_accepted_adr_0006(tmp_path):
    adr, git = adr_repo(tmp_path)
    final_run.guard_test('dev', [tmp_path / 'absent'], root=tmp_path)
    with pytest.raises(SystemExit, match='ADR 0006 Status Accepted'):
        final_run.guard_test('test', [tmp_path / 'input'], root=tmp_path)      # Proposed; ADR 0005 amendment is no longer enough
    adr.write_text(adr.read_text().replace('**Proposed, bản nháp.**', '**Accepted (CMT).**'))
    with pytest.raises(SystemExit, match='ADR 0006 Status Accepted'):
        final_run.guard_test('test', [tmp_path / 'input'], root=tmp_path)      # the working tree alone does not count
    git('commit', '-qam', 'accepted')
    final_run.guard_test('test', [tmp_path / 'input'], root=tmp_path)
    (tmp_path / 'input').write_text('changed')
    with pytest.raises(SystemExit, match='inputs are dirty'):
        final_run.guard_test('test', [tmp_path / 'input'], root=tmp_path)


def test_final_test_gate_refuses_accepted_reverted_to_proposed(tmp_path):
    adr, git = adr_repo(tmp_path)
    adr.write_text(adr.read_text().replace('**Proposed, bản nháp.**', 'Accepted'))
    git('commit', '-qam', 'accepted')
    import colab_b1
    assert colab_b1.adr_accepted_commit(adr) is not None
    adr.write_text(adr.read_text().replace('Accepted\n\n## Context', '**Proposed, lại.**\n\n## Context'))
    git('commit', '-qam', 'back')
    assert colab_b1.adr_accepted_commit(adr) is None


def test_final_refuses_dev_document_leakage():
    r = row()
    r['split'] = 'test'
    dev = row()
    dev['lineage_id'] = 'another'
    with pytest.raises(SystemExit, match='dev leakage by document_id'):
        final_run.validate_rows([r], 'test', [dev])




def test_final_prediction_gate_rejects_incomplete_duplicate_and_foreign_ids(tmp_path):
    r = row()
    path = tmp_path / 'b7.jsonl'
    path.write_text(json.dumps({'id': 'a'}) + '\n')
    final_run.validate_predictions(tmp_path, ['b7'], [r], 'dev')
    for ids in ([], ['a', 'a'], ['a', 'foreign']):
        path.write_text(''.join(json.dumps({'id': i}) + '\n' for i in ids))
        with pytest.raises(SystemExit, match='duplicate, incomplete or foreign-split'):
            final_run.validate_predictions(tmp_path, ['b7'], [r], 'dev')


def test_final_system_list_is_known_and_exports_without_reranker():
    from pathlib import Path

    from vilexgraph.framework import systems

    named = [n for n in (*systems.FINAL_GENERATION, *systems.DEV_ONLY) if n not in systems.ORACLES]
    assert all(n in systems.REGISTRY for n in named)
    assert all(f'`{n}`' in systems.table() for n in (*named, *systems.ORACLES))
    # b7, b7plus and b7pp carry rerank=True in the registry; the reranker was cut 05/11.
    assert 'hybrid=True' in Path(final_run.__file__).read_text(encoding='utf-8')


def test_each_dense_system_reads_embeddings_of_its_own_layer():
    from run_vilextime import embed_dir
    from vilexgraph.framework import systems
    for name in (*systems.FINAL_GENERATION, *systems.DEV_ONLY):
        if name in systems.ORACLES:
            continue
        spec = systems.get(name)
        if spec.dense:
            assert (embed_dir(spec.layer) / 'texts.sqlite').exists(), name
            assert spec.layer in embed_dir(spec.layer).name, name


def test_raw_files_split_by_run_tag(tmp_path):
    for name in ('b7__m__abc.jsonl', 'b7__m__abc.r1.jsonl', 'b7__m__abc.r2.jsonl', 'b7__m__abc.r2.meta.json'):
        (tmp_path / name).write_text('')
    names = lambda tag: [p.name for p in final_run.raw_files(tmp_path, 'b7', tag)]
    assert names(None) == ['b7__m__abc.jsonl']
    assert names('r1') == ['b7__m__abc.r1.jsonl']
    assert names('r2') == ['b7__m__abc.r2.jsonl']


@pytest.mark.parametrize('change, ok', [({}, True), ({'model': 'gpt-4o-mini'}, False), ({'temperature': 0.2}, False),
                                        ({'max_tokens': 512}, False), ({'seed': 1}, False)])
def test_locked_generation_config(tmp_path, change, ok):
    raw = tmp_path / 'b7__m__abc.jsonl'
    raw.write_text('')
    raw.with_suffix('.meta.json').write_text(json.dumps({**final_run.LOCKED_GENERATION, **change}))
    if ok:
        final_run.check_locked_generation(raw)
    else:
        with pytest.raises(SystemExit, match='locked'):
            final_run.check_locked_generation(raw)
    raw.with_suffix('.meta.json').unlink()
    with pytest.raises(SystemExit, match='locked'):
        final_run.check_locked_generation(raw)


@pytest.mark.parametrize('spec, ok', [({'lexical': True, 'dense': False, 'k': 20}, True),
                                      ({'lexical': True, 'dense': True, 'k': 20}, False),
                                      ({'lexical': True, 'dense': False, 'k': 10}, False)])
def test_locked_retrieval_is_lexical_k20(tmp_path, spec, ok):
    (tmp_path / 'b7.run.json').write_text(json.dumps([{'spec': {'lexical': True, 'dense': True, 'k': 5}}, {'spec': spec}]))
    if ok:
        final_run.check_locked_retrieval(tmp_path, ['b7'])
    else:
        with pytest.raises(SystemExit, match='lexical'):
            final_run.check_locked_retrieval(tmp_path, ['b7'])
    with pytest.raises(SystemExit, match='lexical'):
        final_run.check_locked_retrieval(tmp_path, ['absent'])

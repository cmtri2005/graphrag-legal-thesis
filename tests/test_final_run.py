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


def test_final_refuses_test_without_amendment_before_reading_inputs(tmp_path):
    with pytest.raises(SystemExit, match='requires --amendment'):
        final_run.guard_test('test', None, [tmp_path / 'absent'])
    final_run.guard_test('dev', None, [tmp_path / 'absent'])


def test_final_refuses_amendment_outside_head(monkeypatch):
    monkeypatch.setattr(final_run, 'git', lambda *a, **k: SimpleNamespace(returncode=1, stdout=''))
    with pytest.raises(SystemExit, match='not a commit contained in HEAD'):
        final_run.guard_test('test', 'missing', [])


def test_final_test_gate_checks_dirty_inputs_and_accepts_clean(monkeypatch, tmp_path):
    dirty = False
    def git(*args, **kwargs):
        if args[0] == 'show':
            text = '+## Amendment 2026-11-05'
        elif args[0] == 'status':
            text = ' M scripts/eval/score_vilextime.py' if dirty else ''
        else:
            text = 'a' * 40
        return SimpleNamespace(returncode=0, stdout=text)
    monkeypatch.setattr(final_run, 'git', git)
    final_run.guard_test('test', 'abc', [tmp_path / 'input'], root=tmp_path)
    dirty = True
    with pytest.raises(SystemExit, match='inputs are dirty'):
        final_run.guard_test('test', 'abc', [tmp_path / 'input'], root=tmp_path)


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

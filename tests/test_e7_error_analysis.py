from collections import Counter
import csv
import sqlite3

from e7_error_analysis import classify, sample_errors, summarize, write_sheets


def test_exclusive_priority_reuses_scorer_correctness_and_version_direction():
    row = {'id': 'r', 'lineage_id': 'provision:P', 'version_id': 'version:P:2', 'group': 'T2',
           'as_of': '2021-01-01', 'answerable': True, 'short_answer': 'gold',
           'accepted_evidence': ['asis:event:gold'], '_distractors': ['old words']}
    units = {f'version:P:{n}': [('provision:P', n, [('2000-01-01', None)])] for n in (1, 2, 3)}
    cases = [
        ({'answerable': False, 'retrieved': []}, 'ABST'),
        ({'answer': '', 'retrieved': []}, 'RET-UNIT'),
        ({'answer': '', 'retrieved': ['version:P:1']}, 'RET-VER-OLD'),
        ({'answer': '', 'retrieved': ['version:P:3']}, 'RET-VER-NEW'),
        ({'answer': ' ', 'retrieved': ['asis:event:gold']}, 'GEN-BLANK'),
        ({'answer': 'gold old words', 'retrieved': ['version:P:2']}, 'GEN-MISREAD'),
    ]
    records = [classify(row, pred, units) for pred, _ in cases]
    assert [r['layer'] for r in records] == [layer for _, layer in cases]
    assert records[-1]['wrong_version']
    assert summarize(records)['errors'] == sum(summarize(records)['counts'].values()) == 6
    assert classify(row, {'answer': 'gold', 'retrieved': []}, units)['correct']
    repealed = {**row, 'answerable': False, 'version_id': None, 'short_answer': None}
    assert classify(repealed, {'answer': 'gold', 'retrieved': ['asis:event:gold']}, units)['layer'] == 'ABST'
    assert classify(repealed, {'answerable': False}, units)['correct']
    expanded = classify(row, {'answer': 'wrong', 'retrieved': ['other'] * 20 + ['asis:event:gold']}, units)
    assert expanded['gold_in_prompt'] and not expanded['tv20']
    assert expanded['layer'] == 'GEN-MISREAD'  # Expansion after rank 20 still enters the prompt.
    mixed = classify(row, {'answer': 'wrong', 'retrieved': ['version:P:3', 'version:P:1']}, units)
    assert mixed['layer'] == 'RET-VER-OLD' and mixed['mixed_direction']


def test_sampling_is_reproducible_stratified_and_only_errors():
    records = [{'system': s, 'row': {'group': g, 'id': f'{g}{i:02}'}, 'correct': i == 25}
               for s in ('b1', 'b7', 'b5') for g in ('T2', 'T6') for i in range(26)]
    sample = sample_errors(records)
    assert sample == sample_errors(list(reversed(records)))
    assert len(sample) == 80 and not any(r['correct'] for r in sample)
    assert set(Counter((r['system'], r['row']['group']) for r in sample).values()) == {20}
    assert {r['system'] for r in sample[:30]} == {'b1', 'b7'}


def test_human_sheet_hides_system_and_joins_machine_sheet_by_stt(tmp_path):
    corpus = tmp_path / 'derived/corpus'
    corpus.mkdir(parents=True)
    with sqlite3.connect(corpus / 'index.sqlite') as db:
        db.execute('CREATE TABLE units (unit_id TEXT, text TEXT)')
    row = {'id': 'r', 'group': 'T2', 'lineage_id': 'p', 'question': 'question', 'as_of': '2020-01-01',
           'answerable': True, 'answer': 'gold', 'short_answer': 'gold'}
    records = [{'system': s, 'row': row, 'pred': {}, 'correct': False, 'layer': 'RET-UNIT',
                'wrong_version': False, 'mixed_direction': False,
                'resolved_gold_without_accepted_id': False} for s in ('b1', 'proposed')]
    dest = tmp_path / 'sheets'
    write_sheets('fixture', records, dest, tmp_path)
    with (dest / 'phieu_fixture.tsv').open() as f:
        reader = csv.DictReader(f, delimiter='\t')
        assert 'he' not in reader.fieldnames and 'tang_may' not in reader.fieldnames
        human = list(reader)
    with (dest / 'phieu_fixture_may.tsv').open() as f:
        machine = list(csv.DictReader(f, delimiter='\t'))
    assert [(r['stt'], r['id']) for r in human] == [(r['stt'], r['id']) for r in machine]
    assert {r['he'] for r in machine} == {'b1', 'proposed'}
    assert all(r[k] == '' for r in human for k in ('ma_loi_A', 'ghi_chu_A', 'ma_loi_B', 'ghi_chu_B'))

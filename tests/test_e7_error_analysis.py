from collections import Counter

from e7_error_analysis import classify, sample_errors, summarize


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

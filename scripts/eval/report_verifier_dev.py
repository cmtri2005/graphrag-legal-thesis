#!/usr/bin/env python3
"""X4: describe Verifier flags on existing dev citations; never regenerate."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'src'))
from vilexgraph.framework.corpus import Corpus
from vilexgraph.framework.verify import invalid_units
from score_vilextime import load_rows


def group(row):
    return ('T6_answerable' if row['answerable'] else 'T6_unanswerable') if row['group'] == 'T6' else row['group']


def describe(rows, predictions, corpus):
    if len({p['id'] for p in predictions}) != len(predictions):
        raise ValueError('duplicate prediction ID')
    by_id = {p['id']: p for p in predictions}
    if set(by_id) != {r['id'] for r in rows}:
        raise ValueError('predictions must cover exactly the selected dev rows')
    details, groups = [], {}
    for row in rows:
        citations = by_id[row['id']].get('citations') or []
        tiers = {u: 'document' if (unit := corpus.unit(u)) and unit.layer == 'asis'
                 else 'propagated' for u in citations}
        bad = tuple(u for u in citations if invalid_units(corpus, tiers[u], row['as_of'], [u]))
        no_window = [u for u in citations if (unit := corpus.unit(u)) and unit.kind != 'instruction'
                     and not corpus.db.execute('SELECT 1 FROM prop_iv WHERE unit_id=?', (u,)).fetchone()]
        details.append({'id': row['id'], 'group': group(row), 'as_of': row['as_of'],
                        'checked': len(citations), 'invalid': list(bad), 'citation_tiers': tiers,
                        'citations_without_propagated_windows': no_window})
        for key in ('all', group(row)):
            cell = groups.setdefault(key, dict(rows=0, cited_rows=0, flagged_rows=0, checked=0,
                                               invalid_citations=0, rows_without_propagated_windows=0))
            cell['rows'] += 1
            cell['cited_rows'] += bool(citations)
            cell['flagged_rows'] += bool(bad)
            cell['checked'] += len(citations)
            cell['invalid_citations'] += len(bad)
            cell['rows_without_propagated_windows'] += bool(no_window)
    return {'tier_by_layer': {'asis': 'document', 'version': 'propagated'},
            'groups': groups, 'details': details}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--release', type=Path, default=Path('data/vilextime_dataset/vilextime.jsonl'))
    ap.add_argument('--index', type=Path, default=Path('data/derived/corpus/index.sqlite'))
    ap.add_argument('--predictions', type=Path, default=Path('runs/B2_dev/dev'))
    ap.add_argument('--out', type=Path, default=Path('runs/x4_verifier_dev/report.json'))
    args = ap.parse_args()
    rows = [r for r in load_rows(args.release) if r['split'] == 'dev' and r['as_of_strategy'] == 'giua_khoang']
    corpus = Corpus(args.index)
    report = {'split': 'dev', 'tier_by_layer': {'asis': 'document', 'version': 'propagated'},
              'as_of_strategy': 'giua_khoang',
              'limitation': 'Verifier và TVER dùng chung khoảng hiệu lực của đồ thị; đây là mô tả, không phải bằng chứng độc lập. '
                            'Layer asis dùng tier document vì không có prop_iv; version dùng propagated; '
                            'không thể diễn giải mọi cờ là một lỗi pháp lý hay mức cải thiện khi bật Verifier.',
              'release': str(args.release), 'release_sha256': hashlib.sha256(args.release.read_bytes()).hexdigest(),
              'index': str(args.index), 'systems': {}}
    try:
        for name in ('b2ctx', 'b4', 'b7'):
            path = args.predictions / f'{name}.jsonl'
            predictions = [json.loads(line) for line in path.open(encoding='utf-8')]
            report['systems'][name] = {'source': str(path), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                                       **describe(rows, predictions, corpus)}
    finally:
        corpus.close()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({n: r['groups'] for n, r in report['systems'].items()}, ensure_ascii=False))


if __name__ == '__main__':
    main()

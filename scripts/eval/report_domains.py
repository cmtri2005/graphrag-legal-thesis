#!/usr/bin/env python3
"""C5: score only existing E3 predictions by release domain, using the unchanged scorer."""
from __future__ import annotations

import argparse
import hashlib
import json
from collections import defaultdict
from pathlib import Path

from score_vilextime import distractors, load_rows, score, units_of

SYSTEMS = ('b1', 'b2ctx', 'b5', 'b7', 'b7pp', 'proposed')
METRICS = ('accuracy', 'tv_recall@1', 'tver')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def domain_rows(rows):
    buckets = defaultdict(list)
    for row in rows:
        domains = row.get('domain') or ['khong_ro']
        if isinstance(domains, str):
            domains = [domains]
        for domain in sorted(set(domains)):
            buckets[domain].append(row)
    return dict(sorted(buckets.items()))


def summarize(rows, predictions, units):
    out = {}
    for domain, selected in domain_rows(rows).items():
        lineages = len({r['lineage_id'] for r in selected})
        systems = {}
        for name, preds in predictions.items():
            metrics = score(selected, preds, units, ks=(1,))
            systems[name] = {m: metrics[m] for m in METRICS} | {'cited_rows': metrics['cited_rows']}
        out[domain] = {'rows': len(selected), 'lineages': lineages, 'small': lineages < 10, 'systems': systems}
    return out


def analyze(release, directory, data):
    rows = load_rows(release)
    extra = distractors(rows)  # same full-release distractors as score_vilextime.main, before slicing
    metadata = release.with_name('vilextime_meta.jsonl') if release.name == 'vilextime.jsonl' else None
    domains = {r['id']: r.get('domain') for r in map(json.loads, metadata.open(encoding='utf-8'))} if metadata else {}
    for row in rows:
        row['_distractors'] = extra.get(row['id'], [])
        if metadata:
            row['domain'] = domains[row['id']]
    rows = [r for r in rows if r['split'] == 'test' and r['as_of_strategy'] == 'giua_khoang'
            and r['group'] in ('T1', 'T2', 'T3', 'T6')]
    predictions, sources = {}, {}
    for name in SYSTEMS:
        path = directory / f'{name}.jsonl'
        items = [json.loads(line) for line in path.open(encoding='utf-8')]
        preds = {p['id']: p for p in items}
        if len(preds) != len(items) or set(preds) != {r['id'] for r in rows}:
            raise ValueError(f'{path}: duplicate or missing/unexpected IDs')
        predictions[name] = preds
        sources[name] = {'path': str(path), 'sha256': sha(path)}
    units, ids, texts = units_of(data, predictions)
    return {'release': str(release), 'release_sha256': sha(release),
            'metadata': str(metadata) if metadata else None, 'metadata_sha256': sha(metadata) if metadata else None,
            'sources': sources, 'rows': len(rows), 'lineages': len({r['lineage_id'] for r in rows}),
            'unresolved_unit_ids': len(ids - units.keys()), 'unresolved_written_citations': len(texts - units.keys()),
            'overall': {n: {m: s[m] for m in METRICS} for n, p in predictions.items()
                        for s in [score(rows, p, units, ks=(1,))]},
            'domains': summarize(rows, predictions, units)}


def render(results):
    lines = ['# E3 theo miền', '', '**Thăm dò, không vào họ kiểm định** (C5). Chỉ chấm lại dự đoán có sẵn; không sinh hay chạy hệ mới.', '',
             'Chế độ `giua_khoang`, split `test`, nhóm T1/T2/T3/T6. Mỗi dòng được đếm đầy đủ một lần ở mỗi miền của nó '
             '(đa nhãn; không chia trọng số). Lineage đếm riêng trong từng miền; tổng các miền có thể vượt tổng bộ.', '',
             'Dùng nguyên `score_vilextime.load_rows`, `distractors`, `units_of`, `score`; distractor tính trên toàn release trước khi chia miền. '
             'Accuracy và TV-R@1 lấy mẫu số là mọi dòng; TVER lấy mẫu số `cited_rows` của scorer. Không có trích dẫn thì TVER = —. '
             'TVER dựa trên khoảng hiệu lực của đồ thị, không phải kiểm tra pháp lý độc lập. Miền dưới 10 lineage đánh dấu **ít lineage**.', '']
    for label, result in results.items():
        lines += [f'## {label}', '', f"{result['rows']} dòng / {result['lineages']} lineage; release `{result['release']}`; "
                  f"SHA-256 `{result['release_sha256']}`.", '',
                  'v1.0 dùng metadata đồng hành; test 2 dùng bản v2 có đáp án ngắn đã sửa. Nhãn test 2 là nhãn LLM. '
                  'Nguồn, hash dự đoán/metadata và số tổng kiểm lại: `runs/domain_e3/report.json`.', '',
                  '| Miền | Dòng | Lineage | Hệ | Accuracy | TV-R@1 | TVER | Dòng có trích dẫn |',
                  '|---|---:|---:|---|---:|---:|---:|---:|']
        for domain, cell in result['domains'].items():
            for name, metrics in cell['systems'].items():
                values = ['—' if metrics[m] is None else f'{metrics[m]:.3f}' for m in METRICS]
                warning = ' **ít lineage**' if cell['small'] else ''
                lines.append(f"| {domain}{warning} | {cell['rows']} | {cell['lineages']} | {name} | "
                             + ' | '.join(values) + f" | {metrics['cited_rows']} |")
        lines += ['']
    return '\n'.join(lines)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--data', type=Path, default=Path('data'))
    ap.add_argument('--v1-dir', type=Path, default=Path('runs/E3_v1/test'))
    ap.add_argument('--test2-dir', type=Path, default=Path('runs/E3_test2/test'))
    ap.add_argument('--out', type=Path, default=Path('docs/reports/theo_mien_e3.md'))
    ap.add_argument('--json-out', type=Path, default=Path('runs/domain_e3/report.json'))
    args = ap.parse_args()
    results = {'v1.0': analyze(args.data / 'vilextime_dataset/vilextime.jsonl', args.v1_dir, args.data),
               'test 2': analyze(args.data / 'vilextime/test2_release_v2.jsonl', args.test2_dir, args.data)}
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(results, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(render(results) + '\n', encoding='utf-8')
    for label, result in results.items():
        print(label, {d: (c['rows'], c['lineages']) for d, c in result['domains'].items()}, result['overall'])


if __name__ == '__main__':
    main()

"""Như gan5/publish.py cho T1: đúng chủ sở hữu unlabelled_record, nhưng T1 chưa từng bị sửa nên KHÔNG có văn bản tác động;
chỉ cần đoạn+link văn bản gốc. Lấy N lineage đầu theo thứ tự rút (draw_210.jsonl) trong số đủ nguồn; batch đánh số từ --start."""
import argparse, collections, json, sys
from pathlib import Path
sys.dont_write_bytecode = True
R = Path('/home/trica/UIT_Thesis/graphrag-legal-thesis'); sys.path[:0] = [str(R/'scripts/review'), str(R/'scripts/pipeline')]
from test2_labels import unlabelled_record, write_worksheet
ap = argparse.ArgumentParser()
for k in ('--source', '--rank', '--out'): ap.add_argument(k, required=True, type=Path)
ap.add_argument('--n', type=int, default=60); ap.add_argument('--start', type=int, default=12)
ap.add_argument('--reference', type=Path, default=R/'data/review/the4/lo1_silver_worksheet.jsonl'); a = ap.parse_args()
by = {r['lineage_id']: r for r in map(json.loads, a.source.open()) if r}
order = [json.loads(s)['lineage_id'] for s in a.rank.open() if s.strip()]
ok, dropped = [], []
for lid in order:
    r = by.get(lid)
    if not r: continue
    s = r['sources']
    miss = any(row.get('source_missing') for row in r['rows']) or not s['base'].get('passage') or not s['base'].get('source_url') or s['actors']
    (dropped if miss else ok).append(lid)
picked = ok[:a.n]
reference = json.loads(a.reference.open().readline()); clean = []
for i, lid in enumerate(picked):
    c = unlabelled_record({**by[lid], 'batch': a.start + i // 30}); clean.append(c)
    if set(c) != set(reference): raise ValueError('Sai schema cấp lineage')
    for row in c['rows']:
        if set(row) - set(reference['rows'][0]) or set(row['target']) - set(reference['rows'][0]['target']): raise ValueError('Sai schema cấp mốc/target')
print(json.dumps({'dropped_missing_source': dropped, 'eligible': len(ok)}, ensure_ascii=False))
print(json.dumps(write_worksheet(a.out, clean, {'status': 'unlabelled_candidates', 'guideline_version': '4.0', 'questions': len(clean),
      'boundary_rows': sum(len(r['rows']) for r in clean), 'batches': dict(collections.Counter(r['batch'] for r in clean)),
      'source': str(a.source), 'selection': f'{len(picked)} lineage đầu theo thứ tự rút seed vilextime-t1-1111', 'group': 'T1 (đối chứng không làm hại)',
      'pending': ['independent A/B labels', 'lawyer adjudication']}), ensure_ascii=False))

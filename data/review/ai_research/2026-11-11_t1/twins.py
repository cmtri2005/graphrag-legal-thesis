"""Mốc giua_khoang của T1 (đúng hàm twin_of của enrich_vilextime, cùng caps/document_end/SNAPSHOT). Chỉ đọc.
  python twins.py --rows rows.jsonl --out twins.jsonl   # rows: dòng ranh_gioi T1; ghi dòng giua_khoang, in lineage không có twin"""
import argparse, csv, json, sqlite3, sys
from datetime import date
from pathlib import Path
sys.dont_write_bytecode = True
R = Path('/home/trica/UIT_Thesis/graphrag-legal-thesis'); sys.path[:0] = [str(R/'scripts/pipeline')]
from enrich_vilextime import twin_of, _d
ap = argparse.ArgumentParser(); ap.add_argument('--rows', type=Path, required=True); ap.add_argument('--out', type=Path, required=True); a = ap.parse_args()
data = R/'data'
rows = [json.loads(s) for s in a.rows.open() if s.strip()]
want = {r['lineage_id'] for r in rows}
pool = {}
for s in (data/'derived/vilextime_pool.jsonl').open(encoding='utf-8'):
    p = json.loads(s)
    if p['provision_id'] in want: pool[p['provision_id']] = sorted(p['versions'], key=lambda v: v['ordinal'])
db = sqlite3.connect(f"file:{data/'temporal.sqlite'}?mode=ro", uri=True)
end = {d: _d(e) for d, e in db.execute('SELECT id, effective_to FROM documents')}
caps = {}
q = data/'review/validity_queue.tsv'
if q.exists():
    for x in csv.DictReader(q.open(encoding='utf-8'), delimiter='\t'):
        if x['kind'] == 'missed_event' and x['decision'] == 'loi' and x['strategy'] == 'giua_khoang':
            caps.setdefault(x['lineage'], []).append(date.fromisoformat(x['date']))
out, none = [], []
for r in rows:
    t = twin_of(r, pool[r['lineage_id']], end.get(r['target']['document_id']), tuple(caps.get(r['lineage_id'], ())))
    (out if t else none).append(t or r['lineage_id'])
a.out.write_text(''.join(json.dumps(t, ensure_ascii=False) + '\n' for t in out))
print(json.dumps({'rows': len(rows), 'twins': len(out), 'no_twin': none}, ensure_ascii=False))

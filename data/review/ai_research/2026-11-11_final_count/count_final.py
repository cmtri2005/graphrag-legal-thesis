#!/usr/bin/env python3
"""Final-test lineages after CMT confirmation (10/11), H7 and R2 (11/11). Run from repo root.
silver: cmt_confirmed silver_dat, verdict overridden by H7 out_batch*; lo2: cmt_confirmed lo2_dat;
supp: supp18 labels with q1..q4 = dung/co/co/khong; minus R2 ket_luan != giu."""
import collections, glob, json
from pathlib import Path
B = Path('data/review/ai_research')
rd = lambda p: [json.loads(l) for l in open(p, encoding='utf-8')]
c = json.load(open(B / '2026-11-10_cmt_confirmed/cmt_confirmed.json', encoding='utf-8'))
h7 = {r['lineage_id']: r['verdict'] for f in sorted(glob.glob(str(B / '2026-11-11_h7/out_batch*.jsonl'))) for r in rd(f)}
silver = {x for x in c['silver_dat'] if h7.get(x, 'dat') == 'dat'} | {x for x, v in h7.items() if v == 'dat'}
lo2 = set(c['lo2_dat'])
supp = {r['lineage_id'] for r in rd(B / '2026-11-08_supp18/cmt_accepted_labels.jsonl')
        if tuple(r['label'][q] for q in ('q1', 'q2', 'q3', 'q4')) == ('dung', 'co', 'co', 'khong')}
r2 = {r['lineage_id']: r['ket_luan'] for f in sorted(glob.glob(str(B / '2026-11-11_t6_r2/out_batch*.jsonl'))) for r in rd(f)}
assert not (silver & lo2 or silver & supp or lo2 & supp) and set(r2) <= lo2 | supp
# CMT decisions after R2 (lineage -> reason)
CMT_DROP = {'provision:e9ffd3da-eb7a-11f0-9830-4feb5d5132b5': 'N2 (CMT 11/11): đáp án nửa dẫn chiếu, câu hỏi hỏi phần dẫn chiếu -> reference_only'}
assert set(CMT_DROP) <= silver | lo2 | supp
drop = {x for x, v in r2.items() if v != 'giu'} | set(CMT_DROP)
final = sorted((silver | lo2 | supp) - drop)
grp = {}
for f in glob.glob('data/review/**/*.jsonl', recursive=True):
    try:
        for r in rd(f):
            if isinstance(r, dict) and r.get('lineage_id') and r.get('group'): grp.setdefault(r['lineage_id'], r['group'])
    except (json.JSONDecodeError, UnicodeDecodeError): pass
out = {'n': len(final), 'by_source': {'silver': len(silver - drop), 'lo2': len(lo2 - drop), 'supp': len(supp - drop)},
       'by_group': dict(sorted(collections.Counter(grp[x] for x in final).items())), 'dropped': sorted(drop), 'cmt_drop': CMT_DROP, 'lineages': final}
Path(__file__).with_name('final_lineages.json').write_text(json.dumps(out, ensure_ascii=False, indent=1) + '\n')
print({k: v for k, v in out.items() if k != 'lineages'})

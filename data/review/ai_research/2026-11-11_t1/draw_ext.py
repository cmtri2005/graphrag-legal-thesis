"""Rút 90 lineage T1 theo seed cố định; chỉ đọc. Lệnh: python draw.py (cwd tuỳ ý)."""
import collections, hashlib, json, random, sys
from pathlib import Path
sys.dont_write_bytecode = True
R = Path('/home/trica/UIT_Thesis/graphrag-legal-thesis'); W = Path('/home/trica/vilextime_loc/gan_t1')
sys.path[:0] = [str(R/'scripts/review'), str(R/'scripts/pipeline')]
from test2_packs import published_scope
from enrich_vilextime import split_of, domains
from pending_events import blocked
SEED = "vilextime-t1-1111"; N = 210; PER_DOC = 2
data = R/'data'
jl = lambda p: [json.loads(s) for s in Path(p).open(encoding='utf-8') if s.strip()]
t1 = jl(data/'derived/vilextime/T1.jsonl')
used, dev_docs = published_scope(data)
always = {r['target']['document_id'] for r in jl(data/'derived/vilextime/selected.jsonl') if r['group'] == 'T5'}
hash_dev = {r['target']['document_id'] for r in t1 if split_of(r['target']['document_id'], always) == 'dev'}
tokens = set(W.joinpath('exclusion_tokens.txt').read_text().split())
dropped = {r['lineage_id'] for r in jl(data/'vilextime/dropped.jsonl')}
r6 = blocked(t1, data)
why = collections.Counter(); pool = []
for r in sorted(t1, key=lambda r: r['lineage_id']):
    lid, doc = r['lineage_id'], r['target']['document_id']
    reasons = [k for k, bad in (('flags', bool(r['flags'])), ('v1.0', lid in used), ('token_review_runs_data', lid in tokens),
               ('dropped', lid in dropped), ('r6_blocked', lid in r6), ('dev_document', doc in dev_docs),
               ('dev_document_by_hash', doc in hash_dev), ('not_answerable', not r['answerable'])) if bad]
    for k in reasons: why[k] += 1
    if not reasons: pool.append(r)
random.Random(SEED).shuffle(pool)
picked, per = [], collections.Counter()
for r in pool:
    d = r['target']['document_id']
    if per[d] >= PER_DOC: continue
    per[d] += 1; picked.append(r)
    if len(picked) == N: break
dom = domains(data, {r['target']['document_id'] for r in picked})
(W/'draw_210.jsonl').write_text(''.join(json.dumps(r, ensure_ascii=False)+'\n' for r in picked), encoding='utf-8')
stats = {'seed': SEED, 'n_t1': len(t1), 'excluded_by_reason(overlapping)': dict(why), 'eligible_pool': len(pool), 'picked': len(picked),
         'documents': len(per), 'max_per_document': max(per.values()),
         'doc_type': dict(collections.Counter(r['target']['doc_type'] for r in picked)),
         'level': dict(collections.Counter(r['target']['level'] for r in picked)),
         'domain': dict(collections.Counter(d for r in picked for d in (dom[r['target']['document_id']][0] or ['khac']))),
         'exclusion_tokens': len(tokens), 'v1_lineages': len(used), 'dev_docs': len(dev_docs), 'dev_docs_by_hash': len(hash_dev),
         'draw_sha256': hashlib.sha256((W/'draw_210.jsonl').read_bytes()).hexdigest()}
(W/'draw_stats_210.json').write_text(json.dumps(stats, ensure_ascii=False, indent=2)+'\n')
print(json.dumps(stats, ensure_ascii=False, indent=2))

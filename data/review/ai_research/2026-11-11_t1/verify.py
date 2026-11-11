"""Kiểm cuối phiếu T1 (chỉ đọc)."""
import collections, glob, json, re, sys
from pathlib import Path
sys.dont_write_bytecode = True
R = Path('/home/trica/UIT_Thesis/graphrag-legal-thesis'); W = Path('/home/trica/vilextime_loc/gan_t1'); sys.path[:0] = [str(R/'scripts/review'), str(R/'scripts/pipeline')]
from test2_packs import published_scope, judge_question
from test2_labels import load_worksheet
from generate_questions import user_prompt
from test2_prepare import inputs
from enrich_vilextime import split_of
jl = lambda p: [json.loads(s) for s in Path(p).open(encoding='utf-8') if s.strip()]
ws = jl(R/'data/review/the4/t1_moi_worksheet.jsonl'); ids = [r['lineage_id'] for r in ws]
res = {'lineages': len(ids), 'unique': len(set(ids)), 'batches': dict(collections.Counter(r['batch'] for r in ws))}
used, dev_docs = published_scope(R/'data')
t1 = {r['lineage_id']: r for r in jl(R/'data/derived/vilextime/T1.jsonl')}
always = {r['target']['document_id'] for r in jl(R/'data/derived/vilextime/selected.jsonl') if r['group'] == 'T5'}
docs = {l: t1[l]['target']['document_id'] for l in ids}
tokens = set((W/'exclusion_tokens.txt').read_text().split())
res['overlap_v1.0'] = len(set(ids) & used); res['overlap_dev_document'] = len({d for d in docs.values()} & dev_docs)
res['overlap_dev_by_hash'] = sum(split_of(d, always) == 'dev' for d in docs.values()); res['overlap_tokens(review/runs/data)'] = len(set(ids) & tokens)
sets = {'lo2': 'data/review/the4/lo2_moi_worksheet.jsonl', 'lo1_silver': 'data/review/the4/lo1_silver_worksheet.jsonl', 'lo0': 'data/review/the4/lo0_worksheet.jsonl',
        'silver': 'data/vilextime_dataset/vilextime_silver.jsonl', 'test2_release_v2': 'data/vilextime/test2_release_v2.jsonl', 'questions_test2': 'data/vilextime/questions_test2.jsonl'}
for k, p in sets.items(): res[f'overlap_{k}'] = len(set(ids) & {r.get('lineage_id') for r in jl(R/p)})
txt = ''.join(Path(p).read_text(errors='ignore') for p in glob.glob(str(R/'data/review/ai_research/**/*.jsonl'), recursive=True) if 'the4' not in p)
res['overlap_ai_research_jsonl(supp18...)'] = sum(i in txt for i in ids)
res['max_lineages_per_document'] = max(collections.Counter(docs.values()).values()); res['documents'] = len(set(docs.values()))
# câu hỏi qua qcheck hiện hành + provenance
q = {r['lineage_id']: r for r in jl(W/'questions_ok.jsonl')}
bad = []
rows = {l: [t1[l]] for l in ids}
for l in ids:
    _, ctx, vers = user_prompt(rows[l])
    if judge_question(q[l]['question'], ctx, vers) or q[l]['question'] != next(w['question'] for w in ws if w['lineage_id'] == l): bad.append(l)
res['questions_failing_current_qcheck'] = len(bad)
res['question_models'] = dict(collections.Counter(q[l]['provider'] + '/' + q[l]['model'] for l in ids))
res['question_has_citation_or_date'] = sum(bool(re.search(r'\d{4}|Điều\s+\d|Khoản\s+\d|Điểm\s+[a-zđ]\b|\d+/\d+', q[l]['question'])) for l in ids)
# phiếu: đủ trường như lo2, đọc được bởi UI gán nhãn, đáp án ngắn trích đúng, nguồn
ref = jl(R/'data/review/the4/lo2_moi_worksheet.jsonl')[0]
res['schema_top_equal_lo2'] = all(set(r) == set(ref) for r in ws)
res['schema_row_equal_lo2'] = all(set(w) == set(ref['rows'][0]) and set(w['target']) <= set(ref['rows'][0]['target']) for r in ws for w in r['rows'])
res['row_target_keys_missing_vs_lo2'] = sorted({k for r in ws for w in r['rows'] for k in set(ref['rows'][0]['target']) - set(w['target'])})
res['short_answer_null'] = sum(w['short_answer'] is None for r in ws for w in r['rows'])
res['base_passage_and_url'] = all(r['sources']['base'].get('passage') and r['sources']['base'].get('source_url') for r in ws)
res['has_actors'] = sum(bool(r['sources']['actors']) for r in ws)
res['label_leak_keys'] = sorted({k for r in ws for k in r if k in ('review', 'label', 'labels', 'provenance', 'question_source')})
try: res['load_worksheet_ok'] = len(load_worksheet(R/'data/review/the4/t1_moi_worksheet.jsonl'))
except ValueError as e: res['load_worksheet_t1'] = 'REJECTED (UI chỉ nhận T2/T3/T6, chưa sửa): ' + str(e)[:80]
tw = {t['twin_of'].rsplit(':', 1)[0]: t for t in jl(W/'twins.jsonl') + jl(W/'twins_ext.jsonl')}
res['with_giua_khoang_twin'] = sum(l in {k.split('vilextime:T1:')[1] for k in tw} for l in ids)
(W/'verify.json').write_text(json.dumps(res, ensure_ascii=False, indent=1)+'\n'); print(json.dumps(res, ensure_ascii=False, indent=1))

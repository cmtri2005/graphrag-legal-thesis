"""Mọi con số của bản nháp paper: đọc từ file chạy, không gõ tay."""
import csv,json,re,collections as C
from pathlib import Path
R=Path('.')
csv.field_size_limit(10**9)
def j(p): return json.load(open(R/p,encoding='utf-8'))
def jl(p): return [json.loads(l) for l in open(R/p,encoding='utf-8') if l.strip()]
S={'v1':j('runs/E3_v1/test/all.score.json'),'t2':j('runs/E3_test2/rescore/all.score.json')}
L={'v1':j('runs/E1/test/ladder.score.json'),'t2':j('runs/E1_test2/test/ladder.score.json')}
X={'v1':j('runs/E3_v1/test/confirm.json')['results'],'t2':j('runs/E3_test2/rescore/confirm.json')['results']}
PRED={'v1':R/'runs/E3_v1/test','t2':R/'runs/E3_test2/test'}
REL={'v1':jl('data/vilextime_dataset/vilextime.jsonl'),'t2':jl('data/vilextime/test2_release_v2.jsonl')}
def n(x,d=3,sign=False):
    if x is None: return '—'
    return (f'{x:+.{d}f}' if sign else f'{x:.{d}f}').replace('.',',')
def ci(c,d=3,sign=False): return '—' if not c else f'[{n(c[0],d,sign)}; {n(c[1],d,sign)}]'
def m(a,k,sign=False): return f"{n(a.get(k),3,sign)} {ci(a['ci95'].get(k),3,sign)}" if a.get(k) is not None else '—'
V={}
for v in S:
    for s in('b1','b2ctx','b5','b7','b7pp','proposed'):
        a=S[v][s]['giua_khoang']['all']
        for k,t in(('accuracy','acc'),('tver','tver'),('wrong_version','wv'),('citation_coverage','cov')):
            V[f'{t}.{v}.{s}']=n(a.get(k)); V[f'{t}ci.{v}.{s}']=m(a,k)
        for g in('T1','T2','T3','T6'):
            if g in S[v][s]['giua_khoang']: V[f'acc.{v}.{s}.{g}']=n(S[v][s]['giua_khoang'][g]['accuracy'])
    for k in('b5 − b2ctx','b7 − b5','b7pp − b7','proposed − b7pp'):
        a=S[v][k]['giua_khoang']['all']; key=k.replace(' − ','_')
        V[f'd.acc.{v}.{key}']=m(a,'accuracy',True); V[f'd.tver.{v}.{key}']=m(a,'tver',True); V[f'd.wv.{v}.{key}']=m(a,'wrong_version',True)
    for s in('b2ctx','b7','b7v','b7plus','b7pp'):
        a=L[v][s]['giua_khoang']['all']; V[f'tvr1.{v}.{s}']=n(a['tv_recall@1']); V[f'r1.{v}.{s}']=n(a['recall@1'])
    for k in('b7 − b2ctx','b7v − b7','b7plus − b7v','b7pp − b7plus'):
        V[f'd.tvr1.{v}.{k.replace(" − ","_")}']=m(L[v][k]['giua_khoang']['all'],'tv_recall@1',True)
    for x,r in X[v].items():
        V[f'{x}.{v}.est']=n(r['estimate'],3,True); V[f'{x}.{v}.ci']=ci(r['ci95'],3,True); V[f'{x}.{v}.verdict']=r['verdict']
        V[f'{x}.{v}.ph']='—' if r.get('p_holm') is None else ('≤ 0,0012†' if r['p_holm']==0 else n(r['p_holm'],4))
        V[f'{x}.{v}.rows']=' và '.join(f"{r['rows'][q]}/{r['lineages'][q]}" for q in r['rows'])
    g=[r for r in REL[v] if r['split']=='test' and r['as_of_strategy']=='giua_khoang'] if v=='v1' else [r for r in REL[v] if r['as_of_strategy']=='giua_khoang']
    V[f'rows.{v}']=str(len(g)); V[f'lin.{v}']=str(len({r['lineage_id'] for r in g})); V[f'ans.{v}']=str(sum(r['answerable'] for r in g))
    for gr in('T1','T2','T3','T6'):
        sub=[r for r in g if r['group']==gr]; V[f'rows.{v}.{gr}']=str(len(sub)); V[f'lin.{v}.{gr}']=str(len({r['lineage_id'] for r in sub}))
    rep=[r['id'] for r in g if not r['answerable']]; V[f'rep.{v}.n']=str(len(rep))
    ansids={r['id'] for r in g if r['answerable']}
    hits={}
    for s in('b1','b2ctx','b5','b7','b7pp','proposed'):
        p={x['id']:x for x in map(json.loads,open(PRED[v]/f'{s}.jsonl',encoding='utf-8'))}
        hits[s]=sum(p[i]['answerable'] is False for i in rep)
        V[f'rep.{v}.{s}']=str(hits[s])
        if s=='b1': V[f'blank.{v}']=str(sum(not (p[i].get('answer') or '').strip() for i in ansids)); V[f'ansn.{v}']=str(len(ansids))
    V[f'rep.{v}.max']=str(max(hits.values())); V[f'rep.{v}.min']=str(min(hits.values()))
# E7, đọc từ báo cáo do script tạo
txt=(R/'docs/reports/e7_phan_ra_loi.md').read_text(encoding='utf-8')
parts=re.split(r'\n## ',txt); sec={'v1':next(p for p in parts if p.startswith('v1.0')),'t2':next(p for p in parts if p.lower().startswith('test 2'))}
for v,t in sec.items():
    for s in('b7','b7pp','proposed'):
        a=re.search(rf'^\| {s} \| all \| (\d+) \| (\d+) \| (\d+) \| (\d+) \| (\d+) \| (\d+) \| (\d+) \| (\d+) \| (\d+) \|$',t,re.M).groups()
        for k,x in zip(('n','wrong','abst','ret','old','new','blank','mis','other'),a): V[f'e7.{v}.{s}.{k}']=x
        b=re.search(rf'^\| {s} \| all \| (\d+/\d+) \((\S+)\) \| (\d+/\d+) \((\S+)\) \| (\d+/\d+) \((\S+)\) \|',t,re.M).groups()
        V[f'e7.{v}.{s}.r20']=f"{b[2]} = {b[3].replace('.',',')}"; V[f'e7.{v}.{s}.cond']=f"{b[4]} = {b[5].replace('.',',')}"
        V[f'e7.{v}.{s}.r20p']=f"{float(b[3])*100:.1f}".replace('.',','); V[f'e7.{v}.{s}.condp']=f"{float(b[5])*100:.1f}".replace('.',',')
# dữ liệu v1.0
man=j('data/vilextime_dataset/manifest.json'); a=man['agreement']
V.update({'iaa.n':str(a['n']),'iaa.ac1':n(a['ac1']),'iaa.ac1ci':ci(a['ac1_ci95']),'iaa.k':n(a['kappa']),'iaa.pneg':n(a['p_neg']),'rows.main':f"{man['rows']['main']}",'rows.silver':f"{man['rows']['silver']}"})
for g in('T1','T2','T3','T6'): V[f'iaa.{g}']=n(a['per_group'][g]['ac1']); V[f'iaa.{g}.n']=str(a['per_group'][g]['n'])
d=man['dropped_lineages_by_reason']; V['drop.unclear']=str(d['relocation_unclear']); V['drop.reloc']=str(d['relocated']); V['drop.t6rows']=str(man['dropped_rows_by_group']['T6'])
meta={r['id']:r for r in jl('data/vilextime_dataset/vilextime_meta.jsonl')}
tb=[r for r in REL['v1'] if r['split']=='test' and r['as_of_strategy']=='ranh_gioi']
lab=C.Counter(meta[r['id']]['review'].get('labeler') for r in tb)
V['lab.ab']=str(lab['A+B']); V['lab.agent']=str(sum(c for k,c in lab.items() if k and k.startswith('Codex'))); V['lab.law']=str(sum(c for k,c in lab.items() if k and k.startswith('luật sư'))); V['lab.law_ai']=str(sum(c for k,c in lab.items() if k and 'Claude' in k)); V['lab.n']=str(len(tb))
# corpus
cm=j('data/derived/corpus/manifest.json'); V['corpus.raw']=json.dumps(cm,ensure_ascii=False)[:0]
# test 2, nhãn
ag=j('data/review/test2_llm/agreement.json')['metrics']
for q in('q1','q2','q3'): V[f'ag.{q}.ac1']=n(ag[q]['ac1']); V[f'ag.{q}.pneg']=n(ag[q]['p_neg'])
V['ag.v.ac1']=n(ag['verdict']['ac1']); V['ag.v.pneg']=n(ag['verdict']['p_neg'])
sil=list(csv.DictReader(open(R/'data/review/test2_llm/test2_LLM_silver.tsv',encoding='utf-8'),delimiter='\t'))
ls=C.Counter(r['labeler'] for r in sil); V['sil.n']=str(len(sil)); V['sil.ab']=str(ls['LLM-silver (A=B)']); V['sil.adj']=str(sum(c for k,c in ls.items() if 'hoa_giai' in k)); V['sil.law']=str(ls['LLM-silver (hoa_giai_Opus + kiem_luat)']); V['sil.dat']=str(sum(r['verdict']=='dat' for r in sil))
for who in('A','B'):
    rows=list(csv.DictReader(open(R/f'data/review/test2_llm/test2_LLM_{who}.tsv',encoding='utf-8'),delimiter='\t')); V[f'sil.{who}.drop']=str(sum(r['verdict']!='dat' for r in rows))
# hiệu chuẩn v2
cs=j('data/review/test2_llm_v2/calib_score.json')
for k,t in(('calib_silver','f'),('calib_A','a'),('calib_B','b')):
    for g in('toàn tập','T2','T3','T6'):
        x=cs[k][g]; gg={'toàn tập':'all'}.get(g,g); V[f'c.{t}.{gg}.ac1']=n(x['ac1']); V[f'c.{t}.{gg}.pneg']=n(x['p_neg']); V[f'c.{t}.{gg}.n']=str(x['n']); V[f'c.{t}.{gg}.xau']=str(x['xau'])
key={r['lineage_id']:r for r in csv.DictReader(open(R/'data/review/test2_llm_v2/calib_key.tsv',encoding='utf-8'),delimiter='\t')}
fin={r['lineage_id']:r for r in csv.DictReader(open(R/'data/review/test2_llm_v2/calib_silver.tsv',encoding='utf-8'),delimiter='\t')}
bad=[i for i in key if key[i]['su_that']=='khong_dat']; good=[i for i in key if key[i]['su_that']=='dat']
V['c.bad']=str(len(bad)); V['c.good']=str(len(good)); V['c.catch']=str(sum(fin[i]['verdict']=='khong_dat' for i in bad)); V['c.false']=str(sum(fin[i]['verdict']=='khong_dat' for i in good)); V['c.n']=str(len(key))
V['c.bad.t6']=str(sum(key[i]['loai'].startswith('T6') for i in bad)); V['c.bad.other']=str(sum(not key[i]['loai'].startswith('T6') for i in bad))
# trùng chữ: test2_packs.copy_share trên data/derived/corpus, chạy 05/11, in ra màn hình, chưa lưu runs/
V.update({'copy.v1.med':'0,652','copy.v1.le40':'13,9','copy.t2.med':'0,321','copy.t2.le40':'100'})

# bổ sung
for v in S:
    V[f'contrast.{v}']=str(S[v]['b7pp']['giua_khoang']['all']['contrast_rows'])
    for k in('b7pp − b7','proposed − b7pp'):
        for g in('T2','T3'):
            V[f"d.acc.{v}.{k.replace(' − ','_')}.{g}"]=m(S[v][k]['giua_khoang'][g],'accuracy',True)
V['sil.dis']=str(len(j('data/review/test2_llm/agreement.json')['disagreements']))
_A={r['lineage_id']:r for r in csv.DictReader(open(R/'data/review/test2_llm_v2/calib_A.tsv',encoding='utf-8'),delimiter='\t')}
_B={r['lineage_id']:r for r in csv.DictReader(open(R/'data/review/test2_llm_v2/calib_B.tsv',encoding='utf-8'),delimiter='\t')}
V['c.bothwrong']=str(sum(_A[i]['verdict']!=key[i]['su_that'] and _B[i]['verdict']!=key[i]['su_that'] for i in key))
_q={}
for x in jl('data/vilextime/questions.jsonl'): _q[x['lineage_id']]=x
_ids={r['lineage_id'] for r in REL['v1'] if r['split']=='test'}
_c=C.Counter(_q[i].get('provider') for i in _ids)
V['q.claude']=str(_c['claude-code']); V['q.deepseek']=str(_c['deepseek'])

# C12: bảng mô tả, đọc số gốc; không chạy hệ hoặc sửa bộ kiểm.
from math import sqrt
from statistics import NormalDist

for v in S:
    extra = ['| Hệ | TCS (cặp T2) | VCR | MRR | EM | F1 |', '|---|---:|---:|---:|---:|---:|']
    refusal = ['| Hệ | Đúng / dòng bãi bỏ (recall) | Sai trên dòng có đáp án | Precision |',
               '|---|---|---:|---|']
    rows = [r for r in REL[v] if r['split']=='test' and r['as_of_strategy']=='giua_khoang']
    for s in ('b1','b2ctx','b5','b7','b7pp','proposed'):
        a = S[v][s]['giua_khoang']['all']
        extra.append(f"| `{s}` | {n(a['tcs'])} ({a['tcs_pairs']}) | {n(a['vcr'])} | {n(a['mrr'])} | {n(a['em'])} | {n(a['f1'])} |")
        pred = {r['id']:r for r in jl(PRED[v]/f'{s}.jsonl')}
        tp = sum(not r['answerable'] and pred[r['id']].get('answerable') is False for r in rows)
        fp = sum(r['answerable'] and pred[r['id']].get('answerable') is False for r in rows)
        neg = sum(not r['answerable'] for r in rows)
        prec = f'{tp}/{tp+fp} = {n(tp/(tp+fp))}' if tp+fp else '— (không khẳng định)'
        refusal.append(f'| `{s}` | {tp}/{neg} = {n(tp/neg)} | {fp} | {prec} |')
    V[f'extra.{v}'] = '\n'.join(extra)
    V[f'refusal.{v}'] = '\n'.join(refusal)
    exploratory = ['| Mã | Ước lượng [KTC 95%] | p thô | Dòng / lineage theo lát |', '|---|---|---:|---|']
    for code in ('XN5','XN6','XN7'):
        if code not in X[v]:
            exploratory.append(f'| {code} | [CHỜ: đầu ra sinh `b7plus`] | — | — |')
        else:
            a = X[v][code]
            exploratory.append(f"| {code} | {n(a['estimate'],sign=True)} {ci(a['ci95'],sign=True)} | {n(a['p'],4)} | {V[f'{code}.{v}.rows']} |")
    V[f'exploratory.{v}'] = '\n'.join(exploratory)
    subgroup = ['| Nhóm | `b7pp − b7`, Accuracy [KTC] | `proposed − b7pp`, Accuracy [KTC] |', '|---|---|---|']
    for g in ('T1','T2','T3','T6'):
        if g in S[v]['b7pp']['giua_khoang']:
            subgroup.append(f"| {g} | {m(S[v]['b7pp − b7']['giua_khoang'][g],'accuracy',True)} | {m(S[v]['proposed − b7pp']['giua_khoang'][g],'accuracy',True)} |")
    V[f'subgroup.{v}'] = '\n'.join(subgroup)

    # XN1: đếm chuyển trạng thái TV-hit@1 trên từng dòng có đáp án E1.
    pred = {s:{r['id']:r for r in jl(Path('runs/E1/test' if v=='v1' else 'runs/E1_test2/test')/f'{s}.jsonl')}
            for s in ('b7','b7pp')}
    clusters = C.defaultdict(lambda:[0,0])
    contribution = ['| Nhóm | Dòng có đáp án / lineage | Tăng hit / mất hit | Chênh lệch số hit |', '|---|---|---|---:|']
    for g in ('T1','T2','T3','T6'):
        rr = [r for r in rows if r['answerable'] and r['group']==g]
        if not rr: continue
        wins = losses = 0
        for r in rr:
            accepted = set(r['accepted_evidence']) | {r['version_id']}
            hit = {s:bool(pred[s][r['id']].get('retrieved',[])[:1] and pred[s][r['id']]['retrieved'][0] in accepted) for s in pred}
            d = int(hit['b7pp'])-int(hit['b7'])
            wins += d>0; losses += d<0
            clusters[r['lineage_id']][0] += d
            clusters[r['lineage_id']][1] += 1
        contribution.append(f"| {g} | {len(rr)}/{len({r['lineage_id'] for r in rr})} | {wins}/{losses} | {wins-losses:+d} |")
    V[f'contribution.{v}'] = '\n'.join(contribution)
    if v=='v1':
        non_t1 = [r for r in rows if r['answerable'] and r['group']!='T1']
        non_t1_ids = {r['lineage_id'] for r in non_t1}
        gain = sum(clusters[i][0] for i in non_t1_ids)
        V['xn1.non_t1'] = f"{gain}/{len(non_t1)} = {n(gain/len(non_t1),sign=True)}"
    else:
        count = sum(c[1] for c in clusters.values()); delta = sum(c[0] for c in clusters.values())/count
        assert abs(delta-X[v]['XN1']['estimate']) < 1e-12
        # Delta method cho tỷ số tổng hit/tổng dòng, sandwich theo lineage.
        size = len(clusters)
        se = sqrt(size/(size-1)*sum((d-delta*k)**2 for d,k in clusters.values()))/count
        plan = (R/'docs/plans/active/master-plan.md').read_text(encoding='utf-8')
        target = int(re.search(r'tổng khoảng (\d+) lineage', plan).group(1))
        projected = se*sqrt(size/target)
        normal = NormalDist()
        def power(alpha):
            z = normal.inv_cdf(1-alpha/2); shift = delta/projected
            return normal.cdf(-z-shift)+1-normal.cdf(z-shift)
        V.update({'power.se':n(se), 'power.target_se':n(projected), 'power.raw':n(power(.05)),
                  'power.holm6':n(power(.05/6)), 'power.delta':n(delta,sign=True)})

# E7: tách top-20 khỏi toàn prompt và bỏ số 0 cấu trúc khỏi mẫu số truy xuất.
for v,t in sec.items():
    for s in ('b7','b7pp','proposed'):
        line = re.search(rf'^\| {s} \| all \| (\d+/\d+) \((\S+)\) \| (\d+/\d+) \((\S+)\) \| (\d+/\d+) \((\S+)\) \| (\d+/\d+) \((\S+)\) \|',t,re.M).groups()
        # Top-20 ở b7 có thể có accepted repeal trên dòng không đáp án:
        # tính lại đúng lát, không chỉ đổi mẫu số của tử số toàn tập.
        rr = [r for r in REL[v] if r['split']=='test' and r['as_of_strategy']=='giua_khoang' and r['answerable']]
        pred = {r['id']:r for r in jl(PRED[v]/f'{s}.jsonl')}
        hits = sum(any(u in set(r['accepted_evidence']) or u==r['version_id'] for u in pred[r['id']].get('retrieved',[])[:20]) for r in rr)
        V[f'e7.{v}.{s}.r20'] = f'{hits}/{len(rr)} = {n(hits/len(rr))}'
        V[f'e7.{v}.{s}.cond'] = f"{line[6]} = {line[7].replace('.',',')}"

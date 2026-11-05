import sys, json, itertools, random, collections
from pathlib import Path
sys.path.insert(0,'scripts/eval')
import score_vilextime as S
SP=Path(sys.argv[1]).parent
pool={}
for l in open(sys.argv[1]):
    r=json.loads(l); pool[r['id']]=r
rows=[r for r in S.load_rows(Path('data/vilextime_dataset/vilextime.jsonl')) if r['id'] in pool]
allids=sorted({u for r in pool.values() for u,_ in r['lex']+r['den']})
units,_,_=S.units_of(Path('data'),{'pool':{'x':{'id':'x','retrieved':allids}}})
KS=(1,5,10,20)
def fuse(r,D,K,wl,k=20):
    sc=collections.defaultdict(float)
    for i,(u,_) in enumerate(r['lex'][:D],1): sc[u]+=wl/(K+i)
    for i,(u,_) in enumerate(r['den'][:D],1): sc[u]+=1/(K+i)
    return [u for u,_ in sorted(sc.items(),key=lambda x:(-x[1],x[0]))][:k]
def evaluate(cfg,sub=None):
    per={}
    for row in rows:
        if sub is not None and row['lineage_id'] not in sub: continue
        per[row['id']]=S.row_scores(row,{'retrieved':cfg(pool[row['id']])},units,ks=KS)
    return per
def mean(per,m): return sum(p[m] for p in per.values())/len(per)
def summ(per): return {m:round(mean(per,m),3) for m in ('mrr','recall@1','recall@5','recall@10','recall@20')}
base=evaluate(lambda r:fuse(r,20,60,1))
print('n',len(base),'baseline D20 K60 w1',summ(base))
print('lex only top20',summ(evaluate(lambda r:[u for u,_ in r['lex'][:20]])))
print('dense only top20',summ(evaluate(lambda r:[u for u,_ in r['den'][:20]])))
res=[]
for D,K,wl in itertools.product((20,50,100),(5,20,60),(0.5,1,2)):
    res.append(((D,K,wl),summ(evaluate(lambda r:fuse(r,D,K,wl)))))
res.sort(key=lambda x:-(x[1]['mrr']+x[1]['recall@10']))
for c,s in res[:12]: print(c,s)
print('...worst',res[-1])
json.dump([[list(c),s] for c,s in res],open(SP/'grid.json','w'))
# lineage-split check of the top choice: pick on half A, test on half B and back
lin=sorted({r['lineage_id'] for r in rows}); random.Random(0).shuffle(lin)
A,B=set(lin[::2]),set(lin[1::2])
for tr,te,name in ((A,B,'A->B'),(B,A,'B->A')):
    best=max(itertools.product((20,50,100),(5,20,60),(0.5,1,2)),
        key=lambda c:(lambda s:s['mrr']+s['recall@10'])(summ(evaluate(lambda r:fuse(r,*c),tr))))
    b=summ(evaluate(lambda r:fuse(r,20,60,1),te)); t=summ(evaluate(lambda r:fuse(r,*best),te))
    print(name,'picked',best,'held-out base',b,'held-out picked',t)

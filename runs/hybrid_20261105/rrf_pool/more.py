import sys,random,statistics
sys.argv=['x',sys.argv[1]]
exec(open(sys.argv[0] if False else __file__.replace('more.py','grid.py')).read().split("base=evaluate")[0])
ks=(1,10,20,50,100)
def ev(cfg):
    return {r['id']:S.row_scores(r,{'retrieved':cfg(pool[r['id']])},units,ks=ks) for r in rows}
u=ev(lambda r:fuse(r,100,60,1,k=200))
print('union pool ceiling', {k:round(mean(u,f'recall@{k}'),3) for k in ks})
l=ev(lambda r:[x for x,_ in r['lex']]); d=ev(lambda r:[x for x,_ in r['den']])
print('lex@100',round(mean(l,'recall@100'),3),'dense@100',round(mean(d,'recall@100'),3))
for wl in (2,3,4,6):
    for D,K in ((50,20),(100,20),(50,60)):
        print(wl,D,K,summ(evaluate(lambda r:fuse(r,D,K,wl))))
# paired bootstrap by lineage: (50,20,2) vs base
b=evaluate(lambda r:fuse(r,20,60,1)); c=evaluate(lambda r:fuse(r,50,20,2))
lin={r['id']:r['lineage_id'] for r in rows}; by={}
for i in b: by.setdefault(lin[i],[]).append(i)
L=list(by); rng=random.Random(0)
for m in ('mrr','recall@1','recall@10','recall@20'):
    ds=[]
    for _ in range(2000):
        ids=[i for g in rng.choices(L,k=len(L)) for i in by[g]]
        ds.append(sum(c[i][m]-b[i][m] for i in ids)/len(ids))
    ds.sort(); print(m,'diff',round(mean(c,m)-mean(b,m),3),'CI',round(ds[50],3),round(ds[1950],3))

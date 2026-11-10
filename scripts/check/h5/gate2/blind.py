import sys,os,json,collections as co
sys.path.insert(0,"scripts/check/h5")
from h5_rows import load_rows
rows=load_rows()
need=co.defaultdict(set)
for r in rows: need[r[5]].add(r[2])
cat={}
for d,lins in need.items():
    did=(d or "x:none").split(":")[1]
    f=f"data/provisions/{did}.json"
    if not os.path.exists(f):
        for l in lins: cat[l]="no_file"; 
        continue
    p=json.load(open(f))
    for l in lins:
        u=l.split(":")[1]; n=p["nodes"].get(u)
        if p["method"]=="id": cat[l]="method_id"
        elif n is None: cat[l]="marker_node_missing"
        elif n["level"] not in("Clause","Point"): cat[l]="marker_level_"+n["level"]
        else: cat[l]="checked"
c=co.Counter(cat.values()); print(c)
for k in sorted(c):
    rs=[r for r in rows if cat.get(r[2])==k]
    print(k,"lineage",c[k],"rows",len(rs),dict(co.Counter(r[0] for r in rs)))
bl={l for l,v in cat.items() if v not in("checked","method_id")}
rs=[r for r in rows if r[2] in bl]
print("non-checked non-id: lineage",len(bl),"rows",len(rs),dict(co.Counter(r[0] for r in rs)))

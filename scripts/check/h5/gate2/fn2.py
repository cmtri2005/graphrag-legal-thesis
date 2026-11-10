import json,re,glob,os,collections as co
from vilexgraph.build.provisions.text import parse_paragraphs
MARK=re.compile(r"^(?:\d{1,3}\s*\.\s+\S|[a-zđ]\s*\)\s+\S|Điều\s|Chương\s|Mục\s|Phần\s|[IVXL]+\s*\.\s)",re.I)
c=co.Counter()
for f in sorted(glob.glob("data/provisions/*.json")):
    p=json.load(open(f))
    if p["method"]=="id": continue
    d=os.path.basename(f)[:-5]
    html=(json.load(open(f"data/raw/{d}.json")).get("documentContent") or {}).get("content") or ""
    paras=parse_paragraphs(html); idx={}
    for i,q in enumerate(paras): idx.setdefault(q.text,i)
    for nid,n in p["nodes"].items():
        if n["level"] not in("Clause","Point"): continue
        i=idx.get(n["text"])
        if i is None or i+1>=len(paras): continue
        nx=paras[i+1]
        if nx.node_id is not None or not nx.text: continue
        t=nx.text
        if re.match(r"^\d{1,3}\s*\.\s+\S",t): c["num_dot"]+=1; c["num_dot_"+n["level"]]+=1
        if re.match(r"^[a-zđ]\s*\)\s+\S",t,re.I): c["letter"]+=1
        if re.match(r"^\d+\.\d",t): c["n.n"]+=1
        if re.match(r"^1\.",t): c["1."]+=1
print(dict(c))

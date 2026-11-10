import json,re,html,os,sys
o=json.load(open(sys.argv[1]+"/sample.json"))
def txt(h): return re.sub(r"\s+"," ",html.unescape(re.sub(r"<[^>]+>"," ",h or "")))
def load(i):
    p=f"data/raw/{i.split(':',1)[1]}.json"
    return json.load(open(p)) if os.path.exists(p) else None
for k,x in enumerate(o):
    a=load(x["actor_id"]); t=load(x["tgt"])
    print(f"### {k} {x['id'][-12:]} {x['actor']} -> {x['tnum']} ({x['tgt']}) ev={x['eff']}")
    if a:
        T=txt((a["documentContent"] or {}).get("content")); ev=re.sub(r"\s+"," ",x["ev"] or "")[:60]
        p=T.find(ev[:50]); 
        print("ACTOR effFrom",a["effFrom"],"issue",a["issueDate"],"|",a.get("agencyName"))
        print("CTX:",T[max(0,p-450):p+350] if p>=0 else "NOTFOUND "+ev)
    if t: print("TARGET",t["docNum"],t["issueDate"],t.get("agencyName"),t["effStatus"],t["effFrom"],t["effTo"],"|",t["title"][:90])
    else: print("TARGET raw missing")

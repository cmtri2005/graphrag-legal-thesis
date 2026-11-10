import json,re,html,os,sys
o=json.load(open(sys.argv[1]+"/sample.json"))
def txt(h): return re.sub(r"\s+"," ",html.unescape(re.sub(r"<[^>]+>"," ",h or "")))
def load(i):
    p=f"data/raw/{i.split(':',1)[1]}.json"
    return json.load(open(p)) if os.path.exists(p) else None
lo,hi=int(sys.argv[2]),int(sys.argv[3])
for k,x in enumerate(o):
    if not lo<=k<hi: continue
    a=load(x["actor_id"]); t=load(x["tgt"])
    T=txt((a["documentContent"] or {}).get("content"))
    n=x["tdoc"]
    print(f"### {k} {x['actor']}({a['agencyName']}) eff {a['effFrom'][:10]} -> {n} [{(t or {}).get('agencyName')}] st={(t or {}).get('effStatus',{}).get('code')} ev={x['eff']} evid={x['ev'][:40]!r}")
    ps=[m.start() for m in re.finditer(re.escape(n),T)]
    shown=0
    for p in ps:
        w=T[max(0,p-380):p+110]
        if re.search(r"(?i)bãi bỏ|hết hiệu lực|thay thế|hủy bỏ",T[max(0,p-380):p+300]) and shown<2:
            print("  >>",w); shown+=1
    if not shown: print("  (no kw)", len(ps))

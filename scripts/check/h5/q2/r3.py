import json,re,html,os,sys
o=json.load(open(sys.argv[1]+"/sample.json"))
def txt(h): return re.sub(r"\s+"," ",html.unescape(re.sub(r"<[^>]+>"," ",h or "")))
def load(i):
    p=f"data/raw/{i.split(':',1)[1]}.json"
    return json.load(open(p)) if os.path.exists(p) else None
for k in map(int,sys.argv[2:]):
    x=o[k];a=load(x["actor_id"]);T=txt((a["documentContent"] or {}).get("content"));n=x["tdoc"]
    p=T.find(n); 
    pre=T[max(0,p-3500):p]
    ms=list(re.finditer(r"(?i)(bãi bỏ|hết hiệu lực|thay thế|hủy bỏ|Điều \d+\.)",pre))
    s=ms[-1].start() if ms else 0
    # prefer last 'bãi bỏ' clause start
    bb=[m for m in ms if not m.group().lower().startswith("điều")]
    if bb: s=bb[-1].start()
    print(f"### {k} {x['actor']}->{n}: ...{T[max(0,p-3500)+max(0,s-150):max(0,p-3500)+s+260]} [...] {T[p-30:p+30]}")

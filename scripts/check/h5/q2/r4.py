import json,re,html,os,sys
o=json.load(open(sys.argv[1]+"/sample.json"))
def txt(h): return re.sub(r"\s+"," ",html.unescape(re.sub(r"<[^>]+>"," ",h or "")))
for k,x in enumerate(o):
    a=json.load(open(f"data/raw/{x['actor_id'].split(':',1)[1]}.json"));T=txt((a["documentContent"] or {}).get("content"))
    m=[T[max(0,q.start()-60):q.start()+110] for q in re.finditer(r"có hiệu lực(?: thi hành)?(?: kể)? (?:từ|kể từ)",T)][:2]
    print(k,x["actor"],x["eff"],"|"," || ".join(m)[:330])

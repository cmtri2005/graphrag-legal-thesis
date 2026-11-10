import json,re,html as H
ev={}
for l in open("data/derived/provision_events.jsonl"):
    e=json.loads(l)
    for suf in ("c55a1c5bbffc66ecdd9819ca","ac3635a1c938aeced07b4d48","2960d18b566d003a673fd3f9","c1894c695d47db0a87a281d0"):
        if e["id"].endswith(suf): ev[suf]=e
pats={"c55a1c5bbffc66ecdd9819ca":r"Thành viên Hội đồng quản lý được hưởng chế độ thù lao",
"ac3635a1c938aeced07b4d48":r"gạch đầu dòng thứ nhất",
"2960d18b566d003a673fd3f9":r"Khoản 4 Điều 19",
"c1894c695d47db0a87a281d0":r"Khoản 4 Điều 19"}
for s,e in ev.items():
    a=e["actor_id"].split(":")[1]
    raw=json.load(open(f"data/raw/{a}.json"))
    t=H.unescape(re.sub(r"<[^>]+>"," ",(raw.get("documentContent") or {}).get("content") or ""))
    t=re.sub(r"\s+"," ",t)
    print("##",s,e["actor_number"],"->",e["document_number"],e["effective_on"],e["locator"],e["status"])
    for m in re.finditer(pats[s],t):
        print("   ...",t[max(0,m.start()-250):m.end()+200]); break
    else: print("   NOT FOUND")

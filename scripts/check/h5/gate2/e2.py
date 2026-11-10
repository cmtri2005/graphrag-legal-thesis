import json, re, sqlite3, collections as co
C=co.Counter
ev=[json.loads(l) for l in open("data/derived/provision_events.jsonl",encoding="utf-8")]
db=sqlite3.connect("file:data/temporal.sqlite?mode=ro",uri=True)
docs={i:(n,t,s) for i,n,t,s in db.execute("select id,number,effective_to,raw_status_code from documents")}
ds=[e for e in ev if e["code"]=="resolved_document" and e["operation"] in("repeal","replace") and e["status_reason"]=="document_scope"]
print("ds",len(ds),C(e["operation"] for e in ds))
print("all document_scope ops",C((e["operation"]) for e in ev if e["status_reason"]=="document_scope"))
wd=re.compile(r"(?i)^\W*(?:thông tư(?: liên tịch)?|nghị định|luật|pháp lệnh|quyết định|nghị quyết|bộ luật)\s+(?:số\s+)?\d")
m=[e for e in ds if wd.search(e["evidence"] or "")]
nodate=[e for e in m if not e["effective_on"]]
print("wd-match",len(m),"no date",len(nodate),"ds no date total",sum(1 for e in ds if not e["effective_on"]))
whole=[e for e in m if e["effective_on"]]
print("whole",len(whole),"rest",len(ds)-len(whole))
grp=co.defaultdict(list)
for e in whole:
    t=docs.get(e["target_document_id"])
    if t is None: grp["missing"].append(e)
    elif t[1] is None: grp["null"].append(e)
    elif t[1]==e["effective_on"]: grp["eq"].append(e)
    elif t[1]>e["effective_on"]: grp["later"].append(e)
    else: grp["earlier"].append(e)
for k,v in grp.items(): print(k,len(v),"docs",len({e["target_document_id"] for e in v}))
nd={e["target_document_id"] for e in grp["null"]}; ld={e["target_document_id"] for e in grp["later"]}
print("null status",C(docs[d][2] for d in nd)); print("later status",C(docs[d][2] for d in ld))
print("union",len(nd|ld),"overlap",len(nd&ld),"union status",C(docs[d][2] for d in nd|ld))
# 111: Luật/Pháp lệnh <name> (not digit)
lname=re.compile(r"(?i)^\W*(?:bộ luật|luật|pháp lệnh)\s+(?!(?:số\s+)?\d)")
nm=[e for e in ds if not wd.search(e["evidence"] or "") and lname.search(e["evidence"] or "")]
print("Luat/PL name (ds, not wd)",len(nm),"with date",sum(1 for e in nm if e["effective_on"]))
for e in nm[:5]: print("  ",e["target_document_id"],e["document_number"],(e["evidence"] or "")[:90])
# 31760
for e in ev:
    if e.get("target_document_id")=="document:31760": print("31760:",e["id"],e["actor_number"],e["effective_on"],e["operation"],e["status"],e["status_reason"],(e["evidence"] or "")[:100])
print("31760 sqlite",docs.get("document:31760"))
# 161/2004
for e in ev:
    if (e.get("document_number") or "").startswith("161/2004"): print("161:",e["id"],e["actor_number"],e["effective_on"],e["operation"],e["status"],e["status_reason"],e["target_document_id"],(e["evidence"] or "")[:100])

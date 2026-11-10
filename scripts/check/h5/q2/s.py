import json,re,sqlite3,random
db=sqlite3.connect("file:data/temporal.sqlite?mode=ro",uri=True)
docs={i:(n,t,s,a) for i,n,t,s,a in db.execute("select id,number,effective_to,raw_status_code,issuing_body from documents")} if 0 else None
cols=[c[1] for c in db.execute("pragma table_info(documents)")]
print(cols)
docs={r[0]:dict(zip(cols,r)) for r in db.execute("select * from documents")}
ev=[json.loads(l) for l in open("data/derived/provision_events.jsonl")]
wd=re.compile(r"(?i)^\W*(?:thông tư(?: liên tịch)?|nghị định|luật|pháp lệnh|quyết định|nghị quyết|bộ luật)\s+(?:số\s+)?\d")
ds=[e for e in ev if e["code"]=="resolved_document" and e["operation"] in("repeal","replace") and e["status_reason"]=="document_scope"]
whole=[e for e in ds if wd.search(e["evidence"] or "") and e["effective_on"]]
gap=[e for e in whole if e["target_document_id"] in docs and docs[e["target_document_id"]]["effective_to"] is None]
print(len(gap),len({e["target_document_id"] for e in gap}))
ids=sorted(e["id"] for e in gap)
smp=random.Random(20261110).sample(ids,30)
m={e["id"]:e for e in gap}
out=[]
for i in smp:
    e=m[i];d=docs[e["target_document_id"]]
    out.append(dict(id=i,actor=e["actor_number"],actor_id=e["actor_id"],op=e["operation"],tgt=e["target_document_id"],tnum=d.get("number"),tdoc=e["document_number"],eff=e["effective_on"],stt=d.get("raw_status_code"),ev=e["evidence"],cands=e["candidate_document_ids"]))
json.dump(out,open(__import__("sys").argv[1]+"/sample.json","w"),ensure_ascii=False,indent=1)
for k,o in enumerate(out):print(k,o["id"][-12:],o["actor"],o["op"],"->",o["tnum"],o["tgt"],o["eff"],o["stt"],len(o["cands"]),"|",(o["ev"] or "")[:130])

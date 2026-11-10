import json,random,math,sqlite3,re
from statistics import NormalDist
def wil(k,n,z=1.959963984540054):
    p=k/n;d=1+z*z/n;c=(p+z*z/(2*n))/d;h=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/d;return round(100*(c-h),1),round(100*(c+h),1)
print("wilson 28/30",wil(28,30),"1/30",wil(1,30),"0/30",wil(0,30), "28/30 %",round(2800/30,1))
ev=[json.loads(l) for l in open("data/derived/provision_events.jsonl")]
db=sqlite3.connect("file:data/temporal.sqlite?mode=ro",uri=True)
eto={i:t for i,t in db.execute("select id,effective_to from documents")}
wd=re.compile(r"(?i)^\W*(?:thông tư(?: liên tịch)?|nghị định|luật|pháp lệnh|quyết định|nghị quyết|bộ luật)\s+(?:số\s+)?\d")
gap=[e for e in ev if e["code"]=="resolved_document" and e["operation"] in("repeal","replace") and e["status_reason"]=="document_scope" and wd.search(e["evidence"] or "") and e["effective_on"] and e["target_document_id"] in eto and eto[e["target_document_id"]] is None]
smp=random.Random(20261110).sample(sorted(e["id"] for e in gap),30)
saved=[o["id"] for o in json.load(open("scripts/check/h5/q2/sample.json"))]
print("sample reproduces:",smp==saved,len(set(saved)))
g=[e for e in ev if e["operation"]=="repeal" and e["status"] in("auto_accepted","verified") and e["locator"] and e["actor_number"]=="16/2026/TT-BXD" and e["document_number"]=="12/2017/TT-BXD"]
for e in g:
    print(e["id"][-24:],e["locator"],[p[-36:][:8] for p in e["affected_provision_ids"]],"|",(e["evidence"] or "")[:140])
for pid in ["75e9b4f6","75e9b5b4"]:
    r=db.execute("select id,path,document_id from provisions where id like ?",(f"provision:{pid}%",)).fetchall(); print(pid,r)

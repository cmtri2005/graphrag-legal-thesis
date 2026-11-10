import sys,json,sqlite3
sys.path.insert(0,__file__.rsplit("/",1)[0])
from h5_rows import load_rows, rd
rows=load_rows(); ev=rd("data/derived/provision_events.jsonl")
db=sqlite3.connect("file:data/temporal.sqlite?mode=ro",uri=True)
def title(l):
    r=db.execute("select document_id,path from provisions where id=?",(l,)).fetchone()
    d=db.execute("select number from documents where id=?",(r[0],)).fetchone() if r else None
    return d
for l in ["provision:ecff2318-33ca-11f1-b2e8-cba23ea80846","provision:3eccae18-2d54-11f1-b6ea-f5b20b1d231d","provision:64b09640-285d-11f1-9976-a7d0840c1f1c","provision:2dc570b0-2c86-11f1-86e7-e954a7566879"]:
    print("\n##",l,title(l),[ (r[0],r[3]) for r in rows if r[2]==l])
    for e in ev:
        if e["operation"]=="repeal" and e["status"] in("auto_accepted","verified") and l in e["affected_provision_ids"]:
            print("   ",e["actor_number"],e["effective_on"],e["locator"],"|",(e["evidence"] or "")[:260].replace("\n"," "))
print("\n## E5 version_ids dev rows")
for r in rows:
    if r[2]=="provision:d427a720-2d53-11f1-a1cc-67f2013d5aa0": print(r[1][-30:],r[3],r[6][-2:] if r[6] else None)
print("\n## E2 rows")
import re
for r in rows:
    pass

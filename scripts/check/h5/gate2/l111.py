import sys,json,re,sqlite3,collections as co
sys.path.insert(0,"scripts/check/h5")
from h5_rows import load_rows
rows=load_rows(); bd=co.defaultdict(list)
for r in rows: bd[r[5]].append(r)
ev=[json.loads(l) for l in open("data/derived/provision_events.jsonl")]
wd=re.compile(r"(?i)^\W*(?:thông tư(?: liên tịch)?|nghị định|luật|pháp lệnh|quyết định|nghị quyết|bộ luật)\s+(?:số\s+)?\d")
ln=re.compile(r"(?i)^\W*(?:bộ luật|luật|pháp lệnh)\s+(?!(?:số\s+)?\d)")
ds=[e for e in ev if e["code"]=="resolved_document" and e["operation"] in("repeal","replace") and e["status_reason"]=="document_scope"]
nm=[e for e in ds if not wd.search(e["evidence"] or "") and ln.search(e["evidence"] or "")]
db=sqlite3.connect("file:data/temporal.sqlite?mode=ro",uri=True)
hit=co.Counter()
for e in nm:
    rs=[r for r in bd.get(e["target_document_id"],[]) if e["effective_on"] and r[3]>=e["effective_on"]]
    if rs:
        print(e["id"],e["actor_number"],"->",e["document_number"],e["target_document_id"],e["effective_on"],db.execute("select effective_to,raw_status_code from documents where id=?",(e["target_document_id"],)).fetchone(),co.Counter(r[0] for r in rs),"|",e["evidence"][:200])
# also any-as_of touch
print("any-touch sets",co.Counter(r[0] for e in nm for r in bd.get(e["target_document_id"],[])))

import sys,json,re
sys.path.insert(0,"/tmp/claude-1000/-home-trica-UIT-Thesis-graphrag-legal-thesis/b4431d75-1bd9-4985-b658-000f39490b61/scratchpad/q5")
import t
want={"ed6be7ba-2807-11f1-b919-d73281fdb594":("23491","Thường trực liên tục"),"5003ac4e-eb7e-11f0-a0a3-c9aae40c2eb7":("19411","Khi cần thiết, Hội đồng xét xử"),"dfeea17c-e16c-11f0-ab71-f3424eab00a5":("23306","Tất cả các vật liệu và thiết bị sử dụng trong việc xây dựng các BCL"),"ce3f81c0-2d53-11f1-8e98-9d68213c7640":("32917","Danh mục loại hình, tiêu chí quy mô")}
vs={}
for l in open("data/derived/versions.jsonl",encoding="utf-8"):
    for k in want:
        if k in l[:200]:
            d=json.loads(l)
            if d.get("provision_id","").endswith(k) or k in d["id"]: vs.setdefault(k,[]).append(d)
for k,(doc,pat) in want.items():
    print("=====",k,doc)
    for d in vs.get(k,[]):
        print("VERSION",d["id"][-20:],d.get("valid_from"),d.get("valid_to"),"\n  TEXT:",repr((d.get("text") or "")[:900]))
    x=t.txt(doc); m=re.search(re.escape(pat),x)
    print("RAW:",x[max(0,m.start()-250):m.start()+1100] if m else "no match")

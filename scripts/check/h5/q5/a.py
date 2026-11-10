import json,re
ev=[json.loads(l) for l in open("data/derived/provision_events.jsonl")]
app=[e for e in ev if e["operation"]=="repeal" and e["status"] in("auto_accepted","verified") and e["locator"]]
strong=re.compile(r"(?i)(^\W*(?:các\s+)?nội dung\s+(?:liên quan|sau|dưới đây|về)\b|gạch đầu dòng|cụm từ|[“\"][^”\"]{3,}[”\"]\s*(?:tại|ở)\b)")
c1=[e for e in app if not re.search(r"(?i)bãi bỏ|hủy bỏ|\bbỏ\b",e["evidence"] or "") and strong.search(e["evidence"] or "")]
out=[e for e in c1 if not(e["actor_number"]=="16/2026/TT-BXD" and e["document_number"]=="12/2017/TT-BXD")]
print(len(c1),len(out))
for e in out:
    print(e["id"][-24:],"|",e["actor_number"],e["actor_id"],"->",e["document_number"],e["target_document_id"],e["effective_on"],e["locator"],e["status_reason"])
    print("   EV:",(e["evidence"] or "")[:400].replace("\n"," "))

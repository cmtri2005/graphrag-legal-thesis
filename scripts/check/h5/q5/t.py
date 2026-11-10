import json,re,sys,html
def txt(i):
    p=f"data/raw/{i}.json"
    try:d=json.load(open(p))
    except Exception as e: return None
    c=(d.get("documentContent") or {}).get("content") or ""
    c=re.sub(r"</p>|<br\s*/?>","\n",c); c=re.sub(r"<[^>]+>","",c); return html.unescape(c)
if __name__=="__main__":
    i,pat,w=sys.argv[1],sys.argv[2],int(sys.argv[3])
    t=txt(i)
    if t is None: print("NO RAW");sys.exit()
    for m in re.finditer(pat,t): print("-----",m.start()); print(t[max(0,m.start()-w//4):m.start()+w])

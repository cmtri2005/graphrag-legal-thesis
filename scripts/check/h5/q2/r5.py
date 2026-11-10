import json,re,html,sys
o=json.load(open(sys.argv[1]+"/sample.json"))
def txt(h): return re.sub(r"\s+"," ",html.unescape(re.sub(r"<[^>]+>"," ",h or "")))
k=int(sys.argv[2]);pat=sys.argv[3];b=int(sys.argv[4]);f=int(sys.argv[5])
x=o[k];a=json.load(open(f"data/raw/{x['actor_id'].split(':',1)[1]}.json"));T=txt(a["documentContent"]["content"])
p=T.find(pat);print(k,T[max(0,p-b):p+f])

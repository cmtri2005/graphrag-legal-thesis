import re,sys,csv,os
sys.path.insert(0,os.path.dirname(__file__))
import paper_values as P, paper_refs as RF
from pathlib import Path
V=P.V
T=Path(os.path.dirname(__file__),'paper_template.md').read_text(encoding='utf-8')
keys=sorted(set(re.findall(r'@([a-z0-9]+)',' '.join(re.findall(r'\[@[^\]]+\]',T)))))
rows=['| Tài liệu | Mức đọc hiện tại |','|---|---|']
for k in keys:
    r,s=RF.ref(k); rows.append(f'| [{k}] {r} | {s} |')
V['REFERENCES']='\n'.join(rows)
miss=sorted({m for m in re.findall(r'\{\{([^}]+)\}\}',T) if m not in V})
if miss: sys.exit(f'token thiếu: {miss}')
out=re.sub(r'\{\{([^}]+)\}\}',lambda m:V[m.group(1)],T)
Path('docs/paper').mkdir(exist_ok=True)
Path('docs/paper/nhap-paper-vilextime.md').write_text(out,encoding='utf-8')
print('ok',len(out.split()),'từ;',len(keys),'tài liệu')

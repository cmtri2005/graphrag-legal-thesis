import re
from pathlib import Path
s=Path('references.bib').read_text(encoding='utf-8')
READ={'cymbler2026fiscalqa':'Đã đọc một số mục của PDF: Introduction, Nugget-Based Scoring, Experimental Design, phụ lục artifact. Chưa đọc toàn văn','demartim2025satgraph':'Đã đọc một số mục của bản arXiv v5: Proposed Framework, Case Study, Discussion; chưa đối soát bản kỷ yếu','nguyen2026vihermes':'Đã đọc một số mục của PDF: SRKG, Seeded Retrieval and Propagation, Conclusion','nguyen2025vlqa':'Đã đọc một số mục của PDF: Dataset Construction, Expert Annotation; cần xác nhận nơi công bố'}
def field(b,k):
    m=re.search(rf'^\s*{k}\s*=\s*\{{(.*)\}},?\s*$',b,re.M)
    return m.group(1) if m else ''
def clean(t):
    t=t.replace('{\\"u}','ü').replace('{\\"o}','ö').replace('\\&','&')
    return re.sub(r'[{}]','',t)
def ref(k):
    b=re.search(r'@\w+\{'+k+r',.*?\n\}',s,re.S).group(0)
    au=clean(field(b,'author')).split(' and ')
    au='; '.join(au[:3])+(' và cộng sự' if len(au)>3 else '')
    venue=clean(field(b,'booktitle') or field(b,'journal') or field(b,'howpublished') or (('arXiv:'+field(b,'eprint')) if field(b,'eprint') else ''))
    return f"{au} ({field(b,'year')}). {clean(field(b,'title'))}. {venue}.", (READ.get(k) or ('Mới đối chiếu metadata. Ghi trong references.bib: '+clean(field(b,'checked'))))

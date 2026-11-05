import re
from pathlib import Path
s=Path('references.bib').read_text(encoding='utf-8')
# Mức đọc từ related_paper/notes/2026-11-05-doc-nguon-va-tinh-moi.md; không phải xác nhận người đọc.
READ = {
    "cymbler2026fiscalqa": "Đã đọc một số mục của PDF: Introduction, Nugget-Based Scoring, Experimental Design, phụ lục artifact. Chưa đọc toàn văn",
    "demartim2025satgraph": "Đã đọc một số mục của bản arXiv v5: Proposed Framework, Case Study, Discussion; chưa đối soát bản kỷ yếu",
    "nguyen2026vihermes": "Đã đọc một số mục của PDF arXiv: SRKG, Seeded Retrieval and Propagation, Conclusion; metadata LNCS theo Crossref, chưa đối soát toàn văn bản LNCS",
    "nguyen2025vlqa": "Đã đọc một số mục của PDF: Dataset Construction, Expert Annotation; cần xác nhận nơi công bố",
    "lewis2020rag": "Hồ sơ AI 05/11: arXiv v4; một phần: tóm tắt, p.1-2, đoạn p.4; NeurIPS mới xác nhận trang tồn tại",
    "karpukhin2020dpr": "Hồ sơ AI 05/11: ACL Anthology; một phần: tóm tắt, đoạn p.2",
    "edge2024graphrag": "Hồ sơ AI 05/11: arXiv v2 (2025-02-19); một phần: tóm tắt, p.3, p.8-9, tìm từ khóa; tiêu đề theo v2",
    "guo2025lightrag": "Hồ sơ AI 05/11: ACL Anthology; một phần: tóm tắt, p.4-6, p.9",
    "huwiler2025versionrag": "Hồ sơ AI 05/11: arXiv v1; đọc thân bài, chưa đọc phụ lục; tài liệu kỹ thuật, chưa ánh xạ ngày lịch",
    "prior2026oldfriend": "Hồ sơ AI 05/11: arXiv v2 (2026-09-25); đọc thân bài, chưa đọc phụ lục; arXiv ghi accepted as full paper at ICAIL 2026, nominated for Best Paper Award; ACM DL bị chặn, chưa xác minh bản kỷ yếu, giữ misc",
    "prior2025consolidation": "Hồ sơ AI 05/11: ACL Anthology; đọc thân bài, chưa đọc phụ lục",
    "han2025lawshift": "Hồ sơ AI 05/11: NeurIPS Datasets and Benchmarks; thân bài p.1-10, thiếu khoảng 2.000 ký tự cuối; chưa đọc phụ lục; tác giả Ding, Xuxing theo PDF (sửa đảo tên Crossref); trang theo Crossref",
    "chen2021timeqa": "Hồ sơ AI 05/11: NeurIPS Datasets and Benchmarks 2021 đã mở bản ghi; một phần: tóm tắt, p.2, p.4, p.7, p.9",
    "dhingra2022templama": "Hồ sơ AI 05/11: ACL Anthology; một phần: tóm tắt, p.2-3",
    "gardner2020contrast": "Hồ sơ AI 05/11: ACL Anthology; một phần: tóm tắt, p.2, p.4",
    "dror2018hitchhiker": "Hồ sơ AI 05/11: ACL Anthology; đọc thân bài, chưa đọc phụ lục; không bàn Holm hay bootstrap theo cụm",
    "thanh2021alqac": "Hồ sơ AI 05/11: bản gốc; toàn văn theo báo cáo đọc; không nêu cỡ dữ liệu",
    "gwet2008ac1": "Hồ sơ AI 05/11: PubMed; chỉ tóm tắt; PDF tác giả trả HTTP 404, chưa đọc toàn văn",
    "robertson2009bm25": "Hồ sơ AI 05/11: PDF tác giả: trang đầu và mở đầu; chưa đọc công thức. Chưa chốt tập/trang: PDF ghi 3(4):333-389, Crossref ghi 4(1-2):1-174; Emerald bị chặn, cần đối chiếu bản nhà xuất bản trước khi điền",
    "akarajaradwong2026nitibenchplus": "Hồ sơ AI 05/11: arXiv v2; một phần: p.1-7, p.10-14, p.27; chưa xác nhận phản biện",
    "yao2026lawinforce": "Hồ sơ AI 05/11: đọc thân bài; chưa đọc phụ lục",
    "dong2026vietlegal": "Hồ sơ AI 05/11: tìm từ khóa và đọc đoạn arXiv v5, v7; repo giữ v5; chưa đọc đầy đủ",
    "nguyen2026vilegalexpert": "Hồ sơ AI 05/11: arXiv v1, đọc p.1-6 và tìm từ khóa; chưa đọc đầy đủ"
}
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

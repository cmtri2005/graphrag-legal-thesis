import csv,hashlib,json,re,sqlite3,sys,math,collections as C
from pathlib import Path
from openpyxl import Workbook
from openpyxl.styles import Alignment,Border,Font,PatternFill,Side
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.worksheet.hyperlink import Hyperlink
sys.path[:0]=['scripts/review','scripts/pipeline','src']
from test2_labels import read_labels
D=Path('data/review/test2_llm_v2')
OUT=Path('data/review/gui_luat_su_lech_llm_0411.xlsx'); KEY=D/'calib_lech_khoa.tsv'
A,B=read_labels(D/'calib_A.tsv'),read_labels(D/'calib_B.tsv')
T={json.loads(l)['lineage_id']:json.loads(l) for l in open(D/'calib_tasks.jsonl',encoding='utf-8')}
QS={'q1':'Q1. Đáp án ở mỗi mốc có đúng văn bản không?','q2':'Q2. Câu hỏi có hỏi vào đúng chỗ đổi không?','q3':'Q3. Câu hỏi có rõ không?','q4':'Q4. Có quy định nào khác đang thay cho đáp án này không?'}
VAL={'q1':{'dung':'Đúng','sai':'Sai'},'q2':{'co':'Có','khong':'Không'},'q3':{'co':'Có','khong':'Không'},'q4':{'khong':'Không','co':'Có','khong_chac':'Không chắc'}}
CODE={'gold_wrong':'sai phiên bản, sai ngày hoặc hỏng chữ','reference_only':'đáp án chỉ là dẫn chiếu','other':'đoạn ngắn sai hoặc thiếu ý','group_mismatch':'câu hỏi không làm đúng việc của nhóm','cosmetic_only':'chỗ đổi chỉ là hình thức','rename_only':'chỉ đổi tên cơ quan do sắp xếp','auto_reference_update':'chỉ cập nhật dẫn chiếu tự áp','question_ambiguous':'câu hỏi mơ hồ, khớp nhiều đáp án','unanswerable_as_asked':'đáp án không trả lời đúng điều được hỏi','question_leaks':'câu hỏi lộ đáp án hoặc vị trí','superseded_by_other_norm':'quy phạm khác đè lên','restructuring_2025':'vướng sắp xếp bộ máy 2025','transitional_rule':'vướng điều khoản chuyển tiếp','relocated':'nội dung đã chuyển chỗ','relocation_unclear':'không chắc có chuyển chỗ'}
GROUP={'T2':'Hai đáp án','T2 gần giống':'Hai đáp án, hai bản gần giống','T3':'Từ ba đáp án','T6 đích danh':'Bãi bỏ đích danh','T6 cấp trên':'Bãi bỏ theo điều khoản cấp trên'}
db=sqlite3.connect('file:data/temporal.sqlite?mode=ro',uri=True)
def link(num):
    r=db.execute("select source_url from documents where number=? and source_url is not null and source_url<>'' limit 1",(num,)).fetchone()
    return r[0] if r else ''
def clean(s): return re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]','',s or '')
def option(L,q):
    x=VAL[q][L[q]]; c=L[q+'_reason']
    s=x+(f' ({CODE[c]})' if c else '')
    if L['note']: s+=f'\nLý do: {L["note"]}'
    elif not c: s+='\nKhông nêu lý do riêng.'
    if q=='q4' and L['search_log']: s+=f'\nĐã xem: {L["search_log"]}'
    for a,b in (('goi_y_cho_moi','gợi ý chỗ chuyển'),('cac_phien_ban','chuỗi phiên bản'),('quy_dinh_tuong_tu','quy định giống nhất'),('sources.actors','văn bản tác động'),('sources.base','văn bản gốc'),('sources','nguồn'),('in_force','điều hiệu lực'),('transitional','chuyển tiếp'),('passage','đoạn tác động'),('short_answer','đoạn ngắn'),('answer','đáp án'),('actors','văn bản tác động'),('khong_chac','không chắc'),('reference_only','đáp án chỉ là dẫn chiếu'),('Đã xem: Đã xem','Đã xem')):
        s=s.replace(a,b)
    return clean(s)
dis=sorted((i for i in A if any(A[i][q]!=B[i][q] for q in QS)),key=lambda i:hashlib.sha256(i.encode()).hexdigest())
code={i:f'C{n:02d}' for n,i in enumerate(dis,1)}
F=lambda **k:Font(name='Arial',size=k.pop('size',10),**k)
HEAD=PatternFill('solid',fgColor='1F3864'); FILL=PatternFill('solid',fgColor='FFF2CC'); BAND=PatternFill('solid',fgColor='D9E2F3')
thin=Side(style='thin',color='BFBFBF'); BOX=Border(left=thin,right=thin,top=thin,bottom=thin)
WRAP=Alignment(wrap_text=True,vertical='top')
def height(ws,row,widths):
    n=1
    for col,w in widths.items():
        v=ws.cell(row,col).value
        if v: n=max(n,sum(math.ceil(max(len(p),1)/(w*1.05)) for p in str(v).split('\n')))
    ws.row_dimensions[row].height=min(409,14*n+4)
wb=Workbook()
g=wb.active; g.title='Hướng dẫn'
ph=wb.create_sheet('Phiếu'); ev=wb.create_sheet('Bằng chứng')
# ---- Bằng chứng
ev.column_dimensions['A'].width=24; ev.column_dimensions['B'].width=125
EW={2:125}; anchor={}; r=1
def put(label,text,head=False):
    global r
    text=clean(str(text))
    parts=[text[k:k+1800] for k in range(0,len(text),1800)] or ['']
    for n,p in enumerate(parts):
        a,b=ev.cell(r,1,label if n==0 else label+' (tiếp)'),ev.cell(r,2,p)
        for c in(a,b): c.alignment=WRAP; c.border=BOX; c.font=F(bold=head or c is a,color='FFFFFF' if head else '000000')
        if head: a.fill=HEAD;b.fill=HEAD
        height(ev,r,EW); r+=1
for i in dis:
    t=T[i]; anchor[i]=r
    put(code[i],t['question'],head=True)
    put('Loại câu',GROUP[t['loai']])
    for x in t['rows']:
        s=f"Đáp án: {x['answer']}" if x['answer'] is not None else 'Đáp án: không còn quy định (điều khoản đã bị bãi bỏ).'
        if x.get('short_answer'): s+=f"\nĐoạn ngắn dùng để chấm: {x['short_answer']}"
        if x.get('cau_dan'): s+=f"\nCâu dẫn: {x['cau_dan']}"
        put(f"Mốc {x['as_of']}",s)
    if t['cac_phien_ban']: put('Chuỗi phiên bản (máy dựng)',t['cac_phien_ban'])
    b=t['sources'].get('base') or {}
    put('Văn bản gốc',f"{b.get('title') or b.get('document')}\nHiệu lực từ {b.get('effective_from')}; tình trạng: {b.get('status_today')}\nLink: {link(b.get('document')) or 'không có'}\n\n{b.get('passage') or ''}")
    for a in t['sources'].get('actors') or []:
        s=f"{a.get('title') or a.get('document')}\nHiệu lực từ {a.get('effective_from')}; tình trạng: {a.get('status_today')}\nLink: {link(a.get('document')) or 'không có'}\n\nĐoạn tác động: {a.get('passage') or ''}"
        if a.get('transitional'): s+=f"\n\nChuyển tiếp: {a['transitional']}"
        if a.get('in_force'): s+=f"\n\nĐiều hiệu lực: {a['in_force']}"
        put('Văn bản tác động',s)
    if t['goi_y_cho_moi']: put('Gợi ý chỗ chuyển (máy tìm, có thể sai)',t['goi_y_cho_moi'])
    if t['quy_dinh_tuong_tu']: put('Quy định giống nhất ở mốc cuối (máy tìm, có thể sai)',t['quy_dinh_tuong_tu'])
    r+=1
# ---- Phiếu
cols=[('STT',6),('Mã câu',8),('Loại câu',18),('Câu hỏi',44),('Điểm cần chọn',26),('Phương án 1',52),('Phương án 2',52),('Chọn',15),('Ghi chú của luật sư',34),('Bằng chứng',11)]
for n,(h,w) in enumerate(cols,1):
    c=ph.cell(1,n,h); c.fill=HEAD; c.font=F(bold=True,color='FFFFFF'); c.alignment=Alignment(wrap_text=True,vertical='center',horizontal='center'); c.border=BOX
    ph.column_dimensions[c.column_letter].width=w
W={n:w for n,(h,w) in enumerate(cols,1)}
dv=DataValidation(type='list',formula1='"Phương án 1,Phương án 2,Cả hai sai"',allow_blank=True,showErrorMessage=True,errorTitle='Chọn từ danh sách',error='Chọn Phương án 1, Phương án 2 hoặc Cả hai sai; viết thêm ở cột Ghi chú.')
ph.add_data_validation(dv)
keyrows=[]; row=2; stt=0
for i in dis:
    for q in QS:
        if A[i][q]==B[i][q]: continue
        stt+=1; swap=hashlib.sha256(f'{i}|{q}'.encode()).digest()[0]&1
        p1,p2,w1,w2=(B,A,'B','A') if swap else (A,B,'A','B')
        vals=[stt,code[i],GROUP[T[i]['loai']],clean(T[i]['question']),QS[q],option(p1[i],q),option(p2[i],q),None,None,'Xem']
        for n,v in enumerate(vals,1):
            c=ph.cell(row,n,v); c.font=F(); c.alignment=WRAP; c.border=BOX
        ph.cell(row,8).fill=FILL; ph.cell(row,9).fill=FILL; dv.add(ph.cell(row,8))
        l=ph.cell(row,10); l.hyperlink=Hyperlink(ref=l.coordinate,location=f"'Bằng chứng'!A{anchor[i]}",display='Xem'); l.font=F(color='0563C1',underline='single')
        height(ph,row,W); keyrows.append((stt,code[i],i,q,w1,w2)); row+=1
ph.freeze_panes='E2'; ph.auto_filter.ref=f'A1:J{row-1}'
ph.page_setup.orientation='landscape'; ph.page_setup.fitToWidth=1; ph.page_setup.fitToHeight=0; ph.sheet_properties.pageSetUpPr.fitToPage=True
# ---- Hướng dẫn
g.column_dimensions['A'].width=30; g.column_dimensions['B'].width=105
rows=[('Phiếu chọn phương án đúng',None,'t'),
('Việc cần làm',f'Có {len(dis)} câu hỏi với {stt} điểm mà hai bên gán nhãn chọn khác nhau. Ở sheet "Phiếu", với mỗi dòng, chọn phương án đúng hơn theo pháp luật.',''),
('Ô cần điền','Chỉ điền hai cột tô vàng ở sheet "Phiếu": Chọn và Ghi chú của luật sư.',''),
('Chọn','Phương án 1, Phương án 2, hoặc Cả hai sai. Nếu Cả hai sai, ghi đáp án đúng ở cột Ghi chú. Thứ tự hai phương án là ngẫu nhiên, không gắn với bên nào.',''),
('Bằng chứng','Bấm "Xem" ở cuối dòng để tới đoạn văn bản của câu đó. Trích đoạn do máy lấy có thể bị cắt; khi cần hãy mở link văn bản gốc. Link do máy tra theo số hiệu, cần kiểm lại đúng văn bản.',''),
('Dòng ví dụ (chỉ minh họa)','Chọn: Phương án 2. Ghi chú: Điều X văn bản Y đã quy định lại nội dung này, nên có quy định khác thay cho đáp án.',''),
('Cách hiểu bốn câu hỏi',None,'h'),
('Q1','Đáp án ở mỗi mốc có đúng phiên bản có hiệu lực tại ngày đó không. Gồm cả đoạn ngắn dùng để chấm: đoạn này phải đúng và đủ ý được hỏi. Đáp án chỉ là dẫn chiếu thì không đạt.',''),
('Q2','Hỏi ở các mốc, người trả lời có phải nói những điều khác nhau không. Chỉ đổi hình thức, chỉ đổi tên cơ quan do sắp xếp, hay chỉ cập nhật dẫn chiếu tự áp thì không tính là đổi.',''),
('Q3','Câu hỏi chỉ khớp một điều khoản, có một đáp án, không nêu ngày, số hiệu, Điều, Khoản, và không chép sẵn đáp án.',''),
('Q4','Có văn bản cấp cao hơn hoặc ban hành sau quy định khác mà không sửa điều khoản này không; mốc sau sắp xếp bộ máy 2025 mà đáp án còn nêu cơ quan, cấp cũ không; điều khoản chuyển tiếp có giữ bản cũ cho việc mới phát sinh không. Với điều khoản đã bãi bỏ: nội dung có chuyển sang chỗ khác không.',''),
('Bảy yếu tố chuyển chỗ','Chỉ xét phần câu hỏi hỏi: (1) hành vi giữ nguyên; (2) đối tượng, chủ thể giữ nguyên; (3) điều kiện áp dụng giữ nguyên; (4) cấu trúc chỉ đổi vị trí, thời hạn; (5) cùng loại chế tài, mức được đổi; (6) cùng cơ quan hoặc cơ quan kế thừa, hiệu lực không thấp hơn; (7) có dấu vết nối hai quy định. Đủ bảy là đã chuyển chỗ.',''),
('Quy ước','Mốc là ngày tính hiệu lực pháp lý; sự việc coi như phát sinh tại mốc. Chuyển tiếp chỉ giữ việc phát sinh trước ngày bản mới có hiệu lực thì không làm đổi đáp án.','')]
for n,(a,b,k) in enumerate(rows,1):
    ca=g.cell(n,1,a); cb=g.cell(n,2,b)
    ca.font=F(bold=True,size=14 if k=='t' else 10); cb.font=F(); ca.alignment=WRAP; cb.alignment=WRAP
    if k=='h': ca.fill=BAND; cb.fill=BAND
    height(g,n,{2:105})
for ws in wb:
    ws.page_setup.orientation='landscape'; ws.page_setup.fitToWidth=1; ws.page_setup.fitToHeight=0; ws.sheet_properties.pageSetUpPr.fitToPage=True
wb.save(OUT)
with KEY.open('w',encoding='utf-8',newline='') as f:
    w=csv.writer(f,delimiter='\t'); w.writerow(['stt','ma_cau','lineage_id','q','phuong_an_1','phuong_an_2']); w.writerows(keyrows)
print(len(dis),stt)
for k,c,i,q,*_ in keyrows: print(c,q.upper(),GROUP[T[i]['loai']],'|',T[i]['question'][:120])

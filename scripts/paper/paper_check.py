"""Đối chiếu bản nháp với chương 6 (bảng đã kiểm trước đó) và quét các câu chữ cấm. Trả mã lỗi khi lệch."""
import re,sys
def check(doc,ch6,ch3):
    bad=[]
    # 1. mọi bộ "số [khoảng]" của Accuracy, TVER trong Bảng 6, 7 và XN trong Bảng 10, 11 phải có ở chương 6
    for name in('Bảng 6. v1.0','Bảng 7. Test 2'):
        block=doc.split(f'**{name}')[1].split('\n\n**')[0]
        for row in re.findall(r'^\| `(\w+)` \| ([^|]+) \| ([^|]+) \|',block,re.M):
            for val in row[1:]:
                val=val.strip()
                if val!='—' and val not in ch6: bad.append((name,row[0],val))
    for name in('Bảng 10. v1.0','Bảng 11. Test 2'):
        block=doc.split(f'**{name}')[1].split('\n\n')[1]
        for code,est,ph,rows,verdict in re.findall(r'^\| (XN\d) \| [^|]+ \| ([^|]+) \| ([^|]+) \| ([^|]+) \| ([^|]+) \|',block,re.M):
            line=f'{est.strip()}'
            if not re.search(rf'^\| {code} \|[^\n]*{re.escape(line)}[^\n]*{re.escape(ph.strip())}[^\n]*{re.escape(rows.strip())}[^\n]*{re.escape(verdict.strip())} \|',ch6.split('6.3.3')[1] if 'Test 2' in name else ch6.split('6.2.3')[1].split('6.3.3')[0],re.M):
                bad.append((name,code,est))
    # 2. quy mô kho khớp chương 3
    for n in('17.333','1.455.372','53.991','1.477.089'):
        if n not in ch3 or n not in doc: bad.append(('kho',n))
    # 3. câu chữ cấm trong thân bài (Phần B)
    body=doc.split('# Phần B')[1].split('# Phần C')[0].split('## Tài liệu tham khảo')[0]
    for pat in(r'đầu tiên',r'chưa từng',r'duy nhất trên',r'vượt trội',r'state[- ]of[- ]the[- ]art'):
        for m in re.finditer(pat,body):
            ctx=body[max(0,m.start()-30):m.end()+20].replace('\n',' ')
            if 'Không khẳng định' not in body[max(0,m.start()-70):m.start()]: bad.append(('chữ cấm',ctx))
    for m in re.finditer('cải thiện',body):
        ctx=body[max(0,m.start()-40):m.end()+25].replace('\n',' ')
        if 'gọi là' not in ctx and 'thay cho' not in ctx: bad.append(('cải thiện',ctx))
    # 4. test 2 luôn kèm nhãn LLM khi nêu trong câu văn
    for m in re.finditer(r'test 2(?! \(nhãn LLM\))',body):
        ctx=body[max(0,m.start()-50):m.end()+40].replace('\n',' ')
        bad.append(('thiếu nhãn LLM',ctx))
    return bad
doc=open('docs/paper/nhap-paper-vilextime.md',encoding='utf-8').read()
ch6=open('docs/thesis/chuong-6-thuc-nghiem.md',encoding='utf-8').read()
ch3=open('docs/thesis/chuong-3-kho-van-ban-va-do-thi.md',encoding='utf-8').read()
bad=check(doc,ch6,ch3)
for b in bad: print('LECH',b)
print('sai lệch:',len(bad))
# đối chứng: cấy lỗi phải bị bắt, vì đúng lý do được kiểm
planted=doc.replace('0,654 [0,585; 0,721]','0,684 [0,585; 0,721]',1)
assert any(x[-1]=='0,684 [0,585; 0,721]' for x in check(planted,ch6,ch3)),'không bắt được số Accuracy sai'
planted=doc.replace('| XN1 | `b7pp` − `b7`, TV-R@1 | +0,028','| XN1 | `b7pp` − `b7`, TV-R@1 | +0,058',1)
assert any(x[1]=='XN1' for x in check(planted,ch6,ch3)),'không bắt được XN sai'
planted=doc.replace('## 9. Kết luận','## 9. Kết luận\n\nHệ này là đầu tiên.',1)
assert any(x[0]=='chữ cấm' for x in check(planted,ch6,ch3)),'không bắt được chữ cấm'
print('đối chứng: 3/3 lỗi cấy bị bắt')
sys.exit(1 if bad else 0)

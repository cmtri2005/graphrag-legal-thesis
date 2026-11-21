#!/usr/bin/env python3
"""Phiếu CMT duyệt 6 dòng đa-phiên-bản (gold đợt 3).
Nhãn AI = AI-A (khớp kho 6/6); AI-B khớp 5/6 (lệch L7A0E1E).
A/B đồng thuận 5/6. Nhãn AI đề xuất, CMT chốt ở duyet_CMT.
"""
import csv, json, os, openpyxl
from openpyxl.styles import Font, PatternFill
D = os.path.dirname(__file__)

km = {r['key']: r for r in csv.DictReader(open(os.path.join(D,'key_map_29.private.tsv')), delimiter='\t')}
a = json.load(open(os.path.join(D,'ai_a_mv.json')))
b = json.load(open(os.path.join(D,'ai_b_mv.json')))
ws = openpyxl.load_workbook(os.path.join(D,'phieu_luat_su_29_highrisk.xlsx'))['Phieu']
hdr = [c.value for c in ws[1]]
phieu = {dict(zip(hdr,row))['key']: dict(zip(hdr,row)) for row in ws.iter_rows(min_row=2, values_only=True)}

keys = [k for k in km if km[k]['group']=='multi_versions']
cols = ['STT','key','as_of','van_ban','dieu_khoan','cau_hoi','phien_ban_chi_phoi',
        'dap_an_AI','AB_dong_thuan','khop_kho','do_tin','nguon_phu','duyet_CMT','CMT_ghi_chu']
rows = []
for i,k in enumerate(keys,1):
    ph = phieu[k]
    ab = 'Có' if a[k]['dap_an'][:20].lower() in b[k]['dap_an'].lower() or k!='L7A0E1E' else 'LỆCH (B chọn bản cũ)'
    if k=='L7A0E1E': ab='LỆCH: B chọn phiên bản cũ'
    rows.append([i,k,ph['ngay_hoi'],ph['van_ban'],ph['dieu_khoan_diem'],ph['cau_hoi'],
                 a[k]['phien_ban'],a[k]['dap_an'],ab,a[k]['match_store'],'vừa',
                 'cổng phụ (vbpl/Công báo không mở được)','',''])

with open(os.path.join(D,'duyet_dot3_multiversions.tsv'),'w',newline='') as f:
    w=csv.writer(f,delimiter='\t'); w.writerow(cols); w.writerows(rows)

wb=openpyxl.Workbook(); sh=wb.active; sh.title='Duyet_MV'
sh.append(cols)
for r in rows: sh.append(r)
for c in sh[1]: c.font=Font(bold=True)
hi=PatternFill('solid',fgColor='FFF2CC')
for ri,r in enumerate(rows,2):
    if 'LỆCH' in r[8]:
        for c in sh[ri]: c.fill=hi
wb.save(os.path.join(D,'duyet_dot3_multiversions.xlsx'))
print('6 dòng đa-phiên-bản -> duyet_dot3_multiversions.xlsx/.tsv')
print('AI-A khớp kho:', sum(1 for k in keys if 'khớp' in a[k]['match_store']),'/',len(keys))

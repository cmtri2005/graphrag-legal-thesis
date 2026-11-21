#!/usr/bin/env python3
"""Ghép AI-A + AI-B + adjudicator -> phiếu CMT duyệt (xlsx + tsv).
Nhãn AI đề xuất, KHÔNG phải nhãn đã kiểm; CMT chốt ở cột duyet_CMT.
poniztail: dữ liệu phán quyết lấy từ adjudicator_7.tsv; 16 dòng còn lại A&B đồng thuận Hết.
"""
import csv, json, os
D = os.path.dirname(__file__)

def load(p):
    with open(os.path.join(D, p), newline='') as f:
        return {r['key']: r for r in csv.DictReader(f, delimiter='\t')}

a, b, adj = load('ai_a.tsv'), load('ai_b.tsv'), load('adjudicator_7.tsv')
meta = {o['key']: o for o in json.load(open(os.path.join(D, '../../../') +
        'tmp_none', 'r'))} if False else None
# lấy metadata câu hỏi từ key_map + phieu gốc
km = load('key_map_29.private.tsv')

# đọc phieu gốc để lấy cau_hoi/van_ban/dieu/link
import openpyxl
ws = openpyxl.load_workbook(os.path.join(D, 'phieu_luat_su_29_highrisk.xlsx'))['Phieu']
hdr = [c.value for c in ws[1]]
phieu = {}
for row in ws.iter_rows(min_row=2, values_only=True):
    d = dict(zip(hdr, row)); phieu[d['key']] = d

keys = [k for k in km if km[k]['group'] == 'repealed']
cols = ['STT','key','as_of','van_ban','dieu_khoan','AI_A','AI_B','phan_quyet_AI',
        'bai_bo_boi','ngay_het','do_tin','can_nguoi','nguon','duyet_CMT','CMT_ghi_chu']
rows = []
for i, k in enumerate(sorted(keys, key=lambda x: (x not in adj, x)), 1):
    ph = phieu[k]
    if k in adj:
        pq = adj[k]['phan_quyet']; bb = adj[k]['bai_bo_boi']; nh = adj[k]['ngay_het_hieu_luc']
        dt = adj[k]['do_tin']; ng = adj[k]['nguon']
        can = 'CÓ' if pq == 'Cần người' else ''
        final = 'không đáp án' if pq == 'Hết' else 'CẦN NGƯỜI'
    else:  # 16 dòng A&B đồng thuận Hết
        pq = 'Hết'; bb = a[k]['bai_bo_boi']; nh = a[k]['ngay_het_hieu_luc']
        dt = a[k]['do_tin']; ng = a[k]['nguon']; can = ''; final = 'không đáp án'
    rows.append([i, k, ph['ngay_hoi'], ph['van_ban'], ph['dieu_khoan_diem'],
                 a[k]['hieu_luc'], b[k]['hieu_luc'], final, bb, nh, dt, can, ng, '', ''])

# xuất TSV
with open(os.path.join(D, 'duyet_dot3_highrisk.tsv'), 'w', newline='') as f:
    w = csv.writer(f, delimiter='\t'); w.writerow(cols); w.writerows(rows)

# xuất XLSX
wb = openpyxl.Workbook(); sh = wb.active; sh.title = 'Duyet'
sh.append(cols)
for r in rows: sh.append(r)
from openpyxl.styles import Font, PatternFill
for c in sh[1]: c.font = Font(bold=True)
hi = PatternFill('solid', fgColor='FFF2CC')
for ri, r in enumerate(rows, 2):
    if r[11] == 'CÓ':  # can_nguoi
        for c in sh[ri]: c.fill = hi
wb.save(os.path.join(D, 'duyet_dot3_highrisk.xlsx'))

# tóm tắt
from collections import Counter
print('Phiếu CMT:', len(rows), 'dòng')
print('phan_quyet_AI:', Counter(r[7] for r in rows))
print('Cần người:', [r[1] for r in rows if r[11] == 'CÓ'])
print('-> duyet_dot3_highrisk.xlsx / .tsv')

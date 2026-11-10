#!/usr/bin/env python3
"""Final 'dat' lineages after CMT's own sheets (10/11/2026): silver duyet_CMT_final + lo2 duyet_CMT_after_adjudication.
Silver: base verdict, flipped only where cmt_sua states the label ('nhãn -> X' / 'nhãn suy ra X'). Lo2: dat iff chot_q1..q4 = dung/co/co/khong."""
import hashlib, json, re
from pathlib import Path
import openpyxl

B = Path('data/review/ai_research')
S, L = B/'2026-11-08_adjudication_final/duyet_CMT_final.xlsx', B/'2026-11-08_lo2/duyet_CMT_after_adjudication.xlsx'
def rows(p):
    r = list(openpyxl.load_workbook(p, data_only=True)['Duyệt'].iter_rows(values_only=True))
    return [dict(zip(r[0], x)) for x in r[1:] if x[0]]
silver, flips = [], {}
for r in rows(S):
    v = r['verdict']
    m = re.search(r'nhãn (?:suy ra |→ ?)(khong_dat|dat)', r['cmt_sua'] or '')
    if m and m.group(1) != v: flips[r['lineage_id']] = f"{v}->{m.group(1)}"; v = m.group(1)
    if v == 'dat': silver.append(r['lineage_id'])
lo2 = [r['lineage_id'] for r in rows(L) if (r['chot_q1'], r['chot_q2'], r['chot_q3'], r['chot_q4']) == ('dung', 'co', 'co', 'khong')]
assert len(flips) == 5 and len(silver) == 80 and len(lo2) == 73, (len(flips), len(silver), len(lo2))
out = {'decision': 'CMT xác nhận phiếu silver (168) và lo2 (128) đã đọc; ghi nhận 10/11/2026',
       'decided_by': 'CMT (người dùng phiên Claude Code): "Đã xem và mình xác nhận"',
       'note': 'Dòng silver 8b73b0357750 để trống, giữ nhãn AI khong_dat. Xác nhận qua hội thoại, thời gian từng dòng không đo.',
       'xlsx_sha256': {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in (S, L)},
       'silver_flips': flips, 'silver_dat': silver, 'lo2_dat': lo2}
Path(__file__).with_name('cmt_confirmed.json').write_text(json.dumps(out, ensure_ascii=False, indent=1) + '\n')
print(len(silver), len(lo2), flips)

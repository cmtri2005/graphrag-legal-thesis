#!/usr/bin/env python3
"""So nhãn AI-A vs AI-B (gold đợt 3, 23 dòng repealed) và reveal vs đáp án kho.
Dùng: python3 compare_ai.py ai_a.tsv ai_b.tsv [key_map_29.private.tsv]
In: đồng thuận hieu_luc, danh sách lệch A/B (cho adjudicator), và chỗ AI khác kho.
ponytail: so trường hieu_luc là chính; các trường khác chỉ liệt kê khi lệch.
"""
import csv, sys, os

def load(p):
    with open(p, newline='') as f:
        return {r['key']: r for r in csv.DictReader(f, delimiter='\t')}

def norm(v):  # Còn/Hết -> True(còn hiệu lực)/False
    v = (v or '').strip().lower()
    if v.startswith('còn') or v.startswith('con'): return True
    if v.startswith('hết') or v.startswith('het'): return False
    return None

def main():
    a, b = load(sys.argv[1]), load(sys.argv[2])
    km_path = sys.argv[3] if len(sys.argv) > 3 else os.path.join(os.path.dirname(__file__), 'key_map_29.private.tsv')
    km = load(km_path)
    keys = [k for k in km if km[k]['group'] == 'repealed']
    assert keys, 'không có dòng repealed trong key_map'

    agree = disagree = both = 0
    ab_conflict, store_catch = [], []
    for k in keys:
        if k not in a or k not in b:
            print(f'THIẾU nhãn: {k} (A={k in a} B={k in b})'); continue
        both += 1
        va, vb = norm(a[k]['hieu_luc']), norm(b[k]['hieu_luc'])
        store_inforce = km[k]['store_in_force'].strip().lower() == 'true'  # repealed => False
        if va == vb:
            agree += 1
            # cả hai đồng thuận nhưng khác kho (kho nói Hết/không đáp án, AI nói Còn) => nghi sót-sửa-đổi
            if va is True and not store_inforce:
                store_catch.append((k, 'A&B nói CÒN hiệu lực, kho nói không đáp án', a[k], b[k]))
        else:
            disagree += 1
            ab_conflict.append((k, va, vb))

    print(f'== 23 dòng repealed: cả hai gán {both}/{len(keys)} ==')
    print(f'Đồng thuận hieu_luc: {agree}/{both}'
          + (f'  (AC-raw={agree/both:.3f})' if both else ''))
    print(f'Lệch A/B: {disagree}  -> adjudicator xử')
    for k, va, vb in ab_conflict:
        print(f'  {k}: A={va} B={vb} | A.nguon={a[k].get("nguon","")[:60]} | B.nguon={b[k].get("nguon","")[:60]}')
    print(f'\nNghi KHO SAI (A&B thống nhất CÒN, kho không đáp án): {len(store_catch)}')
    for k, why, ra, rb in store_catch:
        print(f'  {k}: {why} | A.dap_an={ra.get("dap_an","")[:50]}')

if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""Reproduce G2 counts and pre-adjudication agreement without changing labels.

Run from repository root. Historical runs remain separate; no test inference.
"""
from __future__ import annotations
import collections
import csv
import hashlib
import json
from math import sqrt
from pathlib import Path
from statistics import NormalDist
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'review'))
from ai_labels import load_inputs, read_labels, metric
from crosscheck import gwet_ac1, specific_agreement

BASE = Path('data/review/ai_research')
OUT = Path('docs/reports/g2-co-mau-dong-thuan-20261109.md')
INPUTS = {}


def sha(p):
    digest = hashlib.sha256(p.read_bytes()).hexdigest()
    INPUTS[str(p)] = digest
    return digest


def rows(p):
    sha(p)
    return [json.loads(line) for line in p.read_text().splitlines() if line.strip()]


def dataset_check():
    p = Path('data/vilextime_dataset/manifest.json')
    m = json.loads(p.read_text()); sha(p)
    counts = {}
    for kind, name in [('main', 'vilextime.jsonl'), ('silver', 'vilextime_silver.jsonl')]:
        rr = rows(p.parent / name)
        assert len(rr) == m['rows'][kind]
        c = collections.Counter(f"{r['group']} · {r['as_of_strategy']} · {r['split']}" for r in rr)
        assert dict(c) == m[f'counts_{kind}']
        counts[kind] = {'rows': len(rr), 'lineages': len({r['lineage_id'] for r in rr})}
    for name, digest in m['sha256'].items():
        assert sha(p.parent / name) == digest, name
    return m, counts


def paired(run):
    rec = load_inputs(run)
    for p in sorted((run / 'input').glob('chunk*.jsonl')):
        sha(p)
    labels = {}
    rejected = {}
    for who in ('a', 'b'):
        sha(run / f'{who}.jsonl')
        labels[who], rejected[who] = read_labels(run / f'{who}.jsonl', who, rec)
    ids = sorted(labels['a'].keys() & labels['b'].keys())
    # Reject bad input visibly. Never silently remove it from agreement.
    assert not any(rejected.values()), (str(run), rejected)
    ms = {q: metric([labels['a'][i][q] for i in ids], [labels['b'][i][q] for i in ids], q)
          for q in ('q1', 'q2', 'q3', 'q4', 'verdict')}
    return rec, labels, ids, ms


def power(n):
    # Same cluster sandwich estimator as scripts/paper/paper_values.py.
    rr = [r for r in rows(Path('data/vilextime/test2_release_v2.jsonl'))
          if r['as_of_strategy'] == 'giua_khoang' and r['answerable'] and r['group'] != 'T5']
    pred = {s: {r['id']: r for r in rows(Path(f'runs/E1_test2/test/{s}.jsonl'))}
            for s in ('b7', 'b7pp')}
    clusters = collections.defaultdict(lambda: [0, 0])
    for r in rr:
        accepted = set(r['accepted_evidence']) | {r['version_id']}
        hits = {s: bool(pred[s][r['id']].get('retrieved', [])[:1]
                        and pred[s][r['id']]['retrieved'][0] in accepted) for s in pred}
        clusters[r['lineage_id']][0] += int(hits['b7pp']) - int(hits['b7'])
        clusters[r['lineage_id']][1] += 1
    size = len(clusters); count = len(rr)
    delta = sum(d for d, k in clusters.values()) / count
    se = sqrt(size / (size - 1) * sum((d - delta*k)**2 for d, k in clusters.values())) / count
    projected = se * sqrt(size / n)
    normal = NormalDist()
    def at(alpha):
        z = normal.inv_cdf(1-alpha/2); shift = delta/projected
        return normal.cdf(-z-shift) + 1-normal.cdf(z-shift)
    return {'n': n, 'historical_lineages': size, 'historical_rows': count,
            'delta': delta, 'historical_se': se, 'projected_se': projected,
            'power_alpha_05': at(.05), 'power_alpha_05_div_6': at(.05/6),
            'mde80_alpha_05': (normal.inv_cdf(.975)+normal.inv_cdf(.8))*projected}


def main():
    m, counts = dataset_check()
    snaps = BASE / '2026-11-07_adjudication_all/snapshots'
    runs = {p.name: p for p in sorted(snaps.iterdir()) if (p / 'a.jsonl').exists()}
    # Use originals when available; snapshot only for otherwise absent frozen rounds.
    runs.update({k: BASE / f'2026-11-06_silver/{k}'
                 for k in ('round2_claude', 'round2_codex', 'round3_mixed')})
    runs['pilot0'] = BASE / '2026-11-06_lo0'
    # Accepted normalization retains Q labels, repairs schema/binding only.
    runs['lo2'] = BASE / '2026-11-08_lo2/schema_validated'
    runs['supp18'] = BASE / '2026-11-08_supp18'
    results = {name: paired(p) for name, p in runs.items()}
    all_ids = set().union(*(set(v[2]) for v in results.values()))
    prod_names = ['silver01', 'round2_codex', 'round3_mixed', 'lo2', 'supp18']
    prod_ids = set()
    for name in prod_names:
        ids = set(results[name][2]); assert not prod_ids & ids, name
        prod_ids.update(ids)
    pooled = {q: metric([results[name][1]['a'][i][q] for name in prod_names for i in results[name][2]],
                        [results[name][1]['b'][i][q] for name in prod_names for i in results[name][2]], q)
              for q in ('q1', 'q2', 'q3', 'q4', 'verdict')}
    approvals = {}
    accepted = set()
    for name, folder in [('silver', '2026-11-08_adjudication_final'),
                         ('lo2', '2026-11-08_lo2'), ('supp18', '2026-11-08_supp18')]:
        p = BASE / folder
        approval = json.loads((p / 'cmt_acceptance.json').read_text()); sha(p / 'cmt_acceptance.json')
        scope = approval['scope']; label_path = p / scope['file']
        assert sha(label_path) == scope['sha256'], label_path
        rr = rows(label_path)
        good = {r['lineage_id'] for r in rr if r.get('label', r)['verdict'] == 'dat'}
        assert len(good) == scope['dat']
        assert not accepted & good
        accepted.update(good)
        approvals[name] = {'resolved_approved': len(rr), 'dat': len(good),
                           'quality_tier': approval['quality_tier'], 'method': approval['method']}
    assert len(accepted) == 162
    pw = [power(n) for n in (81, 130, len(accepted), len(prod_ids))]
    lines = ['# G2: cỡ mẫu và đồng thuận, 09/11/2026', '',
             'Trạng thái: tái lập phép tính; chưa xác nhận cổng G2 đạt.', '',
             'Lệnh: `PYTHONPATH=src .venv/bin/python scripts/check/audit_g2_statistics.py`.',
             'Script chỉ đọc dữ liệu/nhãn; ghi báo cáo này và JSON kèm hash đầu vào.', '',
             '## Manifest và cỡ mẫu', '',
             f"Main: {counts['main']['rows']} dòng/{counts['main']['lineages']} lineage. "
             f"Silver: {counts['silver']['rows']} dòng/{counts['silver']['lineages']} lineage. "
             'Số đếm từng ô và 5 hash file phát hành khớp manifest; không sửa manifest.', '',
             f'Toàn bộ lượt AI gán đôi được kiểm: {sum(len(v[2]) for v in results.values())} '
             f'cặp lượt gán/{len(all_ids)} lineage riêng biệt. Không đếm snapshot trùng lần hai.',
             f'Phần sản xuất không trùng lineage: **{len(prod_ids)} lineage** = silver 168 + lo2 128 + supp18 18. '
             'Không tính các lượt gán lại hoặc pilot thành mẫu nghiên cứu mới.', '',
             '| Nguồn duyệt CMT | Kết luận được nhận | Đạt | Tầng |',
             '|---|---:|---:|---|']
    for name, a in approvals.items():
        lines.append(f"| {name} | {a['resolved_approved']} | {a['dat']} | {a['quality_tier']} |")
    lines += ['', '**162 lineage đạt được chấp nhận**, vượt 130 là 32. Trong đó **81 silver chỉ được '
              'chấp nhận hàng loạt**; receipt ghi rõ không kiểm từng dòng. **81 lineage mới đạt** '
              '(lo2 69 + supp18 12) có lời CMT tự báo đã đọc xong và duyệt. Nếu yêu cầu '
              '130 lineage người xác nhận sau đọc, chỉ chứng minh được 81, còn thiếu **49**. '
              'Không có bằng chứng hai người độc lập kiểm bộ cuối. Không gọi 162 là 162 '
              'lineage người kiểm từng dòng. Không suy lịch sử đọc từng ô từ lời duyệt qua hội thoại.',
              'Có 23 ca mới unresolved, giữ ngoài nhãn cuối. Không đưa 314 cặp AI vào cỡ mẫu '
              'đã đạt và không coi 162 là dataset test đã phát hành.', '',
              '## AC1 và p_neg trước hòa giải', '',
              'Dùng hàm native `ai_labels.metric`, giữ mọi nhãn hợp lệ kể cả thiếu nguồn. '
              'Mỗi ô là AC1 / p_neg. Nhãn âm: Q1≠dung, Q2/Q3≠co, Q4≠khong; '
              'verdict=khong_dat. Không dùng nhãn hòa giải để tăng đồng thuận.', '',
              '| Lượt | N cặp | Q1 | Q2 | Q3 | Q4 | Verdict |',
              '|---|---:|---|---|---|---|---|']
    fmt = lambda x: 'NA' if x is None else f'{x:.6f}'
    for name, (_, _, ids, ms) in results.items():
        lines.append(f'| {name} | {len(ids)} | ' + ' | '.join(
            f"{fmt(ms[q]['ac1'])} / {fmt(ms[q]['p_neg'])}" for q in pooled) + ' |')
    lines += ['', '**Gộp mô tả toàn bộ 314 lineage sản xuất**, gồm lo2 128. Không trộn các '
              'lượt gán lại của cùng lineage. Model khác nhau giữa các lô; số gộp không '
              'thay cổng từng lô và không phải đồng thuận người–người.', '',
              '| Chỉ số | N | AC1 | p_neg | Nhãn âm (hai bên) | Cổng native |',
              '|---|---:|---:|---:|---:|---|']
    for q, v in pooled.items():
        lines.append(f"| {q} | {v['n']} | {fmt(v['ac1'])} | {fmt(v['p_neg'])} | {v['adverse_labels']} | {v['gate']} |")
    # Preserve historical human provenance and guideline separation.
    lines += ['', '## Phần gán đôi lịch sử, tách khỏi bộ cuối', '',
              '| Bộ/hướng dẫn | N dòng | AC1 verdict | p_neg verdict |',
              '|---|---:|---:|---:|']
    for stem in ('crosscheck', 'kiem', 'pilot_T6'):
        paths = [Path(f'data/review/{stem}_{w}.tsv') for w in 'AB']
        if not all(p.exists() for p in paths): continue
        sides = []
        for p in paths:
            sha(p); sides.append({r['id']: r for r in csv.DictReader(p.open(), delimiter='\t')})
        a, b = sides
        groups = collections.defaultdict(list)
        for i in sorted(a.keys() & b.keys()):
            if not a[i].get('verdict') or not b[i].get('verdict'): continue
            va, vb = (s[i].get('guideline_version') or '1.2' for s in sides)
            if stem == 'kiem' and (va != '3.0' or vb != '3.0'): continue
            key = va if va == vb else f'mixed({va}/{vb})'
            if a[i].get('lo') == '0': key += ' calibration'
            groups[key].append(i)
        for key, ids in groups.items():
            aa, bb = [[s[i]['verdict'] for i in ids] for s in sides]
            lines.append(f'| {stem}/{key} | {len(ids)} | {fmt(gwet_ac1(aa,bb))} | '
                         f"{fmt(specific_agreement(aa,bb).get('khong_dat'))} |")
    # Test2 is a separate AI round, never part of final sample.
    sides = []
    for w in 'AB':
        p = Path(f'data/review/test2_llm/test2_LLM_{w}.tsv'); sha(p)
        sides.append({r['lineage_id']: r for r in csv.DictReader(p.open(), delimiter='\t')})
    ids = sorted(i for i in sides[0].keys() & sides[1].keys()
                 if sides[0][i].get('verdict') and sides[1][i].get('verdict'))
    lines += ['', f'Test2 AI–AI riêng: {len(ids)} lineage.']
    test2 = {q: metric([sides[0][i][q] for i in ids], [sides[1][i][q] for i in ids], q) for q in pooled}
    for q, v in test2.items():
        lines.append(f"- {q}: AC1 {fmt(v['ac1'])}, p_neg {fmt(v['p_neg'])}.")
    lines += ['', 'Manifest hướng dẫn 3.0: 246 dòng người–người, AC1 0,377277; '
              'p_neg 0,394558. Theo 138 lineage: AC1 0,389639; p_neg 0,483516. '
              'Không gộp hướng dẫn cũ và mới. Các bảng lịch sử chồng dòng với nhau, không cộng N.', '',
              '## Power tại cỡ mẫu thật', '',
              'Bộ cuối chưa có dự đoán nên **không có power thực nghiệm của bộ cuối**. '
              'Bảng dưới là phân tích độ nhạy tại N thật. Giữ hiệu và phương sai cụm '
              'từ E1 test2 đã có; không chạy hay tinh chỉnh hệ trên test. Công thức cùng '
              '`scripts/paper/paper_values.py`: delta là tỷ số tổng chênh hit/tổng dòng; '
              'SE sandwich theo lineage; SE(N)=SE(cũ)√(101/N). Power chuẩn hai phía '
              '= Φ(−z−delta/SE(N))+1−Φ(z−delta/SE(N)).', '',
              f"Nguồn lịch sử: {pw[0]['historical_rows']} dòng/{pw[0]['historical_lineages']} lineage; "
              f"delta={pw[0]['delta']:.9f}, SE={pw[0]['historical_se']:.9f}.", '',
              '| N lineage | Ý nghĩa | Power α=0,05 | Power α=0,05/6 | MDE 80%, α=0,05 |',
              '|---|---|---:|---:|---:|']
    for v, meaning in zip(pw, ['mới đạt, CMT tự báo đọc', 'ngưỡng G2', 'gồm silver nhận hàng loạt', 'toàn bộ AI sản xuất, chưa lọc chất lượng']):
        lines.append(f"| {v['n']} | {meaning} | {v['power_alpha_05']:.6f} | {v['power_alpha_05_div_6']:.6f} | {v['mde80_alpha_05']:.6f} |")
    lines += ['', 'α/6 là ngưỡng đầu Holm bảo thủ cho sáu phép lịch sử ADR 0005. '
              'Không phải power sau Holm duy nhất và không khóa họ cho bộ cuối. '
              'N=314 chỉ minh họa hậu quả đếm nhầm mọi nhãn AI thành mẫu đạt. '
              'Không phải cỡ mẫu hợp lệ để kết luận. Công thức MDE dùng xấp xỉ z; '
              'cần giả định phân bố/số dòng mỗi lineage tương tự test2. Không suy power '
              'cho Accuracy hoặc TVER từ phương sai TV-Recall.', '',
              '## Giới hạn và việc cần chốt', '',
              'Rà 11/11 dạng sai suy luận theo skill: Simpson và base rate được xử lý bằng '
              'bảng từng lô và số nhãn âm; sinh thái, chọn mẫu và survivorship bằng tách '
              'lineage/lượt, giữ nhãn thiếu nguồn; không có mô hình điều chỉnh collider. '
              'Không suy cải thiện trước/sau từ các lô khác nhau (regression to mean). '
              'Báo mọi Q và mọi lô, giữ ngưỡng/họ (look-elsewhere, forking paths). '
              'Không kết luận nhân quả hoặc chiều nhân quả từ IAA. Phân tích power '
              'có điều kiện và sau quan sát, không phải đăng ký trước.', '',
              'Cần CMT xác nhận cách công bố ngưỡng 130: 162 được chấp nhận theo master '
              'plan, nhưng chỉ 81 mới có lời tự báo đã đọc; silver receipt cấm gọi là '
              'người kiểm từng dòng. Báo cả hai, không tự miễn cổng. M2/gold mù và '
              'phân xử các ca mở vẫn cần người có thẩm quyền. Không sửa nhãn người.', '']
    OUT.write_text('\n'.join(lines), encoding='utf-8')
    detail = {'counts': counts, 'round_metrics': {k: v[3] for k,v in results.items()},
              'production_lineages': len(prod_ids), 'production_metrics': pooled,
              'approvals': approvals, 'accepted_dat_lineages': len(accepted),
              'power_sensitivity': pw, 'input_sha256': INPUTS}
    OUT.with_suffix('.json').write_text(json.dumps(detail,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'manifest': counts, 'production_paired': len(prod_ids),
                      'accepted_dat': len(accepted), 'pooled': pooled, 'power': pw},ensure_ascii=False))


if __name__ == '__main__':
    main()

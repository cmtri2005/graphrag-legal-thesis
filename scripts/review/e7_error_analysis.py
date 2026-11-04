#!/usr/bin/env python3
"""E7, exploratory machine classification; no model calls or retrieval.

Only test/giua_khoang, separately for v1.0 and test 2. Use the official scorer
for correctness, TV-Recall@1/@20 and wrong_version. Priority on incorrect rows:
ABST (answerable=False disagrees with gold), RET-UNIT (no accepted evidence or
resolved gold provision in the prompt), RET-VER-OLD / RET-VER-NEW (gold provision
but no accepted gold unit; ordinal relative to gold), GEN-BLANK, GEN-MISREAD.
ABST means the stored answerable flag, not the literal word 'không' in legal text.
Within RET-VER, OLD precedes NEW if the prompt has both directions but no gold;
count those mixed cases separately. Evidence presence uses the full stored
retrieved list (graph expansion may exceed 20); TV-Recall@20 uses only its prefix.
GEN-MISREAD/wrong_version is a subset, never an extra error in the total.

report: write the two separate descriptive sections.
sample: at most 20 errors/system/group, seed vilextime-e7-0411; blind human TSV
and separate machine TSV. Mark the first 30 sampled records for double coding.
"""
from __future__ import annotations

import argparse
import collections
import csv
import json
import random
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'eval'))
from score_vilextime import (  # noqa: E402
    correct, distractors, load_rows, ordinal, row_scores, spans, units_of,
)

SYSTEMS = ('b1', 'b2ctx', 'b5', 'b7', 'b7pp', 'proposed')
SAMPLE_SYSTEMS = ('proposed', 'b7', 'b2ctx', 'b1')
LAYERS = ('ABST', 'RET-UNIT', 'RET-VER-OLD', 'RET-VER-NEW', 'GEN-BLANK', 'GEN-MISREAD')
SEED = 'vilextime-e7-0411'
DATASETS = (
    ('v1', Path('data/vilextime_dataset/vilextime.jsonl'), Path('runs/E3_v1/test')),
    ('test2', Path('data/vilextime/test2_release_v2.jsonl'), Path('runs/E3_test2/test')),
)


def classify(row: dict, pred: dict, units: dict) -> dict:
    prompt_k = max(1, len(pred.get('retrieved') or []))
    metrics = row_scores(row, pred, units, ks=tuple(sorted({1, 20, prompt_k})))
    right = correct(row, pred)
    result = {'correct': right, 'layer': '', 'wrong_version': bool(metrics['wrong_version']),
              'tv1': bool(metrics['tv_recall@1']), 'tv20': bool(metrics['tv_recall@20']),
              'gold_in_prompt': bool(metrics[f'tv_recall@{prompt_k}']),
              'mixed_direction': False, 'resolved_gold_without_accepted_id': False}
    if right:
        return result
    if (row['answerable'] and pred.get('answerable') is False) or (
            not row['answerable'] and pred.get('answerable') is not False):
        result['layer'] = 'ABST'
    elif not metrics[f'recall@{prompt_k}']:
        result['layer'] = 'RET-UNIT'
    elif not result['gold_in_prompt']:
        gold = ordinal(row['version_id'])
        ns = {n for u in (pred.get('retrieved') or [])
              for pid, n, _ in units.get(u, ()) if pid == row['lineage_id'] and isinstance(n, int)}
        old, new = any(n < gold for n in ns), any(n > gold for n in ns)
        result['mixed_direction'] = old and new
        result['resolved_gold_without_accepted_id'] = gold in ns
        assert gold not in ns, f"Gold ordinal without accepted ID: {row['id']}"
        assert old or new, (row['id'], ns, gold)
        result['layer'] = 'RET-VER-OLD' if old else 'RET-VER-NEW'
    elif not (pred.get('answer') or '').strip():
        result['layer'] = 'GEN-BLANK'
    else:
        result['layer'] = 'GEN-MISREAD'
    assert result['layer'] in LAYERS
    return result


def analyze(release: Path, generation: Path, data: Path) -> list[dict]:
    release_rows = load_rows(release)
    extra = distractors(release_rows)  # Same full-release distractors as score/confirm.
    rows = [{**r, '_distractors': extra.get(r['id'], [])} for r in release_rows
            if r.get('split') == 'test' and r['as_of_strategy'] == 'giua_khoang']
    assert rows and all(not r['answerable'] or spans(r.get('short_answer') or '') for r in rows)
    runs = {}
    for system in SYSTEMS:
        predictions = [json.loads(line) for line in (generation / f'{system}.jsonl').open(encoding='utf-8')]
        runs[system] = {p['id']: p for p in predictions}
        assert len(runs[system]) == len(predictions), f'{system}: duplicate prediction IDs'
        assert {r['id'] for r in rows} <= runs[system].keys(), f'{system}: missing predictions'
    units = units_of(data, runs)[0]  # resolve() is owned by the scorer; one scan per dataset.
    return [{'system': s, 'row': r, 'pred': runs[s][r['id']],
             **classify(r, runs[s][r['id']], units)} for s in SYSTEMS for r in rows]


def summarize(records: list[dict]) -> dict:
    counts = collections.Counter(r['layer'] for r in records if not r['correct'])
    errors = sum(not r['correct'] for r in records)
    assert sum(counts.values()) == errors
    assert set(counts) <= set(LAYERS)
    gold = [r for r in records if r['gold_in_prompt']]
    return {'n': len(records), 'errors': errors, 'counts': counts, 'gold_n': len(gold),
            'gold_correct': sum(r['correct'] for r in gold),
            'tv1': sum(r['tv1'] for r in records), 'tv20': sum(r['tv20'] for r in records),
            'wrong': sum(r['layer'] == 'GEN-MISREAD' and r['wrong_version'] for r in records),
            'mixed': sum(r['mixed_direction'] for r in records),
            'resolved_gold': sum(r['resolved_gold_without_accepted_id'] for r in records)}


def ratio(n: int, d: int) -> str:
    return f'{n}/{d} ({n/d:.3f})' if d else '0/0 (không xác định)'


def section(name: str, records: list[dict], release: Path, generation: Path) -> list[str]:
    lines = [f'## {"v1.0" if name == "v1" else "Test 2 — nhãn LLM, không phải người"}', '',
             f'Nguồn: `{release}`, `{generation}`; split `test`, lát `giua_khoang`.', '',
             '| Hệ | Nhóm | N | Sai | ' + ' | '.join(LAYERS) + ' | MISREAD chứa bản khác |',
             '|---|---|---:|---:|' + '---:|' * (len(LAYERS) + 1)]
    groups = ['all', *sorted({r['row']['group'] for r in records})]
    for system in SYSTEMS:
        for group in groups:
            cut = [r for r in records if r['system'] == system and
                   (r['row']['group'] != 'T5' if group == 'all' else r['row']['group'] == group)]
            s = summarize(cut)
            lines.append(f'| {system} | {group} | {s["n"]} | {s["errors"]} | ' +
                         ' | '.join(str(s['counts'][k]) for k in LAYERS) + f' | {s["wrong"]} |')
    lines += ['', 'Căn cứ đúng trong prompt = TV-hit trong toàn bộ `retrieved` đã lưu, theo scorer. Mở rộng đồ thị có thể đưa thêm căn cứ sau vị trí 20; TV-Recall@20 vẫn chỉ xét 20 vị trí đầu. '
              'Mẫu số tỷ lệ đúng có căn cứ gồm cả dòng bãi bỏ; thêm cột chỉ dòng có đáp án.', '',
              '| Hệ | Nhóm | TV-Recall@1 | TV-Recall@20 | Đúng khi có căn cứ | Chỉ dòng có đáp án |',
              '|---|---|---|---|---|---|']
    for system in SYSTEMS:
        for group in groups:
            cut = [r for r in records if r['system'] == system and
                   (r['row']['group'] != 'T5' if group == 'all' else r['row']['group'] == group)]
            s = summarize(cut)
            a = summarize([r for r in cut if r['row']['answerable']])
            lines.append(f'| {system} | {group} | {ratio(s["tv1"], s["n"])} | '
                         f'{ratio(s["tv20"], s["n"])} | {ratio(s["gold_correct"], s["gold_n"])} | '
                         f'{ratio(a["gold_correct"], a["gold_n"])} |')
    s = summarize(records)
    lines += ['', f'Ca biên trên các hệ (đếm lượt hệ × dòng): cả hướng cũ và mới {s["mixed"]}; '
              f'resolve có ordinal gold nhưng thiếu ID được chấp nhận {s["resolved_gold"]}.', '']
    return lines


def sample_errors(records: list[dict]) -> list[dict]:
    rng = random.Random(SEED)
    sampled = []
    for system in SAMPLE_SYSTEMS:
        for group in sorted({r['row']['group'] for r in records}):
            cell = sorted([r for r in records if r['system'] == system and
                           r['row']['group'] == group and not r['correct']], key=lambda r: r['row']['id'])
            sampled.extend(rng.sample(cell, min(20, len(cell))))
    rng.shuffle(sampled)  # Spread the first 30 across cells instead of the first system/group.
    assert len({(r['system'], r['row']['id']) for r in sampled}) == len(sampled)
    return sampled


def write_sheets(name: str, records: list[dict], dest: Path, data: Path) -> None:
    sampled = sample_errors(records)
    dest.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(f'file:{data / "derived/corpus/index.sqlite"}?mode=ro&immutable=1', uri=True)
    def evidence(ids):
        # Exact ID lookup of existing corpus text, no search/reranking/model calls.
        found = []
        for uid in ids:
            hit = db.execute('SELECT text FROM units WHERE unit_id=?', (uid,)).fetchone()
            found.append({'id': uid, 'text': hit[0] if hit else None})
        return json.dumps(found, ensure_ascii=False)
    human = dest / f'phieu_{name}.tsv'
    machine = dest / f'phieu_{name}_may.tsv'
    with human.open('w', encoding='utf-8', newline='') as h, machine.open('w', encoding='utf-8', newline='') as m:
        hw, mw = csv.writer(h, delimiter='\t'), csv.writer(m, delimiter='\t')
        hw.writerow(['stt', 'cung_ma_hoa_30', 'nhom', 'id', 'lineage_id', 'cau_hoi', 'moc',
                     'co_dap_an', 'dap_an_vang', 'dap_an_ngan', 'tra_loi', 'answerable_du_doan',
                     'can_cu_trich', 'can_cu_prompt', 'ma_loi_A', 'ghi_chu_A', 'ma_loi_B', 'ghi_chu_B'])
        mw.writerow(['stt', 'he', 'nhom', 'id', 'tang_may', 'wrong_version',
                     'mixed_direction', 'resolved_gold_without_accepted_id'])
        for i, r in enumerate(sampled, 1):
            row, pred = r['row'], r['pred']
            hw.writerow([i, 'co' if i <= 30 else '', row['group'], row['id'], row['lineage_id'],
                         row['question'], row['as_of'], row['answerable'], row['answer'], row['short_answer'],
                         pred.get('answer'), pred.get('answerable'), evidence(pred.get('citations') or []),
                         evidence(pred.get('retrieved') or []), '', '', '', ''])
            mw.writerow([i, r['system'], row['group'], row['id'], r['layer'], r['wrong_version'],
                         r['mixed_direction'], r['resolved_gold_without_accepted_id']])
    db.close()
    print(f'{human}: {len(sampled)} errors; first {min(30, len(sampled))} double-coded; {machine}')


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--data', type=Path, default=Path('data'))
    sub = ap.add_subparsers(dest='command', required=True)
    report = sub.add_parser('report')
    report.add_argument('--out', type=Path, default=Path('docs/reports/e7_phan_ra_loi.md'))
    sample = sub.add_parser('sample')
    sample.add_argument('--out-dir', type=Path, default=Path('data/review/e7'))
    args = ap.parse_args()
    lines = ['# E7 — Phân rã lỗi theo tầng', '',
             '> **thăm dò, do máy phân loại, chưa có người kiểm**. Test 2 dùng nhãn LLM, không phải người.', '',
             'Ưu tiên: ABST → RET-UNIT → RET-VER-OLD / RET-VER-NEW → GEN-BLANK → GEN-MISREAD. '
             'ABST dùng `answerable=False`, không tìm từ “không” trong lời văn. '
             'RET-UNIT là thiếu điều khoản; RET-VER là có điều khoản nhưng thiếu bằng chứng gold. '
             'Trong RET-VER, OLD ưu tiên trước NEW nếu có cả hai hướng; số ca trộn được báo riêng. '
             'Các tổng tầng chỉ gồm dòng sai; `wrong_version` là tập con của GEN-MISREAD.', '',
             'Bảng tần suất dùng toàn bộ dòng sai, không phải mẫu phiếu. '
             '`b1` không truy xuất theo thiết kế nên RET-UNIT ở hệ này chỉ mô tả thiếu căn cứ trong prompt, '
             'không phải lỗi triển khai truy xuất. Phân loại ưu tiên không khẳng định nguyên nhân nhân quả.', '',
             'Đối chiếu mô tả với oracle context dev **0,854** (129/151, '
             '`runs/B2_dev/dev/all.score.json`, `oracle`, `giua_khoang/all`). '
             'Khác split, nhóm và số căn cứ; tỷ lệ có điều kiện dưới đây không phải phép so sánh ghép cặp '
             'hay bằng chứng vượt oracle. Không thêm kiểm định hoặc đổi chỉ số.', '',
             'Tái lập tuần tự: `.venv/bin/python scripts/review/e7_error_analysis.py report`; '
             '`.venv/bin/python scripts/review/e7_error_analysis.py sample`. '
             f'Phiếu lấy tối đa 20 lỗi/hệ × nhóm, seed `{SEED}`. '
             'Theo MASTER_RESEARCH_GUIDE §9.4, người gán dùng RET-UNIT, RET-VER-OLD, RET-VER-NEW, FUT, '
             'REP-DIRECT, REP-ANCESTOR, GEN-HEDGE, GEN-MISREAD, ABST-WRONG, CITE, GOLD, QUESTION; '
             '30 dòng đầu mỗi phiếu cần hai người mã hóa độc lập. Chỉ gửi `phieu_*.tsv` không có hậu tố '
             '`_may` cho người gán; các cột mã và ghi chú A/B để trống.', '']
    for name, release, generation in DATASETS:  # Sequential: the workstation has 7 GB RAM.
        records = analyze(release, generation, args.data)
        if args.command == 'report':
            lines += section(name, records, release, generation)
        else:
            write_sheets(name, records, args.out_dir, args.data)
    if args.command == 'report':
        args.out.write_text('\n'.join(lines), encoding='utf-8')
        print(f'-> {args.out}')


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""Close the 6 open adjudications of 07/11 and build the AI-final silver labels + one CMT review workbook.

Run from the repo root:  .venv/bin/python data/review/ai_research/2026-11-08_adjudication_final/build_final.py
Validation reuses the 07/11 native validator on (07/11 results with the 6 cases replaced).
Nothing here is a human label: every row stays label_origin=ai, verification_status=not_verified.
"""
import json, os, sys, tempfile, hashlib
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
OLD = HERE.parent / '2026-11-07_adjudication_all'
SILVER_INPUT = HERE.parent / '2026-11-06_silver/input'
sys.path.insert(0, str(OLD))
import package_review as pr  # noqa: E402  (also puts scripts/review on sys.path)

SILVER_RUNS = ['silver01', 'round2_claude', 'round2_codex', 'round3_mixed']
QF = ('q1', 'q2', 'q3', 'q4', 'verdict')


def merged_results():
    new = {r['case_id']: r for r in pr.read_jsonl(HERE / 'results.jsonl')}
    inputs = {r['case_id']: r for p in (OLD / 'input').glob('*.jsonl') for r in pr.read_jsonl(p)}
    rows = []
    for p in sorted((OLD / 'results').glob('*.jsonl')):
        for r in pr.read_jsonl(p):
            if r['case_id'] in new:
                n = dict(new.pop(r['case_id']))
                assert r['disposition'] == 'unresolved', f"{r['case_id']}: only unresolved cases may be replaced"
                for k in ('worksheet_sha256', 'disputed_fields'):
                    n[k] = inputs[r['case_id']][k]  # binding comes from the frozen input
                r = n
            rows.append(r)
    assert not new, f'unknown case ids: {list(new)}'
    tmp = Path(tempfile.mkdtemp())
    (tmp / 'results').mkdir()
    for n in ('scope.json', 'input', 'snapshots'):
        os.symlink(OLD / n, tmp / n)
    pr.jsonl(tmp / 'results/all.jsonl', rows)
    pr.HERE = tmp
    _, _, outputs = pr.load_validate()  # raises on any binding/schema/consistency error
    return outputs


def final_labels(outputs):
    labs = defaultdict(list)
    for run in SILVER_RUNS:
        for side in 'ab':
            for x in pr.read_jsonl(OLD / 'snapshots' / run / f'{side}.jsonl'):
                labs[x['lineage_id']].append((run, side, x))
    adj = defaultdict(list)
    for o in outputs.values():
        adj[o['lineage_id']].append(o)
    records = {}
    for p in sorted(SILVER_INPUT.glob('chunk*.jsonl')):
        for x in pr.read_jsonl(p):
            records[x['record']['lineage_id']] = x['record']
    out = []
    for lid, L in labs.items():
        sigs = {tuple(x.get(f) for f in QF) for _, _, x in L}
        if len(sigs) == 1:
            src, lab, cases = 'ai_agree', L[0][2], []
        else:
            A = [o for o in adj.get(lid, []) if o['disposition'] != 'unresolved']
            assert A, f'{lid}: AI labels disagree but no adjudication'
            psig = {tuple(o['proposed_label'][f] for f in QF) for o in A}
            assert len(psig) == 1, f'{lid}: adjudications disagree across runs {psig}'
            src, lab, cases = 'ai_adjudicated', A[-1]['proposed_label'], A
        out.append({
            'lineage_id': lid, 'group': records[lid]['group'], 'stratum': records[lid].get('stratum'),
            'question': records[lid]['question'], 'rows': records[lid]['rows'],
            **{k: lab.get(k) for k in pr.LABEL_KEYS}, 'verdict': lab['verdict'],
            'note': lab.get('note', ''), 'source': src,
            'adjudications': [{'case_id': o['case_id'], 'disposition': o['disposition'],
                               'open_questions': o['open_questions']} for o in cases],
            'n_ai_labels': len(L), 'label_origin': 'ai', 'verification_status': 'not_verified',
        })
    assert len(out) == len(records) == 168, (len(out), len(records))
    return out


def workbook(rows, path):
    from openpyxl import Workbook
    from openpyxl.styles import PatternFill, Alignment
    wb = Workbook()
    ws = wb.active
    ws.title = 'Đọc trước'
    for line in [
        'Phiếu duyệt cuối silver ViLexTime, 168 lineage. Nhãn trong phiếu là nhãn AI (chưa kiểm).',
        'Cột xanh do CMT điền: cmt_dong_y = "x" nếu đồng ý toàn bộ nhãn; nếu sửa thì ghi Q cần sửa và lý do ở cmt_sua.',
        'Thứ tự: (1) ca AI hòa giải hoặc có [phân vân]; (2) đạt (vào bộ test); (3) không đạt mà hai AI đồng ý.',
        'Dòng "đạt" là dòng sẽ vào bộ test, nên ưu tiên xem kỹ. Dòng "không đạt" chỉ cần xem lướt lý do.',
        'Không sửa các cột xám. Không ai ký thay CMT.',
    ]:
        ws.append([line])
    ws.column_dimensions['A'].width = 120
    d = wb.create_sheet('Duyệt')
    cols = ['thu_tu', 'lineage_id', 'group', 'question', 'cac_moc_va_dap_an', 'source', 'verdict',
            *pr.LABEL_KEYS, 'note', 'cau_hoi_mo', 'cmt_dong_y', 'cmt_sua', 'cmt_ghi_chu']
    d.append(cols)

    def rank(r):
        hard = r['source'] == 'ai_adjudicated' or '[phân vân]' in (r['note'] or '')
        return (0 if hard else 1 if r['verdict'] == 'dat' else 2, r['group'], r['lineage_id'])
    grey, green = PatternFill('solid', fgColor='EEEEEE'), PatternFill('solid', fgColor='D9F2D0')
    for i, r in enumerate(sorted(rows, key=rank), 1):
        moc = '\n\n'.join(f"[{x['as_of']}] {x.get('short_answer') or x['answer']}" for x in r['rows'])
        mo = '\n'.join(q for a in r['adjudications'] for q in a['open_questions'])
        d.append([i, r['lineage_id'], r['group'], r['question'], moc, r['source'], r['verdict'],
                  *[r[k] for k in pr.LABEL_KEYS], r['note'], mo, '', '', ''])
    for row in d.iter_rows(min_row=2):
        for c in row:
            c.alignment = Alignment(wrap_text=True, vertical='top')
            c.fill = green if c.column > len(cols) - 3 else grey
    for k, w in {'D': 45, 'E': 70, 'B': 30}.items():
        d.column_dimensions[k].width = w
    d.freeze_panes = 'C2'
    wb.save(path)


def main():
    outputs = merged_results()
    print('valid', len(outputs), dict(Counter(o['disposition'] for o in outputs.values())))
    rows = final_labels(outputs)
    with open(HERE / 'silver_ai_final.jsonl', 'w', encoding='utf-8') as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + '\n')
    c = Counter((r['source'], r['verdict']) for r in rows)
    summary = {'lineages': len(rows), 'by_source_verdict': {f'{s}|{v}': n for (s, v), n in sorted(c.items())},
               'dat': sum(r['verdict'] == 'dat' for r in rows),
               'dat_by_group': dict(Counter(r['group'] for r in rows if r['verdict'] == 'dat')),
               'adjudications_total': len(outputs), 'unresolved': sum(o['disposition'] == 'unresolved' for o in outputs.values()),
               'human_confirmations': 0}
    (HERE / 'summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    wb = HERE / 'duyet_CMT_final.xlsx'
    if wb.exists():
        raise SystemExit(f'{wb}: refusing overwrite (may hold CMT input)')
    workbook(rows, wb)
    files = sorted(p for p in HERE.rglob('*') if p.is_file() and p.name != 'SHA256SUMS' and '__pycache__' not in p.parts)
    (HERE / 'SHA256SUMS').write_text(''.join(f"{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.relative_to(HERE)}\n" for p in files))
    print(json.dumps(summary, ensure_ascii=False))


if __name__ == '__main__':
    main()

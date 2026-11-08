#!/usr/bin/env python3
"""Validate and package AI adjudication results; human confirmation stays blank."""
from __future__ import annotations
import argparse, hashlib, json, shutil, sys, tempfile
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / 'scripts/review'))
import ai_labels
import test2_labels

HERE = Path(__file__).resolve().parent
REVIEWS = HERE / 'reviews'
REPORT = HERE / 'report.jsonl'
SUMMARY = HERE / 'summary.json'
SUMS = HERE / 'SHA256SUMS'
LABEL_KEYS = [k for q in test2_labels.GOOD for k in (q, q + '_reason')]

def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()

def read_jsonl(p: Path) -> list[dict]:
    return [json.loads(s) for s in p.read_text(encoding='utf-8').splitlines() if s.strip()]

def jsonl(p: Path, rows):
    p.write_text(''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in rows), encoding='utf-8')

def load_validate():
    scope = json.loads((HERE / 'scope.json').read_text(encoding='utf-8'))
    for rel, digest in scope['frozen_files'].items():
        p = ROOT / rel
        if not p.is_file() or sha(p) != digest:
            raise ValueError(f'frozen original changed/missing: {rel}')
    for rel, digest in scope['snapshot_sha256'].items():
        if sha(HERE / rel) != digest:
            raise ValueError(f'frozen snapshot changed: {rel}')
    inputs = {}
    for p in sorted((HERE / 'input').glob('*.jsonl')):
        for row in read_jsonl(p):
            cid = row['case_id']
            if cid in inputs: raise ValueError(f'duplicate input case_id {cid}')
            rec, lid = row['record'], row['lineage_id']
            if rec.get('lineage_id') != lid or test2_labels.worksheet_sha256(rec) != row['worksheet_sha256']:
                raise ValueError(f'{cid}: worksheet binding mismatch')
            if row['run_id'] not in scope['runs']: raise ValueError(f'{cid}: unknown run')
            inputs[cid] = row
    expected = scope['expected_case_ids']
    if len(expected) != len(set(expected)) or set(inputs) != set(expected):
        raise ValueError(f'input coverage mismatch missing={sorted(set(expected)-set(inputs))} extra={sorted(set(inputs)-set(expected))}')
    outputs = {}
    for p in sorted((HERE / 'results').glob('*.jsonl')):
        for row in read_jsonl(p):
            cid = row['case_id']
            if cid in outputs: raise ValueError(f'duplicate result case_id {cid}')
            outputs[cid] = row
    if set(outputs) != set(expected):
        raise ValueError(f'result coverage mismatch missing={sorted(set(expected)-set(outputs))} extra={sorted(set(outputs)-set(expected))}')
    side_labels = {}
    for run in scope['runs']:
        snap = HERE / 'snapshots' / run
        records = ai_labels.load_inputs(snap)
        side_labels[run] = {
            side: ai_labels.read_labels(snap / f'{side}.jsonl', side, records)[0]
            for side in ('a', 'b')
        }
    for cid, x in inputs.items():
        r = outputs[cid]
        for side in ('a', 'b'):
            source = side_labels[x['run_id']][side][x['lineage_id']]
            digest = hashlib.sha256(json.dumps(source, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
            if x[f'raw_{side}_sha256'] != digest or x[side] != source:
                raise ValueError(f'{cid}: input label {side} differs from frozen snapshot')
        for k in ('run_id', 'lineage_id', 'worksheet_sha256', 'raw_a_sha256', 'raw_b_sha256', 'disputed_fields'):
            if r.get(k) != x.get(k): raise ValueError(f'{cid}: {k} binding mismatch')
        if r.get('labeler') != 'ai-adjudicator' or r.get('label_origin') != 'ai' or r.get('verification_status') != 'not_verified' or r.get('human_adjudication_required') is not True:
            raise ValueError(f'{cid}: adjudicator metadata invalid')
        if not isinstance(r.get('reasoning'), str) or not r['reasoning'].strip(): raise ValueError(f'{cid}: missing reasoning')
        if not isinstance(r.get('evidence'), list) or not isinstance(r.get('open_questions'), list): raise ValueError(f'{cid}: evidence/open_questions must be arrays')
        d, lab = r.get('disposition'), r.get('proposed_label')
        if d not in ('prefer_a', 'prefer_b', 'both_wrong', 'unresolved'): raise ValueError(f'{cid}: invalid disposition')
        if d != 'unresolved' and not isinstance(lab, dict): raise ValueError(f'{cid}: resolved case needs label')
        if lab is not None:
            normalized, errs = test2_labels.validate_label(x['record'], lab, require_quote=(d != 'unresolved'))
            if errs: raise ValueError(f'{cid}: invalid label: {errs}')
            if lab.get('verdict') != normalized['verdict']:
                raise ValueError(f'{cid}: proposed verdict does not match normalized Q1–Q4 verdict')
            if d == 'unresolved' and lab.get('evidence_status') != 'insufficient':
                raise ValueError(f'{cid}: tentative unresolved label must be marked evidence_status=insufficient')
        if d != 'unresolved':
            ev = r.get('evidence')
            if lab.get('evidence_status') != 'sufficient' or not isinstance(ev, list) or not any(isinstance(e, dict) and e.get('url') and e.get('quote') for e in ev):
                raise ValueError(f'{cid}: resolved case requires evidence_status=sufficient and evidence URL plus quote')
            if not isinstance(lab.get('evidence'), list) or not lab['evidence']:
                raise ValueError(f'{cid}: resolved proposed label lacks structured evidence')
        if d in ('prefer_a', 'prefer_b'):
            side = d[-1]
            source = side_labels[x['run_id']][side].get(x['lineage_id'])
            if source is None or lab is None or any(lab.get(k) != source.get(k) for k in LABEL_KEYS):
                raise ValueError(f'{cid}: {d} label differs from frozen {side.upper()} label')
    counts = Counter(r['run_id'] for r in inputs.values())
    for run, spec in scope['runs'].items():
        if counts[run] != spec['cases']: raise ValueError(f'{run}: expected {spec["cases"]} cases, got {counts[run]}')
    proposals = {}
    for cid, r in outputs.items():
        if r['disposition'] == 'unresolved': continue
        key = (r['lineage_id'], r['worksheet_sha256'])
        signature = tuple(r['proposed_label'][field] for field in LABEL_KEYS)
        if key in proposals and proposals[key][1] != signature:
            raise ValueError(f'conflicting adjudications of identical worksheet: {proposals[key][0]} vs {cid}')
        proposals[key] = (cid, signature)
    return scope, inputs, outputs

def report_rows(scope, inputs, outputs):
    return [{**inputs[cid], **outputs[cid]} for cid in scope['expected_case_ids']]

def summary_data(scope, inputs, outputs):
    by_run = {}
    for run in scope['runs']:
        rs = [outputs[c] for c in scope['expected_case_ids'] if inputs[c]['run_id'] == run]
        by_run[run] = {'total': len(rs), 'resolved': sum(r['disposition'] != 'unresolved' for r in rs),
                       'unresolved': sum(r['disposition'] == 'unresolved' for r in rs),
                       'dispositions': dict(sorted(Counter(r['disposition'] for r in rs).items()))}
    return {'total': len(outputs), 'unique_lineages': len({r['lineage_id'] for r in outputs.values()}),
            'resolved': sum(r['disposition'] != 'unresolved' for r in outputs.values()),
            'resolved_lineages': len({r['lineage_id'] for r in outputs.values() if r['disposition'] != 'unresolved'}),
            'unresolved_lineages': len({r['lineage_id'] for r in outputs.values() if r['disposition'] == 'unresolved'}),
            'unresolved': sum(r['disposition'] == 'unresolved' for r in outputs.values()),
            'dispositions': dict(sorted(Counter(r['disposition'] for r in outputs.values()).items())),
            'human_confirmations': 0, 'by_run': by_run,
            'unresolved_cases': [{'case_id': cid, 'open_questions': outputs[cid]['open_questions']}
                                 for cid in scope['expected_case_ids'] if outputs[cid]['disposition'] == 'unresolved']}

def cellstr(v):
    if v is None: return ''
    if isinstance(v, str): return v
    return json.dumps(v, ensure_ascii=False, sort_keys=True)

def package_workbook(run, ids, inputs, outputs):
    from openpyxl import load_workbook
    from openpyxl.styles import Alignment, Font, PatternFill
    out = REVIEWS / f'{run}.xlsx'
    if out.exists(): raise ValueError(f'{out}: refusing overwrite')
    # Native export runs against an isolated copy, with flat proposed labels adapted to its expected schema.
    with tempfile.TemporaryDirectory(prefix='adjudication-export-') as td:
        tmp = Path(td) / run
        shutil.copytree(HERE / 'snapshots' / run, tmp)
        proposals = []
        for cid in ids:
            r = outputs[cid]
            if r['disposition'] != 'unresolved':
                lab = dict(r['proposed_label'])
                lab['lineage_id'] = r['lineage_id']
                proposals.append(lab)
        jsonl(tmp / 'adjudication.jsonl', proposals)
        ai_labels.review_export(tmp, out, {})
    wb = load_workbook(out)
    ws = wb[ai_labels.REVIEW_SHEET]
    heads = {str(c.value): c.column for c in ws[1]}
    detail = wb.create_sheet('Hoa giai')
    detail_heads = ['case_id', 'lineage_id', 'disputed_fields', 'disposition', 'reasoning', 'evidence', 'open_questions']
    detail.append(detail_heads)
    for col, title in enumerate(detail_heads, 1):
        c = detail.cell(1, col); c.font = Font(bold=True, color='FFFFFF'); c.fill = PatternFill('solid', fgColor='44546A')
        detail.column_dimensions[__import__('openpyxl').utils.get_column_letter(col)].width = 24 if title not in ('reasoning','evidence','open_questions') else 55
    by_lid = {}
    for cid in ids:
        x, r = inputs[cid], outputs[cid]
        by_lid.setdefault(r['lineage_id'], []).append((cid, r))
        ev_urls = [str(e.get('url')) for e in r.get('evidence', []) if isinstance(e, dict) and e.get('url')]
        openq = r.get('open_questions', [])
        rationale = f"{r['disposition']}\n{r['reasoning']}\nEvidence URLs: " + ('; '.join(dict.fromkeys(ev_urls)) or '(none)') + "\nOpen questions: " + cellstr(openq)
        detail.append([cid, r['lineage_id'], cellstr(r['disputed_fields']), r['disposition'], r['reasoning'], cellstr(r['evidence']), cellstr(openq)])
        for rownum in range(2, ws.max_row + 1):
            if str(ws.cell(rownum, heads['lineage_id']).value) != r['lineage_id']: continue
            ws.cell(rownum, heads['de_xuat_hoa_giai'], rationale)
            for k in LABEL_KEYS:
                if 'chot_' + k in heads: ws.cell(rownum, heads['chot_' + k], '' if r['disposition'] == 'unresolved' else r['proposed_label'].get(k, ''))
            ws.cell(rownum, heads['xac_nhan'], '')
    for row in ws.iter_rows():
        for c in row:
            if isinstance(c.value, str): c.data_type = 's'; c.alignment = Alignment(wrap_text=True, vertical='top')
    for row in detail.iter_rows():
        for c in row:
            if isinstance(c.value, str): c.data_type = 's'; c.alignment = Alignment(wrap_text=True, vertical='top')
    wb.save(out)

def manifest_files():
    return [p for p in sorted(HERE.rglob('*')) if p.is_file()
            and p != SUMS and '__pycache__' not in p.parts]

def combined_workbook(scope, inputs, outputs):
    from openpyxl import Workbook
    from openpyxl.styles import Alignment, Font
    from openpyxl.utils import get_column_letter
    out = REVIEWS / 'all_conflicts.xlsx'
    if out.exists(): raise ValueError(f'{out}: refusing overwrite')
    wb = Workbook(); ws = wb.active; ws.title = 'Xung đột'
    heads = ['case_id', 'run_id', 'lineage_id', 'question', 'as_of', 'AI_A', 'AI_B',
             'disposition', 'de_xuat_AI', 'reasoning', 'evidence', 'open_questions',
             'verification_status', 'xac_nhan_CMT', 'ghi_chu_CMT']
    ws.append(heads); pending = wb.create_sheet('Cần chốt'); pending.append(heads)
    for cid in scope['expected_case_ids']:
        x, r = inputs[cid], outputs[cid]
        lab = r.get('proposed_label')
        row = [cid, x['run_id'], x['lineage_id'], x['record']['question'],
               ', '.join(z['as_of'] for z in x['record']['rows']), ai_labels.compact(x['a']), ai_labels.compact(x['b']),
               r['disposition'], ai_labels.compact(lab) if lab else 'Chưa đủ căn cứ chốt Q1–Q4',
               r['reasoning'], cellstr(r['evidence']), cellstr(r['open_questions']), 'not_verified', '', '']
        ws.append(row)
        if r['disposition'] == 'unresolved': pending.append(row)
    info = wb.create_sheet('Đọc trước')
    info.append(['Nội dung', 'Giá trị'])
    for key, value in [('Phạm vi', f"{len(outputs)} trường hợp theo lượt; {scope['unique_lineages']} lineage riêng biệt"),
                       ('Trạng thái', 'Đề xuất AI; chưa có xác nhận CMT, không phải nhãn người'),
                       ('Đồng thuận', 'Giữ nguyên số đo trước hòa giải; không gộp các lượt hoặc đo lại để tăng AC1'),
                       ('Runtime', 'Theo spec legal-adjudicator; Claude hết quota, thực thi tiếp bằng Codex native'),
                       ('Nhập phiếu', 'Workbook này tổng hợp xung đột; các file riêng theo run dùng định dạng native để duyệt/nhập')]:
        info.append([key, value])
    for sheet in wb:
        sheet.freeze_panes = 'D2' if sheet != info else 'A2'
        sheet.auto_filter.ref = sheet.dimensions
        for cell in sheet[1]: cell.font = Font(bold=True)
        for col in range(1, sheet.max_column + 1):
            sheet.column_dimensions[get_column_letter(col)].width = 60 if col in (4,9,10,11,12) else 28
        for row in sheet:
            for cell in row:
                if isinstance(cell.value, str): cell.data_type = 's'
                cell.alignment = Alignment(wrap_text=True, vertical='top')
    wb.save(out)

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--validate-only', action='store_true'); args = ap.parse_args()
    scope, inputs, outputs = load_validate()
    if args.validate_only:
        print(f"valid: {len(outputs)} cases; frozen originals verified"); return
    for p in (REPORT, SUMMARY, SUMS):
        if p.exists(): raise ValueError(f'{p}: refusing overwrite')
    REVIEWS.mkdir(exist_ok=True)
    for run in scope['runs']:
        package_workbook(run, [c for c in scope['expected_case_ids'] if inputs[c]['run_id'] == run], inputs, outputs)
    combined_workbook(scope, inputs, outputs)
    jsonl(REPORT, report_rows(scope, inputs, outputs))
    SUMMARY.write_text(json.dumps(summary_data(scope, inputs, outputs), ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    # Verify all frozen source bindings again after export, before committing the manifest.
    for rel, digest in scope['frozen_files'].items():
        if sha(ROOT / rel) != digest: raise ValueError(f'frozen original changed during export: {rel}')
    rows = []
    for p in manifest_files():
        try: name = p.relative_to(HERE).as_posix()
        except ValueError: name = p.relative_to(ROOT).as_posix()
        rows.append(f'{sha(p)}  {name}')
    SUMS.write_text('\n'.join(rows) + '\n', encoding='utf-8')
    print(f'packaged {len(outputs)} cases across {len(scope["runs"])} runs')
if __name__ == '__main__': main()

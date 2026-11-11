"""Serialize explicit manual decisions; validate bindings, coverage and source quotes.

No model/API calls and no other labeler's inputs. Reruns must preserve frozen files.
"""
import calendar
import collections
import datetime
import hashlib
import json
from pathlib import Path
import re
import sys
import unicodedata

RUN = Path(__file__).resolve().parent
REPO = RUN.parents[3]
sys.path.insert(0, str(REPO / 'scripts/review'))
from ai_labels import load_inputs, read_labels
from test2_labels import GOOD

norm = lambda text: re.sub(r'\s+', ' ', unicodedata.normalize('NFC', text)).strip()
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
UNKNOWN_PUBLICATION = {'14501', '24929', '12820', '21732', '18276',
                       '19660', '15913', '15491', '12677', '18444'}
EXPECTED = {'chunk01.jsonl': 'ed7fbed4b313d0cf90df48e1dfa4803832937bf3746d3ba94f1774a15173bbcb',
            'chunk02.jsonl': '7776fa959ce0acf49edc9e3ba28307a5c1f6832c3025f2876d44c65c7526998f'}
EFFECT = re.compile(r'^(?:\d+\.\s*)?(?:Điều \d+\.\s*)?'
                    r'(?:Thông tư(?: liên tịch)?|Nghị định|Luật|Quyết định|Pháp lệnh|Nghị quyết)'
                    r' này.{0,230}?có hiệu lực')

def freeze(path, text):
    if path.exists():
        assert path.read_text() == text, f'{path}: refusing to replace frozen output'
    else:
        path.write_text(text)

def main():
    decisions = json.loads((RUN / 'decisions.json').read_text())
    receipts = {r['item_id']: r for r in json.loads((RUN / 'source_receipts.json').read_text())}
    labels, temporal = [], []
    for chunk in ('chunk01', 'chunk02'):
        source = RUN / 'input' / (chunk + '.jsonl')
        assert sha(source) == EXPECTED[source.name]
        packets = [json.loads(line) for line in source.read_text().splitlines()]
        assert len(packets) == len(decisions[chunk]) == 30
        for number, (packet, decision) in enumerate(zip(packets, decisions[chunk]), 1):
            record = packet['record']
            assert len(record['rows']) == 1 and record['group'] == 'T1'
            row = record['rows'][0]
            item = row['source_url'].split('ItemID=')[1]
            receipt = receipts[item]
            raw = RUN / 'evidence' / (item + '.json')
            assert sha(raw) == receipt['sha256']
            data = json.loads(raw.read_text())['data']
            text = (RUN / 'evidence' / (item + '.txt')).read_text()
            target = row['answer'].strip()
            assert norm(target) in norm(text), (chunk, number, 'target not in downloaded text')
            effects = list(dict.fromkeys(line for line in text.splitlines() if EFFECT.search(line)))
            assert effects, (chunk, number, 'effect clause not found')
            effect = effects[-1]
            # Derive dates from operative wording, not effFrom/effTo or worksheet dates.
            date_match = re.search(r'ngày\s*(\d+)\s*(?:tháng\s*|[/.])'
                                   r'(\d+)\s*(?:năm\s*|[/.])\s*(\d{4})', effect)
            effective = None
            date_method = 'publication_date_not_verified'
            if item not in UNKNOWN_PUBLICATION:
                if date_match:
                    day, month, year = map(int, date_match.groups())
                    effective = datetime.date(year, month, day)
                    date_method = 'explicit_operating_clause'
                elif 'sau 45 ngày' in effect or 'sau 15 ngày' in effect:
                    days = 45 if 'sau 45 ngày' in effect else 15
                    assert 'kể từ ngày ký' in effect
                    effective = datetime.date.fromisoformat(data['issueDate'][:10]) + datetime.timedelta(days=days)
                    date_method = 'operating_clause_plus_official_issue_date'
                elif 'sau 1 tháng' in effect:
                    signed = datetime.date.fromisoformat(data['issueDate'][:10])
                    month = signed.month % 12 + 1
                    year = signed.year + (signed.month == 12)
                    effective = datetime.date(year, month, min(signed.day, calendar.monthrange(year, month)[1]))
                    date_method = 'operating_clause_one_calendar_month_plus_official_issue_date'
                assert effective is not None, (chunk, number, effect)
                assert effective <= datetime.date.fromisoformat(row['as_of']), (chunk, number, effective)
            q_values = decision['q'].split('/')
            assert len(q_values) == 4
            label = {'lineage_id': record['lineage_id'], 'labeler': 'ai-b',
                     'label_origin': 'ai', 'verification_status': 'not_verified',
                     'guideline_version': '4.0', 'worksheet_sha256': packet['worksheet_sha256']}
            for q, value in zip(GOOD, q_values):
                label[q] = value
                label[q + '_reason'] = decision.get(q + '_reason', '')
            label['verdict'] = 'dat' if all(label[q] == value for q, value in GOOD.items()) else 'khong_dat'
            label['quote'] = target
            label['note'] = decision['note']
            if item in UNKNOWN_PUBLICATION:
                label['note'] += (' [phân vân] Đã đọc quy tắc hiệu lực sau 15 ngày đăng Công báo nhưng '
                                  'chưa mở được bản Công báo hoặc thuộc tính gốc xác nhận ngày đăng; '
                                  'Q1/Q2/Q4 là lựa chọn tốt nhất, chưa chốt chắc tình trạng tại mốc.')
            label['evidence_status'] = 'insufficient' if item in UNKNOWN_PUBLICATION else 'sufficient'
            label['search_log'] = (f'Đã tải và đọc toàn văn API CSDL quốc gia ItemID={item}; '
                                   f'tìm số hiệu {data["docNum"]} cùng sửa đổi/hiệu lực '
                                   'trong các lượt tra được lưu ở web_receipts.json; '
                                   f'đối chiếu tác động trước {row["as_of"]}, không loại T1 vì văn bản hết hiệu lực sau mốc. '
                                   'Chưa thấy tác động trước mốc trong phạm vi tra cứu; đây không phải rà soát pháp lý toàn diện.')
            label['evidence'] = [
                {'url': receipt['url'], 'source_tier': 'official', 'document_number': data['docNum'],
                 'provision': row['target']['citation'], 'as_of': row['as_of'],
                 'quote': target, 'accessed_at': receipt['accessed_at']},
                {'url': receipt['url'], 'source_tier': 'official', 'document_number': data['docNum'],
                 'provision': 'Điều khoản hiệu lực trong toàn văn; xem temporal_checks.jsonl',
                 'as_of': row['as_of'], 'quote': effect, 'accessed_at': receipt['accessed_at']}
            ]
            if chunk == 'chunk02' and number == 21:
                label['search_log'] += (' Đã đọc toàn văn Quyết định 1317/QĐ-BTC tại '
                                        'https://vanban.chinhphu.vn/default.aspx?docid=162006&pageid=27160; '
                                        'Điều 1 chỉ đính chính các Điều 11, 13, 17, không sửa Điều 7.')
            temporal.append({'chunk': chunk, 'number': number, 'lineage_id': record['lineage_id'],
                             'item_id': item, 'as_of': row['as_of'], 'effect_quote': effect,
                             'effective_date_from_wording': effective.isoformat() if effective else None,
                             'date_method': date_method, 'issue_date_metadata': data['issueDate'],
                             'target_found_in_downloaded_original': True,
                             'limits': 'Bounded amendment search; no complete independent provision-history registry.'})
            labels.append(label)
    out = RUN / 'b.jsonl'
    freeze(out, ''.join(json.dumps(label, ensure_ascii=False) + '\n' for label in labels))
    freeze(RUN / 'temporal_checks.jsonl', ''.join(json.dumps(t, ensure_ascii=False) + '\n' for t in temporal))
    valid, rejected = read_labels(out, 'b', load_inputs(RUN))
    assert not rejected, rejected
    assert len(valid) == len(labels) == 60
    assert set(valid) == set(load_inputs(RUN))
    for label in labels:
        assert len(label['evidence']) == 2
        for evidence in label['evidence']:
            item = evidence['url'].rsplit('/', 1)[1]
            assert norm(evidence['quote']) in norm((RUN / 'evidence' / (item + '.txt')).read_text())
    summary = {'requested': 60, 'valid': len(valid), 'missing': [], 'duplicates': [], 'rejected': [],
               'verdict': dict(collections.Counter(l['verdict'] for l in labels)),
               'evidence_status': dict(collections.Counter(l['evidence_status'] for l in labels)),
               'all_target_and_evidence_quotes_match_downloaded_official_text': True,
               'files_sha256': {'b.jsonl': sha(out), 'decisions.json': sha(RUN / 'decisions.json'),
                                'temporal_checks.jsonl': sha(RUN / 'temporal_checks.jsonl'),
                                'source_receipts.json': sha(RUN / 'source_receipts.json'),
                                'web_receipts.json': sha(RUN / 'web_receipts.json')},
               'validator': 'ai_labels.read_labels + exact input hashes and coverage + downloaded-source quote checks',
               'limits': 'AI reannotation, all not_verified; source sufficiency is annotator judgment, not legal accuracy or human confirmation. Prior B exposure; no AI-A labels read. No paired agreement measured.'}
    freeze(RUN / 'validation.json', json.dumps(summary, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(summary, ensure_ascii=False, indent=2))

if __name__ == '__main__':
    main()

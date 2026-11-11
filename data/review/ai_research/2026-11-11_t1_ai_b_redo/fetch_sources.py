"""Fetch only the 58 official document URLs in the assigned T1 inputs."""
import concurrent.futures
import datetime
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import urllib.request

ROOT = Path(__file__).resolve().parent

class Text(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []
        self.skip = 0
    def handle_starttag(self, tag, attrs):
        if tag in ('style', 'script'):
            self.skip += 1
        if tag in ('p', 'div', 'br', 'tr'):
            self.parts.append('\n')
    def handle_endtag(self, tag):
        if tag in ('style', 'script'):
            self.skip -= 1
        if tag in ('p', 'div', 'tr'):
            self.parts.append('\n')
    def handle_data(self, data):
        if not self.skip:
            self.parts.append(data)

def fetch(item):
    url = 'https://vbpl-bientap-gateway.moj.gov.vn/api/qtdc/public/doc/' + item
    with urllib.request.urlopen(url, timeout=45) as response:
        raw = response.read()
    obj = json.loads(raw)
    assert obj['success'] and obj['data']['id'] == item
    data = obj['data']
    parser = Text()
    parser.feed(data['documentContent']['content'])
    text = '\n'.join(s.strip() for s in ''.join(parser.parts).splitlines() if s.strip())
    assert len(text) > 200
    (ROOT / 'evidence' / (item + '.json')).write_bytes(raw)
    (ROOT / 'evidence' / (item + '.txt')).write_text(text)
    return {'item_id': item, 'document_number': data['docNum'], 'url': url,
            'accessed_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
            'sha256': hashlib.sha256(raw).hexdigest(), 'text_chars': len(text),
            'application_note': data.get('applicationNote')}

if __name__ == '__main__':
    ids = sorted({json.loads(line)['record']['sources']['base']['source_url'].split('ItemID=')[1]
                  for file in (ROOT / 'input').glob('chunk*.jsonl')
                  for line in file.read_text().splitlines()})
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
        receipts = list(pool.map(fetch, ids))
    (ROOT / 'source_receipts.json').write_text(json.dumps(receipts, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'downloaded': len(receipts), 'text_chars': sum(x['text_chars'] for x in receipts)}))

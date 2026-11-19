"""ADR 0006 Amendment 2026-11-19: strip one leading enumeration mark from each span of the T1 short answers.

Mechanical, no judgement: only rows whose meta has qsource "t1" change, and only the leading mark of each
"…"-separated span. The original release stays untouched; the fixed copy goes to --out with the meta beside it.

    python scripts/eval/fix_t1_short_answers.py --release data/vilextime_final/vilextime.jsonl --out DIR
"""
import argparse
import json
import re
import shutil
from pathlib import Path

MARK = re.compile(r'^\s*(?:\d+(?:\.\d+)*\.|[a-zđ]\)|[a-zđ]\.\d+\))\s+')


def fix(short_answer: str) -> str:
    return ' … '.join(MARK.sub('', part, count=1).strip() for part in short_answer.split('…'))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--release', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    args = ap.parse_args()
    meta_path = args.release.with_name('vilextime_meta.jsonl')
    t1 = {m['id'] for m in map(json.loads, meta_path.open(encoding='utf-8')) if m.get('qsource') == 't1'}
    args.out.mkdir(parents=True, exist_ok=True)
    changed, lines = [], []
    for line in args.release.open(encoding='utf-8'):
        r = json.loads(line)
        if r['id'] in t1 and r['answer']:      # published release: "answer" is the short answer
            new = fix(r['answer'])
            if new != r['answer']:
                changed.append({'id': r['id'], 'before': r['answer'], 'after': new})
                r['answer'] = new
        lines.append(json.dumps(r, ensure_ascii=False))
    (args.out / 'vilextime.jsonl').write_text('\n'.join(lines) + '\n', encoding='utf-8')
    shutil.copyfile(meta_path, args.out / 'vilextime_meta.jsonl')
    (args.out / 'changed.jsonl').write_text(''.join(json.dumps(c, ensure_ascii=False) + '\n' for c in changed),
                                            encoding='utf-8')
    print(f'T1 rows {len(t1)}, changed {len(changed)} -> {args.out}')


if __name__ == '__main__':
    assert fix('1. Phạt tiền … d) Điều khiển xe') == 'Phạt tiền … Điều khiển xe'
    assert fix('a.1) Mức phạt') == 'Mức phạt' and fix('1.2. Nội dung') == 'Nội dung'
    assert fix('Thông tư này không điều chỉnh 1. gì') == 'Thông tư này không điều chỉnh 1. gì'
    main()

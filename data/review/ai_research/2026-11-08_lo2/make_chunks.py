"""Shuffle the lo2 bundle, pack into chunks of ≤200K chars, render A/B prompts from prompt_v2.md.
Run from repo root: python3 data/review/ai_research/2026-11-08_lo2/make_chunks.py"""
import json, hashlib, random
from pathlib import Path
D = Path('data/review/ai_research/2026-11-08_lo2'); SEED = 'vilextime-ai-0811'; MAXC, MAXN = 200_000, 18
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
lines = (D / 'input/all.bundle.jsonl').read_text(encoding='utf-8').splitlines()
random.Random(SEED).shuffle(lines)
chunks, cur = [], []
for l in lines:
    if cur and (sum(map(len, cur)) + len(l) > MAXC or len(cur) >= MAXN):
        chunks.append(cur); cur = []
    cur.append(l)
chunks.append(cur)
tpl = Path('data/review/ai_research/prompt_v2.md').read_text(encoding='utf-8')
dsha, gsha = sha('docs/vilextime-dinh-nghia.md'), sha('docs/vilextime-annotation.md')
man = {'worksheet': 'data/review/the4/lo2_moi_worksheet.jsonl', 'worksheet_file_sha256': sha('data/review/the4/lo2_moi_worksheet.jsonl'),
       'builder': 'scripts/review/official_text.py', 'shuffle_seed': SEED, 'chunks': {}}
for i, c in enumerate(chunks, 1):
    name = f'chunk{i:02d}.jsonl'; p = D / 'input' / name
    p.write_text('\n'.join(c) + '\n', encoding='utf-8')
    man['chunks'][name] = {'sha256': sha(p), 'n': len(c), 'chars': sum(map(len, c)),
                           'lineage_ids': [json.loads(x)['record']['lineage_id'] for x in c]}
    for lab in ('ai-a', 'ai-b'):
        (D / 'prompts' / f'chunk{i:02d}_{lab}.md').write_text(tpl.format(labeler=lab, run=D.name, chunk=name, def_sha=dsha,
            guide_sha=gsha, chunk_sha=sha(p), n=len(c), web_budget=6), encoding='utf-8')
(D / 'input/manifest.json').write_text(json.dumps(man, ensure_ascii=False, indent=1), encoding='utf-8')
assert sum(v['n'] for v in man['chunks'].values()) == len(lines)
print({k: (v['n'], v['chars']) for k, v in man['chunks'].items()})

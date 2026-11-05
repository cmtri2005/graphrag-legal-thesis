"""Dev-only replay of historical B2 configurations; no generation or test run."""
import json
import os
import sys
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[2]
os.chdir(ROOT)
os.environ.update(HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1',
                  OMP_NUM_THREADS='4', MKL_NUM_THREADS='4', CUDA_VISIBLE_DEVICES='')
sys.path.insert(0, str(ROOT / 'scripts/eval'))
import colab_b1
import final_run

OUT = Path('runs/final_rehearsal_dev')
RELEASE = Path('data/vilextime_dataset/vilextime.jsonl')
SYSTEMS = ['b1', 'b2', 'b2ctx', 'b3', 'b4', 'b5', 'b6', 'b7', 'b7v',
           'b7plus', 'b7pp', 'proposed', 'a1', 'a2', 'a3', 'a4', 'oracle']

def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')

def jsonl(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in rows))

def main():
    final_run.run_script('scripts/eval/final_run.py', '--step', 'check', '--split', 'dev',
        '--release', RELEASE, '--raw', 'runs/B2_dev/raw', '--retrieval', 'runs/E1_ladder/dev',
        '--systems', *SYSTEMS, '--proposed', 'proposed', '--out', OUT)
    audit = {'split': 'dev', 'release_sha256': final_run.sha(RELEASE),
             'generation': False, 'systems': {}, 'status': 'exporting'}
    for system in SYSTEMS:
        config = json.loads((Path('runs/B2_dev/prompts') / f'{system}.export.json').read_text())
        colab_b1.export_prompts(SimpleNamespace(system=system, split='dev',
            as_of_strategy='giua_khoang', release=RELEASE, index=colab_b1.INDEX,
            limit=0, out=OUT / 'prompts' / f'{system}.jsonl', b2=True,
            no_dense=config['no_dense'], hybrid=config.get('hybrid', False),
            hits_cache=Path('data/derived/rag/retrieval.sqlite')))
        prompts = colab_b1.read_jsonl(OUT / 'prompts' / f'{system}.jsonl')
        candidates = list(Path('runs/B2_dev/raw').glob(f'{system}__*.jsonl'))
        # Oracle has two historical versions: require the original prompt-file identity.
        old_hash = config['prompt_file_sha256'][:12]
        candidates = [p for p in candidates if p.stem.endswith('__' + old_hash)]
        if len(candidates) != 1:
            raise RuntimeError(f'{system}: ambiguous historical raw: {candidates}')
        raw_path = candidates[0]
        raw_rows = colab_b1.read_jsonl(raw_path)
        if len({r['id'] for r in raw_rows}) != len(raw_rows):
            raise RuntimeError(f'{system}: duplicate raw IDs')
        raw = {r['id']: r for r in raw_rows}
        matched = [p for p in prompts if p['id'] in raw and
                   p['prompt_sha256'] == raw[p['id']].get('prompt_sha256')]
        missing = [p['id'] for p in prompts if p['id'] not in raw]
        mismatched = [p['id'] for p in prompts if p['id'] in raw and
                      p['prompt_sha256'] != raw[p['id']].get('prompt_sha256')]
        audit['systems'][system] = dict(total=len(prompts), matched=len(matched),
            missing_ids=missing, mismatched_ids=mismatched, matched_ids=[p['id'] for p in matched],
            raw=str(raw_path), raw_sha256=final_run.sha(raw_path), config=config)
        print(f'HASH {system}: {len(matched)}/{len(prompts)}, mismatch={len(mismatched)}, missing={len(missing)}', flush=True)
        write(OUT / 'rehearsal.json', audit)
        if not matched:
            continue
        filtered = OUT / 'matched_prompts' / f'{system}.jsonl'
        jsonl(filtered, matched)
        meta = json.loads((OUT / 'prompts' / f'{system}.export.json').read_text())
        meta.update(rows=len(matched), prompt_file_sha256=final_run.sha(filtered))
        write(filtered.with_suffix('.export.json'), meta)
        raw_subset = OUT / 'matched_raw' / f'{system}.jsonl'
        jsonl(raw_subset, [raw[p['id']] for p in matched])
        colab_b1.import_completions(SimpleNamespace(prompts=filtered, raw=raw_subset,
            out=OUT / 'dev' / f'{system}.jsonl', index=colab_b1.INDEX))
    audit['status'] = 'imported'
    write(OUT / 'rehearsal.json', audit)
    final_run.run_script('runs/final_rehearsal_dev/finish.py')

if __name__ == '__main__':
    main()

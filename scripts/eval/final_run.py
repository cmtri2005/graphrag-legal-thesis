#!/usr/bin/env python3
"""Offline final-run pipeline (master plan §6–7; C11).

Run --step all, or rerun check/export/import/score/confirm/report separately.
Export normally builds prompts without generation. --source-prompts replays a
previous export byte for byte; raw import always verifies its prompt hashes.
No model is called. The final family is tooling pending a committed amendment.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import colab_b1
import score_vilextime as scorer
from report_results import render

ROOT = Path(__file__).resolve().parents[2]
ADR = 'docs/decisions/0005-ke-hoach-phan-tich.md'
STEPS = ('check', 'export', 'import', 'score', 'confirm', 'report')


def sha(path):
    with path.open('rb') as handle:
        return hashlib.file_digest(handle, 'sha256').hexdigest()


def git(*args, root=ROOT):
    return subprocess.run(['git', *args], cwd=root, text=True, capture_output=True)


def guard_test(split, amendment, inputs, root=ROOT):
    """C11/G3: amendment must be in HEAD; tracked inputs must be clean."""
    if split != 'test':
        return
    if not amendment:
        raise SystemExit('test requires --amendment COMMIT already in HEAD (master plan G3); commit it before running test')
    commit = git('rev-parse', '--verify', f'{amendment}^{{commit}}', root=root)
    if commit.returncode or git('merge-base', '--is-ancestor', commit.stdout.strip(), 'HEAD', root=root).returncode:
        raise SystemExit('test amendment is not a commit contained in HEAD (master plan G3)')
    change = git('show', '--format=', '--unified=0', commit.stdout.strip(), '--', ADR, root=root)
    if not any(line.startswith('+## Amendment') for line in change.stdout.splitlines()):
        raise SystemExit(f'test amendment must add an Amendment to {ADR}; select the G3 amendment commit')
    paths = []
    for path in inputs:
        try:
            paths.append(str(Path(path).resolve().relative_to(root.resolve())))
        except ValueError:
            raise SystemExit(f'test input outside repository: {path}; use frozen repository inputs')
    status = git('status', '--porcelain', '--untracked-files=all', '--', *paths, root=root)
    if status.returncode or status.stdout.strip():
        raise SystemExit('test inputs are dirty (C11/G3); review and commit inputs first:\n' + status.stdout)


def validate_rows(rows, split, dev_rows):
    """Do not weaken the scorer or silently drop answerable rows."""
    if len({r['id'] for r in rows}) != len(rows):
        raise SystemExit('release has duplicate IDs; fix release before final run')
    selected = [r for r in rows if r.get('split') == split and r['as_of_strategy'] == 'giua_khoang']
    if not selected:
        raise SystemExit(f'release has no {split}/giua_khoang rows')
    missing = [r['id'] for r in selected if r['answerable'] and not scorer.spans(r.get('short_answer') or '')]
    if missing:
        raise SystemExit(f'{len(missing)} answerable rows missing short_answer (C11/A10); repair release: {missing[:5]}')
    for key in ('lineage_id', 'document_id'):
        value = lambda r: r['lineage_id'] if key == 'lineage_id' else r['target']['document_id']
        other = {value(r) for r in rows if r.get('split') in ('dev', 'test') and r.get('split') != split}
        if split == 'test':
            other |= {value(r) for r in dev_rows if r.get('split') == 'dev'}
        overlap = {value(r) for r in selected} & other
        if overlap:
            raise SystemExit(f'dev leakage by {key} (ADR 0003 §7/G2): {sorted(overlap)[:5]}; repair split')
    return selected


def run_script(name, *args):
    subprocess.run([sys.executable, str(ROOT / name), *map(str, args)], cwd=ROOT, check=True)


def input_files(args):
    paths = [args.release, args.release.with_name('vilextime_meta.jsonl'), args.index,
             args.dev_release, args.raw, args.retrieval, ROOT / 'src', ROOT / 'scripts/eval',
             ROOT / 'scripts/check/check_release.py', ROOT / 'scripts/review',
             args.data / 'temporal.sqlite', args.data / 'derived/corpus', args.data / 'derived/vilextime']
    if args.source_prompts:
        paths.append(args.source_prompts)
    # Score/confirm read these immutable derived inputs as well.
    paths.append(args.data / 'derived/versions.jsonl')
    return paths


def selected_inputs(args):
    paths = [p for p in input_files(args) if p.is_file()]
    for folder in (ROOT / 'src', ROOT / 'scripts/eval', ROOT / 'scripts/review'):
        paths += sorted(folder.rglob('*.py'))
    paths += [args.data / 'derived/corpus' / name for name in
              ('manifest.json', 'asis.jsonl', 'versions.jsonl', 'documents.jsonl')]
    paths += [args.data / 'derived/vilextime' / name for name in ('release.jsonl', 'selected.jsonl')]
    for system in args.systems:
        if args.source_prompts:
            paths += [args.source_prompts / f'{system}{suffix}' for suffix in ('.jsonl', '.export.json')]
        paths += sorted(args.raw.glob(f'{system}__*.jsonl'))
    paths += sorted(args.retrieval.glob('*.jsonl'))
    return {str(p): sha(p) for p in paths if p.exists()}


def validate_predictions(folder, systems, rows, split):
    wanted = {r['id'] for r in rows if r.get('split') == split and r['as_of_strategy'] == 'giua_khoang'}
    allowed = {r['id'] for r in rows if r.get('split') == split}
    for system in systems:
        path = folder / f'{system}.jsonl'
        predictions = colab_b1.read_jsonl(path)
        ids = {r['id'] for r in predictions}
        if len(ids) != len(predictions) or not wanted <= ids or not ids <= allowed:
            raise SystemExit(f'{path}: duplicate, incomplete or foreign-split predictions; require all {split}/giua_khoang IDs')


def validate_published_release(args):
    """Tie the supplied published subset to the actual input of check_release."""
    public = colab_b1.read_jsonl(args.release)
    if public and 'context' in public[0]:
        sys.path.insert(0, str(ROOT / 'scripts/pipeline'))
        from export_release import published
        internal = {r['id']: r for r in colab_b1.read_jsonl(args.data / 'derived/vilextime/release.jsonl')}
        bad = [r['id'] for r in public if r['id'] not in internal or r != published(internal[r['id']])]
        if bad:
            raise SystemExit(f'release differs from check_release input: {bad[:5]}; rebuild and validate the intended release')
    elif args.release.resolve() != (args.data / 'derived/vilextime/release.jsonl').resolve():
        raise SystemExit('internal release must be the input validated by check_release; set --data accordingly')


def pipeline(args):
    guard_test(args.split, args.amendment, input_files(args))
    required = {'b4', 'b5', 'b7', 'b7pp', args.proposed}
    if len(set(args.systems)) != len(args.systems) or not required <= set(args.systems):
        raise SystemExit(f'final family needs unique systems including {sorted(required)}')
    rows = scorer.load_rows(args.release)
    selected = validate_rows(rows, args.split, scorer.load_rows(args.dev_release))
    out = args.out
    out.mkdir(parents=True, exist_ok=True)
    stamp = out / 'check.json'
    inputs = None
    steps = STEPS if args.step == 'all' else (args.step,)
    if args.step not in ('all', 'check'):
        if not stamp.exists():
            raise SystemExit('run --step check first')
        inputs = selected_inputs(args)
        previous = json.loads(stamp.read_text())
        if (previous['inputs'] != inputs or previous['split'] != args.split
                or previous['systems'] != args.systems or previous['proposed'] != args.proposed):
            raise SystemExit('inputs/configuration changed since check; rerun --step check')
    for step in steps:
        print(f'[{step}]', flush=True)
        if step == 'check':
            # The native check is read-only: never --manifest.
            run_script('scripts/check/check_release.py', '--data', args.data)
            validate_published_release(args)
            inputs = selected_inputs(args)
            stamp.write_text(json.dumps(dict(split=args.split, rows=len(selected), systems=args.systems,
                                            proposed=args.proposed, inputs=inputs,
                                            head=git('rev-parse', 'HEAD').stdout.strip()), indent=2) + '\n')
        elif step == 'export':
            for system in args.systems:
                dest = out / 'prompts' / f'{system}.jsonl'
                if args.source_prompts:
                    source = args.source_prompts / dest.name
                    record = source.with_suffix('.export.json')
                    meta = json.loads(record.read_text())
                    prompts = colab_b1.read_jsonl(source)
                    if (meta['release_sha256'] != sha(args.release) or meta['system'] != system
                            or meta['split'] != args.split or meta['rows'] != len(selected)
                            or meta['prompt_file_sha256'] != sha(source)
                            or {p['id'] for p in prompts} != {r['id'] for r in selected}
                            or any(p.get('split') != args.split or p.get('system_name') != system for p in prompts)):
                        raise SystemExit(f'{source}: export does not match selected release/system/split')
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copyfile(source, dest)
                    shutil.copyfile(record, dest.with_suffix('.export.json'))
                else:
                    colab_b1.export_prompts(SimpleNamespace(system=system, split=args.split,
                        as_of_strategy='giua_khoang', release=args.release, index=args.index,
                        limit=0, out=dest, b2=True, no_dense=False, hybrid=False,
                        hits_cache=out / 'retrieval.sqlite'))
        elif step == 'import':
            for system in args.systems:
                prompts = out / 'prompts' / f'{system}.jsonl'
                expected = {p['id']: p['prompt_sha256'] for p in colab_b1.read_jsonl(prompts)}
                matches = [p for p in sorted(args.raw.glob(f'{system}__*.jsonl'))
                           if {r['id']: r['prompt_sha256'] for r in colab_b1.read_jsonl(p)} == expected]
                if len(matches) != 1:
                    raise SystemExit(f'{system}: expected exactly one matching raw file, found {matches}; provide complete raw for this export')
                colab_b1.import_completions(SimpleNamespace(prompts=prompts, raw=matches[0],
                    out=out / args.split / f'{system}.jsonl', index=args.index))
        elif step == 'score':
            validate_predictions(out / args.split, args.systems, rows, args.split)
            run_script('scripts/eval/score_vilextime.py',
                       *[out / args.split / f'{s}.jsonl' for s in args.systems],
                       '--split', args.split, '--release', args.release, '--data', args.data,
                       '--ci', args.draws, '--out', out / args.split / 'all.score.json')
        elif step == 'confirm':
            validate_predictions(args.retrieval, ['b2ctx', 'b7', 'b7plus', 'b7pp'], rows, args.split)
            validate_predictions(out / args.split, args.systems, rows, args.split)
            run_script('scripts/eval/confirm_vilextime.py', '--family', 'final', '--proposed', args.proposed,
                       '--retrieval', args.retrieval, '--generation', out / args.split,
                       '--split', args.split, '--release', args.release, '--data', args.data,
                       '--draws', args.draws, '--out', out / 'confirm.json')
            result = json.loads((out / 'confirm.json').read_text())
            if result['tests_run'] != result['family_size']:
                raise SystemExit('final family is incomplete; inspect confirm.json before constructing final tables')
        elif step == 'report':
            (out / 'results.md').write_text(render([out / args.split / 'all.score.json'], out / 'confirm.json'))
        if selected_inputs(args) != inputs:
            raise SystemExit(f'inputs changed during {step}; stop and inspect before resuming')


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--step', choices=('all', *STEPS), default='all')
    ap.add_argument('--split', choices=('dev', 'test'), required=True)
    ap.add_argument('--amendment', help='G3 amendment commit, an ancestor of HEAD')
    ap.add_argument('--release', type=Path, required=True)
    ap.add_argument('--dev-release', type=Path, default=Path('data/vilextime_dataset/vilextime.jsonl'))
    ap.add_argument('--data', type=Path, default=Path('data'))
    ap.add_argument('--index', type=Path, default=colab_b1.INDEX)
    ap.add_argument('--source-prompts', type=Path, help='replay existing exports byte for byte')
    ap.add_argument('--raw', type=Path, required=True)
    ap.add_argument('--retrieval', type=Path, required=True)
    ap.add_argument('--systems', nargs='+', default=['b4', 'b5', 'b2ctx', 'b7', 'b7plus', 'b7pp', 'proposed2'])
    ap.add_argument('--proposed', default='proposed2')
    ap.add_argument('--draws', type=int, default=10000)
    ap.add_argument('--out', type=Path, required=True)
    pipeline(ap.parse_args())


if __name__ == '__main__':
    main()

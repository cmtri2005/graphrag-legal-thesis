"""Score verified imports, compare on identical IDs, confirm both families, render."""
from rehearse import *
import subprocess
from report_results import render, confirm_section
import score_vilextime as scorer


def differences(a, b, prefix=''):
    if isinstance(a, dict) and isinstance(b, dict):
        return [d for k in sorted(a.keys() | b.keys())
                for d in differences(a.get(k), b.get(k), prefix + '/' + k)]
    return [] if a == b else [{'field': prefix, 'new': a, 'old': b}]


def finish():
    audit = json.loads((OUT / 'rehearsal.json').read_text())
    rows = scorer.load_rows(RELEASE)
    extra = scorer.distractors(rows)
    for r in rows:
        r['_distractors'] = extra.get(r['id'], [])
    old_scores_path = Path('runs/B2_dev/dev/all.score.json')
    old_scores = json.loads(old_scores_path.read_text())
    systems = [s for s in SYSTEMS if audit['systems'][s]['matched']]
    new = {s: {r['id']: r for r in colab_b1.read_jsonl(OUT / 'dev' / f'{s}.jsonl')} for s in systems}
    old = {s: {r['id']: r for r in colab_b1.read_jsonl(Path('runs/B2_dev/dev') / f'{s}.jsonl')} for s in systems}
    units = scorer.units_of(Path('data'), {**new, **{'old/' + s: p for s, p in old.items()}})[0]
    results, comparison = {}, {}
    for s in systems:
        selected = [r for r in rows if r['id'] in new[s] and r['split'] == 'dev']
        if len(selected) != len(new[s]):
            raise RuntimeError(f'{s}: unexpected imported IDs')
        report = scorer.report(selected, new[s], units, 'dev', draws=2000)
        baseline = scorer.report(selected, old[s], units, 'dev', draws=2000)
        for rep in (report, baseline):
            for groups in rep.values():
                for scores in groups.values():
                    scores.pop('_draws', None)
        results[s] = report
        full = audit['systems'][s]['matched'] == audit['systems'][s]['total']
        comparison[s] = dict(rows=len(selected),
            old_predictions_same_ids=differences(report, baseline),
            stored_all_score=differences(report, {k: old_scores[s][k] for k in report}) if full else None,
            stored_comparison='direct full cohort' if full else 'restricted old predictions rescored on matched IDs')
        print('COMPARE', s, 'old predictions', len(comparison[s]['old_predictions_same_ids']),
              'stored', None if not full else len(comparison[s]['stored_all_score']), flush=True)
    write(OUT / 'dev/all.score.json', results)
    audit.update(comparison=comparison, baseline=str(old_scores_path),
                 baseline_sha256=final_run.sha(old_scores_path), draws=2000, status='scored')
    write(OUT / 'rehearsal.json', audit)
    if any(c['old_predictions_same_ids'] or c['stored_all_score'] for c in comparison.values()):
        raise RuntimeError('Score differs from historical baseline; inspect rehearsal.json before reporting completion')
    # Use the intersection for both families so an unmatched row is never counted as a prediction.
    common = set.intersection(*(set(new[s]) for s in systems))
    retrieval = OUT / 'retrieval'
    for system in ('b2ctx', 'b7', 'b7plus', 'b7pp'):
        # These are retrieval outputs from the newly executed gold-free exporter.
        prompts = colab_b1.read_jsonl(OUT / 'prompts' / f'{system}.jsonl')
        jsonl(retrieval / f'{system}.jsonl', [dict(id=p['id'], retrieved=p['retrieved'],
              signals=p['signals']) for p in prompts])
    audit['retrieval_source'] = 'retrieved/signals from regenerated published-dev prompts'
    for s in ('b2ctx', 'b7', 'b7plus', 'b7pp'):
        common &= {p['id'] for p in colab_b1.read_jsonl(retrieval / f'{s}.jsonl')}
    if not common:
        raise RuntimeError('No common cohort for confirm')
    public = [r for r in colab_b1.read_jsonl(RELEASE) if r['id'] in common and r['split'] == 'dev']
    confirm_release = RELEASE
    if len(common) != len([r for r in rows if r['split'] == 'dev' and r['as_of_strategy'] == 'giua_khoang']):
        confirm_release = OUT / 'confirm_cohort/vilextime.jsonl'
        jsonl(confirm_release, public)
        jsonl(confirm_release.with_name('vilextime_meta.jsonl'),
              [r for r in colab_b1.read_jsonl(RELEASE.with_name('vilextime_meta.jsonl')) if r['id'] in common])
    audit['confirm_cohort_ids'] = sorted(common)
    audit['confirm'] = {}
    for family in ('xn', 'final'):
        path = OUT / f'confirm_{family}.json'
        args = [] if family == 'xn' else ['--family', 'final', '--proposed', 'proposed']
        final_run.run_script('scripts/eval/confirm_vilextime.py', '--split', 'dev',
            '--release', confirm_release, '--retrieval', retrieval, '--generation', OUT / 'dev',
            '--draws', '2000', '--out', path, *args)
        result = json.loads(path.read_text())
        audit['confirm'][family] = {k: result[k] for k in ('tests_run', 'family_size', 'exploratory')}
        if result['tests_run'] != result['family_size']:
            raise RuntimeError(f'{family}: incomplete confirmatory family; inspect {path}')
    table = render([OUT / 'dev/all.score.json'], OUT / 'confirm_xn.json')
    table += '\n' + '\n'.join(confirm_section(OUT / 'confirm_final.json'))
    table += '\nHash-matched rows by system (no generation):\n\n'
    table += '| System | Matched | Total | Mismatch | Missing |\n|---|---|---|---|---|\n'
    for s in SYSTEMS:
        a = audit['systems'][s]
        table += f"| {s} | {a['matched']} | {a['total']} | {len(a['mismatched_ids'])} | {len(a['missing_ids'])} |\n"
    (OUT / 'results.md').write_text(table)
    audit['environment'] = {k: os.environ[k] for k in ('HF_HUB_OFFLINE', 'TRANSFORMERS_OFFLINE', 'OMP_NUM_THREADS', 'MKL_NUM_THREADS', 'CUDA_VISIBLE_DEVICES')}
    audit['command'] = "HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 OMP_NUM_THREADS=4 MKL_NUM_THREADS=4 CUDA_VISIBLE_DEVICES='' .venv/bin/python runs/final_rehearsal_dev/rehearse.py"
    test_args = [sys.executable, '-m', 'pytest', '-q', 'tests/', '-k', 'final or confirm or colab or score']
    with (OUT / 'pytest.log').open('w') as log:
        tested = subprocess.run(test_args, stdout=log, stderr=subprocess.STDOUT)
    audit['validation'] = {'command': '.venv/bin/python -m pytest -q tests/ -k "final or confirm or colab or score"',
                           'exit_code': tested.returncode, 'result': (OUT / 'pytest.log').read_text().strip(),
                           'log': str(OUT / 'pytest.log')}
    audit['comparison_scope'] = f'giua_khoang only; matched IDs per system; confirm intersection {len(common)} dev rows; other strategies in old report excluded'
    write(OUT / 'rehearsal.json', audit)
    tested.check_returncode()
    audit['unresolved_risks'] = ['dev rehearsal only; final family pending committed amendment']
    audit.update(status='completed', stop='report complete; dev only; no generation',
                 results=str(OUT / 'results.md'))
    write(OUT / 'rehearsal.json', audit)

if __name__ == '__main__':
    finish()

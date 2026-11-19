"""AI-A = Claude (legal-annotator-a, claude-opus-5-5) on the r2codex chunks; same flags as supp18/run_a.py. Skips existing outputs."""
import concurrent.futures, datetime, hashlib, json, subprocess
from pathlib import Path
ROOT = Path(__file__).resolve().parents[4]
RUN = Path(__file__).resolve().parent
(RUN / 'claude_logs').mkdir(exist_ok=True); (RUN / 'raw').mkdir(exist_ok=True)
CMD = ['claude', '-p', '--agent', 'legal-annotator-a', '--model', 'claude-opus-5-5', '--output-format', 'json',
       '--no-session-persistence', '--strict-mcp-config', '--mcp-config', '{"mcpServers":{}}',
       '--allowedTools', 'Read', 'Glob', 'Grep', 'WebSearch', 'WebFetch', 'ToolSearch']

def run(job):
    out = RUN / 'raw' / job['prompt']
    if out.exists():
        return {'file': out.name, 'status': 'already_exists'}
    prompt = (RUN / 'prompts' / job['prompt']).read_text()
    started = datetime.datetime.now(datetime.timezone.utc).isoformat()
    try:
        p = subprocess.run(CMD, input=prompt, text=True, capture_output=True, cwd=ROOT, timeout=2400)
        meta = json.loads(p.stdout); text = meta.get('result', '')
        ok = p.returncode == 0 and not meta.get('is_error') and '```jsonl' in text
        if ok:
            out.write_text(text)
        rec = {k: meta.get(k) for k in ['session_id', 'is_error', 'modelUsage', 'num_turns', 'total_cost_usd', 'duration_ms', 'permission_denials']}
        rec.update(file=out.name, status='completed' if ok else 'failed', started_at=started, returncode=p.returncode,
                   prompt_sha256=hashlib.sha256(prompt.encode()).hexdigest())
        if not ok:
            rec['error'] = text[-2000:]; rec['stderr'] = p.stderr[-2000:]
    except Exception as exc:
        rec = {'file': out.name, 'status': 'failed', 'error': str(exc)}
    (RUN / 'claude_logs' / (out.stem + '.metadata.json')).write_text(json.dumps(rec, ensure_ascii=False, indent=2))
    print('DONE', out.name, rec['status'], flush=True)
    return rec

jobs = [j for j in json.loads((RUN / 'plan.json').read_text()) if j['side'] == 'a']
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as ex:
    print(json.dumps([{k: r.get(k) for k in ('file', 'status')} for r in ex.map(run, jobs)]), flush=True)

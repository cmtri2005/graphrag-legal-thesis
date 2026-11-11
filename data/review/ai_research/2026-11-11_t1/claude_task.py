"""Chạy một phiên Claude cô lập, không công cụ (cùng cờ filter_session.py), một lệnh cho mỗi khối <=N mục.
  questions: --kind q --guide HUONG_DAN.md --input packs_dir|viet_lai.jsonl --out answers_N.jsonl
  shorts:    --kind s --guide short_tasks/AGENTS.md --input short_tasks/tasks.jsonl --out short_answers.jsonl
Ghi nguyên văn phản hồi + modelUsage (model thật) vào --log-dir. Không ghi đè --out."""
import argparse, hashlib, json, re, subprocess, sys
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
ap = argparse.ArgumentParser()
ap.add_argument('--kind', choices='qs', required=True); ap.add_argument('--guide', type=Path, required=True)
ap.add_argument('--input', type=Path, required=True); ap.add_argument('--out', type=Path, required=True)
ap.add_argument('--log-dir', type=Path, required=True); ap.add_argument('--model', default='haiku')
ap.add_argument('--chunk', type=int, default=15); a = ap.parse_args()
if a.out.exists(): sys.exit(f'{a.out} đã có')
a.log_dir.mkdir(parents=True, exist_ok=True)
files = sorted(a.input.glob('pack_*.jsonl')) if a.input.is_dir() else [a.input]
items = [json.loads(s) for f in files for s in f.read_text().splitlines() if s.strip()]
key = 'item' if a.kind == 'q' else 'lineage_id'
chunks = [items[i:i+a.chunk] for i in range(0, len(items), a.chunk)]
guide = a.guide.read_text()
TAIL = {'q': '\n\nViết câu hỏi cho MỌI mục trong GÓI. Xuất đúng một dòng JSON cho mỗi mục: {"item": "...", "question": "..."}; '
             'không markdown, không giải thích. Không chắc đủ ngữ cảnh thì question là KHONG_DU_NGU_CANH. '
             'Mục có "da_viet" và "ly_do" là câu bị loại: viết lại câu mới tránh lý do đó.',
        's': '\n\nLàm cho MỌI câu trong GÓI, mỗi phiên bản (version_id) một đáp án. Xuất mỗi dòng một JSON: '
             '{"lineage_id": "...", "version_id": "...", "short_answer": "<trích NGUYÊN VĂN từ answer hoặc lead_in, hoặc null>", "note": "<nếu null>"}; '
             'không markdown, không giải thích. Chỉ trích đoạn có trong văn bản; không diễn đạt lại. Đây là điều khoản chỉ có một phiên bản: '
             'đáp án giống nhau ở mọi mốc là đúng, đừng tìm khác biệt.'}[a.kind]
CMD = ['claude', '-p', '--model', a.model, '--tools', '', '--disable-slash-commands', '--strict-mcp-config', '--mcp-config',
       '{"mcpServers":{}}', '--setting-sources', '', '--settings', '{"disableAllHooks":true}', '--no-session-persistence',
       '--system-prompt', 'Bạn làm đúng theo hướng dẫn và gói được cung cấp. Không dùng công cụ.', '--output-format', 'json']
def run(n):
    ch = chunks[n]; ids = {c[key] for c in ch}
    prompt = guide + '\n\nGÓI:\n' + ''.join(json.dumps(c, ensure_ascii=False) + '\n' for c in ch) + TAIL
    for attempt in (1, 2, 3):   # chỉ thử lại khi lỗi truyền/định dạng; không chọn lại để lấy số đẹp
        p = subprocess.run(CMD, input=prompt, text=True, capture_output=True)
        stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
        (a.log_dir / f'{a.out.stem}_c{n:02d}_t{attempt}_{stamp}.json').write_text(json.dumps({
            'returncode': p.returncode, 'stdout': p.stdout, 'stderr': p.stderr[-2000:], 'requested_model': a.model,
            'input_sha256': hashlib.sha256(prompt.encode()).hexdigest()}, ensure_ascii=False))
        try:
            env = json.loads(p.stdout); text = env['result']; model = sorted(env.get('modelUsage', {}))
            rows = [json.loads(s) for s in text.strip().strip('`').removeprefix('json').splitlines() if s.strip().startswith('{')]
            got = {r[key] for r in rows}
            if got <= ids and (a.kind == 's' or got == ids): return n, rows, model
        except Exception as e: pass
    return n, None, None
with ThreadPoolExecutor(4) as ex: res = list(ex.map(run, range(len(chunks))))
bad = [n for n, r, _ in res if r is None]
rows = [r for _, rs, _ in res if rs for r in rs]
models = sorted({m for _, _, ms in res if ms for m in ms})
a.out.write_text(''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in rows))
meta = {'out': str(a.out), 'chunks': len(chunks), 'failed_chunks': bad, 'rows': len(rows), 'resolved_models': models, 'requested_model': a.model,
        'guide_sha256': hashlib.sha256(guide.encode()).hexdigest(), 'at': datetime.now(timezone.utc).isoformat()}
a.out.with_suffix('.meta.json').write_text(json.dumps(meta, ensure_ascii=False, indent=1))
print(json.dumps(meta, ensure_ascii=False))

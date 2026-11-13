#!/usr/bin/env python3
"""Local question/date demo over the existing retriever, generator and Verifier."""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from datetime import date
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
sys.path.insert(0, str(Path(__file__).resolve().parent / 'eval'))

from vilexgraph.framework import generate, systems, verify
from vilexgraph.framework.corpus import Corpus
from vilexgraph.framework.graphx import repeal_notes
from vilexgraph.framework.temporal import windows_for
from run_vilextime import INDEX, embed_dir, retriever


PAGE = '''<!doctype html><html lang="vi"><meta charset="utf-8">
<title>ViLexGraph · Hỏi theo mốc ngày</title>
<style>body{font:16px system-ui;max-width:1000px;margin:32px auto;padding:0 16px}
textarea{width:100%;height:90px}pre{white-space:pre-wrap;background:#f3f5f6;padding:12px}
article{border-top:1px solid #ddd;padding:12px 0}button,input{padding:8px}small{color:#555}</style>
<h1>ViLexGraph</h1><p>Tra cứu căn cứ tại một mốc ngày.</p>
<form id="form"><label>Câu hỏi<textarea id="question" required></textarea></label>
<label>Mốc ngày <input id="asof" type="date" required></label> <button>Tra cứu</button></form>
<p id="status" role="status"></p><h2>Căn cứ</h2><div id="evidence"></div>
<h2>Lệnh bãi bỏ liên quan</h2><pre id="repeals"></pre>
<h2>Câu trả lời</h2><pre id="answer"></pre><h2>Verifier</h2><pre id="verifier"></pre>
<script>
const el=id=>document.getElementById(id);
el('form').onsubmit=async event=>{event.preventDefault();el('status').textContent='Đang tra cứu…';
for(const id of ['evidence','repeals','answer','verifier'])el(id).textContent='';
try{const response=await fetch('/ask',{method:'POST',headers:{'Content-Type':'application/json'},
body:JSON.stringify({question:el('question').value,as_of:el('asof').value})});
const result=await response.json();if(!response.ok)throw Error(result.error);
el('status').textContent=result.system+' · '+result.status;
for(const unit of result.evidence){const item=document.createElement('article');
const title=document.createElement('strong');title.textContent='['+unit.label+'] '+unit.unit_id;
const meta=document.createElement('pre');meta.textContent='Phiên bản: '+(unit.ordinal??'không có')+
' · Loại: '+unit.kind+'\\nKhoảng hiệu lực [từ, đến): '+JSON.stringify(unit.effective_intervals);
const text=document.createElement('pre');text.textContent=unit.context+'\\n'+unit.text;
item.append(title,meta,text);el('evidence').append(item);}
el('repeals').textContent=result.repeal_notes.join('\\n')||'Không tìm thấy lệnh bãi bỏ liên quan trong căn cứ.';
el('answer').textContent=result.answer?result.answer.raw:result.status;
el('verifier').textContent=result.verification?JSON.stringify(result.verification,null,2):'Chưa chạy: chưa sinh câu trả lời.';
}catch(error){el('status').textContent=error.message;}};
</script></html>'''


# The locked generator of the final run (ADR 0004 amendment 09/11), not whatever `.env` pins.
PROVIDER, MODEL = 'openai', 'gpt-4o-mini-2024-07-18'


def handle_request(payload, *, spec, corpus, search, generator=generate.answer,
                   note_builder=repeal_notes, provider=PROVIDER, model=MODEL):
    """Request processing is injectable so tests never need models, keys or a server."""
    question, as_of = payload.get('question'), payload.get('as_of')
    if not isinstance(question, str) or not question.strip():
        raise ValueError('Cần nhập câu hỏi.')
    if not isinstance(as_of, str) or date.fromisoformat(as_of).isoformat() != as_of:
        raise ValueError('Mốc ngày cần có dạng YYYY-MM-DD.')
    hits = search(question, as_of) if search else []
    units = corpus.units([h.unit_id for h in hits]) if corpus else []
    notes = note_builder(corpus, spec, question, as_of, hits, enabled=True,
                         seed_search=getattr(search, "seeds", None))
    result = {'question': question, 'as_of': as_of, 'system': spec.name, 'evidence': [],
              'repeal_notes': [n.prompt_line(next(i for i, u in enumerate(units, 1)
                                                 if u.unit_id == n.unit_id)) for n in notes],
              'answer': None, 'verification': None, 'status': ''}
    for label, unit in enumerate(units, 1):
        tier = spec.temporal if spec.temporal != 'none' else 'propagated'
        result['evidence'].append({**asdict(unit), 'label': label,
                                   'effective_intervals': windows_for(corpus, unit.unit_id, tier)})

    def ask(evidence):
        return generator(question, as_of, evidence, with_context=spec.context,
                         repeal_notes=notes if spec.repeal_note else (), retries=1, timeout=60,
                         provider=provider, model=model)

    try:
        answer = ask(units)
        if corpus:
            answer, verdict = verify.verify(corpus, mode=spec.verify, tier=spec.temporal,
                                             as_of=as_of, units=units, answer=answer, regenerate=ask)
            result['verification'] = verdict.as_dict()
        else:
            result['verification'] = verify.Verdict('off', 'off').as_dict()
        result['answer'] = asdict(answer)
        result['status'] = 'Đã truy xuất và sinh câu trả lời.'
    except Exception as exc:
        # Evidence remains useful when credentials/model configuration or the network is unavailable.
        result['status'] = ('Đã truy xuất căn cứ; chưa sinh câu trả lời. '
                            f'Không có cấu hình/khóa LLM phù hợp hoặc dịch vụ gặp lỗi ({type(exc).__name__}).')
    return result


def handler_for(spec, corpus, search, provider=PROVIDER, model=MODEL):
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path != '/':
                self.send_error(404)
                return
            body = PAGE.encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_POST(self):
            if self.path != '/ask':
                self.send_error(404)
                return
            try:
                payload = json.loads(self.rfile.read(int(self.headers.get('Content-Length', '0'))))
                if not isinstance(payload, dict):
                    raise ValueError('Yêu cầu phải là một JSON object.')
                result = handle_request(payload, spec=spec, corpus=corpus, search=search,
                                        provider=provider, model=model)
                status = 200
            except (ValueError, TypeError):
                result, status = {'error': 'Nhập câu hỏi và ngày hợp lệ dạng YYYY-MM-DD.'}, 400
            except Exception as exc:
                result, status = {'error': f'Truy xuất gặp lỗi ({type(exc).__name__}).'}, 500
            body = json.dumps(result, ensure_ascii=False).encode('utf-8')
            self.send_response(status)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)
    return Handler


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--system', choices=sorted(systems.REGISTRY), default='proposed2')
    ap.add_argument('--index', type=Path, default=INDEX)
    ap.add_argument('--embed', type=Path, help='default: embeddings of the selected system layer')
    ap.add_argument('--port', type=int, default=8000)
    ap.add_argument('--provider', default=PROVIDER)
    ap.add_argument('--model', default=MODEL)
    args = ap.parse_args()
    spec = systems.get(args.system)
    corpus = Corpus(args.index) if spec.retrieves else None
    # Same explicit hybrid variant as the Colab export when a row requests the unbuilt reranker.
    if spec.rerank:
        spec = spec.variant(spec.name + '-hyb', rerank=False)
    embed = args.embed or (embed_dir(spec.layer) if spec.dense else None)
    search = retriever(spec, corpus, None, embed=embed)
    server = HTTPServer(('127.0.0.1', args.port), handler_for(spec, corpus, search, args.provider, args.model))
    print(f'http://127.0.0.1:{server.server_port} · {spec.name} · {args.provider}/{args.model}', flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
        if corpus:
            corpus.close()


if __name__ == '__main__':
    main()

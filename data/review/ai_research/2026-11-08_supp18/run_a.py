"""Run Claude AI-A for lo2 chunks 1–2 of supp18 (skip existing); never expose AI-B labels to Claude."""
import concurrent.futures,json,subprocess,datetime,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4]
RUN=Path(__file__).resolve().parent
(RUN/'claude_logs').mkdir(exist_ok=True)
(RUN/'raw').mkdir(exist_ok=True)
def run(n):
 name=f'a_chunk{n:02}.md';out=RUN/'raw'/name
 if out.exists():return {'file':name,'status':'already_exists'}
 prompt=(RUN/'prompts'/f'chunk{n:02}_ai-a.md').read_text()
 cmd=['claude','-p','--agent','legal-annotator-a','--model','claude-opus-5-5','--output-format','json','--no-session-persistence','--strict-mcp-config','--mcp-config','{"mcpServers":{}}','--allowedTools','Read','Glob','Grep','WebSearch','WebFetch','ToolSearch']
 print('START',name,datetime.datetime.now(datetime.timezone.utc).isoformat(),flush=True)
 started=datetime.datetime.now(datetime.timezone.utc).isoformat()
 try:
  p=subprocess.run(cmd,input=prompt,text=True,capture_output=True,cwd=ROOT,timeout=1800)
  meta=json.loads(p.stdout)
  text=meta.get('result','')
  success=p.returncode==0 and not meta.get('is_error') and '```jsonl' in text
  if success:
   with out.open('x') as f:f.write(text)
  record={k:meta.get(k) for k in ['session_id','is_error','api_error','api_error_status','modelUsage','usage','num_turns','total_cost_usd','duration_ms','permission_denials']}
  record.update(file=name,status='completed' if success else 'failed',started_at=started,completed_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),returncode=p.returncode,prompt_sha256=hashlib.sha256(prompt.encode()).hexdigest())
  if not success:record['error']=text;record['stderr']=p.stderr[-2000:]
 except Exception as exc:record={'file':name,'status':'failed','error':str(exc)}
 dest=RUN/'claude_logs'/f'a_chunk{n:02}.metadata.json'
 with dest.open('x') as f:json.dump(record,f,ensure_ascii=False,indent=2)
 print('DONE',name,record['status'],flush=True)
 return record
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as ex:
 results=list(ex.map(run,range(1,3)))
print(json.dumps([{k:r.get(k) for k in ('file','status','error')} for r in results],ensure_ascii=False),flush=True)

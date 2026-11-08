"""Prepare + run legal-adjudicator for supp18 disputes, reusing lo2 prepare_adjudication and the 07/11 runner/validator."""
import concurrent.futures, importlib.util, json, sys
from pathlib import Path
RUN = Path(__file__).resolve().parent
ROOT = RUN.parents[3]
def module(name, path):
    s = importlib.util.spec_from_file_location(name, path); m = importlib.util.module_from_spec(s); s.loader.exec_module(m); return m
import types
src = (RUN.parent / "2026-11-08_lo2/finish_lo2.py").read_text()
src = src.replace('f"lo2-', 'f"supp18-').replace('"run_id": "lo2"', '"run_id": "supp18"').replace('snapshots/lo2', 'snapshots/supp18').replace('{"lo2": {', '{"supp18": {')
lo2 = types.ModuleType("supp18_finish"); lo2.__file__ = str(RUN / "finish.py")
exec(compile(src, "finish_lo2.py(supp18 ids)", "exec"), lo2.__dict__)
lo2.RUN, lo2.ROOT = RUN, ROOT
work = RUN / "adjudication"
if not work.exists():
    lo2.prepare_adjudication(work)
owner = RUN.parent / "2026-11-07_adjudication_all"
runner = module("runner", owner / "run_agents.py"); runner.WORK, runner.ROOT = work, ROOT
with concurrent.futures.ThreadPoolExecutor(3) as ex:
    print(json.dumps(list(ex.map(runner.run, sorted((work / "input").glob("batch*.jsonl")))), ensure_ascii=False))

"""Bảng dev: Qwen3.8-27B so với GPT-4o mini trên cùng prompt (r1/r2). Ghi compare_dev.json, in bảng."""
import json
from pathlib import Path

Q = Path("runs/qwen_gen_20261115/dev")
G = {"r1": Path("runs/final_rehearsal_g3_20261112/r1/dev/all.score.json"),
     "r2": Path("runs/final_rehearsal_g3_20261112/r2/dev/all.score.json")}
L = {t: Path(f"runs/lightrag_20261113/dev/{t}/lightrag_vs_b4_p.score.json") for t in ("r1", "r2")}
ORDER = ["oracle", "oracle_now", "b1", "b2ctx", "b3", "b4", "b5", "b6", "b7", "b7plus", "b7pp", "proposed2", "lightrag"]
KEYS = [("all", "accuracy"), ("all", "wrong_version"), ("all", "tcs"), ("all", "mrr"), ("T2", "accuracy"), ("T6", "accuracy")]


def load(path):
    return {s: v["giua_khoang"] for s, v in json.loads(path.read_text()).items()} if path.exists() else {}


out = {}
for model, files in (("qwen", {t: Q / t / "all.score.json" for t in ("r1", "r2")}), ("gpt4omini", G)):
    for tag, path in files.items():
        scores = load(path)
        if model == "gpt4omini":
            scores.update({k: v for k, v in load(L[tag]).items() if k == "lightrag"})
        for s in ORDER:
            if s in scores:
                out.setdefault(s, {}).setdefault(model, {})[tag] = {f"{g}.{m}": scores[s].get(g, {}).get(m) for g, m in KEYS}
Path("runs/qwen_gen_20261115/compare_dev.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
fmt = lambda v: "  -  " if v is None else f"{v:.3f}"
print("system      " + " | ".join(f"{g}.{m}" for g, m in KEYS) + "   (Qwen r1/r2 ; GPT r1/r2)")
for s in ORDER:
    cells = []
    for g, m in KEYS:
        k = f"{g}.{m}"
        q = [out[s].get("qwen", {}).get(t, {}).get(k) for t in ("r1", "r2")]
        o = [out[s].get("gpt4omini", {}).get(t, {}).get(k) for t in ("r1", "r2")]
        cells.append(f"{fmt(q[0])}/{fmt(q[1])};{fmt(o[0])}/{fmt(o[1])}")
    print(f"{s:11s} " + " | ".join(cells))

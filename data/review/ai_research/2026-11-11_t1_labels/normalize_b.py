"""Restore truncated B lineage_id from the worksheet_sha256 binding. Metadata only; original kept in raw_original/."""
import hashlib, json, re, shutil
from pathlib import Path
RUN = Path(__file__).resolve().parent
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
receipt = []
(RUN / "raw_original").mkdir(exist_ok=True)
for raw in sorted((RUN / "raw").glob("b_chunk*.md")):
    orig = RUN / "raw_original" / raw.name
    if not orig.exists():
        shutil.copyfile(raw, orig)
    text = orig.read_text()
    bound = {p["worksheet_sha256"]: p["record"]["lineage_id"]
             for p in map(json.loads, (RUN / "input" / (raw.stem[2:] + ".jsonl")).read_text().splitlines())}
    m = re.search(r"```jsonl\s*\n(.*?)```", text, re.S)
    fixed, edits = [], []
    for line in filter(str.strip, m.group(1).splitlines()):
        r = json.loads(line)
        lid = bound[r["worksheet_sha256"]]
        if r.get("lineage_id") != lid:
            assert lid.startswith(r.get("lineage_id") or ""), (raw.name, r.get("lineage_id"), lid)
            edits.append({"from": r.get("lineage_id"), "to": lid})
            r["lineage_id"] = lid
        fixed.append(json.dumps(r, ensure_ascii=False))
    raw.write_text(text[:m.start(1)] + "\n".join(fixed) + "\n" + text[m.end(1):])
    receipt.append({"raw": raw.name, "original_sha256": sha(orig), "fixed_sha256": sha(raw), "edits": edits})
(RUN / "raw_original/receipt.json").write_text(json.dumps({"method": __doc__, "chunks": receipt}, ensure_ascii=False, indent=2) + "\n")
print({r["raw"]: len(r["edits"]) for r in receipt})

"""Complete missing A fields, lock/measure, adjudicate and export CMT review.

Reuses the original legal-adjudicator runner and adjudication validator.
Does not record human acceptance or modify the original replies.
Run with .venv/bin/python; Claude calls require network access.
"""
import concurrent.futures
import hashlib
import importlib.util
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

RUN = Path(__file__).resolve().parent
ROOT = RUN.parents[3]
sys.path.insert(0, str(ROOT / "scripts/review"))
from ai_labels import load_inputs, read_labels, review_export
from test2_labels import GOOD, worksheet_sha256


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def jsonl(path, rows):
    with path.open("x") as out:
        out.write("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows))


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def prepare_adjudication(work):
    records = load_inputs(RUN)
    labels = {w: read_labels(RUN / f"{w}.jsonl", w, records)[0] for w in ("a", "b")}
    keys = [k for q in GOOD for k in (q, q + "_reason")]
    packets = {p["record"]["lineage_id"]: p for f in sorted((RUN / "input").glob("chunk*.jsonl"))
               for p in map(json.loads, f.read_text().splitlines())}
    cases = []
    for lid, record in records.items():
        a, b = labels["a"][lid], labels["b"][lid]
        disputed = [k for k in keys if a[k] != b[k]]
        if not disputed:
            continue
        cases.append({"case_id": f"lo2-{len(cases)+1:03}", "run_id": "lo2", "lineage_id": lid,
                      "worksheet_sha256": worksheet_sha256(record), "record": record,
                      "a": a, "b": b, "disputed_fields": disputed,
                      "raw_a_sha256": hashlib.sha256(json.dumps(a, sort_keys=True, ensure_ascii=False).encode()).hexdigest(),
                      "raw_b_sha256": hashlib.sha256(json.dumps(b, sort_keys=True, ensure_ascii=False).encode()).hexdigest(),
                      "official": packets[lid]["official"], "official_missing": packets[lid].get("official_missing", []),
                      "schema_note": "A canonical schema is traceable to original replies and bound Claude completion patches; original_evidence is retained. No B labels were provided to A or its completion."})
    work.mkdir()
    (work / "input").mkdir()
    snap = work / "snapshots/lo2"
    (snap / "input").mkdir(parents=True)
    for path in sorted((RUN / "input").glob("chunk*.jsonl")):
        shutil.copyfile(path, snap / "input" / path.name)
    for name in ("a.jsonl", "b.jsonl", "metrics.json"):
        shutil.copyfile(RUN / name, snap / name)
    batch, chars, number = [], 0, 1
    for case in cases:
        size = len(json.dumps(case, ensure_ascii=False))
        if batch and (len(batch) >= 5 or chars + size > 160000):
            jsonl(work / "input" / f"batch{number:02}.jsonl", batch)
            batch, chars, number = [], 0, number + 1
        batch.append(case)
        chars += size
    if batch:
        jsonl(work / "input" / f"batch{number:02}.jsonl", batch)
    original = [RUN / "a.jsonl", RUN / "b.jsonl", RUN / "metrics.json",
                *sorted((RUN / "raw").glob("*.md")),
                ROOT / "docs/vilextime-dinh-nghia.md", ROOT / "docs/vilextime-annotation.md"]
    scope = {"runs": {"lo2": {"cases": len(cases)}}, "expected_case_ids": [c["case_id"] for c in cases],
             "frozen_files": {str(p.relative_to(ROOT)): sha(p) for p in original},
             "snapshot_sha256": {str(p.relative_to(work)): sha(p) for p in sorted(snap.rglob("*")) if p.is_file()},
             "source_limits": "All Q/reason disagreements included. Agreement with insufficient evidence remains visible in CMT review, not silently verified."}
    (work / "scope.json").write_text(json.dumps(scope, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"adjudication_cases": len(cases), "packets": number if cases else 0}), flush=True)


def main():
    raws = sorted((RUN / "raw").glob("a_chunk*.md"))
    assert len(raws) == 12, "Need all twelve A replies"
    omitted = []
    for raw in raws:
        block = re.findall(r"```jsonl\s*\n(.*?)```", raw.read_text(), re.S)[0]
        omitted += [r for r in map(json.loads, filter(str.strip, block.splitlines()))
                    if any(q not in r for q in GOOD) and "rows" not in r]
    if omitted and not (RUN / "schema_completion/patches.jsonl").exists():
        subprocess.run([sys.executable, str(RUN / "complete_a_schema.py")], check=True)
    subprocess.run([sys.executable, str(RUN / "lock_measure.py")], check=True)
    work = RUN / "adjudication"
    if not work.exists():
        prepare_adjudication(work)
    owner = ROOT / "data/review/ai_research/2026-11-07_adjudication_all"
    runner = module("lo2_adjudicator_runner", owner / "run_agents.py")
    runner.WORK, runner.ROOT = work, ROOT
    packets = sorted((work / "input").glob("batch*.jsonl"))
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        results = list(executor.map(runner.run, packets))
    assert all(r.get("status") in ("completed", "preserved_existing_reply") for r in results), results
    validator = module("lo2_adjudication_validator", owner / "package_review.py")
    validator.HERE, validator.ROOT = work, ROOT
    scope, inputs, outputs = validator.load_validate()
    proposals = [{"lineage_id": r["lineage_id"], **r["proposed_label"],
                  "labeler": "ai-adjudicator", "label_origin": "ai", "verification_status": "not_verified"}
                 for r in outputs.values() if r["disposition"] != "unresolved"]
    out = RUN / "adjudication.jsonl"
    if not out.exists():
        jsonl(out, proposals)
    review = RUN / "duyet_CMT_after_adjudication.xlsx"
    if not review.exists():
        review_export(RUN, review, {})
    summary = validator.summary_data(scope, inputs, outputs)
    summary["human_acceptance"] = "pending; CMT acceptance of prior silver does not cover this batch"
    summary["review"] = review.name
    (work / "validation_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(summary, ensure_ascii=False, indent=2), flush=True)


if __name__ == "__main__":
    main()

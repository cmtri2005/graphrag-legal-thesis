"""Parse the new labels, validate them, pair each with the kept label of the other family, list disagreements.

Writes a.jsonl / b.jsonl (new Claude-vs-Codex pairs for the 28 lineages, raw labels unchanged),
disagreements.jsonl (lineages whose Q1–Q4 or verdict differ; these go to adjudication), metrics.json.
Run from repo root after run_a.py and run_b.sh.
"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, "scripts/review")
from ai_labels import read_labels, metric, worksheet_sha256  # noqa: E402

AI = Path("data/review/ai_research")
RUN = AI / "2026-11-19_uniform"
OLD = {"r2codex": AI / "2026-11-06_silver/round2_codex", "silver01": AI / "2026-11-07_adjudication_all/snapshots/silver01"}
QS = ("q1", "q2", "q3", "q4", "verdict")


def block(text):
    m = re.search(r"```jsonl\n(.*?)```", text, re.S)
    assert m, "no jsonl block"
    return [line for line in m.group(1).splitlines() if line.strip()]


def main():
    plan = json.loads((RUN / "plan.json").read_text())
    records = {}
    for p in sorted((RUN / "input").glob("*.jsonl")):
        for line in p.read_text().splitlines():
            item = json.loads(line)
            assert item["worksheet_sha256"] == worksheet_sha256(item["record"])
            records[item["record"]["lineage_id"]] = (p.name.split("_chunk")[0], item["record"])
    new = {"a": [], "b": []}
    for j in plan:
        new[j["side"]] += block((RUN / "raw" / j["prompt"]).read_text())
    out = {}
    for side in "ab":
        tmp = RUN / f"new_{side}.jsonl"
        rows = [json.loads(x) for x in new[side]]
        by_binding = {worksheet_sha256(rec): lid for lid, (_, rec) in records.items()}
        for r in rows:  # binding identifies the lineage (as in supp18): repair a mistyped lineage_id, log it
            lid = by_binding.get(r.get("worksheet_sha256"))
            if lid and r.get("lineage_id") != lid:
                print("binding repair:", r.get("lineage_id"), "->", lid)
                r["binding_repair"] = {"lineage_id_written": r["lineage_id"]}
                r["lineage_id"] = lid
        for r in rows:  # verdict is derived, as in supp18/normalize_a.py; never overwrite a stated one
            good = (r.get("q1"), r.get("q2"), r.get("q3"), r.get("q4")) == ("dung", "co", "co", "khong")
            r.setdefault("verdict", "dat" if good else "khong_dat")
        tmp.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows))
        recs = {lid: r for lid, (job, r) in records.items() if (side == "a") == (job == "r2codex")}
        valid, rejected = read_labels(tmp, side, recs)
        assert not rejected, rejected
        assert set(valid) == set(recs), set(recs) - set(valid)
        out[side] = valid
    # Kept side: old B of round2_codex (Codex), old A of silver01 (Claude).
    pairs = {}
    for job, keep in (("r2codex", "b"), ("silver01", "a")):
        old = {json.loads(x)["lineage_id"]: json.loads(x) for x in open(OLD[job] / f"{keep}.jsonl")}
        for lid, (j, _) in records.items():
            if j == job:
                a = out["a"][lid] if keep == "b" else old[lid]
                b = old[lid] if keep == "b" else out["b"][lid]
                pairs[lid] = (job, a, b)
    for side, idx in (("a", 1), ("b", 2)):
        (RUN / f"{side}.jsonl").write_text("".join(json.dumps(v[idx], ensure_ascii=False) + "\n" for v in pairs.values()))
    (RUN / "pairs.jsonl").write_text("".join(json.dumps({"lineage_id": lid, "job": v[0]}) + "\n" for lid, v in pairs.items()))
    dis = [{"lineage_id": lid, "job": job, "differs": [q for q in QS if a[q] != b[q]],
            "a": {q: a[q] for q in QS}, "b": {q: b[q] for q in QS}}
           for lid, (job, a, b) in pairs.items() if any(a[q] != b[q] for q in QS)]
    (RUN / "disagreements.jsonl").write_text("".join(json.dumps(d, ensure_ascii=False) + "\n" for d in dis))
    ids = list(pairs)
    m = {q: metric([pairs[i][1][q] for i in ids], [pairs[i][2][q] for i in ids], q) for q in QS}
    m["n"] = len(ids)
    m["verdict_counts"] = {"a_dat": sum(pairs[i][1]["verdict"] == "dat" for i in ids),
                           "b_dat": sum(pairs[i][2]["verdict"] == "dat" for i in ids)}
    (RUN / "metrics.json").write_text(json.dumps(m, ensure_ascii=False, indent=1) + "\n")
    print(json.dumps({"pairs": len(ids), "disagreements": len(dis), "verdict": m["verdict"], **m["verdict_counts"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()

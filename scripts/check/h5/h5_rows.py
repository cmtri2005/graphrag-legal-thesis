"""Doc-only: nạp các tập dòng benchmark (dev, v1.0 test, test2, silver, lo2). Chỉ đọc."""
import json, sqlite3
def rd(p): return [json.loads(l) for l in open(p, encoding="utf-8")]
def load_rows():
    db = sqlite3.connect("file:data/temporal.sqlite?mode=ro", uri=True)
    doc_of = {}
    def doc(lin):
        if lin not in doc_of:
            r = db.execute("select document_id from provisions where id=?", (lin,)).fetchone()
            doc_of[lin] = r[0] if r else None
        return doc_of[lin]
    out = []  # (set, id, lineage, as_of, answerable, doc, vid)
    for r in rd("data/derived/vilextime/release.jsonl"):
        out.append(("dev" if r["split"] == "dev" else "v1.0_test", r["id"], r["lineage_id"], r["as_of"], r["answerable"], r["target"]["document_id"], r.get("version_id")))
    for r in rd("data/vilextime/test2_release_v2.jsonl"):
        out.append(("test2", r["id"], r["lineage_id"], r["as_of"], r["answerable"], r["target"]["document_id"], r.get("version_id")))
    for r in rd("data/vilextime_dataset/vilextime_silver.jsonl"):
        out.append(("silver_old859", r["id"], r["lineage_id"], r["as_of"], r["answerable"], doc(r["lineage_id"]), r.get("version_id")))
    for name, tag in (("lo1_silver", "silver_lo1"), ("lo2_moi", "lo2")):
        for w in rd(f"data/review/the4/{name}_worksheet.jsonl"):
            for r in w["rows"]:
                out.append((tag, r["id"], w["lineage_id"], r["as_of"], r["answerable"], r["target"]["document_id"], r.get("version_id")))
    return out

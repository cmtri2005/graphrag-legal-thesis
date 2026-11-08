"""Preserve Claude replies; derive schema fields from bound records and card 4.0.

Run before locking. This never edits raw replies or infers legal judgments.
Per-date Q1 is adverse if any date is adverse (annotation §§1–3).
Other per-date answers must agree; ambiguous reductions stop for review.
"""
import hashlib
import json
import re
import sys
from pathlib import Path

RUN = Path(__file__).resolve().parent
sys.path.insert(0, str(RUN.parents[3] / "scripts/review"))
from ai_labels import read_labels
from test2_labels import GOOD, validate_label


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    dest = RUN / "normalized_a"
    dest.mkdir(exist_ok=True)
    patch_file = RUN / "schema_completion/patches.jsonl"
    patches = {r["lineage_id"]: r for r in map(json.loads, patch_file.read_text().splitlines())} if patch_file.exists() else {}
    receipt = []
    for raw in sorted((RUN / "raw").glob("a_chunk*.md")):
        inp = RUN / "input" / (raw.stem[2:] + ".jsonl")
        packets = [json.loads(line) for line in inp.read_text().splitlines()]
        bound = {p["worksheet_sha256"]: p["record"] for p in packets}
        assert len(bound) == len(packets)
        blocks = re.findall(r"```jsonl\s*\n(.*?)```", raw.read_text(), re.S)
        assert len(blocks) == 1, raw
        labels = [json.loads(line) for line in blocks[0].splitlines() if line.strip()]
        assert len(labels) == len(packets), raw
        edits = []
        for label in labels:
            record = bound[label["worksheet_sha256"]]
            changed = {}
            if "lineage_id" not in label:
                changed["lineage_id"] = record["lineage_id"]
            else:
                assert label["lineage_id"] == record["lineage_id"]
            missing = [q for q in GOOD if q not in label]
            if missing and "rows" not in label:
                patch = patches.get(record["lineage_id"])
                if patch is None:
                    raise ValueError(f"{raw.name}/{record['lineage_id']}: omitted {missing}; needs bound Claude completion, not adapter inference")
                assert patch["original_raw"] == raw.name and patch["original_raw_sha256"] == sha(raw)
                assert patch["worksheet_sha256"] == label["worksheet_sha256"]
                for q in missing:
                    changed[q], changed[q + "_reason"] = patch[q], patch[q + "_reason"]
                if patch.get("note_append"):
                    changed["note"] = label.get("note", "") + " " + patch["note_append"]
                if patch["evidence_status"] != label["evidence_status"]:
                    changed["original_evidence_status"] = label["evidence_status"]
                    changed["evidence_status"] = patch["evidence_status"]
            for q in GOOD:
                if q in label or q in changed:
                    continue
                rows = label["rows"]
                expected = {r["id"] for r in record["rows"]}
                assert {r.get("row_id", r.get("id")) for r in rows} == expected
                values = {r[q] for r in rows}
                if q == "q1" and "sai" in values:
                    chosen = [r for r in rows if r[q] == "sai"]
                else:
                    assert len(values) == 1, (raw, record["lineage_id"], q, values)
                    chosen = rows
                pairs = {(r[q], r.get(q + "_reason", "")) for r in chosen}
                assert len(pairs) == 1, (raw, record["lineage_id"], q, pairs)
                changed[q], changed[q + "_reason"] = next(iter(pairs))
            label.update(changed)
            canonical, errors = validate_label(record, label)
            assert not errors, (raw, record["lineage_id"], errors)
            verdict = canonical["verdict"]
            if "label" in label:
                assert label["label"] == verdict
            if "verdict" in label:
                assert label["verdict"] == verdict
            else:
                changed["verdict"] = verdict
                label["verdict"] = verdict
            edits.append({"lineage_id": record["lineage_id"], "derived_fields": changed})
        out = dest / (raw.stem + ".jsonl")
        content = "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in labels)
        if out.exists():
            assert out.read_text() == content, out
        else:
            out.write_text(content)
        valid, rejected = read_labels(out, "a", {r["lineage_id"]: r for r in bound.values()})
        assert not rejected and len(valid) == len(packets), rejected
        receipt.append({"raw": raw.name, "raw_sha256": sha(raw), "input_sha256": sha(inp),
                        "normalized_sha256": sha(out), "valid": len(valid), "edits": edits})
    (dest / "receipt.json").write_text(json.dumps({
        "authority": "docs/vilextime-annotation.md §§1–3; scripts/review/test2_labels.py",
        "method": "Binding identifies lineage; adverse per-date Q1 fails the question; other per-date Qs must agree; verdict follows GOOD. Original raw and evidence unchanged. Adapter infers no missing legal answer.",
        "annotation_completion_sha256": sha(patch_file) if patch_file.exists() else None,
        "annotation_completion_note": "Omitted Qs use separate raw-bound Claude patches only. Original Qs preserved; note additions and any source-status downgrade are attributed to the completion patch.",
        "chunks": receipt,
    }, ensure_ascii=False, indent=2) + "\n")
    print({"chunks": len(receipt), "valid": sum(r["valid"] for r in receipt)})


if __name__ == "__main__":
    main()

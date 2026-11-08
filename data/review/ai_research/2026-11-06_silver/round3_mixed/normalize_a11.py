"""Adapt the preserved Claude reply to the existing schema without relabeling.

Retain all original evidence separately; expose only quotes traceable to the
input as structured evidence. This adds source locators, not new legal research.
"""
import hashlib
import json
import re
import sys
from pathlib import Path

RUN = Path(__file__).resolve().parent
ROOT = RUN.parents[4]
sys.path.insert(0, str(ROOT / "scripts/review"))
from test2_labels import validate_label


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def strings(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for child in value.values():
            yield from strings(child)
    elif isinstance(value, list):
        for child in value:
            yield from strings(child)


norm = lambda value: " ".join(value.split())
raw = RUN / "raw/a_chunk11.md"
original = RUN / "claude_logs/a_chunk11.original.md"
if not original.exists():
    original.write_bytes(raw.read_bytes())
content = original.read_text()
block = re.search(r"```jsonl\s*\n(.*?)```", content, re.S)
inputs_path = RUN / "input/chunk11.jsonl"
packets = [json.loads(line) for line in inputs_path.read_text().splitlines()]
labels = [json.loads(line) for line in block[1].splitlines() if line.strip()]
assert len(labels) == len(packets) == 18
receipt = []
for index, (label, packet) in enumerate(zip(labels, packets), 1):
    assert label["lineage_id"] == packet["record"]["lineage_id"]
    validated, errors = validate_label(packet["record"], label)
    assert not errors, errors
    assert label["label"] == validated["verdict"]
    label["verdict"] = validated["verdict"]
    label["original_evidence"] = label["evidence"]
    evidence = []
    omitted = []
    for item in label["original_evidence"]:
        quote = norm(item["quote"])
        matches = [part for part in packet["official"] if quote in norm(part["text"])]
        copy = dict(item)
        if item["source_tier"] != "snippet" and matches:
            part = matches[0]
            copy.update(url="https://vbpl-bientap-gateway.moj.gov.vn/api/qtdc/public/doc/" + str(part["item_id"]),
                        source_tier="official", document_number=part["document"],
                        access_method="provided_official_excerpt; no new request")
        elif item["source_tier"] != "snippet" and any(quote in norm(text) for text in strings(packet["record"])):
            copy.update(url=inputs_path.resolve().as_uri() + f"#L{index}",
                        source_tier="worksheet", access_method="provided_worksheet; no new request")
        else:
            omitted.append(item)
            continue
        evidence.append(copy)
    assert 1 <= len(evidence) <= 2
    label["evidence"] = evidence
    receipt.append({"lineage_id": label["lineage_id"], "derived_verdict": label["verdict"],
                    "structured_evidence": evidence, "unresolved_source_locators": omitted})
replacement = "\n".join(json.dumps(label, ensure_ascii=False) for label in labels) + "\n"
adapted = content[:block.start(1)] + replacement + content[block.end(1):]
raw.write_text(adapted)
(RUN / "schema_normalization.json").write_text(json.dumps({
    "method": "Deterministic schema adapter; Q1–Q4, reasons, note, quote, evidence_status unchanged",
    "original": str(original.relative_to(RUN)), "original_sha256": sha(original),
    "input_sha256": sha(inputs_path), "adapted_sha256": sha(raw),
    "source_limits": "Original evidence retained in full. Structured evidence uses exact input quote matches only. Local worksheet URLs are input locators, not external legal verification. Unresolved source URLs remain in this receipt and original_evidence.",
    "rows": receipt,
}, ensure_ascii=False, indent=2) + "\n")
print("Adapted 18 labels; original judgments and reply preserved")

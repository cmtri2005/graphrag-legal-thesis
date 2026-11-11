"""Attach input locators to Claude evidence without new research or relabeling.

Unlocated entries remain in original_evidence and the receipt. Elisions match
only when all verbatim segments occur in order within a single input passage.
"""
import hashlib
import json
import re
from pathlib import Path

RUN = Path(__file__).resolve().parent


def strings(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for child in value.values():
            yield from strings(child)
    elif isinstance(value, list):
        for child in value:
            yield from strings(child)


def match(quote, text):
    quote, text = " ".join(quote.split()), " ".join(text.split())
    if quote and quote in text:
        return "exact"
    parts = re.split(r"\s*\.\.\.\s*|\s*…\s*", quote)
    if len(parts) < 2:
        return None
    cursor = 0
    for part in filter(None, parts):
        index = text.find(part, cursor)
        if index < 0:
            return None
        cursor = index + len(part)
    return "ordered_verbatim_segments"


def main():
    dest = RUN / "canonical_a"
    dest.mkdir(exist_ok=True)
    receipt = []
    for src in sorted((RUN / "normalized_a").glob("a_chunk*.jsonl")):
        inp = RUN / "input" / (src.stem[2:] + ".jsonl")
        packets = {p["worksheet_sha256"]: (i, p) for i, p in enumerate(
            map(json.loads, inp.read_text().splitlines()), 1)}
        labels = [json.loads(line) for line in src.read_text().splitlines()]
        for label in labels:
            index, packet = packets[label["worksheet_sha256"]]
            original = label["evidence"]
            evidence, omitted = [], []
            for item in original:
                found = [part for part in packet["official"] if match(item["quote"], part["text"])]
                copy = dict(item)
                if found and len({p["item_id"] for p in found}) == 1:
                    part = found[0]
                    copy.update(url="https://vbpl-bientap-gateway.moj.gov.vn/api/qtdc/public/doc/" + str(part["item_id"]),
                                source_tier="official", document_number=part["document"],
                                quote_match=match(item["quote"], part["text"]))
                elif any(match(item["quote"], text) for text in strings(packet["record"])):
                    copy.update(url=inp.resolve().as_uri() + f"#L{index}", source_tier="worksheet",
                                document_number=item.get("document", item.get("doc", "unknown")),
                                quote_match="provided_worksheet")
                elif item.get("url"):
                    copy["quote_match"] = "worker_provided_external_source; not reverified"
                    copy.setdefault("document_number", item.get("document", item.get("doc", "unknown")))
                else:
                    omitted.append(item)
                    continue
                copy.setdefault("provision", item.get("location", item.get("locator", "unknown")))
                copy.setdefault("as_of", "unknown")
                copy.setdefault("accessed_at", "unknown")
                copy["access_method"] = "provided_input_locator; no new source request"
                evidence.append(copy)
            if not evidence:
                # A cited a different provision of a known document after web
                # research. Its URL can be recovered, but the quote is not
                # asserted to occur in the supplied excerpt.
                for item in original:
                    citation = item.get("document", item.get("doc", ""))
                    found = {part["item_id"]: part for part in packet["official"]
                             if re.search(r"(?<![0-9])" + re.escape(part["document"]) + r"(?![A-Za-z0-9/-])", citation)}
                    if item.get("source_tier") == "official" and len(found) == 1:
                        part = next(iter(found.values()))
                        evidence.append({**item,
                            "url": "https://vbpl-bientap-gateway.moj.gov.vn/api/qtdc/public/doc/" + str(part["item_id"]),
                            "document_number": part["document"],
                            "provision": item.get("location", item.get("locator", citation)),
                            "as_of": "unknown", "accessed_at": "unknown",
                            "quote_match": "worker_cited_document; outside provided excerpt; not reverified",
                            "access_method": "known document identity only; no new source request"})
            if not evidence and omitted and len(packet["official"]) == 1 and omitted[0].get("source_tier") == "official":
                # T1 variant (11/11): quote not found in the (possibly truncated) single base excerpt;
                # keep it, bound to the one input document, explicitly unverified. Decisions untouched.
                part, item = packet["official"][0], omitted[0]
                evidence.append({**item, "url": "https://vbpl-bientap-gateway.moj.gov.vn/api/qtdc/public/doc/" + str(part["item_id"]),
                                 "document_number": part["document"], "provision": item.get("location", "unknown"),
                                 "as_of": "unknown", "accessed_at": "unknown",
                                 "quote_match": "worker_cited; not found in provided excerpt; not reverified",
                                 "access_method": "known document identity only; no new source request"})
                omitted = omitted[1:]
            assert 1 <= len(evidence) <= 2, label["lineage_id"]
            label.update(original_evidence=original, evidence=evidence)
            receipt.append({"lineage_id": label["lineage_id"], "structured_evidence": len(evidence),
                            "unlocated_original_evidence": omitted})
        out = dest / src.name
        content = "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in labels)
        if out.exists():
            assert out.read_text() == content
        else:
            out.write_text(content)
    (dest / "receipt.json").write_text(json.dumps({
        "authority": ".claude/skills/vilextime-ai-labeling/SKILL.md; prior round3_mixed/normalize_a11.py locator method",
        "limits": "Input or worker-cited document locators only; worksheet matches and document identity are not independent quote verification. Original evidence, decisions and evidence_status are preserved. Quotes outside excerpts remain explicitly unverified.",
        "source_sha256": {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((RUN / "normalized_a").glob("a_chunk*.jsonl"))},
        "rows": receipt,
    }, ensure_ascii=False, indent=2) + "\n")
    print({"labels": len(receipt), "unlocated_entries": sum(len(r["unlocated_original_evidence"]) for r in receipt)})


if __name__ == "__main__":
    main()

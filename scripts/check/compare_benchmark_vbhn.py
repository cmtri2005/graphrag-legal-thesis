#!/usr/bin/env python3
"""C7: independent PDF wording audit; all row-level outputs stay gitignored.

No LLM, OCR, graph writes or labels. Network is opt-in, serial, portal-only,
with >=1.5 seconds between requests; stop at the first network failure.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from datetime import date
import difflib
import hashlib
import json
from pathlib import Path
import re
import sqlite3
import subprocess
import time
import unicodedata
import urllib.parse
import urllib.request

from compare_neo4j_snapshots import _parents_first, _version
from vilexgraph.build.graph.consolidation_validation import select_base_target
from vilexgraph.build.index import TemporalIndex
from vilexgraph.build.temporal import (
    EventStatus, LegalEvent, LegalOperation, SnapshotService, TemporalState,
)

ROOT = Path("data/vbhn_files")
DATASETS = {
    "silver": Path("data/vilextime_dataset/vilextime_silver.jsonl"),
    "test2": Path("data/vilextime/test2_release_v2.jsonl"),
    "v1.0": Path("data/vilextime_dataset/vilextime.jsonl"),
}
PORTAL = "https://vbpl-bientap-gateway.moj.gov.vn/api/qtdc/public/doc/"
HEADERS = {"Referer": "https://vbpl.vn/", "User-Agent": "Mozilla/5.0 (compatible; legal-crawler/0.1)"}
ARTICLE = re.compile(r"^Điều\s+(\d+[a-zđ]?)\s*[.:]\s*", re.I)
CLAUSE = re.compile(r"^(\d+[a-zđ]?)\s*[.)]\s+")
# A footnote number may sit right after the bracket ("đ)19 (được bãi bỏ)."): it still opens the point
# of that letter, or the marker lands in the point before it (H5 L6, 10/11/2026).
POINT = re.compile(r"^([a-zđ])\s*[.)](?:\s+|(?=\d{1,3}\s))", re.I)
SECTION = re.compile(r"^(?:Chương|Mục|Phần|Tiểu mục)\s+(?:[IVXLC]+|\d+)\b", re.I)
NOTE = re.compile(r"^\d+\s+(?:Điều|Khoản|Điểm|Cụm|Nội dung|Mục|Chương|Phụ lục|Thông tư|Nghị định|Luật|Bộ luật|Từ|Tên)\b", re.I)
DATE = re.compile(r"ngày\s+(\d{1,2})\s+tháng\s+(\d{1,2})\s+năm\s+(\d{4})", re.I)


def norm(text):
    return " ".join(unicodedata.normalize("NFC", text).split())


class ReadOnlyIndex(TemporalIndex):
    def __init__(self, path):
        self._db = sqlite3.connect(f"file:{Path(path).resolve()}?mode=ro", uri=True)
        self._db.row_factory = sqlite3.Row

    def __exit__(self, *exc):
        self.close()


def rows(path):
    with path.open(encoding="utf-8") as stream:
        for line in stream:
            yield json.loads(line)


def write_json(path, obj):
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def discover(index):
    benchmark = []
    for dataset, path in DATASETS.items():
        for row in rows(path):
            if row["group"] not in {"T2", "T3", "T6"}:
                continue
            pid = row["lineage_id"]
            p = index._db.execute("SELECT document_id FROM provisions WHERE id=?", (pid,)).fetchone()
            benchmark.append({"dataset": dataset, "row_id": row["id"], "lineage_id": pid,
                              "group": row["group"], "as_of": row["as_of"],
                              "benchmark_version_id": row.get("version_id"),
                              "document_id": p[0] if p else None})
    docs = {r["document_id"] for r in benchmark}
    report = json.loads(Path("data/derived/consolidated_snapshot_report.json").read_text())
    candidates = [r for r in report["documents"] if docs.intersection(r["target_ids"])]
    return benchmark, candidates


def fetch(candidates):
    metadata = {r["id"]: r["files"] for r in rows(ROOT / "related_files.jsonl")}
    log = []

    def get(url):
        # No redirects outside the public portal, including protocol changes.
        class PortalRedirect(urllib.request.HTTPRedirectHandler):
            def redirect_request(self, req, fp, code, msg, headers, newurl):
                if not newurl.startswith(PORTAL):
                    raise ValueError("redirect outside allowed portal")
                return super().redirect_request(req, fp, code, msg, headers, newurl)
        try:
            with urllib.request.build_opener(PortalRedirect).open(
                urllib.request.Request(url, headers=HEADERS), timeout=60
            ) as response:
                content = response.read(40 * 1024 * 1024 + 1)
                if len(content) > 40 * 1024 * 1024:
                    raise ValueError("file exceeds 40 MiB")
                return content
        finally:
            time.sleep(1.5)

    for candidate in candidates:
        sid = candidate["consolidated_document_id"].split(":", 1)[1]
        path = ROOT / "pdf" / sid / "source.pdf"
        if path.exists():
            continue
        try:
            if sid not in metadata:
                url = PORTAL + urllib.parse.quote(sid, safe="") + "/related-file"
                metadata[sid] = json.loads(get(url)).get("data") or []
                with (ROOT / "related_files.jsonl").open("a", encoding="utf-8") as stream:
                    stream.write(json.dumps({"id": sid, "files": metadata[sid]}, ensure_ascii=False) + "\n")
            names = [f["fileName"] for f in metadata[sid] if f["fileName"].lower().endswith(".pdf")]
            if not names:
                log.append({"id": sid, "status": "no_pdf"})
                continue
            name = sorted(names, key=lambda n: (n.startswith("tvVanBanGoc"), n))[0]
            url = PORTAL + "minio/buckets/vbpl/" + urllib.parse.quote(sid, safe="") + "/" + urllib.parse.quote(name, safe="") + "/download"
            content = get(url)
            if not content.startswith(b"%PDF"):
                raise ValueError("not a PDF")
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("xb") as stream:
                stream.write(content)
            log.append({"id": sid, "status": "downloaded", "file": name, "url": url,
                        "bytes": len(content), "sha256": sha(path)})
        except Exception as exc:
            log.append({"id": sid, "status": "stopped", "error": str(exc)})
            break
    # Append so a resumed fetch never loses the preceding audit trail.
    with (ROOT / "c7_downloads.jsonl").open("a", encoding="utf-8") as stream:
        for row in log:
            stream.write(json.dumps(row, ensure_ascii=False) + "\n")
    return dict(Counter(r["status"] for r in log))


def pdf_units(text):
    """Numbered structure only; never align by resemblance to graph wording.

    Preserve complete own text of Article/Clause/Point, excluding child text.
    Footnote blocks below a page separator or a numbered explanatory note are
    excluded. Ambiguous duplicate keys remain excluded, never pick the best.
    """
    found = defaultdict(list)
    preamble = []
    article = clause = None
    current = None
    parts = []
    notes = []

    def flush():
        nonlocal current, parts
        if current and parts:
            found[current].append(norm(" ".join(parts)))
        current, parts = None, []

    for page in text.split("\f"):
        in_note = False
        for raw in page.splitlines():
            line = norm(raw)
            if not line or re.fullmatch(r"\d{1,3}", line):
                continue
            if re.match(r"^[_─—-]{5,}$", line) or NOTE.match(line):
                in_note = True
            if in_note:
                notes.append(line)
                continue
            if re.match(r"^(?:Nơi nhận\s*:|Phụ lục\b)", line, re.I):
                flush()
                return dict(found), norm(" ".join(preamble)), notes
            a, c, p = ARTICLE.match(line), CLAUSE.match(line), POINT.match(line)
            if a:
                flush()
                article, clause = a[1].lower(), None
                current = (article, None, None)
            elif SECTION.match(line):
                flush()
                continue
            elif article and c:
                flush()
                clause = c[1].lower()
                current = (article, clause, None)
            elif article and clause and p:
                flush()
                current = (article, clause, p[1].lower())
            if article is None:
                preamble.append(line)
            elif current:
                parts.append(line)
    flush()
    return dict(found), norm(" ".join(preamble)), notes


def date_evidence(text, issued):
    """Require issueDate in the PDF's certification header or closing block.

    Header date proves certification date, NOT that every incorporated change
    was already effective. Future effective dates in preamble are quarantined.
    """
    header = norm(re.split(r"(?m)^\s*Điều\s+\d", text, maxsplit=1)[0])
    normalized = norm(text)
    dates = []
    for m in DATE.finditer(normalized):
        try:
            d = date(int(m[3]), int(m[2]), int(m[1])).isoformat()
        except ValueError:
            continue
        before = normalized[max(0, m.start()-350):m.start()]
        nearby = normalized[max(0, m.start()-600):m.end()+200]
        certification = bool(re.search(r"Hà\s+Nội\s*,?\s*$", before, re.I)
                             and ("xác thực văn bản hợp nhất" in nearby.lower() or "VBHN" in nearby))
        dates.append({"date": d, "quote": nearby, "offset": m.start(),
                      "certification": certification, "in_preamble": m.start() < len(header)})
    # A cited act's issue/effective date is never evidence of certification.
    verified = bool(issued and any(x["date"] == issued and x["certification"] for x in dates))
    future = [x for x in dates if issued and x["date"] > issued and x["in_preamble"]]
    return {"issueDate": issued, "certification_verified": verified, "dates": dates,
            "future_effective_dates": future, "usable": verified and not future}


def key_for(pid, provisions):
    parts = {}
    while pid and pid in provisions:
        p = provisions[pid]
        m = re.fullmatch(r"(Điều|Khoản|Điểm)\s+(\d+[a-zđ]?|[a-zđ])", p.title, re.I)
        if m:
            parts[m[1].lower()] = m[2].lower()
        pid = p.parent_id
    if "điều" not in parts:
        return None
    return (parts["điều"], parts.get("khoản"), parts.get("điểm"))


def classify(source, selected, versions):
    """Full-string scores are descriptive; only exact evidence diagnoses version.

    Minor differences require identical word/number tokens, preserving numeric
    separators. Similarity alone never establishes a legal wording match.
    """
    a = norm(source)
    scores = [{"version_id": v.id, "text": v.text,
               "ratio": difflib.SequenceMatcher(None, a, norm(v.text), autojunk=False).ratio()}
              for v in versions]
    chosen = next((s for s in scores if selected and s["version_id"] == selected.id), None)
    exact = [s["version_id"] for s in scores if norm(s["text"]) == a]
    tokens = lambda s: re.findall(r"\d+(?:[.,/:-]\d+)*|[^\W_]+", norm(s))
    if chosen and selected.id in exact:
        category = "khop"
    elif exact and selected and selected.id not in exact:
        category = "chon_sai_phien_ban"
    elif chosen and tokens(a) == tokens(chosen["text"]):
        category = "khac_nho"
    else:
        category = "can_nguoi_xem"
    best = max((s["ratio"] for s in scores), default=None)
    relation = ("no_selected_text" if not chosen else
                "selected_tied_best" if chosen["ratio"] == best and sum(s["ratio"] == best for s in scores) > 1 else
                "selected_best" if chosen["ratio"] == best else "other_closer")
    return {"category": category, "source_text": source, "versions": scores,
            "selected_version_id": selected.id if selected else None,
            "nearest_relation": relation, "exact_version_ids": exact}


def wilson(k, n):
    if not n:
        return None
    z = 1.959963984540054
    den = 1 + z*z/n
    center = (k/n + z*z/(2*n))/den
    radius = z*((k/n*(1-k/n)/n + z*z/(4*n*n))**0.5)/den
    return [center-radius, center+radius]


def text_statistics(details):
    # Keep unresolved wording differences in the denominator when both full
    # texts were compared. Dropping them would select on the match outcome.
    compared = [d for d in details if d.get("selected_version_id")
                and d.get("reason") == "full_own_text_structural_alignment"
                and d["category"] != "dau_bai_bo"]
    matches = sum(d["category"] in {"khop", "khac_nho"} for d in compared)
    return {"comparable": len(compared), "matches": matches,
            "unresolved_comparable": sum(d["category"] == "can_nguoi_xem" for d in compared),
            "match_rate": matches / len(compared) if compared else None,
            "wilson95": wilson(matches, len(compared))}


def repeal_state(snapshot, state, at):
    if snapshot.validity.valid:
        return "lech"
    reason = snapshot.validity.reason.value if snapshot.validity.reason else None
    if reason == "parent_invalid" and snapshot.validity.invalid_ancestor_id:
        snapshot = SnapshotService(state).snapshot(snapshot.validity.invalid_ancestor_id, at)
        reason = snapshot.validity.reason.value if snapshot.validity.reason else None
    return "khop" if reason in {"provision_repealed", "document_expired"} else "can_nguoi_xem"


def load_readonly_states(index, bases):
    states, owner = {}, {}
    for base in sorted(bases):
        state = TemporalState()
        state.add_document(index.document(base))
        for p in _parents_first(index.document_order(base)):
            state.add_provision(p)
            owner[p.id] = base
        states[base] = state
    # Stream the authoritative full histories; do not load the 1 GiB file.
    for row in rows(Path("data/derived/versions.jsonl")):
        if row["provision_id"] in owner and row["valid_from"]:
            states[owner[row["provision_id"]]].add_version(_version(row))
    events = defaultdict(set)
    for base, state in states.items():
        for version in state.versions:
            for eid in (version.created_by_event_id, version.ended_by_event_id):
                if eid:
                    events[eid].add(base)
    for row in rows(Path("data/derived/provision_events.jsonl")):
        if row["id"] not in events:
            continue
        targets = tuple(dict.fromkeys(item for item in (
            row.get("target_provision_id"),
            *(u["target_provision_id"] for u in row.get("text_updates", ())),
            *(i["provision_id"] for i in row.get("insertions", ())),
        ) if item))
        event = LegalEvent(id=row["id"], operation=LegalOperation(row["operation"]),
                           source_document_id=row["actor_id"], target_document_id=row["target_document_id"],
                           effective_on=date.fromisoformat(row["effective_on"]),
                           target_provision_ids=targets,
                           status=EventStatus(row["status"]))
        for base in events.pop(row["id"]):
            states[base].record_applied_event(event)
    if events:
        raise ValueError("referenced graph events missing")
    return states


def audit(index, benchmark, candidates):
    sources = []
    for row in candidates:
        sid = row["consolidated_document_id"].split(":", 1)[1]
        record = {"id": sid, "candidate_targets": row["target_ids"]}
        path = ROOT / "pdf" / sid / "source.pdf"
        if not path.exists():
            record["status"] = "khong_co_pdf"
            sources.append(record)
            continue
        result = subprocess.run(["pdftotext", "-layout", str(path), "-"],
                                capture_output=True, text=True, timeout=180, check=True)
        text = result.stdout
        (ROOT / "text").mkdir(exist_ok=True)
        (ROOT / "text" / f"{sid}.txt").write_text(text, encoding="utf-8")
        record.update(pdf_sha256=sha(path), chars=len(text.strip()))
        if len(text.strip()) < 50:
            record["status"] = "pdf_khong_lop_chu"
            sources.append(record)
            continue
        units, preamble, notes = pdf_units(text)
        numbers = {t.split(":", 1)[1]: index.document(t).number for t in row["target_ids"] if index.document(t)}
        # Even a single target must be independently cited in PDF preamble.
        selected, method = select_base_target(numbers, preamble)
        if selected and select_base_target({**numbers, "__sentinel__": "__absent__"}, preamble)[0] != selected:
            selected = None
        raw = json.loads((Path("data/raw") / f"{sid}.json").read_text())
        issued = (raw.get("issueDate") or "")[:10] or None
        evidence = date_evidence(text, issued)
        record.update(base=f"document:{selected}" if selected else None, selection_method=method,
                      date_evidence=evidence, preamble=preamble, notes=notes,
                      status="ready" if selected and units and evidence["usable"] else "can_nguoi_xem")
        record["_units"] = units
        sources.append(record)
    bases = {s["base"] for s in sources if s.get("base") and any(r["document_id"] == s["base"] for r in benchmark)}
    states = load_readonly_states(index, bases)
    details, repeal = [], []
    for s in sources:
        related = [r for r in benchmark if r["document_id"] == s.get("base")]
        if not s.get("base"):
            related = [r for r in benchmark if r["document_id"] in s["candidate_targets"]]
        state = states.get(s.get("base"))
        provisions = {p.id: p for p in state.provisions} if state else {}
        key_counts = Counter(key_for(pid, provisions) for pid in provisions)
        at = s.get("date_evidence", {}).get("issueDate")
        units = s.get("_units", {})
        for pid in sorted({r["lineage_id"] for r in related}):
            members = [dict(r) for r in related if r["lineage_id"] == pid]
            item = {"vbhn_id": s["id"], "lineage_id": pid, "base": s.get("base"), "at": at,
                    "benchmark_rows": members, "category": "can_nguoi_xem", "reason": s["status"]}
            key = key_for(pid, provisions)
            item["key"] = key
            source = units.get(key, [])
            if s["status"] in {"pdf_khong_lop_chu", "khong_co_pdf"}:
                item["category"] = s["status"]
            elif not key or key_counts[key] != 1 or len(source) != 1:
                item.update(category="khong_can_duoc", reason="missing_or_ambiguous_structural_key")
            elif s["status"] == "ready":
                snapshot = SnapshotService(state).snapshot(pid, date.fromisoformat(at))
                chain = state.chain(pid)
                versions = chain.versions if chain else ()
                item.update(classify(source[0], snapshot.version, versions))
                item["validity_reason"] = snapshot.validity.reason.value if snapshot.validity.reason else None
                item["reason"] = "full_own_text_structural_alignment"
                # State markers must describe the entire unit, not a quoted repeal.
                if re.search(r"(?:\(\s*(?:được\s+)?bãi bỏ\s*\)|[.:)]\s*(?:được\s+)?bãi bỏ\s*[.\d]*$)", source[0], re.I):
                    item.update(category="dau_bai_bo", repeal_state=repeal_state(snapshot, state, date.fromisoformat(at)))
                # A benchmark row is date-covered only if its actual answer
                # version is selected here; equality of dates reported too.
                for member in members:
                    member["same_date"] = member["as_of"] == at
                    member["same_selected_version"] = bool(snapshot.version and member["benchmark_version_id"] == snapshot.version.id)
                    original = SnapshotService(state).snapshot(pid, date.fromisoformat(member["as_of"]))
                    member["same_repeal_state"] = (
                        item["category"] == "dau_bai_bo"
                        and repeal_state(snapshot, state, date.fromisoformat(at)) == "khop"
                        and repeal_state(original, state, date.fromisoformat(member["as_of"])) == "khop"
                        and original.validity.caused_by_event_id == snapshot.validity.caused_by_event_id
                        and original.validity.invalid_ancestor_id == snapshot.validity.invalid_ancestor_id
                    )
                if not snapshot.validity.valid and item["category"] != "dau_bai_bo":
                    item["category"] = "can_nguoi_xem"
            if item["category"] == "can_nguoi_xem" and source:
                item.setdefault("source_text", source)
            details.append(item)
        # Also inspect all aligned repeal markers in the relevant base, not
        # just the benchmark targets; report separately to avoid mixing units.
        if s["status"] == "ready" and state:
            for pid in provisions:
                key = key_for(pid, provisions)
                source = units.get(key, [])
                if key_counts[key] != 1 or len(source) != 1:
                    continue
                if not re.search(r"\(\s*(?:được\s+)?bãi bỏ\s*\)", source[0], re.I):
                    continue
                snap = SnapshotService(state).snapshot(pid, date.fromisoformat(at))
                reason = snap.validity.reason.value if snap.validity.reason else None
                repeal.append({"vbhn_id": s["id"], "lineage_id": pid, "at": at,
                               "source_text": source[0], "validity_reason": reason,
                               "status": repeal_state(snap, state, date.fromisoformat(at))})
    with (ROOT / "doi_chieu_chi_tiet.jsonl").open("w", encoding="utf-8") as stream:
        for item in details:
            stream.write(json.dumps(item, ensure_ascii=False) + "\n")
    write_json(ROOT / "c7_sources.json", [{k: v for k, v in s.items() if k != "_units"} for s in sources])
    write_json(ROOT / "c7_repeal.json", repeal)
    counts = Counter(r["category"] for r in details)
    coverage = {}
    for dataset in DATASETS:
        rr = [r for r in benchmark if r["dataset"] == dataset]
        dd = [d for d in details if any(r["dataset"] == dataset for r in d["benchmark_rows"])]
        confirmed = [d for d in dd if d.get("base") and next(s for s in sources if s["id"] == d["vbhn_id"]).get("date_evidence", {}).get("usable")]
        covered = {r["row_id"] for d in confirmed for r in d["benchmark_rows"] if r["dataset"] == dataset and r.get("same_selected_version")}
        aligned = [d for d in dd if d.get("reason") == "full_own_text_structural_alignment"]
        coverage[dataset] = {"rows": len(rr), "lineages": len({r["lineage_id"] for r in rr}),
                             "candidate_lineages": len({d["lineage_id"] for d in dd}),
                             "confirmed_lineages": len({d["lineage_id"] for d in confirmed}),
                             "aligned_lineages": len({d["lineage_id"] for d in aligned}),
                             "version_covered_rows": len(covered),
                             "version_covered_lineages": len({r["lineage_id"] for r in rr if r["row_id"] in covered}),
                             "version_covered_points": len({(r["lineage_id"], r["as_of"]) for r in rr if r["row_id"] in covered}),
                             "repeal_covered_rows": len({r["row_id"] for d in confirmed for r in d["benchmark_rows"] if r["dataset"] == dataset and r.get("same_repeal_state")}),
                             "exact_date_rows": len({r["row_id"] for d in confirmed for r in d["benchmark_rows"] if r["dataset"] == dataset and r.get("same_date")})}
    summary = {"coverage": coverage, "candidate_sources": len(candidates),
               "source_statuses": dict(Counter(s["status"] for s in sources)),
               "pairs": len(details), "categories": dict(counts), **text_statistics(details),
               "nearest": dict(Counter(d["nearest_relation"] for d in details if "nearest_relation" in d)),
               "repeal": dict(Counter(r["status"] for r in repeal))}
    write_json(ROOT / "c7_summary.json", summary)
    paths = [*DATASETS.values(), Path("data/temporal.sqlite"), Path("data/derived/versions.jsonl"),
             Path("data/derived/provision_events.jsonl"), Path("data/derived/consolidated_snapshot_report.json"),
             ROOT / "related_files.jsonl", Path(__file__),
             *(Path("data/raw") / f"{s['id']}.json" for s in sources),
             *(ROOT / "pdf" / s["id"] / "source.pdf" for s in sources if "pdf_sha256" in s)]
    (ROOT / "c7.sha256").write_text("".join(f"{sha(p)}  {p}\n" for p in paths), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fetch", action="store_true", help="download missing PDFs serially, then stop")
    args = parser.parse_args()
    ROOT.mkdir(exist_ok=True)
    with ReadOnlyIndex("data/temporal.sqlite") as index:
        benchmark, candidates = discover(index)
        if args.fetch:
            print(json.dumps(fetch(candidates)))
        else:
            audit(index, benchmark, candidates)


if __name__ == "__main__":
    main()

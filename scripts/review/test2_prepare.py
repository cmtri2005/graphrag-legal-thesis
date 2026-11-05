#!/usr/bin/env python3
"""Prepare test2 short-answer tasks and the shared, unlabelled A/B worksheet.

Uses the approved test2 plan and annotation card 4.0. Never reads A/B labels,
changes v1.0, or treats model output as a human verification.

  shortpack --questions questions_test2.jsonl --out new_directory
  worksheet --questions questions_test2.jsonl --shorts short_answers_test2.jsonl
            --evidence evidence.jsonl evidence_2.jsonl --out worksheet.jsonl

Short answers use the existing {lineage_id,version_id,short_answer,by,at} schema.
The worksheet contains every boundary date of each question; batch selection
and release/freeze are subsequent steps, not implied by preparing this file.
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "pipeline"))
from enrich_vilextime import check_short_answer, norm
from generate_questions import user_prompt
from test2_packs import judge_question, lineage_rows, published_scope, stratum


def jsonl(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def write_new(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as f:
        f.writelines(json.dumps(r, ensure_ascii=False) + "\n" for r in rows)


def inputs(data: Path, path: Path) -> tuple[dict[str, dict], dict[str, list[dict]]]:
    questions = {}
    for r in jsonl(path):
        lid = r["lineage_id"]
        if lid in questions:
            raise ValueError(f"{lid}: câu hỏi trùng; chọn một kết quả qcheck duy nhất.")
        if r.get("question") and not r.get("rejected_reason"):
            questions[lid] = r
    rows = lineage_rows(data, set(questions))
    used, dev_docs = published_scope(data)
    for lid, q in questions.items():
        if lid not in rows:
            raise ValueError(f"{lid}: không có chuỗi phiên bản; dựng lại đầu vào test2.")
        rs = rows[lid]
        if lid in used or rs[0]["target"]["document_id"] in dev_docs:
            raise ValueError(f"{lid}: trùng lineage v1.0 hoặc văn bản dev; plan vilextime-test2.md "
                             "không cho vào test2. Bỏ ứng viên này, giữ nguyên nhật ký rút mẫu.")
        if q.get("group") != rs[0]["group"]:
            raise ValueError(f"{lid}: nhóm câu hỏi khác chuỗi phiên bản; kiểm lại qcheck.")
        _, context, versions = user_prompt(rs)
        if reason := judge_question(q["question"], context, versions):
            raise ValueError(f"{lid}: câu hỏi không qua kiểm hiện tại ({reason}); chạy qcheck và viết lại.")
        if not q.get("model") or not q.get("provider") or not q.get("prompt_sha"):
            raise ValueError(f"{lid}: thiếu nguồn model/prompt; dùng kết quả qcheck có provenance.")
    return questions, rows


def shortpack(data: Path, questions_path: Path, out: Path) -> dict:
    questions, rows = inputs(data, questions_path)
    records = []
    for lid, q in questions.items():
        versions = {}
        for r in rows[lid]:
            if r["answerable"]:
                key = r["version_id"]
                value = (r["answer"], r["target"].get("lead_in"))
                if key in versions and versions[key] != value:
                    raise ValueError(f"{lid}/{key}: lời văn không thống nhất; kiểm chuỗi phiên bản.")
                versions[key] = value
        records.append({"lineage_id": lid, "group": q["group"], "question": q["question"],
                        "versions": [{"version_id": v, "answer": text, "lead_in": lead}
                                     for v, (text, lead) in versions.items()]})
    out.mkdir(parents=True, exist_ok=False)
    write_new(out / "tasks.jsonl", records)
    instruction = (
        "# Đáp án ngắn ViLexTime test2\n\n"
        "Chỉ đọc tasks.jsonl trong thư mục này. Với mỗi câu hỏi và mỗi phiên bản, chọn đoạn nguyên văn "
        "trả lời đúng và đủ điều được hỏi từ answer hoặc lead_in. Không sửa lời luật hay version_id. "
        "Có thể nối nhiều đoạn bằng ` … `. Không chọn lại đáp án cũ chỉ vì cùng version_id: câu hỏi đã đổi. "
        "T2: đáp án ngắn của mỗi bản không được nằm trong bản kia. T3: cần ít nhất ba đáp án khác nhau. "
        "Không đủ khác biệt thì ghi null kèm note, không thêm lời luật không có trong nguồn. "
        "Ghi answers.jsonl theo schema {lineage_id,version_id,short_answer,by,at}; by là model thực tế, "
        "at là ngày thực tế. Không gán nhãn Q1–Q4 hay tự xác nhận đã được người kiểm. "
        "Không tìm được đoạn đủ trả lời thì ghi short_answer=null kèm note để người biên soạn xem lại; "
        "không bịa đáp án. Quy tắc: docs/vilextime-dinh-nghia.md §6.8, §8; thẻ 4.0 Q1.\n")
    (out / "AGENTS.md").write_text(instruction, encoding="utf-8")
    return {"questions": len(records), "versions": sum(len(r["versions"]) for r in records)}


def source_links(data: Path, evidence: dict[str, dict], *, strict: bool = True) -> None:
    """Recover original actor URLs from document metadata without inventing links."""
    by_number = collections.defaultdict(list)
    db_path = (data / "temporal.sqlite").resolve()
    with sqlite3.connect(db_path.as_uri() + "?mode=ro", uri=True) as db:
        for number, title, issued, url, doc_id in db.execute(
                "SELECT number, title, issued_on, source_url, id FROM documents"):
            by_number[number].append({"title": title, "issued": issued, "source_url": url, "document_id": doc_id})
    for ev in evidence.values():
        for a in ev["actors"]:
            if a.get("source_url"):
                continue
            candidates = by_number.get(a.get("document"), [])
            for field in ("issued", "title"):
                if a.get(field) and (matches := [d for d in candidates if d[field] == a[field]]):
                    candidates = matches
            urls = {d["source_url"] for d in candidates if d["source_url"]}
            if len(urls) != 1:
                if not strict:
                    ev.setdefault("missing", []).append(f"actor_url:{a.get('document')}")
                    continue
                raise ValueError(f"{ev['id']}/{a.get('document')}: chưa xác định duy nhất link văn bản tác động; "
                                 "đối chiếu metadata và bổ sung source_url trước khi gán Q1.")
            a["source_url"] = next(iter(urls))


def contrast_problems(group: str, rows: list[dict], shorts: dict[tuple[str, str], dict]) -> list[str]:
    """Necessary extractive-answer checks from definition §4; not a human verdict.

    T2's short answer must not occur in the other version. T3 needs at least
    three different answers. Semantic correctness still belongs to Q1/Q2.
    """
    versions = {r["version_id"]: r for r in rows if r["answerable"]}
    errors, answers = [], {}
    for vid, row in versions.items():
        short = shorts.get((row["lineage_id"], vid), {}).get("short_answer")
        if not short or not check_short_answer(short, row["answer"], row["target"].get("lead_in")):
            errors.append(f"{vid}: thiếu đáp án ngắn trích đúng lời văn")
        else:
            answers[vid] = short
    required = {"T2": 2, "T3": 3, "T6": 1}[group]
    distinct = len({norm(s) for s in answers.values()})
    if group == "T2" and distinct != 2:
        errors.append("T2: cần đúng 2 đáp án ngắn khác nhau (định nghĩa §4)")
    elif distinct < required:
        errors.append(f"{group}: cần ít nhất {required} đáp án ngắn khác nhau (định nghĩa §4)")
    if group == "T2":
        for vid, short in answers.items():
            for other_id, other in versions.items():
                if other_id != vid and check_short_answer(short, other["answer"], other["target"].get("lead_in")):
                    errors.append(f"{vid}: đáp án ngắn cũng nằm trong {other_id} (định nghĩa §4 T2)")
    return errors


def contrast_audit(data: Path, questions_path: Path, short_paths: list[Path], out: Path) -> dict:
    questions, rows = inputs(data, questions_path)
    shorts = {}
    for path in short_paths:
        for s in jsonl(path):
            key = (s["lineage_id"], s["version_id"])
            if key in shorts:
                raise ValueError(f"{key}: đáp án ngắn trùng; chọn một bản chốt.")
            shorts[key] = s
    findings = [{"lineage_id": lid, "group": q["group"], "problems": problems}
                for lid, q in questions.items() if (problems := contrast_problems(q["group"], rows[lid], shorts))]
    report = {"status": "machine_check_only_not_human_validation", "questions": len(questions),
              "without_detected_problem": len(questions) - len(findings), "needs_review": len(findings),
              "findings": findings, "authority": "docs/vilextime-dinh-nghia.md §4",
              "inputs_sha256": {str(path): hashlib.sha256(path.read_bytes()).hexdigest()
                                for path in [questions_path, *short_paths]}}
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("x", encoding="utf-8") as f:
        f.write(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    return {k: v for k, v in report.items() if k != "findings"}


def prepare_records(questions: dict, rows: dict, shorts: dict, evidence: dict,
                    *, strict: bool = True) -> tuple[list[dict], list[dict]]:
    """Shared v3 assembly. Existing silver is audited, never filtered or repaired."""
    result, thieu = [], []
    for lid, q in questions.items():
        prepared, actors, base = [], {}, None
        for source in rows[lid]:
            r = {k: v for k, v in source.items() if k not in ("review", "question_source")}
            r["question"] = q["question"]
            if strict:
                r["question_source"] = {"kind": "llm", **{k: q[k] for k in ("provider", "model", "prompt_sha")}}
                r["question_source"].update({k: q[k] for k in ("edited_by", "edited_at") if k in q})
            r["as_of_strategy"] = "ranh_gioi"
            r["short_answer"] = None
            if r["answerable"]:
                s = shorts.get((lid, r["version_id"]))
                if not s or not str(s.get("short_answer") or "").strip() or (strict and (not s.get("by") or not s.get("at"))):
                    if strict:
                        raise ValueError(f"{lid}/{r['version_id']}: thiếu đáp án ngắn có nguồn; làm shortpack trước Q1.")
                    thieu.append({"lineage_id": lid, "row_id": r["id"], "field": "short_answer"})
                    s = {"short_answer": None, "by": "", "at": ""}
                if strict and not check_short_answer(s["short_answer"], r["answer"], r["target"].get("lead_in")):
                    raise ValueError(f"{lid}/{r['version_id']}: đáp án ngắn không là trích đoạn; kiểm lại lời văn.")
                r["short_answer"] = s["short_answer"]
                if s.get("by") and s.get("at"):
                    r["short_answer_source"] = {"by": s["by"], "at": s["at"]}
            if r["id"] not in evidence and strict:
                raise ValueError(f"{r['id']}: thiếu trích văn bản gốc/tác động; chạy crosscheck_evidence.py.")
            ev = evidence.get(r["id"], {"base": {}, "actors": [], "missing": ["sources"]})
            missing = list(ev.get("missing", []))
            if not ev.get("base", {}).get("passage"):
                missing.append("base_passage")
            if not source.get("source_url"):
                missing.append("base_url")
            if not ev.get("actors"):
                missing.append("actors")
            if missing:
                thieu.append({"lineage_id": lid, "row_id": r["id"], "field": "sources",
                              "missing": sorted(set(missing))})
            base = base or {**ev["base"], "source_url": r.get("source_url")}
            for a in ev["actors"]:
                # Keep raw passages, including effective-date and transitional clauses.
                actors[json.dumps(a, ensure_ascii=False, sort_keys=True)] = a
            r["source_missing"] = ev.get("missing", [])
            prepared.append(r)
        if strict and (problems := contrast_problems(q["group"], prepared, shorts)):
            raise ValueError(f"{lid}: {'; '.join(problems)}. Rà đáp án/câu hỏi trước khi đưa cho A/B; "
                             "không sửa lời luật để tạo khác biệt.")
        result.append({"lineage_id": lid, "group": q["group"], "stratum": stratum(rows[lid][0]),
                       "question": q["question"], "rows": prepared,
                       "sources": {"base": base, "actors": list(actors.values())}})
    return result, thieu


def worksheet(data: Path, questions_path: Path, short_paths: list[Path], evidence_paths: list[Path], out: Path) -> dict:
    manifest_path = out.with_suffix(".manifest.json")
    for path in (out, manifest_path):
        if path.exists():
            raise FileExistsError(f"{path} đã có; dùng đường dẫn mới để giữ nguyên phiếu và nhãn cũ.")
    questions, rows = inputs(data, questions_path)
    shorts = {}
    for path in short_paths:
        for r in jsonl(path):
            key = (r["lineage_id"], r["version_id"])
            if key in shorts:
                raise ValueError(f"{key}: đáp án ngắn trùng; dùng một bản chốt cho mỗi phiên bản.")
            shorts[key] = r
    evidence = {}
    for path in evidence_paths:
        for e in jsonl(path):
            if e["id"] in evidence and evidence[e["id"]] != e:
                raise ValueError(f"{e['id']}: hai trích nguồn khác nhau; chọn snapshot bằng chứng duy nhất.")
            evidence[e["id"]] = e
    wanted_ids = {r["id"] for rs in rows.values() for r in rs}
    evidence = {i: e for i, e in evidence.items() if i in wanted_ids}
    source_links(data, evidence)

    result, _ = prepare_records(questions, rows, shorts, evidence)
    write_new(out, result)
    manifest = {"status": "unlabelled_candidates", "guideline_version": "4.0", "questions": len(result),
                "boundary_rows": sum(len(r["rows"]) for r in result),
                "groups": dict(collections.Counter(r["group"] for r in result)),
                "sha256": hashlib.sha256(out.read_bytes()).hexdigest(),
                "pending": ["pilot selection and lawyer approval", "independent A/B labels", "agreement gate",
                            "lawyer adjudication", "release and preregistration amendment"]}
    with manifest_path.open("x", encoding="utf-8") as f:
        f.write(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    return manifest


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("command", choices=("shortpack", "worksheet", "contrast"))
    ap.add_argument("--data", type=Path, default=Path("data"))
    ap.add_argument("--questions", type=Path, required=True)
    ap.add_argument("--shorts", type=Path, nargs="+", default=[])
    ap.add_argument("--evidence", type=Path, nargs="+", default=[])
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    try:
        if args.command == "shortpack":
            result = shortpack(args.data, args.questions, args.out)
        elif args.command == "contrast":
            result = contrast_audit(args.data, args.questions, args.shorts, args.out)
        else:
            result = worksheet(args.data, args.questions, args.shorts, args.evidence, args.out)
    except (ValueError, FileExistsError) as e:
        raise SystemExit(str(e)) from e
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

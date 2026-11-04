#!/usr/bin/env python3
"""ViLexTime test 2: gán lại bằng lời dặn v2 làm phép kiểm độ nhạy (ADR 0005, amendment 04/11 mục (b)).

    test2_relabel.py build calib --out DIR --key KEY.tsv   # dòng người kiểm độc lập; khóa nằm ngoài DIR
    test2_relabel.py build test2 --out DIR
    test2_relabel.py collect --tasks DIR --who "LLM-A (...)" --out A.tsv LABELS.jsonl...
    test2_relabel.py score --key KEY.tsv --out R.json A.tsv B.tsv SILVER.tsv
    test2_relabel.py adj --tasks DIR --a A.tsv --b B.tsv --out ADJ_DIR
    test2_relabel.py silver --a A.tsv --b B.tsv --adj ADJ.tsv --out SILVER.tsv
    test2_relabel.py subset --release R.jsonl --silver SILVER.tsv --out SUB.jsonl

Gói chỉ có câu hỏi, đáp án và bằng chứng máy dựng; không có khóa, nhãn hay kết quả hệ thống.
"""
from __future__ import annotations

import argparse
import collections
import csv
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "scripts/pipeline"), str(Path(__file__).parent)]
csv.field_size_limit(sys.maxsize)

from crosscheck import AC1_TARGET, PNEG_TARGET, gwet_ac1, specific_agreement  # noqa: E402
from test2_labels import FIELDS, GOOD, GUIDELINE, read_labels, validate_label, worksheet_sha256  # noqa: E402
from test2_packs import independent, stratum  # noqa: E402

CHUNK = 12
GROUPS = ("T2", "T3", "T6")
ROW_KEYS = ("as_of", "answerable", "answer", "short_answer", "valid_from", "valid_to")
PROMPT, PROMPT_ADJ = ROOT / "prompts/vilextime/test2_gan_v2.md", ROOT / "prompts/vilextime/test2_hoa_giai_v2.md"
# Annotation guide §4 uses this lineage as a worked example, and so does the prompt: it cannot also be scored.
EXAMPLES = {("23/2016/NĐ-CP", "Điểm a Khoản 1 Điều 23")}


def jsonl(path: Path) -> list[dict]:
    return [json.loads(s) for s in path.read_text(encoding="utf-8").splitlines() if s.strip()]


def truth_of(reviews: list[dict], need: int) -> str | None:
    """Question-level truth: every boundary row independently labelled; one bad row makes the question bad."""
    if len(reviews) < need or not all(independent(r) for r in reviews):
        return None
    return "khong_dat" if any(r["verdict"] == "khong_dat" for r in reviews) else "dat"


def with_ops(rows: list[dict], data: Path) -> None:
    need = {t["event_id"] for r in rows for t in (r.get("derivation") or {}).get("transitions") or ()}
    ops = {e["id"]: e["operation"] for e in map(json.loads, (data / "derived/provision_events.jsonl").open(encoding="utf-8"))
           if e["id"] in need}
    for r in rows:
        for t in (r.get("derivation") or {}).get("transitions") or ():
            t["op"] = ops.get(t["event_id"])


def task(record: dict, corpus) -> dict:
    """One task. Same evidence for both labellers: version chain with diffs, and where else to look."""
    from kiem_hints import hints, in_force
    rows = sorted(record["rows"], key=lambda r: r["as_of"])
    with_ops(rows, ROOT / "data")
    first = hints(rows, corpus)[rows[0]["id"]]
    similar = ""
    if record["group"] != "T6":
        last = rows[-1]
        same, other = in_force(corpus, record["lineage_id"], f"{record['question']} {last['answer'] or ''}", last["as_of"],
                               last["target"].get("document_id"), "")
        similar = "\n".join(same + other)
    return {"lineage_id": record["lineage_id"], "group": record["group"], "loai": record["stratum"], "question": record["question"],
            "rows": [{**{k: r.get(k) for k in ROW_KEYS}, "cau_dan": r["target"].get("lead_in")} for r in rows],
            "cac_phien_ban": first["cac_phien_ban"].replace("   ◀ đáp án của dòng này", ""),
            "goi_y_cho_moi": first["goi_y_cho_moi"], "quy_dinh_tuong_tu": similar, "sources": record["sources"]}


def calib_records(data: Path, evidence_paths: list[Path]) -> tuple[list[dict], dict[str, str]]:
    from export_release import final_labels
    rows = [json.loads(s) for g in GROUPS for s in (data / f"derived/vilextime/{g}.jsonl").open(encoding="utf-8")]
    lineages: dict[str, list[dict]] = collections.defaultdict(list)
    for r in rows:
        lineages[r["lineage_id"]].append(r)
    lineage_of = {r["id"]: r["lineage_id"] for r in rows}
    reviews: dict[str, list[dict]] = collections.defaultdict(list)
    for i, rev in final_labels(data / "review").items():
        if i in lineage_of:
            reviews[lineage_of[i]].append(rev)
    truth = {l: t for l, revs in reviews.items() if (t := truth_of(revs, len(lineages[l])))}
    truth = {l: t for l, t in truth.items()
             if (lineages[l][0]["target"]["law_id"], lineages[l][0]["target"]["citation"]) not in EXAMPLES}
    questions = {q["lineage_id"]: q for q in jsonl(ROOT / "data/vilextime/questions.jsonl") if q.get("question")}
    shorts = {(s["lineage_id"], s["version_id"]): s["short_answer"] for s in jsonl(ROOT / "data/vilextime/short_answers.jsonl")}
    wanted = {r["id"] for l in truth for r in lineages[l]}
    evidence = {e["id"]: e for p in evidence_paths for e in jsonl(p) if e["id"] in wanted}
    if missing := wanted - evidence.keys():
        raise SystemExit(f"{len(missing)} dòng hiệu chuẩn thiếu trích nguồn, ví dụ {sorted(missing)[0]}; chạy crosscheck_evidence.py.")
    records = []
    for lid in sorted(truth):
        rs, actors = lineages[lid], {}
        for r in rs:
            r["short_answer"] = shorts.get((lid, r.get("version_id")))
            for a in evidence[r["id"]]["actors"]:
                actors[json.dumps(a, ensure_ascii=False, sort_keys=True)] = a
        records.append({"lineage_id": lid, "group": rs[0]["group"], "stratum": stratum(rs[0]), "question": questions[lid]["question"],
                        "rows": rs, "sources": {"base": evidence[rs[0]["id"]]["base"], "actors": list(actors.values())}})
    return records, truth


def install(out: Path, tasks: list[dict], guide: str) -> None:
    out.mkdir(parents=True, exist_ok=False)
    (out / "AGENTS.md").write_text("Chỉ làm việc trong thư mục được giao, theo HUONG_DAN.md.\n", encoding="utf-8")
    (out / "CLAUDE.md").write_text("Chỉ làm việc trong thư mục được giao, theo HUONG_DAN.md.\n", encoding="utf-8")
    for n in range(0, len(tasks), CHUNK):
        d = out / f"chunk_{n // CHUNK + 1:02d}"
        d.mkdir()
        (d / "HUONG_DAN.md").write_text(guide, encoding="utf-8")
        (d / "tasks.jsonl").write_text("".join(json.dumps(t, ensure_ascii=False) + "\n" for t in tasks[n:n + CHUNK]), encoding="utf-8")


def read_tasks(path: Path) -> list[dict]:
    return [t for f in sorted(path.glob("chunk_*/tasks.jsonl")) for t in jsonl(f)]


def build(which: str, out: Path, key: Path | None, evidence: list[Path]) -> None:
    import random
    from vilexgraph.framework.corpus import Corpus
    corpus = Corpus(ROOT / "data/derived/corpus/index.sqlite")
    if which == "calib":
        records, truth = calib_records(ROOT / "data", evidence)
        with key.open("x", encoding="utf-8") as f:
            f.write("lineage_id\tloai\tsu_that\n")
            f.writelines(f"{r['lineage_id']}\t{r['stratum']}\t{truth[r['lineage_id']]}\n" for r in records)
    else:
        records = jsonl(ROOT / "data/review/test2_candidate_worksheet_v3.jsonl")
    random.Random(f"test2-relabel-{which}").shuffle(records)
    tasks = [task(r, corpus) for r in records]
    install(out, tasks, PROMPT.read_text(encoding="utf-8"))
    print(which, len(tasks), collections.Counter(t["loai"] for t in tasks), "gói", -(-len(tasks) // CHUNK))


def collect(tasks_dir: Path, who: str, out: Path, sources: list[Path]) -> list[str]:
    tasks = {t["lineage_id"]: t for t in read_tasks(tasks_dir)}
    rows, problems = {}, []
    for src in sources:
        for body in jsonl(src):
            lid = body.get("lineage_id")
            if lid not in tasks:
                problems.append(f"{lid}: không thuộc gói")
                continue
            label, errors = validate_label(tasks[lid], body)
            if errors:
                problems.append(f"{lid}: {errors}")
                continue
            rows[lid] = {**label, "lineage_id": lid, "labeler": who, "guideline_version": GUIDELINE,
                         "worksheet_sha256": worksheet_sha256(tasks[lid]), "updated_at": ""}
    problems += [f"{lid}: thiếu nhãn" for lid in tasks if lid not in rows]
    write_tsv(out, rows)
    print(f"{who}: {len(rows)}/{len(tasks)} nhãn; {len(problems)} lỗi")
    return problems


def write_tsv(path: Path, rows: dict[str, dict]) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS, delimiter="\t")
        w.writeheader()
        w.writerows(rows.values())


def agreement(x: list[str], y: list[str]) -> dict:
    ac1, pneg = gwet_ac1(x, y), specific_agreement(x, y).get("khong_dat")
    return {"n": len(x), "ac1": ac1, "p_neg": pneg, "dat_chuan": (ac1 or 0) >= AC1_TARGET and (pneg or 0) >= PNEG_TARGET}


def score(key_path: Path, labels: list[Path]) -> dict:
    with key_path.open(encoding="utf-8") as f:
        key = {r["lineage_id"]: r for r in csv.DictReader(f, delimiter="\t")}
    result = {"thresholds": {"ac1": AC1_TARGET, "p_neg": PNEG_TARGET}}
    for p in labels:
        got = read_labels(p)
        if set(got) != set(key):
            raise SystemExit(f"{p}: {len(set(key) ^ set(got))} mục không khớp khóa")
        one = {}
        for name in ("toàn tập", "T2", "T3", "T6"):
            ids = [i for i in key if name == "toàn tập" or key[i]["loai"].startswith(name)]
            one[name] = {**agreement([key[i]["su_that"] for i in ids], [got[i]["verdict"] for i in ids]),
                         "xau": sum(key[i]["su_that"] == "khong_dat" for i in ids)}
        result[p.stem] = one
    return result


def adjudication(tasks_dir: Path, a: dict, b: dict, out: Path) -> None:
    tasks = {t["lineage_id"]: t for t in read_tasks(tasks_dir)}
    keep = (*[k for q in GOOD for k in (q, q + "_reason")], "quote", "search_log", "note")
    picked = []
    for lid in a:
        if any(a[lid][q] != b[lid][q] for q in GOOD):
            pair = [{k: x[lid][k] for k in keep} for x in (a, b)]
            if hashlib.sha256(lid.encode()).digest()[0] & 1:     # keep the order from identifying a model
                pair.reverse()
            picked.append({**tasks[lid], "label_1": pair[0], "label_2": pair[1]})
    install(out, picked, PROMPT.read_text(encoding="utf-8") + PROMPT_ADJ.read_text(encoding="utf-8"))
    print("lệch", len(picked), "/", len(a))


def silver(a: dict, b: dict, adj: dict) -> dict[str, dict]:
    out = {}
    for lid in a:
        split = any(a[lid][q] != b[lid][q] for q in GOOD)
        if split and lid not in adj:
            raise SystemExit(f"{lid}: lệch mà chưa hòa giải")
        out[lid] = {**(adj[lid] if split else a[lid]), "labeler": "LLM-silver-v2 (hòa giải)" if split else "LLM-silver-v2 (A=B)"}
    return out


def subset(release: Path, labels: dict[str, dict], out: Path) -> dict:
    rows = jsonl(release)
    present = {r["lineage_id"] for r in rows}
    if unknown := present - labels.keys():
        raise SystemExit(f"{len(unknown)} lineage của release không có nhãn v2")
    keep = {l for l in present if labels[l]["verdict"] == "dat"}
    kept = [r for r in rows if r["lineage_id"] in keep]
    out.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in kept), encoding="utf-8")
    return {"release_lineage": len(present), "giu": len(keep), "bo": len(present - keep), "dong_giu": len(kept),
            "dat_v2_ngoai_release": sum(1 for l, x in labels.items() if x["verdict"] == "dat" and l not in present),
            "sha256": hashlib.sha256(out.read_bytes()).hexdigest()}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=("build", "collect", "score", "adj", "silver", "subset"))
    ap.add_argument("files", nargs="*")
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--key", type=Path)
    ap.add_argument("--tasks", type=Path)
    ap.add_argument("--who")
    ap.add_argument("--a", type=Path)
    ap.add_argument("--b", type=Path)
    ap.add_argument("--adj", type=Path)
    ap.add_argument("--release", type=Path)
    ap.add_argument("--silver", type=Path)
    ap.add_argument("--evidence", type=Path, nargs="*", default=[])
    args = ap.parse_args()
    if args.cmd == "build":
        build(args.files[0], args.out, args.key, args.evidence)
    elif args.cmd == "collect":
        problems = collect(args.tasks, args.who, args.out, [Path(f) for f in args.files])
        print("\n".join(problems[:30]))
    elif args.cmd == "score":
        r = score(args.key, [Path(f) for f in args.files])
        args.out.write_text(json.dumps(r, ensure_ascii=False, indent=1), encoding="utf-8")
        print(json.dumps(r, ensure_ascii=False, indent=1))
    elif args.cmd == "adj":
        adjudication(args.tasks, read_labels(args.a), read_labels(args.b), args.out)
    elif args.cmd == "silver":
        rows = silver(read_labels(args.a), read_labels(args.b), read_labels(args.adj))
        write_tsv(args.out, rows)
        print(collections.Counter(x["verdict"] for x in rows.values()))
    else:
        print(json.dumps(subset(args.release, read_labels(args.silver), args.out), ensure_ascii=False))


if __name__ == "__main__":
    main()

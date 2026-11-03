#!/usr/bin/env python3
"""ViLexTime bộ test 2 — gói lọc ứng viên cho Claude, và chấm hiệu chuẩn (docs/plans/active/vilextime-test2.md, bước 1–2).

    python scripts/review/test2_packs.py build --out DIR              # DIR ngoài repo; khóa ở DIR/../../key_loc.tsv
    python scripts/review/test2_packs.py build --second --out DIR3    # đợt 2: hiệu chuẩn cũ + ứng viên kế tiếp; nối vào khóa
    python scripts/review/test2_packs.py build --third --out DIR4/packs     # đợt 3 (T2): seed mới, bỏ lineage đã trong khóa
    python scripts/review/test2_packs.py score --out DIR RESULT.tsv [RESULT2.tsv]   # file sau đè file trước
    python scripts/review/test2_packs.py redo --out DIR2 --from DIR RESULT.tsv     # lọc lại sau khi sửa lời dặn
    python scripts/review/test2_packs.py pending --out NEW/packs --from OLD/packs --key KEY RESULT.tsv...  # chỉ mục còn thiếu
    python scripts/review/test2_packs.py qpack --out DIR RESULT.tsv... [--key KEY] [--limit N]   # bước 4: gói viết câu hỏi
    python scripts/review/test2_packs.py qcheck --out DIR --model M ANSWERS.jsonl...  # kiểm; ghi viet_lai và câu đạt

Một mục là một lineage (một câu hỏi tương lai), không phải một dòng. Gói trộn ứng viên mới (rút ngẫu nhiên theo
tầng, bỏ văn bản của split dev và lineage đã có trong v1.0) với lineage v1.0 đã có nhãn cuối của người, theo thứ tự
ngẫu nhiên, nên bên lọc không biết mục nào bị chấm. Gói không có câu hỏi, đáp án ngắn hay nhãn. Bằng chứng dựng bằng
đúng các hàm người gán đã thấy: `kiem_hints.hints` (chuỗi phiên bản, gợi ý chỗ chuyển) và `crosscheck_evidence.py`
(trích văn bản gốc, văn bản tác động, chuyển tiếp, hiệu lực).
"""
from __future__ import annotations

import argparse
import collections
import csv
import hashlib
import json
import random
import shutil
import subprocess
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts/pipeline"))
sys.path.insert(0, str(Path(__file__).parent))
csv.field_size_limit(sys.maxsize)

SEED = "vilextime-test2-2910"
GROUPS = ("T2", "T3", "T6")
# Đợt 1, khoảng một nửa số cần; thiếu thì rút đợt 2 cùng seed (rút tiếp trong cùng thứ tự đã xáo)
QUOTA = {"T2": 150, "T2 gần giống": 65, "T3": 220, "T6 cấp trên": 75, "T6 đích danh": 75}
# Đợt 2 (02/11): T3 lấy hết kho; T6 giữ được 13% ở đợt 1 nên cần rút nhiều để đủ ~100 câu
QUOTA2 = {"T2": 120, "T2 gần giống": 40, "T3": 221, "T6 cấp trên": 300, "T6 đích danh": 300}
# Đợt 3 (02/11, chỉ T2, bù cho cổng trùng chữ): seed mới, bỏ mọi lineage đã nằm trong khóa; T3 hết kho, T6 để CMT quyết
QUOTA3 = {"T2": 280, "T2 gần giống": 120}
# Lý do ở cấp lineage: bên lọc nhìn được khi chưa có câu hỏi. Lý do ở cấp câu hỏi không dùng để hiệu chuẩn.
LINEAGE_CODES = {"cosmetic_only", "rename_only", "auto_reference_update", "single_change", "relocated",
                 "relocation_unclear", "reference_only", "superseded_by_other_norm", "gold_wrong",
                 "restructuring_2025", "transitional_rule"}
PACK, TEXT_MAX = 25, 3000
CATCH_MIN, FALSE_REJECT_MAX = 0.80, 0.30    # CMT 29/10: "càng chất lượng càng tốt"
OUT_COLS = ["item", "quyet_dinh", "ma", "can_cu", "ghi_chu"]
COPY_MAX, MAX_WRITES = 0.40, 3        # CMT 29/10: trùng chữ ≤ 40%; viết lại tối đa hai lần rồi loại
# Hư từ và từ khung của mọi câu hỏi pháp luật: không phải chữ chép từ đáp án.
STOP = frozenset("""và hoặc của các những một là thì mà có được bị cho với về theo trong ngoài tại từ đến khi nếu để do
bởi vì này đó ấy nào gì ra sao như thế phải không ai bao nhiêu lâu trường hợp quy định pháp luật người""".split())


def stratum(r: dict) -> str:
    if r["group"] == "T2":
        return "T2 gần giống" if r.get("near_identical") else "T2"
    if r["group"] == "T6":
        return "T6 cấp trên" if r.get("repeal_mode") == "ancestor" else "T6 đích danh"
    return r["group"]


def independent(review: dict) -> bool:
    """A final human label made without AI help: A and B agreeing, or the lawyer deciding unaided."""
    who = review.get("labeler") or ""
    return (review.get("status") == "checked" and review.get("source") == "human"
            and (who == "A+B" or who.startswith("luật sư")) and "Claude" not in who)


def lineage_truth(reviews: list[dict]) -> tuple[str, list[str]] | None:
    """('tot', []) when every boundary row passed; ('xau', codes) on a lineage-level reason; else None."""
    if not reviews or not all(independent(r) for r in reviews):
        return None
    bad = sorted({c for r in reviews if r["verdict"] == "khong_dat" for c in r["reasons"]})
    if not bad:
        return "tot", []
    hit = [c for c in bad if c in LINEAGE_CODES]
    return ("xau", hit) if hit else None


def read_tsv(p: Path) -> dict[str, dict]:
    with p.open(encoding="utf-8", newline="") as f:
        return {r[next(iter(r))]: r for r in csv.DictReader(f, delimiter="\t")}


def draw(pool: dict[str, list[str]], rng: random.Random) -> tuple[list[str], list[str]]:
    """(đợt 1, đợt 2) rút tiếp trong cùng một thứ tự đã xáo, nên đợt 2 không làm đổi đợt 1."""
    first, second = [], []
    for s, n in QUOTA.items():
        rng.shuffle(pool[s])
        first += pool[s][:n]
        second += pool[s][n:n + QUOTA2[s]]
    return first, second


def published_scope(data: Path) -> tuple[set[str], set[str]]:
    """All v1.0 lineages and dev documents, including documents represented only by T1.

    The approved test2 plan excludes whole dev documents, not only the groups
    present in the test2 pool. Published metadata is the owner of document IDs.
    """
    root = data / "vilextime_dataset"
    main = [json.loads(line) for line in (root / "vilextime.jsonl").open(encoding="utf-8")]
    dev_ids = {r["id"] for r in main if r["split"] == "dev"}
    docs = {}
    for line in (root / "vilextime_meta.jsonl").open(encoding="utf-8"):
        r = json.loads(line)
        if r["id"] in dev_ids and r.get("target", {}).get("document_id"):
            docs[r["id"]] = r["target"]["document_id"]
    if missing := dev_ids - docs.keys():
        raise SystemExit(f"{sorted(missing)[0]}: thiếu document_id của dev trong vilextime_meta.jsonl; "
                         "không chứng minh được tách văn bản (plan vilextime-test2.md); khôi phục metadata v1.0.")
    return {r["lineage_id"] for r in main}, set(docs.values())


def build(out: Path, data: Path, second_round: bool = False, third: bool = False) -> None:
    from export_release import final_labels
    from kiem_hints import hints, versions_of
    from vilexgraph.framework.corpus import Corpus

    rows = [json.loads(l) for g in GROUPS for l in (data / f"derived/vilextime/{g}.jsonl").open(encoding="utf-8")]
    by_lineage: dict[str, list[dict]] = collections.defaultdict(list)
    for r in rows:
        by_lineage[r["lineage_id"]].append(r)
    lineage_of = {r["id"]: r["lineage_id"] for r in rows}

    used, dev_docs = published_scope(data)
    doc_of = {lid: rs[0]["target"]["document_id"] for lid, rs in by_lineage.items()}

    reviews: dict[str, list[dict]] = collections.defaultdict(list)
    for i, rev in final_labels(data / "review").items():
        if i in lineage_of:
            reviews[lineage_of[i]].append(rev)
    truth = {lid: t for lid, revs in reviews.items() if (t := lineage_truth(revs))}

    rng = random.Random(SEED)
    pool: dict[str, list[str]] = collections.defaultdict(list)
    for lid in sorted(by_lineage):
        # a lineage someone already labelled is calibration or was dropped, never a fresh candidate
        if lid not in used and lid not in reviews and doc_of[lid] not in dev_docs:
            pool[stratum(by_lineage[lid][0])].append(lid)
    picked, later = draw(pool, rng)
    work = out.parent.parent
    tag = "_3" if third else "_2" if second_round else ""
    if third:
        taken, r3 = set(read_tsv(work / "key_loc.tsv")), random.Random(SEED + "-r3")
        picked = []
        for st, n in QUOTA3.items():
            fresh = [l for l in pool[st] if l not in taken]
            r3.shuffle(fresh)
            picked += fresh[:n]
    elif second_round:
        if set(read_tsv(work / "key_loc.tsv")) != set(truth) | set(picked):
            raise SystemExit("Không tái lập được đợt 1 (nhãn đã đổi?): đợt 2 sẽ rút trùng hoặc lệch thứ tự.")
        picked = later
    items = sorted(truth) + picked
    rng.shuffle(items)

    out.mkdir(parents=True, exist_ok=True)
    item_rows = [r for lid in items for r in sorted(by_lineage[lid], key=lambda r: r["as_of"])]
    # the group files predate enrich_vilextime, which names each transition's operation the same way
    need = {t["event_id"] for r in item_rows for t in r["derivation"]["transitions"]}
    ops = {e["id"]: e["operation"] for e in map(json.loads, (data / "derived/provision_events.jsonl").open(encoding="utf-8"))
           if e["id"] in need}
    for r in item_rows:
        for t in r["derivation"]["transitions"]:
            t["op"] = ops.get(t["event_id"])
    (work / f"rows{tag}.jsonl").write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in item_rows),
                                     encoding="utf-8")
    (work / f"ids{tag}.txt").write_text("".join(r["id"] + "\n" for r in item_rows), encoding="utf-8")
    subprocess.run([sys.executable, str(ROOT / "scripts/review/crosscheck_evidence.py"), "--data", str(data),
                    "--ids", str(work / f"ids{tag}.txt"), "--release", str(work / f"rows{tag}.jsonl"),
                    "--out", str(work / f"evidence{tag}.jsonl")], check=True)
    evidence = {e["id"]: e for e in map(json.loads, (work / f"evidence{tag}.jsonl").open(encoding="utf-8"))}
    corpus = Corpus(data / "derived/corpus/index.sqlite")
    hint = hints(item_rows, corpus)

    def record(lid: str) -> dict:
        rs = sorted(by_lineage[lid], key=lambda r: r["as_of"])
        t, first = rs[0]["target"], hint[rs[0]["id"]]
        actors = {}
        for r in rs:
            for a in evidence[r["id"]]["actors"]:
                actors.setdefault((a["document"], a["op"]), a)
        return {"item": lid, "nhom": stratum(rs[0]), "van_ban": t["law_id"], "dieu_khoan": t["citation"],
                "vi_tri": t["provision_path"], "cau_dan": t.get("lead_in"), "source_url": rs[0].get("source_url"),
                "cac_moc": [{"as_of": r["as_of"], "co_dap_an": r["answer"] is not None} for r in rs],
                "loi_van": [{**v, "text": (v["text"] or "")[:TEXT_MAX]} for v in versions_of(corpus, lid)],
                "cac_phien_ban": first["cac_phien_ban"].replace("   ◀ đáp án của dòng này", ""),
                "goi_y_cho_moi": first["goi_y_cho_moi"],
                "van_ban_goc": evidence[rs[0]["id"]]["base"],
                "van_ban_tac_dong": list(actors.values())}

    write_packs(out, [record(lid) for lid in items])
    key = work / "key_loc.tsv"
    if second_round or third:
        with key.open("a", encoding="utf-8") as f:
            f.writelines(f"{lid}\t{stratum(by_lineage[lid][0])}\tung_vien\t\t\n" for lid in picked)
        install_instructions(out, work / "gan")
        print(f"đợt {3 if third else 2}: {len(items)} mục ({len(truth)} hiệu chuẩn, {len(picked)} ứng viên) -> {-(-len(items) // PACK)} gói ở {out}")
        return
    with key.open("w", encoding="utf-8") as f:
        f.write("item\tnhom\tvai_tro\tsu_that\tma\n")
        for lid in items:
            role, (fact, codes) = ("hieu_chuan", truth[lid]) if lid in truth else ("ung_vien", ("", []))
            f.write(f"{lid}\t{stratum(by_lineage[lid][0])}\t{role}\t{fact}\t{','.join(codes)}\n")
    calib = collections.Counter((stratum(by_lineage[l][0]), truth[l][0]) for l in truth)
    print(f"{len(items)} mục ({len(truth)} hiệu chuẩn, {len(picked)} ứng viên) -> {-(-len(items) // PACK)} gói ở {out}")
    print("  hiệu chuẩn:", dict(sorted(calib.items())))
    print("  ứng viên:", {s: min(n, len(pool[s])) for s, n in QUOTA.items()}, "· kho còn:",
          {s: len(v) for s, v in sorted(pool.items())})
    print(f"  khóa: {key}")


def write_packs(out: Path, records: list[dict]) -> None:
    for n in range(0, len(records), PACK):
        with (out / f"pack_{n // PACK + 1:02d}.jsonl").open("w", encoding="utf-8") as f:
            f.writelines(json.dumps(r, ensure_ascii=False) + "\n" for r in records[n:n + PACK])


def install_instructions(out: Path, old: Path) -> None:
    shutil.copy(ROOT / "prompts/vilextime/test2_loc.md", out.parent / "HUONG_DAN.md")
    for name in ("CLAUDE.md", "AGENTS.md"):
        shutil.copy(old / name, out.parent / name)


def redo(out: Path, old: Path, result: Path, codes: set[str]) -> list[str]:
    """Gói lọc lại sau khi sửa lời dặn: mọi mục hiệu chuẩn (chấm lại từ đầu) và mọi ứng viên bị loại với `codes`.

    Lời dặn mới chỉ nới điều ứng với `codes`, nên ứng viên đã giữ vẫn giữ, ứng viên loại vì mã khác vẫn loại.
    Trộn lại thứ tự để bên lọc vẫn không biết mục nào bị chấm.
    """
    key = read_tsv(old.parent.parent / "key_loc.tsv")
    got = read_tsv(result)
    ids = {i for i in key if key[i]["vai_tro"] == "hieu_chuan" or got[i]["ma"] in codes}
    records = [r for p in sorted(old.glob("pack_*.jsonl")) for r in map(json.loads, p.open(encoding="utf-8"))
               if r["item"] in ids]
    random.Random(SEED + "-redo").shuffle(records)
    out.mkdir(parents=True)
    write_packs(out, records)
    install_instructions(out, old.parent)
    print(f"{len(records)} mục lọc lại -> {-(-len(records) // PACK)} gói ở {out}")
    return [r["item"] for r in records]


def copy_share(question: str, versions: list[str]) -> float:
    """Tỷ lệ tiếng có nghĩa của câu hỏi có trong lời văn (cùng cách đo với G7, DATASET_GAP: trung vị 0,71 ở bộ câu cũ)."""
    from generate_questions import words
    asked = [w for w in words(question) if w not in STOP]
    gold = set(words(" ".join(versions)))
    return sum(w in gold for w in asked) / len(asked) if asked else 0.0


def judge_question(question: str, context: str, versions: list[str]) -> str | None:
    """Lý do phải viết lại, hoặc None. `insufficient_context` là từ chối, không viết lại."""
    from generate_questions import validate
    reason = validate(question, context, versions)
    if reason is None and (share := copy_share(question, versions)) > COPY_MAX:
        return f"copy_share:{share:.2f}"
    return reason


def lineage_rows(data: Path, ids: set[str]) -> dict[str, list[dict]]:
    rows: dict[str, list[dict]] = collections.defaultdict(list)
    for g in GROUPS:
        for line in (data / f"derived/vilextime/{g}.jsonl").open(encoding="utf-8"):
            r = json.loads(line)
            if r["lineage_id"] in ids:
                rows[r["lineage_id"]].append(r)
    return {lid: sorted(rs, key=lambda r: r["as_of"]) for lid, rs in rows.items()}


def merged(results: list[Path]) -> dict[str, dict]:
    got = {}
    for r in results:
        got.update(read_tsv(r))
    return got


def pending(out: Path, old: Path, results: list[Path], data: Path, key_path: Path) -> list[str]:
    """Resume the historical draw after interruption, without redoing saved decisions.

    Copies the exact old instruction bytes; never rebuilds/shuffles the draw or
    exposes calibration roles or labels to the new worker directory.
    """
    key, done = read_tsv(key_path), merged(results)
    records = [r for p in sorted(old.glob("pack_*.jsonl")) for r in map(json.loads, p.open(encoding="utf-8"))]
    ids = [r["item"] for r in records]
    if len(ids) != len(set(ids)):
        raise SystemExit("Gói gốc trùng item; khôi phục gói gốc trước khi chạy pending.")
    todo = [r for r in records if r["item"] not in done and key[r["item"]]["vai_tro"] == "ung_vien"]
    rows = lineage_rows(data, {r["item"] for r in todo})
    used, dev_docs = published_scope(data)
    excluded = [r["item"] for r in todo if r["item"] in used or rows[r["item"]][0]["target"]["document_id"] in dev_docs]
    todo = [r for r in todo if r["item"] not in excluded]
    # Read all prerequisite bytes before writing anything, so an incomplete
    # source session cannot leave a plausible but instruction-less work pack.
    instructions = {name: (old.parent / name).read_bytes() for name in ("HUONG_DAN.md", "AGENTS.md", "CLAUDE.md")}
    out.mkdir(parents=True, exist_ok=False)
    write_packs(out, todo)
    for name, content in instructions.items():
        (out.parent / name).write_bytes(content)
    print(f"{len(todo)} ứng viên chưa có quyết định -> {-(-len(todo) // PACK)} gói ở {out}; "
          f"chặn {len(excluded)} trùng v1.0/dev, không sửa kết quả cũ.")
    return [r["item"] for r in todo]


def qpack(out: Path, results: list[Path], data: Path, key_path: Path | None, limit: int | None) -> None:
    """Gói viết câu hỏi: ứng viên được giữ (không phải câu hiệu chuẩn, chúng đã ở v1.0). `limit` rút mẫu thử theo seed."""
    from generate_questions import user_prompt
    key = read_tsv(key_path or out.parent.parent / "key_loc.tsv")
    got = merged(results)
    kept = sorted(i for i in key if key[i]["vai_tro"] == "ung_vien" and got.get(i, {}).get("quyet_dinh") == "giu")
    rows = lineage_rows(data, set(kept))
    used, dev_docs = published_scope(data)
    excluded = {i: "v1.0 lineage" if i in used else "dev document" for i in kept
                if i in used or rows[i][0]["target"]["document_id"] in dev_docs}
    # Historical filter outputs stay intact: the funnel records why a kept
    # candidate cannot progress, instead of changing the original random draw.
    kept = [i for i in kept if i not in excluded]
    if limit:
        kept = random.Random(SEED + "-qpack").sample(kept, limit)
    records = [{"item": i, "nhom": key[i]["nhom"], "dau_vao": user_prompt(rows[i])[0]} for i in kept]
    out.mkdir(parents=True)
    write_packs(out, records)
    prompts = ROOT / "prompts/vilextime"
    parts = ["base.md", "T2.md", "T4.md", "T3.md", "T6.md", "test2_cau_hoi.md"]
    (out.parent / "HUONG_DAN.md").write_text("\n\n---\n\n".join((prompts / p).read_text(encoding="utf-8").strip() for p in parts) + "\n",
                                             encoding="utf-8")
    brief = ("# Viết câu hỏi ViLexTime bộ test 2\n\nĐọc `HUONG_DAN.md` rồi làm đúng theo đó cho mọi gói trong `packs/`.\n"
             "Chỉ đọc file trong thư mục này. Không sửa `HUONG_DAN.md` hay các gói.\n")
    for name in ("CLAUDE.md", "AGENTS.md"):
        (out.parent / name).write_text(brief, encoding="utf-8")
    (out.parent / "excluded_scope.jsonl").write_text("".join(
        json.dumps({"item": i, "reason": why}, ensure_ascii=False) + "\n" for i, why in sorted(excluded.items())),
        encoding="utf-8")
    if excluded:
        print(f"{len(excluded)} mục giữ không sang viết câu hỏi: trùng v1.0/dev "
              "(docs/plans/active/vilextime-test2.md); xem excluded_scope.jsonl, không dùng các mục này cho test2.")
    print(f"{len(records)} mục -> {-(-len(records) // PACK)} gói ở {out}")


def qcheck(out: Path, answers: list[Path], data: Path, model: str, dest: Path, provider: str = "claude-code") -> dict:
    """Mỗi file `answers` là một lượt viết, lượt sau đè lượt trước. Câu đạt và câu hết lượt ghi vào `dest`, câu còn lượt ra viet_lai."""
    from generate_questions import INSUFFICIENT, user_prompt
    packs = {r["item"]: r for p in sorted(out.glob("pack_*.jsonl")) for r in map(json.loads, p.open(encoding="utf-8"))}
    written: dict[str, list[str]] = collections.defaultdict(list)
    for a in answers:
        for r in map(json.loads, a.open(encoding="utf-8")):
            written[r["item"]].append(r["question"].strip())
    if set(written) - set(packs):
        raise SystemExit(f"mục lạ: {sorted(set(written) - set(packs))[:3]}")
    rows = lineage_rows(data, set(packs))
    prompt_sha = hashlib.sha256((out.parent / "HUONG_DAN.md").read_bytes()).hexdigest()[:12]
    today = date.today().isoformat()
    final, redo_list, stats = [], [], collections.Counter()
    for i, tries in sorted(written.items()):
        _, context, versions = user_prompt(rows[i])
        text = tries[-1]
        reason = judge_question(text, context, versions)
        stats["ok" if reason is None else reason.split(":")[0]] += 1
        if reason and text != INSUFFICIENT and len(tries) < MAX_WRITES:
            redo_list.append({**packs[i], "da_viet": text, "ly_do": reason})
        else:
            final.append({"lineage_id": i, "group": rows[i][0]["group"], "question": None if reason else text,
                          "rejected_reason": reason, "raw": text if reason else None, "provider": provider,
                          "model": model, "temperature": None, "attempts": len(tries), "prompt_sha": prompt_sha,
                          "generated_at": today, "copy_share": round(copy_share(text, versions), 3)})
    with (out.parent / "viet_lai.jsonl").open("w", encoding="utf-8") as f:
        f.writelines(json.dumps(r, ensure_ascii=False) + "\n" for r in redo_list)
    dest.parent.mkdir(parents=True, exist_ok=True)
    with dest.open("w", encoding="utf-8") as f:
        f.writelines(json.dumps(r, ensure_ascii=False) + "\n" for r in final)
    print(f"{len(written)}/{len(packs)} mục có câu; {dict(stats)}; viết lại {len(redo_list)}; chốt {len(final)} -> {dest}")
    return stats


def score(out: Path, results: list[Path], key_path: Path | None = None) -> bool:
    key = read_tsv(key_path or out.parent.parent / "key_loc.tsv")
    got = merged(results)
    strange = sorted(set(got) - set(key))
    missing = sorted(set(key) - set(got))
    print(f"quyết định {len(got)} mục; thiếu {len(missing)}; mục lạ {len(strange)}")
    calib = [i for i in key if key[i]["vai_tro"] == "hieu_chuan" and i in got]
    ok = True
    for name in ("toàn tập", *QUOTA):
        sel = [i for i in calib if name == "toàn tập" or key[i]["nhom"] == name]
        bad = [i for i in sel if key[i]["su_that"] == "xau"]
        good = [i for i in sel if key[i]["su_that"] == "tot"]
        caught = sum(got[i]["quyet_dinh"] == "loai" for i in bad) / len(bad) if bad else None
        wrong = sum(got[i]["quyet_dinh"] == "loai" for i in good) / len(good) if good else None
        fmt = lambda x: "-" if x is None else f"{x:.2f}"
        print(f"  {name:13} xấu {len(bad):3} loại đúng {fmt(caught)} · tốt {len(good):3} loại nhầm {fmt(wrong)}")
        if name == "toàn tập":
            ok = (caught or 0) >= CATCH_MIN and (wrong if wrong is not None else 1) <= FALSE_REJECT_MAX
    kept = collections.Counter(key[i]["nhom"] for i in got if key.get(i, {}).get("vai_tro") == "ung_vien"
                               and got[i]["quyet_dinh"] == "giu")
    print("  ứng viên được giữ:", dict(sorted(kept.items())))
    print(f"ngưỡng loại đúng >= {CATCH_MIN} và loại nhầm <= {FALSE_REJECT_MAX} ->", "ĐẠT" if ok else "CHƯA ĐẠT")
    return ok


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=("build", "score", "redo", "pending", "qpack", "qcheck"))
    ap.add_argument("result", nargs="*", type=Path)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--data", type=Path, default=Path("data"))
    ap.add_argument("--key", type=Path, help="khóa cho score; mặc định OUT/../../key_loc.tsv")
    ap.add_argument("--second", action="store_true", help="build: đợt 2 cùng thứ tự rút")
    ap.add_argument("--third", action="store_true", help="build: đợt 3, chỉ T2, seed mới, bỏ lineage đã trong khóa")
    ap.add_argument("--limit", type=int, help="qpack: chỉ rút chừng này mục để thử")
    ap.add_argument("--model", help="qcheck: ai viết câu hỏi")
    ap.add_argument("--provider", default="claude-code", help="qcheck: nguồn thực tế, ví dụ codex hoặc claude-code")
    ap.add_argument("--dest", type=Path, default=Path("data/vilextime/questions_test2.jsonl"), help="qcheck: file câu chốt")
    ap.add_argument("--from", dest="old", type=Path, help="redo: thư mục gói của lần trước")
    ap.add_argument("--codes", default="transitional_rule", help="redo: mã đã sửa trong lời dặn, phẩy ngăn cách")
    args = ap.parse_intermixed_args()
    if args.cmd == "build":
        build(args.out, args.data, args.second, args.third)
    elif args.cmd == "redo":
        redo(args.out, args.old, args.result[0], set(args.codes.split(",")))
    elif args.cmd == "pending":
        if not args.old or not args.key:
            ap.error("pending cần --from OLD/packs và --key KEY; không dựng lại mẫu lịch sử.")
        pending(args.out, args.old, args.result, args.data, args.key)
    elif args.cmd == "qpack":
        qpack(args.out, args.result, args.data, args.key, args.limit)
    elif args.cmd == "qcheck":
        if not args.model:
            ap.error("qcheck cần --model; nếu không xác minh được tên model, ghi rõ chưa biết, không đoán.")
        qcheck(args.out, args.result, args.data, args.model, args.dest, args.provider)
    else:
        score(args.out, args.result, args.key)

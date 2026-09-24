#!/usr/bin/env python3
"""ViLexTime — the natural-language question for each candidate (plan C1–C3).

The gold answer is derived from the version chain and a model never touches
it. What a model is for is the *question*: "Tính đến ngày 16/02/2017, Khoản 1
Điều 3 Thông tư số 36/2016/TT-BTTTT quy định nội dung gì?" is a template, and
2,500 rows of one template is a pattern to memorise, not a benchmark.

Two rules shape this file:

* **One question per lineage, not per row** (C3). A T2 pair is the same
  question asked at two dates; generating twice would give two questions and
  destroy the contrast. The date never appears in the question — it is the
  `as_of` field, which is what lets one question serve every date.
* **Nothing the model writes is trusted** (C2). Every question passes
  `validate()` before it is kept, and a rejection is written down with its
  reason rather than silently retried into something that passes.

Output is `data/vilextime/questions.jsonl`, one row per lineage,
append-only so a run that dies at 2,000 of 2,500 resumes where it stopped.
`build_vilextime.py` merges it into the released records.

Usage:
    python scripts/pipeline/generate_questions.py --group T1 --dry-run --limit 3
    python scripts/pipeline/generate_questions.py --group T1 --limit 50
    python scripts/pipeline/generate_questions.py --group T1
    python scripts/pipeline/generate_questions.py --group T1 --sample data/derived/vilextime/sample.jsonl
    python scripts/pipeline/generate_questions.py --group T1 --revalidate   # after changing validate()
"""
from __future__ import annotations

import argparse
import collections
import difflib
import hashlib
import json
import re
import sys
import unicodedata
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from legal_crawler.llm import Completion, LLMError, complete, configured, pick  # noqa: E402

PROMPTS = Path(__file__).resolve().parents[2] / "prompts/vilextime"
INSUFFICIENT = "KHONG_DU_NGU_CANH"
LEAK_NGRAM = 8          # a shared run this long is the answer, not a shared term
# ponytail: a coverage threshold, not a judgement of which words are "the answer";
# the hand-check (D4) is what catches a question that gives away the asked part.
LEAK_SHARE = 1 / 2      # copying half of a version is answering the question
# "Có phải X không?" with X copied is the answer read back as a question.
_YES_NO = re.compile(r"(?i)\bcó\s+phải\b|\bkhông\s*\?\s*$")
_NUMBER = re.compile(r"\d+(?:[.,]\d+)*")
_DATE = re.compile(r"\b(?:19|20)\d{2}\b|\d{1,2}\s*[/-]\s*\d{1,2}\s*[/-]\s*\d{2,4}"
                   r"|\bngày\s+\d|\btháng\s+\d|\bnăm\s+\d")
# A list label ("loại c)", "mục đ)") names a position as surely as "Điểm c" does.
_CITES = re.compile(r"(?i)\b(?:điều|khoản|điểm|chương|mục)\s+\d|"
                    r"\d+\s*/\s*\d{4}\s*/\s*[A-ZĐ]|(?<!\w)[a-zđ]\)")
_FILLER = re.compile(r"(?i)cho\s+(?:em|tôi|mình)\s+hỏi|xin\s+chào|\bạ\s*[?.]|"
                     r"\bnhé\b|\bnha\b|\bvậy\s+ạ\b|^\s*chào\b")
# "Theo quy định pháp luật hiện hành, ..." is how Vietnamese legal QA normally
# opens, and it is exactly wrong here: it pins the question to the reader's
# present, while the anchor is `as_of`. The same question is asked in 2016 and
# in 2026, so it may not claim either is "now".
_PRESENT = re.compile(r"(?i)hiện\s+hành|hiện\s+nay|hiện\s+t\u1ea1i|bây\s+giờ|"
                      r"đang\s+có\s+hiệu\s+lực|mới\s+nhất|gần\s+đây")


_PUNCT = re.compile(r"[^\w\s]", re.UNICODE)


def words(text: str) -> list[str]:
    """Tokens for comparing two texts, with punctuation dropped.

    Keeping it attached made the comparison wrong in both directions: "hội,"
    in the answer did not match "hội" in the title, so reused framing looked
    like a leak; and "thanh:" did not match "thanh", so a real copy slipped
    through. Punctuation carries no meaning for this check.
    """
    return _PUNCT.sub(" ", unicodedata.normalize("NFC", text).casefold()).split()


def ngrams(text: str, n: int) -> set[tuple[str, ...]]:
    tokens = words(text)
    return {tuple(tokens[i:i + n]) for i in range(len(tokens) - n + 1)}


def leaks(question: str, context: str, versions: list[str]) -> bool:
    """Does the question answer itself, or say which version is meant?

    Any shared 8-word run used to count, and that rejected most situation
    questions: to describe "an act of suspending securities trading" a question
    has to name it, and the provision names it the same way. What actually
    breaks an item is narrower, so only two things count:

    * the copied runs cover half or more of some version, or any of it in a
      yes/no question — the question carries its own answer;
    * with several versions, a copied run holds a word only one version has —
      the question tells which date it is asked at, and the contrast is gone.
    """
    asked = ngrams(question, LEAK_NGRAM) - ngrams(context, LEAK_NGRAM)
    vocab = [set(words(v)) for v in versions]
    for n, version in enumerate(versions):
        tokens = words(version)
        covered = set()
        for i in range(len(tokens) - LEAK_NGRAM + 1):
            if tuple(tokens[i:i + LEAK_NGRAM]) in asked:
                covered.update(range(i, i + LEAK_NGRAM))
        if covered and (len(covered) / len(tokens) >= LEAK_SHARE or _YES_NO.search(question)):
            return True
        others = set().union(*(vocab[:n] + vocab[n + 1:])) if len(versions) > 1 else None
        if others is not None and any(tokens[i] not in others for i in covered):
            return True
    return False


def validate(question: str, context: str, answer: str | list[str]) -> str | None:
    """Why this question must be thrown away, or None when it may be kept.

    `context` is the framing the model was allowed to reuse (document title and
    lead-in); `answer` is the text it must not copy — one string, or every
    version when the provision has several.
    """
    versions = [answer] if isinstance(answer, str) else answer
    answer = "\n".join(versions)
    if not question or "\n" in question.strip():
        return "not_one_line"
    if question.strip() == INSUFFICIENT:
        return "insufficient_context"
    if not question.rstrip().endswith("?"):
        return "not_a_question"
    if _FILLER.search(question):
        return "conversational_filler"
    if _PRESENT.search(question):
        return "presumes_the_present"
    # Citations first: a document number carries a year ("36/2016/TT-BTTTT"), and
    # reporting that as a date would send the prompt fix in the wrong direction.
    if _CITES.search(question):
        return "cites_a_provision"        # it must ask about content, not position
    if _DATE.search(question):
        return "mentions_a_date"          # the anchor is `as_of`, never the text
    source = f"{context}\n{answer}"
    unsourced = [n for n in _NUMBER.findall(question) if n not in source]
    if unsourced:
        return f"unsourced_number:{unsourced[0]}"
    # Only a run the question could not have got from the framing counts:
    # "giải thể cơ sở bảo trợ xã hội" is in the document's own title, so reusing
    # it is the anchoring rule working, not the model copying gold.
    if leaks(question, context, versions):
        return "copies_the_answer"
    if len(words(question)) < 5:
        return "too_short"
    return None


# Two forms, half the lineages each. The proposal defines the input t as "the
# moment the act or legal relation arose", so half the questions describe a
# situation; the other half look the rule up. The model is *told* which form and
# which opening to use: left to rotate on its own it opened 31 of 31 questions
# with "Trong ...", because it only ever sees one question at a time.
STYLE_SEED = "vilextime-style-v1"
OPENINGS = {
    "tra_cuu": ("Theo quy định về <chủ đề>, …?",
                "Pháp luật về <chủ đề> quy định … như thế nào?",
                "… được xác định ra sao trong quy định về <chủ đề>?",
                "Trong lĩnh vực <chủ đề>, …?"),
    "tinh_huong": ("Một <chủ thể> <làm gì / gặp việc gì> thì …?",
                   "Khi <sự việc xảy ra>, <chủ thể> phải / được …?",
                   "Nếu <chủ thể> <hành vi>, …?",
                   "Trường hợp <tình huống cụ thể>, …?"),
}


def style_of(lineage_id: str) -> tuple[str, str]:
    """(form, opening) for this lineage — fixed by its id, never by the model."""
    h = int(hashlib.sha256(f"{STYLE_SEED}:{lineage_id}".encode()).hexdigest(), 16)
    form = ("tra_cuu", "tinh_huong")[h % 2]
    return form, OPENINGS[form][(h // 2) % len(OPENINGS[form])]


def changes(old: str, new: str) -> str:
    """The word-level difference between two versions, as the model should read it.

    The proposal has the code find the difference and the model only word it;
    handing over two raw texts made the model find it, and nothing checked it had.
    """
    a, b = old.split(), new.split()
    parts = []
    for op, i1, i2, j1, j2 in difflib.SequenceMatcher(a=a, b=b, autojunk=False).get_opcodes():
        if op == "delete":
            parts.append(f"bỏ «{' '.join(a[i1:i2])}»")
        elif op == "insert":
            parts.append(f"thêm «{' '.join(b[j1:j2])}»")
        elif op == "replace":
            parts.append(f"«{' '.join(a[i1:i2])}» → «{' '.join(b[j1:j2])}»")
    return "; ".join(parts) or "(chỉ khác dấu câu hoặc khoảng trắng)"


def system_prompt(group: str) -> str:
    base = (PROMPTS / "base.md").read_text(encoding="utf-8").strip()
    per_group = PROMPTS / f"{group}.md"
    if not per_group.exists():
        raise SystemExit(f"no prompt for {group}: expected {per_group}")
    return f"{base}\n\n---\n\n{per_group.read_text(encoding='utf-8').strip()}"


def user_prompt(records: list[dict]) -> tuple[str, str, list[str]]:
    """(message, framing the model may reuse, the versions it must not copy)."""
    target = records[0]["target"]
    title = target["document_title"] or ""
    lead_in = target["lead_in"] or ""
    # One question serves every date, so the model sees every version's text.
    answers = [r["answer"] for r in records if r["answer"]]
    seen: list[str] = []
    for answer in answers:
        if answer not in seen:
            seen.append(answer)

    lines = [f"TÊN VĂN BẢN: {title}"]
    if lead_in:
        lines.append(f"CÂU DẪN (nút cha): {lead_in}")
    if len(seen) == 1:
        lines.append(f"ĐÁP ÁN: {seen[0]}")
    else:
        lines.append("CÁC PHIÊN BẢN CỦA ĐÁP ÁN, theo thứ tự thời gian:")
        lines += [f"  [{n}] {text}" for n, text in enumerate(seen, 1)]
        lines.append("CHỖ THAY ĐỔI (máy tính sẵn, từ phiên bản trước sang phiên bản sau):")
        lines += [f"  [{n}→{n + 1}] {changes(seen[n - 1], seen[n])}" for n in range(1, len(seen))]
    form, opening = style_of(records[0]["lineage_id"])
    lines.append(f"DẠNG CÂU HỎI: {'tình huống' if form == 'tinh_huong' else 'tra cứu'}")
    lines.append(f"MỞ ĐẦU: {opening}")
    return "\n".join(lines), f"{title}\n{lead_in}", seen


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--data", type=Path, default=Path("data"))
    parser.add_argument("--group", required=True)
    parser.add_argument("--provider", help="default: first configured, Groq first")
    parser.add_argument("--model", help="default: $<PROVIDER>_MODEL")
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--limit", type=int, help="stop after this many lineages")
    parser.add_argument("--dry-run", action="store_true", help="print the prompts, call nothing")
    parser.add_argument("--answers", type=Path,
                        help="JSONL of {lineage_id, question} written outside this script (e.g. by a "
                             "Claude Code session); judged exactly like a provider's reply, no calls")
    parser.add_argument("--revalidate", action="store_true",
                        help="re-judge every stored question with the current validate(); no calls")
    parser.add_argument("--sample", type=Path,
                        help="only these lineages, in rank order (sample_vilextime.py writes it)")
    args = parser.parse_args()

    source = args.data / f"derived/vilextime/{args.group}.jsonl"
    if not source.exists():
        raise SystemExit(f"{source} not found — run build_vilextime.py --group {args.group} first")

    by_lineage: dict[str, list[dict]] = collections.defaultdict(list)
    for line in source.open(encoding="utf-8"):
        record = json.loads(line)
        by_lineage[record["lineage_id"]].append(record)
    for records in by_lineage.values():
        records.sort(key=lambda r: r["as_of"])

    out_path = args.data / "vilextime/questions.jsonl"   # committed: not rebuildable
    done: set[str] = set()
    if out_path.exists():
        done = {json.loads(line)["lineage_id"] for line in out_path.open(encoding="utf-8")}

    if args.revalidate:
        # The model's text is kept either way (`question` or `raw`), so a changed
        # rule re-judges it without asking the model again.
        rows = [json.loads(line) for line in out_path.open(encoding="utf-8")]
        moved = collections.Counter()
        for row in rows:
            if row["group"] != args.group:
                continue
            text = row["question"] or row["raw"] or ""
            _, context, versions = user_prompt(by_lineage[row["lineage_id"]])
            reason = validate(text, context, versions)
            moved[(row["rejected_reason"] or "ok").split(":")[0], (reason or "ok").split(":")[0]] += 1
            row.update(question=text if reason is None else None, raw=None if reason is None else text,
                       rejected_reason=reason)
        out_path.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")
        for (before, after), count in sorted(moved.items()):
            print(f"  {before:>20} -> {after:<20} {count:>5}")
        return

    system = system_prompt(args.group)
    prompt_sha = hashlib.sha256(system.encode("utf-8")).hexdigest()[:12]
    order = sorted(by_lineage)
    if args.sample:
        ranked = [json.loads(line) for line in args.sample.open(encoding="utf-8")]
        order = [r["lineage_id"] for r in sorted(ranked, key=lambda r: r["rank"]) if r["group"] == args.group]
    pending = [(lid, by_lineage[lid]) for lid in order if lid not in done]
    if args.limit:
        pending = pending[:args.limit]
    print(f"{args.group}: {len(by_lineage):,} lineage · {len(done):,} đã có · {len(pending):,} sẽ sinh"
          f" · prompt {prompt_sha}")

    if args.dry_run:
        for lid, records in pending:
            message, _, _ = user_prompt(records)
            print(f"\n{'=' * 70}\n{lid}\n{'-' * 70}\n{message}")
        print(f"\n[dry-run] không gọi provider nào. Đã cấu hình: {configured() or '(chưa có key)'}")
        return

    written: dict[str, str] = {}
    if args.answers:
        # Someone read the same prompt and wrote the question by hand or in a chat
        # session. It is no more trusted than an API reply: same validate(), same
        # row, and --model must name who wrote it.
        if not args.model:
            raise SystemExit("--answers needs --model naming who wrote the questions")
        written = {r["lineage_id"]: r["question"] for r in map(json.loads, args.answers.open(encoding="utf-8"))}
        pending = [(lid, recs) for lid, recs in pending if lid in written]
    provider = "claude-code" if args.answers else pick(args.provider)
    stats: collections.Counter[str] = collections.Counter()
    with out_path.open("a", encoding="utf-8") as out:
        for n, (lid, records) in enumerate(pending, 1):
            message, context, answer = user_prompt(records)
            try:
                done_completion = (Completion(written[lid].strip(), provider, args.model, None) if args.answers
                                   else complete(system, message, provider=provider, model=args.model,
                                                 temperature=args.temperature))
            except LLMError as error:
                print(f"\n{error}")
                print(f"dừng ở {n - 1}/{len(pending)}; chạy lại để tiếp tục từ đây")
                break
            reason = validate(done_completion.text, context, answer)
            stats["ok" if reason is None else reason.split(":")[0]] += 1
            out.write(json.dumps({
                "lineage_id": lid,
                "group": args.group,
                "question": done_completion.text if reason is None else None,
                "rejected_reason": reason,
                "raw": done_completion.text if reason is not None else None,
                "provider": done_completion.provider,
                "model": done_completion.model,
                "temperature": done_completion.temperature,
                "prompt_sha": prompt_sha,
                "generated_at": datetime.now(timezone.utc).date().isoformat(),
            }, ensure_ascii=False) + "\n")
            out.flush()
            if n % 25 == 0 or n == len(pending):
                print(f"  {n:,}/{len(pending):,}  " +
                      "  ".join(f"{k}={v}" for k, v in stats.most_common()), flush=True)

    kept = stats["ok"]
    total = sum(stats.values())
    if total:
        print(f"\n{kept:,}/{total:,} giữ được ({kept / total * 100:.1f}%) -> {out_path}")
        for reason, count in stats.most_common():
            if reason != "ok":
                print(f"   loại {count:>5,}  {reason}")


if __name__ == "__main__":
    main()

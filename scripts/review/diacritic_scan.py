#!/usr/bin/env python3
"""ViLexTime — đáp án có chữ hỏng dấu do trích xuất (DATASET_GAP G11; hướng dẫn 3.0 §3 bước 1).

Scorer chuẩn hoá nhưng giữ dấu, nên đáp án chứa "sản xuât" chấm sai câu trả lời viết đúng chính tả.
Ba phép thử trên `context` (lời văn gold) và `answer` (đáp án ngắn) của mọi dòng có đáp án:

1. chính tả: âm tiết tận cùng p, t, c, ch mang dấu phụ (â, ơ, ư…) mà thanh không phải sắc hay nặng
   ("xuât", "côt") — tiếng Việt không có âm tiết như vậy;
2. ký tự ẩn giữa chữ: gạch nối mềm, khoảng trắng rộng 0, ký tự thay thế ("Thủ tr\u00adưởng");
3. tần suất: cặp hai âm tiết gần như không có trong kho (`asis.jsonl`), trong khi một cặp chỉ khác
   dấu xuất hiện nhiều lần hơn hẳn ("giây phép" so với "giấy phép").

Chỉ là ứng viên: dòng có chữ hỏng thật thì người kiểm gán `gold_wrong`, không sửa tay lời văn.

    python scripts/review/diacritic_scan.py         # -> data/review/chu_hong_dau.tsv
"""
from __future__ import annotations

import collections
import csv
import json
import re
import unicodedata
from pathlib import Path

WORD = re.compile(r"[^\W\d_]+")
HIDDEN = re.compile(r"\w*([\u00ad\u200b-\u200d\u2060\ufeff\ufffd])\w*")
TONES = {"̀": "huyen", "́": "sac", "̉": "hoi", "̃": "nga", "̣": "nang"}
MARKS = {"̂", "̆", "̛"}                        # â ê ô · ă · ơ ư
RARE, COMMON, RATIO = 3, 200, 50   # chỉnh 24/10: ~nửa số chỗ là lỗi thật                            # cặp hiếm, cặp đúng phổ biến, chênh tối thiểu


def strip(word: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", word) if not unicodedata.combining(c)).replace("đ", "d")


def bad_syllable(word: str) -> bool:
    """Checked syllable (final p/t/c/ch) with a vowel mark but a tone other than sắc or nặng."""
    w = unicodedata.normalize("NFD", word.lower())
    base = "".join(c for c in w if not unicodedata.combining(c))
    if not re.fullmatch(r"[a-zđ]*[aeiouy][a-z]*(p|t|c|ch)", base) or not (MARKS & set(w) or "đ" in w):
        return False
    return not ({"sac", "nang"} & {TONES[c] for c in w if c in TONES})


def pairs(text: str) -> list[tuple[str, str]]:
    """Adjacent syllables inside one run of words: "khai, phường" is not the pair "khai phường"."""
    out = []
    for run in re.split(r"[^\w\s]|\d|\n", text.lower()):
        words = WORD.findall(run)
        out += zip(words, words[1:])
    return out


def main(data: Path = Path("data")) -> None:
    rows = [json.loads(line) for line in open(data / "vilextime_dataset/vilextime.jsonl", encoding="utf-8")]
    rows = [r for r in rows if r.get("answerable") and (r.get("context") or r.get("answer"))]
    keys = {f"{strip(a)} {strip(b)}" for r in rows for f in ("context", "answer") for a, b in pairs(r.get(f) or "")}
    counts: dict[str, collections.Counter] = collections.defaultdict(collections.Counter)
    memo: dict[str, str] = {}
    for line in open(data / "derived/corpus/asis.jsonl", encoding="utf-8"):
        text = json.loads(line).get("text") or ""
        for a, b in pairs(text):
            sa, sb = memo.get(a) or memo.setdefault(a, strip(a)), memo.get(b) or memo.setdefault(b, strip(b))
            key = f"{sa} {sb}"
            if key in keys:
                counts[key][f"{a} {b}"] += 1
    out = []
    for r in rows:
        for field in ("context", "answer"):
            found = []
            for w in WORD.findall(r.get(field) or ""):
                if bad_syllable(w):
                    found.append((w, "chính tả", ""))
            for m in HIDDEN.finditer(r.get(field) or ""):
                found.append((m.group(0), "ký tự ẩn", f"U+{ord(m.group(1)):04X}"))
            for a, b in pairs(r.get(field) or ""):
                seen = counts[f"{strip(a)} {strip(b)}"]
                best, n = seen.most_common(1)[0] if seen else ("", 0)
                if seen[f"{a} {b}"] <= RARE and n >= COMMON and n >= RATIO * max(seen[f"{a} {b}"], 1) and best != f"{a} {b}":
                    found.append((f"{a} {b}", "tần suất", f"{best} ({n} lần)"))
            for w, how, should in dict.fromkeys(found):
                out.append({"id": r["id"], "lineage_id": r["lineage_id"], "split": r["split"], "group": r["group"],
                            "cot": field, "chu": w, "cach_bat": how, "goi_y": should})
    path = data / "review/chu_hong_dau.tsv"
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["id", "lineage_id", "split", "group", "cot", "chu", "cach_bat", "goi_y"],
                           delimiter="\t", lineterminator="\n")
        w.writeheader()
        w.writerows(out)
    words = collections.Counter(o["chu"] for o in out)
    print(f"{path}: {len(out)} chỗ, {len({o['id'] for o in out})} dòng, {len({o['lineage_id'] for o in out})} lineage")
    for word, n in words.most_common(40):
        print(f"  {n:>4}  {word}")


if __name__ == "__main__":
    assert bad_syllable("xuât") and bad_syllable("Côt") and not bad_syllable("xuất") and not bad_syllable("thuộc")
    assert not bad_syllable("chat") and not bad_syllable("Internet") and not bad_syllable("được")
    main()

"""Turning retrieved units into the answer the scorer reads (plan phase-5-6, P1/P3).

The generator is `vilexgraph.llm.complete` — already multi-provider over the
`chat/completions` shape, already retrying, already refusing a truncated
answer, and configured entirely from `.env`. Anthropic is deliberately absent
from that table, which keeps out half of the standing conflict-of-interest rule:
ViLexTime's short answers and about two thirds of its questions were written by a
Claude model, and the rest of the questions — nearly all of H3 — by DeepSeek, so the
main results column must be neither family (ADR 0004 §3, extended 11/10). DeepSeek
stays in the table because it writes questions and may run in a side table.

**Citations are tags, not prose.** Each retrieved unit is labelled `[n]` and the
model is asked to cite labels, which map back to exact unit ids. The scorer also
accepts a written Vietnamese citation, but a written one "names no version", so
VCR is undefined for a row that cites only in writing. Tags keep every citation
version-exact, which is what formulas (6) and (7) measure.

**Nothing here sees a gold field.** `answer()` takes a question, a date and the
retrieved units. The runner is what guarantees that, and `tests/test_rag_generate.py`
asserts a gold string never reaches the prompt.
"""
from __future__ import annotations

import hashlib
import json
import re
import sqlite3
from dataclasses import dataclass
from pathlib import Path

from .. import llm

SYSTEM = """Bạn là trợ lý pháp luật Việt Nam. Bạn trả lời câu hỏi về nội dung quy định \
tại MỘT MỐC THỜI GIAN cụ thể.

Quy tắc:
1. Chỉ dùng các đoạn căn cứ được cung cấp. Không dùng kiến thức ngoài.
2. Trả lời bằng cách trích đúng lời văn của quy định tại mốc thời gian được hỏi. \
Không diễn giải lại, không rút gọn, không thêm bình luận.
3. HIỆU LỰC là một khẳng định, không phải chỗ để tránh trả lời:
   - ghi "còn" nếu quy định có hiệu lực tại mốc đó;
   - ghi "không" CHỈ KHI các căn cứ cho thấy quy định đã hết hiệu lực hoặc chưa có hiệu \
lực tại mốc đó — đây là một khẳng định về pháp lý;
   - ghi "không rõ" nếu bạn không xác định được. Đừng ghi "không" khi ý bạn là "không biết".
4. Căn cứ phải dẫn theo nhãn [n] của đoạn bạn đã dùng, ở mức Điều/Khoản/Điểm.
5. Nhiều phiên bản của cùng một điều khoản có thể xuất hiện. Chỉ dùng phiên bản \
có hiệu lực tại mốc được hỏi; không liệt kê mọi phiên bản.

Định dạng bắt buộc, đúng ba dòng:
TRẢ LỜI: <lời văn quy định, hoặc để trống nếu không trả lời được>
HIỆU LỰC: còn|không|không rõ
CĂN CỨ: [n], [m]"""

# B1 has no evidence at all, and the rules above then push a model toward
# "HIỆU LỰC: không" for want of anything to read — which would score B1's
# abstentions as a property of B1 rather than of this prompt. Say so explicitly.
NO_EVIDENCE = """Không có đoạn căn cứ nào được cung cấp.

Ghi đè quy tắc 1 và 3: hãy trả lời dựa trên hiểu biết của bạn về pháp luật Việt Nam tại \
mốc thời gian được hỏi. Chỉ ghi HIỆU LỰC: không khi bạn thực sự biết quy định đó đã hết \
hiệu lực hoặc chưa có hiệu lực tại mốc đó; nếu chỉ là không biết nội dung thì ghi \
HIỆU LỰC: không rõ và vẫn trả lời hết sức mình. Để CĂN CỨ trống vì không có nhãn nào để dẫn."""

# The answer runs until the next label, counting a mistyped one ("HIỆU LỰNG:"),
# so a typo cannot be swallowed into the answer text.
_ANSWER = re.compile(r"^\s*TRẢ\s*LỜI\s*:\s*(.*?)"
                     r"(?=^\s*(?:TRẢ\s*LỜI|HIỆU\s*L\w*|CĂN\s*C\w*)\s*:|\Z)",
                     re.IGNORECASE | re.MULTILINE | re.DOTALL)
# The whole line, not one token: "không rõ" must not truncate to "không".
_FORCE = re.compile(r"^\s*HIỆU\s*LỰC\s*:\s*(.+)$", re.IGNORECASE | re.MULTILINE)
_CITES = re.compile(r"^\s*CĂN\s*CỨ\s*:\s*(.*)$", re.IGNORECASE | re.MULTILINE)
_TAG = re.compile(r"\[(\d+)\]")
# Only the three known labels, allowing a mistyped tail ("HIỆU LỰNG:").
_LOOSE_LABEL = re.compile(r"^\s*(?:TRẢ\s*LỜI|HIỆU\s*L\w*|CĂN\s*C\w*)\s*:", re.IGNORECASE)


@dataclass(frozen=True, slots=True)
class Answer:
    """What one row's prediction needs, plus what produced it."""

    text: str
    answerable: bool
    citations: tuple[str, ...]
    raw: str
    provider: str
    model: str
    cached: bool = False
    prompt_tokens: int | None = None
    completion_tokens: int | None = None


def build_prompt(question: str, as_of: str, units, *, with_context: bool) -> tuple[str, str, list[str]]:
    """The two messages, and the unit id each `[n]` stands for."""
    blocks, ids = [], []
    for n, unit in enumerate(units, 1):
        ids.append(unit.unit_id)
        blocks.append(f"[{n}] {unit.retrieval_text(with_context)}".strip())
    body = "\n\n".join(blocks) if blocks else NO_EVIDENCE
    user = (f"MỐC THỜI GIAN: {as_of}\n"
            f"CÂU HỎI: {question}\n\n"
            f"CÁC ĐOẠN CĂN CỨ:\n{body}")
    return SYSTEM, user, ids


def parse(raw: str, ids: list[str]) -> tuple[str, bool, tuple[str, ...]]:
    """Read the three lines back, tolerantly.

    `answerable=False` is only returned for an explicit "không", which is a legal
    claim that the unit was not in force. "không rõ" — and anything unparseable —
    is *not* that claim, so it stays `answerable=True` with whatever text there
    is, and scores wrong. The distinction matters: a model that declines because
    it does not know would otherwise be scored correct on every genuinely
    unanswerable row, and the reason is the thing this benchmark measures
    (ADR 0003 §3).

    A model that ignores the format still gets its whole output read as the
    answer, minus any line that is a mangled label ("HIỆU LỰNG:"), so a typo
    does not land in the answer text.
    """
    match = _ANSWER.search(raw)
    if match:
        text = match.group(1).strip()
    else:
        kept = [ln for ln in raw.splitlines() if not _LOOSE_LABEL.match(ln)]
        text = "\n".join(kept).strip()
    force = _FORCE.search(raw)
    verdict = _normalise_force(force.group(1) if force else "")
    cite_line = _CITES.search(raw)
    seen, cites = set(), []
    for tag in _TAG.findall(cite_line.group(1) if cite_line else ""):
        index = int(tag) - 1
        if 0 <= index < len(ids) and ids[index] not in seen:
            seen.add(ids[index])
            cites.append(ids[index])
    if verdict == "expired":
        text = ""
    return text, verdict != "expired", tuple(cites)


def format_ok(raw: str, citations: tuple[str, ...], *, has_evidence: bool) -> bool:
    """B1 gate: required fields, plus a usable citation when evidence was supplied."""
    return bool(_ANSWER.search(raw) and _FORCE.search(raw) and _CITES.search(raw)
                and (not has_evidence or citations))


def _normalise_force(value: str) -> str:
    """"còn" | "không" | "không rõ" -> in_force | expired | unknown.

    "không rõ" starts with "không", so it has to be tested first.
    """
    cleaned = " ".join(value.strip().lower().split())
    if cleaned.startswith(("không rõ", "khong ro", "unknown", "unclear")):
        return "unknown"
    if cleaned.startswith(("không", "khong", "no")):
        return "expired"
    if cleaned.startswith(("còn", "con", "yes", "valid")):
        return "in_force"
    return "unknown"


class Cache:
    """Prompt -> completion, on disk.

    Not an optimisation: the full grid is roughly 2.481 rows x 14 systems, and a
    free-tier provider will not serve that twice.
    """

    def __init__(self, path: Path | str | None) -> None:
        self.db = None
        if path is None:
            return
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(path)
        self.db.execute("CREATE TABLE IF NOT EXISTS completions ("
                        "key TEXT PRIMARY KEY, provider TEXT, model TEXT, raw TEXT)")
        self.db.commit()

    @staticmethod
    def key(system: str, user: str, provider: str | None, model: str | None) -> str:
        payload = json.dumps([system, user, provider, model], ensure_ascii=False)
        return hashlib.sha256(payload.encode()).hexdigest()

    def get(self, key: str):
        if self.db is None:
            return None
        return self.db.execute(
            "SELECT provider, model, raw FROM completions WHERE key=?", (key,)).fetchone()

    def put(self, key: str, provider: str, model: str, raw: str) -> None:
        if self.db is None:
            return
        self.db.execute("INSERT OR REPLACE INTO completions VALUES (?,?,?,?)",
                        (key, provider, model, raw))
        self.db.commit()

    def close(self) -> None:
        if self.db is not None:
            self.db.close()


def answer(question: str, as_of: str, units, *, with_context: bool = True,
           provider: str | None = None, model: str | None = None,
           cache: Cache | None = None, **kwargs) -> Answer:
    """One answer for one (question, t). Never receives a gold field."""
    system, user, ids = build_prompt(question, as_of, units, with_context=with_context)
    key = Cache.key(system, user, provider, model)
    hit = cache.get(key) if cache else None
    if hit is not None:
        used_provider, used_model, raw = hit
        cached = True
        prompt_tokens = completion_tokens = None
    else:
        completion = llm.complete(system, user, provider=provider, model=model, **kwargs)
        used_provider, used_model, raw = completion.provider, completion.model, completion.text
        cached = False
        prompt_tokens, completion_tokens = completion.prompt_tokens, completion.completion_tokens
        if cache:
            cache.put(key, used_provider, used_model, raw)
    text, answerable, citations = parse(raw, ids)
    return Answer(text, answerable, citations, raw, used_provider, used_model, cached,
                  prompt_tokens, completion_tokens)

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
3. Nhiều phiên bản của cùng một điều khoản có thể xuất hiện. Chỉ dùng phiên bản \
có hiệu lực tại mốc được hỏi; không liệt kê mọi phiên bản.
4. Nếu nội dung được hỏi đã chuyển sang điều khoản hoặc văn bản khác, và căn cứ có quy định \
đang điều chỉnh đúng nội dung đó tại mốc được hỏi, thì trả lời theo quy định đó.
5. HIỆU LỰC là một khẳng định, không phải chỗ để tránh trả lời:
   - ghi "còn" nếu quy định dùng để trả lời có hiệu lực tại mốc đó;
   - ghi "không" CHỈ KHI các căn cứ cho thấy quy định được hỏi đã hết hiệu lực hoặc chưa có \
hiệu lực tại mốc đó — đây là một khẳng định về pháp lý. Lệnh bãi bỏ một Điều, Khoản, Mục, \
Chương hoặc cả văn bản cũng làm mọi phần nằm trong đó hết hiệu lực, kể từ ngày lệnh có hiệu \
lực. Khi đó để trống TRẢ LỜI và dẫn nhãn của lệnh bãi bỏ ở CĂN CỨ;
   - ghi "không rõ" nếu bạn không xác định được. Thiếu căn cứ không phải là bằng chứng bãi \
bỏ. Đừng ghi "không" khi ý bạn là "không biết".
   Lệnh sửa đổi, bổ sung, hoặc lệnh bãi bỏ một phần khác không làm quy định được hỏi hết \
hiệu lực.
6. Mục THÔNG BÁO BÃI BỎ TỪ ĐỒ THỊ, nếu có, là căn cứ về việc bãi bỏ. Áp dụng quy tắc 5 khi \
đích bị bãi bỏ là quy định được hỏi hoặc phần chứa quy định đó, và ngày hiệu lực không sau \
mốc được hỏi.
7. Căn cứ phải dẫn theo nhãn [n] của đoạn bạn đã dùng, ở mức Điều/Khoản/Điểm.

Định dạng bắt buộc, đúng ba dòng:
TRẢ LỜI: <lời văn quy định, hoặc để trống nếu không trả lời được>
HIỆU LỰC: còn|không|không rõ
CĂN CỨ: [n], [m]"""

# B1 has no evidence at all, and the rules above would then push a model toward
# "HIỆU LỰC: không" for want of anything to read, which would score B1's abstentions
# as a property of B1 rather than of this prompt. It gets its own system message: an
# override placed in the user turn loses to the system rule on models that rank them.
SYSTEM_NO_EVIDENCE = """Bạn là trợ lý pháp luật Việt Nam. Bạn trả lời câu hỏi về nội dung \
quy định tại MỘT MỐC THỜI GIAN cụ thể. Không có đoạn căn cứ nào được cung cấp, nên hãy trả \
lời hết sức mình dựa trên hiểu biết của bạn về pháp luật Việt Nam tại mốc đó.

HIỆU LỰC là một khẳng định, không phải chỗ để tránh trả lời:
- ghi "còn" nếu quy định có hiệu lực tại mốc đó;
- ghi "không" CHỈ KHI bạn thực sự biết quy định đã hết hiệu lực hoặc chưa có hiệu lực tại mốc đó;
- ghi "không rõ" nếu bạn không biết, và vẫn trả lời hết sức mình.

Định dạng bắt buộc, đúng ba dòng:
TRẢ LỜI: <nội dung quy định>
HIỆU LỰC: còn|không|không rõ
CĂN CỨ:"""

USER = "MỐC THỜI GIAN: {as_of}\nCÂU HỎI: {question}\n\nCÁC ĐOẠN CĂN CỨ:\n{body}"
REPEAL_NOTES = "\n\nTHÔNG BÁO BÃI BỎ TỪ ĐỒ THỊ:\n"

# A label counts at the start of a line (any case) or, for a one-line answer, after a space
# in capitals ("TRẢ LỜI: x HIỆU LỰC: không CĂN CỨ: [1]"). A value ends at the next capital label
# on the same line or at the end of the line; the last label of each kind wins.
_NEXT = r"(?-i:HIỆU\s*L\w*|CĂN\s*C\w*|TRẢ\s*LỜI)\s*:"


def _label(body: str, value: str) -> re.Pattern:
    return re.compile(rf"(?:(?i:^[ \t]*{body})|(?<=\s)(?-i:{body}))\s*:\s*({value})(?=[ \t]+{_NEXT}|$)",
                      re.IGNORECASE | re.MULTILINE)


# The answer runs until the next label, counting a mistyped one ("HIỆU LỰNG:"),
# so a typo cannot be swallowed into the answer text.
_ANSWER = re.compile(r"^\s*TRẢ\s*LỜI\s*:\s*(.*?)"
                     r"(?=^\s*(?:TRẢ\s*LỜI|HIỆU\s*L\w*|CĂN\s*C\w*)\s*:|\s(?-i:HIỆU\s*L\w*|CĂN\s*C\w*)\s*:|\Z)",
                     re.IGNORECASE | re.MULTILINE | re.DOTALL)
# The whole value, not one token: "không rõ" must not truncate to "không".
_FORCE = _label(r"HIỆU\s*LỰC", ".+?")
_CITES = _label(r"CĂN\s*CỨ", ".*?")
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


def validity_line(windows) -> str:
    """Half-open windows `[(start, end or None), ...]` as one prompt line (`bvdate`, post hoc 13/11)."""
    spans = "; ".join(f"từ {start} đến trước {end}" if end else f"từ {start}, chưa có ngày kết thúc"
                      for start, end in windows if start)
    return f"(Hiệu lực của đoạn này: {spans or 'không có khoảng hiệu lực nào'})"


def build_prompt(question: str, as_of: str, units, *, with_context: bool,
                 repeal_notes=(), validity=None) -> tuple[str, str, list[str]]:
    """The two messages, and the unit id each `[n]` stands for.

    `validity` maps a unit id to its windows; when given, each block ends with them.
    """
    blocks, ids = [], []
    for n, unit in enumerate(units, 1):
        ids.append(unit.unit_id)
        block = f"[{n}] {unit.retrieval_text(with_context)}".strip()
        if validity is not None:
            block += "\n" + validity_line(validity.get(unit.unit_id, ()))
        blocks.append(block)
    body = "\n\n".join(blocks) if blocks else "(không có)"
    user = USER.format(as_of=as_of, question=question, body=body)
    lines = [note.prompt_line(ids.index(note.unit_id) + 1) for note in repeal_notes
             if note.unit_id in ids]
    if lines:
        user += REPEAL_NOTES + "\n".join(lines)
    return (SYSTEM if blocks else SYSTEM_NO_EVIDENCE), user, ids


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
    force = _last(_FORCE, raw)
    verdict = _normalise_force(force.group(1) if force else "")
    cite_line = _last(_CITES, raw)
    seen, cites = set(), []
    for tag in _TAG.findall(cite_line.group(1) if cite_line else ""):
        index = int(tag) - 1
        if 0 <= index < len(ids) and ids[index] not in seen:
            seen.add(ids[index])
            cites.append(ids[index])
    if verdict == "expired":
        text = ""
    return text, verdict != "expired", tuple(cites)


def _last(pattern: re.Pattern, raw: str):
    found = list(pattern.finditer(raw))
    return found[-1] if found else None


def format_ok(raw: str, citations: tuple[str, ...], *, has_evidence: bool) -> bool:
    """B1 gate: required fields, plus a usable citation when evidence was supplied."""
    return bool(_ANSWER.search(raw) and _last(_FORCE, raw) and _last(_CITES, raw)
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
    def key(system: str, user: str, provider: str | None, model: str | None, *,
            temperature: float = 0.0, max_tokens: int = 4096, effort: str | None = None) -> str:
        payload = json.dumps(["completion-v2", system, user, provider, model,
                              float(temperature), max_tokens, effort or None], ensure_ascii=False)
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
           cache: Cache | None = None, repeal_notes=(), temperature: float = 0.0,
           max_tokens: int = 4096, effort: str | None = None, **kwargs) -> Answer:
    """One answer for one (question, t). Never receives a gold field."""
    system, user, ids = build_prompt(question, as_of, units, with_context=with_context,
                                     repeal_notes=repeal_notes)
    if cache is not None and cache.db is not None:
        # A missing explicit model is not a stable identity: .env may have changed.
        provider = llm.pick(provider)
        model = llm.model_for(provider, model)
    key = Cache.key(system, user, provider, model, temperature=temperature,
                    max_tokens=max_tokens, effort=effort)
    hit = cache.get(key) if cache else None
    if hit is not None:
        used_provider, used_model, raw = hit
        cached = True
        prompt_tokens = completion_tokens = None
    else:
        completion = llm.complete(system, user, provider=provider, model=model,
                                  temperature=temperature, max_tokens=max_tokens, effort=effort, **kwargs)
        used_provider, used_model, raw = completion.provider, completion.model, completion.text
        cached = False
        prompt_tokens, completion_tokens = completion.prompt_tokens, completion.completion_tokens
        if cache:
            cache.put(key, used_provider, used_model, raw)
    text, answerable, citations = parse(raw, ids)
    return Answer(text, answerable, citations, raw, used_provider, used_model, cached,
                  prompt_tokens, completion_tokens)

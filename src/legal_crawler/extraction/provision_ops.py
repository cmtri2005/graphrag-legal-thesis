"""L2 — provision-level operations read from an acting document's own text.

The portal says *that* a document was partly repealed, rarely *which*
provision, and never *by whom* when several documents act on it
(docs/crawling-plan.md §6c). The acting document says both, in running text:
"Bãi bỏ khoản 2 Điều 11 Nghị định số 78/2016/NĐ-CP", or an article headed
"Sửa đổi, bổ sung một số điều của Nghị định số X như sau:" whose numbered
items name "khoản 2 Điều 5" without repeating X. This module turns that text
into (operation, locators, cited document number) mentions. It resolves
nothing: the number and locators go through `TargetResolver` like every
other reference, so a mention only becomes a provision id deterministically.

Precision over recall, because a wrong repeal date is a silent wrong answer:

* quoted text (“…”) is the new wording, never an instruction — dropped first;
* only the first document cited in a statement is its target; later ones are
  usually that document's own title ("Nghị định số 09/2001/NĐ-CP … sửa đổi
  Điều 21 Nghị định số 05-CP") and are ignored;
* an operation must open its statement, open the list it belongs to, or
  follow the citation passively ("… hết hiệu lực", "được sửa đổi");
* anything pointing at the acting document itself ("Nghị định này",
  "khoản 4 Điều này") is skipped.
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass

from legal_crawler.temporal.models import LegalOperation, ProvisionLevel

from .models import ProvisionLocator, ProvisionReferencePart

L = ProvisionLevel
_ORDER = {L.PART: 0, L.CHAPTER: 1, L.SECTION: 2, L.SUBSECTION: 3, L.ARTICLE: 4, L.CLAUSE: 5, L.POINT: 6}
_KEYWORD_LEVEL = {"phần": L.PART, "chương": L.CHAPTER, "mục": L.SECTION,
                  "điều": L.ARTICLE, "khoản": L.CLAUSE, "điểm": L.POINT}
_NUMBERED = re.compile(r"\d+[a-zđ]?")
_LABEL_OK = {L.ARTICLE: _NUMBERED, L.CLAUSE: _NUMBERED, L.POINT: re.compile(r"[a-zđ]")}
_OUTER_LABEL = re.compile(r"[IVXLCDM]+|\d+")

_W = r"[\wÀ-ỹ]"
_TOKEN = re.compile(
    rf"(?<!{_W})(?P<kw>[Pp]hần|[Cc]hương|[Mm]ục|[Đđ]iều|[Kk]hoản|[Đđ]iểm)\s+"
    rf"(?P<label>[IVXLCDM]+|\d+[a-zđ]?|[a-zđ])(?!{_W})"
    rf"|(?P<sep>,|;|(?<!{_W})(?:và|hoặc|đến)(?!{_W}))\s*(?P<bare>[IVXLCDM]+|\d+[a-zđ]?|[a-zđ])(?![\wÀ-ỹ/])"
)

_DOC_TYPE = (r"(?i:bộ luật|luật|pháp lệnh|nghị quyết(?:\s+liên tịch)?|nghị định|quyết định"
             r"|thông tư(?:\s+liên tịch)?|chỉ thị|sắc lệnh|lệnh)")
_NUM = (r"\d{1,4}\s[A-ZĐ]{2,}(?:\s?[/\-]\s?[\wĐđ&().]+)+"
        r"|\d{1,4}(?:\s?[/\-]\s?[\wĐđ&().]+)+")
_CITE = re.compile(
    rf"(?<!{_W})(?:{_DOC_TYPE}\s+(?:(?i:số)\s*)?(?P<num>{_NUM})"
    rf"|(?i:bộ luật|luật|pháp lệnh)(?:\s+(?!này(?!{_W}))[^\s,;.:]+){{1,8}}?\s+(?i:số)\s*(?P<named>{_NUM})"
    rf"|{_DOC_TYPE}\s+(?P<self>này)(?!{_W}))"
)
_SELF_LOCATOR = re.compile(rf"(?<!{_W})(?:[Đđ]iều|[Kk]hoản|[Đđ]iểm|[Cc]hương|[Mm]ục)\s+này(?!{_W})")
_LEADING_LOCATOR = re.compile(r"(?:[Cc]ác\s+)?(?:[Đđ]iều|[Kk]hoản|[Đđ]iểm|[Mm]ục|[Cc]hương|[Pp]hần)\s")

_OPS = (r"sửa đổi,?\s+bổ sung|sửa đổi|bổ sung|bãi bỏ|hủy bỏ|huỷ bỏ|thay thế|thay(?=\s+(?:các\s+)?(?:cụm\s+)?từ\s)"
         r"|đính chính|tạm ngưng|đình chỉ")
_ACTIVE = re.compile(
    rf"^(?:{_DOC_TYPE}\s+này\s+(?:(?i:cũng)\s+)?|(?i:nay|đồng thời)\s+)?(?P<op>(?i:{_OPS}))(?!{_W})"
)
_PASSIVE = re.compile(
    r"(?i:(?P<op>được sửa đổi(?:,?\s+bổ sung)?|được bổ sung|được thay thế|bị thay thế"
    r"|được bãi bỏ|bị bãi bỏ|bị hủy bỏ|bị huỷ bỏ|hết hiệu lực|(?:đều\s+)?bãi bỏ(?=\s*[.;]?\s*$)))"
)
# "… Nghị định số X (đã) được sửa đổi, bổ sung tại/bởi Nghị định số Y" is X's
# history, told in passing; the act being performed is elsewhere in the text.
_HISTORY_AFTER = re.compile(r"\s*(?i:tại|bởi|theo)(?!\w)")
_HISTORY_BEFORE = re.compile(r"(?i:đã)\s*$")
# A phrase edit ("bãi bỏ/thay/bổ sung cụm từ … tại khoản 2") or a subject-limited
# repeal ("bãi bỏ quy định về X tại Điều 5") rewrites the provision; it survives.
_PHRASE = re.compile(
    r"(?<!\w)(?i:cụm từ|khái niệm)(?!\w)|(?<!\w)(?i:từ|chữ|nội dung)\s+(?:«Q»|[\"“'])|^\s*(?i:các\s+)?(?i:từ|chữ)\s"
)
# "Bãi bỏ quy định hướng dẫn thực hiện Điều 41 Nghị định X tại Thông tư Y" acts
# on Y; X is only what Y implemented. Too tangled to resolve: skipped.
_GUIDANCE_OF = re.compile(r"(?i:hướng dẫn\s+(?:thực hiện|thi hành))")
_QUOTE_LINE = re.compile(r"[«Q»\s.,;:”\"']*")
# Only "quy định về/liên quan …": "Bãi bỏ một số nội dung của các Thông tư sau:" or
# "các nội dung quy định tại:" just open a list whose items go whole.
_SUBJECT_LIMITED = re.compile(
    r"^\s*(?i:các\s+)?(?i:một số\s+)?(?:(?i:nội dung)\s+)?(?i:quy định)\s+(?i:về|liên quan)"
)
_PARENTHETICAL = re.compile(r"\s\([^()]*\)")
_TEXT_EDITS = (LegalOperation.REPEAL, LegalOperation.REPLACE, LegalOperation.SUPPLEMENT)
_STOP = re.compile(r"\s(?i:như sau|vào sau|vào trước|vào|bằng)(?!\w)")
_AT = re.compile(r"(?<!\w)(?i:tại)(?!\w)")
_EXCEPT = re.compile(r"(?<!\w)(?i:trừ)(?!\w)")
_MARKER = re.compile(r"^(?P<num>\d+[a-zđ]?\.(?!\d))\s*|^(?P<letter>[a-zđ]\))\s*|^(?P<dash>[-–+•])\s*")
_ARTICLE_HEAD = re.compile(r"^Điều\s+\d+[a-zđ]?\s*[.:\-–]\s*")
_SENTENCE = re.compile(r"(?<=\.)\s+(?=[A-ZĐ])")
_QUOTE_MARK = "«Q»"
_WHOLE_DOC_OPS = (LegalOperation.REPEAL, LegalOperation.REPLACE, LegalOperation.SUSPEND)


def _op_of(phrase: str) -> LegalOperation:
    p = phrase.casefold()
    if any(w in p for w in ("bãi bỏ", "hủy bỏ", "huỷ bỏ", "hết hiệu lực")):
        return LegalOperation.REPEAL
    if p.startswith("thay") or "thay thế" in p:
        return LegalOperation.REPLACE
    if "sửa đổi" in p:
        return LegalOperation.AMEND
    if "bổ sung" in p:
        return LegalOperation.SUPPLEMENT
    if "đính chính" in p:
        return LegalOperation.CORRECT
    return LegalOperation.SUSPEND


# Look-alikes the portal's own `docNum` fields use and running text does not:
# Latin Eth for Đ, Cyrillic letters in "TT-BTС" / "NĐ-СР", and "QD" for "QĐ".
_LOOKALIKE = str.maketrans({"ð": "d", "đ": "d", "с": "c", "р": "p", "о": "o", "а": "a",
                            "е": "e", "т": "t", "н": "h", "к": "k", "м": "m", "в": "b", "х": "x"})


def normalize_number(value: str) -> str:
    """One key for "14-CP"/"14/CP", "64 TC/TCT"/"64/TC-TCT", "BGD&ĐT"/"BGDĐT", "09/2019"/"9/2019"."""
    text = unicodedata.normalize("NFC", value).casefold().translate(_LOOKALIKE)
    text = re.sub(r"[&'’]", "", text)
    text = re.sub(r"[\s/\-]+", "/", text).strip("/.,;")
    if text.count("(") < text.count(")"):
        text = text.rstrip(")")
    return "/".join(p.lstrip("0") or "0" if p.isdigit() else p for p in text.split("/"))


@dataclass(frozen=True, slots=True)
class Mention:
    operation: LegalOperation
    locators: tuple[ProvisionLocator, ...]  # empty: the whole cited document
    document_number: str
    method: str  # explicit | forward | list_forward | intro | article_context | title_context
    evidence: str


def parse_locators(segment: str) -> list[dict[ProvisionLevel, str]]:
    """"điểm b khoản 1, khoản 2 Điều 5" -> [{Điểm b, Khoản 1, Điều 5}, {Khoản 2, Điều 5}].

    Vietnamese writes a path inner-to-outer; an outer word closes every inner
    item waiting for it. Mục/Chương written right after an article list only
    qualify it (article numbers are unique within a document).
    """
    tokens: list[tuple[ProvisionLevel, str, str]] = []
    last_level: ProvisionLevel | None = None
    last_end = 0
    for m in _TOKEN.finditer(segment):
        between = segment[last_end:m.start()]
        if m.group("kw"):
            level, label = _KEYWORD_LEVEL[m.group("kw").casefold()], m.group("label")
        else:
            # "Điều 5, 6" continues a list; "Điều 19, Phụ lục 1, 2" does not —
            # a bare number only inherits a level when nothing else intervenes.
            if last_level is None or between.strip():
                last_level = None
                continue
            level, label, between = last_level, m.group("bare"), between + m.group("sep")
        last_end = m.end()
        if not _LABEL_OK.get(level, _OUTER_LABEL).fullmatch(label):
            continue
        if re.search(r"(?<!\w)đến(?!\w)", between):
            sep = "list"
            prev_level, prev_label, _ = tokens[-1] if tokens else (None, "", "")
            if prev_level is level and prev_label.isdigit() and label.isdigit():
                tokens.extend((level, str(n), "list") for n in range(int(prev_label) + 1, int(label)))
        else:
            sep = "list" if re.search(r"[,;]|(?<!\w)(?:và|hoặc)(?!\w)", between) else "adj"
        tokens.append((level, label, sep))
        last_level = level

    emitted: list[dict[ProvisionLevel, str]] = []
    waiting: list[dict[ProvisionLevel, str]] = []  # items not yet given their Điều
    prev: ProvisionLevel | None = None
    for level, label, sep in tokens:
        rank = _ORDER[level]
        if level is L.ARTICLE:
            if waiting:  # "khoản 1 và điểm b khoản 8 Điều 3": both are in Điều 3
                for item in waiting:
                    item.setdefault(level, label)
                emitted.extend(waiting)
                waiting = []
            else:
                emitted.append({level: label})
        elif rank > _ORDER[L.ARTICLE]:
            if not waiting and sep == "adj" and prev is L.ARTICLE and emitted and level not in emitted[-1]:
                emitted[-1][level] = label  # "Điều 5 khoản 2"
            else:
                inner = [it for it in waiting if level not in it and max(_ORDER[k] for k in it) > rank]
                for item in inner:  # "điểm a, điểm b khoản 2": both points are in khoản 2
                    item[level] = label
                if not inner:
                    waiting.append({level: label})
        elif waiting:
            for item in waiting:
                item.setdefault(level, label)
        elif not (prev is not None and _ORDER[prev] > rank and emitted):
            waiting.append({level: label})  # a standalone Chương/Mục; else it qualifies the last item
        prev = level
    emitted.extend(waiting)
    return emitted


def _locator(parts: dict[ProvisionLevel, str]) -> ProvisionLocator:
    ordered = sorted(parts.items(), key=lambda kv: _ORDER[kv[0]])
    return ProvisionLocator(tuple(ProvisionReferencePart(level, label) for level, label in ordered))


def _drop_quotes(text: str) -> str:
    """Remove every balanced “…” span; an unclosed one is left in place."""
    out, depth, start, last = [], 0, 0, 0
    for i, ch in enumerate(text):
        if ch == "“":
            if depth == 0:
                start = i
            depth += 1
        elif ch == "”" and depth:
            depth -= 1
            if depth == 0:
                out.append(text[last:start])
                out.append(f" {_QUOTE_MARK} ")
                last = i + 1
    out.append(text[last:])
    return "".join(out)


@dataclass(slots=True)
class _Stmt:
    text: str
    active: LegalOperation | None
    passive: LegalOperation | None
    cite: str | None  # raw number, "self", or None
    locators: list[dict[ProvisionLevel, str]]
    self_ref: bool
    excepted: bool


def _statement(text: str) -> _Stmt:
    active_m = _ACTIVE.match(text)
    op_end = active_m.end() if active_m else 0
    active = _op_of(active_m.group("op")) if active_m else None
    if active in _TEXT_EDITS and (_PHRASE.search(text, op_end) or _SUBJECT_LIMITED.match(text[op_end:])):
        active = LegalOperation.AMEND
    cite_m = _CITE.search(text, op_end)
    cite, cite_start, cite_end = None, len(text), len(text)
    if cite_m:
        cite = "self" if cite_m.group("self") else (cite_m.group("num") or cite_m.group("named"))
        cite_start, cite_end = cite_m.start(), cite_m.end()
    passive_m = None
    if not active_m:
        pos = cite_end if cite_m else 0
        while (m := _PASSIVE.search(text, pos)) is not None:
            if not (_HISTORY_AFTER.match(text, m.end()) or _HISTORY_BEFORE.search(text[:m.start()])):
                passive_m = m
                break
            pos = m.end()
    if cite_m:
        end = cite_start
        if active is LegalOperation.SUPPLEMENT:  # "Bổ sung Điều 5a vào sau Điều 5 …": Điều 5 is only the anchor
            stop = _STOP.search(text, op_end, cite_start)
            end = stop.start() if stop else end
    else:
        stop = _STOP.search(text, op_end)
        end = min(stop.start() if stop else len(text), passive_m.start() if passive_m else len(text))
    guidance = bool(cite_m and _GUIDANCE_OF.search(text, op_end, cite_start))
    phrase = None
    for phrase in _PHRASE.finditer(text, op_end):
        pass  # the last one: "thay cụm từ A bằng cụm từ B tại …"
    # The first "tại" after it; a later one is usually history ("… được bổ sung tại …").
    last_at = _AT.search(text, phrase.end()) if phrase else None
    if last_at:
        # A phrase edit acts where "tại …" points; a number inside the phrase
        # itself ("thay cụm từ «… Nghị định số X» bằng …") is wording, not a target.
        cite_m = _CITE.search(text, last_at.end())
        cite, cite_start, cite_end = None, len(text), len(text)
        if cite_m:
            cite = "self" if cite_m.group("self") else (cite_m.group("num") or cite_m.group("named"))
            cite_start, cite_end = cite_m.start(), cite_m.end()
        locators = parse_locators(text[last_at.end():cite_start])
    else:
        locators = parse_locators(text[op_end:end])
        if not locators:
            at = _AT.search(text, op_end)
            if at and at.end() < cite_start:
                stop = _STOP.search(text, at.end())
                locators = parse_locators(text[at.end():cite_start if cite_m else (stop.start() if stop else len(text))])
    return _Stmt(
        text=text,
        active=active,
        passive=_op_of(passive_m.group("op")) if passive_m else None,
        cite=cite,
        locators=locators,
        self_ref=bool(_SELF_LOCATOR.search(text[:cite_start])) or guidance,
        excepted=bool(cite_m and _EXCEPT.search(text, cite_end)),
    )


def _merge_intro(parts: dict[ProvisionLevel, str], intro: dict[ProvisionLevel, str] | None) -> dict:
    """"a) Sửa đổi khoản 2" under "1. Sửa đổi Điều 5 như sau:" means Điều 5 khoản 2."""
    if not intro or not parts:
        return parts
    outer = min(_ORDER[k] for k in parts)
    return {**{k: v for k, v in intro.items() if _ORDER[k] < outer}, **parts}


def _shared_outer(locs: list[dict[ProvisionLevel, str]]) -> dict[ProvisionLevel, str] | None:
    """The one locator an intro names, or the article all of its locators share.

    "2. Sửa đổi, bổ sung khoản 1, điểm c khoản 3 và điểm b khoản 8 Điều 3 như sau:"
    puts its sub-items in Điều 3 even though it names four targets.
    """
    if len(locs) == 1:
        return locs[0]
    shared = {k: v for k, v in (locs[0] if locs else {}).items()
              if _ORDER[k] <= _ORDER[L.ARTICLE] and all(loc.get(k) == v for loc in locs)}
    return shared or None


@dataclass(slots=True)
class _Intro:
    op: LegalOperation
    locator: dict[ProvisionLevel, str] | None
    doc: str | None


def extract_mentions(paragraphs: list[str], title_doc: str | None = None) -> list[Mention]:
    """Mentions in body order; `title_doc` is the number the actor's title amends, if any."""
    text = "\n".join(paragraphs).replace("Ð", "Đ").replace("ð", "đ")  # "Ðiều" (Latin Eth) is Điều
    lines = [_PARENTHETICAL.sub(" ", line) for line in _drop_quotes(text).split("\n")]
    mentions: list[Mention] = []
    seen: set[tuple] = set()
    article_doc: str | None = None
    level0: _Intro | None = None   # set by a plain line or article heading ending in ":"
    level1: _Intro | None = None   # set by a numbered/dash item ending in ":"
    pending: list[tuple[LegalOperation, list[dict], str]] = []  # letter items waiting for a later citation

    def emit(op, locs, doc, method, evidence):
        if not locs and op not in _WHOLE_DOC_OPS:
            return
        locators = tuple(_locator(p) for p in locs)
        key = (op, normalize_number(doc), tuple(tuple((x.level, x.label) for x in loc.parts) for loc in locators))
        if key not in seen:
            seen.add(key)
            mentions.append(Mention(op, locators, doc, method, evidence[:400]))

    for raw_line in lines:
        line = raw_line.strip()
        if _QUOTE_LINE.fullmatch(line):
            continue  # a quoted paragraph (and its closing "."), not a new instruction
        head = _ARTICLE_HEAD.match(line)
        if head:
            kind, line, article_doc = "head", line[head.end():], None
        else:
            marker = _MARKER.match(line)
            kind = marker.lastgroup if marker else "plain"
            if marker:
                line = line[marker.end():]
        if kind == "head":
            level0 = level1 = None
            pending = []
        elif kind == "num":
            level1 = None
            pending = []
        # An unmarked line under "2. Thay thế … Thông tư số X như sau:" is one of its items.
        intro = (level1 or level0) if kind in ("letter", "plain") else (level0 if kind in ("num", "dash") else None)

        for sentence in _SENTENCE.split(line):
            head_part, colon, rest = sentence.partition(":")
            texts = [head_part, *rest.split(";")] if colon else sentence.split(";")
            stmts = [_statement(t.strip()) for t in texts]
            for i, st in enumerate(stmts):
                if not st.text:
                    continue
                later = next((s.passive for s in stmts[i:] if s.passive and not s.active), None)
                earlier = next((s.active for s in reversed(stmts[:i]) if s.active), None)
                op = st.active or later or earlier or (intro.op if intro else None)
                if op is None or st.cite == "self" or st.self_ref:
                    continue
                if not st.active and op in _TEXT_EDITS and (_PHRASE.search(st.text) or _SUBJECT_LIMITED.match(st.text)):
                    op = LegalOperation.AMEND  # a list item under "Bãi bỏ:" that removes a phrase or a subject
                if not st.active and not earlier and later and not st.cite and not _LEADING_LOCATOR.match(st.text):
                    continue  # a passive clause must name its target or start with one
                doc, method = st.cite, "explicit"
                if doc is None:
                    fwd = next((s.cite for s in stmts[i + 1:] if s.cite), None)
                    if fwd and fwd != "self":
                        doc, method = fwd, "forward"
                    elif intro and intro.doc:
                        doc, method = intro.doc, "intro"
                    elif article_doc:
                        doc, method = article_doc, "article_context"
                    elif title_doc:
                        doc, method = title_doc, "title_context"
                locs = [_merge_intro(p, intro.locator if intro else None) for p in st.locators]
                if colon and i == 0:
                    new_intro = _Intro(op, _shared_outer(locs), doc)
                    if kind == "head":
                        level0 = new_intro
                    elif kind in ("num", "dash", "plain"):
                        level1 = new_intro
                if kind == "head" and i == 0 and st.active and st.cite and not st.locators:
                    article_doc = st.cite
                if doc is None:
                    if locs and kind == "letter":
                        pending.append((op, locs, st.text))
                    continue
                if method == "explicit" and pending:
                    for p_op, p_locs, p_text in pending:
                        emit(p_op, p_locs, doc, "list_forward", p_text)
                    pending = []
                if not locs and (method != "explicit" or st.excepted):
                    continue
                emit(op, locs, doc, method, st.text)
        if kind == "num" and not line.rstrip().endswith(":"):
            level1 = None
    return mentions


def title_document(title: str) -> str | None:
    """The document an amending act names in its own title ("… Sửa đổi Điều 12 Nghị định số X")."""
    cites = list(_CITE.finditer(title))
    if len(cites) < 2:
        return None
    st = _statement(title[cites[0].end():].strip())
    if st.active in (LegalOperation.AMEND, LegalOperation.SUPPLEMENT) and st.cite and st.cite != "self":
        return st.cite
    return None

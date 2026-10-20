#!/usr/bin/env python3
"""ViLexTime — candidate questions with their gold answers (plan phase-4, B1–B4).

Every candidate is derived from `data/derived/versions.jsonl`: the gold answer
at a date is the version whose *effective* window contains it, so the label is
a property of the data, not of any model. An LLM later phrases the question in
Vietnamese and never touches the answer (P4.4).

Groups, per the proposal's structure table. T5 is built as *candidates*:
which retroactive acts fall under Điều 152 is a legal judgement the adviser
makes (plan phase-4, Q3), so every T5 row carries `retroactive` with the
facts that judgement needs, and nothing here decides it.

  T1  one version, unambiguous in time            control
  T2  two versions: same question, two dates      core group
  T3  three or more versions: A -> B -> C         where the graph should pay
  T4  two versions whose texts are near-identical the citation trap
  T5  a change made by a document that takes effect before it was signed
  T6  a Khoản/Điểm that ended inside a document still in force; `repeal_mode`
      says how: "direct" (an event ended it) or "ancestor" (it lost force
      because its Điều, Khoản, Mục or Chương was repealed — H3, decided 28/09)

A provision lands in exactly one group, scarcest first (T5, then T6 "ancestor",
T3, T6 "direct", T4, T2, T1), so no node — and so no text — can appear twice in
the benchmark. The dev/test split is by document for the same reason (Q6) and is
left to P4.9.

The order matters most for T6 "ancestor", which is H3. 10,055 provisions qualify
across 484 documents, and 9,929 of them are *also* T1 candidates — T1 is exactly
where `classify` sends a one-version chain — so while ancestor was written last
its yield was whatever T1's seeded sample happened to leave behind, which was 264
candidates for a 24-row quota. It is written before the cascade's groups now and
takes `--ancestor-quota` x `--per-group-cap`.

Every row also carries the difficulty covariates (`n_versions`, `similarity`,
`similarities`, `substantive_transitions`) rather than only the group whose
definition needs one, and every gold entry says which gap a missing answer is
(`no_answer_reason`) and whether a later version was already signed but not yet
in force at that date (`pending`). Those are facets, not groups: the T2/T4 cut at
NEAR_IDENTICAL is a threshold on a continuous variable, and reporting the
variable lets the analysis slice it without another rebuild.

A candidate must also have a *different* answer at each of its dates, which
11.1% of consecutive version pairs do not: their amendment left the text
character-for-character the same, either because the portal already carried
the amended wording or because the extracted block was that wording. Asking
"what did this say before and after" about those has one answer, so they are
dropped and counted rather than shipped as contrast pairs.

Writes `data/derived/vilextime_pool.jsonl`. Offline, deterministic: delete and
re-run for a byte-identical file.

Usage:
    python scripts/pipeline/build_question_pool.py [--per-group-cap 10]
"""
from __future__ import annotations

import argparse
import collections
import difflib
import hashlib
import json
import random
import re
import sqlite3
from datetime import date, timedelta
from pathlib import Path

ONE_DAY = timedelta(days=1)
# Both from enrich_vilextime.py, which owns them: no row may be asked after the
# corpus snapshot (check_release.py rejects it), and MARGIN is the distance a
# mid-interval twin keeps from a boundary, so a boundary row must stay inside it.
SNAPSHOT = date(2026, 9, 17)
MARGIN = 30
# Quota from the proposal; the pool keeps `cap` times as many candidates so the
# hand-check and the adviser can reject freely without starving a group.
# T4 is no longer a group: its 150 rows are T2's, and `similarity` tells them
# apart as a facet (see `facets_of`). Two humans could not apply the cut — the D4
# cross-check scored kappa 0.054 on T4 against 0.684 on T3, whose "3+ versions"
# is a fact on the page rather than a threshold inside the pipeline — and a pair
# at 0.91 and one at 0.89 landing in separate quotas could not be compared at all.
QUOTA = {"T1": 250, "T2": 550, "T3": 200, "T5": 50, "T6": 100}
PRIORITY = ("T3", "T6", "T2", "T1")  # scarcest first; T5 is taken out after capping
# Kept as the boundary of the *reported* T4 slice, so the proposal's Bang 1 still
# has its row, and as the `near_identical` facet below.
NEAR_IDENTICAL = 0.90
SEED = 20260920
# T6 "ancestor" — the H3 case — is a part with its own quota, not a leftover.
# 10,055 provisions in 484 documents qualify (measured 05/10, read-only replay of
# classify + repealed_by_ancestor), so the old ANCESTOR_CAP = 300 was the only
# thing holding H3 at 12 lineages. 200 is the target at which a paired MDE lands
# near 8-9 pp; `--per-group-cap` multiplies it like every other group's.
ANCESTOR_QUOTA = 200


# The event that opened each version travels with it: joining by the acting document's own
# effective_from misses an amendment dated by a part of the act (5877a5a, TT 13/2019/TT-NHNN).
VERSION_FIELDS = ("id", "ordinal", "text", "effective_from", "effective_to", "created_by_event_id")


def _d(value: str | None) -> date | None:
    return date.fromisoformat(value) if value else None


def in_force_at(versions: list[dict], at: date) -> dict | None:
    """The version whose effective window contains `at`, per [from, to)."""
    for v in versions:
        start, end = _d(v["effective_from"]), _d(v["effective_to"])
        if start and start <= at and (end is None or at < end):
            return v
    return None


# Old and new Vietnamese tone placement ("hoá"/"hóa", "uỷ"/"ủy") are the same word.
_OLD_TONE = re.compile("o[àáảãạ]|o[èéẻẽẹ]|u[ỳýỷỹỵ]")
_LIST_LETTER = re.compile(r"(?<!\w)[a-zđ]\)")
_NEW_TONE = {"oà": "òa", "oá": "óa", "oả": "ỏa", "oã": "õa", "oạ": "ọa",
             "oè": "òe", "oé": "óe", "oẻ": "ỏe", "oẽ": "õe", "oẹ": "ọe",
             "uỳ": "ùy", "uý": "úy", "uỷ": "ủy", "uỹ": "ũy", "uỵ": "ụy"}


def _words(text: str | None) -> str:
    """Case, spacing, punctuation, tone placement and list letters ("a)") removed — what
    `cosmetic_only` compares on. A number is kept: "tại Điều 5." is not a list marker."""
    folded = _OLD_TONE.sub(lambda m: _NEW_TONE[m[0]], (text or "").casefold())
    return " ".join(re.findall(r"\w+", _LIST_LETTER.sub(" ", folded)))


# R1-ii (docs/vilextime-dinh-nghia.md): renames from the 2025 reorganisation, in `_words`
# form. Khoản 1 Điều 3 NQ 190/2025/QH15 already carries an old name over to the agency
# that took the function, from the reorganisation date (ministries: 01/03/2025, the date
# NĐ 25/2025 ... 55/2025/NĐ-CP on the new ministries took effect), so a later amendment
# that only rewrites the name does not change the legal answer. Where a function was
# split, every receiving agency is listed: the rename is recognised only if the new
# text names one of them in its place.
# The more specific name first: `_renamed` replaces in this order.
RENAMES: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("bộ kế hoạch và đầu tư", ("bộ tài chính",)),
    ("bộ giao thông vận tải", ("bộ xây dựng",)),
    ("bộ tài nguyên và môi trường", ("bộ nông nghiệp và môi trường",)),
    ("bộ nông nghiệp và phát triển nông thôn", ("bộ nông nghiệp và môi trường",)),
    ("bộ thông tin và truyền thông", ("bộ khoa học và công nghệ", "bộ văn hóa thể thao và du lịch")),
    ("bộ lao động thương binh và xã hội", ("bộ nội vụ", "bộ y tế", "bộ giáo dục và đào tạo")),
    ("ủy ban dân tộc", ("bộ dân tộc và tôn giáo",)),
    ("sở kế hoạch và đầu tư", ("sở tài chính",)),
    ("sở giao thông vận tải", ("sở xây dựng",)),
    ("sở tài nguyên và môi trường", ("sở nông nghiệp và môi trường",)),
    ("sở nông nghiệp và phát triển nông thôn", ("sở nông nghiệp và môi trường",)),
    ("sở thông tin và truyền thông", ("sở khoa học và công nghệ",)),
    ("sở lao động thương binh và xã hội", ("sở nội vụ", "sở y tế")),
    # NHNN: 63 provincial branches became regional ones from 01/03/2025
    ("ngân hàng nhà nước chi nhánh tỉnh thành phố trực thuộc trung ương",
     ("ngân hàng nhà nước chi nhánh tại các khu vực", "ngân hàng nhà nước chi nhánh khu vực",
      "ngân hàng nhà nước khu vực")),
    ("ngân hàng nhà nước chi nhánh", ("ngân hàng nhà nước khu vực",)),
    ("tổng cục tiêu chuẩn đo lường chất lượng", ("ủy ban tiêu chuẩn đo lường chất lượng quốc gia",
                                                 "ủy ban tiêu chuẩn đo lường chất lượng")),
    ("cục thuế địa phương", ("cơ quan thuế cấp tỉnh", "thuế tỉnh")),
    ("cục đường thủy nội địa việt nam", ("cục hàng hải và đường thủy việt nam",)),
    ("cục hàng hải việt nam", ("cục hàng hải và đường thủy việt nam",)),
    ("tổng cục", ("cục",)),
)
# R1-iii: a citation changed and nothing else. Counts only in a document that says a
# replaced act applies in its place (`auto_update_documents`).
_CITATION = re.compile(r"(?i)(?:số\s*)?\d+[a-zđ]?/\d{4}/[\wĐđ&\-]+"
                       r"|ngày\s+\d{1,2}\s*(?:tháng|/)\s*\d{1,2}\s*(?:năm|/)\s*\d{4}"
                       r"|\b\d{1,2}/\d{1,2}/\d{4}\b")
_AUTO_UPDATE = re.compile(r"(?i)(?:văn bản|quy định)[^.;]{0,160}(?:được|bị) sửa đổi, bổ sung(?:,| hoặc) (?:hoặc )?"
                          r"thay thế[^.;]{0,100}thì[^.;]{0,60}(?:áp dụng|thực hiện|thay đổi) (?:theo|quy định tại)")


def _renamed(a: str, b: str) -> bool:
    """`b` is `a` with old agency names swapped for their successors, and nothing else."""
    out = a
    for old, successors in RENAMES:
        if old in out and old not in b:
            new = next((s for s in successors if s in b), None)
            if new:
                out = out.replace(old, new)
    return (out != a and out == b) or _renamed_somewhere(a, b)


def _renamed_somewhere(a: str, b: str) -> bool:
    """An amendment that renames some occurrences and leaves others ("tổng cục … ủy ban …").

    Every old name, in either text, and every successor in `b` become one tag per pair; a
    successor already in `a` stays as written, so a real swap of two agencies still differs.
    """
    tagged_a, tagged_b, hit = f" {a} ", f" {b} ", False
    for k, (old, successors) in enumerate(RENAMES):
        tag = f" #{k}# "
        hit = hit or f" {old} " in tagged_a
        tagged_a = tagged_a.replace(f" {old} ", tag).replace(f" {old} ", tag)   # twice: adjacent names
        for name in (old, *successors):
            tagged_b = tagged_b.replace(f" {name} ", tag).replace(f" {name} ", tag)
    return hit and a != b and tagged_a.split() == tagged_b.split()


def transition_kind(before: str | None, after: str | None, auto_update: bool = False) -> str:
    """R1: whether one version -> the next changes the legal content.

    `substantive`, or why not: `cosmetic_only` (case, punctuation, spacing, tone
    placement), `rename_only` (2025 reorganisation renames), `auto_reference_update`
    (only a cited act changed, in a document that applies replaced acts itself).
    """
    a, b = _words(before), _words(after)
    if a == b:
        return "cosmetic_only"
    if _renamed(a, b):
        return "rename_only"
    if auto_update and _words(_CITATION.sub(" ", before or "")) == _words(_CITATION.sub(" ", after or "")):
        return "auto_reference_update"
    return "substantive"


def legal_states(versions: list[dict], auto_update: bool = False) -> list[int]:
    """Indices of the versions that open a new legal state: 0, then every substantive transition."""
    return [0] + [i for i in range(1, len(versions))
                  if transition_kind(versions[i - 1]["text"], versions[i]["text"], auto_update) == "substantive"]


def auto_update_documents(db: sqlite3.Connection) -> set[str]:
    """Documents with a clause applying a replaced act's successor (TT 84/2018/TT-BTC k3 Đ7 kind)."""
    return {doc for doc, text in db.execute(
        "SELECT p.document_id, v.text FROM versions v JOIN provisions p ON p.id = v.provision_id "
        "WHERE v.text LIKE '%thay thế%' AND v.text LIKE '%thì%'") if _AUTO_UPDATE.search(text or "")}


def facets_of(versions: list[dict], auto_update: bool = False) -> dict:
    """Difficulty covariates, on every row rather than only where a group needs one.

    `similarity` used to be written for T4 alone, which is the same number that
    decides T4 membership: the cut at NEAR_IDENTICAL is a threshold on a
    continuous variable, so the group boundary is arbitrary while the variable
    is not. Written for every chain it becomes a covariate the analysis can slice
    on, and the 275 released pairs stay one population instead of 150 + 125.

    `substantive_transitions` is the text half of rule R2: a transition whose two
    texts differ only in case, spacing or punctuation ("Trung ương" -> "trung
    ương") cannot carry a question, and 18.4% of T3's transitions are that or an
    agency rename. The full rule is a property of the *question* — whether it
    touches every change — so this is an upper bound and the row is kept, not
    dropped: which definition T3 ships with is still open (report decision 6).
    """
    texts = [v["text"] for v in versions]
    ratios = [round(difflib.SequenceMatcher(None, a, b).ratio(), 4)
              for a, b in zip(texts, texts[1:])]
    kinds = [transition_kind(a, b, auto_update) for a, b in zip(texts, texts[1:])]
    return {
        "n_versions": len(versions),
        # This row's own chance level: the odds of being right by picking a version
        # uniformly at random. 1/2 for a pair, 1/3 for a three-step chain — which is
        # why T2's and T3's raw accuracies were never comparable (the "newest
        # version" probe scores 0.500 on T2 and 0.325 on T3, and the gap is the
        # chance level, not the difficulty). Normalise on this before tabling them.
        "chance_accuracy": round(1 / len(versions), 4) if versions else None,
        # What used to decide T4 membership, kept as the boundary of the reported
        # slice so Bang 1 still has a T4 row to show.
        "near_identical": bool(ratios) and max(ratios) >= NEAR_IDENTICAL,
        # kept under its old name and old meaning for the two-version chains
        # `build_vilextime.py` already reads it from
        "similarity": ratios[0] if len(ratios) == 1 else None,
        "similarities": ratios,
        # R1 of docs/vilextime-dinh-nghia.md: cosmetic, rename-only and auto-reference
        # transitions do not count; `transition_kinds` says which each one was
        "substantive_transitions": kinds.count("substantive"),
        "transition_kinds": kinds,
    }


# An operation that can put a successor norm in place. Co-dated with another
# unit's ending, in the same document, this is the shape the adviser's 05/10
# ruling is about: the clause is gone, the rule it carried may not be.
SUCCESSOR_OPS = ("amend", "supplement", "replace")
# graph_justification.md S3: valid(u, t) needs, beyond u's own text, the version
# chain (I1), the ancestor chain (I2), and the acting documents with their
# transitive closure (I3). These name the weakest tier that holds each.
REPR_TIERS = ("doc_metadata", "clause_version", "ancestor_chain", "cross_document")


def norm_continuity(document_id: str, ended_on: str | None, co_dated: set[tuple[str, str]]) -> str:
    """Whether this unit's rule is known to have simply ended, or may have moved.

    `valid(u, t)` says the clause is out of force. It does not say the *content*
    is, and the adviser ruled on 05/10 that every ViLexTime question is a content
    question: a repealed clause whose rule now lives elsewhere must not ship gold
    "(khong co dap an)". That gold is what annotator B rejected on 45 of the 54
    contested T6 rows, every one of them flagged `group_mismatch`, with notes
    naming the successor ("khoan 4 bi bai bo nhung khoan 5 duoc bo sung").

    The test is a proxy and over-triggers on purpose: an amendment landing in the
    same document on the same day is a *candidate* successor, not a proven one, so
    this returns "unclear" and never "moved". Only a person reading the target
    text may write "moved", in data/review/audit_queue_relocation.tsv,
    and the 18 unchecked rows there are what measures this proxy's precision.
    """
    if not ended_on:
        return "none"
    return "unclear" if (document_id, ended_on[:10]) in co_dated else "none"


def min_repr(row: dict, acted_on: dict[str, str]) -> str:
    """The weakest representation that can decide this row — graph_justification.md S3.

    A row the containing document's own effective dates settle is one B7 (metadata
    filter, no graph) can serve. A row that needs an edge followed is not. That
    gap is exactly what RQ3 asks about ("loi ich den tu do thi, hay chi tu loc
    sieu du lieu"), and H2 is called the decisive test of the representation — so
    the tier belongs on every row as a stratum, not in a group definition.

    It is *derived*, never hand-labelled: S3 proves valid(u, t) is a computation
    over (1)-(3). This is also the repair for the D4 cross-check, where the two
    verdicts humans could not agree on — is this T4, is this T6 — were both
    properties of the pipeline rather than of the text in front of them.

    Two limits, both to be reported. A tier says what is *necessary*, so a system
    holding the whole graph can still answer wrongly and one below the tier can
    still guess right; the claim is about the gap between tiers, not about any
    single tier's score. And it inherits the extraction's own recall, so it has to
    be re-derived by hand on the independent gold subset (W5).
    """
    last_as_of = max(g["as_of"] for g in row["gold"])
    actors = {f"document:{e.split(':')[1]}" for e in row["event_ids"] if ":" in e}
    if row.get("norm_continuity") == "unclear" or any(
            (on := acted_on.get(a)) is not None and on <= last_as_of for a in actors):
        return "cross_document"     # I3: an edge leaving this document decides it
    if row.get("repeal_mode") == "ancestor":
        return "ancestor_chain"     # I2: 14,157 units end with no event of their own
    if row["n_versions"] > 1 or any(not g["in_force"] for g in row["gold"]):
        return "clause_version"     # I1: the document's own dates do not say
    return "doc_metadata"           # B7's reach: the containing document settles it


def add_repr_fields(row: dict, continuity: str, acted_on: dict[str, str]) -> dict:
    """`norm_continuity` then `min_repr`, in that order — the second reads the first."""
    row["norm_continuity"] = continuity
    row["min_repr"] = min_repr(row, acted_on)
    return row


def spread_as_of(provision_id: str, start: date, bound: date) -> date:
    """A deterministic as_of in [start + 1, start + MARGIN], not fixed at start + 1.

    Asking every one-version lineage at exactly start + 1 leaks through the
    *marginal* distribution rather than through any single row: across the release
    it teaches that `as_of - 1` is a version boundary, which a system can then use
    on the groups that do have a choice without reading anything. JUDGE N3 found
    this on T3 and T3 was moved on 29/09; T1 was left behind.

    The spread stays inside MARGIN so the row keeps its `ranh_gioi` meaning — near
    the start of the version — and so it cannot land on the mid-interval twin
    `enrich_vilextime.mid_date` builds for the same lineage, which holds MARGIN
    days off both boundaries. Seeded on the lineage id: a rebuild reproduces it.
    """
    span = min((bound - start).days, MARGIN)
    if span <= 0:
        return start
    offset = int(hashlib.sha1(provision_id.encode()).hexdigest(), 16) % span
    return start + timedelta(days=1 + offset)


def classify(versions: list[dict], document_ends: date | None, level: str, today: date,
             moved: bool = False, states: list[int] | None = None) -> str | None:
    """Which group this provision's chain can serve, or None.

    `moved` is `norm_continuity(...) == "unclear"`: a sibling unit in the same
    document gained or changed a rule on the very day this one ended. Such a chain
    is kept out of T6, whose gold asserts the content is simply gone, and falls
    through to the group its dated versions allow — where it is asked *inside* a
    version's window, so its gold is the version text and stays correct.

    `states` (`legal_states`) are the versions that open a new legal state. T2 and T3
    count states, not versions (R1): a chain whose only other change is a rename is a
    pair, and a chain with no substantive change at all is no group (None). Without
    `states` every transition counts, as before R1.
    """
    dated = [v for v in versions if v["effective_from"]]
    if len(dated) != len(versions) or not dated:
        return None  # an undated version can never be an answer
    # Scarcest group wins, so a chain that could serve two groups goes to the
    # one that cannot spare it: T3 has 2x its quota, T6 has 22x.
    states = states if states is not None else list(range(len(dated)))
    if len(states) >= 3:
        return "T3"
    last = dated[-1]
    if (
        last["effective_to"]
        and last["ended_by_event_id"]
        and level in ("Clause", "Point")
        and (document_ends is None or document_ends > today)
        and not moved
    ):
        return "T6"  # ended while its document still stands, with nothing taking over
    if len(dated) == 1:
        return "T1"
    if len(states) == 2:
        return "T2"  # T4 merged in: `similarity` is a facet, not a group
    return None      # several versions, one legal state: nothing to ask apart (R1)


def ask_dates(group: str, versions: list[dict], today: date,
              provision_id: str = "", document_ends: date | None = None,
              states: list[int] | None = None) -> list[date]:
    """The dates a question is asked at — chosen so the answers differ.

    T2 and T3 are asked around the transitions that open a legal state (`states`),
    so a rename between them is never the switch a pair turns on.
    """
    starts = [_d(v["effective_from"]) for v in versions]
    need = {"T2": 2, "T3": 3}.get(group, 0)
    if need and states is not None and len(states) >= need:
        starts = [starts[i] for i in states]
    if group == "T1":
        # Anywhere in the one version's window, so the answer is the same wherever
        # it lands; the date is spread rather than fixed at start + 1 (see
        # `spread_as_of`). Bounded by the document's own end as well, because a
        # version whose `effective_to` is null inside a document that already
        # ended is exactly the metadata gap JUDGE C1 is about.
        ends = [d for d in (_d(versions[0]["effective_to"]), document_ends) if d]
        bound = min([*ends, min(today, SNAPSHOT) + ONE_DAY]) - ONE_DAY
        return [spread_as_of(provision_id, starts[0], bound)]
    if group == "T6":
        end = _d(versions[-1]["effective_to"])
        return [end - ONE_DAY, end]
    if group == "T3":
        # the day before each switch, then the day of the last one — like T2, so a
        # system that picks the version starting nearest to as_of is caught (JUDGE
        # N3: at start + 1 it solved 200/200 T3 boundary rows; decided 29/09)
        return [s - ONE_DAY for s in starts[1:]] + [starts[-1]]
    return [starts[1] - ONE_DAY, starts[1]]  # T2, T4: either side of the switch


def repealed_by_ancestor(last: dict, level: str, document_ends: date | None, today: date) -> bool:
    """Out of force without an event of its own, inside a document still in force."""
    return (level in ("Clause", "Point") and last["effective_to"] is not None and last["valid_to"] is None
            and last["ended_by_event_id"] is None and _d(last["effective_to"]) <= today
            and (document_ends is None or document_ends > today))


def pending_version(versions: list[dict], at: date, issued_on: dict[str, str]) -> dict | None:
    """A later version already signed at `at` but not yet in force.

    The amending act is on the portal, retrievable and textually authoritative,
    and it is not law yet — so every retrieval signal points at the answer that
    is wrong. `not_yet_in_force` was a schema value with no rows behind it; this
    names the case where it already occurs, which is most of T2's "before" row,
    instead of carving out a seventh group for it.
    """
    for v in versions:
        start, event = _d(v["effective_from"]), v["created_by_event_id"]
        if not start or start <= at or not event:
            continue
        actor = f"document:{event.split(':')[1]}"
        signed = _d(issued_on.get(actor))
        if signed and signed <= at:
            return {"version_id": v["id"], "actor_document_id": actor,
                    "signed_on": signed.isoformat(), "effective_from": v["effective_from"],
                    "days_until_effect": (start - at).days}
    return None


def why_no_answer(versions: list[dict], at: date) -> str:
    """Before the first version opens is not the same gap as after the last one closes."""
    first = _d(versions[0]["effective_from"])
    return "not_yet_in_force" if first and at < first else "provision_repealed"


def after_snapshot(row: dict) -> bool:
    """A date past the corpus snapshot, which nothing in the corpus can answer.

    `check_release.py` rejects these, so shipping them in the pool only defers the
    failure: JUDGE V2 found 6 in the release reaching to 2027-03-01. A transition
    or an expiry dated in the future produces them, which is why the test is on
    the built row rather than on any one group.
    """
    return any(g["as_of"] > SNAPSHOT.isoformat() for g in row["gold"])


def build_row(group: str, provision: dict, versions: list[dict], today: date,
              evidence: dict[str, dict], document_ends: date | None = None,
              issued_on: dict[str, str] | None = None, auto_update: bool = False) -> dict:
    dates = ask_dates(group, versions, today, provision["id"], document_ends,
                      legal_states(versions, auto_update))
    gold = []
    for at in dates:
        hit = in_force_at(versions, at)
        gold.append({
            "as_of": at.isoformat(),
            "in_force": hit is not None,
            "version_id": hit["id"] if hit else None,
            "text": hit["text"] if hit else None,
            "no_answer_reason": None if hit else why_no_answer(versions, at),
            "pending": pending_version(versions, at, issued_on or {}),
        })
    events = [v["created_by_event_id"] for v in versions if v["created_by_event_id"]]
    events += [v["ended_by_event_id"] for v in versions if v["ended_by_event_id"]]
    row = {
        "schema_version": 1,
        "id": f"vilextime:{group}:{provision['id']}",
        "group": group,
        "document_id": provision["document_id"],
        "provision_id": provision["id"],
        "level": provision["level"],
        "title": provision["title"],
        # T6 asks about the ending, so its transition is when the last version
        # stopped; every other group's is when the last one opened.
        "transition_on": (versions[-1]["effective_to"] if group == "T6"
                          else versions[-1]["effective_from"] if len(versions) > 1 else None),
        "gold": gold,
        "versions": [
            {k: v[k] for k in VERSION_FIELDS}
            for v in versions
        ],
        "event_ids": sorted(set(events)),
        "evidence": [evidence[e]["evidence"] for e in sorted(set(events)) if e in evidence],
        "actor_numbers": sorted({evidence[e]["actor_number"] for e in set(events) if e in evidence}),
    }
    if group == "T6":
        row["repeal_mode"] = "direct"
    row.update(facets_of(versions, auto_update))
    return row


# A document whose effect starts before its signing. Two kinds look the same in
# the numbers and the adviser excluded both (20/09): corrections, and guidance
# that takes effect together with the act it details. The second is measured,
# not guessed from wording: the act its title cites by number takes effect on
# the same day. They are named for the audit rather than silently dropped.
_CITED_NUMBER = re.compile(r"\b(\d+/\d{4}/[A-ZĐ][A-ZĐa-z0-9\-]*)")
# Read before parsing, so the ancestor pass json.loads only the lines it wants.
_PROVISION_ID = re.compile(r'"provision_id"\s*:\s*"([^"]+)"')


def retro_kind(number: str, title: str, effective: str, effective_by_number: dict[str, str]) -> str:
    low = (title or "").lower()
    if "đính chính" in low:
        return "correction"
    # The portal's titles open with the document's own number; that one is not a citation.
    cited = {n for n in _CITED_NUMBER.findall(title or "") if n.replace(" ", "") != (number or "").replace(" ", "")}
    if any(effective_by_number.get(n) == effective for n in cited):
        return "guidance_in_sync"
    return "stated_retroactive"


def build_t5_row(provision: dict, versions: list[dict], evidence: dict[str, dict],
                 actors: dict[str, tuple], issued_on: dict[str, str] | None = None,
                 auto_update: bool = False) -> dict | None:
    """Either side of the first change made by a retroactive document.

    `actors` maps a retroactive document to (number, title, issued_on,
    effective_from). The later date is the day the change took effect — in
    the retroactive window, before anyone could read it — which is the case a
    point-in-time system gets wrong.
    """
    for i, v in enumerate(versions[1:], 1):
        event = v["created_by_event_id"]
        actor = f"document:{event.split(':')[1]}" if event else None
        if actor not in actors:
            continue
        if transition_kind(versions[i - 1]["text"], v["text"], auto_update) != "substantive":
            continue    # R1: a retroactive rename or reformatting changes no answer
        number, title, issued, effective, kind = actors[actor]
        start = _d(v["effective_from"])
        dates = [start - ONE_DAY, start]
        gold = []
        for at in dates:
            hit = in_force_at(versions, at)
            gold.append({"as_of": at.isoformat(), "in_force": hit is not None,
                         "version_id": hit["id"] if hit else None, "text": hit["text"] if hit else None,
                         "no_answer_reason": None if hit else why_no_answer(versions, at),
                         "pending": pending_version(versions, at, issued_on or {})})
        if len({(g["in_force"], g["text"]) for g in gold}) != 2:
            return None
        events = sorted({x for w in versions for x in (w["created_by_event_id"], w["ended_by_event_id"]) if x})
        row = {
            "schema_version": 1,
            "id": f"vilextime:T5:{provision['id']}",
            "group": "T5",
            "document_id": provision["document_id"],
            "provision_id": provision["id"],
            "level": provision["level"],
            "title": provision["title"],
            "transition_on": v["effective_from"],
            "gold": gold,
            "versions": [{k: w[k] for k in VERSION_FIELDS} for w in versions],
            "event_ids": events,
            "evidence": [evidence[e]["evidence"] for e in events if e in evidence],
            "actor_numbers": sorted({evidence[e]["actor_number"] for e in events if e in evidence}),
            "retroactive": {
                "actor_document_id": actor, "actor_law_id": number,
                "effective_from": effective, "issued_on": issued,
                "window_days": (_d(issued) - _d(effective)).days,
                "kind": kind, "event_id": event,
            },
        }
        row.update(facets_of(versions, auto_update))
        return row
    return None


def stable_sample(rows: list[dict], cap: int, ranked: set[str]) -> list[dict]:
    """`cap` rows: every row whose lineage is already ranked in this group, then a seeded sample of the rest.

    A seeded sample of a list that gained or lost a row picks different rows, so
    a rebuild that moves a few provisions between groups would drop lineages the
    release already holds (data/vilextime/sample.jsonl is walked in rank order)
    out of the pool (plan phase-4, J3). `ranked` must be this group's lineages
    only: a T6 "ancestor" lineage is also a T1 candidate, and kept in T1 it would
    be taken before T6 could have it.
    """
    kept = [r for r in rows if r["provision_id"] in ranked]
    rest = [r for r in rows if r["provision_id"] not in ranked]
    picked = random.Random(SEED).sample(rest, max(0, min(cap - len(kept), len(rest))))
    return sorted(kept + picked, key=lambda r: r["id"])


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--data", type=Path, default=Path("data"))
    parser.add_argument("--per-group-cap", type=int, default=10,
                        help="keep this many times each group's quota (default 10)")
    parser.add_argument("--ancestor-quota", type=int, default=ANCESTOR_QUOTA,
                        help=f"T6 'ancestor' (H3) release target, also scaled by --per-group-cap "
                             f"(default {ANCESTOR_QUOTA}; 10,055 provisions qualify)")
    parser.add_argument("--today", type=date.fromisoformat, default=date(2026, 9, 20))
    args = parser.parse_args()
    data = args.data
    ranking = data / "vilextime/sample.jsonl"
    ranked: dict[str, set[str]] = collections.defaultdict(set)     # group -> its ranked lineages
    for line in ranking.open(encoding="utf-8") if ranking.exists() else ():
        entry = json.loads(line)
        # A ranking line written before T4 was merged says "T4", and `stable_sample`
        # looks the group up by name — so without this the former T4 lineages lose
        # the protection that keeps a rebuild from dropping lineages the release
        # already holds. 71 of them, each with a question already paid for, fell out
        # of the pool on the 07/10 rebuild that way.
        ranked["T2" if entry["group"] == "T4" else entry["group"]].add(entry["lineage_id"])

    eligible = {
        f"document:{row['doc_id']}"
        for row in map(json.loads, (data / "derived/eligibility.jsonl").read_text(encoding="utf-8").splitlines())
        if row["benchmark_eligible"]
    }
    db = sqlite3.connect(data / "temporal.sqlite")
    provisions = {
        pid: {"id": pid, "document_id": doc, "level": lvl, "title": title}
        for pid, doc, lvl, title in db.execute("SELECT id, document_id, level, title FROM provisions")
    }
    document_ends = {doc: _d(end) for doc, end in db.execute("SELECT id, effective_to FROM documents")}
    # When each document was signed, so a version that is on the portal but not
    # yet law at `as_of` can be named (`pending_version`).
    issued_on = {doc: issued for doc, issued in db.execute("SELECT id, issued_on FROM documents") if issued}
    effective_by_number = {n: e for n, e in db.execute("SELECT number, effective_from FROM documents") if n}
    retro_actors = {
        doc: (number, title, issued, effective, retro_kind(number, title, effective, effective_by_number))
        for doc, number, title, issued, effective in db.execute(
            "SELECT id, number, title, issued_on, effective_from FROM documents "
            "WHERE issued_on IS NOT NULL AND effective_from IS NOT NULL AND effective_from < issued_on")
    }
    auto_docs = auto_update_documents(db)    # R1-iii
    t5_rows: list[dict] = []
    ancestor_rows: list[dict] = []
    evidence = {}
    # (document, date) pairs where something was amended, supplemented or replaced:
    # a unit ending on that same day in that same document may have handed its rule
    # over rather than lost it (`norm_continuity`). And, per document, the earliest
    # day it was itself acted on — an acting document that has since been amended is
    # I3, the transitive case, so a row depending on it cannot be settled inside one
    # document (`min_repr`).
    co_dated: set[tuple[str, str]] = set()
    acted_on: dict[str, str] = {}
    for line in (data / "derived/provision_events.jsonl").read_text(encoding="utf-8").splitlines():
        e = json.loads(line)
        evidence[e["id"]] = {"evidence": e["evidence"], "actor_number": e["actor_number"]}
        target, on = e.get("target_document_id"), e.get("effective_on")
        if not target or not on:
            continue
        on = on[:10]
        if e.get("operation") in SUCCESSOR_OPS:
            co_dated.add((target, on))
        if on < acted_on.get(target, "9999-99-99"):
            acted_on[target] = on

    # One streaming pass: every version of a provision is adjacent in the file.
    buckets: dict[str, list[dict]] = collections.defaultdict(list)
    counts: collections.Counter[str] = collections.Counter()
    current: list[dict] = []

    def flush(rows: list[dict]) -> None:
        if not rows:
            return
        provision = provisions.get(rows[0]["provision_id"])
        if provision is None or provision["document_id"] not in eligible:
            return
        rows.sort(key=lambda v: v["ordinal"])
        ends = document_ends.get(provision["document_id"])
        continuity = norm_continuity(provision["document_id"], rows[-1]["effective_to"], co_dated)
        moved = continuity == "unclear"
        auto = provision["document_id"] in auto_docs
        states = legal_states(rows, auto) if all(v["effective_from"] for v in rows) else None
        if (t5 := build_t5_row(provision, rows, evidence, retro_actors, issued_on, auto)) is not None:
            t5_rows.append(add_repr_fields(t5, continuity, acted_on))
        is_ancestor = all(v["effective_from"] for v in rows) and repealed_by_ancestor(
            rows[-1], provision["level"], ends, args.today)
        if is_ancestor:
            row = build_row("T6", provision, rows, args.today, evidence, ends, issued_on, auto)
            row.update(id=f"vilextime:T6:{provision['id']}", repeal_mode="ancestor")
            add_repr_fields(row, continuity, acted_on)
            if after_snapshot(row):
                counts["bỏ T6/anc: hỏi sau ngày chụp corpus"] += 1
            elif moved:
                # Same reason as direct T6: the H3 gold also asserts the content is
                # gone. Nothing is lost — the cascade below still places this chain,
                # asked inside a version's window, where its gold is the text.
                counts["bỏ T6/anc: nghi chuyển chỗ quy phạm, chờ người kiểm"] += 1
            else:
                ancestor_rows.append(row)
        group = classify(rows, ends, provision["level"], args.today, moved, states)
        if moved and group != "T6":
            counts["T6 -> nhóm khác: nghi chuyển chỗ quy phạm, chờ người kiểm"] += 1
        if group is None:
            if states is None:
                counts["bỏ: phiên bản không có ngày"] += 1
            else:
                kinds = {transition_kind(a["text"], b["text"], auto) for a, b in zip(rows, rows[1:])}
                counts[f"bỏ (R1): chỉ {'+'.join(sorted(kinds - {'substantive'}))}"] += 1
            return
        if is_ancestor:
            # Which group classify() would otherwise hand an H3 lineage to. The
            # ancestor part is written first now, so this is a monitor, not a loss:
            # if it ever stops being T1-dominated the allocation needs revisiting.
            counts[f"ancestor cũng là ứng viên {group}"] += 1
        # A chain classify() sends to T3 that also satisfies the direct-T6 test
        # would be a confound: T6 would hold only short chains. Measured 05/10 on
        # the whole store it is 0, which is why the cascade is left as it is.
        last = rows[-1]
        if (group == "T3" and last["effective_to"] and last["ended_by_event_id"]
                and provision["level"] in ("Clause", "Point") and (ends is None or ends > args.today)):
            counts["CẢNH BÁO: T3 ăn mất một ứng viên T6-direct"] += 1
        row = add_repr_fields(build_row(group, provision, rows, args.today, evidence, ends, issued_on, auto),
                              continuity, acted_on)
        answers = [(g["in_force"], g["text"]) for g in row["gold"]]
        if len(answers) > 1 and len(set(answers)) != len(answers):
            counts[f"bỏ {group}: đáp án trùng nhau ở các mốc"] += 1
            return
        if after_snapshot(row):
            counts[f"bỏ {group}: hỏi sau ngày chụp corpus"] += 1
            return
        counts[group] += 1
        buckets[group].append(row)

    for line in (data / "derived/versions.jsonl").open(encoding="utf-8"):   # ~1 GB: stream it
        v = json.loads(line)
        if current and v["provision_id"] != current[0]["provision_id"]:
            flush(current)
            current = []
        current.append(v)
    flush(current)

    # T6 "ancestor": a seeded sample with the repeal it inherits named. It is
    # written *before* the other groups now (see the write loop): 9,929 of the
    # 10,055 qualifying provisions are also T1 candidates, and T1 is where
    # classify() puts them, so leaving ancestor last made its yield a function of
    # whichever T1 rows happened to be sampled rather than of the quota.
    ancestor_cap = args.ancestor_quota * args.per_group_cap
    counts["T6 ancestor (đủ điều kiện)"] = len(ancestor_rows)
    ancestor_rows = stable_sample(sorted(ancestor_rows, key=lambda r: r["id"]), ancestor_cap, ranked["T6"])
    parent_of = {pid: parent for pid, parent in db.execute("SELECT id, parent_id FROM provisions")}
    chains = {r["provision_id"]: [] for r in ancestor_rows}
    for pid in list(chains):
        up = parent_of.get(pid)
        while up:
            chains[pid].append(up)
            up = parent_of.get(up)
    wanted = {a for chain in chains.values() for a in chain}
    last_of: dict[str, dict] = {}
    for line in (data / "derived/versions.jsonl").open(encoding="utf-8"):
        found = _PROVISION_ID.search(line)
        if found and found.group(1) in wanted:
            v = json.loads(line)
            keep = last_of.get(v["provision_id"])
            if keep is None or v["ordinal"] > keep["ordinal"]:
                # Only the three fields the repeal lookup below reads. Holding the
                # whole version meant holding every ancestor's text, which was
                # affordable at 300 H3 candidates and is not at thousands.
                last_of[v["provision_id"]] = {
                    "ordinal": v["ordinal"], "effective_to": v["effective_to"],
                    "ended_by_event_id": v["ended_by_event_id"]}
    for row in ancestor_rows:
        end = row["versions"][-1]["effective_to"]
        hit = next((a for a in chains[row["provision_id"]] if (v := last_of.get(a))
                    and v["ended_by_event_id"] and v["effective_to"] == end), None)
        row["repealed_by"] = ({"ancestor_id": hit, "event_id": last_of[hit]["ended_by_event_id"]} if hit else None)
    counts["T6 ancestor (đã lấy mẫu)"] = len(ancestor_rows)

    out_path = data / "derived/vilextime_pool.jsonl"
    written: collections.Counter[str] = collections.Counter()
    documents: set[str] = set()
    taken = {r["provision_id"] for r in t5_rows}   # provisions already written for another group
    facet_stats: collections.Counter[str] = collections.Counter()
    t3_substantive: collections.Counter[int] = collections.Counter()
    tiers: collections.Counter[str] = collections.Counter()
    with out_path.open("w", encoding="utf-8") as out:
        def emit(row: dict) -> None:
            out.write(json.dumps(row, ensure_ascii=False) + "\n")
            documents.add(row["document_id"])
            taken.add(row["provision_id"])
            facet_stats["dòng"] += len(row["gold"])
            facet_stats["dòng có phiên bản đã ký chưa hiệu lực"] += sum(
                1 for g in row["gold"] if g["pending"])
            facet_stats["dòng không đáp án: chưa có hiệu lực"] += sum(
                1 for g in row["gold"] if g["no_answer_reason"] == "not_yet_in_force")
            if row["group"] == "T3":
                t3_substantive[row["substantive_transitions"]] += 1
            tiers[row["min_repr"]] += 1
            if row["group"] == "T2" and row["near_identical"]:
                facet_stats["lineage lát cắt T4 (độ giống >= 0,90)"] += 1

        for row in sorted(t5_rows, key=lambda r: r["id"]):
            emit(row)
        written["T5"] = counts["T5"] = len(t5_rows)
        # Scarcest first, and T6 "ancestor" is the scarcest of all once the
        # collision with T1 is counted: it goes before the cascade's groups so a
        # provision that can only serve H3 is never spent on T1.
        ancestor_rows = [r for r in ancestor_rows if r["provision_id"] not in taken and r["repealed_by"]]
        for row in ancestor_rows:
            emit(row)
        written["T6 ancestor"] = len(ancestor_rows)
        for group in PRIORITY:
            rows = sorted(buckets[group], key=lambda r: r["id"])
            cap = QUOTA[group] * args.per_group_cap
            if len(rows) > cap:
                rows = stable_sample(rows, cap, ranked[group])
            rows = [r for r in rows if r["provision_id"] not in taken]   # T5 and H3 are scarcer
            for row in rows:
                emit(row)
            written[group] = len(rows)

    print(f"{sum(written.values()):,} ứng viên -> {out_path}\n")
    print(f"  {'nhóm':<5} {'quota':>6} {'có':>9} {'giữ':>8}   dư")
    for group in ("T1", "T2", "T3", "T5", "T6"):
        have = counts[group]
        margin = have / QUOTA[group]
        print(f"  {group:<5} {QUOTA[group]:>6,} {have:>9,} {written[group]:>8,}   {margin:>5.1f}x")
    kinds = collections.Counter(r["retroactive"]["kind"] for r in t5_rows)
    have_anc = counts["T6 ancestor (đủ điều kiện)"]
    print(f"  {'T6/anc':<5} {args.ancestor_quota:>6,} {have_anc:>9,} {written['T6 ancestor']:>8,}"
          f"   {have_anc / max(1, args.ancestor_quota):>5.1f}x  (H3: mất hiệu lực do nút cha bị bãi bỏ)")
    print(f"\n  T5 là ứng viên, chờ cố vấn luật theo Điều 152: {dict(kinds)}")
    for key, value in counts.items():
        if key.startswith(("bỏ", "CẢNH BÁO", "ancestor cũng", "T6 ->")):
            print(f"  {value:,} {key}")
    print(f"\n  văn bản khác nhau trong pool đã ghi: {len(documents):,}")
    print("\n  Trường độ khó (mọi nhóm):")
    for key, value in facet_stats.most_common():
        print(f"    {value:>9,}  {key}")
    # Rule R2's text half: a T3 chain needs two transitions that are not merely
    # cosmetic. The split here is the number report decision 6 has to choose on.
    if t3_substantive:
        total = sum(t3_substantive.values())
        ok = sum(n for k, n in t3_substantive.items() if k >= 2)
        print(f"    T3 theo số lần sửa thực chất: {dict(sorted(t3_substantive.items()))}"
              f" -> {ok:,}/{total:,} chuỗi đạt R2 (>=2)")
    # The stratum RQ3 is answered on: B7 reaches `doc_metadata`, and every tier
    # above it names an edge a metadata filter cannot follow.
    print("\n  Biểu diễn yếu nhất đủ để quyết (min_repr, graph_justification §3):")
    shipped = max(1, sum(tiers.values()))
    for tier in REPR_TIERS:
        print(f"    {tiers[tier]:>9,}  {tier:<16} {tiers[tier] / shipped:>5.1%}")


if __name__ == "__main__":
    main()

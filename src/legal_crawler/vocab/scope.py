"""Which documents a point-in-time answer may rest on (ADR 0002, backfill T2).

Only central legal normative documents (QPPL) are retrieved at a date t or
used for ViLexTime. Everything else stays on disk and stays in the genealogy
graph — a Công văn can still be the document that repealed something — it is
just never evidence.

The portal's own `docType.parentCode` is the classification, with two
corrections measured on 2026-09-15:

* `organization.orgType` is not trusted for "local": 26 documents issued by
  Chính phủ, Thủ tướng or Quốc hội carry the local value. The issuing agency's
  name (or, when absent, the document number) decides instead; every one of
  the 1,248 UBND/HĐND documents is caught by it.
* Four historical normative types carry no `VBQPPL` code at all (Hiến pháp,
  Sắc lệnh, Sắc luật, Thông tư liên bộ) and are counted as QPPL.

"Quyết định" is not split further: the portal files individual decisions and
normative ones under the same code, and nothing in the metadata separates them.
"""
from __future__ import annotations

import re

QPPL = "qppl"
LOCAL = "local"
CONSOLIDATED = "consolidated"
TRANSLATION = "translation"
NON_NORMATIVE = "non_normative"

_HISTORICAL_QPPL_TYPES = frozenset({"Hiến pháp", "Sắc lệnh", "Sắc luật", "Thông tư liên bộ"})
_LOCAL_AGENCY = re.compile(r"^(UBND|HĐND|Ủy ban nhân dân|Uỷ ban nhân dân|Hội đồng nhân dân)", re.IGNORECASE)
_LOCAL_NUMBER = re.compile(r"(HĐND|UBND|QĐ-UB\b)")


def document_class(document: dict) -> str:
    """One of QPPL, LOCAL, CONSOLIDATED, TRANSLATION, NON_NORMATIVE."""
    doc_type = document.get("docType") or {}
    name = doc_type.get("name") or ""
    if document.get("isTranslationDoc") or name == "Bản dịch văn bản":
        return TRANSLATION
    if doc_type.get("parentCode") == "VBHN" or document.get("isConsolidatedDocument"):
        return CONSOLIDATED
    if doc_type.get("parentCode") != "VBQPPL" and name not in _HISTORICAL_QPPL_TYPES:
        return NON_NORMATIVE
    agencies = [document.get("agencyName") or ""] + [
        issue.get("agencyName") or "" for issue in document.get("documentIssues") or []
    ]
    if any(_LOCAL_AGENCY.match(agency) for agency in agencies):
        return LOCAL
    if not any(agencies) and _LOCAL_NUMBER.search(document.get("docNum") or ""):
        return LOCAL
    return QPPL

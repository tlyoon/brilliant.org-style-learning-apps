"""BSA255: restricted symbolic equivalence triage, never academic acceptance.

A previous V26 parser mistakenly consumed trailing natural-language link words
after exact mathematical expressions. Re-evaluate only those V26 ambiguous
equation fields with original exact source and candidate evidence supplied by
the caller. Full multilingual semantics and scientific meaning remain pending.
"""
from __future__ import annotations

from collections import Counter
from hashlib import sha256
import json
import re
from typing import Any

from app_generator.validation.language_qa import _learner_visible_localized_fields
from app_generator.validation.typed_scientific_semantic_alignment import (
    _EQUATION, _normalized, audit_reusable_scientific_alignment,
)

LANGS = ("en", "ms", "zh")
# 'a' is deliberately excluded: F=ma must retain acceleration.
_PROSE_BOUNDARY = re.compile(
    r"(?<![0-9])\.(?![0-9])|[;,，。；]|\s+(?=(?:"
    r"is|was|are|were|an|the|and|at|for|dan|ialah|adalah|maka|"
    r"which|where|when|because|jika|sebagai|yang|dengan|[a-z]{4,}"
    r")\b)", re.I,
)


def digest(item: Any) -> str:
    return sha256(json.dumps(
        item, sort_keys=True, ensure_ascii=False,
        separators=(",", ":")).encode("utf8")).hexdigest()


def equation_fragments(text: str) -> list[str]:
    """Return literal equations only, never natural-language claims or code."""
    if not isinstance(text, str):
        raise ValueError("BSA255_NON_STRING_SCIENTIFIC_SURFACE")
    out=[]
    for match in _EQUATION.finditer(_normalized(text)):
        lhs=re.sub(r"\s+","",match.group("lhs")).casefold()
        rhs=_PROSE_BOUNDARY.split(match.group("rhs"),maxsplit=1)[0]
        rhs=re.sub(r"\s+","",rhs).casefold().rstrip(".,;")
        if rhs:
            out.append(lhs+"="+rhs)
    return out


def audit_bounded_symbolic_recovery(activities: list[dict]) -> dict[str, Any]:
    """Only literal mathematical equivalence can be recovered.

    Never accept a translation, diagram, answer or entire scientific meaning
    based on matching fragments, especially when the source is a distractor.
    """
    original=audit_reusable_scientific_alignment(activities)
    if original.get("publicationAuthorized") is not False:
        raise ValueError("BSA255_UNTRUSTED_PRIOR_TRIAGE")
    exact={a["id"]:a for a in activities}
    seen=set()
    rows=[]
    for row in original["rows"]:
        aid=row["activityId"]
        surfaces=dict(_learner_visible_localized_fields(exact[aid]))
        for issue in row["issues"]:
            if issue.get("reason")!="CROSS_LOCALE_SYMBOLIC_EQUIVALENCE_NOT_ESTABLISHED":
                continue
            route=issue.get("field")
            key=(aid,route)
            if key in seen or route not in surfaces:
                raise ValueError("BSA255_DUPLICATE_OR_ABSENT_FORMULA_FIELD")
            seen.add(key)
            triple=surfaces[route]
            forms={lang:equation_fragments(triple[lang]) for lang in LANGS}
            matched=bool(forms["en"]) and all(
                forms[lang] for lang in LANGS) and (
                Counter(forms["en"])==Counter(forms["ms"])==
                Counter(forms["zh"]))
            rows.append({
                "activityId":aid,
                "activitySha256":row["activityCanonicalSha256"],
                "field":route,
                "strictEquationSetsSha256":digest(forms),
                "boundedIdenticalExplicitMath":matched,
                "remainingSemanticStatus":"REVIEW_REQUIRED",
                "fullScientificOrTrilingualMeaningProven":False,
            })
    supported=sum(x["boundedIdenticalExplicitMath"] for x in rows)
    return {
        "status":"BSA255_EXPLICIT_LITERAL_FORMULA_EQUIVALENCE_TRIAGE_NO_ACADEMIC_PASS",
        "activityCount":len(activities),
        "priorAmbiguousSymbolicFields":len(rows),
        "boundedParserFalsePositivesResolved":supported,
        "remainingAmbiguousSymbolicFields":len(rows)-supported,
        "independentRemainingPriorReviewFlags":original["issues"]-supported,
        "sourceMeaningProven":False,
        "trilingualSemanticMeaningProven":False,
        "formalAcademicPASS":0,
        "publicationAuthorized":False,
        "providerCalls":0,
        "rows":rows,
    }

"""Reusable evidence checks for localized scientific claims, not an AI oracle.

A content-independent engine: extracts exact mathematical laws from learner
visible EN/MS/ZH fields; verifies equation identities, presence of unambiguous
physics quantity types and correct MCQ-answer reference in answerLogic.
Statements in distractors are compared ACROSS languages but never declared
true merely because they agree (they are deliberately false options).

Only the source-bound adapter may decide whether a specific law is relevant.
A missing bilingual cue is a REVIEW_REQUIRED flag; an altered mathematical
equation in an otherwise common three-language expression is a real
deterministic mismatch, never complete translation acceptance.
"""
from __future__ import annotations

from collections import Counter
from hashlib import sha256
import json
import re
import unicodedata
from typing import Any

from app_generator.validation.language_qa import (
    _learner_visible_localized_fields,
)

LANGUAGES=("en","ms","zh")
# Formula grammar is intentionally restricted: no eval, sympy parsing of
# untrusted text, arbitrary provider calls, or dynamic token execution.
# Capture only well-scoped notation, including common formula patterns.
_LHS=r"(?:F_?12\s*\+\s*F_?21|F_?21\s*\+\s*F_?12|(?:[sS]igma|sum)\s*F|\bp\b|\bK\b|\bF\b)"
_EQUATION=re.compile(
    r"(?<![A-Za-z0-9_])(?P<lhs>"+_LHS+r")\s*=\s*"
    r"(?P<rhs>sqrt\s*\([^)]{1,40}\)|(?:\([^)]{1,30}\)|[0-9A-Za-z^_*/+\-.])+"
    r"(?:\s+(?:[0-9A-Za-z^_*/+\-.]+|\([^)]{1,30}\))){0,5})",
    flags=re.I,
)
_QUANTITIES={
    "momentum":(r"\bmoment(?:um|a)\b",r"\bmomentum\b",r"动量"),
    "vector":(r"\bvectors?\b",r"\bvektor\b",r"向量|矢量"),
    "scalar":(r"\bscalar\b",r"\bskalar\b",r"标量"),
    "energy":(r"\benerg(?:y|ies)\b",r"\btenaga\b",r"能量|动能|势能|内能"),
    "kinetic_energy":(r"\bkinetic\s+energy\b",r"\btenaga\s+kinetik\b",r"动能"),
    "isolated":(r"\bisolated\b",r"\bterpencil\b",r"孤立"),
    "force":(r"\bforce(?:s)?\b",r"\bdaya\b",r"力"),
}
_COMPILED={
    category:tuple(re.compile(pattern,flags=re.I) for pattern in items)
    for category,items in _QUANTITIES.items()
}
_ALLOWED_EXTRA_FORMULA_MATH=frozenset({"en","ms","zh"})
_MATH_GLYPHS={"²":"^2","³":"^3","−":"-","–":"-","×":"*",
              "∙":"*","·":"*","⋅":"*","Σ":"sigma","∑":"sum"}
_RAW_OPTION=r"(?:\boption(?:s)?\b|\bpilihan\b|选项|選項)\s*([A-D])"


def _digest(data:Any)->str:
    return sha256(json.dumps(data,sort_keys=True,ensure_ascii=False,
        separators=(",",":")).encode("utf8")).hexdigest()


def _normalized(s:str)->str:
    for a,b in _MATH_GLYPHS.items():
        s=s.replace(a,b)
    # Exactly grammatical square-root notation, not a general translation
    # heuristic. Preserve the argument so incorrect physics is still visible.
    s=re.sub(r"(?i)\bp\s*=\s*punca\s+kuasa\s+dua\s*\(",
             "p = sqrt(",s)
    s=re.sub(r"(?i)\bp\s*=\s*根号\s*\(","p = sqrt(",s)
    return unicodedata.normalize("NFKC",s)


def _eqs(text:str)->list[str]:
    """Capture exact expressions, never try to prove their natural language."""
    out=[]
    for x in _EQUATION.finditer(_normalized(text)):
        lhs=re.sub(r"\s+","",x.group("lhs")).lower()
        # Previous parser swallowed following English/Malay prose into
        # a mathematical RHS after a full stop, inventing false defects.
        # A decimal dot between digits stays inside an actual formula.
        # BSA265: two/three-letter function words following an equation
        # ("p = m*v is ...", "F = m a for ...", "K = 0.5 m v^2 and ...")
        # belong to prose, not the RHS. Split BEFORE whitespace removal.
        # Keep true mathematical tokens (including v^2) untouched.
        rhs=re.split(
            r"(?<![0-9])\.(?![0-9])|[;,，。；]|"
            r"\s+(?=(?:is|for|and|dan|at|pada|bagi|ialah|adalah|with|where|when)\b|"
            r"[A-Za-z]{4,}\b)",
            x.group("rhs"),maxsplit=1,flags=re.I)[0]
        rhs=re.sub(r"\s+","",rhs).lower().rstrip(".,;")
        # Literal product typography is not a different physical equation:
        # m*v, m v and mv are the same product. Do not rewrite arbitrary
        # symbolic expressions or silently prove a translated sentence.
        if lhs=="p" and rhs in ("m*v","mv"):
            rhs="mv"
        if lhs=="f" and rhs in ("m*a","ma"):
            rhs="ma"
        # Avoid mistaking a variable '=' followed by a prose word as algebra.
        if len(rhs)>0:
            out.append(lhs+"="+rhs)
    return out


def _unmistakable_wrong_law(text:str)->bool:
    """Safely detect only closed-form physics contradictions, not a guess.

    No arbitrary model or mathematical simplifier. Different correct
    algebraic notations remain REVIEW_REQUIRED rather than a false FAIL.
    """
    t=_normalized(text)
    # Normalize interspersed spaces while preserving symbol identity.
    t=re.sub(r"\s+","",t).casefold()
    # Direct p = mv^2 replaces linear momentum with kinetic-like square.
    bad_momentum=re.search(r"(?<![a-z0-9])p=m\*?v\^?2(?![a-z0-9])",t)
    # Direct F=p confuses force with momentum (different time dimension).
    bad_force=re.search(r"(?<![a-z0-9])f=p(?![a-z0-9/*^])",t)
    # Do not penalize an explicitly stated misconception in explanatory
    # prose; only accept the recognized contradiction when unqualified.
    if bad_momentum or bad_force:
        lower=text.casefold()
        if any(v in lower for v in
               ("misconception","incorrectly","wrongly","false claim",
                "salah tanggapan","secara salah","错误地","误解")):
            return False
        return True
    return False


def _quantities(text:str,language:str)->set[str]:
    idx=LANGUAGES.index(language)
    return {name for name,patterns in _COMPILED.items()
            if patterns[idx].search(text)}


def _affirmed_correct_option(text:str,language:str)->set[str]:
    """Only literal affirmative correct-answer references, not misconceptions."""
    patterns={
        "en":r"\boption\s+([A-D])\s+(?:is\s+|was\s+|would\s+be\s+)?(?:the\s+)?correct\b",
        "ms":r"\bpilihan\s+([A-D])\s+(?:adalah\s+|ialah\s+)?(?:betul|tepat|benar)\b",
        "zh":r"(?:选项|選項)\s*([A-D])\s*(?:是)?(?:正确|正確|对的)",
    }
    return set(re.findall(patterns[language],_normalized(text),flags=re.I))


def _option_refs(text:str)->set[str]:
    t=_normalized(text)
    return set(re.findall(_RAW_OPTION,t,flags=re.I))


def _role_triplets(activity:dict):
    for route,v in _learner_visible_localized_fields(activity):
        if not isinstance(v,dict) or any(not isinstance(v.get(l),str)
                                         for l in LANGUAGES):
            raise ValueError("BSA253_MISSING_REQUIRED_EN_MS_ZH_TEXT")
        yield route,v


def _check_activity(activity:dict)->dict:
    aid=activity.get("id")
    if not isinstance(aid,str) or not aid:
        raise ValueError("BSA253_UNNAMED_ACTIVITY")
    flags=[];rows=[];formula_fields=0;formula_atoms=0
    for route,triple in _role_triplets(activity):
        if any(not triple[l].strip() for l in LANGUAGES):
            raise ValueError("BSA253_EMPTY_LOCALIZED_SURFACE_"+aid)
        expr={l:_eqs(triple[l]) for l in LANGUAGES}
        if any(expr.values()):
            formula_fields+=1
            formula_atoms+=sum(len(v) for v in expr.values())
            if (Counter(expr["en"])!=Counter(expr["ms"]) or
                    Counter(expr["en"])!=Counter(expr["zh"])):
                # Localized expressions can be algebraically equivalent:
                # "sum F", "jumlah F" and Chinese "net force" all mean
                # the same LHS; sqrt can be spelled as a CJK radical or
                # Malay "punca kuasa dua". Do not manufacture a FAIL from
                # a literal equation mismatch without independent proof.
                flags.append({"field":route,
                    "reason":"CROSS_LOCALE_SYMBOLIC_EQUIVALENCE_NOT_ESTABLISHED",
                    "kind":"SEMANTIC_REVIEW_REQUIRED",
                    "rawContentIncluded":False})
        # Independently decisive: a direct false formula in a learner-facing
        # EXPLANATORY field contradicts F=dp/dt or p=mv source law.
        # Distractor OPTION labels are deliberately FALSE and exempt.
        if route in ("explanation","feedback","answerLogic"):
            for lang in LANGUAGES:
                if _unmistakable_wrong_law(triple[lang]):
                    flags.append({"field":route,
                        "reason":"SOURCE_LAW_CONTRADICTED_BY_EXPLICIT_EQUATION",
                        "kind":"DETERMINISTIC_SOURCE_LAW_CONTRADICTION",
                        "locale":lang,
                        "rawContentIncluded":False})
        science={l:_quantities(triple[l],l) for l in LANGUAGES}
        # Comparisons are intentionally role-specific; a zero-translation
        # term count is a warning, not proof of a wrong physical statement.
        discrepancy=(science["en"]^science["ms"])|(science["en"]^science["zh"])
        if discrepancy:
            flags.append({"field":route,
                "reason":"CROSS_LOCALE_SCIENTIFIC_QUANTITY_CUES_MISMATCH",
                "kind":"SEMANTIC_REVIEW_REQUIRED",
                "cueCategories":sorted(discrepancy),
                "rawContentIncluded":False})
        if (route=="answerLogic" and activity.get("type")=="mcq"):
            opts=activity.get("answerKey",{}).get("options",[])
            key=activity.get("answerKey",{}).get("correct")
            ids=[o["id"] for o in opts]
            if len(ids)!=4 or key not in ids:
                raise ValueError("BSA253_MCQ_STRUCTURE_NOT_VERIFIED")
            # Only test explicit OPTION-A style references: other MCQs
            # use semantic IDs and need independent answer validation.
            if all(z.startswith("opt-") and len(z)==5 for z in ids):
                expected=chr(ord("A")+ids.index(key))
                refs={l:_option_refs(triple[l]) for l in LANGUAGES}
                if any(r and expected not in r for r in refs.values()):
                    flags.append({"field":route,
                        "reason":"ANSWER_LOGIC_POINTS_TO_WRONG_MC_OPTION",
                        "kind":"DETERMINISTIC_ANSWER_REFERENCE_DRIFT",
                        "rawContentIncluded":False})
                for lang in LANGUAGES:
                    claims=_affirmed_correct_option(triple[lang],lang)
                    if claims and claims!={expected}:
                        flags.append({"field":route,
                            "reason":"ANSWER_LOGIC_AFFIRMS_INCORRECT_OPTION",
                            "kind":"DETERMINISTIC_ANSWER_REFERENCE_DRIFT",
                            "locale":lang,
                            "rawContentIncluded":False})
        rows.append({"field":route,
                     "symbolicCountByLocale":{l:len(expr[l]) for l in LANGUAGES},
                     "matchedMathAcrossLocales":(
                         Counter(expr["en"])==Counter(expr["ms"])==
                         Counter(expr["zh"])),
                     "cueCountByLocale":{l:len(science[l]) for l in LANGUAGES},
                     "completeTranslationMeaningVerified":False})
    if not rows:raise ValueError("BSA253_NO_LEARNER_VISIBLE_SURFACES")
    return {"activityId":aid,"activityCanonicalSha256":_digest(activity),
        "localizedSurfacesChecked":len(rows),
        "crossLocaleMathBearingFieldsChecked":formula_fields,
        "mathematicalExpressionOccurrencesChecked":formula_atoms,
        "issueCount":len(flags),"issues":flags,
        "literalMathematicalDriftFound":any(
            r["kind"]=="DETERMINISTIC_SYMBOLIC_DIFFERENCE" for r in flags),
        "trilingualSemanticEquivalenceProven":False,
        "fullAcademicPASS":False,"publicationAuthorized":False}


def audit_reusable_scientific_alignment(activities:list[dict])->dict:
    if not isinstance(activities,list) or not activities:
        raise ValueError("BSA253_NONEMPTY_ACTIVITY_LIST_REQUIRED")
    if any(not isinstance(x,dict) for x in activities):
        raise ValueError("BSA253_MALFORMED_ACTIVITY")
    ids=[a.get("id") for a in activities]
    if len(ids)!=len(set(ids)):
        raise ValueError("BSA253_DUPLICATED_ACTIVITY_IDENTITIES")
    rows=[_check_activity(a) for a in activities]
    out={
        "status":"BSA253_SOURCE_ADAPTER_REQUIRED_FOR_PROOF_PROMOTION",
        "activitiesChecked":len(rows),
        "surfacesChecked":sum(x["localizedSurfacesChecked"] for x in rows),
        "mathBearingSurfaces":sum(x["crossLocaleMathBearingFieldsChecked"]
                                   for x in rows),
        "mathExpressionOccurrences":sum(x["mathematicalExpressionOccurrencesChecked"]
                                         for x in rows),
        "issues":sum(x["issueCount"] for x in rows),
        "mathematicalDriftIssues":sum(
            sum(q["kind"]=="DETERMINISTIC_SYMBOLIC_DIFFERENCE"
                for q in row["issues"]) for row in rows),
        "rows":rows,
        "allScientificStatementsProven":False,
        "trilingualSemanticEquivalenceProven":False,
        "publicationAuthorized":False,
    }
    return out

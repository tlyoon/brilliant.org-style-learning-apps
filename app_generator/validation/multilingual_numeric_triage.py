"""Source-bound EN/MS/ZH numeric-token drift detection, not translation PASS.

NFKC handles full-width digits, CJK-adjacent Arabic numerals and superscripts.
Different literal appearances are actionable triage, not guaranteed mistranslation
(e.g., Chinese number words or algebraically equivalent forms may differ).
No protected text/passages are returned in the diagnostic report.
"""
from __future__ import annotations

from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
import re
from typing import Any
import unicodedata

from app_generator.validation.reviewer_source_packets import source_packets_for_activities

_LANGS=("en","ms","zh")
_TOKENS=re.compile(r"[0-9]+(?:[.,][0-9]+)?")
_FIELDS=("prompt","feedback","answerLogic","explanation","objective",
         "accessibilityText")


def numeric_tokens(value: str) -> list[str]:
    if not isinstance(value,str):
        raise TypeError("numeric token source must be text")
    # Decimal punctuation is preserved; do not translate prose or infer units.
    norm=unicodedata.normalize("NFKC",value)
    return _TOKENS.findall(norm)


def _triplets(activity: dict[str,Any]):
    for field in _FIELDS:
        value=activity.get(field)
        if isinstance(value,dict) and all(isinstance(value.get(lang),str) for lang in _LANGS):
            yield field,value
    hints=activity.get("hints")
    if isinstance(hints,list):
        for i,hint in enumerate(hints):
            if isinstance(hint,dict) and all(isinstance(hint.get(lang),str) for lang in _LANGS):
                yield f"hints[{i}]",hint
    key=activity.get("answerKey",{})
    if isinstance(key,dict):
        opts=key.get("options",[])
        if isinstance(opts,list):
            for i,opt in enumerate(opts):
                if isinstance(opt,dict) and isinstance(opt.get("label"),dict):
                    value=opt["label"]
                    if all(isinstance(value.get(lang),str) for lang in _LANGS):
                        yield f"answerKey.options[{i}].label",value


def _notation_candidate(texts: dict[str,str], counts: dict[str,Counter]) -> str:
    """Classify a narrow *possible* notation explanation, never correctness."""
    en=unicodedata.normalize("NFKC", texts["en"])
    zh=unicodedata.normalize("NFKC", texts["zh"])
    if counts["en"]!=counts["ms"]:
        return "UNEXPLAINED_LITERAL_DIFFERENCE"
    missing=counts["en"]-counts["zh"]
    extra=counts["zh"]-counts["en"]
    if extra or len(missing)!=1:
        return "UNEXPLAINED_LITERAL_DIFFERENCE"
    token,number=next(iter(missing.items()))
    if token in ("1","2"):
        # Require the exact numeric dimension notation in EN and precisely
        # as many Chinese-character notation occurrences as missing digits.
        dimension_pattern=rf"(?<![0-9A-Za-z]){token}\s*-?\s*[dD]\b"
        en_dim_count=len(re.findall(dimension_pattern,en))
        written = "\u4e00\u7ef4" if token=="1" else "\u4e8c\u7ef4"
        if en_dim_count>=number and zh.count(written)>=number:
            return ("POSSIBLE_ONE_DIMENSION_NOTATION" if token=="1"
                    else "POSSIBLE_TWO_DIMENSION_NOTATION")
    if (token=="0" and number==1 and
            "momentum" in en.casefold() and "\u96f6" in zh):
        return "POSSIBLE_WRITTEN_ZERO_NOTATION"
    return "UNEXPLAINED_LITERAL_DIFFERENCE"


def _scan_activity(activity: dict[str,Any]) -> tuple[int,list[dict[str,Any]]]:
    checked=0
    flags=[]
    for field,texts in _triplets(activity):
        checked+=1
        number_sets={lang:Counter(numeric_tokens(texts[lang])) for lang in _LANGS}
        if number_sets["en"] != number_sets["ms"] or number_sets["en"] != number_sets["zh"]:
            flags.append({
                "field":field,
                "reasonCode":"CROSS_LOCALE_NUMERIC_TOKEN_DIFFERENCE",
                "numericTokenCounts":{lang:sum(number_sets[lang].values()) for lang in _LANGS},
                "crossLocaleNumericTokensEqual":False,
                "candidateReason":_notation_candidate(texts,number_sets),
                "confirmedSemanticEquivalence":False,
            })
    return checked,flags


def audit_source_bound_multilingual_numeric_triage(
    *, package_file:Path,source_pdf:Path,source_packets_file:Path,
) -> dict[str,Any]:
    if not all(path.is_file() for path in (package_file,source_pdf,source_packets_file)):
        raise ValueError("private package, original PDF and source packets required")
    pkg_raw=package_file.read_bytes()
    pdf_raw=source_pdf.read_bytes()
    if pdf_raw[:5]!=b"%PDF-":
        raise ValueError("original PDF not recognized")
    pkg=json.loads(pkg_raw)
    packet=json.loads(source_packets_file.read_text(encoding="utf-8"))
    pkg_sha=sha256(pkg_raw).hexdigest()
    src_sha=sha256(pdf_raw).hexdigest()
    acts=pkg.get("activities")
    if (not isinstance(acts,list) or len(acts)!=18 or
        len({a.get("id") for a in acts if isinstance(a,dict)})!=18 or
        packet.get("sourceSha256")!=src_sha or
        packet.get("packageSha256")!=pkg_sha or
        not isinstance(packet.get("packets"),dict) or len(packet["packets"])!=18):
        raise ValueError("private source/package manifest mismatch")
    anchors=[]
    for a in acts:
        old=packet["packets"].get(a["id"])
        if not isinstance(old,dict) or not isinstance(old.get("sourceAnchors"),list):
            raise ValueError("source passage receipt missing")
        anchors.extend(old["sourceAnchors"])
    fresh=source_packets_for_activities(source_pdf,src_sha,pkg,anchors)
    if any(fresh[id_]["passageSha256"]!=packet["packets"][id_]["passageSha256"] or
           fresh[id_]["sourceEvidence"]!=packet["packets"][id_]["sourceEvidence"]
           for id_ in fresh):
        raise ValueError("original PDF source passages no longer reverify")
    rows=[]
    for activity in acts:
        count,flags=_scan_activity(activity)
        rows.append({"activityId":activity["id"],"localizedFieldsChecked":count,
                     "numericTokenDriftFlags":flags,
                     "academicQA":"REVIEW_REQUIRED"})
    return {
        "status":"SOURCE_BOUND_NUMERIC_TOKEN_TRIAGE",
        "sourceSha256":src_sha,"packageSha256":pkg_sha,
        "sourceVerifiedActivities":len(fresh),
        "localizedFieldsChecked":sum(r["localizedFieldsChecked"] for r in rows),
        "numericDriftFlagCount":sum(len(r["numericTokenDriftFlags"]) for r in rows),
        "activitiesWithFlags":sum(bool(r["numericTokenDriftFlags"]) for r in rows),
        "numericTokenIdentityProvesTranslation":False,
        "academicQA":"REVIEW_REQUIRED","academicPASS":0,"publicationAuthorized":False,
        "activities":rows,
    }

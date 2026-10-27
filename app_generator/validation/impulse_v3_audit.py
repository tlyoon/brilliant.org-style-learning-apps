"""Fail-closed v3 academic subclaim audit: five options and three locales.

Evidence from matching terms or exact arithmetic does not prove all nuanced
translations, visuals, or student-level clarity. Full academic PASS remains off.
"""
from __future__ import annotations

from hashlib import sha256
import json
import re
from pathlib import Path
from typing import Any

from app_generator.validation.impulse_v3 import (
    V3_LABEL, V3_ANSWER_LOGIC, ITEM_ID, review_candidate_v3, canonical_digest,
)
from app_generator.validation.impulse_semantics import (
    IDS, OPTION_CONCEPTS, option_signature, narrative_semantic_surface,
    physics_counterexamples,
)
from app_generator.validation.impulse_qualifier_repair import ACTIVITY_ID

EXPECTED_V3_FILE_SHA256 = "cd2c17864e155cc870e5ba8f6d3013a0c73e3bf3aa2d22a91834030eaf047fbc"
EXPECTED_V3_CANONICAL_SHA256 = "33828329938512a661fbebd71ef04a830545981878555173bab50c86c3bb5f56"

NEW_ITEM_MARKERS = {
    "en": ("net external impulse", "negligible", "collision impulse",
           "does not require each external force"),
    "ms": ("impuls luar bersih", "boleh diabaikan", "impuls perlanggaran",
           "tidak mensyaratkan setiap daya luar"),
    "zh": ("\u51c0\u5916\u529b\u51b2\u91cf", "\u53ef\u5ffd\u7565",
           "\u78b0\u649e\u76f8\u4e92\u4f5c\u7528\u51b2\u91cf", "\u4e0d\u8981\u6c42\u6bcf\u4e00\u4e2a\u5916\u529b"),
}


# Negative controls for a known lexical-marker false-positive failure mode.
# Deliberately narrow to explicit, scientifically falsifiable contradictions.
# Absence of a conflict NEVER establishes translation equivalence.
EXPLICIT_CONTRADICTIONS = {
    "en": (
        ("individual-forces-must-be-small",
         r"\b(?:each|every|all)\s+external\s+forces?\b.{0,48}\b(?:must|need|have to)\s+(?:be\s+)?(?:small|negligible)\b"),
        ("net-external-impulse-not-negligible",
         r"\bnet\s+external\s+impulse\b.{0,40}\b(?:not|never)\s+(?:be\s+)?(?:negligible|small)\b"),
    ),
    "ms": (
        ("individual-forces-must-be-small",
         r"\b(?:setiap|semua)\s+daya\s+luar\b.{0,48}\b(?:mesti|harus|wajib)\s+(?:menjadi\s+)?kecil\b"),
        ("net-external-impulse-not-negligible",
         r"\bimpuls\s+luar\s+bersih\b.{0,40}\btidak\s+(?:boleh\s+diabaikan|kecil)\b"),
    ),
    "zh": (
        ("individual-forces-must-be-small",
         r"(?:\u6bcf\u4e00\u4e2a|\u6bcf\u4e2a)\u5916\u529b.{0,20}(?:\u90fd)?\u5fc5\u987b.{0,16}(?:\u5f88\u5c0f|\u5fae\u5c0f|\u8f83\u5c0f)"),
        ("net-external-impulse-not-negligible",
         r"\u51c0\u5916\u529b\u51b2\u91cf.{0,20}(?:\u4e0d\u53ef\u5ffd\u7565|\u4e0d\u80fd\u5ffd\u7565|\u5fc5\u987b\u5f88\u5927)"),
    ),
}


def net_impulse_scope_conflicts(text: str, language: str) -> list[str]:
    if language not in EXPLICIT_CONTRADICTIONS or not isinstance(text,str):
        raise ValueError("unsupported localized net-impulse proposition")
    normalized=" ".join(text.casefold().split())
    return [code for code,regex in EXPLICIT_CONTRADICTIONS[language]
            if re.search(regex,normalized) is not None]


def check_first_option(option: dict[str,Any]) -> dict[str,Any]:
    labels = option.get("label",{})
    flags={}
    for lang, markers in NEW_ITEM_MARKERS.items():
        text = labels.get(lang,"") if isinstance(labels,dict) else ""
        missing = [marker for marker in markers if marker not in text.casefold()]
        conflicts = net_impulse_scope_conflicts(text,lang)
        flags[lang] = {
            "status":"BOUNDED_CONCEPT_PRESENT" if not (missing or conflicts)
                     else "REVIEW_REQUIRED",
            "reason":("explicit conflicting net-impulse proposition: "+",".join(conflicts)
                      if conflicts else
                      "missing bounded source-condition markers"
                      if missing else
                      "bounded scope markers present; semantic equivalence unverified"),
            "explicitContradictionCodes":conflicts,
        }
    return flags


def audit_v3(candidate_file:Path, review_file:Path, parent_v2_file:Path,
             parent_v2_review:Path, source_pdf:Path) -> dict[str,Any]:
    raw=candidate_file.read_bytes()
    digest=sha256(raw).hexdigest()
    if digest!=EXPECTED_V3_FILE_SHA256:
        raise ValueError("unexpected private v3 file version")
    candidate=json.loads(raw.decode("utf-8"))
    if canonical_digest(candidate)!=EXPECTED_V3_CANONICAL_SHA256:
        raise ValueError("unexpected v3 canonical content identity")
    receipt=json.loads(review_file.read_text(encoding="utf-8"))
    if (receipt.get("candidateFileSha256")!=digest or
        receipt.get("candidateCanonicalSha256")!=EXPECTED_V3_CANONICAL_SHA256 or
        receipt.get("reviewOnly") is not True or
        receipt.get("publicationAuthorized") is not False or
        receipt.get("humanReviewed") is not False):
        raise ValueError("private v3 receipt is stale or claims unauthorized approval")
    reconstructed,_=review_candidate_v3(parent_v2_file,parent_v2_review,source_pdf)
    if candidate!=reconstructed:
        raise ValueError("v3 content deviates from exact parent-bound correction")
    matches=[a for a in candidate.get("activities",[]) if a.get("id")==ACTIVITY_ID]
    if len(matches)!=1:
        raise ValueError("v3 target activity missing or ambiguous")
    activity=matches[0]
    if activity.get("answerLogic")!=V3_ANSWER_LOGIC:
        raise ValueError("independent v3 answer explanation mismatched")
    choices=activity["interaction"]["items"]
    if len(choices)!=len(IDS) or set(x.get("id") for x in choices)!=set(IDS):
        raise ValueError("v3 selected/distractor IDs changed")
    witness=physics_counterexamples()
    result=[]
    for item in choices:
        label=item.get("label",{})
        if item["id"]==ITEM_ID:
            if label!=V3_LABEL:
                raise ValueError("reviewed net-impulse correction altered")
            checks=check_first_option(item)
        else:
            checks=option_signature(item,OPTION_CONCEPTS[item["id"]])
        verified=all(x["status"] in ("BOUNDED_CONCEPT_PRESENT",
                                     "BOUNDED_SIGNATURE_FOUND") for x in checks.values())
        result.append({
            "itemId":item["id"], "status":"BOUNDED_PROPOSITION_MODEL_VERIFIED"
                                    if verified else "REVIEW_REQUIRED",
            "localized":checks,
            "reason":("bounded physics and explicit concept signatures agree; "
                      "full translation equivalence unverified" if verified
                      else "one or more language conditions unsupported"),
        })
    narrative=narrative_semantic_surface(activity)
    return {
        "sourceSha256":receipt["sourcePdfSha256"],
        "candidateFileSha256":digest,
        "parentV2FileSha256":receipt["parentV2FileSha256"],
        "activityId":ACTIVITY_ID,
        "options":result,
        "boundedOptionsVerified":sum(x["status"]=="BOUNDED_PROPOSITION_MODEL_VERIFIED" for x in result),
        "optionReviewsRequired":sum(x["status"]=="REVIEW_REQUIRED" for x in result),
        "multilingualNarrative":narrative,
        "physicsCounterexample":witness,
        "fullSemanticEquivalenceVerified":False,
        "fullAcademicActivitiesPassed":0,
        "academicQA":"REVIEW_REQUIRED",
        "humanReviewed":False,
        "publicationAuthorized":False,
    }

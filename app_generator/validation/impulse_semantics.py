"""Conservative, source-version-bound review of a five-option trilingual physics item.

Deterministic mathematical counterexamples are independently recomputed.
Small multilingual lexical signatures detect lost polarity/scope but do not
claim semantic equivalence or human-level translated-text understanding.
"""
from __future__ import annotations

from fractions import Fraction as Q
import hashlib
import json
from pathlib import Path
import re
from typing import Any

from app_generator.validation.impulse_qualifier_repair import ACTIVITY_ID, SELECTED_ITEM, SOURCE_SHA256

IDS = (
    "item-large-internal-forces",
    "item-action-reaction-internal",
    SELECTED_ITEM,
    "item-deformation-decreases-momentum",
    "item-requires-zero-external-forces-ever",
)
SELECTED = IDS[:3]
EXPECTED_V2_SHA256 = "31a52ab461c62d0d9c7e244290b8ec94f3dd105f8056f2a8bb7db2b61cd5967a"

# Each language has independently specified meaning-carrying clause markers.
# These markers are a bounded screening test, NOT a complete translation judge.
MARKERS = {
    "en": {
        "approx_condition": ("negligible", "approximately"),
        "exact_condition": ("zero", "exactly"),
        "internal_pair": ("third law", "internal"),
        "energy_misconception": ("kinetic energy", "momentum decreases"),
        "external_before_after": ("only if", "zero", "before", "after"),
        "force_universal": ("vastly greater", "any external"),
    },
    "ms": {
        "approx_condition": ("boleh diabaikan", "anggaran"),
        "exact_condition": ("sifar", "tepat"),
        "internal_pair": ("hukum ketiga", "dalaman"),
        "energy_misconception": ("tenaga kinetik", "momentum linear sistem berkurang"),
        "external_before_after": ("hanya jika", "sifar", "sebelum", "selepas"),
        "force_universal": ("jauh lebih besar", "sebarang daya luar"),
    },
    "zh": {
        "approx_condition": ("\u53ef\u5ffd\u7565", "\u8fd1\u4f3c"),
        "exact_condition": ("\u96f6", "\u7cbe\u786e"),
        "internal_pair": ("\u725b\u987f\u7b2c\u4e09\u5b9a\u5f8b", "\u5185\u90e8"),
        "energy_misconception": ("\u52a8\u80fd", "\u52a8\u91cf", "\u51cf\u5c11"),
        "external_before_after": ("\u4ec5\u5f53", "\u96f6", "\u524d\u540e"),
        "force_universal": ("\u8fdc\u5927\u4e8e", "\u4efb\u4f55\u5916\u90e8\u529b"),
    },
}
OPTION_CONCEPTS = dict(zip(IDS,(
    "force_universal", "internal_pair", "conditional_momentum",
    "energy_misconception", "external_before_after"
)))

def norm(s: str) -> str:
    return " ".join(s.casefold().split())

def ordered_condition(text: str, language: str) -> tuple[bool,str]:
    """Bounded order/scope test for condition-to-consequence in option 3."""
    value=norm(text)
    approx_c, approx_result=MARKERS[language]["approx_condition"]
    exact_c, exact_result=MARKERS[language]["exact_condition"]
    def locate(term: str, start: int=0) -> int:
        if language in ("en","ms"):
            hit=re.search(r"(?<![a-z])"+re.escape(term)+r"(?![a-z])",value[start:])
            return start+hit.start() if hit else -1
        return value.find(term,start)
    p=locate(approx_result)
    e=locate(exact_result,p+len(approx_result)) if p>=0 else -1
    c=locate(approx_c)
    z=locate(exact_c)
    # Grammar varies: Chinese usually places the condition first; English
    # and Malay often say "approximately conserved WHEN impulse is small".
    # Bind both condition/result pairs to separate, nearby clauses.
    if not (0 <= p < e and c >= 0 and z >= 0 and
            abs(p-c)<=100 and abs(e-z)<=120 and
            max(p,c)<min(e,z)):
        return False,"approximate/exact conditional pairs missing, reversed or crossed"
    if language=="en" and re.search(r"\b(?:not|never)\s+(?:approximately|exactly)\b",value):
        return False,"explicit negation of approximate/exact conservation"
    if language=="ms" and re.search(r"\b(?:tidak|bukan)\s+(?:diabadikan|secara|anggaran|tepat)\b",value):
        return False,"explicit Malay negation contradicts conservation"
    if language=="zh" and re.search(r"\u4e0d(?:\u8fd1\u4f3c|\u7cbe\u786e|\u5b88\u6052)",value):
        return False,"explicit Chinese negation contradicts conservation"
    return True,"conditional lexical signatures aligned; semantic completeness unverified"

def option_signature(option: dict[str,Any], concept: str) -> dict[str,Any]:
    out={}
    labels=option.get("label")
    for lang in ("en","ms","zh"):
        v=labels.get(lang) if isinstance(labels,dict) else None
        if not isinstance(v,str) or not v.strip() or "\ufffd" in v or "?" in v:
            out[lang]={"status":"REVIEW_REQUIRED","reason":"missing/corrupt localized label"}
            continue
        if lang=="zh" and not re.search(r"[\u4e00-\u9fff]",v):
            out[lang]={"status":"REVIEW_REQUIRED","reason":"no Chinese script"}
            continue
        if concept=="conditional_momentum":
            yes,reason=ordered_condition(v,lang)
        else:
            keys=MARKERS[lang][concept]
            missing=[x for x in keys if x not in norm(v)]
            yes=not missing
            reason=(
                "bounded localized proposition signature found; translation equivalence unverified"
                if yes else "missing bounded proposition signature, cross-language meaning needs review"
            )
        out[lang]={"status":"BOUNDED_SIGNATURE_FOUND" if yes else "REVIEW_REQUIRED",
                   "reason":reason}
    return out

def narrative_semantic_surface(activity: dict[str,Any]) -> dict[str,Any]:
    """Independently specified bounded physics concept signatures for 7 fields.

    Passing is only evidence that crucial tokens exist with exact formulae;
    it never establishes full translation equivalence or learner clarity.
    """
    required={
        "en":(("approximate","approximately"),("exact",),("external impulse",)),
        "ms":(("anggaran","hampir sifar"),("tepat",),("impuls luar",)),
        "zh":(("\u8fd1\u4f3c",),("\u7cbe\u786e",),("\u5916\u529b\u51b2\u91cf",)),
    }
    ix=activity.get("interaction",{})
    selected=next((x for x in ix.get("items",[]) if x.get("id")==SELECTED_ITEM),None)
    nodes={
        "prompt":activity.get("prompt"),
        "feedback":activity.get("feedback"),
        "answerLogic":activity.get("answerLogic"),
        "explanation":activity.get("explanation"),
        "hint2":activity.get("hints",[])[1] if len(activity.get("hints",[]))>1 else None,
        "prerequisite":activity.get("prerequisiteRecovery",{}).get("prompt"),
        "selectedItem":selected.get("label") if selected else None,
    }
    cases=[]
    for field,values in nodes.items():
        for lang in ("en","ms","zh"):
            val=values.get(lang) if isinstance(values,dict) else None
            value=norm(val) if isinstance(val,str) else ""
            required_terms=required[lang]
            errors=[]
            if not value or "\ufffd" in value:
                errors.append("localized text missing or corrupt")
            for names in required_terms:
                if not any(name in value for name in names):
                    errors.append("bounded concept missing")
            if field in ("feedback","explanation","prerequisite"):
                if norm("\u0394p") not in value or "j_ext" not in value:
                    errors.append("exact impulse-momentum relation missing")
            if field=="explanation" and "\u222b" not in value:
                errors.append("integral momentum-impulse formula absent")
            cases.append({"field":field,"language":lang,
                          "status":"BOUNDED_CONCEPT_PRESENT" if not errors else "REVIEW_REQUIRED",
                          "reason":"; ".join(errors) if errors else "bounded terms/formula present, semantics not certified"})
    return {
        "narrativeFields":len(nodes),"localizedFieldChecks":len(cases),
        "boundedConceptsPresent":sum(x["status"]=="BOUNDED_CONCEPT_PRESENT" for x in cases),
        "translationMeaningCertified":False,
        "checks":cases,
    }


def physics_counterexamples() -> dict[str,str]:
    m,u=Q(1),Q(2)
    p_before=m*u
    vf=p_before/(m+m)
    p_after=(m+m)*vf
    ki=m*u*u/2
    kf=(m+m)*vf*vf/2
    if p_before!=p_after or not ki>kf:
        raise ValueError("sticky-collision momentum/energy witness fails")
    # Nonzero external impulse changes system p, however small it is.
    net_j=Q(1,100000)
    if p_before+net_j==p_before:
        raise ValueError("nonzero external impulse witness fails")
    # Nonzero external forces can cancel *each other* and need not be
    # smaller than each individual internal contact force.
    f_ext_1,f_ext_2=Q(1000),Q(-1000)
    f_internal=Q(1)
    if f_ext_1+f_ext_2!=0 or abs(f_ext_1)<=abs(f_internal):
        raise ValueError("opposed external forces counterexample fails")
    # Gravity before/after impact does not determine net impact impulse.
    f_before,f_after,f_during=Q(10),Q(10),Q(0)
    if f_before<=0 or f_after<=0 or f_during*Q(1,100)!=0:
        raise ValueError("before/after forces witness fails")
    return {
        "stickingInitialMomentum":str(p_before),
        "stickingFinalMomentum":str(p_after),
        "stickingKEInitial":str(ki),
        "stickingKEFinal":str(kf),
        "nonzeroExternalImpulse":str(net_j),
        "balancedExternalForceA":str(f_ext_1),
        "balancedExternalForceB":str(f_ext_2),
        "exampleInternalForce":str(f_internal),
        "nonzeroGravityBeforeAndAfter":str(f_before),
        "netExternalImpactImpulse":"0",
    }

def audit_impulse_candidate(package_file: Path, review_file: Path,
                             source_pdf: Path) -> dict[str,Any]:
    raw=package_file.read_bytes()
    digest=hashlib.sha256(raw).hexdigest()
    if digest!=EXPECTED_V2_SHA256:
        raise ValueError("unexpected or changed impulse candidate file version")
    review=json.loads(review_file.read_text(encoding="utf-8"))
    if (review.get("candidatePackageFileSha256")!=digest or
        review.get("controlledSourceSha256")!=SOURCE_SHA256 or
        review.get("reviewOnly") is not True or
        review.get("publicationAuthorized") is not False):
        raise ValueError("candidate review receipt mismatched or unapproved")
    if hashlib.sha256(source_pdf.read_bytes()).hexdigest()!=SOURCE_SHA256:
        raise ValueError("controlled textbook PDF identity mismatch")
    package=json.loads(raw.decode("utf-8"))
    matches=[x for x in package.get("activities",[]) if x.get("id")==ACTIVITY_ID]
    if len(matches)!=1:
        raise ValueError("target activity missing/duplicated")
    activity=matches[0]
    if activity.get("interactionMode")!="selection":
        raise ValueError("candidate answer mode changed")
    ix=activity.get("interaction",{})
    items=ix.get("items",[])
    if len(items)!=len(IDS) or set(x.get("id") for x in items)!=set(IDS):
        raise ValueError("answer choices missing/duplicated/unexpected")
    if ix.get("correctSelections")!=list(SELECTED):
        raise ValueError("selection key not equal to independently specified reference")
    source=physics_counterexamples()
    narrative=narrative_semantic_surface(activity)
    results=[]
    for item in items:
        id_=item["id"]
        signatures=option_signature(item,OPTION_CONCEPTS[id_])
        missing=[lang for lang,v in signatures.items() if v["status"]!="BOUNDED_SIGNATURE_FOUND"]
        status=("REVIEW_REQUIRED" if missing or id_==IDS[0]
                else "BOUNDED_PROPOSITION_MODEL_VERIFIED")
        caveat=("Overstrong universal individual-force comparison does not follow from a small net external impulse"
                if id_==IDS[0] else
                "At least one language lacks the expected bounded meaning signature"
                if missing else
                "Mathematical counterexample or Newton-third-law premise agrees; full semantic QA remains pending")
        results.append({"itemId":id_,"intendedCorrect":id_ in SELECTED,
                        "status":status,"localizedSignatures":signatures,
                        "reason":caveat})
    count=sum(x["status"]=="BOUNDED_PROPOSITION_MODEL_VERIFIED" for x in results)
    return {
        "sourceSha256":SOURCE_SHA256,"candidateFileSha256":digest,
        "activityId":ACTIVITY_ID,"options":results,
        "boundedOptionModelsVerified":count,
        "optionQualifiersReviewRequired":len(results)-count,
        "numericalWitness":source,
        "multilingualNarrative":narrative,
        "completeMultilingualSemanticAgreement":False,
        "academicQA":"REVIEW_REQUIRED","humanReviewed":False,
        "publicationAuthorized":False,
    }

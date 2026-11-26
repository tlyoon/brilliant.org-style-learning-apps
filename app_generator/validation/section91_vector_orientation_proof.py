"""BSA275 first reusable vector-orientation misconception witness (NOT admission).

The original Serway law p=m*v implies a nonzero momentum vector PARALLEL
to v, disproving a false alternative claiming it is always perpendicular or
vertically upward. Fully parse all three exact statement localizations; use
two exact rational 3D countermodels independently of the stored answer key.
All other scientific/translation/diagram tasks remain REVIEW_REQUIRED.

Proof production is a registered BSA275 batch handler; it does not modify
A1/A2, sign an academic receipt or grant any new full activity PASS.
"""
from __future__ import annotations
from fractions import Fraction
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

from app_generator.validation.section91_first_distractor_proof import (
    _PROMPT, _parse_complete,
)
from app_generator.validation.section91_formal_physics import (
    _SOURCE_SHA, _CANDIDATE_SHA, _source_axioms, _digest,
)
from app_generator.validation.full_semantic_proof_queue import (
    plan_full_semantic_proofs,
)
from app_generator.validation.source_passages import extract_pages
from app_generator.runtime.v3_selected_textbook_scientific_provenance import (
    _source_activity_anchors,
)

_ACTIVITY="act-mcq-01-vector-nature"
_OPTION="opt-d"
_PATH="answerKey/options/3/label"
_KIND="MCQ_DISTRACTOR_SCIENCE"
_FALSE_OPTION={
    "en":(
        "Their linear momenta point vertically upward perpendicular to their flight path",
        ", because ",
        "momentum always acts at a right angle to velocity",
        ".",
    ),
    "ms":(
        "Momentum linear kedua-duanya menghala tegak ke atas berserenjang dengan laluan penerbangan",
        ", kerana ",
        "momentum sentiasa bertindak pada sudut tepat terhadap halaju",
        ".",
    ),
    "zh":(
        "\u5b83\u4eec\u7684\u7ebf\u52a8\u91cf\u5782\u76f4\u5411\u4e0a\u5e76\u5782\u76f4\u4e8e\u98de\u884c\u8def\u5f84",
        "\uff0c\u56e0\u4e3a",
        "\u52a8\u91cf\u603b\u662f\u4e0e\u901f\u5ea6\u65b9\u5411\u5782\u76f4",
        "\u3002",
    ),
}


def _witness_data(*,mass:Fraction,speed:Fraction)->dict[str,Any]:
    if mass<=0 or speed<=0:
        raise ValueError("BSA275_POSITIVE_MASS_NONZERO_SPEED_REQUIRED")
    cases=[]
    for velocity_x in (speed,-speed):
        v=(velocity_x,Fraction(0),Fraction(0))
        p=tuple(mass*component for component in v)
        dot=sum(a*b for a,b in zip(v,p))
        cross=(v[1]*p[2]-v[2]*p[1],
               v[2]*p[0]-v[0]*p[2],
               v[0]*p[1]-v[1]*p[0])
        if (p[0]==0 or p[1]!=0 or p[2]!=0 or
            dot!=mass*speed*speed or dot<=0
            or cross!=(0,0,0)):
            raise ValueError("BSA275_VECTOR_PARALLEL_NOT_PERPENDICULAR")
        cases.append({
            "velocity":[str(x) for x in v],
            "momentum":[str(x) for x in p],
            "dotVelocityMomentum":str(dot),
            "crossVelocityMomentum":[str(x) for x in cross],
            "verticalMomentumComponent":str(p[2]),
            "momentumPerpendicularToVelocity":False,
        })
    if Fraction(cases[0]["momentum"][0]) != -Fraction(cases[1]["momentum"][0]):
        raise ValueError("BSA275_OPPOSITE_VECTORS_NOT_CONFIRMED")
    return {"mass":str(mass),"speed":str(speed),"drones":cases}


def verify_perpendicular_momentum_false(
    *,source_pdf:Path,candidate_path:Path,package:dict|None=None
)->dict[str,Any]:
    if (source_pdf.is_symlink() or not source_pdf.is_file()
        or candidate_path.is_symlink() or not candidate_path.is_file()
        or sha256(source_pdf.read_bytes()).hexdigest()!=_SOURCE_SHA
        or sha256(candidate_path.read_bytes()).hexdigest()!=_CANDIDATE_SHA):
        raise ValueError("BSA275_ORIGINAL_TEXTBOOK_AND_CANDIDATE_REQUIRED")
    axioms=_source_axioms(source_pdf,_SOURCE_SHA)
    if (axioms.get("defined to be the product of the mass and velocity",0)<1
        or axioms.get("linear momentum is a vector",0)<1):
        raise ValueError("BSA275_MISSING_ORIGINAL_VECTOR_LAW")
    candidate=json.loads(candidate_path.read_text(encoding="utf8"))
    if package is not None and candidate!=package:
        raise ValueError("BSA275_CANDIDATE_PACKAGE_NOT_FROZEN")
    roster=candidate.get("activities")
    if not isinstance(roster,list) or len(roster)!=18:
        raise ValueError("BSA275_UNTRUSTED_ACTIVITY_ROSTER")
    act=roster[0]
    if act.get("id")!=_ACTIVITY:
        raise ValueError("BSA275_WRONG_ACTIVITY")
    answer=act.get("answerKey",{})
    options=answer.get("options",[])
    if (not isinstance(options,list) or len(options)!=4
        or answer.get("correct")!="opt-a"
        or options[3].get("id")!=_OPTION):
        raise ValueError("BSA275_FALSE_OPTION_OR_KEY_CHANGED")
    localized={}
    for language in ("en","ms","zh"):
        _parse_complete(act["prompt"].get(language),_PROMPT[language],
                        "BSA275_PREMISE_"+language.upper())
        localized[language]=_parse_complete(
            options[3]["label"].get(language),_FALSE_OPTION[language],
            "BSA275_OPTION_"+language.upper())
    pages=extract_pages(source_pdf)
    anchor=_source_activity_anchors(pages=pages,activities=roster)[0]
    if (anchor.get("activityId")!=_ACTIVITY
        or anchor.get("uniquePagePassageLocated") is not True
        or anchor.get("physicalPage") not in (1,2,3)):
        raise ValueError("BSA275_UNVERIFIED_ONE_TEXTBOOK_PASSAGE")
    queue=plan_full_semantic_proofs(package=candidate,source_sha256=_SOURCE_SHA)
    matches=[t for t in queue["tasks"] if (
        t["activityId"]==_ACTIVITY and t["kind"]==_KIND
        and t["surfacePath"]==_PATH)]
    if (len(matches)!=1 or queue["taskCount"]!=429
        or matches[0]["surfaceSha256"]!=_digest(options[3]["label"])):
        raise ValueError("BSA275_SOURCE_SIGNED_PENDING_TASK_NOT_REPRODUCIBLE")
    countermodels=[
        _witness_data(mass=Fraction(3,1),speed=Fraction(7,2)),
        _witness_data(mass=Fraction(11,3),speed=Fraction(9,4)),
    ]
    body={
        "taskId":matches[0]["taskId"],
        "taskKind":_KIND,
        "activityId":_ACTIVITY,
        "optionId":_OPTION,
        "surfacePath":_PATH,
        "surfaceSha256":matches[0]["surfaceSha256"],
        "sourceSha256":_SOURCE_SHA,
        "candidateSha256":_CANDIDATE_SHA,
        "sourcePageIndex":anchor["physicalPage"],
        "sourcePassageSha256":anchor["passageSha256"],
        "sourcePhysicsPremisesDigest":_digest(sorted(axioms.items())),
        "completeLocalizedFiniteGrammarDigests":localized,
        "proofFamily":"VECTOR_NONZERO_PARALLEL_TO_VELOCITY_NOT_PERPENDICULAR",
        "rationalVectorCountermodels":countermodels,
        "independentScienceWitnessVerified":True,
        "newProviderCalls":0,
        "publicationAuthorized":False,
        "academicTaskAccepted":False,
        "otherScientificClaimsAccepted":False,
        "completeAcademicProofGatesStillOpen":90,
    }
    return {**body,"witnessSha256":_digest(body)}


def independently_recheck_vector_witness(proof:dict[str,Any])->None:
    """Independent rational arithmetic readback, never trusting booleans."""
    if (not isinstance(proof,dict)
        or proof.get("proofFamily")!=
          "VECTOR_NONZERO_PARALLEL_TO_VELOCITY_NOT_PERPENDICULAR"
        or proof.get("academicTaskAccepted") is not False
        or proof.get("completeAcademicProofGatesStillOpen")!=90
        or proof.get("newProviderCalls")!=0
        or proof.get("publicationAuthorized") is not False):
        raise ValueError("BSA275_INDEPENDENT_COUNTERMODEL_INVALID")
    material={k:v for k,v in proof.items() if k!="witnessSha256"}
    if _digest(material)!=proof.get("witnessSha256"):
        raise ValueError("BSA275_VECTOR_WITNESS_INTEGRITY")
    cases=proof.get("rationalVectorCountermodels",[])
    if not isinstance(cases,list) or len(cases)!=2:
        raise ValueError("BSA275_TWO_RATIONAL_MODELS_REQUIRED")
    for case in cases:
        mass=Fraction(case["mass"])
        speed=Fraction(case["speed"])
        expected=_witness_data(mass=mass,speed=speed)
        if expected!=case:
            raise ValueError("BSA275_INDEPENDENT_VECTOR_ARITHMETIC_DISAGREES")

"""BSA277: original Serway three Newton momentum-rate false alternatives.

A finite, source-grounded adapter; does not infer correctness from marked
MCQ key, English cues or model-generated text. Each exact EN/MS/ZH claim is
separately refuted with two exact rational constant-mass, nonzero-force
models derived from F=dp/dt=m*a. The source is the same pinned original PDF,
not extra online PDFs. Any new scientific task remains UNADMITTED until a
separate immutable owner-private receipt and independent readback.
"""
from __future__ import annotations

from fractions import Fraction as F
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

from app_generator.validation.section91_first_distractor_proof import _parse_complete
from app_generator.validation.section91_formal_physics import (
    _SOURCE_SHA,_CANDIDATE_SHA,_source_axioms,_digest,
)
from app_generator.validation.full_semantic_proof_queue import plan_full_semantic_proofs
from app_generator.validation.source_passages import extract_pages
from app_generator.runtime.v3_selected_textbook_scientific_provenance import (
    _source_activity_anchors,
)

_ACTIVITY="act-mcq-03-net-force-definition"
_KIND="MCQ_DISTRACTOR_SCIENCE"
_PROMPT={
    "en":"A deep-space probe is subjected to a constant nonzero net force acting in the direction of its motion. According to Newton's second law expressed in terms of momentum, how is the net force related to the probe's linear momentum?",
    "ms":"Suatu kuar angkasa lepas dikenakan daya padu bukan sifar yang malar dan bertindak mengikut arah pergerakannya. Menurut hukum kedua Newton yang dinyatakan dalam sebutan momentum, bagaimanakah daya padu berkaitan dengan momentum linear kuar tersebut?",
    "zh":"深空探测器受到沿其运动方向的恒定非零合外力作用。根据用动量表示的牛顿第二定律，合外力与探测器的线动量之间有何关系？",
}
_OPTIONS={
    "opt-b":{
        "en":"The net force is equal to the probe's linear momentum itself, so a constant net force means the momentum remains constant.",
        "ms":"Daya padu adalah sama dengan momentum linear kuar itu sendiri, jadi daya padu yang malar bermakna momentum kekal malar.",
        "zh":"合外力等于探测器本身的线动量，因此恒定的合外力意味着动量保持不变。",
    },
    "opt-c":{
        "en":"The net force equals the time rate of change of mass only, having no effect on velocity or momentum.",
        "ms":"Daya padu adalah sama dengan kadar perubahan jisim terhadap masa sahaja, tanpa memberi kesan kepada halaju atau momentum.",
        "zh":"合外力仅等于质量对时间的变化率，对速度或动量没有任何影响。",
    },
    "opt-d":{
        "en":"The net force must be zero whenever an object already possesses linear momentum.",
        "ms":"Daya padu mestilah sifar apabila sesuatu objek sudah memiliki momentum linear.",
        "zh":"只要物体已经具有线动量，合外力就必须为零。",
    },
}
_CLAIMS={
    "opt-b":"FORCE_IS_NOT_MOMENTUM_AND_NONZERO_FORCE_CHANGES_P",
    "opt-c":"CONSTANT_MASS_NONZERO_FORCE_CHANGES_V_AND_P",
    "opt-d":"NONZERO_MOMENTUM_MAY_COEXIST_WITH_NONZERO_NET_FORCE",
}
_DIM_FORCE=(1,1,-2)
_DIM_P=(1,1,-1)
_DIM_MASS_RATE=(1,0,-1)


def _countermodels()->list[dict[str,Any]]:
    models=[]
    for mass,velocity,acceleration,dt in (
        (F(3,2),F(4,1),F(5,3),F(2,1)),
        (F(7,4),F(9,2),F(3,2),F(5,3)),
    ):
        force=mass*acceleration
        p0=mass*velocity
        v1=velocity+acceleration*dt
        p1=mass*v1
        mass_change_rate=F(0)
        dp_dt=(p1-p0)/dt
        if (mass<=0 or velocity<=0 or acceleration<=0 or dt<=0 or force<=0
            or p0<=0 or dp_dt!=force or p1<=p0 or v1<=velocity
            or mass_change_rate!=0 or force==mass_change_rate):
            raise ValueError("BSA277_RATIONAL_NEWTON_WITNESS_NOT_PHYSICAL")
        models.append({
            "mass":str(mass),"initialVelocity":str(velocity),
            "acceleration":str(acceleration),"timeIncrement":str(dt),
            "constantNonzeroNetForce":str(force),
            "initialMomentum":str(p0),"finalMomentum":str(p1),
            "finalVelocity":str(v1),"timeRateOfMomentumChange":str(dp_dt),
            "timeRateOfMassChange":str(mass_change_rate),
            "momentumRemainsConstant":False,
            "forceIsZeroGivenNonzeroMomentum":False,
            "forceEqualsMassRate":False,
        })
    return models


def _dimensions()->dict[str,list[int]]:
    mass=(1,0,0)
    velocity=(0,1,-1)
    acc=(0,1,-2)
    force=tuple(a+b for a,b in zip(mass,acc))
    momentum=tuple(a+b for a,b in zip(mass,velocity))
    mass_rate=tuple(a+b for a,b in zip(mass,(0,0,-1)))
    if force!=_DIM_FORCE or momentum!=_DIM_P or mass_rate!=_DIM_MASS_RATE:
        raise ValueError("BSA277_NEWTON_DIMENSIONS_NOT_REDERIVED")
    if len({force,momentum,mass_rate})!=3:
        raise ValueError("BSA277_FORCE_MOMENTUM_UNIT_FRAUD")
    return {
        "force":list(force),
        "momentum":list(momentum),
        "massRate":list(mass_rate),
        "siForce":"kg*m/s^2",
        "siMomentum":"kg*m/s",
        "siMassRate":"kg/s",
    }


def independently_verify_newton_force_witness(item:dict[str,Any])->None:
    if (not isinstance(item,dict) or item.get("optionId") not in _OPTIONS
        or item.get("sourceSha256")!=_SOURCE_SHA
        or item.get("candidateSha256")!=_CANDIDATE_SHA
        or item.get("proofFamily")!="NEWTON_NET_FORCE_IS_RATE_OF_MOMENTUM"
        or item.get("counterexampleClass")!=_CLAIMS[item["optionId"]]
        or item.get("independentScienceWitnessVerified") is not True
        or item.get("academicTaskAccepted") is not False
        or item.get("completeAcademicProofGatesStillOpen")!=90
        or item.get("newProviderCalls")!=0
        or item.get("publicationAuthorized") is not False):
        raise ValueError("BSA277_SOURCE_NEWTON_WITNESS_INVALID")
    if item.get("witnessSha256")!=_digest({
            k:v for k,v in item.items() if k!="witnessSha256"}):
        raise ValueError("BSA277_NEWTON_RECEIPT_DIGEST_CHANGED")
    if (item.get("exactRationalNewtonModels")!=_countermodels()
        or item.get("dimensionProof")!=_dimensions()):
        raise ValueError("BSA277_EXACT_INDEPENDENT_MOMENTUM_RATE_RECHECK_FAILED")


def independently_prove_newton_false_option(
    *,source_pdf:Path,candidate_path:Path,option_id:str
)->dict[str,Any]:
    if option_id not in _OPTIONS:
        raise ValueError("BSA277_UNREGISTERED_FALSE_OPTION")
    if (source_pdf.is_symlink() or not source_pdf.is_file()
        or candidate_path.is_symlink() or not candidate_path.is_file()
        or sha256(source_pdf.read_bytes()).hexdigest()!=_SOURCE_SHA
        or sha256(candidate_path.read_bytes()).hexdigest()!=_CANDIDATE_SHA):
        raise ValueError("BSA277_ORIGINAL_ONE_TEXTBOOK_AND_CANDIDATE_REQUIRED")
    axioms=_source_axioms(source_pdf,_SOURCE_SHA)
    if (axioms.get("time rate of change of the linear momentum",0)<1
        or axioms.get("defined to be the product of the mass and velocity",0)<1
        or axioms.get("linear momentum is a vector",0)<1):
        raise ValueError("BSA277_MISSING_ORIGINAL_NEWTON_MOMENTUM_RATE_SOURCE")
    data=json.loads(candidate_path.read_text(encoding="utf8"))
    acts=data.get("activities")
    if (not isinstance(acts,list) or len(acts)!=18
        or acts[2].get("id")!=_ACTIVITY or acts[2].get("type")!="mcq"):
        raise ValueError("BSA277_FROZEN_NEWTON_ACTIVITY_CHANGED")
    act=acts[2]
    answer=act.get("answerKey",{})
    opts=answer.get("options",[])
    if (answer.get("correct")!="opt-a" or len(opts)!=4
        or [o.get("id") for o in opts]!=["opt-a","opt-b","opt-c","opt-d"]):
        raise ValueError("BSA277_NEWTON_CORRECT_ANSWER_CHANGED")
    option=next(o for o in opts if o["id"]==option_id)
    localized={}
    for lang in ("en","ms","zh"):
        _parse_complete(act["prompt"].get(lang),(_PROMPT[lang],),
                        "BSA277_NEWTON_PREMISE_"+lang.upper())
        localized[lang]=_parse_complete(
            option["label"].get(lang),(_OPTIONS[option_id][lang],),
            "BSA277_NEWTON_FALSE_"+option_id.upper()+"_"+lang.upper())
    pages=extract_pages(source_pdf)
    anchor=_source_activity_anchors(pages=pages,activities=acts)[2]
    if (anchor.get("activityId")!=_ACTIVITY
        or anchor.get("uniquePagePassageLocated") is not True
        or anchor.get("physicalPage") not in (1,2,3)):
        raise ValueError("BSA277_SOURCE_NEWTON_PASSAGE_NOT_LOCATED")
    tasks=plan_full_semantic_proofs(package=data,source_sha256=_SOURCE_SHA)
    i=next(i for i,o in enumerate(opts) if o["id"]==option_id)
    path=f"answerKey/options/{i}/label"
    match=[t for t in tasks["tasks"] if t["kind"]==_KIND
           and t["activityId"]==_ACTIVITY and t["surfacePath"]==path]
    if (tasks["taskCount"]!=429 or len(match)!=1
        or match[0]["surfaceSha256"]!=_digest(option["label"])):
        raise ValueError("BSA277_EXACT_SIGNED_NEWTON_TASK_NOT_REPRODUCED")
    body={
        "taskId":match[0]["taskId"],
        "taskKind":_KIND,
        "activityId":_ACTIVITY,
        "optionId":option_id,
        "surfacePath":path,
        "surfaceSha256":match[0]["surfaceSha256"],
        "sourceSha256":_SOURCE_SHA,
        "candidateSha256":_CANDIDATE_SHA,
        "sourcePageIndex":anchor["physicalPage"],
        "sourcePassageSha256":anchor["passageSha256"],
        "sourcePhysicsPremisesDigest":_digest(sorted(axioms.items())),
        "completeLocalizedFiniteGrammarDigests":localized,
        "proofFamily":"NEWTON_NET_FORCE_IS_RATE_OF_MOMENTUM",
        "counterexampleClass":_CLAIMS[option_id],
        "dimensionProof":_dimensions(),
        "exactRationalNewtonModels":_countermodels(),
        "independentScienceWitnessVerified":True,
        "academicTaskAccepted":False,
        "completeAcademicProofGatesStillOpen":90,
        "otherScientificOrTrilingualGatesAccepted":False,
        "newProviderCalls":0,
        "publicationAuthorized":False,
    }
    item={**body,"witnessSha256":_digest(body)}
    independently_verify_newton_force_witness(item)
    return item

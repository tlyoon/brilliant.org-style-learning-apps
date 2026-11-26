"""BSA276: three independently checkable original-source SI-unit distractors.

For one original Serway 9.1 question, distinguish vector momentum p=m*v
from scalar magnitude, energy and inverse-velocity units. The exact
EN/MS/ZH learner statements must each fully parse. Mathematical countermodels
are exact Fractions and independent dimensional algebra, NEVER the saved key.
Each option becomes a distinct signed V36 MCQ science task; no translation,
diagram, other explanation or full activity gate is implicitly accepted.
"""
from __future__ import annotations

from fractions import Fraction as F
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

from app_generator.validation.section91_first_distractor_proof import _parse_complete
from app_generator.validation.section91_formal_physics import (
    _SOURCE_SHA, _CANDIDATE_SHA, _source_axioms, _digest,
)
from app_generator.validation.full_semantic_proof_queue import plan_full_semantic_proofs
from app_generator.validation.source_passages import extract_pages
from app_generator.runtime.v3_selected_textbook_scientific_provenance import (
    _source_activity_anchors,
)

_ACTIVITY="act-mcq-02-si-units"
_OPTIONS={
    "opt-b":{
        "en":"Unit of kg · m/s, dimensions ML/T, but fully specified by magnitude alone because momentum is a scalar quantity.",
        "ms":"Unit kg · m/s, dimensi ML/T, tetapi ditentukan sepenuhnya oleh magnitud sahaja kerana momentum ialah kuantiti skalar.",
        "zh":"单位为 kg · m/s，量纲为 ML/T，但仅凭大小即可完全确定，因为动量是标量。",
    },
    "opt-c":{
        "en":"Unit of kg · m^2/s^2, dimensions ML^2/T^2, and characterized purely as a scalar quantity without direction because it represents energy.",
        "ms":"Unit kg · m^2/s^2, dimensi ML^2/T^2, dan dicirikan semata-mata sebagai kuantiti skalar tanpa arah kerana ia mewakili tenaga.",
        "zh":"单位为 kg · m^2/s^2，量纲为 ML^2/T^2，且纯粹表现为没有方向的标量，因为它是能量。",
    },
    "opt-d":{
        "en":"Unit of kg · s/m, dimensions MT/L, and pointing perpendicular to the trajectory at all times.",
        "ms":"Unit kg · s/m, dimensi MT/L, dan menghala berserenjang dengan trajektori pada setiap masa.",
        "zh":"单位为 kg · s/m，量纲为 MT/L，且始终垂直于运动轨迹。",
    },
}
_PROMPT={
    "en":"A laboratory measurement ledger records the physical properties of a moving particle's linear momentum. Which entry correctly states the SI unit, dimensions, and directional property of linear momentum?",
    "ms":"Buku lejar pengukuran makmal merekodkan sifat fizikal momentum linear bagi suatu zarah yang bergerak. Catatan manakah yang menyatakan unit SI, dimensi, dan sifat berarah momentum linear dengan betul?",
    "zh":"一份实验室测量记录本记录了运动粒子的线动量物理特性。下列哪一项正确陈述了线动量的国际单位制（SI）单位、量纲及方向属性？",
}
_DIM_P=(1,1,-1)
_DIM_ENERGY=(1,2,-2)
_DIM_INV_V=(1,-1,1)
_KIND="MCQ_DISTRACTOR_SCIENCE"


def _exact_vector_models()->list[dict[str,Any]]:
    witnesses=[]
    for m,s in ((F(3,2),F(5,3)),(F(7,4),F(9,2))):
        # Three independent directional vectors of the same |p| and one
        # kinetic energy; no use of marked answers.
        pv=(m*s, F(0),F(0))
        opposite=(-m*s,F(0),F(0))
        ke=m*s*s/F(2)
        if (m<=0 or s<=0 or pv[0]==0 or pv==opposite
            or abs(pv[0])!=abs(opposite[0]) or ke<=0
            or sum(x*y for x,y in zip(pv,(s,F(0),F(0))))<=0):
            raise ValueError("BSA276_RATIONAL_DIRECTIONAL_WITNESS_WRONG")
        witnesses.append({
            "mass":str(m),"speed":str(s),
            "momentumForward":str(pv[0]),
            "momentumBackward":str(opposite[0]),
            "kineticEnergy":str(ke),
            "magnitudeAloneSpecifiesMomentum":False,
            "pParallelToPositiveVelocity":True,
            "pPerpendicularToVelocity":False,
        })
    return witnesses


def _dimensional_witness()->dict[str,Any]:
    add=lambda a,b: tuple(x+y for x,y in zip(a,b))
    mass=(1,0,0)
    velocity=(0,1,-1)
    momentum=add(mass,velocity)
    energy=add(mass,(0,2,-2))
    inverse_velocity=add(mass,(0,-1,1))
    if (momentum!=_DIM_P or energy!=_DIM_ENERGY
        or inverse_velocity!=_DIM_INV_V or
        len({momentum,energy,inverse_velocity})!=3):
        raise ValueError("BSA276_DIMENSIONS_NOT_DERIVED_FROM_MV")
    return {
        "baseOrder":["mass","length","time"],
        "mass":list(mass),"velocity":list(velocity),
        "momentum":list(momentum),"energy":list(energy),
        "massDividedByVelocity":list(inverse_velocity),
        "siUnitMomentum":"kg*m/s",
        "siUnitEnergy":"kg*m^2/s^2",
        "siUnitMassDividedByVelocity":"kg*s/m",
    }


def independently_verify_si_option_witness(proof:dict[str,Any])->None:
    if (not isinstance(proof,dict) or proof.get("optionId") not in _OPTIONS
        or proof.get("proofFamily")!="SI_DIMENSION_AND_VECTOR_MOMENTUM"
        or proof.get("sourceSha256")!=_SOURCE_SHA
        or proof.get("candidateSha256")!=_CANDIDATE_SHA
        or proof.get("independentScienceWitnessVerified") is not True
        or proof.get("academicTaskAccepted") is not False
        or proof.get("completeAcademicProofGatesStillOpen")!=90
        or proof.get("newProviderCalls")!=0
        or proof.get("publicationAuthorized") is not False):
        raise ValueError("BSA276_SIGNED_SCIENCE_WITNESS_NOT_RECHECKABLE")
    signature=proof.get("witnessSha256")
    body={k:v for k,v in proof.items() if k!="witnessSha256"}
    if signature!=_digest(body):
        raise ValueError("BSA276_SCIENCE_WITNESS_DIGEST_CHANGED")
    if proof.get("dimensionalWitness")!=_dimensional_witness():
        raise ValueError("BSA276_DIMENSIONAL_ALGEBRA_NOT_REDERIVED")
    expected=_exact_vector_models()
    if proof.get("rationalVectorModels")!=expected:
        raise ValueError("BSA276_RATIONAL_VECTOR_ALGEBRA_NOT_REDERIVED")
    options={
        "opt-b":"MOMENTUM_IS_NOT_SCALAR_MAGNITUDE_ALONE",
        "opt-c":"ENERGY_DIMENSIONS_DIFFER_FROM_MOMENTUM",
        "opt-d":"INVERSE_VELOCITY_DIMENSIONS_AND_PERPENDICULARITY_FALSE",
    }
    if proof.get("counterexampleClass")!=options[proof["optionId"]]:
        raise ValueError("BSA276_WRONG_OPTION_SCIENCE_FAMILY")


def independently_prove_si_unit_false_option(
    *,source_pdf:Path,candidate_path:Path,option_id:str
)->dict[str,Any]:
    if option_id not in _OPTIONS:
        raise ValueError("BSA276_UNREGISTERED_OR_CORRECT_OPTION_REJECTED")
    if (source_pdf.is_symlink() or not source_pdf.is_file()
        or candidate_path.is_symlink() or not candidate_path.is_file()
        or sha256(source_pdf.read_bytes()).hexdigest()!=_SOURCE_SHA
        or sha256(candidate_path.read_bytes()).hexdigest()!=_CANDIDATE_SHA):
        raise ValueError("BSA276_ORIGINAL_SERWAY_AND_FROZEN_CANDIDATE_REQUIRED")
    axioms=_source_axioms(source_pdf,_SOURCE_SHA)
    if (axioms.get("defined to be the product of the mass and velocity",0)<1
        or axioms.get("linear momentum is a vector",0)<1
        or axioms.get("dimensions ml/t",0)<1):
        raise ValueError("BSA276_ORIGINAL_TEXTBOOK_SI_VECTOR_AXIOMS_REQUIRED")
    candidate=json.loads(candidate_path.read_text(encoding="utf8"))
    acts=candidate.get("activities",[])
    if (len(acts)!=18 or acts[1].get("id")!=_ACTIVITY or
        acts[1].get("type")!="mcq"):
        raise ValueError("BSA276_FROZEN_MC_Q_ACTIVITY_CHANGED")
    answer=acts[1].get("answerKey",{})
    options=answer.get("options",[])
    if (answer.get("correct")!="opt-a" or len(options)!=4
        or [o["id"] for o in options]!=["opt-a","opt-b","opt-c","opt-d"]):
        raise ValueError("BSA276_CHANGED_OR_FORGED_ANSWER_KEY")
    exact=next(o for o in options if o["id"]==option_id)
    localized={}
    for language in ("en","ms","zh"):
        _parse_complete(acts[1]["prompt"].get(language),
                        (_PROMPT[language],),
                        "BSA276_PROMPT_"+language.upper())
        localized[language]=_parse_complete(
            exact.get("label",{}).get(language),
            (_OPTIONS[option_id][language],),
            "BSA276_OPTION_"+option_id.upper()+"_"+language.upper())
    pages=extract_pages(source_pdf)
    anchor=_source_activity_anchors(pages=pages,activities=acts)[1]
    if (anchor.get("activityId")!=_ACTIVITY
        or anchor.get("uniquePagePassageLocated") is not True
        or anchor.get("physicalPage") not in (1,2,3)):
        raise ValueError("BSA276_ORIGINAL_MC_Q_SOURCE_ANCHOR_MISSING")
    planned=plan_full_semantic_proofs(
        package=candidate,source_sha256=_SOURCE_SHA)
    position=next(i for i,o in enumerate(options) if o["id"]==option_id)
    path=f"answerKey/options/{position}/label"
    found=[t for t in planned["tasks"] if
           t["kind"]==_KIND and t["activityId"]==_ACTIVITY and
           t["surfacePath"]==path]
    if (planned["taskCount"]!=429 or len(found)!=1 or
        found[0]["surfaceSha256"]!=_digest(exact["label"])):
        raise ValueError("BSA276_ORIGINAL_SIGNED_TASK_NOT_REDERIVED")
    kinds={
        "opt-b":"MOMENTUM_IS_NOT_SCALAR_MAGNITUDE_ALONE",
        "opt-c":"ENERGY_DIMENSIONS_DIFFER_FROM_MOMENTUM",
        "opt-d":"INVERSE_VELOCITY_DIMENSIONS_AND_PERPENDICULARITY_FALSE",
    }
    body={
        "taskId":found[0]["taskId"],
        "taskKind":_KIND,
        "activityId":_ACTIVITY,
        "optionId":option_id,
        "surfacePath":path,
        "surfaceSha256":found[0]["surfaceSha256"],
        "sourceSha256":_SOURCE_SHA,
        "candidateSha256":_CANDIDATE_SHA,
        "sourcePageIndex":anchor["physicalPage"],
        "sourcePassageSha256":anchor["passageSha256"],
        "sourcePhysicsPremisesDigest":_digest(sorted(axioms.items())),
        "completeLocalizedFiniteGrammarDigests":localized,
        "proofFamily":"SI_DIMENSION_AND_VECTOR_MOMENTUM",
        "counterexampleClass":kinds[option_id],
        "dimensionalWitness":_dimensional_witness(),
        "rationalVectorModels":_exact_vector_models(),
        "independentScienceWitnessVerified":True,
        "academicTaskAccepted":False,
        "completeAcademicProofGatesStillOpen":90,
        "otherMultilingualProofsAccepted":False,
        "newProviderCalls":0,
        "publicationAuthorized":False,
    }
    result={**body,"witnessSha256":_digest(body)}
    independently_verify_si_option_witness(result)
    return result

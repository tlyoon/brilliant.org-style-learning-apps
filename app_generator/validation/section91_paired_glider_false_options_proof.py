"""BSA278: original Serway paired glider momentum vs kinetic-energy MCQ proofs.

Three distinct false alternatives of one frozen trilingual learner activity
are independently disproven by exact rational kinetic energy and signed
one-dimensional vector momentum. No source-free evidence, marked answer, or
model output substitutes for physical proof. No new academic acceptance here.
"""
from __future__ import annotations

from fractions import Fraction
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

_ACTIVITY="act-mcq-04-two-particle-opposite-momentum"
_KIND="MCQ_DISTRACTOR_SCIENCE"
_PROMPT={
    "en":"Two identical gliders on a horizontal frictionless air track move directly toward each other with the same constant speed. How do the total linear momentum and the total kinetic energy of this two-glider system compare?",
    "ms":"Dua peluncur serupa di atas trek udara mendatar tanpa geseran bergerak terus ke arah satu sama lain dengan laju malar yang sama. Bagaimanakah perbandingan antara jumlah momentum linear dan jumlah tenaga kinetik bagi sistem dua peluncur ini?",
    "zh":"在水平无摩擦气垫导轨上，两个完全相同的滑块以相同的恒定速率迎面相向运动。关于该双滑块系统的总线动量与总动能，下列哪项说法是正确的？",
}
_OPTIONS={
    "opt-b":{
        "en":"Both the total linear momentum and the total kinetic energy are positive and non-zero, because moving objects always contribute positive momentum regardless of direction.",
        "ms":"Kedua-dua jumlah momentum linear dan jumlah tenaga kinetik adalah positif dan bukan sifar, kerana objek yang bergerak sentiasa menyumbang momentum positif tanpa mengira arah.",
        "zh":"总线动量和总动能均为正且非零，因为运动的物体无论运动方向如何总是贡献正动量。",
    },
    "opt-c":{
        "en":"Both the total linear momentum and the total kinetic energy are zero, because equal kinetic energies cancel out when moving in opposite directions.",
        "ms":"Kedua-dua jumlah momentum linear dan jumlah tenaga kinetik adalah sifar, kerana tenaga kinetik yang sama saling membatalkan apabila bergerak dalam arah bertentangan.",
        "zh":"总线动量和总动能均为零，因为在相反方向运动时，相等的动能会相互抵消。",
    },
    "opt-d":{
        "en":"The total linear momentum is positive, while the total kinetic energy is zero because opposite velocities negate kinetic energy.",
        "ms":"Jumlah momentum linear adalah positif, manakala jumlah tenaga kinetik adalah sifar kerana halaju bertentangan meniadakan tenaga kinetik.",
        "zh":"总线动量为正，而总动能为零，因为相反的速度抵消了动能。",
    },
}
_FALSE_CLASSES={
    "opt-b":"OPPOSITE_VECTOR_MOMENTA_SUM_ZERO_NOT_POSITIVE",
    "opt-c":"SCALAR_KINETIC_ENERGIES_ADD_NOT_CANCEL",
    "opt-d":"OPPOSITE_VELOCITIES_CANNOT_CANCEL_SQUARED_KINETIC_ENERGY",
}


def _models()->list[dict[str,Any]]:
    results=[]
    for mass,speed in (
        (Fraction(3,2),Fraction(7,3)),
        (Fraction(11,4),Fraction(5,2)),
    ):
        if mass<=0 or speed<=0:
            raise ValueError("BSA278_NONZERO_GLIDER_MASS_SPEED_REQUIRED")
        forward,backward=mass*speed,-mass*speed
        kin=mass*speed*speed/2
        net_p=forward+backward
        total_kin=kin+kin
        if (forward<=0 or backward>=0 or kin<=0
            or net_p!=0 or total_kin<=0
            or total_kin!=mass*speed*speed):
            raise ValueError("BSA278_EXACT_PAIRED_VECTOR_ENERGY_MODEL_FAILED")
        results.append({
            "massEach":str(mass),
            "speedMagnitudeEach":str(speed),
            "momentumForward":str(forward),
            "momentumBackward":str(backward),
            "systemVectorMomentum":str(net_p),
            "kineticEnergyPerGlider":str(kin),
            "systemScalarKineticEnergy":str(total_kin),
            "gliderMomentaCancelExactly":True,
            "gliderKineticEnergiesCancel":False,
            "systemKineticEnergyPositive":True,
        })
    return results


def independently_check_paired_glider_witness(proof:dict[str,Any])->None:
    if (not isinstance(proof,dict)
        or proof.get("optionId") not in _OPTIONS
        or proof.get("falseScientificAssertion")!=_FALSE_CLASSES[
            proof.get("optionId")]
        or proof.get("proofFamily")!=
            "PAIRED_OPPOSITE_VECTOR_MOMENTA_SCALAR_KINETIC_ENERGY"
        or proof.get("sourceSha256")!=_SOURCE_SHA
        or proof.get("candidateSha256")!=_CANDIDATE_SHA
        or proof.get("academicTaskAccepted") is not False
        or proof.get("independentScienceWitnessVerified") is not True
        or proof.get("newProviderCalls")!=0
        or proof.get("publicationAuthorized") is not False
        or proof.get("completeAcademicProofGatesStillOpen")!=90):
        raise ValueError("BSA278_UNTRUSTED_SOURCE_BOUND_GLIDER_WITNESS")
    if proof.get("witnessSha256")!=_digest({
        k:v for k,v in proof.items() if k!="witnessSha256"}):
        raise ValueError("BSA278_GLIDER_WITNESS_DIGEST_INVALID")
    if proof.get("exactRationalSystemModels")!=_models():
        raise ValueError("BSA278_RATIONAL_GLIDER_P_AND_KE_RECHECK_FAILED")
    for case in proof["exactRationalSystemModels"]:
        try:
            m=Fraction(case["massEach"])
            v=Fraction(case["speedMagnitudeEach"])
            p0=Fraction(case["momentumForward"])
            p1=Fraction(case["momentumBackward"])
            k0=Fraction(case["kineticEnergyPerGlider"])
            net=Fraction(case["systemVectorMomentum"])
            ktotal=Fraction(case["systemScalarKineticEnergy"])
        except (TypeError,ValueError,ZeroDivisionError) as e:
            raise ValueError("BSA278_SOURCE_RATIONAL_GLIDER_WITNESS_NOT_REPARSEABLE") from e
        if (m<=0 or v<=0 or p0!=m*v or p1!=-m*v or
            net!=p0+p1 or net!=0 or
            k0!=m*v*v/2 or ktotal!=2*k0 or ktotal<=0):
            raise ValueError("BSA278_ORIGINAL_VECTOR_ENERGY_PHYSICS_FAILED")


def independently_prove_paired_glider_false_option(
    *,source_pdf:Path,candidate_path:Path,option_id:str
)->dict[str,Any]:
    if option_id not in _OPTIONS:
        raise ValueError("BSA278_NOT_A_REGISTERED_FALSE_OPTION")
    if (source_pdf.is_symlink() or not source_pdf.is_file()
        or candidate_path.is_symlink() or not candidate_path.is_file()
        or sha256(source_pdf.read_bytes()).hexdigest()!=_SOURCE_SHA
        or sha256(candidate_path.read_bytes()).hexdigest()!=_CANDIDATE_SHA):
        raise ValueError("BSA278_ORIGINAL_ONE_SERWAY_PDF_AND_CANDIDATE_REQUIRED")
    axioms=_source_axioms(source_pdf,_SOURCE_SHA)
    if (axioms.get("defined to be the product of the mass and velocity",0)<1
        or axioms.get("linear momentum is a vector",0)<1
        or axioms.get("kinetic energy can transform",0)<1):
        raise ValueError("BSA278_SOURCE_VECTOR_AND_KINETIC_ENERGY_MISSING")
    package=json.loads(candidate_path.read_text(encoding="utf8"))
    acts=package.get("activities",[])
    if (not isinstance(acts,list) or len(acts)!=18
        or acts[3].get("id")!=_ACTIVITY
        or acts[3].get("type")!="mcq"):
        raise ValueError("BSA278_ORIGINAL_18_ACTIVITY_ROSTER_CHANGED")
    activity=acts[3]
    key=activity.get("answerKey",{})
    options=key.get("options",[])
    if (key.get("correct")!="opt-a" or len(options)!=4
        or [opt.get("id") for opt in options]!=
        ["opt-a","opt-b","opt-c","opt-d"]):
        raise ValueError("BSA278_ORIGINAL_MCQ04_ANSWER_KEY_CHANGED")
    exact=next(o for o in options if o["id"]==option_id)
    locales={}
    for lang in ("en","ms","zh"):
        _parse_complete(activity["prompt"].get(lang),(_PROMPT[lang],),
                        "BSA278_GLIDER_PREMISE_"+lang.upper())
        locales[lang]=_parse_complete(
            exact.get("label",{}).get(lang),
            (_OPTIONS[option_id][lang],),
            "BSA278_GLIDER_OPTION_"+option_id.upper()+"_"+lang.upper())
    pages=extract_pages(source_pdf)
    source_anchor=_source_activity_anchors(
        pages=pages,activities=acts)[3]
    if (source_anchor.get("activityId")!=_ACTIVITY
        or source_anchor.get("uniquePagePassageLocated") is not True
        or source_anchor.get("physicalPage") not in (1,2,3)):
        raise ValueError("BSA278_ORIGINAL_SOURCE_PASSAGE_NOT_VERIFIED")
    queue=plan_full_semantic_proofs(
        package=package,source_sha256=_SOURCE_SHA)
    position=next(j for j,o in enumerate(options) if o["id"]==option_id)
    surface_path=f"answerKey/options/{position}/label"
    matches=[task for task in queue["tasks"]
             if task["kind"]==_KIND
             and task["activityId"]==_ACTIVITY
             and task["surfacePath"]==surface_path]
    if (queue["taskCount"]!=429 or len(matches)!=1
        or matches[0]["surfaceSha256"]!=_digest(exact["label"])):
        raise ValueError("BSA278_SIGNED_FALSE_GLIDER_TASK_NOT_DERIVED")
    body={
        "taskId":matches[0]["taskId"],
        "taskKind":_KIND,
        "activityId":_ACTIVITY,
        "optionId":option_id,
        "surfacePath":surface_path,
        "surfaceSha256":matches[0]["surfaceSha256"],
        "sourceSha256":_SOURCE_SHA,
        "candidateSha256":_CANDIDATE_SHA,
        "sourcePageIndex":source_anchor["physicalPage"],
        "sourcePassageSha256":source_anchor["passageSha256"],
        "sourcePhysicsPremisesDigest":_digest(sorted(axioms.items())),
        "completeLocalizedFiniteGrammarDigests":locales,
        "proofFamily":"PAIRED_OPPOSITE_VECTOR_MOMENTA_SCALAR_KINETIC_ENERGY",
        "falseScientificAssertion":_FALSE_CLASSES[option_id],
        "exactRationalSystemModels":_models(),
        "independentScienceWitnessVerified":True,
        "academicTaskAccepted":False,
        "completeAcademicProofGatesStillOpen":90,
        "newProviderCalls":0,
        "publicationAuthorized":False,
    }
    result={**body,"witnessSha256":_digest(body)}
    independently_check_paired_glider_witness(result)
    return result

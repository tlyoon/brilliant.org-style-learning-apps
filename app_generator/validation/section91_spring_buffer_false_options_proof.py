"""Original-source MCQ09 false-option countermodels for a spring buffer.

Exact energy and impulse balances are independently recomputed at readback.
The witness alone never admits an academic task.
"""
from __future__ import annotations

from fractions import Fraction as F
from hashlib import sha256
import json
from pathlib import Path

from app_generator.validation.section91_formal_physics import _SOURCE_SHA, _CANDIDATE_SHA, _source_axioms, _digest
from app_generator.validation.full_semantic_proof_queue import plan_full_semantic_proofs
from app_generator.validation.source_passages import extract_pages
from app_generator.runtime.v3_selected_textbook_scientific_provenance import _source_activity_anchors

_ACTIVITY = "act-mcq-09-no-momentum-conversion"
# BSA308: BSA253 hashes the whole candidate into each task ID. The tracked
# sample cannot supply canonical IDs for the SHA-pinned private owner roster.
_OPTIONS_ORDER = (
    "opt-potential-momentum-stored", "opt-both-turn-to-heat",
    "opt-momentum-conserved-internally",
)
_PROMPT = {"en":"7724e203aa4e2fa6c4cf9323cdc1582f2d483ffc2722c5c0bbf89e1e6d8dfe43", "ms":"bf4f734d13473b16d69c7bfaf95d91d0511eb755e788cee7e0a9345b4b54e90c", "zh":"4b42ff07b233f8524673c8f3a3f3b143081f2cdfef1cb11b833418aae5c5c692"}
_OPTIONS = {
    "opt-potential-momentum-stored": {"en":"98de4f974840f6bcadf0fa5771fc3f45c879588ecce2825d2a9e9210881418a9", "ms":"0bf82b2ec9ce1b7a33eede5d7f32bee39250a04ddac4e02e617e532482a85f61", "zh":"22cded7f29a52cbcdd89e1db5be4be04a6ccd8709da8f4ecd4bac5ff193a9010"},
    "opt-both-turn-to-heat": {"en":"e0223f72aa394f91edfce17b4c023caa78fd18783d8cc6c5087425fc5bb1962d", "ms":"3bc628908ced59b840e5877f9b97a7a9ec14af946bbf0ad2b02168566d0ec079", "zh":"eb578d01fde0cc00711276b68e1eaa0330f9c47e92634a8ffdd85c3f9f859ebd"},
    "opt-momentum-conserved-internally": {"en":"12b157b434a3b77106377ab261a0cd8bb4ec623ae8b7cb4861319b9b90b862c6", "ms":"a3c84b610493e637de26a8b10ebb15de080244bae4443f59065f09d241d372fa", "zh":"e39cfa75a44d22f1a3433b9fc612fd922c9dfdb494d60fd5f41164cb261cb505"},
}
_CLAIMS = {
    "opt-potential-momentum-stored": "SPRING_STORES_POTENTIAL_MOMENTUM",
    "opt-both-turn-to-heat": "KINETIC_ENERGY_AND_MOMENTUM_BOTH_BECOME_HEAT",
    "opt-momentum-conserved-internally": "POD_MOMENTUM_CONSERVED_AS_SCALAR_AND_ENERGY_DESTROYED",
}
_CASES = ((F(3), F(2), F(2)), (F(5,2), F(4,3), F(7,3)))


def _locales(value:dict, expected:dict)->dict:
    if not isinstance(value,dict) or set(value)!={"en","ms","zh"} or any(
        not isinstance(v,str) or not v.strip() for v in value.values()
    ):
        raise ValueError("BSA291_COMPLETE_TRILINGUAL_SENTENCE_REQUIRED")
    actual={lang:sha256(value[lang].encode("utf8")).hexdigest() for lang in ("en","ms","zh")}
    if actual!=expected:
        raise ValueError("BSA291_FROZEN_TRILINGUAL_PROPOSITION_CHANGED")
    return actual


def _model(mass:F, speed:F, contact_time:F)->dict:
    if not all(isinstance(x,F) and x>0 for x in (mass,speed,contact_time)):
        raise ValueError("BSA291_POSITIVE_EXACT_RATIONAL_MODEL_REQUIRED")
    initial_p=mass*speed
    initial_k=mass*speed*speed/2
    final_p=F(0)
    spring_energy=initial_k
    rail_impulse=initial_p-final_p
    rail_force=rail_impulse/contact_time
    thermal_energy=F(0)
    if not (initial_p>0 and initial_k>0 and spring_energy==initial_k
            and rail_impulse>0 and rail_force*contact_time==rail_impulse
            and final_p+rail_impulse==initial_p and thermal_energy==0
            and (1,1,-1)!=(1,2,-2)):
        raise ValueError("BSA291_SPRING_ENERGY_IMPULSE_NOT_DERIVED")
    return {"mass":str(mass),"initialSpeed":str(speed),"contactTime":str(contact_time),
            "initialMomentum":str(initial_p),"finalPodMomentum":str(final_p),
            "initialKineticEnergy":str(initial_k),"springPotentialEnergy":str(spring_energy),
            "railImpulse":str(rail_impulse),"averageRailForce":str(rail_force),
            "thermalEnergy":str(thermal_energy),"momentumDimension":"M L T^-1",
            "energyDimension":"M L^2 T^-2"}


def _models()->list[dict]:
    return [_model(*case) for case in _CASES]


def independently_check_spring_buffer_witness(proof:dict)->None:
    option=proof.get("optionId") if isinstance(proof,dict) else None
    task_id=proof.get("taskId") if isinstance(proof,dict) else None
    if option not in _OPTIONS_ORDER or (not isinstance(task_id,str) or len(task_id)!=64
        or any(c not in "0123456789abcdef" for c in task_id)
        or proof.get("falseClaim")!=_CLAIMS[option]
        or proof.get("sourceSha256")!=_SOURCE_SHA
        or proof.get("candidateSha256")!=_CANDIDATE_SHA
        or proof.get("promptLocaleSha256")!=_PROMPT
        or proof.get("optionLocaleSha256")!=_OPTIONS[option]
        or proof.get("models")!=_models()
        or type(proof.get("sourcePageIndex")) is not int or proof["sourcePageIndex"]<1
        or any(not isinstance(proof.get(k),str) or len(proof[k])!=64 for k in
               ("surfaceSha256","sourcePassageSha256","sourcePhysicsPremisesSha256"))
        or proof.get("academicTaskAccepted") is not False
        or proof.get("completeAcademicProofGatesStillOpen")!=90
        or proof.get("publicationAuthorized") is not False
        or proof.get("newProviderCalls")!=0
        or proof.get("witnessSha256")!=_digest({k:v for k,v in proof.items() if k!="witnessSha256"})):
        raise ValueError("BSA291_UNTRUSTED_SPRING_BUFFER_WITNESS")
    for row in proof["models"]:
        if row!=_model(*(F(row[k]) for k in ("mass","initialSpeed","contactTime"))):
            raise ValueError("BSA291_EXACT_RATIONAL_RECOMPUTATION_FAILED")


def independently_prove_spring_buffer_false_option(*,source_pdf:Path,candidate_path:Path,option_id:str)->dict:
    if option_id not in _OPTIONS_ORDER:
        raise ValueError("BSA291_UNREGISTERED_SPRING_BUFFER_OPTION")
    candidate_bytes=candidate_path.read_bytes() if candidate_path.is_file() and not candidate_path.is_symlink() else b""
    if (source_pdf.is_symlink() or candidate_path.is_symlink() or not source_pdf.is_file()
        or not candidate_bytes or sha256(source_pdf.read_bytes()).hexdigest()!=_SOURCE_SHA
        or sha256(candidate_bytes).hexdigest()!=_CANDIDATE_SHA):
        raise ValueError("BSA291_AUTHENTIC_ONE_SERWAY_SOURCE_AND_CANDIDATE_REQUIRED")
    axioms=_source_axioms(source_pdf,_SOURCE_SHA)
    if (axioms.get("kinetic energy can transform",0)<1
        or axioms.get("only one type of linear momentum",0)<1
        or axioms.get("isolated system",0)<3
        or axioms.get("defined to be the product of the mass and velocity",0)<1):
        raise ValueError("BSA291_ORIGINAL_SPRING_MOMENTUM_PREMISES_MISSING")
    package=json.loads(candidate_bytes.decode("utf8"))
    activities=package.get("activities")
    if not isinstance(activities,list) or len(activities)!=18 or activities[8].get("id")!=_ACTIVITY:
        raise ValueError("BSA291_FROZEN_MCQ09_ACTIVITY_CHANGED")
    activity=activities[8]
    prompt=_locales(activity.get("prompt"),_PROMPT)
    key=activity.get("answerKey",{})
    options=key.get("options",[])
    expected=["opt-ke-transforms-momentum-transfers",*_OPTIONS_ORDER]
    if key.get("correct")!=expected[0] or [x.get("id") for x in options]!=expected:
        raise ValueError("BSA291_FROZEN_MCQ09_ANSWER_KEY_CHANGED")
    position=expected.index(option_id)
    locale=_locales(options[position].get("label"),_OPTIONS[option_id])
    anchors=_source_activity_anchors(pages=extract_pages(source_pdf),activities=activities)
    if sha256(source_pdf.read_bytes()).hexdigest()!=_SOURCE_SHA:
        raise ValueError("BSA291_SOURCE_CHANGED_DURING_EXTRACTION")
    anchor=anchors[8]
    if anchor.get("activityId")!=_ACTIVITY or anchor.get("uniquePagePassageLocated") is not True:
        raise ValueError("BSA291_ORIGINAL_SOURCE_ANCHOR_MISSING")
    queue=plan_full_semantic_proofs(package=package,source_sha256=_SOURCE_SHA)
    tasks=[t for t in queue["tasks"] if t["activityId"]==_ACTIVITY and
           t["kind"]=="MCQ_DISTRACTOR_SCIENCE" and
           t["surfacePath"]==f"answerKey/options/{position}/label"]
    if (queue["taskCount"]!=429 or len(tasks)!=1
        or tasks[0]["surfaceSha256"]!=_digest(options[position]["label"])):
        raise ValueError("BSA291_CANONICAL_MCQ09_TASK_NOT_REDERIVED")
    body={"taskId":tasks[0]["taskId"],"optionId":option_id,"falseClaim":_CLAIMS[option_id],
          "sourceSha256":_SOURCE_SHA,"candidateSha256":_CANDIDATE_SHA,
          "surfaceSha256":tasks[0]["surfaceSha256"],
          "sourcePageIndex":anchor["physicalPage"],"sourcePassageSha256":anchor["passageSha256"],
          "sourcePhysicsPremisesSha256":_digest(sorted(axioms.items())),
          "promptLocaleSha256":prompt,"optionLocaleSha256":locale,"models":_models(),
          "academicTaskAccepted":False,"completeAcademicProofGatesStillOpen":90,
          "newProviderCalls":0,"publicationAuthorized":False}
    proof={**body,"witnessSha256":_digest(body)}
    independently_check_spring_buffer_witness(proof)
    return proof

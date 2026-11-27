"""MCQ08: source-bound countermodels for three isolated-pair fallacies.

The exact rational dynamics concern two people, while the false alternatives
misapply the isolated-system conservation law to one member of the pair.
The witness is deliberately separate from owner academic admission.
"""
from __future__ import annotations

from fractions import Fraction as F
from hashlib import sha256
import json
from pathlib import Path

from app_generator.validation.section91_formal_physics import (
    _SOURCE_SHA, _CANDIDATE_SHA, _source_axioms, _digest,
)
from app_generator.validation.full_semantic_proof_queue import plan_full_semantic_proofs
from app_generator.validation.source_passages import extract_pages
from app_generator.runtime.v3_selected_textbook_scientific_provenance import _source_activity_anchors

_ACTIVITY = "act-mcq-08-isolated-subsystem-fallacy"
_TASKS = {
    "opt-single-particle-conserved": "a65d34052e0033cd2cc6e7acd99918a30248c6df8ce5d191c2c1333aaa581e45",
    "opt-force-equals-momentum": "4b69fcc5fcfe0ed5e832fabafeb09effdc7a9b64564b695e5cb2d17d944c43c8",
    "opt-forces-cancel-on-body": "3d275501690934ce80226ba789c9d4b4f1ffd82b67d0e7768b26d70faf4ee669",
}
_PROMPT = {"en":"b3f7144c4d1c84c5fed4102458af50a75fd021705caf65a1ae53262deb50ec30", "ms":"cfdd4605fbde2b75b808d6df8e1e439ed6207f28f5e2a3e6b1ee69b534dc5807", "zh":"1cf5beeaec2bbbdbb667e685252dc45784a1d5f56433b5d441fefcbd2e4a73a4"}
_OPTIONS = {
    "opt-single-particle-conserved": {"en":"6e82bcf06747c9eafab61372a932de4ce4858187fef698b290ea70eeb3262622", "ms":"5bc04e850c61d65b06686b8fe46bd9a64cb71cb1984cc6bdeb25ba135896d82b", "zh":"c221f09745a649c8fc073b69a02f82c7b2069da5db5010efd672bcbe6f328383"},
    "opt-force-equals-momentum": {"en":"40b9652ea6ea347f5a96cbb344e68c12a6071c33d8eb5bd4d7394a3aefd61917", "ms":"59b222fc9f92559b13f5cb1531b653cc9659a2d7ce680cdc9807df11d36c3f3b", "zh":"da49b46976014ed754d189bf7c71e3281ea70c8c2c607ab29f8d444345c43402"},
    "opt-forces-cancel-on-body": {"en":"3e8b5ac289e9f41c6a019fe939a0b43916d5b774ea58495d498091080ca0dc85", "ms":"fed9240e47e787908029c2d1421d1f2d0742943b2e4fab32db308839c7162dcd", "zh":"1666f2338a3cd1c06e8d439d0bc6b6d50af0029a8e47acac9b2880e40410e174"},
}
_CLAIMS = {
    "opt-single-particle-conserved":"ISOLATED_PAIR_IMPLIES_INDIVIDUAL_MOMENTUM_CONSTANT",
    "opt-force-equals-momentum":"CONTACT_FORCE_EQUALS_INSTANTANEOUS_MOMENTUM",
    "opt-forces-cancel-on-body":"THIRD_LAW_FORCES_CANCEL_ON_ONE_BODY",
}
_CASES = ((F(2), F(3), F(4), F(2)), (F(5,2), F(7,3), F(9,2), F(3,2)))


def _locales(value:dict, expected:dict)->dict:
    if not isinstance(value,dict) or set(value)!={"en","ms","zh"} or any(
        not isinstance(v,str) or not v.strip() for v in value.values()
    ):
        raise ValueError("BSA290_COMPLETE_TRILINGUAL_SENTENCE_REQUIRED")
    actual={lang:sha256(value[lang].encode("utf8")).hexdigest() for lang in ("en","ms","zh")}
    if actual!=expected:
        raise ValueError("BSA290_FROZEN_TRILINGUAL_PROPOSITION_CHANGED")
    return actual


def _model(nadia_mass:F, leo_mass:F, impulse:F, duration:F)->dict:
    if not all(isinstance(x,F) and x>0 for x in (nadia_mass,leo_mass,impulse,duration)):
        raise ValueError("BSA290_POSITIVE_EXACT_RATIONAL_MODEL_REQUIRED")
    # Nadia receives -J, Leo +J. The two forces act on different bodies.
    nadia_force=-impulse/duration
    leo_force=impulse/duration
    nadia_p=nadia_force*duration
    leo_p=leo_force*duration
    nadia_v=nadia_p/nadia_mass
    leo_v=leo_p/leo_mass
    nadia_a=nadia_force/nadia_mass
    leo_a=leo_force/leo_mass
    if not (nadia_force==-leo_force and nadia_force!=0 and
            nadia_p+leo_p==0 and nadia_p!=0 and
            nadia_p==nadia_mass*nadia_v and leo_p==leo_mass*leo_v and
            nadia_force==nadia_p/duration and nadia_force!=nadia_p and
            nadia_a!=0 and leo_a!=0 and
            nadia_force+leo_force==0):
        raise ValueError("BSA290_PAIR_DYNAMICS_NOT_DERIVED")
    return {"nadiaMass":str(nadia_mass),"leoMass":str(leo_mass),
            "impulseMagnitude":str(impulse),"duration":str(duration),
            "nadiaForce":str(nadia_force),"leoForce":str(leo_force),
            "nadiaMomentum":str(nadia_p),"leoMomentum":str(leo_p),
            "nadiaVelocity":str(nadia_v),"leoVelocity":str(leo_v),
            "nadiaAcceleration":str(nadia_a),"leoAcceleration":str(leo_a),
            "pairMomentum":"0","forcesActOnDifferentBodies":True,
            "forceDimension":"M L T^-2","momentumDimension":"M L T^-1"}


def _models()->list[dict]:
    return [_model(*case) for case in _CASES]


def independently_check_isolated_pair_witness(proof:dict)->None:
    option=proof.get("optionId") if isinstance(proof,dict) else None
    if option not in _TASKS or (proof.get("taskId")!=_TASKS[option]
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
        raise ValueError("BSA290_UNTRUSTED_ISOLATED_PAIR_WITNESS")
    for row in proof["models"]:
        args=(F(row[k]) for k in ("nadiaMass","leoMass","impulseMagnitude","duration"))
        if row!=_model(*args):
            raise ValueError("BSA290_EXACT_RATIONAL_RECOMPUTATION_FAILED")


def independently_prove_isolated_pair_false_option(*,source_pdf:Path,candidate_path:Path,option_id:str)->dict:
    if option_id not in _TASKS:
        raise ValueError("BSA290_UNREGISTERED_ISOLATED_PAIR_OPTION")
    candidate_bytes=candidate_path.read_bytes() if candidate_path.is_file() and not candidate_path.is_symlink() else b""
    if (source_pdf.is_symlink() or candidate_path.is_symlink() or not source_pdf.is_file()
        or not candidate_bytes or sha256(source_pdf.read_bytes()).hexdigest()!=_SOURCE_SHA
        or sha256(candidate_bytes).hexdigest()!=_CANDIDATE_SHA):
        raise ValueError("BSA290_AUTHENTIC_ONE_SERWAY_SOURCE_AND_CANDIDATE_REQUIRED")
    axioms=_source_axioms(source_pdf,_SOURCE_SHA)
    if (axioms.get("isolated system",0)<3 or axioms.get("third law",0)<1
        or axioms.get("time rate of change of the linear momentum",0)<1
        or axioms.get("defined to be the product of the mass and velocity",0)<1):
        raise ValueError("BSA290_ORIGINAL_PAIR_FORCE_PREMISES_MISSING")
    package=json.loads(candidate_bytes.decode("utf8"))
    activities=package.get("activities")
    if not isinstance(activities,list) or len(activities)!=18 or activities[7].get("id")!=_ACTIVITY:
        raise ValueError("BSA290_FROZEN_MCQ08_ACTIVITY_CHANGED")
    activity=activities[7]
    prompt=_locales(activity.get("prompt"),_PROMPT)
    key=activity.get("answerKey",{})
    options=key.get("options",[])
    expected=["opt-nadia-momentum-changes",*_TASKS]
    if key.get("correct")!=expected[0] or [x.get("id") for x in options]!=expected:
        raise ValueError("BSA290_FROZEN_MCQ08_ANSWER_KEY_CHANGED")
    position=expected.index(option_id)
    locale=_locales(options[position].get("label"),_OPTIONS[option_id])
    anchors=_source_activity_anchors(pages=extract_pages(source_pdf),activities=activities)
    anchor=anchors[7]
    if anchor.get("activityId")!=_ACTIVITY or anchor.get("uniquePagePassageLocated") is not True:
        raise ValueError("BSA290_ORIGINAL_SOURCE_ANCHOR_MISSING")
    queue=plan_full_semantic_proofs(package=package,source_sha256=_SOURCE_SHA)
    tasks=[t for t in queue["tasks"] if t["activityId"]==_ACTIVITY and
           t["kind"]=="MCQ_DISTRACTOR_SCIENCE" and
           t["surfacePath"]==f"answerKey/options/{position}/label"]
    if (queue["taskCount"]!=429 or len(tasks)!=1 or tasks[0]["taskId"]!=_TASKS[option_id]
        or tasks[0]["surfaceSha256"]!=_digest(options[position]["label"])):
        raise ValueError("BSA290_CANONICAL_MCQ08_TASK_NOT_REDERIVED")
    body={"taskId":tasks[0]["taskId"],"optionId":option_id,"falseClaim":_CLAIMS[option_id],
          "sourceSha256":_SOURCE_SHA,"candidateSha256":_CANDIDATE_SHA,
          "surfaceSha256":tasks[0]["surfaceSha256"],
          "sourcePageIndex":anchor["physicalPage"],"sourcePassageSha256":anchor["passageSha256"],
          "sourcePhysicsPremisesSha256":_digest(sorted(axioms.items())),
          "promptLocaleSha256":prompt,"optionLocaleSha256":locale,"models":_models(),
          "academicTaskAccepted":False,"completeAcademicProofGatesStillOpen":90,
          "newProviderCalls":0,"publicationAuthorized":False}
    proof={**body,"witnessSha256":_digest(body)}
    independently_check_isolated_pair_witness(proof)
    return proof

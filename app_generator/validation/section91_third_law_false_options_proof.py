"""BSA281 original Serway Section 9.1 MCQ05: three independent physics counterproofs.

False MCQ statements are evaluated against two distinct *exact rational*
isolated two-particle encounters with equal/opposite nonzero internal forces.
Every entire frozen EN/MS/ZH option and premise is bound to a separately
pinned, human-read, finite proposition; unknown edits fail closed. The
physical derivation comes from rereading the *original selected Serway PDF*,
not from the marked correct answer or any outside source. The task-specific
source science witness is not a full translation/diagram/activity PASS.
"""
from __future__ import annotations

from fractions import Fraction as F
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

from app_generator.validation.section91_formal_physics import (
    _SOURCE_SHA,_CANDIDATE_SHA,_source_axioms,_digest,
)
from app_generator.validation.full_semantic_proof_queue import (
    plan_full_semantic_proofs,
)
from app_generator.validation.source_passages import extract_pages
from app_generator.runtime.v3_selected_textbook_scientific_provenance import (
    _source_activity_anchors,
)

_ACTIVITY="act-mcq-05-third-law-connection"
_KIND="MCQ_DISTRACTOR_SCIENCE"
_PROOF="NONZERO_MUTUAL_FORCE_MOMENTUM_TRANSFER_THIRD_LAW"
_TRUE_SEMANTIC_ROLE=(
    "ISOLATED_TWO_PARTICLE_PAIR_EQUAL_OPPOSITE_INTERNAL_FORCES_"
    "INDIVIDUAL_NONZERO_IMPULSES_WITH_CONSTANT_TOTAL_MOMENTUM"
)
_FALSE_CLASSES={
    "opt-b":"FALSE_EACH_INDIVIDUAL_MOMENTUM_MUST_REMAIN_CONSTANT",
    "opt-c":"FALSE_INTERNAL_FORCES_CANCEL_EACH_PARTICLE_ACCELERATION",
    "opt-d":"FALSE_NEWTON_THIRD_LAW_REQUIRES_EQUAL_MASS_AND_VELOCITY",
}
_TASK_IDS={
    "opt-b":"1ae0a77b534fbb9c5cda2443fc505bf525e1cfdb62a9e49c59b172572565abac",
    "opt-c":"324222da117c7f885d3f6df16f8a1309dcb536dcd8e9b2e9a8b2304cdc38708f",
    "opt-d":"f6917a98f5db9cd3be290e9393e4455c8e8e7b78fb2961f007b7dd652c76b8c8",
}
# Frozen complete localized sentences, independently pinned to their
# human-audited semantic roles above; no substring/keyword truth inference.
# Changing even a suffix, negation, punctuation or Chinese glyph fails.
_PROMPT_SHA={
    "en":"cc2b326a5d0ccef11f8439bd68a09862fed7f46f5edf9270a38af27fafcde74b",
    "ms":"4d9186915e8e0b9cd51b0c056998d84a9d2419c48ff55d39dae7a229375ec26c",
    "zh":"966a6789b5e81a73fbf1b42a281bf9a3b02370b7e0ec4f57b5228c8fe4bb059a",
}
_OPTION_SHA={
    "opt-b":{
        "en":"29fff4be30b64b57cf362caedf71c45081ec4aede71af8f506e6341a7db012dd",
        "ms":"fcfe90e2df36ec6b760fc562e65310da0eb65a1f9048ec996128fa5939b8df46",
        "zh":"98f2965d45d29c31c0cf87a658824ac820f4565e35214ca99eb008c295873335",
    },
    "opt-c":{
        "en":"9fb1b047e213359598dafa6b89ec5cbd55eab862ea1417afd6e15413f40a9e7b",
        "ms":"5b8874f231978053c53629bb7b3d93aba21d6d5ce70100bf54f9d7fc3635fcbf",
        "zh":"67ee98572955459753c09bd72b6817151195c8253de7d6f6cc1fd07ec3ca89b5",
    },
    "opt-d":{
        "en":"414f08700c44d3ed6f565089e9043bc1c3ac7394558f3494608f8fd3febba81f",
        "ms":"d9d065e74db0ae1887088a002417327020519b96e12d424cea097fda52f16246",
        "zh":"6b586046204e5966de9581701093dde2d42694dc4191462f59bb0c3f4403289c",
    },
}
# The original page actually contains opposite equal internal forces and
# Newton's momentum-rate second law. The models do not assume equal mass,
# equal speed, or conservation for each individual particle.
_CASE_PARAMETERS=(
    # (mass1,mass2,velocity1,velocity2,impulse_on_1,interaction_duration)
    (F(2),F(3),F(1),F(-1),F(1,2),F(1,4)),
    (F(4),F(1),F(-3,2),F(2),F(-3,4),F(3,2)),
)

def _sha(value:str)->str:
    if not isinstance(value,str) or not value.strip():
        raise ValueError("BSA281_MISSING_EXACT_SOURCE_LOCALE_SENTENCE")
    return sha256(value.encode("utf8")).hexdigest()

def _all_locales(sentence:dict[str,str],expected:dict[str,str])->dict[str,str]:
    if not isinstance(sentence,dict) or set(sentence)!=set(expected):
        raise ValueError("BSA281_UNPARSED_EN_MS_ZH_LOCALE")
    out={}
    for lang in ("en","ms","zh"):
        digest=_sha(sentence[lang])
        if digest!=expected[lang]:
            raise ValueError("BSA281_COMPLETE_LOCALIZED_PROPOSITION_CHANGED_"+lang.upper())
        out[lang]=digest
    return out

def _model(m1:F,m2:F,v1:F,v2:F,j:F,dt:F)->dict[str,Any]:
    if (m1<=0 or m2<=0 or m1==m2 or v1==v2 or j==0 or dt<=0):
        raise ValueError("BSA281_COUNTERMODEL_NONDEGENERATE_PAIR_REQUIRED")
    pi1,pi2=m1*v1,m2*v2
    pf1,pf2=pi1+j,pi2-j
    vf1,vf2=pf1/m1,pf2/m2
    f1,f2=j/dt,-j/dt
    a1,a2=f1/m1,f2/m2
    if (pf1==pi1 or pf2==pi2 or vf1==vf2
        or a1==0 or a2==0 or f1+f2!=0
        or pi1+pi2!=pf1+pf2
        or f1!=(pf1-pi1)/dt or f2!=(pf2-pi2)/dt
        or a1!=(vf1-v1)/dt or a2!=(vf2-v2)/dt):
        raise ValueError("BSA281_THIRD_LAW_RATIONAL_PHYSICS_FAILED")
    return {
        "mass1":str(m1),"mass2":str(m2),
        "velocity1Before":str(v1),"velocity2Before":str(v2),
        "interactionDuration":str(dt),"impulseOn1":str(j),
        "impulseOn2":str(-j),
        "particle1MomentumBefore":str(pi1),"particle2MomentumBefore":str(pi2),
        "particle1MomentumAfter":str(pf1),"particle2MomentumAfter":str(pf2),
        "particle1VelocityAfter":str(vf1),"particle2VelocityAfter":str(vf2),
        "forceOn1":str(f1),"forceOn2":str(f2),
        "particle1Acceleration":str(a1),"particle2Acceleration":str(a2),
        "totalMomentumBefore":str(pi1+pi2),
        "totalMomentumAfter":str(pf1+pf2),
        "thirdLawEqualOppositeForces":True,
        "individualMomentaRemainConstant":False,
        "individualAccelerationsVanish":False,
        "thirdLawRequiresEqualMassOrVelocity":False,
    }

def _models()->list[dict[str,Any]]:
    return [_model(*args) for args in _CASE_PARAMETERS]

def _reparse_physics(row:dict[str,Any])->None:
    """Independent rational recomputation, not trust in a signed JSON digest."""
    try:
        m1,m2=F(row["mass1"]),F(row["mass2"])
        v1,v2=F(row["velocity1Before"]),F(row["velocity2Before"])
        j,dt=F(row["impulseOn1"]),F(row["interactionDuration"])
        fresh=_model(m1,m2,v1,v2,j,dt)
    except (ValueError,KeyError,TypeError,ZeroDivisionError) as e:
        raise ValueError("BSA281_RATIONAL_COUNTERMODEL_UNREPARSEABLE") from e
    if row!=fresh:
        raise ValueError("BSA281_MOMENTUM_FORCE_ACCELERATION_MODEL_RECHECK_FAILED")
    if row["thirdLawRequiresEqualMassOrVelocity"] is not False:
        raise ValueError("BSA281_MISLABELED_THIRD_LAW_MODEL")

def independently_check_third_law_witness(proof:dict[str,Any])->None:
    if (not isinstance(proof,dict) or proof.get("optionId") not in _FALSE_CLASSES
        or proof.get("taskId")!=_TASK_IDS.get(proof.get("optionId"))
        or proof.get("falseScientificAssertion")!=_FALSE_CLASSES[
            proof.get("optionId")]
        or proof.get("proofFamily")!=_PROOF
        or proof.get("premiseSemanticRole")!=_TRUE_SEMANTIC_ROLE
        or proof.get("completePromptLocaleDigests")!=_PROMPT_SHA
        or proof.get("completeFalseOptionLocaleDigests")!=_OPTION_SHA[
            proof.get("optionId")]
        or proof.get("sourceSha256")!=_SOURCE_SHA
        or proof.get("candidateSha256")!=_CANDIDATE_SHA
        or proof.get("independentScienceWitnessVerified") is not True
        or proof.get("academicTaskAccepted") is not False
        or proof.get("completeAcademicProofGatesStillOpen")!=90
        or proof.get("newProviderCalls")!=0
        or proof.get("publicationAuthorized") is not False):
        raise ValueError("BSA281_UNTRUSTED_THIRD_LAW_SCIENCE_WITNESS")
    if proof.get("witnessSha256")!=_digest({
            k:v for k,v in proof.items() if k!="witnessSha256"}):
        raise ValueError("BSA281_WITNESS_INTEGRITY_CHANGED")
    models=proof.get("rationalIsolatedPairCountermodels")
    if models!=_models() or not isinstance(models,list) or len(models)!=2:
        raise ValueError("BSA281_COUNTERMODELS_NOT_DISTINCT_AND_REPRODUCED")
    for case in models:
        _reparse_physics(case)
        if (case["individualMomentaRemainConstant"] is not False
            or case["individualAccelerationsVanish"] is not False
            or case["thirdLawEqualOppositeForces"] is not True):
            raise ValueError("BSA281_FALSE_CLAIM_NOT_DISPROVED")

def independently_prove_third_law_false_option(
    *,source_pdf:Path,candidate_path:Path,option_id:str,
)->dict[str,Any]:
    if option_id not in _FALSE_CLASSES:
        raise ValueError("BSA281_UNREGISTERED_THIRD_LAW_FALSE_OPTION")
    if (source_pdf.is_symlink() or not source_pdf.is_file()
        or candidate_path.is_symlink() or not candidate_path.is_file()
        or sha256(source_pdf.read_bytes()).hexdigest()!=_SOURCE_SHA
        or sha256(candidate_path.read_bytes()).hexdigest()!=_CANDIDATE_SHA):
        raise ValueError("BSA281_AUTHENTIC_ONE_SERWAY_SOURCE_AND_CANDIDATE_REQUIRED")
    axioms=_source_axioms(source_pdf,_SOURCE_SHA)
    if (axioms.get("third law",0)<3
        or axioms.get("time rate of change of the linear momentum",0)<1
        or axioms.get("defined to be the product of the mass and velocity",0)<1):
        raise ValueError("BSA281_ORIGINAL_FORCE_PAIR_MOMENTUM_AXIOMS_MISSING")
    pages=extract_pages(source_pdf)
    page1=" ".join(pages[0].casefold().split())
    if ("equal in magnitude" not in page1
        or "opposite in direction" not in page1):
        raise ValueError("BSA281_ORIGINAL_MUTUAL_FORCE_CLAUSE_NOT_FOUND")
    pkg=json.loads(candidate_path.read_text(encoding="utf8"))
    acts=pkg.get("activities",[])
    if (not isinstance(acts,list) or len(acts)!=18
        or acts[4].get("id")!=_ACTIVITY or acts[4].get("type")!="mcq"):
        raise ValueError("BSA281_ORIGINAL_MC_Q05_ACTIVITY_CHANGED")
    activity=acts[4]
    prompt=_all_locales(activity["prompt"],_PROMPT_SHA)
    key=activity.get("answerKey",{})
    opts=key.get("options",[])
    if (key.get("correct")!="opt-a" or len(opts)!=4
        or [o.get("id") for o in opts]!=
           ["opt-a","opt-b","opt-c","opt-d"]):
        raise ValueError("BSA281_ORIGINAL_THIRD_LAW_KEY_STRUCTURE_CHANGED")
    option_pos=next(i for i,o in enumerate(opts) if o["id"]==option_id)
    opt=opts[option_pos]
    full_locales=_all_locales(opt["label"],_OPTION_SHA[option_id])
    source_anchor=_source_activity_anchors(pages=pages,activities=acts)[4]
    if (source_anchor.get("activityId")!=_ACTIVITY
        or source_anchor.get("uniquePagePassageLocated") is not True
        or source_anchor.get("physicalPage")!=1):
        raise ValueError("BSA281_ORIGINAL_SOURCE_PAGE1_UNIQUE_ANCHOR_MISSING")
    queue=plan_full_semantic_proofs(package=pkg,source_sha256=_SOURCE_SHA)
    surface_path=f"answerKey/options/{option_pos}/label"
    tasks=[t for t in queue["tasks"] if (
        t["kind"]==_KIND and t["activityId"]==_ACTIVITY
        and t["surfacePath"]==surface_path)]
    if (queue["taskCount"]!=429 or len(tasks)!=1
        or tasks[0]["taskId"]!=_TASK_IDS[option_id]
        or tasks[0]["surfaceSha256"]!=_digest(opt["label"])):
        raise ValueError("BSA281_CANONICAL_MC_Q05_TASK_NOT_REDERIVED")
    body={
        "taskId":tasks[0]["taskId"],
        "taskKind":_KIND,
        "activityId":_ACTIVITY,
        "optionId":option_id,
        "surfacePath":surface_path,
        "surfaceSha256":tasks[0]["surfaceSha256"],
        "sourceSha256":_SOURCE_SHA,
        "candidateSha256":_CANDIDATE_SHA,
        "sourcePageIndex":source_anchor["physicalPage"],
        "sourcePassageSha256":source_anchor["passageSha256"],
        "sourcePhysicsPremisesDigest":_digest(sorted(axioms.items())),
        "completePromptLocaleDigests":prompt,
        "completeFalseOptionLocaleDigests":full_locales,
        "premiseSemanticRole":_TRUE_SEMANTIC_ROLE,
        "proofFamily":_PROOF,
        "falseScientificAssertion":_FALSE_CLASSES[option_id],
        "rationalIsolatedPairCountermodels":_models(),
        "independentScienceWitnessVerified":True,
        "academicTaskAccepted":False,
        "completeAcademicProofGatesStillOpen":90,
        "newProviderCalls":0,
        "publicationAuthorized":False,
    }
    proof={**body,"witnessSha256":_digest(body)}
    independently_check_third_law_witness(proof)
    return proof

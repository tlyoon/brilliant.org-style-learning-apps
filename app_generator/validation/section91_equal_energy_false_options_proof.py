"""Original Serway MCQ07: exact countermodels for three false energy claims.

The producer checks the one pinned textbook, frozen trilingual candidate and
canonical task identity. Its witness is not an academic admission receipt.
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

_ACTIVITY = "act-mcq-07-equal-ke-momentum-relation"
# BSA294: BSA253 task IDs include the digest of the *whole* candidate.
# The tracked sample differs from the private revised candidate. Derive IDs
# from that SHA-pinned candidate and compare them to signed V36 rows at
# admission; sample-derived constants would reject genuine owner science.
_OPTIONS_ORDER = ("opt-equal-momentum", "opt-scout-greater", "opt-cannot-determine")
_PROMPT = {"en":"8ddd8b8f9df0de8465bd510ee59c09f5526835a0e031e05349066dbf922e3fdf",
           "ms":"6cb146f86eeac8a988059fd331f060120cc34289483b25bb7e025e06f670d0cb",
           "zh":"60bcdefbe2ea5bd0159af064ddc204200191704b0b952dc4685eeb1122e8ca43"}
_OPTIONS = {
    "opt-equal-momentum": {"en":"9330526df3603f0682e17a3691986e42e4281813328d9e7ddeaff1eabcbbdb26", "ms":"49b7bd05dad16711d5001403ebec175d1ac9cdeee0fe5630a5a0753ba0e4c77d", "zh":"38bbca890ec4eba5d6e8e48d59e6a57844e7688195a62b8c794b1cb3b13e046d"},
    "opt-scout-greater": {"en":"aa1b08ab830d56e2772bdbdd7f058ad5dbfe9554d17791d553e31da2074f289c", "ms":"ce7320c1edeeb78988301fb254864f3e0c623602249ba910469a80f85569e407", "zh":"b0ac3e4c82316d4519c7efdeace7a5f718cd65182f22a780b2c2513c880a2d33"},
    "opt-cannot-determine": {"en":"49502b05efcf674d09a763cc6f2e064045bd5b961e379c7e3e56b0b36ebc95fb", "ms":"4386efae1e04c6315e596523ffff94a3fc31485bdbbcf4a42bd21decee869677", "zh":"a36165d8d24851665b1d0b21a2fe20ad107678eac8129781c4b6094338870b52"},
}
_CLAIMS = {"opt-equal-momentum":"EQUAL_K_IMPLIES_EQUAL_P_MAGNITUDE",
           "opt-scout-greater":"HIGHER_SPEED_OVERRIDES_MASS_AT_EQUAL_K",
           "opt-cannot-determine":"SPEED_REQUIRED_TO_RANK_P_AT_EQUAL_K"}
_CASES = ((F(8),F(1),F(2),F(2)), (F(25),F(1,5),F(1),F(1)))


def _locale_hashes(value: dict, expected: dict) -> dict:
    if not isinstance(value,dict) or set(value)!={"en","ms","zh"} or any(
        not isinstance(x,str) or not x.strip() for x in value.values()
    ):
        raise ValueError("BSA289_COMPLETE_TRILINGUAL_SENTENCE_REQUIRED")
    actual={k:sha256(value[k].encode("utf8")).hexdigest() for k in ("en","ms","zh")}
    if actual!=expected:
        raise ValueError("BSA289_FROZEN_TRILINGUAL_MEANING_CHANGED")
    return actual


def _model(heavy_mass:F,heavy_speed:F,light_mass:F,light_speed:F)->dict:
    if not all(isinstance(x,F) and x>0 for x in (heavy_mass,heavy_speed,light_mass,light_speed)):
        raise ValueError("BSA289_POSITIVE_EXACT_RATIONAL_MODEL_REQUIRED")
    heavy_k=heavy_mass*heavy_speed*heavy_speed/2
    light_k=light_mass*light_speed*light_speed/2
    heavy_p=heavy_mass*heavy_speed
    light_p=light_mass*light_speed
    if not (heavy_mass>light_mass and heavy_speed<light_speed and
            heavy_k==light_k and heavy_p>light_p and
            heavy_p*heavy_p==2*heavy_mass*heavy_k and
            light_p*light_p==2*light_mass*light_k):
        raise ValueError("BSA289_EQUAL_K_MOMENTUM_ORDER_NOT_DERIVED")
    return {"heavyMass":str(heavy_mass),"heavySpeed":str(heavy_speed),
            "lightMass":str(light_mass),"lightSpeed":str(light_speed),
            "heavyKineticEnergy":str(heavy_k),"lightKineticEnergy":str(light_k),
            "heavyMomentumMagnitude":str(heavy_p),"lightMomentumMagnitude":str(light_p)}


def _models()->list[dict]:
    return [_model(*case) for case in _CASES]


def independently_check_equal_energy_witness(proof:dict)->None:
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
        or type(proof.get("sourcePageIndex")) is not int
        or proof["sourcePageIndex"]<1
        or any(not isinstance(proof.get(k),str) or len(proof[k])!=64 for k in
               ("surfaceSha256","sourcePassageSha256","sourcePhysicsPremisesSha256"))
        or proof.get("academicTaskAccepted") is not False
        or proof.get("completeAcademicProofGatesStillOpen")!=90
        or proof.get("publicationAuthorized") is not False
        or proof.get("newProviderCalls")!=0
        or proof.get("witnessSha256")!=_digest({k:v for k,v in proof.items() if k!="witnessSha256"})):
        raise ValueError("BSA289_UNTRUSTED_EQUAL_ENERGY_WITNESS")
    for row in proof["models"]:
        if row!=_model(*(F(row[k]) for k in ("heavyMass","heavySpeed","lightMass","lightSpeed"))):
            raise ValueError("BSA289_EXACT_RATIONAL_RECOMPUTATION_FAILED")


def independently_prove_equal_energy_false_option(*,source_pdf:Path,candidate_path:Path,option_id:str)->dict:
    if option_id not in _OPTIONS_ORDER:
        raise ValueError("BSA289_UNREGISTERED_EQUAL_ENERGY_OPTION")
    if (source_pdf.is_symlink() or candidate_path.is_symlink() or not source_pdf.is_file()
        or not candidate_path.is_file() or sha256(source_pdf.read_bytes()).hexdigest()!=_SOURCE_SHA
        or sha256(candidate_path.read_bytes()).hexdigest()!=_CANDIDATE_SHA):
        raise ValueError("BSA289_AUTHENTIC_ONE_SERWAY_SOURCE_AND_CANDIDATE_REQUIRED")
    axioms=_source_axioms(source_pdf,_SOURCE_SHA)
    if (axioms.get("linear momentum is a vector",0)<1
        or axioms.get("defined to be the product of the mass and velocity",0)<1
        or axioms.get("kinetic energy can transform",0)<1):
        raise ValueError("BSA289_ORIGINAL_MOMENTUM_ENERGY_PREMISES_MISSING")
    package=json.loads(candidate_path.read_text(encoding="utf8"))
    activities=package.get("activities")
    if not isinstance(activities,list) or len(activities)!=18 or activities[6].get("id")!=_ACTIVITY:
        raise ValueError("BSA289_FROZEN_MCQ07_ACTIVITY_CHANGED")
    activity=activities[6]
    prompt=_locale_hashes(activity.get("prompt"),_PROMPT)
    key=activity.get("answerKey",{})
    options=key.get("options",[])
    expected=["opt-transport-greater",*_OPTIONS_ORDER]
    if key.get("correct")!=expected[0] or [x.get("id") for x in options]!=expected:
        raise ValueError("BSA289_FROZEN_MCQ07_ANSWER_KEY_CHANGED")
    position=expected.index(option_id)
    locale=_locale_hashes(options[position].get("label"),_OPTIONS[option_id])
    anchors=_source_activity_anchors(pages=extract_pages(source_pdf),activities=activities)
    anchor=anchors[6]
    if anchor.get("activityId")!=_ACTIVITY or anchor.get("uniquePagePassageLocated") is not True:
        raise ValueError("BSA289_ORIGINAL_SOURCE_ANCHOR_MISSING")
    queue=plan_full_semantic_proofs(package=package,source_sha256=_SOURCE_SHA)
    tasks=[t for t in queue["tasks"] if t["activityId"]==_ACTIVITY and
           t["kind"]=="MCQ_DISTRACTOR_SCIENCE" and
           t["surfacePath"]==f"answerKey/options/{position}/label"]
    if (queue["taskCount"]!=429 or len(tasks)!=1
        or tasks[0]["surfaceSha256"]!=_digest(options[position]["label"])):
        raise ValueError("BSA289_CANONICAL_MCQ07_TASK_NOT_REDERIVED")
    body={"taskId":tasks[0]["taskId"],"optionId":option_id,"falseClaim":_CLAIMS[option_id],
          "sourceSha256":_SOURCE_SHA,"candidateSha256":_CANDIDATE_SHA,
          "surfaceSha256":tasks[0]["surfaceSha256"],
          "sourcePageIndex":anchor["physicalPage"],"sourcePassageSha256":anchor["passageSha256"],
          "sourcePhysicsPremisesSha256":_digest(sorted(axioms.items())),
          "promptLocaleSha256":prompt,"optionLocaleSha256":locale,"models":_models(),
          "academicTaskAccepted":False,"completeAcademicProofGatesStillOpen":90,
          "newProviderCalls":0,"publicationAuthorized":False}
    result={**body,"witnessSha256":_digest(body)}
    independently_check_equal_energy_witness(result)
    return result

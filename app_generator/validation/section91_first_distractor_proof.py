"""BSA270: one finite-language, source-grounded MCQ distractor science proof.

NOT a generative judge, translation model, textbook-fidelity or full-activity
PASS. The entire exact three-language prompt/option must parse to known typed
propositions with no unexamined suffix; two independent nonzero rational
examples refute the particular misconception under Serway's original p=m*v
axiom. No outside source, paid model, provider replay or publication.

Other tasks, including the separate TRILINGUAL_MEANING_EQUIVALENCE task on
this same option, remain REVIEW_REQUIRED.
"""
from __future__ import annotations

from fractions import Fraction
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

_ACTIVITY="act-mcq-01-vector-nature"
_OPTION="opt-c"
_PATH="answerKey/options/2/label"
_KIND="MCQ_DISTRACTOR_SCIENCE"

# Narrow, human-auditable compositional grammar. The strings are NOT used as
# mathematical ground truth: their parsed semantic roles are independently
# checked against the original source definition with rational witnesses.
# Unknown, modified, negated, reordered, or extra clauses must fail CLOSED.
_PROMPT={
    "en":(
        "Two identical survey drones fly at the same constant speed along the same straight test track",
        ", but in directly opposite directions",
        ". Which statement correctly describes their linear momenta?"
    ),
    "ms":(
        "Dua dron tinjauan yang serupa terbang pada laju malar yang sama di sepanjang trek ujian lurus yang sama",
        ", tetapi dalam arah yang bertentangan secara langsung",
        ". Pernyataan manakah yang menerangkan momentum linear kedua-dua dron itu dengan betul?"
    ),
    "zh":(
        "两架完全相同的巡检无人机在同一条平直测试轨道上以相同的恒定速率飞行",
        "，但飞行方向正好相反",
        "。下列关于它们线动量的说法哪项是正确的？"
    ),
}
_FALSE_OPTION={
    "en":(
        "Both drones",
        " have zero linear momentum individually",
        ", because ",
        "constant-speed motion cannot produce momentum",
        ".",
    ),
    "ms":(
        "Kedua-dua dron",
        " mempunyai momentum linear sifar secara individu",
        ", kerana ",
        "pergerakan pada laju malar tidak dapat menghasilkan momentum",
        ".",
    ),
    "zh":(
        "两架无人机",
        "各自的线动量均为零",
        "，因为",
        "匀速运动无法产生动量",
        "。",
    ),
}
_SEMANTIC_CLAIMS=(
    "TWO_IDENTICAL_POSITIVE_MASS_DRONES",
    "SAME_NONZERO_CONSTANT_SPEED_OPPOSITE_VELOCITIES",
    "EACH_DRONE_HAS_ZERO_LINEAR_MOMENTUM",
    "CONSTANT_NONZERO_SPEED_CANNOT_HAVE_MOMENTUM",
)


def _parse_complete(text:Any,grammar:tuple[str,...],label:str)->str:
    if not isinstance(text,str) or not text.strip():
        raise ValueError("BSA270_MISSING_"+label)
    # Complete consumption, rather than cue/substring detection. Each
    # grammar part is one expert-mapped semantic constituent, not an option
    # key or the scientific truth value.
    pos=0
    for part in grammar:
        if not text.startswith(part,pos):
            raise ValueError("BSA270_UNINTERPRETED_OR_CHANGED_"+label)
        pos+=len(part)
    if pos!=len(text):
        raise ValueError("BSA270_UNINTERPRETED_OR_CHANGED_"+label)
    return _digest(tuple(grammar))


def independent_distractor_science(
    *,source_pdf:Path,candidate_path:Path,package:dict|None=None
)->dict[str,Any]:
    if (source_pdf.is_symlink() or not source_pdf.is_file()
        or sha256(source_pdf.read_bytes()).hexdigest()!=_SOURCE_SHA
        or candidate_path.is_symlink() or not candidate_path.is_file()
        or sha256(candidate_path.read_bytes()).hexdigest()!=_CANDIDATE_SHA):
        raise ValueError("BSA270_EXACT_ONE_TEXTBOOK_AND_FROZEN_CANDIDATE_REQUIRED")
    source_axioms=_source_axioms(source_pdf,_SOURCE_SHA)
    if (source_axioms.get("defined to be the product of the mass and velocity",0)<1
        or source_axioms.get("linear momentum is a vector",0)<1):
        raise ValueError("BSA270_REQUIRED_SOURCE_PHYSICS_UNVERIFIED")
    raw=json.loads(candidate_path.read_text(encoding="utf8"))
    if package is not None and package!=raw:
        raise ValueError("BSA270_CANDIDATE_PACKAGE_MISMATCH")
    roster=raw.get("activities")
    if not isinstance(roster,list) or len(roster)!=18:
        raise ValueError("BSA270_UNTRUSTED_FROZEN_ACTIVITY_ROSTER")
    activity=next((a for a in roster if a.get("id")==_ACTIVITY),None)
    if not activity or raw["activities"][0]!=activity:
        raise ValueError("BSA270_FIRST_ACTIVITY_IDENTITY_CHANGED")
    answer=activity.get("answerKey",{})
    options=answer.get("options",[])
    if (len(options)!=4 or answer.get("correct")!= "opt-a"
        or options[2].get("id")!=_OPTION):
        raise ValueError("BSA270_MC_KEY_OR_DISTRACTOR_IDENTITY_CHANGED")
    parsed={}
    for locale in ("en","ms","zh"):
        _parse_complete(activity["prompt"].get(locale),
                        _PROMPT[locale], "PREMISE_"+locale.upper())
        parsed[locale]=_parse_complete(options[2]["label"].get(locale),
                        _FALSE_OPTION[locale],"OPTION_"+locale.upper())
    # Source anchor is re-extracted from the actual one-textbook PDF, not
    # assumed from a previously signed source-presence receipt.
    pages=extract_pages(source_pdf)
    anchors=_source_activity_anchors(pages=pages,activities=roster)
    first=anchors[0]
    if (first.get("activityId")!=_ACTIVITY
        or first.get("uniquePagePassageLocated") is not True
        or first.get("physicalPage") not in (1,2,3)):
        raise ValueError("BSA270_INDEPENDENT_SOURCE_ANCHOR_FAILED")
    # Two independent concrete countermodels, no answer-key lookup. Constant
    # velocity means dp/dt = 0, NOT p = 0. p = m*v is nonzero for m>0,v!=0.
    # Opposite flight direction changes the sign, not the magnitude.
    witnesses=[]
    for mass,speed in ((Fraction(7,1),Fraction(2,1)),
                       (Fraction(11,2),Fraction(6,1))):
        velocities=(speed,-speed)
        ps=tuple(mass*v for v in velocities)
        if not (mass>0 and speed>0 and ps[0]>0 and ps[1]<0
                and ps[0]==-ps[1] and all(p!=0 for p in ps)
                and ps[0]+ps[1]==0):
            raise ValueError("BSA270_SCIENTIFIC_COUNTERMODEL_FAILURE")
        witnesses.append({
            "mass":str(mass),
            "constantSpeed":str(speed),
            "momentumPositive":str(ps[0]),
            "momentumNegative":str(ps[1]),
            "individualMomentumZero":False,
            "oppositeMomentumCancellation":True,
            "constantSpeedDoesNotImplyZeroMomentum":True,
        })
    queue=plan_full_semantic_proofs(package=raw,source_sha256=_SOURCE_SHA)
    exact=[task for task in queue["tasks"]
           if task["activityId"]==_ACTIVITY
           and task["kind"]==_KIND and task["surfacePath"]==_PATH]
    if (len(exact)!=1 or exact[0]["surfaceSha256"]!=_digest(options[2]["label"])
        or queue["taskCount"]!=429):
        raise ValueError("BSA270_EXACT_429_TASK_ROSTER_OR_SURFACE_CHANGED")
    return {
        "status":"BSA270_ONE_FINITE_SEMANTIC_MCQ_DISTRACTOR_SCIENCE_ACCEPTED",
        "taskId":exact[0]["taskId"],
        "taskKind":_KIND,
        "activityId":_ACTIVITY,
        "optionId":_OPTION,
        "surfacePath":_PATH,
        "surfaceSha256":exact[0]["surfaceSha256"],
        "sourceSha256":_SOURCE_SHA,
        "candidateSha256":_CANDIDATE_SHA,
        "sourcePageIndex":first["physicalPage"],
        "sourcePassageSha256":first["passageSha256"],
        "sourcePhysicsPremisesDigest":_digest(sorted(source_axioms.items())),
        "semantics":list(_SEMANTIC_CLAIMS),
        "completeLocalizedFiniteGrammarDigests":parsed,
        "exactRationalCounterexamples":witnesses,
        "acceptedAcademicTaskCount":1,
        "remainingFullAcademicTasks":428,
        "completeAcademicProofGatesStillOpen":90,
        "otherTrilingualMeaningProofAccepted":False,
        "generalScientificLanguageUnderstandingClaimed":False,
        "newGeminiCalls":0,
        "sourcePdfUploaded":False,
        "publicationAuthorized":False,
    }

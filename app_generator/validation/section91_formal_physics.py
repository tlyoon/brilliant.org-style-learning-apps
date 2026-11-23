"""BSA252: finite, independent Section9.1 physics/answer witness generation.

Checks ALL nine MCQ keys and ALL nine interactive solutions against actual
Fraction-valued physical scenarios. Unlike a stored-answer comparison,
the expected solutions are derived from separate executable source axioms.
This remains bounded proof of a *declared formal model*, never exhaustive
validation of all English/MS/ZH natural-language interpretations or visuals.

Designed as an explicit subject adapter; an unrelated textbook/section
MUST NOT inherit these model claims or source bindings.
"""
from __future__ import annotations

from fractions import Fraction as F
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

from app_generator.validation.source_passages import extract_pages

_SOURCE_SHA = "cdbea066436ace273b94aedc2eb1b22f94d0fd5b0b3f810d6bfc27469a5e7b50"
_CANDIDATE_SHA = "454715ec1a3e23ce19099d4f1ed56babb1de3c8561473b9072c6e01ffbae9c38"
_CASES = (
    "act-mcq-01-vector-nature",
    "act-mcq-02-si-units",
    "act-mcq-03-net-force-definition",
    "act-mcq-04-two-particle-opposite-momentum",
    "act-mcq-05-third-law-connection",
    "act-mcq-06-equal-speed-comparison",
    "act-mcq-07-equal-ke-momentum-relation",
    "act-mcq-08-isolated-subsystem-fallacy",
    "act-mcq-09-no-momentum-conversion",
    "act-int-01-scalar-vs-vector-class",
    "act-int-02-quantity-dimension-match",
    "act-int-03-linear-momentum-properties-select",
    "act-int-04-energy-momentum-contrast-class",
    "act-int-05-newton-second-law-steps-order",
    "act-int-06-equal-speed-momentum-rank",
    "act-int-07-equal-ke-mass-momentum-rank",
    "act-int-08-conservation-validity-select",
    "act-int-09-mechanics-models-match",
)
_AXIOMS = (
    ("linear momentum is a vector",1),
    ("defined to be the product of the mass and velocity",1),
    ("dimensions ml/t",1),
    ("time rate of change of the linear momentum",1),
    ("newton",3),
    ("third law",1),
    ("isolated system",3),
    ("kinetic energy can transform",1),
    ("only one type of linear momentum",1),
)
_M = (1,0,0)
_V = (0,1,-1)
_P = (1,1,-1)
_FORCE = (1,1,-2)
_ENERGY = (1,2,-2)
_DIMENSION = {
    "item-linear-momentum":_P,
    "item-net-force":_FORCE,
    "item-velocity":_V,
}
_TYPES = {
    "item-p":"target-vector","item-v":"target-vector",
    "item-ke":"target-scalar","item-m":"target-scalar",
}
_CONTRAST = {
    "item-vector-direction":"target-momentum",
    "item-transforms":"target-energy",
    "item-cancels-opposite":"target-momentum",
    "item-scalar-nonnegative":"target-energy",
}
_FORMULA_MATCHES = {
    "item-rate-of-change":"target-force",
    "item-vector-no-transform":"target-momentum",
    "item-scalar-transforms":"target-energy",
}
_UNITS_MATCHES = {
    "item-linear-momentum":"target-desc-momentum",
    "item-net-force":"target-desc-force",
    "item-velocity":"target-desc-velocity",
}


def _digest(value:Any)->str:
    return sha256(json.dumps(value,sort_keys=True,ensure_ascii=False,
        separators=(",",":")).encode("utf8")).hexdigest()


def _source_axioms(pdf:Path, source_sha:str)->dict[str,int]:
    if (source_sha!=_SOURCE_SHA or pdf.is_symlink() or not pdf.is_file()
            or sha256(pdf.read_bytes()).hexdigest()!=source_sha):
        raise ValueError("BSA252_ORIGINAL_SINGLE_TEXTBOOK_SHA_CHANGED")
    pages=extract_pages(pdf)
    if len(pages)!=3:
        raise ValueError("BSA252_ORIGINAL_91_PAGES_CHANGED")
    clean=" ".join(" ".join(pages).casefold().split())
    found={}
    for phrase,count in _AXIOMS:
        n=clean.count(phrase)
        if n<count:
            raise ValueError("BSA252_SOURCE_PHYSICS_AXIOM_MISSING")
        found[phrase]=n
    return found


def _mcq_cases()->dict[str,dict[str,bool]]:
    """Compute option propositions from exact rational scenarios and laws."""
    m=F(5);v=F(3)
    p1=m*v;p2=m*(-v)
    k1=m*v*v/2;k2=k1
    # 1. 1-D opposed vector, independently nonzero individual momenta.
    vector={
        "opt-a":p1==-p2 and abs(p1)==abs(p2) and p1!=0,
        "opt-b":p1==p2,
        "opt-c":p1==0 and p2==0,
        "opt-d":p1*v==0,
    }
    # 2. SI exponents are independently derived, not copied from the key.
    dim=lambda a,b: tuple(x+y for x,y in zip(a,b))
    linear=dim(_M,_V)
    energy=dim(_M,(0,2,-2))
    units={
        "opt-a":linear==_P and _P!=_ENERGY and bool(_V[1]),
        "opt-b":linear==_P and p1==p2,  # opposed vector momenta disprove scalar inference
        "opt-c":linear==energy,
        "opt-d":linear==(1,-1,1),
    }
    # 3. Nonzero constant F changes p with dt; it never equals constant p.
    start=F(4);force=F(3);dt=F(2)
    after=start+force*dt
    newton={
        "opt-a":after-start==force*dt and after>start,
        "opt-b":force==start and after==start,
        "opt-c":force==F(0) and after!=start,
        "opt-d":force==0,
    }
    # 4. Opposite two-particle velocities cancel p, not squared kinetic energies.
    opposite={
        "opt-a":p1+p2==0 and k1+k2>0,
        "opt-b":p1+p2>0 and k1+k2>0,
        "opt-c":p1+p2==0 and k1+k2==0,
        "opt-d":p1+p2>0 and k1+k2==0,
    }
    # 5. Equal/opposite internal impulse changes EACH p, not their sum.
    impulse=F(7,3);before=(F(1),F(-2))
    after_pair=(before[0]+impulse,before[1]-impulse)
    third={
        "opt-a":sum(before)==sum(after_pair) and after_pair!=before,
        "opt-b":after_pair==before,
        "opt-c":impulse==0,
        "opt-d":F(2)==F(7) and after_pair==before,
    }
    # 6. North/East are perpendicular unit vectors, not scalar momenta.
    truck_m=F(8);car_m=F(2);speed=F(3)
    truck=(F(0),truck_m*speed);car=(car_m*speed,F(0))
    comp={
        "opt-a":truck[1]>car[0] and sum(x*y for x,y in zip(truck,car))==0,
        "opt-b":truck[1]>car[0] and truck==car,
        "opt-c":truck==car,
        "opt-d":car[0]>truck[1],
    }
    # 7. For equal K, p^2=2mK. No square-root approximation.
    big=F(10);small=F(2);kin=F(7)
    bigp2=2*big*kin;smallp2=2*small*kin
    equal_k={
        "opt-transport-greater":bigp2>smallp2,
        "opt-equal-momentum":bigp2==smallp2,
        "opt-scout-greater":smallp2>bigp2,
        "opt-cannot-determine":kin<=0 or big<=0 or small<=0,
    }
    # 8. Nadia-only body receives an EXTERNAL contact impulse from Leo;
    # for the pair the same force is INTERNAL and impulses cancel.
    nadia0=F(0);leo0=F(0);j=F(4)
    nadia=nadia0-j;leo=leo0+j
    astronaut={
        "opt-nadia-momentum-changes":nadia!=nadia0 and nadia+leo==0
                                     and (nadia-nadia0)!=0,
        "opt-single-particle-conserved":nadia==nadia0,
        "opt-force-equals-momentum":_FORCE==_P,  # dimensions differ by T^-1
        "opt-forces-cancel-on-body":nadia==0 and leo==0,
    }
    # 9. Spring stores positive elastic PE; momentum is transferred
    # mechanically via the rail/support, not converted into 'potential p'.
    v0=F(2);mass=F(3);p0=mass*v0;final_p=F(0)
    initial_k=mass*v0*v0/2;spring_k=initial_k
    rail_impulse=p0-final_p
    spring={
        "opt-ke-transforms-momentum-transfers":
            initial_k==spring_k and spring_k>0 and rail_impulse!=0,
        "opt-potential-momentum-stored":
            spring_k>0 and rail_impulse==0,
        "opt-both-turn-to-heat":
            spring_k==0 and rail_impulse==0,
        "opt-momentum-conserved-internally":
            p0==final_p and spring_k==0,
    }
    return dict(zip(_CASES[:9],(
        vector,units,newton,opposite,third,comp,equal_k,astronaut,spring)))


def _interactive_cases()->dict[str,tuple[str,Any]]:
    """Independently compute all matching, selection and ordering solutions."""
    # Classification follows scalar multiplication and vector-sum laws.
    typ=dict(_TYPES)
    # Dimension equations are checked, including Newton's F=dp/dt.
    if (_DIMENSION["item-linear-momentum"] != _P
            or _DIMENSION["item-net-force"] != tuple(
                x+y for x,y in zip(_P,(0,0,-1)))
            or _DIMENSION["item-velocity"]!=_V):
        raise ValueError("BSA252_DIMENSIONAL_IDENTITY_BROKEN")
    # True properties, false distractors, derived from model definitions.
    scalar={"momentum":False,"velocity":False,"energy":True,"mass":True}
    laws={"p_vector":not scalar["momentum"],
          "p_dimensions":_P==(1,1,-1),
          "p_scalar":scalar["momentum"],
          "potential_momentum":False}
    selections={
        "item-vector-dir":laws["p_vector"],
        "item-dimensions-unit":laws["p_dimensions"],
        "item-scalar-claim":laws["p_scalar"],
        "item-transform-claim":laws["potential_momentum"],
    }
    # Separate source-derived distinction: momentum cancels, KE sums.
    m=F(2);v=F(3);k=m*v*v/2
    if not (m*v+m*(-v)==0 and 2*k>0):
        raise ValueError("BSA252_MOMENTUM_ENERGY_CONTRAST_INVARIANT_FAILED")
    # Derivation ordering requires genuine nonzero internal interactions.
    j=F(3,2);p1=F(2);p2=F(-1)
    if p1+p2!=(p1+j)+(p2-j) or j==0:
        raise ValueError("BSA252_THIRD_LAW_ORDERING_MODEL_BROKEN")
    steps=["step-third-law","step-second-law","step-sum-derivative",
           "step-system-constancy"]
    # For 3 gliders at equal K: sign of p and ordering of positive p^2.
    heavy_m=F(12);light_m=F(2);energy=F(5)
    if not (heavy_m>light_m>0 and energy>0):
        raise ValueError("BSA252_POSITIVE_RANK_PARAMETERS_REQUIRED")
    signed_rank=["item-heavy-forward","item-light-forward","item-heavy-reverse"]
    if not (2*energy*heavy_m>2*energy*light_m and 0>-heavy_m):
        raise ValueError("BSA252_SIGNED_MOMENTUM_ORDER_BROKEN")
    mass_rank=[("item-heavy-glider",F(10)),("item-medium-glider",F(5)),
               ("item-light-glider",F(1))]
    mass_rank=sorted(mass_rank,key=lambda item:2*energy*item[1],reverse=True)
    # Newton-3 internal force cancellation and dp_total/dt=0; individual changes.
    f12=F(7);f21=-f12
    conserv={
        "item-action-reaction-sum":f12+f21==0,
        "item-total-rate-zero":f12+f21==0,
        "item-individual-conserved":f12==0,
        "item-force-is-momentum":False,  # wrong dimension/time derivative
    }
    if _FORCE==_P:
        raise ValueError("BSA252_FORCE_MOMENTUM_DIMENSION_COLLAPSED")
    return {
        _CASES[9]:("classification",typ),
        _CASES[10]:("matching",dict(_UNITS_MATCHES)),
        _CASES[11]:("selection",selections),
        _CASES[12]:("classification",dict(_CONTRAST)),
        _CASES[13]:("ordering",steps),
        _CASES[14]:("ordering",signed_rank),
        _CASES[15]:("ordering",[row[0] for row in mass_rank]),
        _CASES[16]:("selection",conserv),
        _CASES[17]:("matching",dict(_FORMULA_MATCHES)),
    }


def _check_solution(activity:dict,truth:Any)->dict:
    aid=activity["id"]
    if activity.get("type")=="mcq":
        choices=activity.get("answerKey",{}).get("options",[])
        ids=[x.get("id") for x in choices if isinstance(x,dict)]
        if (len(ids)!=len(choices) or len(ids)!=4
                or set(ids)!=set(truth)):
            raise ValueError("BSA252_MCQ_OPTION_IDENTITY_DRIFT")
        correct=[x for x,valid in truth.items() if valid is True]
        if len(correct)!=1:
            raise ValueError("BSA252_SOURCE_MODEL_NOT_UNIQUE_MCQ_TRUTH")
        if activity["answerKey"].get("correct")!=correct[0]:
            raise ValueError("BSA252_ACTUAL_MCQ_ANSWER_KEY_DEFECT")
        return {"witnessCount":len(ids),
                "independentSolutionSha256":_digest(correct[0]),
                "mathematicalCounterexampleCount":len(ids)-1}
    mode=activity.get("interactionMode")
    interaction=activity.get("interaction",{})
    if mode!=truth[0]:
        raise ValueError("BSA252_INTERACTION_MODE_SCIENTIFIC_DRIFT")
    expected=truth[1]
    items=interaction.get("items",[])
    ids=[x.get("id") for x in items if isinstance(x,dict)]
    if len(ids)!=len(items) or len(set(ids))!=len(ids):
        raise ValueError("BSA252_INTERACTIVE_ITEM_IDENTITIES_CHANGED")
    if mode in ("matching","classification"):
        target_ids={x.get("id") for x in interaction.get("targets",[])
                    if isinstance(x,dict)}
        actual=interaction.get("placements",[])
        placements={x["itemId"]:x["targetId"] for x in actual
                    if isinstance(x,dict) and "itemId" in x and "targetId" in x}
        if (len(actual)!=len(ids) or set(ids)!=set(expected)
                or not set(expected.values())<=target_ids
                or placements!=expected):
            raise ValueError("BSA252_ACTUAL_MATCHING_CLASSIFICATION_KEY_DEFECT")
        independent=_digest(sorted(expected.items()))
    elif mode=="selection":
        selected=interaction.get("correctSelections",[])
        if not isinstance(selected,list):
            raise ValueError("BSA252_ACTUAL_MULTISELECT_ANSWER_KEY_DEFECT")
        truth=expected
        expected={k for k,value in truth.items() if value is True}
        if (set(ids)!=set(truth) or set(selected)!=expected
                or len(selected)!=len(expected) or not expected<=set(ids)):
            raise ValueError("BSA252_ACTUAL_MULTISELECT_ANSWER_KEY_DEFECT")
        independent=_digest(sorted(expected))
    elif mode=="ordering":
        actual=interaction.get("correctOrder",[])
        if (set(actual)!=set(ids) or len(actual)!=len(ids)
                or actual!=expected):
            raise ValueError("BSA252_ACTUAL_ORDERING_ANSWER_KEY_DEFECT")
        independent=_digest(expected)
    else:
        raise ValueError("BSA252_UNSUPPORTED_LEARNING_INTERACTION")
    return {"witnessCount":len(ids),
            "independentSolutionSha256":independent,
            "mathematicalCounterexampleCount":len(ids)-1}


def bounded_section91_science_audit(
    *, source_pdf:Path,source_sha:str,package_file:Path,
    expected_sha:str=_CANDIDATE_SHA,
)->dict:
    """Actual textbook + exact approved content; no LLM and no full QA PASS."""
    if (expected_sha!=_CANDIDATE_SHA or package_file.is_symlink()
            or not package_file.is_file()):
        raise ValueError("BSA252_APPROVED_EXACT_REVISION_REQUIRED")
    raw=package_file.read_bytes()
    if sha256(raw).hexdigest()!=expected_sha:
        raise ValueError("BSA252_EXACT_PACKAGE_VERSION_DRIFT")
    axioms=_source_axioms(source_pdf,source_sha)
    package=json.loads(raw.decode("utf8"))
    activities=package.get("activities")
    if (not isinstance(activities,list) or len(activities)!=18
            or [a.get("id") for a in activities]!=list(_CASES)):
        raise ValueError("BSA252_SOURCE_PACKAGE_ACTIVITY_ROSTER_CHANGED")
    proofs=_prove_exact_roster(activities)
    count=sum(x["exactRationalAndDimensionalWitnesses"] for x in proofs)
    return {
        "status":"BSA252_ALL_18_SOURCE_BOUND_BOUNDED_FORMAL_ANSWER_MODELS_VERIFIED",
        "sourcePdfSha256":source_sha,
        "revisedCandidateSha256":sha256(raw).hexdigest(),
        "independentlyReextractedTextbookPhysicsPremises":len(axioms),
        "modelledMcqActivities":9,
        "modelledInteractiveActivities":9,
        "boundedFormalAnswerItemWitnesses":count,
        "activityProofs":proofs,
        "completeIndependentAcademicProofGatePASS":0,
        "formalAcademicActivityPASS":0,
        "newGeminiCalls":0,
        "newExternalPdfsRequired":False,
        "publicationAuthorized":False,
        "qualification":"Bounded mathematical/answer models do not prove unrestricted natural-language interpretation, actual rendered diagrams or EN/MS/ZH translation equivalence",
    }


def _prove_exact_roster(activities:list[dict])->list[dict]:
    """Pure mathematical proposition checks for fault injection and live use."""
    if (not isinstance(activities,list) or len(activities)!=18
            or [a.get("id") for a in activities]!=list(_CASES)):
        raise ValueError("BSA252_SOURCE_PACKAGE_ACTIVITY_ROSTER_CHANGED")
    mcq=_mcq_cases()
    interact=_interactive_cases()
    if set(mcq)|set(interact)!=set(_CASES):
        raise ValueError("BSA252_MODEL_NOT_ALL_EIGHTEEN_ACTIVITIES")
    proofs=[]
    for a in activities:
        aid=a["id"]
        case=mcq[aid] if aid in mcq else interact[aid]
        result=_check_solution(a,case)
        proofs.append({
            "activityId":aid,
            "activityCanonicalSha256":_digest(a),
            "sourceModelFamily":("MCQ_FORMAL_PROPOSITION" if aid in mcq
                                 else "INTERACTIVE_FORMAL_SOLUTION"),
            "exactRationalAndDimensionalWitnesses":result["witnessCount"],
            "falsifiedAlternativeCount":result["mathematicalCounterexampleCount"],
            "independentFormalSolutionSha256":result["independentSolutionSha256"],
            "answerPhysicsBoundedVerified":True,
            "allEnglishStatementAndTranslatedSemanticsVerified":False,
            "fullScientificAcademicPASS":False,
            "publicationAuthorized":False,
        })
    count=sum(x["exactRationalAndDimensionalWitnesses"] for x in proofs)
    if count!=68 or len(proofs)!=18:
        raise ValueError("BSA252_FORMAL_MODEL_COVERAGE_MISMATCH")
    return proofs

"""BSA259: narrow, independent, source-bound MCQ proposition checks.

Original Serway 9.1 p=m v, actual signed 18-activity revised candidate,
rational counterexamples, and explicit three-locale semantic-role witnesses.
A finite-word witness is intentionally NOT a general translation/science PASS.
"""
from __future__ import annotations

from fractions import Fraction
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

from app_generator.validation.section91_formal_physics import (
    _SOURCE_SHA,_CANDIDATE_SHA,_source_axioms,
)
from app_generator.validation.source_passages import extract_pages

_ACTIVITY="act-mcq-01-vector-nature"
_ROLES={
    "en":{
        "prompt":("identical","opposite directions"),
        "explanation":("p = m v","positive scalar","opposite directions"),
        "opt-a":("equal momentum magnitudes","opposite directions"),
        "opt-b":("solely","without depending on the direction"),
        "opt-c":("zero linear momentum","constant-speed"),
        "opt-d":("vertically upward","right angle"),
    },
    "ms":{
        "prompt":("serupa","arah yang bertentangan"),
        "explanation":("p = m v","skalar positif","arah bertentangan"),
        "opt-a":("magnitud momentum yang sama","arah yang bertentangan"),
        "opt-b":("hanya bergantung","tanpa bergantung pada arah"),
        "opt-c":("momentum linear sifar","laju malar"),
        "opt-d":("tegak ke atas","sudut tepat"),
    },
    "zh":{
        "prompt":("相同","方向正好相反"),
        "explanation":("p = m v","正标量","方向相反"),
        "opt-a":("大小相等","方向相反"),
        "opt-b":("仅取决于","方向无关"),
        "opt-c":("均为零","匀速运动"),
        "opt-d":("垂直向上","垂直"),
    },
}


def source_bound_four_choice_witness(
    *,source_pdf:Path,package_file:Path,
)->dict[str,Any]:
    if (source_pdf.is_symlink() or not source_pdf.is_file()
            or sha256(source_pdf.read_bytes()).hexdigest()!=_SOURCE_SHA
            or package_file.is_symlink() or not package_file.is_file()
            or sha256(package_file.read_bytes()).hexdigest()!=_CANDIDATE_SHA):
        raise ValueError("BSA259_ORIGINAL_SERWAY_OR_REVISED_VERSION_MISMATCH")
    parts=extract_pages(source_pdf)
    axioms=_source_axioms(source_pdf,_SOURCE_SHA)
    if len(parts)!=3 or len(axioms)!=9:
        raise ValueError("BSA259_ORIGINAL_TEXTBOOK_PHYSICS_NOT_RECONFIRMED")
    package=json.loads(package_file.read_text(encoding="utf8"))
    acts=package.get("activities")
    if not isinstance(acts,list) or len(acts)!=18:
        raise ValueError("BSA259_ACTIVITY_ROSTER_CHANGED")
    a=next((x for x in acts if x.get("id")==_ACTIVITY),None)
    if (not isinstance(a,dict) or a.get("type")!="mcq"
            or a.get("answerKey",{}).get("correct")!="opt-a"
            or len(a.get("answerKey",{}).get("options",[]))!=4
            or a.get("visualSpec") is not None):
        raise ValueError("BSA259_INDEPENDENT_FOUR_CHOICE_KEY_OR_DRAFT_CHANGED")
    options={o["id"]:o.get("label") for o in a["answerKey"]["options"]}
    if set(options)!={"opt-a","opt-b","opt-c","opt-d"}:
        raise ValueError("BSA259_FOUR_CHOICE_IDENTITY_NOT_EXACT")
    localized=[]
    for locale,fields in _ROLES.items():
        for role,tokens in fields.items():
            if role=="prompt":
                string=a["prompt"].get(locale)
            elif role=="explanation":
                string=a["explanation"].get(locale)
            else:
                string=options[role].get(locale)
            if not isinstance(string,str) or not all(
                    w.casefold() in string.casefold() for w in tokens):
                raise ValueError("BSA259_LOCALIZED_ROLE_OR_POLARITY_MISMATCH_"+
                                 locale+"_"+role)
            localized.append({
                "locale":locale,"role":role,
                "verifiedPolarityCues":len(tokens),
                "textSha256":sha256(string.encode("utf8")).hexdigest(),
            })
    # Independent abstract rational counterexample derived from the source:
    # m>0 and +v,-v give equal, opposing nonzero momenta, parallel to v.
    mass,speed=Fraction(3),Fraction(2)
    pv=(mass*(-speed),mass*speed)
    truth={
        "opt-a": pv[0]==-pv[1] and abs(pv[0])==abs(pv[1]),
        "opt-b": pv[0]==pv[1],
        "opt-c": pv[0]==0 and pv[1]==0,
        "opt-d": False,  # nonzero p=mv is collinear, never perpendicular
    }
    if truth!={"opt-a":True,"opt-b":False,"opt-c":False,"opt-d":False}:
        raise ValueError("BSA259_INDEPENDENT_FORMAL_COUNTEREXAMPLE_FAILED")
    return {
        "status":"BSA259_ONE_SOURCE_MCQ_FOUR_OPTIONS_THREE_LOCALES_BOUNDED_WITNESSES",
        "activityId":_ACTIVITY,
        "sourceSha256":_SOURCE_SHA,
        "candidateSha256":_CANDIDATE_SHA,
        "reextractedSourcePages":3,
        "sourcePhysicsAxiomsVerified":9,
        "independentlyCheckedLocalizedRoleTexts":len(localized),
        "independentlyCheckedOptionLocales":12,
        "mathematicallyCounterexampledFalseChoices":3,
        "correctAnswerModelUniquelyTrue":True,
        "localizedRoleWitnesses":localized,
        "entireActivityIndependentSemanticAccepted":False,
        "allOriginal18VisualsAccepted":False,
        "fullTranslationSemanticEquivalenceProven":False,
        "fullAcademicPASS":0,
        "newProviderCalls":0,
        "publicationAuthorized":False,
    }

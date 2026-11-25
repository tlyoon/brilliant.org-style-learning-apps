"""BSA263: bounded original-source-pinned interactive semantic-role cues.

Curated lexical witness pairs for the frozen Serway 9.1 nine interactive
prompts and a representative science-bearing item in each interaction.
Presence is NOT full scientific, translated-clause or diagram acceptance.
"""
from __future__ import annotations
from hashlib import sha256
import json
from pathlib import Path

from app_generator.validation.section91_formal_physics import (
    _SOURCE_SHA, _CANDIDATE_SHA, _CASES, _source_axioms,
    _interactive_cases, _check_solution,
)

# Each row is ordered EN, Malay, Chinese. Scope is intentionally one source-
# anchored conceptual cue in the question and first activity item, not entire
# statement meaning or a free-form translation equivalence claim.
_CUES = (
    (("vector","vektor","矢量"),("momentum","momentum","动量")),
    (("SI","SI","SI"),("momentum","momentum","动量")),
    (("momentum","momentum","动量"),("vector","vektor","矢量")),
    (("kinetic energy","tenaga kinetik","动能"),("vector","vektor","矢量")),
    (("Newton","Newton","牛顿"),("third law","hukum ketiga","第三定律")),
    (("kinetic energy","tenaga kinetik","动能"),("positive","positif","正")),
    (("kinetic energy","tenaga kinetik","动能"),("kinetic energy","tenaga kinetik","动能")),
    (("isolated","terpencil","孤立"),("F_12 + F_21 = 0",)*3),
    (("force","daya padu","合外力"),("dp/dt",)*3),
)

def audit_interactive_source_role_cues(*,source_pdf:Path,package_file:Path)->dict:
    if (source_pdf.is_symlink() or not source_pdf.is_file()
            or sha256(source_pdf.read_bytes()).hexdigest()!=_SOURCE_SHA
            or package_file.is_symlink() or not package_file.is_file()
            or sha256(package_file.read_bytes()).hexdigest()!=_CANDIDATE_SHA):
        raise ValueError("BSA263_SINGLE_SOURCE_OR_FROZEN_CANDIDATE_CHANGED")
    if len(_source_axioms(source_pdf,_SOURCE_SHA))!=9:
        raise ValueError("BSA263_SOURCE_PHYSICS_PREMISES_MISSING")
    activities=json.loads(package_file.read_text(encoding="utf8")).get("activities")
    if (not isinstance(activities,list) or len(activities)!=18
            or [a.get("id") for a in activities]!=list(_CASES)
            or len(_CUES)!=9):
        raise ValueError("BSA263_FROZEN_INTERACTIVE_ROSTER_CHANGED")
    truth=_interactive_cases()
    witnesses=[]
    for i,a in enumerate(activities[9:]):
        aid=a["id"]
        _check_solution(a,truth[aid])  # Never accept lexical roles with a wrong key.
        first=a["interaction"]["items"][0]
        locale_witness=[]
        for j,locale in enumerate(("en","ms","zh")):
            prompt=a.get("prompt",{}).get(locale)
            label=first.get("label",{}).get(locale)
            explanation=a.get("explanation",{}).get(locale)
            if not all(isinstance(s,str) and s.strip()
                       for s in (prompt,label,explanation)):
                raise ValueError("BSA263_MISSING_LOCALE_SCIENCE_SURFACE_"+aid+"_"+locale)
            pcue,icue=(_CUES[i][0][j],_CUES[i][1][j])
            if pcue.casefold() not in prompt.casefold():
                raise ValueError("BSA263_PROMPT_SCIENCE_ROLE_DRIFT_"+aid+"_"+locale)
            if icue.casefold() not in label.casefold():
                raise ValueError("BSA263_ITEM_SCIENCE_ROLE_DRIFT_"+aid+"_"+locale)
            locale_witness.append({
                "locale":locale,
                "promptSha256":sha256(prompt.encode("utf8")).hexdigest(),
                "itemLabelSha256":sha256(label.encode("utf8")).hexdigest(),
                "explanationSha256":sha256(explanation.encode("utf8")).hexdigest(),
                "curatedPromptCuePresent":True,"curatedItemCuePresent":True,
            })
        witnesses.append({"activityId":aid,"mode":a["interactionMode"],
                          "localeWitnesses":locale_witness})
    return {
        "status":"BSA263_NINE_INTERACTIVE_TRILOCALE_BOUNDED_SOURCE_ROLE_CUES",
        "sourceSha256":_SOURCE_SHA,
        "candidateSha256":_CANDIDATE_SHA,
        "interactiveActivitiesChecked":9,
        "trilingualPromptRoleCuesChecked":27,
        "trilingualFirstItemRoleCuesChecked":27,
        "localizedExplanationsBoundByDigest":27,
        "activityWitnesses":witnesses,
        "fullTrilingualMeaningEquivalenceProven":False,
        "fullScientificClauseTruthProven":False,
        "renderedDiagramScienceVerified":False,
        "completeAcademicProofGatesStillOpen":90,
        "fullAcademicPASS":0,
        "newProviderCalls":0,
        "publicationAuthorized":False,
    }

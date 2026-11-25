"""BSA257: single original Serway Section 9.1 source-bound velocity-vector visual.

Private, never updates the frozen 18-activity candidate or releases the app.
The abstract circle is explicitly a pedagogical symbol, not a textbook figure.
"""
from __future__ import annotations
from fractions import Fraction
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

from app_generator.runtime.v3_selected_textbook_scientific_provenance import (
    _source_activity_anchors,
)
from app_generator.validation.section91_formal_physics import (
    _SOURCE_SHA, _CANDIDATE_SHA, _source_axioms,
)
from app_generator.validation.source_passages import extract_pages

_TARGET="act-mcq-01-vector-nature"
_TEMPLATE="mechanics.opposite_velocity_pair_1d"


def _digest(data:Any)->str:
    return sha256(json.dumps(
        data,sort_keys=True,ensure_ascii=False,
        separators=(",",":")).encode("utf8")).hexdigest()


def _labels(a:str,b:str,c:str)->dict[str,str]:
    return {"en":a,"ms":b,"zh":c}


def make_opposite_velocity_private_visual(
    *,source_pdf:Path,source_sha:str,package_file:Path,
)->dict[str,Any]:
    if (source_sha!=_SOURCE_SHA or source_pdf.is_symlink()
            or not source_pdf.is_file()
            or sha256(source_pdf.read_bytes()).hexdigest()!=_SOURCE_SHA
            or package_file.is_symlink() or not package_file.is_file()
            or sha256(package_file.read_bytes()).hexdigest()!=_CANDIDATE_SHA):
        raise ValueError("BSA257_SOURCE_OR_FROZEN_CANDIDATE_SHA_DRIFT")
    original=json.loads(package_file.read_text(encoding="utf8"))
    acts=original.get("activities")
    if not isinstance(acts,list) or len(acts)!=18:
        raise ValueError("BSA257_FROZEN_ORIGINAL_ACTIVITY_ROSTER_MISSING")
    activity=next((a for a in acts if a.get("id")==_TARGET),None)
    if not isinstance(activity,dict) or activity.get("type")!="mcq":
        raise ValueError("BSA257_SELECTED_ACTIVITY_CHANGED")
    if activity.get("visualSpec") is not None:
        raise ValueError("BSA257_WOULD_REPLACE_EXISTING_ACCEPTED_VISUAL")
    # This question itself explicitly gives the two-identical-drone,
    # equal-speed, opposite-direction precondition in each locale.
    en=activity["prompt"]["en"].casefold()
    ms=activity["prompt"]["ms"].casefold()
    zh=activity["prompt"]["zh"]
    if (not all(s in en for s in ("identical","same constant speed",
                                   "opposite directions"))
            or not all(s in ms for s in ("serupa","laju malar yang sama",
                                         "arah yang bertentangan"))
            or not all(s in zh for s in ("相同","方向正好相反"))):
        raise ValueError("BSA257_OPPOSING_VELOCITY_SCENARIO_MISMATCH")
    axioms=_source_axioms(source_pdf,source_sha)
    pages=extract_pages(source_pdf)
    source=_source_activity_anchors(pages=pages,activities=acts)
    row=next(x for x in source if x["activityId"]==_TARGET)
    if (len(axioms)!=9 or len(pages)!=3
            or row["uniquePagePassageLocated"] is not True):
        raise ValueError("BSA257_SOURCE_GROUNDING_UNVERIFIED")
    # Independent exact-rational witness (not original measured data).
    m=Fraction(3);speed=Fraction(2)
    momenta=(m*(-speed),m*speed)
    if not (momenta[0]==-momenta[1] and sum(momenta)==0):
        raise ValueError("BSA257_VECTOR_PHYSICS_INTERNAL_FAILURE")
    spec={
        "schemaVersion":"1.0","mode":"vector_diagram",
        "template":_TEMPLATE,
        "semanticParameters":{"mass_relation":"equal",
                              "speed_relation":"equal",
                              "track_orientation":"horizontal"},
        "entities":[
            {"id":"drone-a","kind":"body",
             "label":_labels("Drone A","Dron A","无人机 A"),
             "properties":{"relativeMass":"equal"}},
            {"id":"drone-b","kind":"body",
             "label":_labels("Drone B","Dron B","无人机 B"),
             "properties":{"relativeMass":"equal"}},
        ],
        "vectors":[
            {"id":"velocity-a","entityId":"drone-a",
             "quantity":"velocity","direction":"left",
             "relativeMagnitude":0.8,
             "label":_labels("Velocity A","Halaju A","速度 A")},
            {"id":"velocity-b","entityId":"drone-b",
             "quantity":"velocity","direction":"right",
             "relativeMagnitude":0.8,
             "label":_labels("Velocity B","Halaju B","速度 B")},
        ],
        "accessibility":{
            "description":_labels(
                "Two identical objects with equal speeds moving in opposite directions; arrows indicate velocities, not momentum.",
                "Dua objek serupa bergerak pada laju yang sama dalam arah bertentangan; anak panah menunjukkan halaju, bukan momentum.",
                "两个相同物体以相同速率朝相反方向运动；箭头表示速度，而不是动量。"),
            "colorIndependent":True,
            "reducedMotionStrategy":"not-applicable",
        },
        "grounding":[
            {"factId":"linear-momentum-is-mass-times-velocity",
             "origin":"source_fact",
             "appliesTo":["drone-a","drone-b"]},
            {"factId":"abstract-markers-for-generated-opposite-drone-scenario",
             "origin":"pedagogical_simplification",
             "appliesTo":["drone-a","drone-b"]},
        ],
        "fallback":{"mode":"structured_interaction",
                    "reason":"An accessible text-only question remains available."},
        "validation":{"answerRelevantIds":["velocity-a","velocity-b"],
                      "forbidAnswerLeakage":True},
        "invariants":[
            {"id":"equal-velocity-magnitudes","kind":"equal",
             "references":["velocity-a","velocity-b"]},
            {"id":"opposite-velocity-directions","kind":"opposite",
             "references":["velocity-a","velocity-b"]},
        ],
    }
    if (len(spec["vectors"])!=2 or
            {v["quantity"] for v in spec["vectors"]}!={"velocity"} or
            spec["vectors"][0]["relativeMagnitude"]!=
                spec["vectors"][1]["relativeMagnitude"] or
            spec["vectors"][0]["direction"]==
                spec["vectors"][1]["direction"]):
        raise ValueError("BSA257_VECTOR_SCENE_NOT_TRUE")
    return {
        "status":"BSA257_PRIVATE_ONE_SOURCE_GROUNDED_VISUAL_DRAFT_NO_RELEASE",
        "sourceSha256":source_sha,
        "candidateSha256":_CANDIDATE_SHA,
        "activityId":_TARGET,
        "activitySha256":_digest(activity),
        "originalSourcePhysicalPdfPage":row["physicalPage"],
        "originalSourcePassageSha256":row["passageSha256"],
        "independentSourcePhysicsAxiomCount":len(axioms),
        "boundedRationalPhysicalWitness":True,
        "specSha256":_digest(spec),
        "spec":spec,
        "isOriginalTextbookFigure":False,
        "isReleasedIntoOriginalPackage":False,
        "completeScientificMeaningProven":False,
        "completeEN_MS_ZHSemanticsProven":False,
        "browserRenderedPixelScienceProven":False,
        "fullAcademicPASS":0,
        "publicationAuthorized":False,
        "newProviderCalls":0,
        "additionalPdfsRequired":False,
    }

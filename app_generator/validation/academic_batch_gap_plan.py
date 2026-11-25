"""Exact-version private review-work queue across an entire original-source pack.

Only verifies alignment of previously independently verified receipts. Never
treats source locations or bounded mathematical witnesses as full academic PASS.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app_generator.validation.activity_evidence_dossier import reconcile_activity_evidence
from app_generator.validation.impulse_qualifier_repair import ACTIVITY_ID

def plan_exact_academic_batch(
    *, package_file:Path, source_pdf:Path, matrix_file:Path, physics_file:Path,
    expected_count:int=18, first_activity_id:str=ACTIVITY_ID,
) -> dict[str,Any]:
    if type(expected_count) is not int or expected_count<1 or expected_count>100:
        raise ValueError("bounded original-source activity count required")
    data=json.loads(package_file.read_text(encoding="utf-8"))
    activities=data.get("activities",[])
    if not isinstance(activities,list) or len(activities)!=expected_count:
        raise ValueError("activity count differs from expected authoritative package")
    ids=[a.get("id") if isinstance(a,dict) else None for a in activities]
    if any(not isinstance(a,str) or not a for a in ids) or len(set(ids))!=len(ids):
        raise ValueError("duplicate or absent academic activity ID")
    if first_activity_id not in ids:
        raise ValueError("requested original-source pilot is absent")
    planned=[]
    # Exact-version dossier verification checks ALL activity hashes on every
    # receipt, preventing selective source-evidence omissions.
    for aid in [first_activity_id]+[x for x in ids if x!=first_activity_id]:
        dossier=reconcile_activity_evidence(
            package_file=package_file,source_pdf=source_pdf,
            matrix_file=matrix_file,physics_file=physics_file,
            activity_id=aid,
        )
        if dossier["fullAcademicPass"] is not False or dossier["publicationAuthorized"] is not False:
            raise ValueError("private evidence must never preapprove content")
        missing=[g for g,status in dossier["gates"].items() if status!="PASS"]
        planned.append({
            "priority":len(planned)+1,
            "activityId":aid,
            "activitySha256":dossier["activitySha256"],
            "sourceLocationVerifiedInMatrix":dossier["sourceLocationVerifiedInMatrix"],
            "boundedPhysicsReceiptMatched":dossier["boundedPhysicsReceiptMatched"],
            "sourcePages":dossier["sourcePages"],
            "academicQA":dossier["academicQA"],
            "outstandingGates":missing,
            "nextAction":dossier["nextAction"],
            "requiresIndependentSemanticReview":True,
            "requiresFreshRenderedVisualReview":True,
            "fullAcademicPass":False,
            "publicationAuthorized":False,
        })
    sample=reconcile_activity_evidence(
        package_file=package_file,source_pdf=source_pdf,
        matrix_file=matrix_file,physics_file=physics_file,
        activity_id=first_activity_id,
    )
    statuses={kind:sum(a["academicQA"]==kind for a in planned)
              for kind in ("PASS","FAIL","REVIEW_REQUIRED")}
    next_counts={kind:sum(a["nextAction"]==kind for a in planned)
                 for kind in ("AUTO_REPAIR","AUTO_SOURCE_CHECK",
                              "AUTO_INDEPENDENT_SEMANTIC_VISUAL_REVIEW")}
    return {
        "packageSha256":sample["packageSha256"],
        "sourceSha256":sample["sourceSha256"],
        "activityCount":len(planned),
        "verifiedSourceLocationReceipts":sum(a["sourceLocationVerifiedInMatrix"] for a in planned),
        "matchedBoundedPhysicsReceipts":sum(a["boundedPhysicsReceiptMatched"] for a in planned),
        "fullAcademicPassCount":0,
        "academicCounts":statuses,
        "nextActionCounts":next_counts,
        "prioritizedActivities":planned,
        "sourceLocationsIndependentlyExtractedThisRun":False,
        "completeTrilingualSemanticsVerified":False,
        "renderedVisualScientificallyVerified":False,
        "humanAcademicApprovalRequired":False,
        "academicQA":"REVIEW_REQUIRED",
        "publicationAuthorized":False,
    }
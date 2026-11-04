"""Recheck bounded Section 9.4 physics models across exact-content revisions.

Carry forward genuine deterministic witnesses ONLY for byte-equivalent
academic activities, and independently recheck explicitly corrected v3.
Never promote partial mathematical identities into full academic PASS.
"""
from __future__ import annotations
from hashlib import sha256
import json
from pathlib import Path
from typing import Any, Callable

from app_generator.validation.interactive_physics import audit_interaction_models
from app_generator.validation.physics_proofs import audit_proofs
from app_generator.validation.impulse_v3_audit import audit_v3

def digest(v:Any)->str:
    return sha256(json.dumps(v,sort_keys=True,ensure_ascii=False,
                             separators=(",",":")).encode("utf-8")).hexdigest()

def reverify_bounded_physics(
    *, prior_package:Path, revised_package:Path, source_pdf:Path,
    source_sha256:str, mcq_receipts:Path, interaction_receipts:Path,
    parent_v2_package:Path, parent_v2_review:Path, revised_v3_review:Path,
    mcq_auditor:Callable[...,dict[str,Any]]=audit_proofs,
    interaction_auditor:Callable[...,dict[str,Any]]=audit_interaction_models,
    revision_auditor:Callable[...,dict[str,Any]]=audit_v3,
)->dict[str,Any]:
    if sha256(source_pdf.read_bytes()).hexdigest()!=source_sha256:
        raise ValueError("controlled textbook PDF has changed")
    old=json.loads(prior_package.read_text(encoding="utf-8"))
    revised_raw=revised_package.read_bytes()
    new=json.loads(revised_raw.decode("utf-8"))
    old_acts=old.get("activities",[])
    new_acts=new.get("activities",[])
    if not isinstance(old_acts,list) or not isinstance(new_acts,list) or not new_acts:
        raise ValueError("invalid physics package activities")
    prior={a["id"]:a for a in old_acts if isinstance(a,dict) and isinstance(a.get("id"),str)}
    updated={a["id"]:a for a in new_acts if isinstance(a,dict) and isinstance(a.get("id"),str)}
    if len(prior)!=len(old_acts) or len(updated)!=len(new_acts) or set(prior)!=set(updated):
        raise ValueError("activity set changed across physics verification")
    m=mcq_auditor(old,source_pdf,source_sha256,
                  json.loads(mcq_receipts.read_text(encoding="utf-8")))
    i=interaction_auditor(old,source_pdf,source_sha256,
                          json.loads(interaction_receipts.read_text(encoding="utf-8")))
    v=revision_auditor(revised_package,revised_v3_review,
                       parent_v2_package,parent_v2_review,source_pdf)
    if (m.get("sourceSha256")!=source_sha256 or
        i.get("sourceSha256")!=source_sha256 or
        v.get("sourceSha256")!=source_sha256 or
        m.get("packageCanonicalSha256")!=digest(old) or
        i.get("packageCanonicalSha256")!=digest(old) or
        v.get("candidateFileSha256")!=sha256(revised_raw).hexdigest()):
        raise ValueError("source/parent/candidate witness identity mismatch")
    old_results=m.get("proofs",[])+i.get("results",[])
    old_by_id={}
    for item in old_results:
        aid=item.get("activityId")
        if aid not in prior or aid in old_by_id:
            raise ValueError("missing/duplicate original bounded physics proof")
        old_by_id[aid]=item
    if set(old_by_id)!=set(prior):
        raise ValueError("prior bounded proof coverage incomplete")
    changed=[aid for aid in sorted(updated) if digest(prior[aid])!=digest(updated[aid])]
    if changed!=[v.get("activityId")]:
        raise ValueError("new/changed activity is not exact independently reviewed correction")
    if (v.get("boundedOptionsVerified")!=5 or v.get("optionReviewsRequired")!=0 or
        v.get("fullAcademicActivitiesPassed")!=0 or v.get("publicationAuthorized") is not False):
        raise ValueError("revised bounded physics verification incomplete")
    results=[]
    for aid in sorted(updated):
        previous=old_by_id[aid]
        if aid==changed[0]:
            status="REVISED_BOUNDED_PHYSICS_VERIFIED"
            evidence="source-bound v3 reconstruction, finite rational counterexamples and five localized option checks"
        else:
            if previous.get("status") not in (
                "BOUNDED_PROPOSITION_VERIFIED","BOUNDED_INTERACTION_MODEL_VERIFIED",
            ):
                raise ValueError("unchanged activity has unresolved original physics witness")
            status="UNCHANGED_BOUNDED_PHYSICS_REVERIFIED"
            evidence="exact unchanged activity digest and independently recomputed prior rational physics model"
        results.append({
            "activityId":aid,"status":status,
            "priorActivitySha256":digest(prior[aid]),
            "currentActivitySha256":digest(updated[aid]),
            "activityChanged":aid in changed,
            "proofKind":"bounded_exact_physics_only",
            "proofDetail":evidence,
            "fullAcademicPass":False,
            "publicationAuthorized":False,
        })
    return {
        "priorPackageCanonicalSha256":digest(old),
        "revisedPackageSha256":sha256(revised_raw).hexdigest(),
        "revisedPackageCanonicalSha256":digest(new),
        "sourceSha256":source_sha256,
        "activityCount":len(results),
        "unchangedBoundedVerified":len(results)-len(changed),
        "revisedBoundedVerified":len(changed),
        "boundedPropositionsVerified":len(results),
        "fullyAcademicallyApproved":0,
        "changedActivityIds":changed,
        "activities":results,
        "academicQA":"REVIEW_REQUIRED",
        "humanReviewRequired":False,
        "publicationAuthorized":False,
        "qualification":"Finite source-bound mathematical witness is not full answer, distractor, language or scientific visual verification",
    }

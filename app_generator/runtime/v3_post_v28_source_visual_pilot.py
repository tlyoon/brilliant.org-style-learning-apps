"""BSA257: immutable, private, exact-source visual draft and DOM geometry witness.

This stage follows V28 autonomously, NEVER overwrites original candidate,
never fetches an outside PDF, calls a model, merges a PR, or deploys a page.
"""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import subprocess
from typing import Any

from app_generator.runtime.v3_five_stage_completion import _hash
from app_generator.runtime.v3_native_release_adapter import _v6_checkpoint
from app_generator.runtime.v3_public_bundle_handoff import _trusted_json
from app_generator.runtime.v3_public_nonmerging_draft_pr import _preflight
from app_generator.runtime.v3_revised_source_proof_rebinding import _signed
from app_generator.runtime.v3_post_v27_five_proof_producers import (
    _V28, _STATUS28,
)
from app_generator.runtime.v3_selected_textbook_scientific_provenance import (
    _SOURCE_BINDING,
)
from app_generator.runtime.v3_exact_revised_review_reconciliation import (
    _CANDIDATE,
)
from app_generator.validation.section91_formal_physics import (
    _SOURCE_SHA, _CANDIDATE_SHA,
)
from app_generator.validation.section91_private_velocity_visual import (
    make_opposite_velocity_private_visual,
)

_V29_PRE="V29_SOURCE_BOUND_VISUAL_PRE_CALL.json"
_V29_DRAFT="V29_PRIVATE_ONE_SOURCE_VELOCITY_VISUAL_DRAFT.json"
_V29_GEOMETRY="V29_ACTUAL_DOM_SVG_GEOMETRY_RESULT.json"
_V29="V29_PRIVATE_SOURCE_VISUAL_RENDERER_VERIFIED_NO_ACADEMIC_PASS.json"
_STATUS29="V29_ACTUAL_SOURCE_BOUND_PRIVATE_VECTOR_RENDERER_RECHECKED_NO_PUBLICATION"


def run_post_v28_private_visual_pilot(
    repo:Path, private:Path, ready:dict[str,Any],
    v9:dict, v11:dict, v12:dict, v28_result:dict,
)->dict[str,Any]:
    folder,_,_,_,_=_preflight(repo,private,ready,v9,v11,v12)
    prior=_signed(folder,_V28,ready)
    if (v28_result!=prior or prior.get("status")!=_STATUS28
            or prior.get("realSourcePageAnchors")!=18
            or prior.get("completeAcademicProofGatesStillOpen")!=90
            or prior.get("independentMeaningMicroproofsPending")!=429
            or prior.get("formalAcademicPASS")!=0
            or prior.get("newProviderCalls")!=0
            or prior.get("publicationAuthorized") is not False
            or prior.get("sourceSha256")!=_SOURCE_SHA
            or prior.get("revisedCandidateSha256")!=_CANDIDATE_SHA):
        raise ValueError("BSA257_GENUINE_SIGNED_V28_SOURCE_PREDECESSOR_REQUIRED")
    binding=_trusted_json(private/_SOURCE_BINDING)
    pdf=Path(binding["sourcePdf"])
    root=Path(binding["sourceRoot"])
    if (binding.get("integritySha256")!=_hash({
            k:v for k,v in binding.items() if k!="integritySha256"})
            or binding.get("contract")!="BOSLA_SELECTED_SERWAY_TEXTBOOK_LOCAL_BINDING_V1"
            or binding.get("section")!="9.1"
            or binding.get("sourceSha256")!=_SOURCE_SHA
            or binding.get("sourcePdfUploaded") is not False
            or binding.get("externalFallbackAllowed") is not False
            or pdf.is_symlink() or not pdf.is_file()
            or pdf.resolve()!= (root/"9"/"9.1"/"source.pdf").resolve()
            or pdf.resolve().is_relative_to(repo.resolve())
            or sha256(pdf.read_bytes()).hexdigest()!=_SOURCE_SHA):
        raise ValueError("BSA257_ORIGINAL_TEXTBOOK_SOURCE_BINDING_FAILED")
    candidate=folder/_CANDIDATE
    if (candidate.is_symlink() or not candidate.is_file()
            or sha256(candidate.read_bytes()).hexdigest()!=_CANDIDATE_SHA):
        raise ValueError("BSA257_IMMUTABLE_REVISED_CANDIDATE_CHANGED")
    identity={
        "gitHead":ready["gitHead"],
        "proposalSha256":ready["proposalSha256"],
        "sourceV28ReceiptSha256":prior["integritySha256"],
        "sourceSha256":_SOURCE_SHA,
        "revisedCandidateSha256":_CANDIDATE_SHA,
    }
    _v6_checkpoint(folder/_V29_PRE,{
        **identity,"status":"V29_ONE_SELECTED_TEXTBOOK_VISUAL_PRE_CALL",
        "externalSourcePdfsAllowed":False,"modelCallsAllowed":False,
        "publicationAuthorized":False,
    })
    draft=make_opposite_velocity_private_visual(
        source_pdf=pdf,source_sha=_SOURCE_SHA,package_file=candidate)
    if (draft.get("fullAcademicPASS")!=0
            or draft.get("completeEN_MS_ZHSemanticsProven") is not False
            or draft.get("browserRenderedPixelScienceProven") is not False
            or draft.get("publicationAuthorized") is not False
            or draft.get("spec",{}).get("template")!="mechanics.opposite_velocity_pair_1d"
            or draft.get("activityId")!="act-mcq-01-vector-nature"
            or draft.get("newProviderCalls")!=0):
        raise ValueError("BSA257_PRIVATE_DRAFT_FALSELY_PROMOTED")
    saved=_v6_checkpoint(folder/_V29_DRAFT,{**identity,**draft})
    if (folder/_V29_DRAFT).stat().st_size>=12000:
        raise ValueError("BSA257_VISUAL_DRAFT_EXCEEDS_12KB_LIMIT")
    # Actually instantiate *the same production SVG renderer* using local Node
    # and inspect the emitted DOM geometry in each locale; no browser/HTTP.
    checked=subprocess.run(
        ["node",str(repo/"scripts"/"verify_bosla_private_velocity_svg.js"),
         str(folder/_V29_DRAFT)],
        cwd=repo,capture_output=True,text=True,check=False,timeout=40,
    )
    if checked.returncode!=0:
        raise ValueError("BSA257_REAL_RENDERER_GEOMETRY_CHECK_FAILED")
    geometry=json.loads(checked.stdout)
    if (geometry.get("status")!=
            "BSA257_REAL_RENDERER_SVG_ARROW_GEOMETRY_RECHECKED_NO_ACADEMIC_PASS"
            or geometry.get("localesChecked")!=3
            or geometry.get("actualSvgVelocityArrowsVerified")!=6
            or geometry.get("equalOppositeArrowGeometry") is not True
            or geometry.get("rendererNoAnswerLeakage") is not True
            or geometry.get("sourceFigureExactMatchProven") is not False
            or geometry.get("screenshotPixelsIndependentlyReviewed") is not False
            or geometry.get("trilingualFullMeaningProven") is not False
            or geometry.get("publicationAuthorized") is not False):
        raise ValueError("BSA257_REAL_DOM_EVIDENCE_FAILED_CLOSED")
    geometry_saved=_v6_checkpoint(folder/_V29_GEOMETRY,{
        **identity,**geometry,"privateSpecSha256":draft["specSha256"],
        "sourceVisualDraftSha256":saved["integritySha256"],
        "publicationAuthorized":False,
    })
    return _v6_checkpoint(folder/_V29,{
        **identity,"status":_STATUS29,
        "privateDraftSha256":saved["integritySha256"],
        "realSvgGeometryReceiptSha256":geometry_saved["integritySha256"],
        "actualSourceGroundedDraftCount":1,
        "actualRenderedSvgArrowsVerified":6,
        "actualBrowserPixelOrScreenshotReviewPassed":False,
        "sourceTextFigureExactMatchProven":False,
        "fullAcademicPASS":0,
        "independentMeaningMicroproofsPending":429,
        "completeAcademicProofGatesStillOpen":90,
        "newModelCalls":0,
        "outsideTextbookPdfsRequired":False,
        "publicationAuthorized":False,
        "nextEligibleMilestone":"PRIVATE_ACTUAL_BROWSER_SCREENSHOTS_AND_DOMAIN_SCIENCE_PIXELS",
    })

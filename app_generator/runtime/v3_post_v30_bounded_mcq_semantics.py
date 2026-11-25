"""BSA259: signed, restart-aware V31 bounded selected-MCQ source semantics.

Independent rational opposition witnesses and 3-language option-role checks;
never promotes this limited evidence to any of 90 complete academic gates.
"""
from __future__ import annotations

from hashlib import sha256
from pathlib import Path
from typing import Any

from app_generator.runtime.v3_native_release_adapter import _v6_checkpoint
from app_generator.runtime.v3_public_nonmerging_draft_pr import _preflight
from app_generator.runtime.v3_revised_source_proof_rebinding import _signed
from app_generator.runtime.v3_post_v29_real_browser_pixels import (
    _V30,_V30_RASTER,_STATUS30,
)
from app_generator.runtime.v3_selected_textbook_scientific_provenance import _SOURCE_BINDING
from app_generator.runtime.v3_exact_revised_review_reconciliation import _CANDIDATE
from app_generator.runtime.v3_public_bundle_handoff import _trusted_json
from app_generator.validation.section91_formal_physics import _SOURCE_SHA,_CANDIDATE_SHA
from app_generator.validation.section91_bounded_semantic_witness import (
    source_bound_four_choice_witness,
)

_V31_PRE="V31_SOURCE_BOUND_THREE_LOCALE_MCQ_PRE_CALL.json"
_V31_WITNESS="V31_INDEPENDENT_ONE_ACTIVITY_MCQ_ROLE_WITNESSES.json"
_V31="V31_BOUNDED_SOURCE_MCQ_LOCALIZED_SEMANTIC_NO_ACADEMIC_PASS.json"
_STATUS31="V31_BOUNDED_SOURCE_THREE_LOCALE_MCQ_SEMANTIC_WITNESS_PRIVATE"


def run_post_v30_independent_mcq_semantics(
    repo:Path,private:Path,ready:dict[str,Any],
    v9:dict,v11:dict,v12:dict,v30_result:dict[str,Any],
)->dict[str,Any]:
    folder,_,_,_,_=_preflight(repo,private,ready,v9,v11,v12)
    v30=_signed(folder,_V30,ready)
    raster=_signed(folder,_V30_RASTER,ready)
    if (v30!=v30_result or v30.get("status")!=_STATUS30
            or v30.get("sourceV30RasterReceiptSha256")!=raster["integritySha256"]
            or v30.get("realChromeScreenshotPixelEvidenceCount")!=3
            or v30.get("realChromeScreenshotVelocityArrowsVerified")!=6
            or v30.get("completeAcademicProofGatesStillOpen")!=90
            or v30.get("independentMeaningMicroproofsPending")!=429
            or v30.get("fullAcademicPASS")!=0
            or v30.get("newModelCalls")!=0
            or v30.get("publicationAuthorized") is not False
            or v30.get("sourceSha256")!=_SOURCE_SHA
            or v30.get("revisedCandidateSha256")!=_CANDIDATE_SHA):
        raise ValueError("BSA259_SIGNED_GENUINE_BROWSER_V30_REQUIRED")
    source=_trusted_json(private/_SOURCE_BINDING)
    pdf=Path(source["sourcePdf"])
    candidate=folder/_CANDIDATE
    if (pdf.is_symlink() or not pdf.is_file()
            or sha256(pdf.read_bytes()).hexdigest()!=_SOURCE_SHA
            or candidate.is_symlink() or not candidate.is_file()
            or sha256(candidate.read_bytes()).hexdigest()!=_CANDIDATE_SHA):
        raise ValueError("BSA259_GENUINE_TEXTBOOK_OR_REVISED_CANDIDATE_MISSING")
    identity={
        "gitHead":ready["gitHead"],"proposalSha256":ready["proposalSha256"],
        "sourceSha256":_SOURCE_SHA,"revisedCandidateSha256":_CANDIDATE_SHA,
        "sourceV30ReceiptSha256":v30["integritySha256"],
        "sourceV30RasterSha256":raster["integritySha256"],
    }
    _v6_checkpoint(folder/_V31_PRE,{
        **identity,"status":"V31_INDEPENDENT_BOUNDED_MCQ_PRE_CALL",
        "outsideTextbookPdfsRequired":False,
        "newProviderCalls":0,"publicationAuthorized":False,
    })
    witness=source_bound_four_choice_witness(
        source_pdf=pdf,package_file=candidate)
    if (witness.get("status")!=
            "BSA259_ONE_SOURCE_MCQ_FOUR_OPTIONS_THREE_LOCALES_BOUNDED_WITNESSES"
            or witness.get("independentlyCheckedLocalizedRoleTexts")!=18
            or witness.get("independentlyCheckedOptionLocales")!=12
            or witness.get("mathematicallyCounterexampledFalseChoices")!=3
            or witness.get("correctAnswerModelUniquelyTrue") is not True
            or witness.get("entireActivityIndependentSemanticAccepted") is not False
            or witness.get("fullTranslationSemanticEquivalenceProven") is not False
            or witness.get("fullAcademicPASS")!=0
            or witness.get("newProviderCalls")!=0
            or witness.get("publicationAuthorized") is not False):
        raise ValueError("BSA259_SOURCE_ROLE_WITNESSES_UNVERIFIED")
    signed=_v6_checkpoint(folder/_V31_WITNESS,{
        **identity,**witness,"publicationAuthorized":False,
    })
    return _v6_checkpoint(folder/_V31,{
        **identity,"status":_STATUS31,
        "sourceV31LocalizedWitnessSha256":signed["integritySha256"],
        "sourceBoundVerifiedMcqOptionLocalePairs":12,
        "sourceBoundVerifiedCorrectMcqOptionCount":1,
        "sourceBoundCounterexampledFalseChoices":3,
        "sourceBoundLocalizedTextRoleChecks":18,
        "all90AcademicGateFullAcceptances":0,
        "independentMeaningMicroproofsPending":429,
        "completeAcademicProofGatesStillOpen":90,
        "fullAcademicPASS":0,"newModelCalls":0,
        "outsideTextbookPdfsRequired":False,
        "publicationAuthorized":False,
        "nextEligibleMilestone":
            "GENERALIZE_SOURCE_BOUND_SEMANTIC_AND_PIXEL_WITNESSES_TO_OTHER_17_ACTIVITIES",
    })

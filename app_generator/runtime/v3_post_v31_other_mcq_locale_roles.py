"""BSA260: V32 auto-dispatched from signed V31, eight other MCQs.

Full other-MCQ localized text cue evidence is split into two small signed,
restart-idempotent four-item receipts; source PDF and frozen candidate unchanged.
"""
from __future__ import annotations

from hashlib import sha256
from pathlib import Path
from typing import Any

from app_generator.runtime.v3_native_release_adapter import _v6_checkpoint
from app_generator.runtime.v3_five_stage_completion import _hash
from app_generator.runtime.v3_public_nonmerging_draft_pr import _preflight
from app_generator.runtime.v3_revised_source_proof_rebinding import _signed
from app_generator.runtime.v3_post_v30_bounded_mcq_semantics import (
    _V31,_V31_WITNESS,_STATUS31,
)
from app_generator.runtime.v3_selected_textbook_scientific_provenance import _SOURCE_BINDING
from app_generator.runtime.v3_exact_revised_review_reconciliation import _CANDIDATE
from app_generator.runtime.v3_public_bundle_handoff import _trusted_json
from app_generator.validation.section91_formal_physics import _SOURCE_SHA,_CANDIDATE_SHA
from app_generator.validation.section91_other_mcq_locale_roles import (
    bound_all_other_mcq_locale_option_roles,
)

_V32_PRE="V32_OTHER_EIGHT_MCQ_MULTILINGUAL_PRE_CALL.json"
_V32_CHUNK_A="V32_MCQ_02_TO_05_LOCALIZED_ROLE_PROOF_ROWS.json"
_V32_CHUNK_B="V32_MCQ_06_TO_09_LOCALIZED_ROLE_PROOF_ROWS.json"
_V32="V32_ALL_NINE_MCQ_BOUNDED_LOCALIZED_CUES_NO_ACADEMIC_PASS.json"
_STATUS32="V32_OTHER_EIGHT_MCQS_SOURCE_BOUND_96_LOCALE_OPTION_CUES_PRIVATE"


def run_post_v31_other_eight_mcq_localized_proofs(
    repo:Path,private:Path,ready:dict[str,Any],
    v9:dict,v11:dict,v12:dict,v31_result:dict[str,Any],
)->dict[str,Any]:
    folder,_,_,_,_=_preflight(repo,private,ready,v9,v11,v12)
    v31=_signed(folder,_V31,ready)
    w31=_signed(folder,_V31_WITNESS,ready)
    if (v31!=v31_result or v31.get("status")!=_STATUS31
            or v31.get("sourceV31LocalizedWitnessSha256")!=w31["integritySha256"]
            or v31.get("sourceBoundVerifiedMcqOptionLocalePairs")!=12
            or v31.get("sourceBoundCounterexampledFalseChoices")!=3
            or v31.get("fullAcademicPASS")!=0
            or v31.get("completeAcademicProofGatesStillOpen")!=90
            or v31.get("independentMeaningMicroproofsPending")!=429
            or v31.get("newModelCalls")!=0
            or v31.get("publicationAuthorized") is not False
            or v31.get("sourceSha256")!=_SOURCE_SHA
            or v31.get("revisedCandidateSha256")!=_CANDIDATE_SHA):
        raise ValueError("BSA260_GENUINE_SIGNED_FIRST_MCQ_V31_REQUIRED")
    binding=_trusted_json(private/_SOURCE_BINDING)
    pdf=Path(binding["sourcePdf"])
    candidate=folder/_CANDIDATE
    if (pdf.is_symlink() or not pdf.is_file()
            or sha256(pdf.read_bytes()).hexdigest()!=_SOURCE_SHA
            or candidate.is_symlink() or not candidate.is_file()
            or sha256(candidate.read_bytes()).hexdigest()!=_CANDIDATE_SHA):
        raise ValueError("BSA260_EXACT_ORIGINAL_SERWAY_PDF_OR_CANDIDATE_CHANGED")
    identity={
        "gitHead":ready["gitHead"],"proposalSha256":ready["proposalSha256"],
        "sourceSha256":_SOURCE_SHA,"revisedCandidateSha256":_CANDIDATE_SHA,
        "sourceV31ReceiptSha256":v31["integritySha256"],
        "sourceV31FirstMcqWitnessSha256":w31["integritySha256"],
    }
    _v6_checkpoint(folder/_V32_PRE,{
        **identity,"status":"V32_REAL_SELECTED_SERWAY_MCQ_ROLES_PRE_CALL",
        "newProviderCalls":0,"publicationAuthorized":False,
        "outsideTextbookPdfsRequired":False,
    })
    proof=bound_all_other_mcq_locale_option_roles(
        source_pdf=pdf,package_file=candidate)
    if (proof.get("status")!=
            "BSA260_OTHER_EIGHT_SOURCE_BOUND_MCQ_LOCALIZED_CUE_WITNESSES"
            or proof.get("sourceSha256")!=_SOURCE_SHA
            or proof.get("candidateSha256")!=_CANDIDATE_SHA
            or proof.get("otherMcqActivitiesChecked")!=8
            or proof.get("otherMcqLocalizedOptionRolesChecked")!=96
            or proof.get("otherMcqPromptExplanationRoleChecks")!=48
            or proof.get("otherMcqFormalTrueChoiceWitnesses")!=8
            or proof.get("otherMcqFormalFalseChoiceCounterexamples")!=24
            or proof.get("fullTrilingualMeaningEquivalenceProven") is not False
            or proof.get("fullNaturalLanguageScientificTruthCertified") is not False
            or proof.get("fullAcademicPASS")!=0
            or proof.get("newProviderCalls")!=0
            or proof.get("publicationAuthorized") is not False
            or len(proof.get("sourceBoundActivityWitnesses",[]))!=8):
        raise ValueError("BSA260_INDEPENDENT_EIGHT_MCQ_SOURCE_ROLES_MISSING")
    # Bounded signed receipts: retain exact per-activity proof hashes and
    # explicit modelled true/false identities, not tens of KB of duplicated
    # localized strings. Independent readback recomputes these full evidence
    # hashes directly from the original PDF and unchanged frozen candidate.
    items=[{
        "activityId":row["activityId"],
        "correctAnswerModel":row["correctAnswerModel"],
        "falseOptionsModelled":row["falseOptionsModelled"],
        "fullSourceBoundRoleEvidenceSha256":_hash(row),
        "checkedLocaleOptionRoles":12,
        "checkedLocalizedExplanationPromptRoles":6,
    } for row in proof["sourceBoundActivityWitnesses"]]
    first=_v6_checkpoint(folder/_V32_CHUNK_A,{
        **identity,"status":"V32_REAL_MCQ_02_TO_05_CUE_ROWS_PRIVATE",
        "activities":items[:4],"publicationAuthorized":False,
    })
    second=_v6_checkpoint(folder/_V32_CHUNK_B,{
        **identity,"status":"V32_REAL_MCQ_06_TO_09_CUE_ROWS_PRIVATE",
        "activities":items[4:],"publicationAuthorized":False,
    })
    return _v6_checkpoint(folder/_V32,{
        **identity,"status":_STATUS32,
        "otherMcqSourceRoleReceiptASha256":first["integritySha256"],
        "otherMcqSourceRoleReceiptBSha256":second["integritySha256"],
        "allNineMcqLocalizedOptionRolesChecked":108,
        "otherEightMcqLocalizedOptionRolesChecked":96,
        "otherEightMcqExplanationPromptRolesChecked":48,
        "allNineMcqFormalFalseAlternativeCounterexamples":27,
        "otherEightMcqModelledFalseAlternatives":24,
        "otherEightMcqModelledCorrectAlternatives":8,
        "fullIndependentAllNaturalLanguageMeaningAccepted":False,
        "completeAcademicProofGatesStillOpen":90,
        "independentMeaningMicroproofsPending":429,
        "fullAcademicPASS":0,"newModelCalls":0,
        "publicationAuthorized":False,
        "outsideTextbookPdfsRequired":False,
        "nextEligibleMilestone":"OTHER_NINE_INTERACTIVE_SOURCE_BOUND_MEANING_VISUAL_PROOFS",
    })

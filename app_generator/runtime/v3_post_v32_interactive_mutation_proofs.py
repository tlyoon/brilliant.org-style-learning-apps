"""BSA262: registered V34 source-bound nine-interaction mutation witness stage."""
from __future__ import annotations
from pathlib import Path
from typing import Any

from app_generator.runtime.v3_native_release_adapter import _v6_checkpoint
from app_generator.runtime.v3_public_nonmerging_draft_pr import _preflight
from app_generator.runtime.v3_revised_source_proof_rebinding import _signed
from app_generator.runtime.v3_post_v31_other_mcq_locale_roles import _V32, _STATUS32
from app_generator.runtime.v3_selected_textbook_scientific_provenance import _SOURCE_BINDING
from app_generator.runtime.v3_exact_revised_review_reconciliation import _CANDIDATE
from app_generator.runtime.v3_public_bundle_handoff import _trusted_json
from app_generator.validation.section91_formal_physics import _SOURCE_SHA, _CANDIDATE_SHA
from app_generator.validation.section91_interactive_mutation_witness import (
    audit_nine_interactive_mutants,
)

_V34 = "V34_NINE_INTERACTIVE_MUTANT_PROOFS_NO_ACADEMIC_PASS.json"
_STATUS34 = "V34_NINE_SOURCE_BOUND_INTERACTIVE_MUTANTS_REJECTED_PRIVATE_NO_RELEASE"

def run_post_v32_interactive_mutation_proofs(
    repo: Path, private: Path, ready: dict[str, Any],
    v9: dict, v11: dict, v12: dict, v32_result: dict[str, Any],
) -> dict[str, Any]:
    folder, _, _, _, _ = _preflight(repo, private, ready, v9, v11, v12)
    v32 = _signed(folder, _V32, ready)
    if (v32 != v32_result or v32.get("status") != _STATUS32
            or v32.get("sourceSha256") != _SOURCE_SHA
            or v32.get("revisedCandidateSha256") != _CANDIDATE_SHA
            or v32.get("allNineMcqLocalizedOptionRolesChecked") != 108
            or v32.get("allNineMcqFormalFalseAlternativeCounterexamples") != 27
            or v32.get("fullAcademicPASS") != 0
            or v32.get("publicationAuthorized") is not False):
        raise ValueError("BSA262_SIGNED_V32_MCQS_REQUIRED")
    binding = _trusted_json(private / _SOURCE_BINDING)
    pdf = Path(binding["sourcePdf"])
    candidate = folder / _CANDIDATE
    proof = audit_nine_interactive_mutants(source_pdf=pdf, package_file=candidate)
    if (proof.get("status") != "BSA262_REAL_NINE_INTERACTIVE_FORMAL_MUTANTS_REJECTED"
            or proof.get("interactiveActivitiesChecked") != 9
            or proof.get("independentlyRejectedWrongAnswerMutants") != 9
            or proof.get("localizedPromptExplanationFieldsPresent") != 54
            or proof.get("localizedItemLabelsPresent", 0) < 27
            or len(proof.get("activityProofs", ())) != 9
            or proof.get("sourceSha256") != _SOURCE_SHA
            or proof.get("candidateSha256") != _CANDIDATE_SHA
            or proof.get("fullTrilingualMeaningEquivalenceProven") is not False
            or proof.get("fullAcademicPASS") != 0
            or proof.get("newProviderCalls") != 0
            or proof.get("publicationAuthorized") is not False):
        raise ValueError("BSA262_REAL_INTERACTIVE_MUTANT_EVIDENCE_NOT_ACCEPTED")
    return _v6_checkpoint(folder / _V34, {
        "status": _STATUS34,
        "gitHead": ready["gitHead"],
        "proposalSha256": ready["proposalSha256"],
        "sourceSha256": _SOURCE_SHA,
        "revisedCandidateSha256": _CANDIDATE_SHA,
        "sourceV32ReceiptSha256": v32["integritySha256"],
        "interactiveActivitiesChecked": 9,
        "independentlyRejectedWrongAnswerMutants": 9,
        "localizedItemLabelsPresent": proof["localizedItemLabelsPresent"],
        "localizedPromptExplanationFieldsPresent": 54,
        "interactiveFormalProofHashes": [x["correctModelSha256"] for x in proof["activityProofs"]],
        "sourceBoundActivityProofHashes": [x["activitySha256"] for x in proof["activityProofs"]],
        "fullTrilingualMeaningEquivalenceProven": False,
        "completeAcademicProofGatesStillOpen": 90,
        "independentMeaningMicroproofsPending": 429,
        "fullAcademicPASS": 0,
        "newModelCalls": 0,
        "publicationAuthorized": False,
        "outsideTextbookPdfsRequired": False,
        "nextEligibleMilestone": "INTERACTIVE_SOURCE_SEMANTIC_POLARITY_AND_VISUAL_PROOFS",
    })

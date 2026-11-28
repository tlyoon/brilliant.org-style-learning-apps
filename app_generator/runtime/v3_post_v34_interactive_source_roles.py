"""BSA263 V35 source-anchored, bounded interactive trilingual role proof."""
from __future__ import annotations
from pathlib import Path
from typing import Any

from app_generator.runtime.v3_native_release_adapter import _v6_checkpoint
from app_generator.runtime.v3_public_nonmerging_draft_pr import _preflight
from app_generator.runtime.v3_revised_source_proof_rebinding import _signed
from app_generator.runtime.v3_post_v32_interactive_mutation_proofs import _V34, _STATUS34
from app_generator.runtime.v3_selected_textbook_scientific_provenance import _SOURCE_BINDING
from app_generator.runtime.v3_exact_revised_review_reconciliation import _CANDIDATE
from app_generator.runtime.v3_public_bundle_handoff import _trusted_json
from app_generator.validation.section91_formal_physics import _SOURCE_SHA, _CANDIDATE_SHA
from app_generator.validation.section91_interactive_source_roles import (
    audit_interactive_source_role_cues,
)

_V35="V35_INTERACTIVE_SOURCE_ROLE_CUES_NO_ACADEMIC_PASS.json"
_STATUS35="V35_REAL_NINE_INTERACTIVE_TRILINGUAL_SOURCE_ROLE_CUES_PRIVATE"

def run_post_v34_interactive_source_roles(
    repo:Path,private:Path,ready:dict[str,Any],
    v9:dict,v11:dict,v12:dict,v34_result:dict[str,Any],
)->dict[str,Any]:
    folder,_,_,_,_=_preflight(repo,private,ready,v9,v11,v12)
    signed=_signed(folder,_V34,ready)
    if (signed!=v34_result or signed.get("status")!=_STATUS34
            or signed.get("sourceSha256")!=_SOURCE_SHA
            or signed.get("revisedCandidateSha256")!=_CANDIDATE_SHA
            or signed.get("interactiveActivitiesChecked")!=9
            or signed.get("independentlyRejectedWrongAnswerMutants")!=9
            or signed.get("fullAcademicPASS")!=0
            or signed.get("newModelCalls")!=0
            or signed.get("publicationAuthorized") is not False):
        raise ValueError("BSA263_SIGNED_V34_PREDECESSOR_REQUIRED")
    binding=_trusted_json(private/_SOURCE_BINDING)
    witness=audit_interactive_source_role_cues(
        source_pdf=Path(binding["sourcePdf"]),package_file=folder/_CANDIDATE)
    if (witness.get("status")!="BSA263_NINE_INTERACTIVE_TRILOCALE_BOUNDED_SOURCE_ROLE_CUES"
            or witness.get("sourceSha256")!=_SOURCE_SHA
            or witness.get("candidateSha256")!=_CANDIDATE_SHA
            or witness.get("interactiveActivitiesChecked")!=9
            or witness.get("trilingualPromptRoleCuesChecked")!=27
            or witness.get("trilingualFirstItemRoleCuesChecked")!=27
            or witness.get("localizedExplanationsBoundByDigest")!=27
            or len(witness.get("activityWitnesses",()))!=9
            or witness.get("fullTrilingualMeaningEquivalenceProven") is not False
            or witness.get("fullAcademicPASS")!=0
            or witness.get("newProviderCalls")!=0
            or witness.get("publicationAuthorized") is not False):
        raise ValueError("BSA263_SOURCE_ROLE_PROOF_INCOMPLETE_OR_FORGED")
    return _v6_checkpoint(folder/_V35,{
        "status":_STATUS35,
        "gitHead":ready["gitHead"],
        "proposalSha256":ready["proposalSha256"],
        "sourceV34ReceiptSha256":signed["integritySha256"],
        "sourceSha256":_SOURCE_SHA,
        "revisedCandidateSha256":_CANDIDATE_SHA,
        "interactiveActivitiesChecked":9,
        "trilingualPromptRoleCuesChecked":27,
        "trilingualFirstItemRoleCuesChecked":27,
        "localizedExplanationsBoundByDigest":27,
        "activityLocaleWitnessHashes":[
            [[x["promptSha256"],x["itemLabelSha256"],x["explanationSha256"]]
             for x in row["localeWitnesses"]]
            for row in witness["activityWitnesses"]],
        "fullTrilingualMeaningEquivalenceProven":False,
        "fullScientificClauseTruthProven":False,
        "renderedDiagramScienceVerified":False,
        "completeAcademicProofGatesStillOpen":90,
        "independentMeaningMicroproofsPending":429,
        "fullAcademicPASS":0,"newModelCalls":0,
        "publicationAuthorized":False,
        "outsideTextbookPdfsRequired":False,
        "nextEligibleMilestone":"SOURCE_BOUND_EXPLANATION_MEANING_AND_INTERACTIVE_VISUAL_PROOFS",
    })

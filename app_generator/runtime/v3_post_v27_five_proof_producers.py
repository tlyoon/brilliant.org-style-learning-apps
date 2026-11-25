"""BSA256 V28: actual five-channel bounded textbook proof execution.

Source PDF stays on Yoga6. The runtime verifies exact signed V26/V27
predecessors and reads unchanged candidate bytes. Every generated artifact
is an evidence receipt, NOT full semantic/diagram-science approval.
"""
from __future__ import annotations

from hashlib import sha256
from pathlib import Path
from typing import Any

from app_generator.runtime.v3_five_stage_completion import _hash
from app_generator.runtime.v3_native_release_adapter import _v6_checkpoint
from app_generator.runtime.v3_public_bundle_handoff import _trusted_json
from app_generator.runtime.v3_public_nonmerging_draft_pr import _preflight
from app_generator.runtime.v3_revised_source_proof_rebinding import _signed
from app_generator.runtime.v3_post_v26_bounded_symbolic_recovery import (
    _V27, _STATUS27,
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
from app_generator.validation.independent_academic_proof_producers import (
    audit_five_proof_channels,
)

_V28_PRE="V28_FIVE_PROOF_PRODUCERS_PRE_CALL.json"
_V28_MCQ="V28_NINE_MCQ_BOUNDED_PROOF_TASK_ROWS.json"
_V28_INT="V28_NINE_INTERACTIVE_BOUNDED_PROOF_TASK_ROWS.json"
_V28_RESULT="V28_FIVE_BOUNDED_SOURCE_PROOF_RESULTS.json"
_V28="V28_FIVE_PROOF_CHANNELS_EXECUTED_NO_ACADEMIC_PASS.json"
_STATUS28="V28_FIVE_BOUNDED_PROOF_PRODUCERS_REAL_EXECUTION_NOT_FULL_ACADEMIC_PASS"


def _assert_bounded_receipt(evidence:dict[str,Any])->None:
    if (evidence.get("status")!="BSA256_FIVE_INDEPENDENT_BOUNDED_PRODUCERS_EXECUTED"
            or evidence.get("sourceSha256")!=_SOURCE_SHA
            or evidence.get("candidateSha256")!=_CANDIDATE_SHA
            or evidence.get("sourceFidelity",{}).get("pageAnchorsReextracted")!=18
            or evidence.get("scientificExplanations",{}).get("textbookAxiomsReextracted")!=9
            or evidence.get("scientificExplanations",{}).get("boundedMathWitnesses")!=68
            or evidence.get("mcqIncorrectChoices",{}).get("correctMCQKeysVerified")!=9
            or evidence.get("mcqIncorrectChoices",{}).get("falseMCQAlternativeCountermodels")!=27
            or evidence.get("englishMalayChinese",{}).get("localizedSurfacesInspected")!=222
            or evidence.get("englishMalayChinese",{}).get("matchingNumericLiteralSurfaces")!=222
            or evidence.get("englishMalayChinese",{}).get("numericLiteralReviewNeeded")!=0
            or evidence.get("englishMalayChinese",{}).get("strictFormulaLiteralMatches")!=5
            or evidence.get("englishMalayChinese",{}).get("unresolvedSymbolicFields")!=3
            or evidence.get("interactiveDiagrams",{}).get("declaredDiagramsFound")!=0
            or evidence.get("interactiveDiagrams",{}).get("sourceGroundedVisualNecessityTasksOpen")!=18
            or evidence.get("interactiveDiagrams",{}).get("sourceSectionMentionsFigure91") is not True
            or evidence.get("originalIndependentSemanticTasksPending")!=429
            or evidence.get("completeAcademicProofGatesStillOpen")!=90
            or evidence.get("formalAcademicPASS")!=0
            or evidence.get("providerCalls")!=0
            or evidence.get("additionalTextbooks")!=0
            or evidence.get("publicationAuthorized") is not False
            or any(evidence.get(k,{}).get(field) is not False for k,field in (
                ("sourceFidelity","fullSourceStatementMeaningProven"),
                ("scientificExplanations","fullExplanationClauseTruthProven"),
                ("mcqIncorrectChoices","allDistractorNaturalLanguageSemanticsProven"),
                ("englishMalayChinese","fullTrilingualMeaningProven"),
                ("interactiveDiagrams","renderedVisualScienceApproved"),
            ))):
        raise ValueError("BSA256_FIVE_CHANNEL_EVIDENCE_FALSELY_PROMOTED_OR_INCOMPLETE")


def run_post_v27_five_proof_producers(
    repo:Path,private:Path,ready:dict[str,Any],
    v9:dict,v11:dict,v12:dict,v27_result:dict,
)->dict[str,Any]:
    folder,_,_,_,_=_preflight(repo,private,ready,v9,v11,v12)
    signed_v27=_signed(folder,_V27,ready)
    if (v27_result!=signed_v27
            or signed_v27.get("status")!=_STATUS27
            or signed_v27.get("boundedParserFalsePositivesResolved")!=5
            or signed_v27.get("remainingAmbiguousSymbolicFields")!=3
            or signed_v27.get("completeIndependentAcademicProofSlotsStillOpen")!=90
            or signed_v27.get("fullAcademicPASS")!=0
            or signed_v27.get("newGeminiCalls")!=0
            or signed_v27.get("publicationAuthorized") is not False
            or signed_v27.get("sourceSha256")!=_SOURCE_SHA
            or signed_v27.get("revisedCandidateSha256")!=_CANDIDATE_SHA):
        raise ValueError("BSA256_SIGNED_V27_SOURCE_BOUND_PREDECESSOR_REQUIRED")
    binding=_trusted_json(private/_SOURCE_BINDING)
    pdf=Path(binding["sourcePdf"])
    source_root=Path(binding["sourceRoot"])
    if (binding.get("integritySha256")!=_hash({
            k:v for k,v in binding.items() if k!="integritySha256"})
            or binding.get("contract")!="BOSLA_SELECTED_SERWAY_TEXTBOOK_LOCAL_BINDING_V1"
            or binding.get("section")!="9.1"
            or binding.get("sourceSha256")!=_SOURCE_SHA
            or binding.get("externalFallbackAllowed") is not False
            or binding.get("sourcePdfUploaded") is not False
            or pdf.is_symlink() or not pdf.is_file()
            or pdf.resolve().is_relative_to(repo.resolve())
            or pdf.resolve()!=(source_root/"9"/"9.1"/"source.pdf").resolve()
            or sha256(pdf.read_bytes()).hexdigest()!=_SOURCE_SHA):
        raise ValueError("BSA256_SELECTED_ORIGINAL_TEXTBOOK_SOURCE_CHANGED")
    candidate=folder/_CANDIDATE
    if (candidate.is_symlink() or not candidate.is_file()
            or sha256(candidate.read_bytes()).hexdigest()!=_CANDIDATE_SHA):
        raise ValueError("BSA256_EXACT_REVISED_18_ACTIVITIES_CHANGED")
    identity={
        "gitHead":ready["gitHead"],
        "proposalSha256":ready["proposalSha256"],
        "sourceV27ReceiptSha256":signed_v27["integritySha256"],
        "sourceSha256":_SOURCE_SHA,
        "revisedCandidateSha256":_CANDIDATE_SHA,
    }
    _v6_checkpoint(folder/_V28_PRE,{
        **identity,"status":"V28_ACTUAL_SOURCE_AND_FIVE_PRODUCERS_PRE_CALL",
        "additionalSourcePdfsAllowed":False,
        "newProviderCallsAllowed":False,"publicationAuthorized":False,
    })
    evidence=audit_five_proof_channels(
        source_pdf=pdf,source_sha=_SOURCE_SHA,candidate_path=candidate)
    _assert_bounded_receipt(evidence)
    rows=evidence.pop("perActivityBoundedProofRows")
    if (len(rows)!=18 or len({x["activityId"] for x in rows})!=18
            or _hash(rows)!=evidence["perActivityBoundedProofRowsSha256"]
            or sum(x["boundedFormalWitnessCount"] for x in rows)!=68
            or sum(x["mcqFalseChoicesProven"] for x in rows)!=27
            or any(x["completeSemanticAcceptance"] is not False
                   or x["publicationAuthorized"] is not False
                   or x["visualSpecAvailable"] is not False for x in rows)):
        raise ValueError("BSA256_INDIVIDUAL_EXACT_TASK_PROOF_ROWS_TAMPERED")
    partition=[]
    for kind,file,subset,prefix in (
        ("MCQ",_V28_MCQ,rows[:9],"act-mcq-"),
        ("INTERACTIVE",_V28_INT,rows[9:],"act-int-"),
    ):
        if (len(subset)!=9 or
                any(not x["activityId"].startswith(prefix) for x in subset)):
            raise ValueError("BSA256_INDIVIDUAL_PROOF_ROW_ORDER_CHANGED")
        saved=_v6_checkpoint(folder/file,{
            **identity,"status":"V28_NINE_INDEPENDENT_BOUNDED_TASK_PROOFS",
            "sourceModelFamily":kind,
            "rows":subset,"completeAcademicPASS":0,
            "publicationAuthorized":False,
        })
        if (folder/file).stat().st_size>=12000:
            raise ValueError("BSA256_SPLIT_PROOF_ROW_EXCEEDS_12KB_RESTART_LIMIT")
        partition.append({"family":kind,"rows":9,
                          "signedSha256":saved["integritySha256"]})
    evidence["nineActivitySignedProofPartitions"]=partition
    result=_v6_checkpoint(folder/_V28_RESULT,{
        **identity,**evidence,
    })
    if (folder/_V28_RESULT).stat().st_size>=12000:
        raise ValueError("BSA256_SIGNED_PROOF_RECEIPT_EXCEEDS_SAFE_12KB_CAP")
    return _v6_checkpoint(folder/_V28,{
        **identity,"status":_STATUS28,
        "resultSha256":result["integritySha256"],
        "realSourcePageAnchors":18,
        "boundedScientificAnswerWitnesses":68,
        "falseMcqOptionsProvenAgainstFormalModels":27,
        "trilingualSurfacesNumericLiteralChecked":222,
        "actualDiagramsAbsent":18,
        "independentMeaningMicroproofsPending":429,
        "completeAcademicProofGatesStillOpen":90,
        "formalAcademicPASS":0,
        "externalPdfAcquisition":False,
        "newProviderCalls":0,
        "publicationAuthorized":False,
        "nextEligibleMilestone":"SOURCE_EXPLANATION_TRILINGUAL_AND_RENDERED_VISUAL_SEMANTIC_PROOF_EXECUTION",
    })

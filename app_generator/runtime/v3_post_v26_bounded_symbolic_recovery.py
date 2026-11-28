"""BSA255 V27: normal-worker bounded mathematical ambiguity auto-repair.

Only a source-version-specific supplemental evidence receipt, never a rewrite
to V26 claims. Original original textbook/Candidate V26 gates still authoritative.
"""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
from typing import Any

from app_generator.runtime.v3_five_stage_completion import _hash
from app_generator.runtime.v3_native_release_adapter import _v6_checkpoint
from app_generator.runtime.v3_public_bundle_handoff import _trusted_json
from app_generator.runtime.v3_public_nonmerging_draft_pr import _preflight
from app_generator.runtime.v3_revised_source_proof_rebinding import _signed
from app_generator.runtime.v3_source_semantic_triage import (
    _V26 as _V26_LANGUAGE, _STATUS26 as _STATUS_LANGUAGE,
)
from app_generator.runtime.v3_full_semantic_proof_dispatch import (
    _V26 as _V26_QUEUE, _STATUS26 as _STATUS_QUEUE,
)
from app_generator.runtime.v3_selected_textbook_scientific_provenance import _SOURCE_BINDING
from app_generator.runtime.v3_exact_revised_review_reconciliation import _CANDIDATE
from app_generator.validation.section91_formal_physics import _SOURCE_SHA,_CANDIDATE_SHA
from app_generator.validation.bounded_symbolic_qa import audit_bounded_symbolic_recovery

_V27_PRE = "V27_BOUNDED_SYMBOLIC_PRE_CALL.json"
_V27_RESULT = "V27_BOUNDED_SYMBOLIC_RECOVERY_RESULT.json"
_V27 = "V27_SOURCE_PINNED_SYMBOLIC_TRIAGE_NO_ACADEMIC_PASS.json"
_STATUS27 = "V27_FIVE_FALSE_POSITIVE_SYMBOLIC_FLAGS_BOUNDED_NO_ACADEMIC_PASS"


def _compact(result:dict[str,Any])->dict[str,Any]:
    rows=result["rows"]
    if (result.get("status")!="BSA255_EXPLICIT_LITERAL_FORMULA_EQUIVALENCE_TRIAGE_NO_ACADEMIC_PASS"
            or result.get("sourceMeaningProven") is not False
            or result.get("trilingualSemanticMeaningProven") is not False
            or result.get("formalAcademicPASS")!=0
            or result.get("publicationAuthorized") is not False
            or result.get("providerCalls")!=0
            or len({(r.get("activityId"),r.get("field")) for r in rows})!=len(rows)
            or result["activityCount"]!=18
            # BSA267: accept independently recomputed counts only when
            # algebraically consistent, not a stale 8/5/3/21 or 2/0/2/20
            # snapshot. The caller already reopens the exact-SHA textbook
            # and candidate and computes this report from actual content.
            or not isinstance(rows,list) or len(rows)>222
            or result["priorAmbiguousSymbolicFields"]!=len(rows)
            or result["boundedParserFalsePositivesResolved"]!=sum(
                x.get("boundedIdenticalExplicitMath") is True for x in rows)
            or result["remainingAmbiguousSymbolicFields"]!=(
                len(rows)-result["boundedParserFalsePositivesResolved"])
            or not isinstance(result["independentRemainingPriorReviewFlags"],int)
            or result["independentRemainingPriorReviewFlags"]<
                result["remainingAmbiguousSymbolicFields"]
            or any(not isinstance(r.get("activityId"),str)
                   or not isinstance(r.get("field"),str)
                   or not isinstance(r.get("activitySha256"),str)
                   or len(r["activitySha256"])!=64
                   or not isinstance(r.get("strictEquationSetsSha256"),str)
                   or len(r["strictEquationSetsSha256"])!=64
                   or type(r.get("boundedIdenticalExplicitMath")) is not bool
                   or r.get("remainingSemanticStatus")!="REVIEW_REQUIRED"
                   or r.get("fullScientificOrTrilingualMeaningProven") is not False
                   for r in rows)):
        raise ValueError("BSA255_FALSE_SYMBOLIC_DIAGNOSTIC_NOT_INDEPENDENTLY_JUSTIFIED")
    return {
        "symbolicReviewFields":len(rows),
        "strictLiteralFormulaMatches":result["boundedParserFalsePositivesResolved"],
        "unresolvedSymbolicReviewFields":result["remainingAmbiguousSymbolicFields"],
        "remainingTechnicalReviewFlags":result["independentRemainingPriorReviewFlags"],
        "rowsSha256":_hash(rows),
        "rowsByActivity":[{
            "activityId":row["activityId"],"activitySha256":row["activitySha256"],
            "field":row["field"],"formulaSha256":row["strictEquationSetsSha256"],
            "strictLiteralMatch":row["boundedIdenticalExplicitMath"],
        } for row in rows],
        "formalAcademicPASS":0,
        "sourceMeaningProven":False,
        "trilingualSemanticMeaningProven":False,
        "publicationAuthorized":False,
    }


def run_post_v26_bounded_symbolic_recovery(
    repo:Path,private:Path,ready:dict[str,Any],
    v9:dict,v11:dict,v12:dict,source_v26:dict,queue_v26:dict,
)->dict[str,Any]:
    """Auto-reuse original source/version and completed two V26 SHA receipts."""
    folder,_,_,_,_=_preflight(repo,private,ready,v9,v11,v12)
    source=_signed(folder,_V26_LANGUAGE,ready)
    queue=_signed(folder,_V26_QUEUE,ready)
    if (source!=source_v26 or queue!=queue_v26
            or source.get("status")!=_STATUS_LANGUAGE
            or queue.get("status")!=_STATUS_QUEUE
            or source.get("activitiesChecked")!=18
            or source.get("scientificLocalizedFieldsChecked")!=222
            or not isinstance(source.get("unresolvedTriLocaleSemanticReviewItems"),int)
            or source["unresolvedTriLocaleSemanticReviewItems"]<0
            or source["unresolvedTriLocaleSemanticReviewItems"]>222
            or source.get("academicProofGatesStillOpen")!=90
            or source.get("formalAcademicPASS")!=0
            or queue.get("activityCount")!=18
            or queue.get("additionalSemanticMicroproofsPending")!=429
            or queue.get("completeAcademicGateSlotsStillOpen")!=90
            or queue.get("independentSemanticPASS")!=0
            or source.get("publicationAuthorized") is not False
            or queue.get("publicationAuthorized") is not False):
        raise ValueError("BSA255_EXACT_BOTH_SIGNED_V26_PRECONDITIONS_REQUIRED")
    binding=_trusted_json(private/_SOURCE_BINDING)
    pdf=Path(binding["sourcePdf"])
    source_root=Path(binding["sourceRoot"])
    if (binding.get("integritySha256")!=_hash({
            k:v for k,v in binding.items() if k!="integritySha256"})
            or binding.get("sourceSha256")!=_SOURCE_SHA
            or binding.get("contract")!="BOSLA_SELECTED_SERWAY_TEXTBOOK_LOCAL_BINDING_V1"
            or binding.get("section")!="9.1"
            or binding.get("externalFallbackAllowed") is not False
            or binding.get("sourcePdfUploaded") is not False
            or pdf.is_symlink() or not pdf.is_file()
            or pdf.resolve().is_relative_to(repo.resolve())
            or pdf.resolve()!=(source_root/"9"/"9.1"/"source.pdf").resolve()
            or sha256(pdf.read_bytes()).hexdigest()!=_SOURCE_SHA):
        raise ValueError("BSA255_SELECTED_ORIGINAL_ONE_TEXTBOOK_SOURCE_CHANGED")
    path=folder/_CANDIDATE
    if (path.is_symlink() or not path.is_file()
            or sha256(path.read_bytes()).hexdigest()!=_CANDIDATE_SHA):
        raise ValueError("BSA255_EXACT_REVISED_SOURCE_VERSION_CHANGED")
    payload=json.loads(path.read_text(encoding="utf8"))
    checked=audit_bounded_symbolic_recovery(payload["activities"])
    compact=_compact(checked)
    if (source["unresolvedTriLocaleSemanticReviewItems"]!=
            checked["independentRemainingPriorReviewFlags"]+
            checked["boundedParserFalsePositivesResolved"]):
        raise ValueError("BSA267_SIGNED_SOURCE_V26_AND_RECOMPUTED_V27_COUNTS_DIFFER")
    identity={
        "gitHead":ready["gitHead"],
        "proposalSha256":ready["proposalSha256"],
        "sourceV26ScientificSha256":source["integritySha256"],
        "sourceV26QueueSha256":queue["integritySha256"],
        "sourceSha256":_SOURCE_SHA,
        "revisedCandidateSha256":_CANDIDATE_SHA,
    }
    _v6_checkpoint(folder/_V27_PRE,{
        **identity,"status":"PRE_CALL_RESTRICTED_SYMBOLIC_PARSER_ONLY",
        "modelRequestsPermitted":False,"publicationAuthorized":False})
    result=_v6_checkpoint(folder/_V27_RESULT,{
        **identity,**compact,
        "status":"V27_SOURCE_EXACT_SYMBOLIC_FALSE_POSITIVES_RECONCILED",
        "academicProofGatesStillOpen":90,"providerCalls":0,
        "publicationAuthorized":False,
    })
    if (folder/_V27_RESULT).stat().st_size>=12000:
        raise ValueError("BSA255_HISTORICAL_SIGNED_CHECKPOINT_LIMIT_EXCEEDED")
    return _v6_checkpoint(folder/_V27,{
        **identity,"status":_STATUS27,
        "resultSha256":result["integritySha256"],
        "boundedParserFalsePositivesResolved":checked["boundedParserFalsePositivesResolved"],
        "remainingAmbiguousSymbolicFields":checked["remainingAmbiguousSymbolicFields"],
        "remainingTechnicalReviewFlags":checked["independentRemainingPriorReviewFlags"],
        "completeIndependentAcademicProofSlotsStillOpen":90,
        "fullAcademicPASS":0,
        "newGeminiCalls":0,
        "outsideSourcePdfsRequired":False,
        "publicationAuthorized":False,
        "nextEligibleMilestone":"EXECUTE_INDEPENDENT_TEXTBOOK_REASONING_TRANSLATION_AND_VISUAL_PROOFS",
    })

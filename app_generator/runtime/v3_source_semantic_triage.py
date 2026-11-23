"""BSA253 V26: normal Yoga6 source/answer/explanation/trilingual triage.

Runs AFTER genuine BSA252 signed V25 complete. Independently recomputes
bounded source physics and typed learner-visible scientific language cues,
correct/distractor references, and literal mathematical notation across 18
activities. Does not pretend semantic cues are complete academic proof.
"""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
from typing import Any

from app_generator.runtime.v3_section91_formal_academic_dispatch import (
    _V25, _V25_RESULT, _STATUS25, _V25_MCQ_PROOFS,
    _V25_INTERACTIVE_PROOFS,
)
from app_generator.runtime.v3_revised_source_proof_rebinding import _signed
from app_generator.runtime.v3_selected_textbook_scientific_provenance import _SOURCE_BINDING
from app_generator.runtime.v3_malay_auto_revision import _CANDIDATE
from app_generator.runtime.v3_five_stage_completion import _hash
from app_generator.runtime.v3_native_release_adapter import _v6_checkpoint
from app_generator.runtime.v3_public_bundle_handoff import _trusted_json
from app_generator.runtime.v3_public_nonmerging_draft_pr import _preflight
from app_generator.validation.section91_formal_physics import _SOURCE_SHA,_CANDIDATE_SHA
from app_generator.validation.section91_explanation_distractor_claims import (
    audit_source_bound_explanation_distractors,
)

_V26_PRE="V26_EXPLANATION_SEMANTICS_PRE_CALL.json"
_V26_MCQ="V26_NINE_MCQ_EXPLANATION_CUE_PROOFS.json"
_V26_INTERACTIVE="V26_NINE_INTERACTIVE_EXPLANATION_CUE_PROOFS.json"
_V26_RESULT="V26_EXPLANATION_DISTRACTOR_SEMANTIC_TRIAGE_RESULT.json"
_V26="V26_EXPLANATION_DISTRACTOR_SEMANTIC_TRIAGE_NO_RELEASE.json"
_STATUS26="V26_SOURCE_BOUND_EXPLANATION_AND_TRILINGUAL_CUE_TRIAGE_COMPLETE_NO_RELEASE"


def _verify_v25_partitions(folder:Path, ready:dict,
                          result25:dict)->None:
    """Re-open real BSA252 signed partitions; no trust in summary alone."""
    manifest=result25.get("splitImmutableProofReceipts")
    if not isinstance(manifest,list) or len(manifest)!=2:
        raise ValueError("BSA253_GENUINE_BSA252_SMALL_PROOF_PARTITIONS_REQUIRED")
    rows=[]
    for item,path,expected_kind in zip(
        manifest,(_V25_MCQ_PROOFS,_V25_INTERACTIVE_PROOFS),
        ("MCQ","INTERACTIVE"),
    ):
        receipt=_signed(folder,path,ready)
        if (item.get("savedSha256")!=receipt["integritySha256"]
                or receipt.get("formalModelFamily")!=expected_kind
                or item.get("formalModelFamily")!=expected_kind
                or len(receipt.get("proofRows",[]))!=9
                or receipt.get("revisedCandidateSha256")!=_CANDIDATE_SHA
                or receipt.get("sourcePdfSha256")!=_SOURCE_SHA
                or receipt.get("publicationAuthorized") is not False):
            raise ValueError("BSA253_PRIOR_EXACT_PHYSICS_EVIDENCE_CHANGED")
        rows.extend(receipt["proofRows"])
    if (len(rows)!=18
            or len({x.get("activityId") for x in rows})!=18
            or _hash(rows)!=result25["completeFormalProofRosterSha256"]
            or sum(x.get("exactRationalAndDimensionalWitnesses",0)
                   for x in rows)!=68):
        raise ValueError("BSA253_PRIOR_18_BOUNDED_FORMAL_PROOFS_NOT_RECOMPUTABLE")


def _write_small_explanation_rows(folder:Path,identity:dict,
                                  result:dict)->list[dict]:
    rows=result.get("rows")
    if (not isinstance(rows,list) or len(rows)!=18
            or len({x.get("activityId") for x in rows})!=18):
        raise ValueError("BSA253_EXPLANATION_ROWS_REQUIRE_EXACT_18")
    out=[]
    for kind,path,subset in (
        ("MCQ",_V26_MCQ,rows[:9]),
        ("INTERACTIVE",_V26_INTERACTIVE,rows[9:]),
    ):
        if (len(subset)!=9 or any(not r.get("activityId","").startswith(
            "act-mcq-" if kind=="MCQ" else "act-int-") for r in subset)):
            raise ValueError("BSA253_EXPLANATION_ACTIVITY_PARTITION_INVALID")
        saved=_v6_checkpoint(folder/path,{
            **identity,
            "status":"V26_IMMUTABLE_9_ACTIVITY_SCIENTIFIC_SEMANTIC_CUE_REVIEW",
            "sourceSha256":_SOURCE_SHA,
            "candidateSha256":_CANDIDATE_SHA,
            "family":kind,
            "rows":subset,
            "publicationAuthorized":False,
        })
        if (folder/path).stat().st_size>=12000:
            raise ValueError("BSA253_HISTORICAL_12KB_CHECKPOINT_CAP_BREACHED")
        out.append({
            "family":kind,
            "rows":len(subset),
            "signedSha256":saved["integritySha256"],
        })
    return out


def run_post_v25_source_scientific_semantic_triage(
    repo:Path,private:Path,ready:dict[str,Any],v9:dict,v11:dict,v12:dict,
    v25:dict,
)->dict:
    folder,_,_,_,_=_preflight(repo,private,ready,v9,v11,v12)
    real25=_signed(folder,_V25,ready)
    result25=_signed(folder,_V25_RESULT,ready)
    if (v25!=real25
            or real25.get("status")!=_STATUS25
            or real25.get("resultSha256")!=result25["integritySha256"]
            or real25.get("academicProofGatesStillOpen")!=90
            or result25.get("academicProofGatesStillOpen")!=90
            or real25.get("formalAcademicPASS")!=0
            or result25.get("formalAcademicActivityPASS")!=0
            or real25.get("boundedFormalAnswerItemWitnesses")!=68
            or result25.get("sourcePdfSha256")!=_SOURCE_SHA
            or result25.get("revisedCandidateSha256")!=_CANDIDATE_SHA
            or real25.get("publicationAuthorized") is not False):
        raise ValueError("BSA253_VERIFIED_V25_EXACT_DOMAIN_RECEIPT_REQUIRED")
    _verify_v25_partitions(folder,ready,result25)
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
            or pdf.resolve()!=(source_root/"9"/"9.1"/"source.pdf").resolve()
            or pdf.resolve().is_relative_to(repo.resolve())
            or sha256(pdf.read_bytes()).hexdigest()!=_SOURCE_SHA):
        raise ValueError("BSA253_SINGLE_ORIGINAL_TEXTBOOK_BINDING_CHANGED")
    candidate=folder/_CANDIDATE
    if (candidate.is_symlink() or not candidate.is_file()
            or sha256(candidate.read_bytes()).hexdigest()!=_CANDIDATE_SHA):
        raise ValueError("BSA253_PRIVATE_EXACT_REVISION_CHANGED")
    identity={
        "gitHead":ready["gitHead"],
        "proposalSha256":ready["proposalSha256"],
        "sourceV25ReceiptSha256":real25["integritySha256"],
        "sourceV25FormalResultSha256":result25["integritySha256"],
    }
    _v6_checkpoint(folder/_V26_PRE,{
        **identity,
        "status":"V26_REAL_SOURCE_AND_LOCALIZED_CLAIM_PRE_CALL_NO_PROVIDER",
        "sourceSha256":_SOURCE_SHA,
        "candidateSha256":_CANDIDATE_SHA,
        "providerCallsAllowed":False,
        "publicationAuthorized":False,
    })
    science=audit_source_bound_explanation_distractors(
        source_pdf=pdf,source_sha=_SOURCE_SHA,candidate_path=candidate)
    if (science["sourceBoundFormalAnswerWitnessesRecomputed"]!=68
            or science["originalTextbookPremisesReverified"]!=9
            or science["completeMCQCorrectAndDistractorTruthModels"]!=9
            or science["completeInteractiveFormalSolutions"]!=9
            or science["localisedFieldsExamined"]!=222
            or science["scientificMathBearingFields"]!=32
            or science["unambiguousScienceOrAnswerContradictions"]!=0
            or science["visualSpecsInPilot"]!=0
            or science["diagramSemanticClaimsMade"] is not False
            or science["formalAcademicPASS"]!=0
            or science["fullAcademicProofGatesOpen"]!=90
            or science["newProviderCalls"]!=0
            or science["publicationAuthorized"] is not False):
        raise ValueError("BSA253_UNTRUSTED_TRIAGE_OR_FALSE_COMPLETE_PROOF")
    partitions=_write_small_explanation_rows(folder,identity,science)
    bounded={k:v for k,v in science.items() if k!="rows"}
    result=_v6_checkpoint(folder/_V26_RESULT,{
        **identity,
        **bounded,
        "status":"V26_EXACT_SOURCE_TWENTY_SIX_SEMANTIC_REVIEW_ITEMS_STAGED",
        "signedPartReceipts":partitions,
        "full18ActivityClaimsSha256":_hash(science["rows"]),
        "sourcePdfNotUploaded":True,
        "publicationAuthorized":False,
    })
    if (folder/_V26_RESULT).stat().st_size>=12000:
        raise ValueError("BSA253_12KB_SAFE_AGGREGATE_LIMIT")
    return _v6_checkpoint(folder/_V26,{
        **identity,
        "status":_STATUS26,
        "resultSha256":result["integritySha256"],
        "activitiesChecked":18,
        "scientificLocalizedFieldsChecked":science["localisedFieldsExamined"],
        "unresolvedTriLocaleSemanticReviewItems":
            science["unresolvedSemanticAlignmentReviewItems"],
        "deterministicScienceDefects":0,
        "renderedDiagramSemanticsVerified":False,
        "academicProofGatesStillOpen":90,
        "formalAcademicPASS":0,
        "newGeminiCalls":0,
        "publicationAuthorized":False,
        "nextAction":"INDEPENDENT_FULL_SCIENTIFIC_SEMANTIC_AND_ACTUAL_DIAGRAM_VERIFIERS",
    })

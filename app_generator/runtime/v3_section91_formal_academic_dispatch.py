"""BSA252 V25: actual Section9.1 formal-answer physics in normal Yoga6 worker.

No external PDF, provider call, release, AI-only proof promotion or mutation.
Independent correct MCQ/interactive answers are computed by executable
Fraction-valued science models and the one selected original textbook.
Limited numeric/scientific proposition coverage is still NOT full academic PASS.
"""
from __future__ import annotations
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

from app_generator.runtime.v3_autonomous_academic_recovery import (
    _V24, _RESULT as _V24_RESULT, _STATUS as _V24_STATUS,
)
from app_generator.runtime.v3_revised_source_proof_rebinding import _signed
from app_generator.runtime.v3_selected_textbook_scientific_provenance import (
    _SOURCE_BINDING,
)
from app_generator.runtime.v3_exact_revised_review_reconciliation import _CANDIDATE
from app_generator.runtime.v3_five_stage_completion import _hash
from app_generator.runtime.v3_native_release_adapter import _v6_checkpoint
from app_generator.runtime.v3_public_bundle_handoff import _trusted_json
from app_generator.runtime.v3_public_nonmerging_draft_pr import _preflight
from app_generator.validation.section91_formal_physics import (
    _SOURCE_SHA, _CANDIDATE_SHA, bounded_section91_science_audit,
)

_V25_PRE = "V25_EXACT_SOURCE_FORMAL_PHYSICS_PRE_CALL.json"
_V25_RESULT = "V25_18_BOUNDED_FORMAL_ANSWER_WITNESSES.json"
_V25 = "V25_SOURCE_BOUND_FORMAL_SCIENCE_DISPATCH_NO_RELEASE.json"
_V25_MCQ_PROOFS = "V25_NINE_MCQ_FORMAL_PHYSICS_PROOFS.json"
_V25_INTERACTIVE_PROOFS = "V25_NINE_INTERACTIVE_FORMAL_PHYSICS_PROOFS.json"
_STATUS25="V25_ALL_18_REAL_SOURCE_BOUND_FORMAL_ANSWER_MODELS_VERIFIED_PARTIAL_ACADEMIC"
_EXPECTED_WITNESSES=68
_EXPECTED_SOURCE_PREMISES=9


def _persist_split_formal_witnesses(
    folder:Path,identity:dict,science:dict,
)->list[dict[str,Any]]:
    """Reuse BSA251's V24 signed small-receipt checkpoint recovery.

    The genuine first BSA252 live attempt produced a 12648-byte aggregate
    proof receipt, which cannot be replay-read by the original 12000-byte
    safe checkpoint parser. Never loosen that size limit: split exact nine
    MCQ and nine interactive rows into two SHA-pinned safe receipts.
    """
    rows=science.get("activityProofs")
    if (not isinstance(rows,list) or len(rows)!=18
            or len({q.get("activityId") for q in rows})!=18
            or sum(q.get("exactRationalAndDimensionalWitnesses",0)
                   for q in rows)!=68):
        raise ValueError("BSA252_EIGHTEEN_FORMAL_PROOFS_REQUIRED")
    manifest=[]
    for kind, name, subset in (
        ("MCQ",_V25_MCQ_PROOFS,rows[:9]),
        ("INTERACTIVE",_V25_INTERACTIVE_PROOFS,rows[9:]),
    ):
        if (len(subset)!=9 or any(q.get("sourceModelFamily")!=(
            "MCQ_FORMAL_PROPOSITION" if kind=="MCQ"
            else "INTERACTIVE_FORMAL_SOLUTION") for q in subset)):
            raise ValueError("BSA252_WRONG_FORMAL_PROOF_PARTITION")
        record=_v6_checkpoint(folder/name,{
            **identity,
            "status":"V25_IMMUTABLE_EXACT_PHYSICS_PROOF_PARTITION",
            "sourcePdfSha256":science["sourcePdfSha256"],
            "revisedCandidateSha256":science["revisedCandidateSha256"],
            "formalModelFamily":kind,
            "proofRows":subset,
            "publicationAuthorized":False,
        })
        if (folder/name).stat().st_size>=12000:
            raise ValueError("BSA252_SIGNED_PROOF_EXCEEDS_HISTORICAL_RESTART_LIMIT")
        manifest.append({
            "formalModelFamily":kind,
            "proofCount":len(subset),
            "savedSha256":record["integritySha256"],
        })
    return manifest


def run_post_v24_formal_science(
    repo:Path,private:Path,ready:dict[str,Any],
    v9:dict,v11:dict,v12:dict,v24:dict,
)->dict[str,Any]:
    """Actual normal-worker historical replay-free BSA252 dispatch."""
    folder,_,_,_,_=_preflight(repo,private,ready,v9,v11,v12)
    prior=_signed(folder,_V24,ready)
    v24_result=_signed(folder,_V24_RESULT,ready)
    if (prior!=v24
            or prior.get("status")!=_V24_STATUS
            or prior.get("resultSha256")!=v24_result["integritySha256"]
            or prior.get("academicFixedPointReached") is not True
            or prior.get("completeAcademicProofGapsStillOpen")!=90
            or prior.get("academicPASS")!=0
            or v24_result.get("independentProofGaps")!=90
            or v24_result.get("newDeterministicDefectSlots")!=0
            or v24_result.get("formalAcademicPassedActivities")!=0
            or v24_result.get("sourceSha256")!=_SOURCE_SHA
            or v24_result.get("candidatePackageSha256")!=_CANDIDATE_SHA
            or v24_result.get("publicationAuthorized") is not False):
        raise ValueError("BSA252_GENUINE_V24_SOURCE_PROOF_QUEUE_REQUIRED")
    binding=_trusted_json(private/_SOURCE_BINDING)
    pdf=Path(binding["sourcePdf"])
    source_root=Path(binding["sourceRoot"])
    if (binding.get("integritySha256")!=_hash({
            k:v for k,v in binding.items() if k!="integritySha256"})
            or binding.get("sourceSha256")!=_SOURCE_SHA
            or binding.get("contract")!=
                "BOSLA_SELECTED_SERWAY_TEXTBOOK_LOCAL_BINDING_V1"
            or binding.get("section")!="9.1"
            or binding.get("externalFallbackAllowed") is not False
            or binding.get("sourcePdfUploaded") is not False
            or pdf.is_symlink() or not pdf.is_file()
            or pdf.resolve()!=(source_root/"9"/"9.1"/"source.pdf").resolve()
            or pdf.resolve().is_relative_to(repo.resolve())):
        raise ValueError("BSA252_ONE_SELECTED_LOCAL_TEXTBOOK_ONLY")
    target=folder/_CANDIDATE
    if (target.is_symlink() or not target.is_file()
            or sha256(target.read_bytes()).hexdigest()!=_CANDIDATE_SHA):
        raise ValueError("BSA252_REVISED_PACKAGE_IS_NOT_EXACT_VERSION")
    identity={
        "gitHead":ready["gitHead"],
        "proposalSha256":ready["proposalSha256"],
        "sourceV24ReceiptSha256":prior["integritySha256"],
        "sourceV24AcademicQueueSha256":v24_result["integritySha256"],
    }
    _v6_checkpoint(folder/_V25_PRE,{
        **identity,
        "status":"PRE_CALL_EXACT_SOURCE_PHYSICS_NO_PROVIDER",
        "sourcePdfSha256":_SOURCE_SHA,
        "candidatePackageSha256":_CANDIDATE_SHA,
        "geminiRequestsPermitted":False,
        "externalPdfAcquisitionPermitted":False,
        "publicationAuthorized":False,
    })
    science=bounded_section91_science_audit(
        source_pdf=pdf,source_sha=_SOURCE_SHA,package_file=target)
    if (science.get("status")!=
            "BSA252_ALL_18_SOURCE_BOUND_BOUNDED_FORMAL_ANSWER_MODELS_VERIFIED"
            or science.get("independentlyReextractedTextbookPhysicsPremises")!=
               _EXPECTED_SOURCE_PREMISES
            or science.get("boundedFormalAnswerItemWitnesses")!=_EXPECTED_WITNESSES
            or science.get("modelledMcqActivities")!=9
            or science.get("modelledInteractiveActivities")!=9
            or len(science.get("activityProofs",[]))!=18
            or science.get("completeIndependentAcademicProofGatePASS")!=0
            or science.get("formalAcademicActivityPASS")!=0
            or science.get("newGeminiCalls")!=0
            or science.get("newExternalPdfsRequired") is not False
            or science.get("publicationAuthorized") is not False
            or any(row.get("fullScientificAcademicPASS") is not False
                   or row.get("allEnglishStatementAndTranslatedSemanticsVerified") is not False
                   for row in science["activityProofs"])):
        raise ValueError("BSA252_BOUNDED_PROOF_NOT_FULL_ACCEPTANCE")
    # BSA251 historical repair is mandatory: old 12 KB reader limit
    # remains intact; V25's full 18-row proof list MUST be split safely.
    partitions=_persist_split_formal_witnesses(folder,identity,science)
    bounded={key:value for key,value in science.items()
             if key!="activityProofs"}
    result=_v6_checkpoint(folder/_V25_RESULT,{
        **identity,
        **bounded,
        "status":"V25_REAL_18_ACTIVITY_BOUNDED_FORMAL_PROOFS_EXECUTED_NO_RELEASE",
        "splitImmutableProofReceipts":partitions,
        "completeFormalProofRosterSha256":_hash(science["activityProofs"]),
        "sourcePdfNotUploaded":True,
        "oldReviewClaimsNotReplayed":True,
        "academicProofGatesStillOpen":90,
        "publicationAuthorized":False,
    })
    if (folder/_V25_RESULT).stat().st_size>=12000:
        raise ValueError("BSA252_RESTART_SAFE_AGGREGATE_SIZE_FAILED")
    return _v6_checkpoint(folder/_V25,{
        **identity,
        "status":_STATUS25,
        "resultSha256":result["integritySha256"],
        "independentlyReextractedTextbookPhysicsPremises":_EXPECTED_SOURCE_PREMISES,
        "boundedFormalAnswerItemWitnesses":_EXPECTED_WITNESSES,
        "formalModelledActivities":18,
        "academicProofGatesStillOpen":90,
        "formalAcademicPASS":0,
        "newGeminiCalls":0,
        "externalPdfAcquisition":False,
        "publicationAuthorized":False,
        "nextEligibleMilestone":"SOURCE_BOUND_FULL_DISTRACTOR_MEANING_AND_MULTILINGUAL_PROOFS",
    })

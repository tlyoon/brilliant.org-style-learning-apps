"""BSA314: inexpensive, source-bound A28 check BEFORE a new owner V36 rebuild.

This is a read-only failure-localization step. It cannot sign a scientific
receipt, increment academic acceptance or replace hosted exact-head CI/V36.
It reuses only the signed prior original Serway checkpoint and canonical
candidate, never an outside textbook or a generated mock source.
"""
from __future__ import annotations

from pathlib import Path

from app_generator.runtime.v3_long_horizon_development import read_long_horizon_development
from app_generator.runtime.v3_selected_textbook_scientific_provenance import _SOURCE_BINDING
from app_generator.runtime.v3_exact_revised_review_reconciliation import _CANDIDATE
from app_generator.runtime.v3_public_bundle_handoff import _trusted_json
from app_generator.runtime.v3_revised_source_proof_rebinding import _signed
from app_generator.runtime.v3_vector_explanation_academic_admission import _FRONTIER
from app_generator.validation.section91_vector_explanation_proof import (
    independently_prove_vector_explanation,
    independently_check_vector_explanation_witness,
)


def preflight_next_a28_before_rebuild(*,private:Path,current_head:str)->dict:
    """Check the pending A28 source/row without writing any private artifact.

    A failed known task stops a costly rebuilt-V36 operation at its earliest
    attributable failure. When it passes, NORMAL owner V36 + signed readback
    remain fully mandatory. Previously signed A28 is not replayed.
    """
    if not isinstance(private,Path) or not isinstance(current_head,str) or len(current_head)!=40:
        raise ValueError("BSA314_PREFLIGHT_OWNER_INPUTS_REQUIRED")
    latest=read_long_horizon_development(private)
    if latest.get("gitHead")==current_head:
        return {"status":"BSA314_SAME_HEAD_NO_REBUILD",
                "academicAcceptanceAdvanced":False}
    frontier=private/"long-horizon-development"/_FRONTIER
    if frontier.is_file() and not frontier.is_symlink():
        return {"status":"BSA314_A28_ALREADY_SIGNED_NO_PREFLIGHT",
                "academicAcceptanceAdvanced":False}
    ready={"gitHead":latest["gitHead"],"proposalSha256":latest["proposalSha256"]}
    folder=private/"owner-five-stage-completion"/latest["gitHead"]/latest["proposalSha256"]
    candidate=folder/_CANDIDATE
    try:
        source=Path(_trusted_json(private/_SOURCE_BINDING)["sourcePdf"])
        # The producer authenticates BOTH exact input hashes and rereads
        # original physics passages. The signed prior V36 row is separately
        # authenticated and checked against the canonical A28 task ID.
        proof=independently_prove_vector_explanation(
            source_pdf=source,candidate_path=candidate)
        independently_check_vector_explanation_witness(proof)
        part=_signed(folder,"V36_PARTITION_01.json",ready)
        rows=part["activity"]["evidenceRows"]
        hits=[row for row in rows if row.get("taskId")==proof["taskId"]]
        if (len(hits)!=1
            or hits[0].get("kind")!="COMPLETE_SCIENTIFIC_MEANING"
            or hits[0].get("status")!="BOUNDED_SUPPORT_ONLY_REVIEW_REQUIRED"
            or hits[0].get("surfaceSha256")!=proof["surfaceSha256"]):
            raise ValueError("BSA314_A28_SIGNED_ROW_AND_CANONICAL_TASK_DISAGREE")
    except (OSError,ValueError,KeyError,IndexError,TypeError) as exc:
        # Never expose original textbook text or candidate content in logs.
        raise ValueError("BSA314_A28_ORIGINAL_SOURCE_PREFLIGHT_FAILED") from exc
    return {"status":"BSA314_A28_ORIGINAL_SOURCE_PREFLIGHT_PASS",
            "academicAcceptanceAdvanced":False,
            "sourceBound":True,
            "signedOriginalRowReverified":True,
            "mustRunNormalOwnerV36":True,
            "publicationAuthorized":False}

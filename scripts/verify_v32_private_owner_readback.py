"""BSA260 independently re-read original Serway, all V29–V32 signed proofs.

Recomputes all 8 other MCQ localized source role-witness hashes directly from
exact unchanged candidate; separately re-decodes true Chrome PNG evidence.
"""
from __future__ import annotations

from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from app_generator.runtime.v3_five_stage_completion import _hash
from app_generator.runtime.v3_revised_source_proof_rebinding import _signed
from app_generator.runtime.v3_post_v31_other_mcq_locale_roles import (
    _V32,_V32_CHUNK_A,_V32_CHUNK_B,_STATUS32,
)
from app_generator.runtime.v3_post_v30_bounded_mcq_semantics import _V31
from app_generator.runtime.v3_exact_revised_review_reconciliation import _CANDIDATE
from app_generator.runtime.v3_selected_textbook_scientific_provenance import _SOURCE_BINDING
from app_generator.runtime.v3_public_bundle_handoff import _trusted_json
from app_generator.validation.section91_formal_physics import _SOURCE_SHA,_CANDIDATE_SHA
from app_generator.validation.section91_other_mcq_locale_roles import (
    bound_all_other_mcq_locale_option_roles,
)
from scripts.verify_v31_private_owner_readback import main as verify_v31


def main()->None:
    # Execute independent PNG decoder and first-MCQ source witness too.
    verify_v31()
    head=subprocess.run(["git","rev-parse","HEAD"],cwd=ROOT,check=True,
                         capture_output=True,text=True,timeout=20).stdout.strip()
    loc=os.environ.get("LOCALAPPDATA")
    if not loc or len(head)!=40:
        raise ValueError("BSA260_INDEPENDENT_HEAD_OR_PRIVATE_ROOT_MISSING")
    private=Path(loc)/"Microvid"/"BoslaV3ReviewYoga6"
    ready={"gitHead":head,
           "proposalSha256":"738a612d6d192cae715858c226bf0f952ceeb0a2df823502d15a387448b968b0"}
    folder=private/"owner-five-stage-completion"/head/ready["proposalSha256"]
    v31=_signed(folder,_V31,ready)
    v32=_signed(folder,_V32,ready)
    a=_signed(folder,_V32_CHUNK_A,ready)
    b=_signed(folder,_V32_CHUNK_B,ready)
    if (v32.get("status")!=_STATUS32
            or v32.get("sourceV31ReceiptSha256")!=v31["integritySha256"]
            or v32.get("otherMcqSourceRoleReceiptASha256")!=a["integritySha256"]
            or v32.get("otherMcqSourceRoleReceiptBSha256")!=b["integritySha256"]
            or v32.get("allNineMcqLocalizedOptionRolesChecked")!=108
            or v32.get("allNineMcqFormalFalseAlternativeCounterexamples")!=27
            or v32.get("otherEightMcqExplanationPromptRolesChecked")!=48
            or v32.get("completeAcademicProofGatesStillOpen")!=90
            or v32.get("independentMeaningMicroproofsPending")!=429
            or v32.get("fullAcademicPASS")!=0
            or v32.get("newModelCalls")!=0
            or v32.get("publicationAuthorized") is not False):
        raise ValueError("BSA260_SIGNED_V32_NOT_SOURCE_BOUND_OR_FALSE_ACADEMIC_PASS")
    binding=_trusted_json(private/_SOURCE_BINDING)
    pdf=Path(binding["sourcePdf"])
    candidate=folder/_CANDIDATE
    if (pdf.is_symlink() or not pdf.is_file()
            or candidate.is_symlink() or not candidate.is_file()
            or sha256(pdf.read_bytes()).hexdigest()!=_SOURCE_SHA
            or sha256(candidate.read_bytes()).hexdigest()!=_CANDIDATE_SHA):
        raise ValueError("BSA260_INDEPENDENT_SINGLE_ORIGINAL_SOURCE_CHANGED")
    roles=bound_all_other_mcq_locale_option_roles(
        source_pdf=pdf,package_file=candidate)
    saved=a.get("activities",[])+b.get("activities",[])
    if len(saved)!=8:
        raise ValueError("BSA260_WRONG_TWO_SIGNED_SMALL_FOUR_MCQ_RECEIPTS")
    for stored,independent in zip(saved,roles["sourceBoundActivityWitnesses"],
                                   strict=True):
        if (stored.get("activityId")!=independent["activityId"]
                or stored.get("correctAnswerModel")!=independent["correctAnswerModel"]
                or stored.get("falseOptionsModelled")!=independent["falseOptionsModelled"]
                or stored.get("fullSourceBoundRoleEvidenceSha256")!=_hash(independent)
                or stored.get("checkedLocaleOptionRoles")!=12
                or stored.get("checkedLocalizedExplanationPromptRoles")!=6):
            raise ValueError("BSA260_INDEPENDENT_LOCALIZED_ROLE_SHA_MISMATCH")
    print(json.dumps({
        "status":"BSA260_INDEPENDENT_ALL_NINE_SERWAY_MCQ_SOURCE_LOCALE_ROLES_PASS",
        "gitHead":head,"sourceSha256":_SOURCE_SHA,
        "candidateSha256":_CANDIDATE_SHA,
        "signedV31Sha256":v31["integritySha256"],
        "signedV32Sha256":v32["integritySha256"],
        "signedV32RoleChunkHashes":[a["integritySha256"],b["integritySha256"]],
        "otherEightMcqSourceRoleProofHashesRecomputed":len(saved),
        "allNineMcqLocalizedOptionsBoundedRechecked":108,
        "allNineMcqFalseAlternativesModelled":27,
        "otherEightLocalizedPromptExplanationRoleChecks":48,
        "realChromeThreeLocalePngReadbackAlsoExecuted":True,
        "completeAcademicProofGatesStillOpen":90,
        "comprehensiveMeaningMicroproofsStillPending":429,
        "fullAcademicPASS":0,"newModelCalls":0,
        "publicationAuthorized":False,
    },sort_keys=True))
if __name__=="__main__":
    main()

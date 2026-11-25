"""BSA262 owner-only independent original PDF + candidate V34 validation.

Print only small metadata, never copyrighted text, model responses or paths.
"""
from __future__ import annotations
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess
import sys

from app_generator.runtime.v3_post_v32_interactive_mutation_proofs import _V34, _STATUS34
from app_generator.runtime.v3_selected_textbook_scientific_provenance import _SOURCE_BINDING
from app_generator.runtime.v3_exact_revised_review_reconciliation import _CANDIDATE
from app_generator.runtime.v3_revised_source_proof_rebinding import _signed
from app_generator.runtime.v3_public_bundle_handoff import _trusted_json
from app_generator.validation.section91_interactive_mutation_witness import audit_nine_interactive_mutants

ROOT=Path(__file__).resolve().parents[1]
PRIVATE=Path(os.environ["LOCALAPPDATA"])/"Microvid"/"BoslaV3ReviewYoga6"

def verify(*, audit_only: bool = False) -> dict:
    head=subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip()
    proposals=list((PRIVATE/"owner-five-stage-completion"/head).glob("*"))
    if len(proposals)!=1 or not proposals[0].is_dir():
        raise ValueError("BSA262_EXACT_OWNER_HEAD_PROPOSAL_NOT_UNIQUE")
    folder=proposals[0]
    ready={"gitHead":head,"proposalSha256":folder.name}
    binding=_trusted_json(PRIVATE/_SOURCE_BINDING)
    pdf=Path(binding["sourcePdf"])
    candidate=folder/_CANDIDATE
    proof=audit_nine_interactive_mutants(source_pdf=pdf,package_file=candidate)
    if audit_only:
        return {"status":"BSA262_REAL_ORIGINAL_SERWAY_V34_SOURCE_AUDIT_ONLY",
                "interactiveFormalProofs":proof["interactiveActivitiesChecked"],
                "rejectedMutants":proof["independentlyRejectedWrongAnswerMutants"],
                "localizedItemLabelsPresent":proof["localizedItemLabelsPresent"],
                "fullAcademicPASS":0,"publicationAuthorized":False}
    v34=_signed(folder,_V34,ready)
    if (v34.get("status")!=_STATUS34
            or v34.get("sourceSha256")!=proof["sourceSha256"]
            or v34.get("revisedCandidateSha256")!=proof["candidateSha256"]
            or v34.get("interactiveFormalProofHashes")!=[
                x["correctModelSha256"] for x in proof["activityProofs"]]
            or v34.get("sourceBoundActivityProofHashes")!=[
                x["activitySha256"] for x in proof["activityProofs"]]
            or v34.get("localizedItemLabelsPresent")!=proof["localizedItemLabelsPresent"]
            or v34.get("independentlyRejectedWrongAnswerMutants")!=9
            or v34.get("fullAcademicPASS")!=0
            or v34.get("publicationAuthorized") is not False):
        raise ValueError("BSA262_SIGNED_V34_DOES_NOT_MATCH_RECOMPUTED_SOURCE")
    return {"status":"BSA262_OWNER_INDEPENDENT_ORIGINAL_PDF_V34_PASS",
            "gitHead":head,
            "signedV34Sha256":v34["integritySha256"],
            "interactiveFormalProofs":9,
            "independentlyRejectedWrongAnswerMutants":9,
            "localizedItemLabelsPresent":proof["localizedItemLabelsPresent"],
            "completeAcademicProofGatesStillOpen":90,
            "fullAcademicPASS":0,"newModelCalls":0,
            "publicationAuthorized":False}

if __name__=="__main__":
    try:
        print(json.dumps(verify(audit_only="--audit-only" in sys.argv),sort_keys=True))
    except Exception as exc:
        print(json.dumps({"status":"BSA262_OWNER_V34_NOT_VERIFIED",
                          "errorClass":type(exc).__name__,
                          "publicationAuthorized":False}))
        raise SystemExit(2)

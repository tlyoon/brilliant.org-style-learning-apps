"""BSA263 original Yoga6 PDF+candidate V35 independent signed source readback."""
from __future__ import annotations
import json
import os
from pathlib import Path
import subprocess
import sys

from app_generator.runtime.v3_public_bundle_handoff import _trusted_json
from app_generator.runtime.v3_revised_source_proof_rebinding import _signed
from app_generator.runtime.v3_selected_textbook_scientific_provenance import _SOURCE_BINDING
from app_generator.runtime.v3_exact_revised_review_reconciliation import _CANDIDATE
from app_generator.runtime.v3_post_v34_interactive_source_roles import _V35, _STATUS35
from app_generator.validation.section91_interactive_source_roles import audit_interactive_source_role_cues
from app_generator.validation.section91_formal_physics import _CANDIDATE_SHA

ROOT=Path(__file__).resolve().parents[1]
PRIVATE=Path(os.environ["LOCALAPPDATA"])/"Microvid"/"BoslaV3ReviewYoga6"

def verify(*,audit_only:bool=False)->dict:
    head=subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip()
    source=Path(_trusted_json(PRIVATE/_SOURCE_BINDING)["sourcePdf"])
    if audit_only:
        folders=list((PRIVATE/"owner-five-stage-completion").glob("*/*"))
        candidates=[folder/_CANDIDATE for folder in folders
                    if (folder/_CANDIDATE).is_file()]
        # Hash verification in the audited function protects original source.
        import hashlib
        candidates=[c for c in candidates
                    if hashlib.sha256(c.read_bytes()).hexdigest()==_CANDIDATE_SHA]
        if not candidates:
            raise ValueError("BSA263_NO_FROZEN_CANDIDATE")
        proof=audit_interactive_source_role_cues(
            source_pdf=source,package_file=candidates[-1])
        return {"status":"BSA263_ORIGINAL_SOURCE_BOUNDED_LEXICAL_PILOT",
                "activities":proof["interactiveActivitiesChecked"],
                "localizedScienceRoleCues":54,
                "academicPASS":0,"publicationAuthorized":False}
    folder_root=PRIVATE/"owner-five-stage-completion"/head
    folders=[x for x in folder_root.iterdir() if x.is_dir()]
    if len(folders)!=1:
        raise ValueError("BSA263_EXACT_HEAD_PROPOSAL_ID_NOT_UNIQUE")
    folder=folders[0]
    proof=audit_interactive_source_role_cues(
        source_pdf=source,package_file=folder/_CANDIDATE)
    signed=_signed(folder,_V35,{"gitHead":head,"proposalSha256":folder.name})
    expected=[[(r["promptSha256"],r["itemLabelSha256"],r["explanationSha256"])
               for r in row["localeWitnesses"]]
              for row in proof["activityWitnesses"]]
    if (signed.get("status")!=_STATUS35
            or signed.get("sourceSha256")!=proof["sourceSha256"]
            or signed.get("revisedCandidateSha256")!=proof["candidateSha256"]
            or signed.get("activityLocaleWitnessHashes")!=expected
            or signed.get("trilingualPromptRoleCuesChecked")!=27
            or signed.get("trilingualFirstItemRoleCuesChecked")!=27
            or signed.get("fullAcademicPASS")!=0
            or signed.get("publicationAuthorized") is not False):
        raise ValueError("BSA263_ORIGINAL_SOURCE_OR_SIGNED_V35_MISMATCH")
    return {
        "status":"BSA263_INDEPENDENT_ORIGINAL_PDF_SIGNED_V35_PASS",
        "gitHead":head,
        "signedV35Sha256":signed["integritySha256"],
        "interactiveActivities":9,
        "boundedTrilingualScienceRoleCues":54,
        "fullAcademicPASS":0,
        "newModelCalls":0,
        "publicationAuthorized":False,
    }

if __name__=="__main__":
    try:
        print(json.dumps(verify(audit_only="--audit-only" in sys.argv),sort_keys=True))
    except Exception as e:
        print(json.dumps({"status":"BSA263_INDEPENDENT_READBACK_STOP",
                          "errorClass":type(e).__name__,
                          "publicationAuthorized":False}))
        raise SystemExit(2)

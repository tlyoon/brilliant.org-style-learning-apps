"""BSA223: native V3 release-gate adapter, reusing only saved genuine role pairs.

The six corrected science-reviewed packages get separate HMAC-attested private
V3 technical receipts only after exact committed+hosted CI, two real Chrome
runs, privacy QA, source-derived Gemini reviews and matching immutable
five-stage evidence. This does NOT merge, publish, grant institutional privacy
permission, or replay a single external model request.
"""
from __future__ import annotations

from collections import defaultdict
from hashlib import sha256
import json
import os
from pathlib import Path
import re
import tempfile

from app_generator.runtime.v3_versioned_acceptance_scope import _encoded
from app_generator.runtime.v3_standing_paid_science import _bytes
from app_generator.runtime.v3_five_stage_completion import (
    _BASE, _STAGE_NAMES, _checked_stage, _candidate_dir,
    _files_snapshot, _hash,
)
from app_generator.validation.autonomous_completion import (
    _build_review_report, _validate_cached_review, package_identity,
    verify_automated_release_assessment, seal_private_release_receipt,
    read_private_release_receipt,
)
from app_generator.runtime.academic_release import enforce_academic_release_gate

_V6="V6_GENUINE_NATIVE_V3_RELEASE_ATTESTATION"
_RESULT="SIX_PRIVATE_NATIVE_V3_RELEASE_ATTESTATIONS_VERIFIED_NO_PUBLIC_DEPLOY"
_SHA64=re.compile(r"^[0-9a-f]{64}$")


def _safe_json(path:Path, *,maxbytes:int)->dict:
    if path.is_symlink() or not path.is_file() or path.stat().st_size>maxbytes:
        raise ValueError("V3_NATIVE_ADAPTER_UNSAFE_PRIVATE_PROOF")
    doc=json.loads(path.read_text(encoding="utf8"))
    if not isinstance(doc,dict):
        raise ValueError("V3_NATIVE_ADAPTER_INVALID_PRIVATE_PROOF")
    return doc


def _candidate_rows(private:Path,manifest:dict,packages:list)->dict:
    """Source SHA, exact role prompts and immutable Gemini aggregates only.

    The proposal and _source_bound_packages have independently verified the
    original and revised source provenance; this second independent audit
    matches EVERY reused role row back to its genuine persisted report.
    """
    reuse=manifest.get("potentiallyReusableOriginalPasses")
    if not isinstance(reuse,list) or len(reuse)!=103:
        raise ValueError("V3_NATIVE_ADAPTER_UNEXPECTED_103_REUSE")
    witness:dict[str,list[dict]]=defaultdict(list)
    originals=sorted(private.glob("v3-generated-*/batches/v3-assessment-*.json"))
    if not originals or len(originals)>300:
        raise ValueError("V3_NATIVE_ADAPTER_MODEL_EVIDENCE_INVENTORY_MISSING")
    for file in originals:
        if (file.parent.is_symlink() or file.parent.parent.is_symlink()
                or file.is_symlink()):
            raise ValueError("V3_NATIVE_ADAPTER_UNSAFE_ASSESSMENT_PATH")
        doc=_safe_json(file,maxbytes=8_000_000)
        rawrows=doc.get("reviews",[])
        if not isinstance(rawrows,list) or len(rawrows)>200:
            raise ValueError("V3_NATIVE_ADAPTER_BAD_REVIEW_ROWS")
        for row in rawrows:
            if not isinstance(row,dict) or row.get("status")!="AI_CONSENSUS_PASS":
                continue
            for encoder in (_encoded,_bytes):
                key=sha256(encoder(row)).hexdigest()
                if not any(saved==row for saved in witness[key]):
                    witness[key].append(row)
    activities={
        (f"section-9-{number}",row["id"]):row
        for number,_,items in packages for row in items
    }
    matched={}
    for item in reuse:
        if (not isinstance(item,dict)
                or item.get("status")!="POTENTIALLY_REUSABLE_NOT_RELEASE_ACCEPTED"):
            raise ValueError("V3_NATIVE_ADAPTER_UNTRUSTED_REUSE_MANIFEST")
        key=(item.get("section"),item.get("activityId"))
        digest=item.get("sourceReviewSha256")
        if (key not in activities or not isinstance(digest,str)
                or not _SHA64.fullmatch(digest) or key in matched
                or len(witness.get(digest,[]))!=1):
            raise ValueError("V3_NATIVE_ADAPTER_REUSED_REAL_REVIEW_NOT_UNIQUE")
        row=witness[digest][0]
        _validate_cached_review(activities[key],row)
        matched[key]=row

    changed={("section-9-2",13):manifest["isolatedReviewSliceSha256"]}
    science=manifest["section96ScientificFailureReplacement"]
    if (science.get("changedActivityIndices")!=[5,9]
            or science.get("originalIndex9ScientificFailurePreserved") is not True
            or science.get("originalIndex6ProviderUnknownPreserved") is not True):
        raise ValueError("V3_NATIVE_ADAPTER_FROZEN_HISTORY_NOT_PRESERVED")
    for entry in science["independentNewVersionGeminiEvidence"]:
        key=("section-9-6",entry["index"])
        if key in changed or entry.get("genuineConsensusPass") is not True:
            raise ValueError("V3_NATIVE_ADAPTER_INVALID_REVISED96_ROLE_PROOF")
        changed[key]=entry["reviewSliceSha256"]
    final=manifest["finalTwoNewVersionGenuineScience"]
    if (final.get("originalSection91Index0UnknownPreserved") is not True
            or final.get("originalSection96Index6UnknownPreserved") is not True
            or final.get("reviewedNewSourceOnly") is not True):
        raise ValueError("V3_NATIVE_ADAPTER_OLD_UNKNOWN_ROLE_REPLAY")
    for entry in final["proofs"]:
        key=(entry["section"],entry["index"])
        if key in changed or entry.get("genuineConsensusPass") is not True:
            raise ValueError("V3_NATIVE_ADAPTER_INVALID_FINAL_TWO_ROLE_PROOF")
        changed[key]=entry["reviewSliceSha256"]
    if set(changed)!={
        ("section-9-1",0),("section-9-2",13),
        ("section-9-6",5),("section-9-6",6),("section-9-6",9)
    }:
        raise ValueError("V3_NATIVE_ADAPTER_UNEXPECTED_CHANGED_CONTENT")
    for (section,index),digest in changed.items():
        if not isinstance(digest,str) or not _SHA64.fullmatch(digest):
            raise ValueError("V3_NATIVE_ADAPTER_MISSING_SLICE_SHA")
        assessment=(private/("v3-generated-"+digest)/"batches"/
                    ("v3-assessment-"+digest+".json"))
        saved=_safe_json(assessment,maxbytes=8_000_000)
        if (saved.get("packageSha256")!=digest
                or saved.get("activitiesTotal")!=1
                or saved.get("activitiesAssessed")!=1
                or saved.get("status")!="AI_ASSESSED_PASS"
                or len(saved.get("reviews",[]))!=1):
            raise ValueError("V3_NATIVE_ADAPTER_MISSING_GENUINE_REVISED_PASS")
        activity=packages[int(section[-1])-1][2][index]
        row=saved["reviews"][0]
        if row["activityId"]!=activity["id"]:
            raise ValueError("V3_NATIVE_ADAPTER_REVISED_ACTIVITY_ID_CHANGED")
        _validate_cached_review(activity,row)
        key=(section,activity["id"])
        if key in matched:
            raise ValueError("V3_NATIVE_ADAPTER_REVISED_STALE_ORIGINAL_ROW")
        matched[key]=row
    if len(matched)!=108 or len(activities)!=108 or set(matched)!=set(activities):
        raise ValueError("V3_NATIVE_ADAPTER_MODEL_COVERAGE_NOT_108")
    return matched


def _validate_gate_inputs(private:Path,repo:Path,ready:dict,packages:list)->tuple[Path,dict]:
    head=ready["gitHead"]
    proposal=ready["proposalSha256"]
    folder=private/_BASE/head/proposal
    stages=[
        _checked_stage(folder/(name+".json"),head=head,source=proposal)
        for name in _STAGE_NAMES
    ]
    if (len(stages)!=5 or any(stage is None for stage in stages)
            or any(stage.get("status")!="PASS_PRIVATE_ONLY" for stage in stages[:4])
            or stages[4].get("status")!="READY_FOR_NEXT_AUTHORIZED_STAGE"
            or stages[4].get("sourceFreeDownstreamWorkExecuted") is not True
            or stages[4].get("sourceFreePublicAdapter",{}).get("status")
               !="PRIVATE_RELEASE_ADAPTER_EVIDENCE_VERIFIED"
            or stages[3].get("stagedRealBrowserChecks")!=698
            or stages[3].get("faultInjectedRollbackRestoredAndVerified") is not True
            or stages[1].get("technicalPrivacyChecksPassed") is not True
            or stages[2].get("originalScientificReadinessSha256")
               !=ready["integritySha256"]
            or stages[2].get("realBrowserReceiptSha256")
               !=ready["browserReceiptSha256"]
            or stages[2].get("exactHeadHostedCiSuccess") is not True):
        raise ValueError("V3_NATIVE_ADAPTER_FIVE_STAGE_REAL_QA_MISSING")
    preview=_candidate_dir(private,head,proposal)
    if _hash({"files":_files_snapshot(preview)})!=stages[3].get("stagedFilesSha256"):
        raise ValueError("V3_NATIVE_ADAPTER_PREVIEW_HASH_NOT_VERIFIED")
    for number,raw,_ in packages:
        package=(preview/"content"/"chapter-9"/f"section-9-{number}"/"package.json")
        if package.is_symlink() or package.read_bytes()!=raw:
            raise ValueError("V3_NATIVE_ADAPTER_STAGED_PACKAGE_CHANGED")
    return folder,stages[4]


def _v6_checkpoint(path:Path,body:dict)->dict:
    if path.is_symlink():
        raise ValueError("V3_NATIVE_ADAPTER_UNSAFE_V6_CHECKPOINT")
    result={**body,"integritySha256":_hash(body)}
    if path.exists():
        if _safe_json(path,maxbytes=12000)!=result:
            raise ValueError("V3_NATIVE_ADAPTER_V6_CHECKPOINT_CHANGED")
        return result
    fd,temp=tempfile.mkstemp(prefix=".native-v3-attestation-",suffix=".tmp",
                            dir=path.parent)
    try:
        with os.fdopen(fd,"w",encoding="utf8") as file:
            json.dump(result,file,sort_keys=True,indent=2)
            file.write("\n")
            file.flush()
            os.fsync(file.fileno())
        os.replace(temp,path)
    finally:
        Path(temp).unlink(missing_ok=True)
    return result


def run_exact_native_release_adapter(
    repo:Path,private:Path,ready:dict,packages:list
)->dict:
    """One normal recovery step, exact hosted evidence; no outbound I/O."""
    if (ready.get("status")!="VERSIONED_SCIENCE_BROWSER_AND_CI_VERIFIED_UNADMITTED"
        or ready.get("exactHeadHostedCiSuccess") is not True
        or ready.get("codeWorkingTreeClean") is not True
        or ready.get("publicationAuthorized") is not False
        or ready.get("proposedContentScientificCoverage")!=108
        or ready.get("realChromeChecks")!=698):
        raise ValueError("V3_NATIVE_ADAPTER_EXACT_HOSTED_READINESS_MISSING")
    from app_generator.runtime.v3_versioned_readiness import (
        _read_previous, _git_info, _git_clean, _hosted_runs, _exact_ci_success,
    )
    if _read_previous(private/"v3-current-versioned-evidence-readiness.json")!=ready:
        raise ValueError("V3_NATIVE_ADAPTER_SAVED_READINESS_MISMATCH")
    head=ready["gitHead"]
    actual_head,branch=_git_info(repo)
    if (actual_head!=head or not _git_clean(repo)
            or not _exact_ci_success(_hosted_runs(repo,branch),head)):
        raise ValueError("V3_NATIVE_ADAPTER_NOT_CURRENT_CLEAN_HOSTED_CI")
    proposal=ready["proposalSha256"]
    folder,_=_validate_gate_inputs(private,repo,ready,packages)
    manifest_file=private/"versioned-course-proposals"/proposal/"scope-proposal.json"
    manifest=_safe_json(manifest_file,maxbytes=800000)
    if (manifest.get("integritySha256")!=proposal
            or sha256(_encoded({k:v for k,v in manifest.items()
                               if k!="integritySha256"})).hexdigest()!=proposal
            or manifest.get("publicationAuthorized") is not False):
        raise ValueError("V3_NATIVE_ADAPTER_UNTRUSTED_SOURCE_ROSTER")
    actual=_candidate_rows(private,manifest,packages)
    if len(actual)!=108 or not isinstance(actual,dict):
        raise ValueError("V3_NATIVE_ADAPTER_INVALID_MODEL_ASSEMBLY")
    preflight=[]
    # Verify ALL six with the pre-existing native V3 gate BEFORE emitting any
    # locally signed receipt. A model failure anywhere leaves no partial PASS.
    for number,raw,items in packages:
        name=f"section-9-{number}"
        digest,validated=package_identity(raw)
        if len(validated)!=18 or validated!=items:
            raise ValueError("V3_NATIVE_ADAPTER_INVALID_PACKAGE_INPUT")
        rows=[actual[(name,item["id"])] for item in items]
        assessment=_build_review_report(digest,items,rows)
        checks={"packageSha256":digest,"gitHead":head,"ciHead":head,
                "ciConclusion":"success","browserResult":"PASS",
                "privacyResult":"PASS"}
        verify_automated_release_assessment(raw,assessment,checks)
        preflight.append((number,raw,digest,assessment,checks))
    outputs=[]
    for number,raw,digest,assessment,checks in preflight:
        receipt_dir=folder/"native-v3-exact-attestations"/f"section-9-{number}"
        if receipt_dir.is_symlink():
            raise ValueError("V3_NATIVE_ADAPTER_LINKED_ATTESTATION_FOLDER")
        receipt=receipt_dir/"autonomous-v3-release-receipt.json"
        if receipt.exists():
            if receipt.is_symlink():
                raise ValueError("V3_NATIVE_ADAPTER_LINKED_ATTESTATION_RECEIPT")
            record=_safe_json(receipt,maxbytes=2_000_000)
            if (record.get("assessment")!=assessment
                    or record.get("checks")!=checks):
                raise ValueError("V3_NATIVE_ADAPTER_STALE_ATTESTED_MODEL_CONTENT")
        else:
            seal_private_release_receipt(raw,assessment,checks,receipt_dir)
        original=read_private_release_receipt(raw,receipt)
        staged=(_candidate_dir(private,head,proposal)/"content"/"chapter-9"/
                f"section-9-{number}"/"package.json")
        result=enforce_academic_release_gate(repo,staged,receipt_dir)
        if (original!=result or result.get("automatedTechnicalEligible") is not True
                or result.get("artifactSha256")!=digest):
            raise ValueError("V3_NATIVE_ADAPTER_NATIVE_RELEASE_GATE_REJECTED")
        outputs.append({
            "section":f"section-9-{number}",
            "packageSha256":digest,
            "activityCount":18,
            "savedGenuineReviewerPairCount":18,
            "privateAttestationSha256":sha256(receipt.read_bytes()).hexdigest(),
            "nativeV3TechnicalGatePassed":True,
        })
    report={
        "contract":"BOSLA_NATIVE_V3_EXACT_RELEASE_ADAPTER_V1",
        "status":_RESULT,
        "gitHead":head,"proposalSha256":proposal,
        "sourceFiveStageReceiptSha256":
            _checked_stage(folder/(_STAGE_NAMES[4]+".json"),
                           head=head,source=proposal)["integritySha256"],
        "sourceGenuineTwoReviewerPositions":108,
        "packages":outputs,"packageCount":6,"totalActivities":108,
        "nativeV3TechnicalReleaseChecksPassed":6,
        "historicalOriginalScienceLedgerAltered":False,
        "originalAmbiguousRolesReplayed":False,
        "newGeminiCalls":0,
        "technicalReleaseEligibilityOnly":True,
        "publicDeployExecuted":False,
        "publicMergeExecuted":False,
        "institutionalPrivacyCertificationClaimed":False,
        "publicationAuthorized":False,
    }
    signed=_v6_checkpoint(folder/(_V6+".json"),report)
    return {**report,"integritySha256":signed["integritySha256"]}

"""BSA250: separately authorized NEW revised Section9.1 model-review inputs.

An old frozen Chapter9 campaign is NOT reopened. This stage checks genuine
V22 source/version receipts and presents ONLY four NEW, exact activity
review slices to the existing one-shot two-role Gemini V3 engine. It never
uploads source PDFs or excerpts, replays an old/uncertain role, or infers
full scientific, textbook, visual or multilingual acceptance from AI votes.
"""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import time
from typing import Any, Callable

from app_generator.runtime.v3_exact_revised_review_reconciliation import (
    _V22, _RESULT22, _QUEUE, _STATUS22,
)
from app_generator.runtime.v3_revised_source_proof_rebinding import (
    _signed, _V21, _RESULT21,
)
from app_generator.runtime.v3_malay_auto_revision import _CANDIDATE
from app_generator.runtime.v3_selected_textbook_scientific_provenance import (
    _SOURCE_BINDING,
)
from app_generator.runtime.v3_five_stage_completion import _hash
from app_generator.runtime.v3_public_bundle_handoff import _trusted_json
from app_generator.runtime.v3_standing_paid_science import (
    authorize_standing, section91_evidence,
)
from app_generator.runtime.v3_section96_authorized_revised_qa import (
    unsent_revised_input, read_prior_two_role_science,
    verify_persisted_two_role_science,
)
from app_generator.validation.autonomous_completion import package_identity

_SCHEMA = "BOSLA_V3_NEW_PRIVATE_REVISED_91_FOUR_ACTIVITY_MODEL_QA_V1"


def _one(raw_activity: dict[str, Any], *, package_sha: str,
         section_index: int) -> tuple[bytes, str]:
    package = {
        "schema": _SCHEMA,
        "sourcePackageSha256": package_sha,
        "sourceSection": "section-9-1",
        "sourceActivityIndex": section_index,
        "sourcePdfUploaded": False,
        "originalReviewerClaimsTransferred": False,
        "activities": [raw_activity],
    }
    raw = (json.dumps(package, indent=2, ensure_ascii=False,
                      sort_keys=True) + "\n").encode("utf8")
    digest, activities = package_identity(raw)
    if len(activities) != 1 or activities[0] != raw_activity:
        raise ValueError("V23_CORRUPT_NEW_SINGLE_ACTIVITY_MODEL_REVIEW_INPUT")
    return raw, digest


def fresh_revised91_inputs(
    *, repo: Path, private: Path, source_head: str,
    proposal_sha: str,
) -> dict[str, Any]:
    """Read source version and exact prior receipts; no API or files written."""
    if (not isinstance(source_head, str) or len(source_head) != 40
            or not isinstance(proposal_sha, str) or len(proposal_sha) != 64
            or any(c not in "0123456789abcdef" for c in source_head + proposal_sha)):
        raise ValueError("V23_PRECISE_SIGNED_V22_SOURCE_ID_REQUIRED")
    repo = repo.resolve(strict=True)
    if (not private.is_absolute() or private.is_symlink()
            or private.resolve().is_relative_to(repo)):
        raise ValueError("V23_UNSAFE_PRIVATE_EVIDENCE_ROOT")
    folder = (private / "owner-five-stage-completion" /
              source_head / proposal_sha)
    if folder.is_symlink() or not folder.is_dir():
        raise ValueError("V23_SIGNED_V22_PRIVATE_CHECKPOINT_MISSING")
    ready = {"gitHead":source_head,"proposalSha256":proposal_sha}
    v22 = _signed(folder, _V22, ready)
    r22 = _signed(folder, _RESULT22, ready)
    v21 = _signed(folder, _V21, ready)
    r21 = _signed(folder, _RESULT21, ready)
    if (v22.get("status") != _STATUS22
            or v22.get("resultSha256") != r22["integritySha256"]
            or v22.get("sourceV21ReceiptSha256") != v21["integritySha256"]
            or v21.get("resultSha256") != r21["integritySha256"]
            or r22.get("existingVerifiedOriginalReviewerPairs") != 17
            or r22.get("advisoryHistoricallyVerifiedIdenticalRolePairs") != 13
            or r22.get("changedActivityOldPairsNotTransferred") != 4
            or r22.get("originalIndex0UncertainQuarantined") is not True
            or v22.get("oldUncertainRoleReplayed") is not False
            or v22.get("newGeminiCalls") != 0
            or v22.get("formalAcademicPASS") != 0
            or r22.get("independentFullAcademicProofSlotsOpen") != 90):
        raise ValueError("V23_REVISED_91_SIGNED_EVIDENCE_ORIGINAL_FROZEN_REPLAY_STOP")
    binding = _trusted_json(private / _SOURCE_BINDING)
    pdf = Path(binding["sourcePdf"])
    source_sha = binding.get("sourceSha256")
    if (binding.get("integritySha256") != _hash({
            k:v for k,v in binding.items() if k!="integritySha256"})
            or binding.get("contract") !=
                "BOSLA_SELECTED_SERWAY_TEXTBOOK_LOCAL_BINDING_V1"
            or binding.get("section") != "9.1"
            or pdf.resolve() !=
                (Path(binding["sourceRoot"]) / "9" / "9.1" / "source.pdf").resolve()
            or binding.get("externalFallbackAllowed") is not False
            or binding.get("sourcePdfUploaded") is not False
            or pdf.is_symlink() or not pdf.is_file()
            or pdf.resolve().is_relative_to(repo)
            or sha256(pdf.read_bytes()).hexdigest() != source_sha
            or r22.get("sourceSha256") != source_sha
            or r21.get("sourceSha256") != source_sha):
        raise ValueError("V23_ORIGINAL_SELECTED_PRIVATE_PDF_CHANGED_OR_UNSAFE")
    candidate_path = folder / _CANDIDATE
    if candidate_path.is_symlink() or not candidate_path.is_file():
        raise ValueError("V23_PRIVATE_REVISED_PACKAGE_MISSING")
    package_raw = candidate_path.read_bytes()
    current_package_sha = sha256(package_raw).hexdigest()
    if (current_package_sha != r22.get("revisedCandidateSha256")
            or current_package_sha != r21.get("revisedCandidateSha256")):
        raise ValueError("V23_REVISED_91_GENERATED_CONTENT_VERSION_CHANGED")
    package = json.loads(package_raw.decode("utf8"))
    activities = package.get("activities")
    if not isinstance(activities,list) or len(activities)!=18:
        raise ValueError("V23_ORIGINAL_18_ACTIVITY_SCOPE_REQUIRED")
    index_by_id = {a["id"]:i for i,a in enumerate(activities)}
    if len(index_by_id)!=18:
        raise ValueError("V23_REVISED_91_DUPLICATED_ACTIVITY_ROSTER")
    stage = folder / _QUEUE
    staged = r22.get("newPrivateVersionedReviewInputsStaged")
    if (not isinstance(staged,list) or len(staged)!=4
            or stage.is_symlink() or not stage.is_dir()
            or len({x.get("activityId") for x in staged}) != 4):
        raise ValueError("V23_EXACT_FOUR_NEW_IMMUTABLE_ROLE_INPUTS_REQUIRED")
    items = []
    for item in staged:
        aid=item["activityId"]
        if aid not in index_by_id:
            raise ValueError("V23_UNDECLARED_NEW_REVIEW_ACTIVITY")
        root = stage / item["reviewInputSha256"]
        if root.is_symlink() or not root.is_dir():
            raise ValueError("V23_NEW_REVISED_REVIEW_INPUT_NOT_PRIVATE")
        content_path = root / "activity.json"
        identity_path = root / "review-identity.json"
        if any(x.is_symlink() or not x.is_file() for x in (content_path, identity_path)):
            raise ValueError("V23_NEW_REVISED_REVIEW_INPUT_LINKED_OR_ABSENT")
        body = content_path.read_bytes()
        identity = identity_path.read_bytes()
        try:
            meta=json.loads(identity.decode("utf8"))
            activity=json.loads(body.decode("utf8"))
        except (ValueError, UnicodeError):
            raise ValueError("V23_NEW_VERSIONED_PRIVATE_ROLE_INPUT_CHANGED") from None
        canonical_sha=sha256(json.dumps(
            activity,sort_keys=True,ensure_ascii=False,
            separators=(",",":")).encode("utf8")).hexdigest()
        if (sha256(identity+body).hexdigest()!=item["reviewInputSha256"]
                or activity!=activities[index_by_id[aid]]
                or canonical_sha!=meta.get("activityCanonicalSha256")
                or meta.get("activityId")!=aid
                or meta.get("sourcePdfSha256")!=source_sha
                or meta.get("candidatePackageSha256")!=current_package_sha
                or meta.get("originalActivityIndex")!=index_by_id[aid]
                or meta.get("providerSubmissionOccurred") is not False
                or meta.get("originalModelClaimsReusable") is not False
                or meta.get("sourcePdfUploadAllowed") is not False):
            raise ValueError("V23_NEW_VERSIONED_PRIVATE_ROLE_INPUT_CHANGED")
        raw,slice_sha = _one(activity,package_sha=current_package_sha,
                             section_index=index_by_id[aid])
        items.append({"index":index_by_id[aid],"activityId":aid,
                      "raw":raw,"sha":slice_sha,
                      "originalStagedSha256":item["reviewInputSha256"]})
    items.sort(key=lambda row:row["index"])
    if len({x["sha"] for x in items})!=4:
        raise ValueError("V23_NEW_SLICE_COLLISION_OR_DUPLICATE")
    return {
        "status":"FOUR_NEW_EXACT_REVISED_91_REVIEW_INPUTS_VERIFIED",
        "sourcePdfSha256":source_sha,
        "revisedCandidateSha256":current_package_sha,
        "sourceHead":source_head,
        "proposalSha256":proposal_sha,
        "stagedReviewInputs":items,
        "oldOriginalUncertainStillQuarantined":True,
        "fullAcademicProofSlotsStillOpen":90,
        "publicationAuthorized":False,
    }


def advance_bounded_revised91(
    *, repo:Path, private:Path, source_head:str, proposal_sha:str,
    execute:bool, transfer:bool, max_activities:int=4,
    max_seconds:int=900, review_one:Callable|None=None,
) -> dict[str,Any]:
    """Use genuine two-role V3 claims, max 8 new calls and zero unsafe replay."""
    authorized = authorize_standing(
        execute=execute,transfer=transfer,
        activities=max_activities,seconds=max_seconds)
    plan = fresh_revised91_inputs(
        repo=repo,private=private,source_head=source_head,
        proposal_sha=proposal_sha)
    if not callable(review_one):
        raise ValueError("V23_REAL_REVIEW_ONE_CALLBACK_REQUIRED")
    from app_generator.runtime.v3_yoga6_recovery import coordinator_lock
    started=time.monotonic()
    outcomes=[]
    with coordinator_lock(private):
        original=section91_evidence(repo/"content"/"chapter-9",repo,private)
        if (original.get("oldUncertainIndex") != 0
                or original.get("originalAssessedUnchanged") != 1):
            raise ValueError("V23_ORIGINAL_UNKNOWN_BECAME_REPLAYABLE")
        for entry in plan["stagedReviewInputs"]:
            if len(outcomes)>=max_activities or time.monotonic()-started>=max_seconds:
                break
            # The SDK call is one-shot per unique NEW slice SHA. Existing
            # incomplete, ambiguous or in-flight roles cannot be replayed.
            if not unsent_revised_input(private,entry["sha"]):
                saved=read_prior_two_role_science(private,entry)
                outcomes.append({
                    "activityId":entry["activityId"],
                    "reviewSliceSha256":entry["sha"],
                    "preexistingCompleteReviewReused":True,
                    "newModelCalls":0,
                    "newConsensusPass":saved["pass"],
                    "newRepairRequired":saved["repair"],
                    "newUncertain":saved["uncertain"],
                })
            else:
                response=review_one(entry["raw"],entry["activityId"],private)
                if not isinstance(response,dict) or response.get("activitiesAssessed")!=1:
                    raise ValueError("V23_GENUINE_REVIEW_CALLBACK_INCOMPLETE")
                saved=verify_persisted_two_role_science(
                    private,entry["raw"],entry["activityId"],
                    entry["sha"],response)
                outcomes.append({
                    "activityId":entry["activityId"],
                    "reviewSliceSha256":entry["sha"],
                    "preexistingCompleteReviewReused":False,
                    "newModelCallsUpperBound":2,
                    "newConsensusPass":saved["pass"],
                    "newRepairRequired":saved["repair"],
                    "newUncertain":saved["uncertain"],
                })
            if outcomes[-1]["newUncertain"]:
                break
    return {
        "status":"V23_NEW_REVISED_91_BOUNDED_REVIEW_ATTEMPT_RECONCILED",
        "sourceHead":source_head,
        "sourcePdfSha256":plan["sourcePdfSha256"],
        "reviewerInputsTotal":4,
        "reviewsHandled":len(outcomes),
        "outcomes":outcomes,
        "maximumNewGeminiCalls":authorized["maxPaidGeminiCalls"],
        "previousOriginalUnknownReplayed":False,
        "sourcePdfUploaded":False,
        "academicAcceptanceGranted":False,
        "independentAcademicProofSlotsStillOpen":90,
        "publicationAuthorized":False,
    }

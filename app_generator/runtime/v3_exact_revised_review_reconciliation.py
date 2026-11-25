"""BSA249/V22: reuse EXACT-unchanged original model evidence on revised 9.1.

The old 17 two-role claims were already verified in V19. Model claims from
identical 13 activities can be inventoried for the new exact private package;
four Malay-revised activities must receive new genuinely independent role
assessments. The original index0 uncertainty NEVER becomes a fresh request.
No source prose, model response or private activity content is put into Git.
No content correctness, scientific semantics, or release is inferred.
"""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
from typing import Any

from app_generator.runtime.v3_five_stage_completion import _hash
from app_generator.runtime.v3_native_release_adapter import _v6_checkpoint
from app_generator.runtime.v3_public_nonmerging_draft_pr import _preflight
from app_generator.runtime.v3_revised_source_proof_rebinding import (
    _V21, _RESULT21, _STATUS21, _signed,
)
from app_generator.runtime.v3_original_reviewer_evidence_reuse import (
    _V19, _STATUS19,
)
from app_generator.runtime.v3_malay_auto_revision import _CANDIDATE, _RECEIPT
from app_generator.runtime.v3_selected_textbook_scientific_provenance import _PACKAGE
from app_generator.runtime.v3_standing_paid_science import (
    section91_evidence, verified_section91_standing_passes,
    authorize_standing,
)

_V22 = "V22_REVISED_91_EXACT_ROLE_REUSE_NO_RELEASE.json"
_PRE22 = "V22_EXACT_REVIEW_VERSION_RECONCILIATION_PRE_CALL.json"
_RESULT22 = "V22_EXACT_REVIEW_VERSION_RECONCILIATION_RESULT.json"
_STATUS22 = "V22_13_UNCHANGED_REVIEW_PAIRS_VERIFIED_4_NEW_SCOPED_NOT_SUBMITTED"
_QUEUE = "V22_PRIVATE_REVISED_ACTIVITY_ROLE_INPUTS"
_REVISED = frozenset({
    "act-mcq-05-third-law-connection",
    "act-mcq-08-isolated-subsystem-fallacy",
    "act-int-05-newton-second-law-steps-order",
    "act-int-08-conservation-validity-select",
})


def _activity_digest(activity: dict[str, Any]) -> str:
    return sha256(json.dumps(activity, sort_keys=True, ensure_ascii=False,
                             separators=(",", ":")).encode("utf8")).hexdigest()


def plan_exact_revised_history(
    *, original: dict[str, Any], candidate: dict[str, Any],
    existing_pairs: list[dict[str, Any]], original_state: dict[str, Any],
    signed_repair: dict[str, Any], source_sha: str,
) -> dict[str, Any]:
    """Compare actual old/new activity bodies, not a file or source label."""
    old = original.get("activities")
    new = candidate.get("activities")
    if (not isinstance(old, list) or not isinstance(new, list)
            or len(old) != 18 or len(new) != 18
            or any(not isinstance(a, dict) or not isinstance(a.get("id"), str)
                   for a in old + new)):
        raise ValueError("V22_EXACT_18_OLD_NEW_ACTIVITIES_REQUIRED")
    old_ids = [a["id"] for a in old]
    new_ids = [a["id"] for a in new]
    if (len(set(old_ids)) != 18 or len(set(new_ids)) != 18
            or old_ids != new_ids):
        raise ValueError("V22_ORIGINAL_AND_REVISED_ROSTER_CHANGED")
    old_by_id = {a["id"]: a for a in old}
    new_by_id = {a["id"]: a for a in new}
    def without_malay(value: Any) -> Any:
        if isinstance(value, dict):
            return {k: without_malay(v) for k, v in value.items() if k != "ms"}
        if isinstance(value, list):
            return [without_malay(x) for x in value]
        return value
    if any(without_malay(old_by_id[aid]) != without_malay(new_by_id[aid])
           for aid in old_ids):
        raise ValueError("V22_OUTSIDE_PRIOR_APPROVED_MALAY_ONLY_SCOPE")
    changed = {aid for aid in old_ids
               if _activity_digest(old_by_id[aid]) != _activity_digest(new_by_id[aid])}
    if (changed != _REVISED or
            changed != set(signed_repair.get("affectedOriginalActivityIds", []))
            or signed_repair.get("repairedActivityCount") != 4):
        raise ValueError("V22_ONLY_FOUR_SUPPORTED_MALAY_REVISIONS_ADMISSIBLE")
    if (original_state.get("oldUncertainIndex") != 0 or
            original_state.get("originalAssessedUnchanged") != 1 or
            len(original_state.get("items", [])) != 17 or
            len(existing_pairs) != 17 or
            {r.get("originalActivityIndex") for r in existing_pairs} != set(range(1, 18))):
        raise ValueError("V22_ORIGINAL_17_ROLE_PAIRS_AND_UNKNOWN_REQUIRED")
    reviewed = {r["activityId"]: r for r in existing_pairs}
    if len(reviewed) != 17 or set(reviewed) != set(old_ids[1:]):
        raise ValueError("V22_WRONG_PREVIOUSLY_REVIEWED_ACTIVITY_IDENTITIES")
    fresh = []
    reused = []
    for index, aid in enumerate(old_ids):
        prior = _activity_digest(old_by_id[aid])
        current = _activity_digest(new_by_id[aid])
        if index == 0:
            if aid in reviewed or prior != current:
                raise ValueError("V22_OLD_UNCERTAIN_ACTIVITY_IDENTITY_CHANGED")
            continue
        receipt = reviewed[aid]
        if (receipt.get("originalActivityIndex") != index
                or receipt.get("activitySha256") != prior
                or receipt.get("sourcePackageSha256") != original_state.get("parentSha256")
                or receipt.get("status") != "POTENTIALLY_REUSABLE_NOT_RELEASE_ACCEPTED"
                or any(not isinstance(receipt.get(k), str) or len(receipt[k]) != 64
                       for k in ("supplementalReviewSliceSha256", "sourceReviewSha256"))):
            raise ValueError("V22_STALE_OR_FABRICATED_ORIGINAL_ROLE_PROOF")
        if aid in changed:
            if prior == current:
                raise ValueError("V22_CHANGED_ACTIVITY_WAS_NOT_REVISED")
            fresh.append({
                "activityId": aid, "originalIndex": index,
                "activityCanonicalSha256": current,
                "sourcePdfSha256": source_sha,
                "priorModelClaimsReused": False,
                "rolesRequired": ["physics", "semantics"],
                "status": "NEW_EXACT_VERSION_ROLE_INPUT_NOT_SUBMITTED",
                "publicationAuthorized": False,
            })
        else:
            if prior != current:
                raise ValueError("V22_UNCHANGED_ROLE_RECEIPT_MISMATCH")
            reused.append({
                "activityId": aid, "originalIndex": index,
                "currentActivitySha256": current,
                "historicalReviewSha256": receipt["sourceReviewSha256"],
                "historicalReviewerPairVerified": True,
                "independentAcademicPASS": False,
            })
    if (len(reused) != 13 or len(fresh) != 4
            or len({r["historicalReviewSha256"] for r in reused}) != 13
            or set(r["activityId"] for r in fresh) != changed
            or set(r["activityId"] for r in reused) & changed):
        raise ValueError("V22_ACTUAL_EXACT_HASH_ROLE_RECONCILIATION_FAILED")
    return {
        "unchangedEvidence": reused,
        "changedRoleInputs": fresh,
        "originalIndex0Quarantined": True,
        "alreadyVerifiedHistoricRolePairs": 17,
        "exactUnchangedHistoricPairsSafeForAdvisoryReuse": 13,
        "changedPreviouslyReviewedPairsDisallowed": 4,
        "newRolePairsStillNeeded": 4,
        "fullAcademicAccepted": 0,
        "publicationAuthorized": False,
    }


def _stage_changed_private(
    *, folder: Path, candidate: dict[str, Any],
    candidate_sha: str, source_sha: str,
    fresh: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Create private immutable, idempotent inputs; SEND NOTHING to provider."""
    root = folder / _QUEUE
    if root.is_symlink() or (root.exists() and not root.is_dir()):
        raise ValueError("V22_REVIEW_INPUT_ROOT_UNSAFE")
    root.mkdir(exist_ok=True)
    by_id = {a["id"]: a for a in candidate["activities"]}
    outputs = []
    for item in fresh:
        aid = item["activityId"]
        body = by_id[aid]
        if _activity_digest(body) != item["activityCanonicalSha256"]:
            raise ValueError("V22_ROLE_INPUT_CONTENT_CHANGED")
        packet = {
            "contract": "BOSLA_V22_ONLY_GENUINELY_NEW_MALAY_REVISED_QA_INPUT_V1",
            "candidatePackageSha256": candidate_sha,
            "sourcePdfSha256": source_sha,
            "activityId": aid,
            "activityCanonicalSha256": item["activityCanonicalSha256"],
            "originalActivityIndex": item["originalIndex"],
            "roles": ["physics", "semantics"],
            "sourcePdfUploadAllowed": False,
            "originalModelClaimsReusable": False,
            "providerSubmissionOccurred": False,
            "publicationAuthorized": False,
        }
        metadata = (json.dumps(packet, indent=2, ensure_ascii=False) + "\n").encode("utf8")
        raw = (json.dumps(body, indent=2, ensure_ascii=False) + "\n").encode("utf8")
        key = sha256(metadata + raw).hexdigest()
        path = root / key
        if path.is_symlink() or (path.exists() and not path.is_dir()):
            raise ValueError("V22_ROLE_INPUT_SYMLINK_OR_NOT_DIRECTORY")
        if not path.exists():
            path.mkdir()
        for filename, content in (
            ("activity.json", raw), ("review-identity.json", metadata),
        ):
            target = path / filename
            if target.is_symlink():
                raise ValueError("V22_ROLE_INPUT_CHANGED_OR_LINKED")
            if target.exists():
                if not target.is_file() or target.read_bytes() != content:
                    raise ValueError("V22_RESTART_CHANGED_ALREADY_STAGED_INPUT")
            else:
                with target.open("xb") as fd:
                    fd.write(content)
        outputs.append({
            "activityId": aid,
            "reviewInputSha256": key,
            "sourcePdfSha256": source_sha,
            "candidatePackageSha256": candidate_sha,
            "providerCallsMade": 0,
        })
    if len(outputs) != 4 or len({x["reviewInputSha256"] for x in outputs}) != 4:
        raise ValueError("V22_PRIVATE_ROLE_INPUT_ROSTER_INCOMPLETE")
    return outputs


def run_post_v21_exact_revised_history_reconciliation(
    repo: Path, private: Path, ready: dict[str, Any],
    v9: dict, v11: dict, v12: dict,
    v19: dict, v21: dict,
) -> dict[str, Any]:
    """Owner Yoga6 normal V22: 13 rechecks, 4 private fresh slices, zero calls."""
    folder, _, _, _, _ = _preflight(repo, private, ready, v9, v11, v12)
    signed19 = _signed(folder, _V19, ready)
    signed21 = _signed(folder, _V21, ready)
    result21 = _signed(folder, _RESULT21, ready)
    repair = _signed(folder, _RECEIPT, ready)
    if (signed19 != v19 or signed19.get("status") != _STATUS19
            or signed21 != v21 or signed21.get("status") != _STATUS21
            or signed21.get("resultSha256") != result21["integritySha256"]
            or signed21.get("candidateSourceLocationsActuallyReverified") != 18
            or signed21.get("changedActivitiesReverified") != 4
            or signed21.get("priorModelReviewerClaimsTransferred") != 0
            or signed21.get("independentAcademicProofSlotsStillOpen") != 90
            or signed21.get("candidateFormalAcademicPASS") != 0
            or signed21.get("newGeminiCalls") != 0
            or result21.get("revisedCandidateSha256") !=
                repair.get("newPrivateCandidateSha256")
            or result21.get("revisedPrivateSourceLocationsVerified") != 18
            or result21.get("candidateAcademicPASS") != 0
            or result21.get("candidateDeterministicFAIL") != 0
            or result21.get("originalReviewerRoleClaimsTransferred") != 0):
        raise ValueError("V22_SIGNED_REAL_V19_V21_ORIGINAL_AND_REVISED_CHAIN_REQUIRED")
    # Standing consent is a bounded permission ceiling for future fresh calls.
    # Checking this immutable contract NEVER opens a model client or submits.
    authorization = authorize_standing(execute=True, transfer=True, activities=4)
    if (authorization.get("maxPaidGeminiCalls") != 8 or
            authorization.get("standingConsent") is not True):
        raise ValueError("V22_STANDING_NEW_INPUT_OWNER_CONSENT_CHANGED")
    original_bytes = (repo / _PACKAGE).read_bytes()
    candidate_path = folder / _CANDIDATE
    if candidate_path.is_symlink() or not candidate_path.is_file():
        raise ValueError("V22_REVISED_PRIVATE_CANDIDATE_MISSING_OR_UNSAFE")
    candidate_bytes = candidate_path.read_bytes()
    original_sha, candidate_sha = (
        sha256(original_bytes).hexdigest(), sha256(candidate_bytes).hexdigest())
    if (original_sha != result21["originalPackageSha256"]
            or candidate_sha != result21["revisedCandidateSha256"]):
        raise ValueError("V22_ACTUAL_CANDIDATE_BYTES_CHANGED")
    source_sha = result21["sourceSha256"]
    identity = {
        "gitHead": ready["gitHead"],
        "proposalSha256": ready["proposalSha256"],
        "sourceV21ReceiptSha256": signed21["integritySha256"],
        "sourceV19ReceiptSha256": signed19["integritySha256"],
    }
    _v6_checkpoint(folder / _PRE22, {
        **identity,
        "status": "PRE_CALL_READONLY_HASH_MATCH_AND_PRIVATE_VERSION_STAGE",
        "replayingOriginalReviewerClaimsAllowed": False,
        "freshProviderCallsAllowedInThisStage": False,
        "outsidePdfAllowed": False,
        "publicationAuthorized": False,
    })
    course = repo / "content" / "chapter-9"
    original_state = section91_evidence(course, repo, private)
    verified = verified_section91_standing_passes(course, repo, private)
    plan = plan_exact_revised_history(
        original=json.loads(original_bytes.decode("utf8")),
        candidate=json.loads(candidate_bytes.decode("utf8")),
        existing_pairs=verified, original_state=original_state,
        signed_repair=repair, source_sha=source_sha,
    )
    if original_state["parentSha256"] != original_sha:
        raise ValueError("V22_HISTORICAL_PARENT_SHA_MISMATCH")
    stages = _stage_changed_private(
        folder=folder, candidate=json.loads(candidate_bytes.decode("utf8")),
        candidate_sha=candidate_sha, source_sha=source_sha,
        fresh=plan["changedRoleInputs"],
    )
    if (sha256(candidate_path.read_bytes()).hexdigest() != candidate_sha
            or sha256((repo / _PACKAGE).read_bytes()).hexdigest() != original_sha):
        raise ValueError("V22_SOURCE_VERSION_CHANGED_DURING_STAGE")
    result = _v6_checkpoint(folder / _RESULT22, {
        **identity,
        "status": "REAL_EXACT_UNCHANGED_ROLE_CLAIMS_RECONCILED_AND_CHANGED_INPUTS_STAGED",
        "sourceSha256": source_sha,
        "originalPackageSha256": original_sha,
        "revisedCandidateSha256": candidate_sha,
        "existingVerifiedOriginalReviewerPairs": 17,
        "advisoryHistoricallyVerifiedIdenticalRolePairs": 13,
        "changedActivityOldPairsNotTransferred": 4,
        "originalIndex0UncertainQuarantined": True,
        "newPrivateVersionedReviewInputsStaged": stages,
        "newReviewPairsRequired": 4,
        "alreadyReviewerSupportedIsNotScientificProof": True,
        "independentFullAcademicProofSlotsOpen": 90,
        "academicPASS": 0,
        "providerCalls": 0, "outsidePdfDownloads": 0,
        "publicationAuthorized": False,
    })
    return _v6_checkpoint(folder / _V22, {
        **identity,
        "status": _STATUS22,
        "resultSha256": result["integritySha256"],
        "original17ReviewerClaimsRechecked": True,
        "unchangedReviewerPairsReusedAsAdvisoryEvidence": 13,
        "revisedReviewerPairsThatRequireFreshAssessment": 4,
        "oldUncertainRoleReplayed": False,
        "fourPrivateReviewInputsStaged": True,
        "remainingIndependentAcademicProofSlots": 90,
        "formalAcademicPASS": 0,
        "newGeminiCalls": 0,
        "publicationAuthorized": False,
        "nextEligibleMilestone": "AUTHORIZED_FRESH_REVISED_FOUR_ACTIVITY_SOURCE_SEMANTIC_ASSESSMENT",
    })

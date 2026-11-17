"""Verified single-activity provider restoration lane for BOSLA V3.

A missing historical model answer NEVER becomes reconciled. This read-only
claim selector permits *only* a separately owner-authorized, previously
unsubmitted frozen activity to be considered for one bounded live trial after
the current provider metadata check succeeds. The ordinary global capacity
gate is unchanged. Never assume models.get proves generation permission.
"""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path

from app_generator.runtime.v3_historical_role_rollforward import (
    stage_known_unrecoverable_section96,
)
from app_generator.runtime.v3_frozen_original_tail import plan_frozen_original_tail
from app_generator.runtime.v3_frozen_tail_forward import (
    existing_frozen_original_tail_preflight,
)
from app_generator.validation.v3_course_readiness import course_readiness
from app_generator.validation.v3_server_error_recovery import provider_capacity_gate

_PARENT = "1620d15e1d645c81301997f0e42d0efbad0a7b2d123eb6b11cba9ec8c04b027f"
_ACTIVITY = "mcq-mod-bat-cut-mass-comparison"


def plan_authorized_independent_recovery_trial(
    course: Path, repo: Path, private: Path,
) -> dict:
    """Return a non-authorizing source-bound provider decision (zero network).

    Do not call this as authorization by itself: the normal paid worker must
    independently enforce the exact original-activity charter, host, owner
    execute/transfer flags, fresh metadata health and per-activity PRE_CALL.
    """
    original = course_readiness(course, repo, private_root=private)
    normal = provider_capacity_gate(private, original["sectionProgress"])
    blocked = {
        "status": "STOP_NEW_INDEPENDENT_PROVIDER_TRIAL",
        "originalProviderStatus": normal["status"],
        "originalProviderCapacity": normal,
        "publicationAuthorized": False,
        "paidCalls": 0,
        "historicalRoleReconciled": False,
    }
    if normal["status"] == "READY":
        return {**blocked, "status": "READY_ORDINARY_PROVIDER"}
    if normal["status"] != "STOP_UNCLASSIFIED_PROVIDER_REVIEW":
        return blocked
    try:
        recovery = stage_known_unrecoverable_section96(course, repo, private)
    except ValueError as exc:
        # The immutable candidate's old-claim SHA no longer agrees with
        # current bytes. A prior valid signed-by-hash candidate is never
        # overwritten or used as a recovery ticket after such a conflict.
        if str(exc) == "V3_REPAIR_EXISTING_IDENTITY_CONFLICT":
            return {**blocked,"status":"STOP_HISTORICAL_ROLE_EVIDENCE_CONFLICT"}
        raise
    if recovery.get("status") != (
            "NEW_VERSIONED_SECTION96_REPAIR_STAGED_QA_NOT_AUTHORIZED"):
        return blocked
    if recovery.get("parentPackageSha256") != _PARENT:
        return blocked
    receipt_path = (private / "historical-role-rollforward" /
                    "section-9-6" / recovery["candidatePackageSha256"] /
                    "review-required.json")
    claim_path = (private / ("v3-generated-" + _PARENT) / "batches" /
                  f"v3-review-{_PARENT[:12]}-005-0.json")
    if (receipt_path.is_symlink() or claim_path.is_symlink()
            or not receipt_path.is_file() or not claim_path.is_file()
            or receipt_path.stat().st_size > 100_000
            or claim_path.stat().st_size > 100_000):
        return blocked
    receipt = json.loads(receipt_path.read_text(encoding="utf8"))
    role_bytes = claim_path.read_bytes()
    role = json.loads(role_bytes.decode("utf8"))
    identity = sha256(role_bytes).hexdigest()
    if (receipt.get("historicalRoleClaimSha256") != identity
            or receipt.get("parentPackageSha256") != _PARENT
            or receipt.get("candidatePackageSha256") !=
               recovery["candidatePackageSha256"]
            or receipt.get("oldRequestReplayed") is not False
            or role.get("packageSha256") != _PARENT
            or role.get("activityId") != _ACTIVITY
            or role.get("roleIndex") != 0
            or role.get("state") != "AMBIGUOUS"
            or role.get("reasonCode") != "ValueError"
            or role.get("providerId") != "gemini_api"):
        return blocked
    tail = plan_frozen_original_tail(
        course, repo, private, section="section-9-6")
    if (tail.get("status") !=
            "READY_FOR_AUTHORIZED_FROZEN_ORIGINAL_TAIL_REVIEW"
            or tail.get("originalUncertaintyPreserved") is not True
            or tail.get("originalAssessedUnchanged") != 6
            or tail.get("originalModelConsensusPassesUnchanged") != 5
            or tail.get("sourcePackageSha256") != _PARENT
            or tail.get("next") is None
            or tail["next"]["index"] <= 5):
        return blocked
    if existing_frozen_original_tail_preflight(
            course, repo, private) != "READY":
        return blocked
    after = provider_capacity_gate(
        private, original["sectionProgress"],
        quarantined_historical_claim=(_PARENT, identity))
    if after["status"] != "READY_RESTRICTED_HISTORICAL_QUARANTINE":
        return {**blocked, "status": after["status"],
                "historicCapacityAfterQuarantine": after}
    # A reviewed, source-verified *new* original activity constitutes later
    # local transport evidence; before it exists, one trial only. Scientific
    # results remain separately interpreted by the existing QA engine.
    accepted = tail["supplemental"]["passed"]
    return {
        **blocked,
        "status": (
            "READY_AFTER_INDEPENDENT_GEMINI_REVIEW"
            if accepted else
            "READY_ONE_NEW_AUTHORIZED_ACTIVITY_PROBATION"),
        "nextNewOriginalIndex": tail["next"]["index"],
        "previousIndependentGeminiPasses": accepted,
        "historicalUnknownClaimSha256": identity,
        "sourcePackageSha256": _PARENT,
        "currentCapacityAfterQuarantine": after,
        "allowedActivitiesBeforeNewEvidence": 4 if accepted else 1,
    }

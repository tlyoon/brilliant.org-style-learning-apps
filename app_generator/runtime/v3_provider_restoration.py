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
import os
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

# BSA-196: exactly two immutable, previously submitted and unresolved
# ClientError role checkpoint bytes, recorded under the old Standard-key
# epoch. Their HTTP statuses were NOT saved and MUST NEVER be guessed.
_MIGRATED_SLICE = "2eb44d0bf0dc715ac806ad353aacced57d7265c0245457a0d14c9429a6878954"
_OLD_CLIENTERROR_ROLES = (
    (_MIGRATED_SLICE, "f168835612fe40e97241cdadd00ea61b088fc025dc45ce9c84a79abae39e4b92", 0),
    (_MIGRATED_SLICE, "4fedd6ad8191e6eae4c0ca3e9a211707c02aa738ea3ccbf8a45c10a40815a196", 1),
)


def known_bsa196_source_claims_present(private: Path) -> bool:
    """Before ANY SDK/config loading, restrict migration to the exact live
    historical two-role BSA-196 checkpoint. Never match unrelated unknowns.
    """
    for digest, expected_sha, role_index in _OLD_CLIENTERROR_ROLES:
        file=(private/("v3-generated-"+digest)/"batches"/
              f"v3-review-{digest[:12]}-000-{role_index}.json")
        if (file.is_symlink() or not file.is_file()
                or file.stat().st_size>100_000
                or sha256(file.read_bytes()).hexdigest()!=expected_sha):
            return False
    return True


def _verified_migrated_auth_keys(
    private: Path, capability: dict | None, next_index: int,
) -> tuple[tuple[str, str, int], ...]:
    """Exact-BSA-196 one-time migration witness; not general provider access."""
    if not isinstance(capability, dict) or next_index != 7:
        return ()
    if (capability.get("status") !=
            "MODEL_GENERATION_ACTION_DECLARED_QUOTA_UNVERIFIED"
            or capability.get("sourceFree") is not True
            or capability.get("paidModelCalls") != 0
            or capability.get("generationPermissionVerified") is not False
            or capability.get("projectQuotaVerified") is not False):
        return ()
    attempts=capability.get("attempts")
    if (not isinstance(attempts,list) or len(attempts) != 2
            or any(
                item != {
                    "candidateIndex":i,
                    "httpStatus":200,
                    "keyFormatHint":"AUTH_FORMAT_HINT",
                    "classification":"MODEL_DECLARES_GENERATE_CONTENT",
                } for i,item in enumerate(attempts))):
        return ()
    from app_generator.llm.gemini_key_failover import find_gemini_keys
    keys = find_gemini_keys()
    if len(keys) != 2 or any(not c.secret.startswith("AQ.") for c in keys):
        return ()
    local=os.environ.get("LOCALAPPDATA")
    if not local:
        return ()
    dotenv=Path(local)/"Microvid"/".env"
    if (dotenv.is_symlink() or not dotenv.is_file()
            or dotenv.stat().st_size>10_000):
        return ()
    # The auth-key configuration is confirmed to be newer than BOTH
    # unclassified submitted requests. Values never leave local process.
    newer_than = dotenv.stat().st_mtime
    for digest, expected_sha, role_index in _OLD_CLIENTERROR_ROLES:
        path=(private/("v3-generated-"+digest)/"batches"/
              f"v3-review-{digest[:12]}-000-{role_index}.json")
        if (path.is_symlink() or not path.is_file()
                or path.stat().st_size>100_000
                or newer_than <= path.stat().st_mtime):
            return ()
        raw=path.read_bytes()
        if sha256(raw).hexdigest()!=expected_sha:
            return ()
        role=json.loads(raw.decode("utf8"))
        if (role.get("packageSha256")!=digest
                or role.get("activityId")!="mcq-chal-nonuniform-density-rod"
                or role.get("roleIndex")!=role_index
                or role.get("state")!="AMBIGUOUS"
                or role.get("reasonCode")!="ClientError"
                or role.get("providerId")!="gemini_api"
                or role.get("providerHttpStatus") is not None
                or role.get("providerFailureClass") is not None
                or role.get("responseSha256") is not None):
            return ()
    return _OLD_CLIENTERROR_ROLES


def plan_authorized_independent_recovery_trial(
    course: Path, repo: Path, private: Path, *,
    auth_migration_capability: dict | None = None,
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
    migrated = _verified_migrated_auth_keys(
        private, auth_migration_capability, tail["next"]["index"])
    if migrated and (tail["supplemental"] != {
            "passed":0,"uncertain":1,"failed":0,"reserved":0,"eligible":11}
            or tail["next"]["slicePackageSha256"] !=
                "816e451c5f3027bd76969ed4c16551d2ab2951aee765aba69a0e94803484d867"):
        migrated=()
    if existing_frozen_original_tail_preflight(
            course, repo, private,
            migrated_clienterrors=migrated) != "READY":
        return blocked
    additional=tuple(row["slicePackageSha256"]
                     for row in tail["rows"]) if migrated else ()
    after = provider_capacity_gate(
        private, original["sectionProgress"],
        additional_package_shas=additional,
        quarantined_historical_claim=(_PARENT, identity),
        quarantined_migrated_clienterrors=migrated)
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
        "quarantinedMigratedClientErrorClaims": list(migrated),
        "migrationProbationOnly": bool(migrated),
    }

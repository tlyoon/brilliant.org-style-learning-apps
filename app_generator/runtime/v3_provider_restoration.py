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
# BSA-200: ACTUAL new two-Gemini index7 consensus PASS, with both
# immutable role requests COMPLETE and raw response hashes. These
# are transport recovery evidence for future NEW work only.
_RESTORED_SLICE7 = "816e451c5f3027bd76969ed4c16551d2ab2951aee765aba69a0e94803484d867"
_RESTORED_ROLE_SHAS = (
    "3eda096510368adc863345402f76f36528dff34dc23920afda2cf0aa44d98483",
    "ce1166a6f242b194f34a7903aed728a706f15f2b464011897e07311d2e75f4ac",
)


def _verified_separate_scientific_fail_repair(
    private: Path, tail: dict, *,
    expected_role_shas: tuple[str, str] | None = None,
    expected_aggregate_sha: str | None = None,
) -> bool:
    """BSA-203: repaired REAL scientific FAIL is not provider downtime.

    A scientific FAIL never becomes PASS: the original reviewer state must
    remain failed and the separate, source-bound NEW candidate must exist
    intact. A third unknown provider error remains controlled elsewhere.
    """
    failures = [row for row in tail.get("rows",[])
                if row.get("state") == "SUPPLEMENTAL_SCIENTIFIC_REPAIR_REQUIRED"]
    count = tail.get("supplemental",{}).get("failed")
    if count == 0 and not failures:
        return True
    if (count != 1 or len(failures)!=1 or failures[0].get("index")!=9):
        return False
    from app_generator.runtime.v3_section96_scientific_failure_repair import (
        _OLD_SLICE, _ROLE_SHAS, _AGGREGATE_SHA, _CHANGED,
    )
    # The normal executor ALWAYS uses the two ACTUAL pinned private SHA
    # witnesses. Optional parameters are only for isolated synthetic
    # fault-injection regression fixtures.
    role_shas=_ROLE_SHAS if expected_role_shas is None else expected_role_shas
    aggregate_sha=(_AGGREGATE_SHA if expected_aggregate_sha is None
                   else expected_aggregate_sha)
    if (not isinstance(role_shas,tuple) or len(role_shas)!=2
            or any(not isinstance(x,str) or len(x)!=64
                   or set(x)-set("0123456789abcdef")
                   for x in (*role_shas,aggregate_sha))):
        return False
    if failures[0].get("slicePackageSha256") != _OLD_SLICE:
        return False
    repair_sha="65e35a3727090119031411422a2728e1fefb2cb0c0ae71dd3307937eec2871dd"
    review_sha="45d6ba0cf52b952bbc9267bb94893d3642aa2b1fa3322fd49a0e4b4dd9b169d6"
    previous_sha="bf9c5553f435b53a8822e1a907811d61d0fcc286d22e85e3473ce38d59ffb49d"
    folder=private/"scientific-failure-rollforward"/"section-9-6"/repair_sha
    sub=private/"scientific-failure-review-inputs"/"section-9-6"/review_sha
    source=folder/"package.json"
    receipt=folder/"review-required.json"
    single=sub/"package.json"
    single_receipt=sub/"review-required.json"
    originals=private/("v3-generated-"+_OLD_SLICE)/"batches"
    checks=[source,receipt,single,single_receipt,
            originals/("v3-assessment-"+_OLD_SLICE+".json")]
    checks.extend(originals/f"v3-review-{_OLD_SLICE[:12]}-000-{i}.json"
                  for i in (0,1))
    if (any(p.is_symlink() or not p.is_file()
            or p.stat().st_size>8_000_000 for p in checks)
            or any(p.is_symlink() for p in (folder,sub,originals))):
        return False
    if (sha256(source.read_bytes()).hexdigest()!=repair_sha
            or sha256(single.read_bytes()).hexdigest()!=review_sha
            or sha256(checks[4].read_bytes()).hexdigest()!=aggregate_sha):
        return False
    old_shas=tuple(sha256(p.read_bytes()).hexdigest() for p in checks[5:])
    if old_shas!=role_shas:
        return False
    try:
        expected=json.loads(receipt.read_text(encoding="utf8"))
        sliced=json.loads(single_receipt.read_text(encoding="utf8"))
        aggregate=json.loads(checks[4].read_text(encoding="utf8"))
    except (OSError,UnicodeError,ValueError):
        return False
    # BSA-175/201: the receipt must match the atomic SHA-bound writer
    # exactly; whitespace edits are not valid new immutable provenance.
    if (receipt.read_bytes() != (
            json.dumps(expected,ensure_ascii=True,sort_keys=True,
                       indent=2)+"\n").encode("utf8")
            or single_receipt.read_bytes() != (
                json.dumps(sliced,ensure_ascii=True,sort_keys=True,
                           indent=2)+"\n").encode("utf8")):
        return False
    return bool(
        expected.get("contract") ==
            "BOSLA_V3_SCIENTIFIC_FAILURE_ROLLFORWARD_V1"
        and expected.get("parentPackageSha256")==previous_sha
        and expected.get("originalPackageSha256")==_PARENT
        and expected.get("candidatePackageSha256")==repair_sha
        and expected.get("failedOriginalReviewSliceSha256")==_OLD_SLICE
        and expected.get("failedReviewAggregateSha256")==aggregate_sha
        and expected.get("failedReviewerRoleSha256s")==list(role_shas)
        and expected.get("activityIndex")==9
        and expected.get("activityId")=="int-easy-line-of-action-motion"
        and sorted(expected.get("changedFieldPaths",[]))==sorted(_CHANGED)
        and expected.get("newModelConsensusPassClaimed") is False
        and expected.get("publicationAuthorized") is False
        and expected.get("versionedScopeAdmitted") is False
        and sliced.get("candidatePackageSha256")==review_sha
        and sliced.get("parentPackageSha256")==repair_sha
        and sliced.get("newModelConsensusPassClaimed") is False
        and sliced.get("publicationAuthorized") is False
        and isinstance(aggregate.get("reviews"),list)
        and len(aggregate["reviews"])==1
        and isinstance(aggregate["reviews"][0],dict)
        and aggregate["reviews"][0].get("status")==
            "AI_REPAIR_REQUIRED"
    )


def _verified_restored_index7(
    private: Path, tail: dict, *,
    expected_role_shas: tuple[str, str] = _RESTORED_ROLE_SHAS,
) -> bool:
    """Post-migration *real* two-role original index7 PASS is durable.

    No synthetic outcome, no client metadata or single role may authorize
    follow-on work. Tail status is independently computed using the actual
    source-bound assessor, preserving all old uncertainty and release STOP.
    """
    if (tail.get("sourcePackageSha256") != _PARENT
            or not isinstance(tail.get("next"),dict)
            or type(tail["next"].get("index")) is not int
            or not 8 <= tail["next"]["index"] <= 17
            or not isinstance(tail.get("supplemental"),dict)
            or tail["supplemental"].get("passed",0)<1
            or tail["supplemental"].get("uncertain")!=1
            or not _verified_separate_scientific_fail_repair(private,tail)
            or tail["supplemental"].get("reserved")!=0
            or not any(
                row.get("index")==7
                and row.get("slicePackageSha256")==_RESTORED_SLICE7
                and row.get("state")=="GENUINE_SUPPLEMENTAL_CONSENSUS_PASS"
                for row in tail.get("rows",[]))):
        return False
    folder=private/("v3-generated-"+_RESTORED_SLICE7)/"batches"
    if folder.is_symlink() or not folder.is_dir():
        return False
    for role_index, expected in enumerate(expected_role_shas):
        file=folder/f"v3-review-{_RESTORED_SLICE7[:12]}-000-{role_index}.json"
        if (file.is_symlink() or not file.is_file()
                or file.stat().st_size>100_000):
            return False
        raw=file.read_bytes()
        if sha256(raw).hexdigest()!=expected:
            return False
        role=json.loads(raw.decode("utf8"))
        if (role.get("state")!="COMPLETE"
                or role.get("providerId")!="gemini_api"
                or role.get("roleIndex")!=role_index
                or role.get("activityId")!="mcq-chal-hollow-geometry-cm"
                or role.get("packageSha256")!=_RESTORED_SLICE7
                or not isinstance(role.get("responseSha256"),str)
                or len(role["responseSha256"])!=64):
            return False
    return True


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
    """Exact-BSA-196 migration witness, never a general provider bypass."""
    if (not isinstance(capability, dict)
            or type(next_index) is not int
            or not 7 <= next_index <= 17):
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
    if migrated:
        if tail["next"]["index"] == 7:
            if (tail["supplemental"] != {
                    "passed":0,"uncertain":1,"failed":0,"reserved":0,"eligible":11}
                    or tail["next"]["slicePackageSha256"] !=
                        _RESTORED_SLICE7):
                migrated=()
        elif not _verified_restored_index7(private,tail):
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

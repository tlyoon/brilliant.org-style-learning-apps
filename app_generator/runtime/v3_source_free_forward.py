"""BOSLA V3 safe forward development when paid Gemini review is unavailable.

Uses existing registered source-free repair, immutable proposal and exact frozen
original-tail slice staging. Never constructs a model SDK or writes PRE_CALL,
never changes original source/review claims, and never admits/releases a course.
"""
from __future__ import annotations

from hashlib import sha256
import json
import os
from pathlib import Path
import tempfile

from app_generator.runtime.v3_course_review import plan_v3_course_review
from app_generator.runtime.v3_forward_progress import snapshot
from app_generator.runtime.v3_recovery_policy import apply_registered_recovery
from app_generator.runtime.v3_versioned_acceptance_scope import (
    prepare_versioned_course_proposal,
)
from app_generator.runtime.v3_frozen_original_tail import (
    plan_frozen_original_tail, stage_frozen_original_tail_slice,
)
from app_generator.runtime.v3_yoga6_recovery import coordinator_lock
from app_generator.validation.v3_server_error_recovery import provider_capacity_gate

_RECEIPT = "v3-source-free-forward-checkpoint.json"
_SCHEMA = "BOSLA_V3_SOURCE_FREE_BLOCKED_PROVIDER_FORWARD_V1"


def _encode(value: dict) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode("utf8")


def read_source_free_checkpoint(private: Path) -> dict | None:
    path = private / _RECEIPT
    if path.is_symlink():
        raise ValueError("V3_SOURCE_FREE_UNSAFE_RECEIPT")
    if not path.exists():
        return None
    if not path.is_file() or path.stat().st_size > 4096:
        raise ValueError("V3_SOURCE_FREE_INVALID_RECEIPT")
    try:
        value = json.loads(path.read_text(encoding="utf8"))
    except (OSError, UnicodeError, ValueError):
        raise ValueError("V3_SOURCE_FREE_UNREADABLE_RECEIPT") from None
    keys = {"schema", "rosterSha256", "originalAssessed", "originalPasses",
            "repairStatus", "proposalSha256", "stagedTailCount",
            "providerCapacity", "publicationAuthorized", "integritySha256"}
    if (not isinstance(value, dict) or set(value) != keys
            or value.get("schema") != _SCHEMA
            or value.get("publicationAuthorized") is not False
            or type(value.get("originalAssessed")) is not int
            or type(value.get("originalPasses")) is not int
            or type(value.get("stagedTailCount")) is not int
            or not 0 <= value["stagedTailCount"] <= 18
            or value.get("proposalSha256") is not None and (
                not isinstance(value["proposalSha256"], str)
                or len(value["proposalSha256"]) != 64
                or set(value["proposalSha256"]) - set("0123456789abcdef"))
            or value.get("integritySha256") != sha256(_encode({
                k: v for k, v in value.items() if k != "integritySha256"
            })).hexdigest()):
        raise ValueError("V3_SOURCE_FREE_TAMPERED_RECEIPT")
    return value


def _save_source_free_checkpoint(private: Path, payload: dict) -> dict:
    receipt = {**payload, "integritySha256": sha256(_encode(payload)).hexdigest()}
    previous = read_source_free_checkpoint(private)
    if (previous is not None
            and previous["rosterSha256"] != receipt["rosterSha256"]):
        raise ValueError("V3_SOURCE_FREE_FROZEN_ROSTER_CHANGED")
    if previous == receipt:
        return receipt
    data = _encode(receipt)
    if len(data) > 4096:
        raise ValueError("V3_SOURCE_FREE_RECEIPT_TOO_LARGE")
    private.mkdir(parents=True, exist_ok=True)
    path = private / _RECEIPT
    fd, tmp = tempfile.mkstemp(prefix=".v3-source-free-", suffix=".tmp", dir=private)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(tmp, path)
    finally:
        Path(tmp).unlink(missing_ok=True)
    return receipt


def advance_source_free_until_boundary(
    course: Path, repo: Path, private: Path,
    *, repair=apply_registered_recovery,
    proposal_builder=prepare_versioned_course_proposal,
) -> dict:
    """Run the registered safe forward stages, even if provider circuit STOP.

    The OS owner lock, immutable source identities, finite 12-item original
    tail and existing atomic repair/proposal handlers make restart idempotent.
    This function does not have a provider callback or an authorization to
    perform paid calls; it must never infer model success from staging.
    """
    if not callable(repair) or not callable(proposal_builder):
        raise ValueError("V3_SOURCE_FREE_MISSING_VERIFIED_HANDLER")
    with coordinator_lock(private):
        plan = plan_v3_course_review(
            course, repo, private_root=private, continue_independent=True)
        before = snapshot(plan)
        read_source_free_checkpoint(private)  # Reject tampering before work.
        outcome = repair(course, private, plan)
        if (not isinstance(outcome, dict)
                or outcome.get("publicationAuthorized") is not False
                or outcome.get("repairStaged") not in (True, False)
                or not isinstance(outcome.get("repairStatus"), str)):
            raise ValueError("V3_SOURCE_FREE_UNVERIFIED_REMEDY")
        proposal_hash = None
        if outcome["repairStaged"]:
            if outcome["repairStatus"] != (
                    "PRIVATE_REPAIR_STAGED_PENDING_TWO_GEMINI_REVIEWS"):
                raise ValueError("V3_SOURCE_FREE_UNVERIFIED_REPAIR")
            candidate = proposal_builder(course, repo, private)
            if (candidate.get("status") !=
                    "VERSIONED_COURSE_PROPOSAL_STAGED_NOT_ADMITTED"
                    or candidate.get("versionedScopeAdmitted") is not False
                    or candidate.get("publicationAuthorized") is not False
                    or not isinstance(candidate.get("proposalSha256"), str)
                    or len(candidate["proposalSha256"]) != 64):
                raise ValueError("V3_SOURCE_FREE_UNVERIFIED_PROPOSAL")
            proposal_hash = candidate["proposalSha256"]
        staged = 0
        if "section-9-6" in plan.get("quarantinedSections", ()):
            tail = plan_frozen_original_tail(
                course, repo, private, section="section-9-6")
            if tail.get("originalUncertaintyPreserved") is not True:
                raise ValueError("V3_SOURCE_FREE_TAIL_NOT_FROZEN")
            for item in tail["rows"]:
                if item["state"] != "UNREVIEWED_ELIGIBLE":
                    continue
                raw, meta = stage_frozen_original_tail_slice(
                    course, repo, private, section="section-9-6",
                    index=item["index"])
                if (meta["slicePackageSha256"] != item["slicePackageSha256"]
                        or meta["sourcePackageSha256"] !=
                        tail["sourcePackageSha256"]):
                    raise ValueError("V3_SOURCE_FREE_TAIL_STAGE_MISMATCH")
                staged += 1
        after_plan = plan_v3_course_review(
            course, repo, private_root=private, continue_independent=True)
        if snapshot(after_plan) != before:
            raise ValueError("V3_SOURCE_FREE_CHANGED_ORIGINAL_ASSESSMENT")
        capacity = provider_capacity_gate(private, plan["sectionProgress"])
        if not isinstance(capacity, dict) or not isinstance(capacity.get("status"), str):
            raise ValueError("V3_SOURCE_FREE_INVALID_PROVIDER_STATE")
        payload = {
            "schema": _SCHEMA, "rosterSha256": before["rosterSha256"],
            "originalAssessed": before["activitiesAssessedRows"],
            "originalPasses": before["modelConsensusPassActivities"],
            "repairStatus": outcome["repairStatus"],
            "proposalSha256": proposal_hash, "stagedTailCount": staged,
            "providerCapacity": capacity["status"], "publicationAuthorized": False,
        }
        receipt = _save_source_free_checkpoint(private, payload)
        return {
            "status": ("SOURCE_FREE_BOUNDARIES_STAGED_PROVIDER_STILL_BLOCKED"
                       if capacity["status"] != "READY"
                       else "SOURCE_FREE_BOUNDARIES_STAGED"),
            "repairStatus": outcome["repairStatus"],
            "stagedImmutableOriginalTailSlices": staged,
            "proposalSha256": proposal_hash,
            "originalAssessedUnchanged": receipt["originalAssessed"],
            "originalConsensusPassesUnchanged": receipt["originalPasses"],
            "providerCapacity": capacity["status"],
            "checkpointIntegritySha256": receipt["integritySha256"],
            "paidGeminiCalls": 0, "publicationAuthorized": False,
            "versionedScopeAdmitted": False,
        }

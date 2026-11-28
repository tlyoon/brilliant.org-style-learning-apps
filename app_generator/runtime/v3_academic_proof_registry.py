"""BSA274: generic, strictly admitted source-bound academic proof registry.

A registered rule is executable reviewed Python with an independent *signed*
proof readback, not a JSON label, AI judgment or source-cue substring. The
default handlers wrap two previously real-admitted A1/A2 proof families.
Additional future families are registered without changes to the dispatcher,
but require their own independently verified receipt and negative controls.

All 27 MCQ false-choice task IDs are recovered from the SAME immutable
selected-textbook candidate and ALL nine genuine signed V36 partitions.
Unregistered entries remain REVIEW_REQUIRED; neither an untrusted callback nor
a source-free task row may be promoted to academic PASS.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
import re
from typing import Any, Callable

from app_generator.runtime.v3_first_academic_proof_admission import _bound_inputs
from app_generator.runtime.v3_long_horizon_development import read_long_horizon_development
from app_generator.runtime.v3_revised_source_proof_rebinding import _signed
from app_generator.runtime.v3_post_v35_semantic_task_dispatch import _PREFIX
from app_generator.runtime.v3_academic_cross_head_continuity import (
    verify_academic_across_git_heads,
)
from app_generator.runtime.v3_second_academic_proof_admission import (
    verify_second_academic_across_git_heads,
)
from app_generator.validation.section91_formal_physics import _SOURCE_SHA, _CANDIDATE_SHA
from app_generator.validation.full_semantic_proof_queue import (
    plan_full_semantic_proofs,
)

_CONTRACT = "BOSLA_SOURCE_BOUND_ACADEMIC_PROOF_REGISTRY_V1"
_RESULT = "BSA274_INDEPENDENT_PROOF_REGISTRY_VERIFIED_NOT_FULL_ACADEMIC_PASS"
_KIND = "MCQ_DISTRACTOR_SCIENCE"
_SHA64 = re.compile(r"[0-9a-f]{64}\Z")
_CODE = re.compile(r"[A-Z][A-Z0-9_]{3,79}\Z")
_MAX_RULES = 27
_EXPECTED_MCQS = 9
_EXPECTED_DISTRACTORS = 27
_EXPECTED_TASKS = 429
_EXPECTED_GATES = 90

# A trusted code rule must reread the academic admission receipt, actual
# original-textbook proposition and math, both historic and current V36.
# Verifier returns a normalized immutable claim; never simply "PASS".
Verifier = Callable[[Path], dict[str, Any]]


@dataclass(frozen=True)
class AcademicProofRule:
    rule_id: str
    task_id: str
    science_family: str
    task_kind: str
    verify_signed_academic_proof: Verifier


class AcademicProofRegistry:
    """Explicit closed-code plugin interface, not dynamic code loading."""

    def __init__(self) -> None:
        self._rules: dict[str, AcademicProofRule] = {}
        self._ids: set[str] = set()

    def register(self, rule: AcademicProofRule) -> None:
        if (not isinstance(rule, AcademicProofRule)
            or not _CODE.fullmatch(rule.rule_id)
            or not _CODE.fullmatch(rule.science_family)
            or rule.task_kind != _KIND
            or not isinstance(rule.task_id, str)
            or not _SHA64.fullmatch(rule.task_id)
            or not callable(rule.verify_signed_academic_proof)
            or rule.rule_id in self._rules or rule.task_id in self._ids
            or len(self._rules) >= _MAX_RULES):
            raise ValueError("BSA274_UNTRUSTED_OR_DUPLICATE_ACADEMIC_PROOF_RULE")
        self._rules[rule.rule_id] = rule
        self._ids.add(rule.task_id)

    def rules(self) -> tuple[AcademicProofRule, ...]:
        return tuple(self._rules[k] for k in sorted(self._rules))


def _verify_a1(private: Path) -> dict[str, Any]:
    verified = verify_academic_across_git_heads(private=private)
    if (verified.get("independentlyAcceptedAcademicTasks") != 1
        or verified.get("completeAcademicProofGatesStillOpen") != 90
        or verified.get("publicationAuthorized") is not False
        or verified.get("newProviderCalls") != 0):
        raise ValueError("BSA274_A1_PRIOR_PROOF_NOT_INDEPENDENTLY_ACCEPTED")
    return {
        "taskId": verified["taskId"],
        "proofReceiptSha256": verified["proofReceiptSha256"],
        "originGitHead": verified["academicProofOriginGitHead"],
        "sourceSha256": verified["sourceSha256"],
        "candidateSha256": verified["candidateSha256"],
        "verifiedAcademicAcceptances": 1,
        "providerCalls": 0,
        "publicationAuthorized": False,
    }


def _verify_a2(private: Path) -> dict[str, Any]:
    verified = verify_second_academic_across_git_heads(private=private)
    if (verified.get("independentlyAcceptedAcademicTasks") != 2
        or verified.get("completeAcademicProofGatesStillOpen") != 90
        or len(verified.get("acceptedAcademicTaskIds", [])) != 2
        or len(set(verified["acceptedAcademicTaskIds"])) != 2
        or len(verified.get("academicProofReceiptSha256s", [])) != 2
        or verified.get("newProviderCalls") != 0
        or verified.get("publicationAuthorized") is not False):
        raise ValueError("BSA274_A2_PRIOR_PROOF_NOT_INDEPENDENTLY_ACCEPTED")
    return {
        "taskId": verified["acceptedAcademicTaskIds"][1],
        "proofReceiptSha256": verified["academicProofReceiptSha256s"][1],
        "originGitHead": verified["academicProofOriginGitHead"],
        "sourceSha256": _SOURCE_SHA,
        "candidateSha256": _CANDIDATE_SHA,
        "verifiedAcademicAcceptances": 1,
        "providerCalls": 0,
        "publicationAuthorized": False,
    }


def legacy_approved_rules() -> AcademicProofRegistry:
    """Verified legacy admissions; never silently synthesize new PASS."""
    from app_generator.runtime.v3_first_academic_proof_admission import _ID as first
    from app_generator.validation.section91_second_distractor_proof import (
        _ACTIVITY as _SECOND_ACTIVITY,
        _OPTION as _SECOND_OPTION,
    )
    from app_generator.validation.full_semantic_proof_queue import _digest
    # A2 identity is an already frozen, independently admitted SHA. The
    # trusted V36 queue below re-derives it before any acceptance is reported.
    second = "8d0ca6feb05d1376db2898613d1cd17d4da61512da429f8d3d8922b3c2cb49df"
    if (_SECOND_ACTIVITY != "act-mcq-01-vector-nature"
        or _SECOND_OPTION != "opt-b"):
        raise ValueError("BSA274_A2_LEGACY_PROOF_IDENTITY_CHANGED")
    rules = AcademicProofRegistry()
    rules.register(AcademicProofRule(
        "A1_NONZERO_P_AT_CONSTANT_SPEED", first,
        "NONZERO_VECTOR_FROM_NONZERO_VELOCITY", _KIND, _verify_a1))
    rules.register(AcademicProofRule(
        "A2_DIRECTION_MATTERS_FOR_VECTOR_P", second,
        "MOMENTUM_VECTOR_VS_EQUAL_MAGNITUDE", _KIND, _verify_a2))
    return rules


def _original_v36_mcq_tasks(
    *, private: Path, ready: dict[str, Any],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    folder, v36, first_partition, pdf, candidate = _bound_inputs(private, ready)
    if (v36.get("semanticTasksAutomaticallyDispatched") != _EXPECTED_TASKS
        or v36.get("activitySignedPartitionCount") != 18
        or v36.get("fullAcademicProofTasksAccepted") != 0
        or v36.get("completeAcademicProofGatesStillOpen") != _EXPECTED_GATES
        or v36.get("publicationAuthorized") is not False):
        raise ValueError("BSA274_SIGNED_V36_FULL_BACKLOG_REQUIRED")
    # _bound_inputs independently authenticates the original PDF and
    # candidate. Original content is never serialized into this report.
    raw = json.loads(candidate.read_text(encoding="utf8"))
    queue = plan_full_semantic_proofs(package=raw, source_sha256=_SOURCE_SHA)
    if (queue["taskCount"] != _EXPECTED_TASKS
        or queue["taskCounts"][_KIND] != _EXPECTED_DISTRACTORS
        or len(raw["activities"]) != 18
        or queue["publicationAuthorized"] is not False):
        raise ValueError("BSA274_EXACT_FULL_SEMANTIC_TASK_ROSTER_REQUIRED")
    selected = [t for t in queue["tasks"] if t["kind"] == _KIND]
    index = {x["taskId"]: x for x in selected}
    if len(index) != _EXPECTED_DISTRACTORS:
        raise ValueError("BSA274_MC_Q_TASK_ID_COLLISION")
    # Check *all* nine signed original MCQ activity partitions against each
    # SHA-derived task, not just the first already admitted activity. V36
    # rows have no surfacePath (the task ID already binds it).
    signed_index = v36.get("signedPartitionHashes", [])
    if len(signed_index) != 18:
        raise ValueError("BSA274_EXPECTED_18_SIGNED_PARTITIONS")
    signed_mcqs = {}
    found = {}
    for idx, activity in enumerate(raw["activities"]):
        if activity.get("type") != "mcq":
            continue
        ai = signed_index[idx]
        partition = (first_partition if idx == 0
                     else _signed(folder, f"{_PREFIX}{idx+1:02}.json", ready))
        if (ai.get("activityId") != activity["id"]
            or ai.get("signedEvidenceSha256") != partition.get("integritySha256")
            or partition.get("activity",{}).get("activityId") != activity["id"]
            or partition.get("candidateSha256") != _CANDIDATE_SHA
            or partition.get("sourceSha256") != _SOURCE_SHA
            or partition.get("publicationAuthorized") is not False
            or partition.get("academicPASS") != 0):
            raise ValueError("BSA274_SIGNED_MC_Q_PARTITION_NOT_AUTHENTIC")
        rows = [r for r in partition["activity"]["evidenceRows"]
                if r.get("kind") == _KIND]
        if len(rows) != 3:
            raise ValueError("BSA274_EXPECTED_THREE_FALSE_OPTIONS_PER_MC_Q")
        for row in rows:
            t = index.get(row.get("taskId"))
            if (t is None or t["activityId"] != activity["id"]
                or row.get("surfaceSha256") != t["surfaceSha256"]
                or row.get("status") != "BOUNDED_SUPPORT_ONLY_REVIEW_REQUIRED"
                or row["taskId"] in found):
                raise ValueError("BSA274_UNSIGNED_OR_FORGED_MC_Q_TASK_ROW")
            found[row["taskId"]] = row
        signed_mcqs[activity["id"]] = ai["signedEvidenceSha256"]
    if (len(signed_mcqs) != _EXPECTED_MCQS
        or set(found) != set(index)):
        raise ValueError("BSA274_INCOMPLETE_GENUINE_27_DISTRACTOR_BACKLOG")
    return {
        "sourceSha256": _SOURCE_SHA,
        "candidateSha256": _CANDIDATE_SHA,
        "signedV36Sha256": v36["integritySha256"],
        "signedMcqPartitionHashes": signed_mcqs,
        "signedMcqPartitionCount": _EXPECTED_MCQS,
        "fullSemanticTaskCount": queue["taskCount"],
    }, selected


def audit_source_bound_academic_registry(
    *, private: Path, rules: AcademicProofRegistry | None = None,
) -> dict[str, Any]:
    """Independently enumerate every signed task and reverify every admission.

    One corrupt/missing previously-accepted proof fails the *whole audit*;
    unregistered tasks remain pending, not implicitly approved. Non-mutating.
    """
    registry = legacy_approved_rules() if rules is None else rules
    if not isinstance(registry, AcademicProofRegistry):
        raise ValueError("BSA274_INVALID_PROOF_REGISTRY_OBJECT")
    state = read_long_horizon_development(private)
    ready = {"gitHead":state["gitHead"],
             "proposalSha256":state["proposalSha256"]}
    if (state.get("sourceSha256") != _SOURCE_SHA
        or state.get("candidateSha256") != _CANDIDATE_SHA
        or state.get("academicAcceptedProofTaskCount") != 0
        or state.get("completeAcademicProofGatesStillOpen") != 90):
        raise ValueError("BSA274_SOURCE_FREE_BASELINE_CANNOT_ADMIT_ACADEMIC_TASKS")
    ledger, tasks = _original_v36_mcq_tasks(private=private, ready=ready)
    by_id = {t["taskId"]: t for t in tasks}
    approved = []
    for rule in registry.rules():
        task = by_id.get(rule.task_id)
        if not task or rule.task_kind != task["kind"]:
            raise ValueError("BSA274_REGISTERED_PROOF_NOT_IN_SIGNED_TASK_BACKLOG")
        verified = rule.verify_signed_academic_proof(private)
        if (not isinstance(verified, dict)
            or verified.get("taskId") != rule.task_id
            or verified.get("sourceSha256") != _SOURCE_SHA
            or verified.get("candidateSha256") != _CANDIDATE_SHA
            or verified.get("verifiedAcademicAcceptances") != 1
            or verified.get("providerCalls") != 0
            or verified.get("publicationAuthorized") is not False
            or not _SHA64.fullmatch(str(verified.get("proofReceiptSha256")))
            or not re.fullmatch(r"[0-9a-f]{40}",str(verified.get("originGitHead")))):
            raise ValueError("BSA274_RULE_WITHOUT_INDEPENDENT_SIGNED_ACCEPTANCE")
        approved.append({
            "ruleId": rule.rule_id,
            "scienceFamily": rule.science_family,
            "taskKind": rule.task_kind,
            "taskId": rule.task_id,
            "activityId": task["activityId"],
            "surfaceSha256": task["surfaceSha256"],
            "proofReceiptSha256": verified["proofReceiptSha256"],
            "originGitHead": verified["originGitHead"],
            "status": "INDEPENDENTLY_REVERIFIED_ACADEMIC_TASK",
        })
    accepted = {e["taskId"] for e in approved}
    pending = [
        {"taskId":t["taskId"],"activityId":t["activityId"],
         "surfaceSha256":t["surfaceSha256"],"status":"REVIEW_REQUIRED"}
        for t in tasks if t["taskId"] not in accepted
    ]
    if (len(accepted) != len(approved)
        or len(approved)+len(pending) != _EXPECTED_DISTRACTORS
        or any(t["taskId"] in accepted for t in pending)):
        raise ValueError("BSA274_DUPLICATE_OR_DROPPED_ACADEMIC_TASK")
    return {
        "contract": _CONTRACT,
        "status": _RESULT,
        "gitHead": ready["gitHead"],
        "proposalSha256": ready["proposalSha256"],
        **ledger,
        "registeredIndependentRuleCount": len(registry.rules()),
        "acceptedMcqDistractorTaskCount": len(approved),
        "pendingMcqDistractorTaskCount": len(pending),
        "acceptedAcademicTaskIds": [x["taskId"] for x in approved],
        "acceptedEvidence": approved,
        "pendingMcqTasks": pending,
        "fullAcademicTasksStillOpen": _EXPECTED_TASKS-len(approved),
        "completeAcademicProofGatesStillOpen": _EXPECTED_GATES,
        "fullAcademicActivityPASS": 0,
        "newProviderCalls": 0,
        "newOutsidePdfDownloads": 0,
        "sourcePdfUploaded": False,
        "publicationAuthorized": False,
        "autoMergeAuthorized": False,
    }

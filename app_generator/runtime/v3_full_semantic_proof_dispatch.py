"""BSA253: automatic V26 full semantics proof-queue dispatch after signed V25.

This is a demand for exact-version independent checks, not academic PASS.
No new external PDF, model call, public release or old ambiguous-role replay.
"""
from __future__ import annotations

from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

from app_generator.runtime.v3_five_stage_completion import _hash
from app_generator.runtime.v3_native_release_adapter import _v6_checkpoint
from app_generator.runtime.v3_public_bundle_handoff import _trusted_json
from app_generator.runtime.v3_public_nonmerging_draft_pr import _preflight
from app_generator.runtime.v3_revised_source_proof_rebinding import _signed
from app_generator.runtime.v3_section91_formal_academic_dispatch import _V25, _STATUS25
from app_generator.runtime.v3_selected_textbook_scientific_provenance import _SOURCE_BINDING
from app_generator.runtime.v3_exact_revised_review_reconciliation import _CANDIDATE
from app_generator.validation.section91_formal_physics import _SOURCE_SHA, _CANDIDATE_SHA
from app_generator.validation.full_semantic_proof_queue import plan_full_semantic_proofs

_V26_PRE = "V26_FULL_SEMANTIC_PROOF_PRE_CALL.json"
_V26_RESULT = "V26_EXACT_VERSION_SEMANTIC_PROOF_TASK_ROSTER.json"
_V26 = "V26_SOURCE_BOUND_FULL_SEMANTIC_PROOF_DISPATCH.json"
_STATUS26 = "V26_FULL_EXPLANATION_DISTRACTOR_DIAGRAM_TRILINGUAL_TASKS_QUEUED"


def _small_signed_plan(queue: dict[str, Any]) -> dict[str, Any]:
    """Persist reproducible digests instead of unsafe >12K full task receipts."""
    tasks = queue["tasks"]
    rows = []
    for aid in queue["activityIds"]:
        selected = [t for t in tasks if t["activityId"] == aid]
        if not selected:
            raise ValueError("BSA253_ACTIVITY_PROOF_TASKS_MISSING")
        rows.append({
            "activityId": aid,
            "activitySha256": selected[0]["activitySha256"],
            "requiredIndependentTasks": len(selected),
            "proofTaskRosterSha256": _hash(selected),
            "taskCounts": dict(sorted(Counter(t["kind"] for t in selected).items())),
            "formalAcademicPASS": False,
        })
    if sum(x["requiredIndependentTasks"] for x in rows) != len(tasks):
        raise ValueError("BSA253_INCOMPLETE_SEMANTIC_TASK_PLAN")
    return {
        "sourceSha256": queue["sourceSha256"],
        "packageSha256": queue["packageSha256"],
        "activityCount": queue["activityCount"],
        "totalIndependentProofTasks": len(tasks),
        "taskKindCounts": queue["taskCounts"],
        "exactRecomputableTaskRosterSha256": _hash(tasks),
        "activityTaskRoster": rows,
        "academicProofsIndependentVerified": 0,
        "academicQA": "REVIEW_REQUIRED",
        "publicationAuthorized": False,
    }


def run_post_v25_full_semantic_queue(
    repo: Path, private: Path, ready: dict[str, Any],
    v9: dict, v11: dict, v12: dict, v25: dict,
) -> dict[str, Any]:
    folder, _, _, _, _ = _preflight(repo, private, ready, v9, v11, v12)
    exact = _signed(folder, _V25, ready)
    if (v25 != exact or exact.get("status") != _STATUS25
            or exact.get("formalModelledActivities") != 18
            or exact.get("academicProofGatesStillOpen") != 90
            or exact.get("formalAcademicPASS") != 0
            or exact.get("newGeminiCalls") != 0
            or exact.get("publicationAuthorized") is not False):
        raise ValueError("BSA253_SIGNED_V25_BEFORE_NEXT_DISPATCH_REQUIRED")
    binding = _trusted_json(private / _SOURCE_BINDING)
    pdf = Path(binding["sourcePdf"])
    source_root = Path(binding["sourceRoot"])
    if (binding.get("integritySha256") != _hash({
            k: v for k, v in binding.items() if k != "integritySha256"})
            or binding.get("contract") != "BOSLA_SELECTED_SERWAY_TEXTBOOK_LOCAL_BINDING_V1"
            or binding.get("section") != "9.1"
            or binding.get("sourceSha256") != _SOURCE_SHA
            or binding.get("externalFallbackAllowed") is not False
            or pdf.is_symlink() or not pdf.is_file()
            or pdf.resolve() != (source_root / "9" / "9.1" / "source.pdf").resolve()
            or sha256(pdf.read_bytes()).hexdigest() != _SOURCE_SHA):
        raise ValueError("BSA253_EXACT_SINGLE_ORIGINAL_TEXTBOOK_REQUIRED")
    candidate = folder / _CANDIDATE
    if (candidate.is_symlink() or not candidate.is_file()
            or sha256(candidate.read_bytes()).hexdigest() != _CANDIDATE_SHA):
        raise ValueError("BSA253_REVISED_PRIVATE_ACTIVITY_VERSION_CHANGED")
    queue = plan_full_semantic_proofs(
        package=json.loads(candidate.read_text(encoding="utf8")),
        source_sha256=_SOURCE_SHA)
    if queue["activityCount"] != 18:
        raise ValueError("BSA253_ALL_EIGHTEEN_SOURCE_ACTIVITIES_REQUIRED")
    identity = {"gitHead": ready["gitHead"],
                "proposalSha256": ready["proposalSha256"],
                "sourceV25ReceiptSha256": v25["integritySha256"]}
    _v6_checkpoint(folder / _V26_PRE, {
        **identity, "status": "PRE_CALL_NO_MODEL_OR_OUTSIDE_PDF",
        "sourcePdfSha256": _SOURCE_SHA,
        "exactCandidateSha256": _CANDIDATE_SHA,
        "paidCallsPermitted": False, "publicationAuthorized": False,
    })
    result = _v6_checkpoint(folder / _V26_RESULT, {
        **identity, **_small_signed_plan(queue),
        "status": "FULL_SEMANTIC_PROOFS_QUEUED_NOT_ACCEPTED",
        "historicAmbiguousGeminiRoleReplayed": False,
        "oldAcademicClaimsPromoted": False,
    })
    if (folder / _V26_RESULT).stat().st_size >= 12000:
        raise ValueError("BSA253_HISTORICAL_SIGNED_RECEIPT_SIZE_LIMIT")
    return _v6_checkpoint(folder / _V26, {
        **identity, "status": _STATUS26,
        "resultSha256": result["integritySha256"],
        "completeAcademicGateSlotsStillOpen": 90,
        "additionalSemanticMicroproofsPending": queue["taskCount"],
        "independentSemanticTaskRosterSha256": _hash(queue["tasks"]),
        "activityCount": 18, "independentSemanticPASS": 0,
        "newProviderCalls": 0, "externalPdfAcquisition": False,
        "publicationAuthorized": False,
        "nextEligibleMilestone": "EXECUTE_INDEPENDENT_SOURCE_BOUND_SEMANTIC_PROOF_PRODUCERS",
    })

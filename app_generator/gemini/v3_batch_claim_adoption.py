"""Read-only authenticated Gemini Batch result -> real V3 immutable role claims.

This is NOT a Batch submission or independent proof of external authorization.
Only a previously journaled, uniquely identified, completed provider job may
be reconciled. Every raw provider response must pass the existing V3 exact
activity/rubric checker before any private claim is written. Never derives
model PASS from job success, output order, a local JSON file or a model label.
"""
from __future__ import annotations

from hashlib import sha256
import json
import os
from pathlib import Path
from typing import Any

from app_generator.gemini.v3_batch_recovery import BatchJournal, validate_manifest
from app_generator.gemini.v3_keyed_batch import reconcile_keyed_sdk_job
from app_generator.runtime.run_context import RunContext
from app_generator.validation.autonomous_ai_review import ReviewerSession
from app_generator.validation.autonomous_completion import (
    _build_review_report, _parse_response, _review_consensus,
    assess_with_models, assessment_progress, make_prompt, package_identity,
)

_PERSPECTIVES = (("physics", "physics-adversary"),
                 ("semantics", "language-and-learner-adversary"))
_REVIEWERS = ("v3-gemini-api-physics", "v3-gemini-api-semantics")
_SUCCESS = "BATCH_VERIFIED_V3_REVIEW_CLAIMS_IMPORTED_NOT_RELEASE"
_REPO = Path(__file__).resolve().parents[2]


class _OfflineOnlyConversation:
    def ask(self, prompt: str, *, stage: str) -> str:
        raise RuntimeError("V3_BATCH_ADOPTION_NETWORK_CALL_FORBIDDEN")


def _extract_v3_text(result: dict[str, Any], activity_id: str) -> tuple[str, dict]:
    """Use documented Gemini GenerateContent response shape, no position guess.

    Candidate[0] is permissible only when it is the EXACT ONE candidate; role
    identity comes from echoed JSONL key, never provider candidate order.
    """
    if not isinstance(result, dict) or set(result) != {"response"}:
        raise ValueError("V3_BATCH_ROW_NOT_SUCCESSFUL_GENERATION")
    response = result["response"]
    if not isinstance(response, dict):
        raise ValueError("V3_BATCH_INVALID_GENERATE_CONTENT")
    choices = response.get("candidates")
    if not isinstance(choices, list) or len(choices) != 1:
        raise ValueError("V3_BATCH_EXPECTED_EXACT_ONE_CANDIDATE")
    only = choices[0]
    if (not isinstance(only, dict)
            or only.get("finishReason") != "STOP"
            or not isinstance(only.get("content"), dict)):
        raise ValueError("V3_BATCH_UNFINISHED_OR_BLOCKED_CANDIDATE")
    parts = only["content"].get("parts")
    if (not isinstance(parts, list) or len(parts) != 1
            or not isinstance(parts[0], dict)
            or set(parts[0]) != {"text"} or not isinstance(parts[0]["text"], str)):
        raise ValueError("V3_BATCH_NON_TEXT_OR_MULTIPART_RESULT")
    text = parts[0]["text"]
    if not text or len(text) > 50_000:
        raise ValueError("V3_BATCH_EMPTY_OR_OVERSIZE_RESPONSE")
    return text, _parse_response(text, activity_id)


def adopt_verified_keyed_batch_one_activity(
    journal: BatchJournal, manifest: dict[str, Any], sdk: Any,
    package: bytes, private_root: Path, *,
    provider_reconciliation_authorized: bool = False,
) -> dict[str, Any]:
    """Safely consume a prior externally authorized real Batch job.

    No POST/submit, no paid-generation request. Existing ambiguous synchronous
    claims cannot be overwritten; a crash between two locally imported claims
    is restart-safe because each claim is compared before any further write.
    The ordinary V3 verifier recomputes full scientific rubric consensus.
    """
    if provider_reconciliation_authorized is not True:
        raise ValueError("V3_BATCH_RECONCILIATION_NOT_AUTHORIZED")
    if (not isinstance(private_root, Path) or not private_root.is_absolute()
            or private_root.is_symlink() or
            private_root.resolve().is_relative_to(_REPO.resolve())):
        raise ValueError("V3_BATCH_UNSAFE_PRIVATE_ROOT")
    if (not isinstance(journal, BatchJournal)
            or not journal.directory.is_absolute()
            or not journal.directory.resolve().is_relative_to(private_root.resolve())
            or journal.directory.is_symlink()):
        raise ValueError("V3_BATCH_UNOWNED_PROVIDER_JOURNAL")
    validate_manifest(manifest)
    digest, activities = package_identity(package)
    if len(activities) != 1 or len(manifest["rows"]) != 2:
        raise ValueError("V3_BATCH_ADOPTION_ONE_ACTIVITY_ONLY")
    activity = activities[0]
    rowmap = {(r["activityId"], r["role"]): r for r in manifest["rows"]}
    if set(rowmap) != {(activity["id"], "physics"),
                       (activity["id"], "semantics")}:
        raise ValueError("V3_BATCH_ADOPTION_MISMATCHED_ACTIVITY_ROSTER")
    for role, perspective in _PERSPECTIVES:
        r = rowmap[(activity["id"], role)]
        if (r["packageSha256"] != digest or
                r["promptSha256"] != sha256(
                    make_prompt(activity, perspective).encode("utf8")).hexdigest()):
            raise ValueError("V3_BATCH_ADOPTION_UNVERIFIED_PROMPT_OR_PACKAGE")
    state = journal.status()
    if (state["batchSha256"] != manifest["batchSha256"]
            or state["state"] not in {"SUBMITTED", "RUNNING", "SUCCEEDED"}
            or not state.get("providerJob")):
        raise ValueError("V3_BATCH_ADOPTION_NO_AUTHENTIC_JOURNAL_JOB")
    read_only = reconcile_keyed_sdk_job(journal, manifest, sdk)
    if read_only["status"] == "WAIT_PROVIDER_BATCH":
        return {"status": "WAIT_AUTHENTIC_BATCH_COMPLETION",
                "v3ModelRowsAccepted": 0, "publicationAuthorized": False}
    if read_only["status"] != "KEYED_RESULTS_ATTRIBUTED_NOT_ACADEMIC_PASS":
        raise ValueError("V3_BATCH_ADOPTION_PROVIDER_NOT_SUCCEEDED")
    results = read_only["results"]
    if set(results) != set(rowmap):
        raise ValueError("V3_BATCH_ADOPTION_INCOMPLETE_RESULTS")
    provider_job = state["providerJob"]
    responses = []
    expected_claims = []
    for index, (role, perspective) in enumerate(_PERSPECTIVES):
        text, decision = _extract_v3_text(results[(activity["id"], role)],
                                          activity["id"])
        prompt_sha = rowmap[(activity["id"], role)]["promptSha256"]
        model_sha = sha256(text.encode("utf8")).hexdigest()
        reviewer = _REVIEWERS[index]
        session = f"{provider_job}-role-{index}"
        claim = f"v3-review-{digest[:12]}-000-{index}"
        expected_claims.append((claim, {
            "packageSha256": digest,
            "activityId": activity["id"],
            "promptSha256": prompt_sha,
            "roleIndex": index,
            "providerId": "gemini_api",
            "state": "COMPLETE",
            "reviewerId": reviewer,
            "sessionId": session,
            "responseSha256": model_sha,
            "decision": decision,
        }))
        responses.append({
            "reviewerId": reviewer,
            "sessionId": session,
            "providerId": "gemini_api",
            "promptSha256": prompt_sha,
            "responseSha256": model_sha,
            "decision": decision,
        })
    dims, verdict = _review_consensus(responses)
    expected = _build_review_report(digest, activities, [{
        "activityId": activity["id"],
        "status": verdict,
        "dimensions": dims,
        "reviewers": responses,
    }])
    # Run the existing complete validator BEFORE any private checkpoint write.
    observed = assessment_progress(package, expected)
    if observed["activitiesFullyModelReviewed"] != 1:
        raise ValueError("V3_BATCH_ADOPTION_INCOMPLETE_V3_RUBRIC")
    run_dir = private_root / ("v3-generated-" + digest)
    if run_dir.is_symlink() or (run_dir.exists() and not run_dir.is_dir()):
        raise ValueError("V3_BATCH_ADOPTION_UNSAFE_RUN_DIRECTORY")
    run_dir.mkdir(parents=True, exist_ok=True)
    lock = run_dir / ".active-review.lock"
    try:
        fd = os.open(lock, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError:
        raise ValueError("V3_BATCH_ADOPTION_ACTIVE_REVIEW_OWNERSHIP")
    try:
        os.close(fd)
        checkpoint = RunContext.create(private_root, "v3-generated-" + digest)
        prior = checkpoint.load_stage("v3-assessment-" + digest)
        if prior is not None and prior != expected:
            # Never overwrite an existing assessment from another provider,
            # earlier uncertain role, or a different unverified batch.
            raise ValueError("V3_BATCH_ADOPTION_CONFLICTING_ASSESSMENT")
        for name, expected_claim in expected_claims:
            prior_role = checkpoint.load_stage(name)
            if prior_role is not None and prior_role != expected_claim:
                raise ValueError("V3_BATCH_ADOPTION_CONFLICTING_ROLE_CLAIM")
        # All claims preflighted; on crash, completed claims are checked for
        # exact bytes on the next read-only provider reconciliation. No POST.
        for name, expected_claim in expected_claims:
            if checkpoint.load_stage(name) is None:
                checkpoint.save_stage(name, expected_claim)
        if prior is None:
            checkpoint.save_stage("v3-assessment-" + digest, expected)
        # Confirm the ordinary engine can resume from these claims without
        # any .ask() call, and recomputes consensus from raw model decisions.
        sessions = tuple(ReviewerSession(
            _REVIEWERS[i], f"{provider_job}-role-{i}",
            _OfflineOnlyConversation(), provider_id="gemini_api"
        ) for i in (0, 1))
        verified = assess_with_models(
            package, sessions, checkpoint=checkpoint,
            generated_content_transfer_allowed=True, max_activities=1)
        if verified != expected:
            raise ValueError("V3_BATCH_ADOPTION_V3_ENGINE_DISAGREEMENT")
    finally:
        lock.unlink()
    return {
        "status": _SUCCESS,
        "providerJob": provider_job,
        "reviewedActivitySha256": digest,
        "genuineVerdictRecordedFromProvider": verdict,
        "reviewerClaimsPersisted": 2,
        "wholeCourseScopeAdmitted": False,
        "publicationAuthorized": False,
    }

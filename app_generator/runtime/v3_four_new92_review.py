"""BSA209: exactly four previously untouched Section9.2 independent Gemini reviews.

This separate, owner-authorized campaign never expands the old paid charter,
replays old roles, changes frozen originals, admits a version or publishes.
Source-bound one-item slices reuse the BSA185 source-free identity model;
immutable two-role evidence uses the BSA206 assessor verifier.
"""
from __future__ import annotations

import json
import os
import shutil
import tempfile
import time
from pathlib import Path
from typing import Callable

from app_generator.runtime.v3_frozen_original_tail import (
    _slice, _safe_evidence, _bytes,
)
from app_generator.runtime.v3_paid_review_authorization import (
    load_paid_review_contract,
)
from app_generator.runtime.v3_section96_authorized_revised_qa import (
    _EXPECTED_CONTRACT as _REVISED96_CONTRACT,
    verified_new_provider_capability,
    read_prior_two_role_science,
    unsent_revised_input,
    verify_persisted_two_role_science,
)
from app_generator.validation.autonomous_completion import (
    assessment_progress, package_identity,
)
from app_generator.validation.v3_locale_script_integrity import script_findings
from app_generator.validation.v3_course_readiness import course_readiness

ROOT = Path(__file__).resolve().parents[2]
AUTHORITY = ROOT / "docs" / "v3_authorized_four_new_original92_20261118.json"
PRIOR_AUTHORITY = ROOT / "docs" / "v3_authorized_revised_section96_scientific_qa_20261118.json"
SECTION = "section-9-2"
PARENT = "cfe7bab820aa01ce71bd7a6a334c742101ebd10d8895cccd5f05d599030f971c"
PINNED = (
    (14, "act-int-iso-06", "2a625cdf0889f7e6adeba090d25e0fb03fa0b54b53eed092f9c7ef10acb98fe8"),
    (15, "act-int-iso-07", "a1b7eaeecb91ac9f0892daa039823a511a332e4c0bedd4118676e5a8ba2ecbf3"),
    (16, "act-int-iso-08", "f86df040c2da54587000a0a706e38e73f0bce96bc6713ebf1a73699e0aa14033"),
    (17, "act-int-iso-09", "fb0b2f5b1a246ea494047765dd2530dd9db650491de6162a5203100c0dae2aa5"),
)
EXPECTED = {
    "schemaVersion": 1,
    "contractId": "BOSLA_V3_OWNER_AUTHORIZED_FOUR_NEW_UNREVIEWED_SECTION92_20261118",
    "authorizedBy": "OWNER_EXPLICIT_CHAT_AUTHORIZATION_2026-11-18_MAX8_CALLS",
    "scope": "FOUR_NEVER_REVIEWED_FROZEN_SECTION92_ORIGINAL_ONE_ACTIVITY_INPUTS",
    "authorizedHost": "Yoga 6", "provider": "gemini_api",
    "historicalCharter": "docs/acceptance_closure_chapter9.json",
    "historicalCharterRemainsFrozen": True,
    "previousPaidCharter": "docs/v3_paid_gemini_review_authorization_20261117.json",
    "previousPaidCharterRemainsFrozen": True,
    "revised96Charter": "docs/v3_authorized_revised_section96_scientific_qa_20261118.json",
    "revised96CharterRemainsFrozen": True,
    "originalSection": SECTION, "originalPackageSha256": PARENT,
    "reviewInputs": [
        {"index": index, "activityId": activity, "reviewSliceSha256": sha}
        for index, activity, sha in PINNED
    ],
    "maxActivitiesPerInvocation": 4,
    "maxIndependentGeminiCallsPerActivity": 2,
    "maxTotalGeminiCalls": 8, "maxElapsedSecondsPerInvocation": 900,
    "paidGeminiApiGenerationAuthorized": True,
    "generatedLearningTextTransferAuthorized": True,
    "noReplayOfAnySubmittedOriginalOrIsolatedRole": True,
    "useImmutableRoleClaims": True,
    "allowSourcePDFUpload": False, "allowBatchJobCreation": False,
    "allowAutomatedScheduler": False, "allowUnboundedRecurrence": False,
    "versionedCourseAdmissionAuthorized": False,
    "publicationAuthorized": False, "releaseApprovalRequiredSeparately": True,
}


def authorize_four_new(*, execute: bool, transfer: bool,
                       activities: int, seconds: int = 900,
                       file: Path = AUTHORITY) -> dict:
    """Separate owner consent; old scopes and previously spent calls immutable."""
    if not execute or not transfer:
        raise ValueError("V3_NEW4_BOTH_FLAGS_REQUIRED")
    if (type(activities) is not int or not 1 <= activities <= 4
            or type(seconds) is not int or not 30 <= seconds <= 900):
        raise ValueError("V3_NEW4_BUDGET_EXCEEDED")
    if file.is_symlink() or not file.is_file() or file.stat().st_size > 9000:
        raise ValueError("V3_NEW4_MISSING_AUTHORITY")
    try:
        grant = json.loads(file.read_text(encoding="utf8"))
    except (OSError, UnicodeError, ValueError):
        raise ValueError("V3_NEW4_UNREADABLE_AUTHORITY") from None
    if grant != EXPECTED:
        raise ValueError("V3_NEW4_OWNER_SCOPE_CHANGED")
    old = load_paid_review_contract()
    if (old.get("publicationAuthorized") is not False
            or old.get("maxActivitiesPerInvocation") != 4
            or old.get("allowedSectionsForOriginalReviews") !=
               ["section-9-3", "section-9-4", "section-9-5", "section-9-6"]):
        raise ValueError("V3_NEW4_PRIOR_PAID_CHARTER_CHANGED")
    if (PRIOR_AUTHORITY.is_symlink()
            or json.loads(PRIOR_AUTHORITY.read_text(encoding="utf8")) !=
               _REVISED96_CONTRACT):
        raise ValueError("V3_NEW4_REVISED96_CHARTER_CHANGED")
    return {"activityLimit": activities, "maximumGeminiCalls": 2 * activities,
            "publicationAuthorized": False}


def exact_four_unreviewed(course: Path, repo: Path, private: Path) -> list[dict]:
    """Read-only individual eligibility: old failure quarantined, others untouched."""
    if (not private.is_absolute() or private.is_symlink()
            or private.resolve().is_relative_to(repo.resolve())):
        raise ValueError("V3_NEW4_UNSAFE_PRIVATE_ROOT")
    progress = course_readiness(course, repo, private_root=private)
    row = next((x for x in progress["sectionProgress"]
                if x["section"] == SECTION), None)
    source_file = course / SECTION / "package.json"
    if source_file.is_symlink() or not source_file.is_file():
        raise ValueError("V3_NEW4_UNSAFE_FROZEN_SOURCE")
    raw_parent = source_file.read_bytes()
    sha, items = package_identity(raw_parent)
    if (progress.get("scopeSource") != "FROZEN_CANDIDATE_MANIFEST"
            or progress.get("sectionsTotal") != 6
            or progress.get("publicationAuthorized") is not False
            or sha != PARENT or not isinstance(row, dict)
            or row.get("packageSha256") != PARENT
            or row.get("activitiesTotal") != 18
            or len(items) != 18 or row.get("activitiesAssessedRows") != 14
            or row.get("modelConsensusPassActivities") != 13
            or row.get("modelRepairRequiredActivities") != 1
            or row.get("modelUncertainActivities") != 0
            or row.get("unreconciledRoleClaims") != 0):
        raise ValueError("V3_NEW4_FROZEN_ORIGINAL_INVENTORY_CHANGED")
    saved_file = (private / ("v3-generated-" + sha) / "batches" /
                  ("v3-assessment-" + sha + ".json"))
    if (saved_file.is_symlink() or not saved_file.is_file()
            or saved_file.stat().st_size > 8_000_000):
        raise ValueError("V3_NEW4_MISSING_FROZEN_ASSESSMENT")
    saved = json.loads(saved_file.read_text(encoding="utf8"))
    summary = assessment_progress(raw_parent, saved)
    if (summary.get("activitiesAssessed") != 14
            or summary.get("modelConsensusPassActivities") != 13
            or summary.get("modelRepairRequiredActivities") != 1
            or len(saved.get("reviews", [])) != 14
            or saved["reviews"][-1].get("status") != "AI_REPAIR_REQUIRED"):
        raise ValueError("V3_NEW4_OLD_SCIENTIFIC_FAILURE_CHANGED")
    findings = script_findings(json.loads(raw_parent))
    if any(f.get("activityId") != items[13]["id"] for f in findings):
        raise ValueError("V3_NEW4_OTHER_LOCALE_SCRIPT_DEFECT")
    rows = []
    for index, activity_id, expected_sha in PINNED:
        item = items[index]
        if item.get("id") != activity_id or script_findings({"activities": [item]}):
            raise ValueError("V3_NEW4_CHANGED_ACTIVITY_OR_LOCALE")
        raw, slice_sha, receipt = _slice(PARENT, SECTION, index, item)
        if slice_sha != expected_sha:
            raise ValueError("V3_NEW4_SOURCE_SHA_CHANGED")
        status = _safe_evidence(private, PARENT, index, slice_sha)
        if status not in ("UNREVIEWED_ELIGIBLE", "AGGREGATE_EXISTS"):
            raise ValueError("V3_NEW4_OLD_OR_UNRECONCILED_ROLE_NO_REPLAY")
        rows.append({"index": index, "activityId": activity_id,
                     "sha": slice_sha, "raw": raw, "manifest": receipt,
                     "originalReviewState": status})
    if source_file.read_bytes() != raw_parent:
        raise ValueError("V3_NEW4_SOURCE_CHANGED_DURING_READ")
    return rows


def stage_exact_one(private: Path, entry: dict) -> None:
    """BSA185 atomic private staging; content never sent from a PDF."""
    folder = private / "four-new-original92-slices"
    dest = folder / entry["sha"]
    raw = entry["raw"]
    receipt = _bytes(entry["manifest"])
    if folder.is_symlink() or dest.is_symlink():
        raise ValueError("V3_NEW4_UNSAFE_STAGE")
    if dest.exists():
        if (not dest.is_dir()
                or any(p.is_symlink() for p in
                       (dest / "package.json", dest / "review-slice.json"))
                or (dest / "package.json").read_bytes() != raw
                or (dest / "review-slice.json").read_bytes() != receipt):
            raise ValueError("V3_NEW4_STAGED_SOURCE_IDENTITY_CHANGED")
        return
    folder.mkdir(parents=True, exist_ok=True)
    tmp = Path(tempfile.mkdtemp(prefix=".new4-", dir=folder))
    try:
        for name, data in (("package.json", raw), ("review-slice.json", receipt)):
            with (tmp / name).open("xb") as fh:
                fh.write(data)
                fh.flush()
                os.fsync(fh.fileno())
        tmp.rename(dest)
    finally:
        if tmp.exists():
            shutil.rmtree(tmp)


def advance_four_new(course: Path, repo: Path, private: Path, *,
                     execute: bool, transfer: bool, max_activities: int = 4,
                     max_seconds: int = 900, capability: dict | None = None,
                     review_one: Callable | None = None) -> dict:
    """Review only distinct new SHA inputs; true failures are not provider outages."""
    authorize_four_new(execute=execute, transfer=transfer,
                       activities=max_activities, seconds=max_seconds)
    if not verified_new_provider_capability(private, capability):
        raise ValueError("V3_NEW4_UNVERIFIED_AUTH_KEY_OR_PROVIDER")
    if review_one is None:
        raise ValueError("V3_NEW4_MISSING_REAL_REVIEWER")
    from app_generator.runtime.v3_yoga6_recovery import coordinator_lock
    results = []
    started = time.monotonic()
    with coordinator_lock(private):
        # Repeat the read-only preflight under the actual owner lock.
        candidates = exact_four_unreviewed(course, repo, private)
        for entry in candidates[:max_activities]:
            if time.monotonic() - started >= max_seconds:
                break
            stage_exact_one(private, entry)
            new = unsent_revised_input(private, entry["sha"])
            if new:
                callback = review_one(entry["raw"], entry["activityId"], private)
                if (not isinstance(callback, dict)
                        or callback.get("activitiesAssessed") != 1):
                    raise ValueError("V3_NEW4_UNVERIFIED_REVIEW_CALLBACK")
                saved = verify_persisted_two_role_science(
                    private, entry["raw"], entry["activityId"], entry["sha"], callback)
            else:
                saved = read_prior_two_role_science(private, entry)
            outcome = {
                "index": entry["index"], "activityId": entry["activityId"],
                "reviewSliceSha256": entry["sha"],
                "reusedPreviouslyVerifiedRoles": not new,
                "newConsensusPass": saved["pass"],
                "newScientificRepairRequired": saved["repair"],
                "newUncertain": saved["uncertain"],
            }
            results.append(outcome)
            if saved["uncertain"]:
                break
    return {
        "status": ("NEW4_AUTHORIZED_BATCH_COMPLETED"
                   if len(results) == max_activities
                      and not results[-1]["newUncertain"]
                   else "NEW4_STOPPED_AT_REVIEW_BOUNDARY"),
        "outcomes": results, "maximumGeminiCalls": 2 * max_activities,
        "allNewScientificPass": (len(results) == 4 and
                                 all(x["newConsensusPass"] for x in results)),
        "originalFrozenReviewsModified": False,
        "versionedScopeAdmitted": False, "publicationAuthorized": False,
    }

def continue_four_to_browser(reviewed: dict, run_sourcefree: Callable) -> dict:
    """BSA209 automatic next local step, no further paid Gemini operations."""
    base = {"paidGeminiCalls": 0, "publicationAuthorized": False,
            "versionedScopeAdmitted": False}
    if (not isinstance(reviewed, dict)
            or reviewed.get("status") != "NEW4_AUTHORIZED_BATCH_COMPLETED"
            or reviewed.get("allNewScientificPass") is not True
            or reviewed.get("publicationAuthorized") is not False
            or reviewed.get("versionedScopeAdmitted") is not False):
        return {**base, "status": "NEW4_STOP_SCIENCE_OR_REVIEW_INCOMPLETE"}
    outcomes = reviewed.get("outcomes")
    if (not isinstance(outcomes, list) or len(outcomes) != 4
            or any(not isinstance(row, dict)
                   or row.get("index") != index
                   or row.get("reviewSliceSha256") != sha
                   or row.get("newConsensusPass") is not True
                   or row.get("newUncertain") is not False
                   or row.get("newScientificRepairRequired") is not False
                   for row, (index, _, sha) in zip(outcomes, PINNED))):
        return {**base, "status": "NEW4_STOP_CHANGED_SCIENCE_EVIDENCE"}
    if not callable(run_sourcefree):
        return {**base, "status": "NEW4_STOP_NO_LOCAL_DISPATCH"}
    try:
        local = run_sourcefree()
    except Exception as exc:
        return {**base, "status": "NEW4_STOP_LOCAL_BROWSER_ERROR",
                "errorClass": type(exc).__name__}
    if not isinstance(local, dict):
        return {**base, "status": "NEW4_STOP_UNVERIFIED_BROWSER"}
    browser = local.get("realCandidateBrowserAcceptance", {})
    proposal = local.get("proposalSha256")
    if (local.get("section96ScienceIntegrated") is not True
            or local.get("paidGeminiCalls") != 0
            or local.get("publicationAuthorized") is not False
            or local.get("versionedScopeAdmitted") is not False
            or not isinstance(proposal, str) or len(proposal) != 64
            or not isinstance(browser, dict)
            or browser.get("status") != "ACTUAL_UNADMITTED_CHAPTER9_BROWSER_QA_PASS"
            or browser.get("proposalSha256") != proposal
            or browser.get("activitiesInCandidate") != 108
            or browser.get("all108ActivitiesVisited") is not True
            or browser.get("renderedChecks") != 698
            or browser.get("allLocaleViewportPromptChecks") != 648
            or browser.get("publicationAuthorized") is not False
            or not isinstance(browser.get("integritySha256"), str)
            or len(browser["integritySha256"]) != 64):
        return {**base, "status": "NEW4_STOP_UNVERIFIED_BROWSER"}
    return {**base, "status": "NEW4_AUTOMATICALLY_ADVANCED_108_BROWSER_PASS",
            "proposalSha256": proposal,
            "browserReceiptSha256": browser["integritySha256"],
            "reusedVerifiedBrowserReceipt":
                browser.get("reusedVerifiedBrowserReceipt") is True}

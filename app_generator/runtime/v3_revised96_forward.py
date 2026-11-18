"""BSA208: automatic safe local continuation after two genuine revised Gemini passes.

Never treat the reviewer's terminal "completed" status as two science PASSes:
it also covers complete scientific FAIL results. The normal worker supplies
the genuine source-free version+browser execution callback. No API call here.
"""
from __future__ import annotations

from collections.abc import Callable

from app_generator.runtime.v3_section96_authorized_revised_qa import (
    _EXPECTED_SLICES,
)

_EXPECTED = tuple((item[0], item[3]) for item in _EXPECTED_SLICES)
_BROWSER_PASS = "ACTUAL_UNADMITTED_CHAPTER9_BROWSER_QA_PASS"


def advance_post_revised96_science(
    reviewed: dict, run_source_free: Callable[[], dict],
) -> dict:
    """Dispatch local 108-item browser QA only after both exact scientific PASSes."""
    base = {"sourceFreeExecuted": False, "paidGeminiCalls": 0,
            "versionedScopeAdmitted": False, "publicationAuthorized": False}
    if not isinstance(reviewed, dict):
        return {**base, "status": "STOP_REVISED96_UNVERIFIED_REVIEW_REPORT"}
    if reviewed.get("status") != "REVISED96_AUTHORIZED_BATCH_COMPLETED":
        return {**base, "status": "STOP_REVISED96_REVIEW_BOUNDARY_UNRESOLVED"}
    outcomes = reviewed.get("outcomes")
    if (reviewed.get("publicationAuthorized") is not False
            or reviewed.get("versionedScopeAdmitted") is not False
            or reviewed.get("maxGeminiReviewerCalls") not in (2, 4)
            or not isinstance(outcomes, list)
            or len(outcomes) != len(_EXPECTED)
            or any(
                not isinstance(row, dict)
                or row.get("index") != expected_index
                or row.get("reviewSliceSha256") != expected_sha
                or row.get("newConsensusPass") is not True
                or row.get("newScientificRepairRequired") is not False
                or row.get("newUncertain") is not False
                for row, (expected_index, expected_sha)
                in zip(outcomes, _EXPECTED)
            )):
        return {**base, "status": "STOP_REVISED96_NOT_TWO_GENUINE_SCIENCE_PASSES"}
    if not callable(run_source_free):
        return {**base, "status": "STOP_REVISED96_SOURCEFREE_DISPATCH_MISSING"}
    try:
        forward = run_source_free()
    except Exception as exc:
        return {**base, "sourceFreeExecuted": True,
                "status": "STOP_REVISED96_SOURCEFREE_EXECUTION_FAILED",
                "errorClass": type(exc).__name__}
    if not isinstance(forward, dict):
        return {**base, "sourceFreeExecuted": True,
                "status": "STOP_REVISED96_SOURCEFREE_NOT_VERIFIED"}
    browser = forward.get("realCandidateBrowserAcceptance")
    proposal = forward.get("proposalSha256")
    if (forward.get("section96ScienceIntegrated") is not True
            or forward.get("paidGeminiCalls") != 0
            or forward.get("publicationAuthorized") is not False
            or forward.get("versionedScopeAdmitted") is not False
            or not isinstance(proposal, str) or len(proposal) != 64
            or not isinstance(browser, dict)
            or browser.get("status") != _BROWSER_PASS
            or browser.get("proposalSha256") != proposal
            or browser.get("activitiesInCandidate") != 108
            or browser.get("all108ActivitiesVisited") is not True
            or browser.get("renderedChecks") != 698
            or browser.get("allLocaleViewportPromptChecks") != 648
            or browser.get("publicationAuthorized") is not False
            or not isinstance(browser.get("integritySha256"), str)
            or len(browser["integritySha256"]) != 64):
        return {**base, "sourceFreeExecuted": True,
                "status": "STOP_REVISED96_SOURCEFREE_NOT_VERIFIED"}
    return {**base, "sourceFreeExecuted": True,
            "status": "REVISED96_AUTOMATICALLY_ADVANCED_TO_108_BROWSER_PASS",
            "proposalSha256": proposal,
            "browserReceiptSha256": browser["integritySha256"],
            "reusedVerifiedBrowserReceipt":
                browser.get("reusedVerifiedBrowserReceipt") is True}

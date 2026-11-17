"""Separate, owner-authorized V3 paid Gemini campaign; frozen V2 intact.

Executable permission is strictly narrower than course acceptance and release.
The CLI retains explicit --execute / --allow-generated-text-transfer per
invocation. No scheduler, unknown provider, ambiguous claim replay or PDF upload.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app_generator.validation.final_acceptance_closure import (
    load_frozen_charter,
)

ROOT = Path(__file__).resolve().parents[2]
CONTRACT = ROOT / "docs" / "v3_paid_gemini_review_authorization_20261117.json"
_ID = "BOSLA_V3_OWNER_AUTHORIZED_PAID_GEMINI_REVIEW_20261117"
_CORRECTED = "49a7f18c7cc2b7c00e0b6b23838cca1ed7fe52262384e0c26bbc8360fa3e9174"
_ORIGINAL = ("section-9-3", "section-9-4", "section-9-5", "section-9-6")
_KEYS = frozenset((
    "schemaVersion", "contractId", "authorizedBy", "scope",
    "historicalCharter", "historicalCharterRemainsFrozen",
    "paidGeminiApiGenerationAuthorized",
    "generatedLearningTextTransferAuthorized", "authorizedHost", "provider",
    "allowedWorkflows", "allowedSectionsForOriginalReviews",
    "correctedActivityId", "correctedCandidateSha256",
    "maxActivitiesPerInvocation", "maxElapsedSecondsPerInvocation",
    "maxIndependentGeminiCallsPerActivity",
    "noRetryOfAmbiguousProviderRequest", "protectedHistoricalSection",
    "useImmutableRoleClaims", "allowBatchJobCreation",
    "allowAutomatedScheduler", "allowUnboundedRecurrence",
    "allowSourcePDFUpload", "versionedCourseAdmissionAuthorized",
    "publicationAuthorized", "releaseApprovalRequiredSeparately",
))


def load_paid_review_contract(path: Path = CONTRACT) -> dict[str, Any]:
    """Fail closed before opening any paid model client."""
    if (path.is_symlink() or not path.is_file()
            or path.stat().st_size > 8000):
        raise ValueError("V3_PAID_CONTRACT_MISSING_OR_LINKED")
    try:
        authorization = json.loads(path.read_text(encoding="utf8"))
    except (OSError, UnicodeError, ValueError):
        raise ValueError("V3_PAID_CONTRACT_NOT_VALID_JSON") from None
    if (not isinstance(authorization, dict)
            or set(authorization) != _KEYS
            or authorization["schemaVersion"] != 1
            or authorization["contractId"] != _ID
            or authorization["authorizedBy"] !=
                "OWNER_EXPLICIT_CHAT_APPROVAL_2026-11-17"
            or authorization["scope"] !=
                "NEW_VERSIONED_CHAPTER9_GEMINI_EVIDENCE_CAMPAIGN"
            or authorization["historicalCharter"] !=
                "docs/acceptance_closure_chapter9.json"
            or authorization["authorizedHost"] != "Yoga 6"
            or authorization["provider"] != "gemini_api"
            or authorization["allowedWorkflows"] !=
                ["FROZEN_ORIGINAL_ELIGIBLE_NEW_ACTIVITY",
                 "ISOLATED_CORRECTED_SECTION_9_2_ACTIVITY"]
            or authorization["allowedSectionsForOriginalReviews"] != list(_ORIGINAL)
            or authorization["correctedActivityId"] != "act-int-iso-05"
            or authorization["correctedCandidateSha256"] != _CORRECTED
            or type(authorization["maxActivitiesPerInvocation"]) is not int
            or authorization["maxActivitiesPerInvocation"] != 4
            or type(authorization["maxElapsedSecondsPerInvocation"]) is not int
            or authorization["maxElapsedSecondsPerInvocation"] != 900
            or type(authorization["maxIndependentGeminiCallsPerActivity"]) is not int
            or authorization["maxIndependentGeminiCallsPerActivity"] != 2):
        raise ValueError("V3_PAID_CONTRACT_SCOPE_OR_BUDGET_CHANGED")
    required_true = (
        "historicalCharterRemainsFrozen", "paidGeminiApiGenerationAuthorized",
        "generatedLearningTextTransferAuthorized",
        "noRetryOfAmbiguousProviderRequest", "useImmutableRoleClaims",
        "releaseApprovalRequiredSeparately",
    )
    required_false = (
        "allowBatchJobCreation", "allowAutomatedScheduler",
        "allowUnboundedRecurrence", "allowSourcePDFUpload",
        "versionedCourseAdmissionAuthorized", "publicationAuthorized",
    )
    if (any(authorization[k] is not True for k in required_true)
            or any(authorization[k] is not False for k in required_false)
            or authorization["protectedHistoricalSection"] != "section-9-1"):
        raise ValueError("V3_PAID_CONTRACT_SAFETY_BOUNDARY_CHANGED")
    historical = load_frozen_charter()
    if (historical["policy"]["publicReleaseAuthorized"] is not False
            or historical["policy"]["frozen"] is not True
            or historical["policy"]["historicalAttemptsResetAllowed"] is not False):
        raise ValueError("V3_PAID_CONTRACT_ORIGINAL_CHARTER_CHANGED")
    return authorization


def authorize_paid_v3_action(
    workflow: str, *, execute: bool, transfer: bool,
    next_section: str | None = None,
    max_activities: int = 1,
    max_elapsed_seconds: int = 900,
    corrected_candidate_sha256: str | None = None,
) -> dict[str, Any]:
    """Single invocation permission, NOT academic approval or publication."""
    if execute is not True or transfer is not True:
        raise ValueError("V3_PAID_CONTRACT_BOTH_EXECUTE_AND_TRANSFER_REQUIRED")
    contract = load_paid_review_contract()
    if (type(max_activities) is not int or
            not 1 <= max_activities <= contract["maxActivitiesPerInvocation"]
            or type(max_elapsed_seconds) is not int
            or not 30 <= max_elapsed_seconds <=
                   contract["maxElapsedSecondsPerInvocation"]):
        raise ValueError("V3_PAID_CONTRACT_INVOCATION_BUDGET_EXCEEDED")
    if workflow == "FROZEN_ORIGINAL_ELIGIBLE_NEW_ACTIVITY":
        if (next_section not in _ORIGINAL or
                corrected_candidate_sha256 is not None):
            raise ValueError("V3_PAID_CONTRACT_ORIGINAL_SCOPE_NOT_AUTHORIZED")
    elif workflow == "ISOLATED_CORRECTED_SECTION_9_2_ACTIVITY":
        if (next_section is not None
                or corrected_candidate_sha256 != _CORRECTED
                or max_activities != 1):
            raise ValueError("V3_PAID_CONTRACT_REVISED_SCOPE_NOT_AUTHORIZED")
    else:
        raise ValueError("V3_PAID_CONTRACT_UNKNOWN_WORKFLOW")
    return {
        "contractId": contract["contractId"],
        "workflow": workflow,
        "maxActivities": max_activities,
        "maxElapsedSeconds": max_elapsed_seconds,
        "perActivityReviewerCallLimit":
            contract["maxIndependentGeminiCallsPerActivity"],
        "publicationAuthorized": False,
    }

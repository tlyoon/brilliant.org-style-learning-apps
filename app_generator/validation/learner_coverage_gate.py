"""Fail closed on empty or incomplete browser/learner QA coverage.

This is a metadata-only quality boundary: matching counters never prove that a
browser was run, pixels are sound, interactions are correct, or scientific
meaning is accurate. It never produces academic or publication approval.
"""
from __future__ import annotations

from typing import Any

LANGUAGES = ("en", "ms", "zh")
VIEWPORTS = (390, 1280)
PER_VISUAL = len(LANGUAGES) * len(VIEWPORTS)


def audit_visual_browser_scope(
    *, visual_ids: list[str], mcq_ids: set[str],
    responsive_checks: int, keyboard_checks: int,
    screenshots_captured: int, capture_requested: bool,
    issue_count: int,
) -> dict[str, Any]:
    """Validate observed counts against *non-empty* requested visual scope."""
    if (not isinstance(visual_ids, list) or
        any(not isinstance(aid, str) or not aid for aid in visual_ids) or
        len(visual_ids) != len(set(visual_ids)) or
        not isinstance(mcq_ids, set) or
        any(not isinstance(aid, str) for aid in mcq_ids) or
        any(type(value) is not int or value < 0 for value in
            (responsive_checks, keyboard_checks, screenshots_captured, issue_count)) or
        type(capture_requested) is not bool):
        raise ValueError("invalid nonsecret visual browser coverage metadata")
    expected_responsive = len(visual_ids) * PER_VISUAL
    expected_keyboard = len(set(visual_ids) & mcq_ids) * PER_VISUAL
    missing = []
    if not visual_ids:
        missing.append("NO_VISUAL_ACTIVITIES_EXERCISED")
    if responsive_checks != expected_responsive or expected_responsive == 0:
        missing.append("RESPONSIVE_LOCALE_COVERAGE_MISSING")
    # A visual-only run without MCQ keyboard coverage is not a learner
    # interaction acceptance test. An independent interactive test is needed.
    if expected_keyboard == 0 or keyboard_checks != expected_keyboard:
        missing.append("KEYBOARD_COVERAGE_MISSING")
    if capture_requested and screenshots_captured != expected_responsive:
        missing.append("VISUAL_SCREENSHOTS_MISSING")
    if not capture_requested:
        missing.append("SCREENSHOT_EVIDENCE_NOT_REQUESTED")
    if issue_count:
        missing.append("BROWSER_ISSUES_REPORTED")
    return {
        "status": "VISUAL_BROWSER_SCOPE_COMPLETE_UNREVIEWED"
                  if not missing else "INSUFFICIENT_VISUAL_BROWSER_COVERAGE",
        "expectedResponsiveChecks": expected_responsive,
        "observedResponsiveChecks": responsive_checks,
        "expectedKeyboardChecks": expected_keyboard,
        "observedKeyboardChecks": keyboard_checks,
        "expectedScreenshotCount": expected_responsive if capture_requested else 0,
        "observedScreenshotCount": screenshots_captured,
        "missing": missing,
        "visualActivities": len(visual_ids),
        "independentBrowserEvidenceVerified": False,
        "fullLearnerAcceptanceVerified": False,
        "trilingualMeaningVerified": False,
        "scientificVisualSemanticsVerified": False,
        "academicQA": "REVIEW_REQUIRED",
        "publicationAuthorized": False,
    }


def audit_full_learner_coverage(
    package: dict[str, Any], evidence: dict[str, Any],
) -> dict[str, Any]:
    """Check exact activity/locale/viewport *records*, not aggregate counters.

    Matching metadata is not a cryptographic or academic verification of
    browser activity. Every MCQ AND interactive activity must have an exact
    per-viewport per-locale observation; an empty success claim fails.
    """
    activities = package.get("activities") if isinstance(package, dict) else None
    if (not isinstance(activities, list) or not activities or
        any(not isinstance(a, dict) or
            not isinstance(a.get("id"), str) or not a["id"] or
            a.get("type") not in {"mcq", "interactive"} for a in activities)):
        raise ValueError("complete nonempty learner package roster required")
    ids = [a["id"] for a in activities]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate learner activity ID")
    if not isinstance(evidence, dict):
        raise ValueError("learner evidence must be a structured object")
    rows = evidence.get("checks")
    if not isinstance(rows, list):
        raise ValueError("per-activity learner browser observations required")
    expected = {(aid, lang, width)
                for aid in ids for lang in LANGUAGES for width in VIEWPORTS}
    seen: set[tuple[str,str,int]] = set()
    invalid = []
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("non-structured learner observation")
        key = (row.get("activityId"), row.get("locale"), row.get("viewportWidth"))
        if key not in expected or key in seen:
            raise ValueError("extra, duplicate or misaligned learner observation")
        seen.add(key)
        for field in ("rendered", "responsive", "keyboardOperable",
                      "answerInteractionExercised"):
            if row.get(field) is not True:
                invalid.append({"activityId": key[0], "locale": key[1],
                                "viewportWidth": key[2], "missing": field})
    missing = sorted(expected - seen)
    count_complete = not missing and not invalid
    return {
        "status": "COMPLETE_COVERAGE_METADATA_UNVERIFIED"
                  if count_complete else "INCOMPLETE_LEARNER_COVERAGE",
        "activityCount": len(ids),
        "expectedCheckCount": len(expected),
        "observedCheckCount": len(seen),
        "missingCheckCount": len(missing),
        "failedCheckCount": len(invalid),
        "coverageOnly": True,
        "browserObservationsIndependentlyVerified": False,
        "interactiveLearnerAcceptanceVerified": False,
        "trilingualMeaningVerified": False,
        "scientificVisualSemanticsVerified": False,
        "academicQA": "REVIEW_REQUIRED",
        "publicationAuthorized": False,
    }

"""Finite V3 course dispatcher over the *existing* authorized model engine.

Never supplies provider credentials, uploads a source PDF, retries a
denied call, or turns synthetic model data into authentic proof. An externally
approved source-free factory may open isolated browser reviewer contexts
only after independent operation authorization and immutable-scope preflight.
"""
from __future__ import annotations

from hashlib import sha256
from pathlib import Path
from typing import Any

from app_generator.runtime.v3_authorized_review import advance_v3_generated_text
from app_generator.gemini.v3_existing_login_sessions import V3ExistingLoginSessions
from app_generator.validation.v3_course_readiness import course_readiness


def plan_v3_course_review(
    chapter_dir: Path, repo_root: Path, *, private_root: Path | None = None,
    expected_sections: int = 6,
    section_numbers: tuple[int, ...] | None = None,
) -> dict:
    """Select one unfinished approved section from durable validated evidence.

    The plan is read-only; it never creates a checkpoint or contacts a model.
    Uncertain/failed prior model responses are terminal for course-level
    dispatch until independently reconciled or a versioned content repair.
    """
    progress=course_readiness(
        chapter_dir,repo_root,private_root=private_root,
        expected_sections=expected_sections,
        section_numbers=section_numbers)
    result={**progress,"nextSection":None,"dispatchStatus":None,
            "activitiesRemaining":(
                progress["activitiesTotal"]-progress["activitiesAssessedRows"])}
    if progress["scopeSource"]!="FROZEN_CANDIDATE_MANIFEST":
        result["dispatchStatus"]="BLOCKED_NO_APPROVED_COURSE_SCOPE"
    elif progress["modelRepairRequiredActivities"]>0:
        result["dispatchStatus"]="STOP_VERSIONED_CONTENT_REPAIR_REQUIRED"
    elif (progress["modelUncertainActivities"]>0
          or progress["reviewerRequestsSkippedUnsent"]>0):
        result["dispatchStatus"]="STOP_UNRECONCILED_MODEL_REVIEW"
    elif any(row["activitiesAssessedRows"]<row["activitiesTotal"]
             for row in progress["sectionProgress"]):
        row=next(row for row in progress["sectionProgress"]
                 if row["activitiesAssessedRows"]<row["activitiesTotal"])
        result["nextSection"]=row["section"]
        result["dispatchStatus"]="READY_FOR_AUTHORIZED_REVIEW_SESSIONS"
    elif progress["activitiesFullyModelReviewed"]==progress["activitiesTotal"]:
        result["dispatchStatus"]="PENDING_DETERMINISTIC_RELEASE_EVIDENCE"
    else:
        result["dispatchStatus"]="STOP_UNRECONCILED_MODEL_REVIEW"
    # Publication remains a distinct signed receipt and deterministic gate.
    result["publicationAuthorized"]=False
    return result


def advance_v3_course_review(
    chapter_dir: Path, repo_root: Path, *, private_root: Path,
    sessions: tuple | None = None,
    generated_content_transfer_allowed: bool = False,
    max_activities: int = 6,
    expected_sections: int = 6,
    session_factory: Any | None = None,
    external_operation_authorized: bool = False,
) -> dict:
    """Advance only one package/batch of an approved course per invocation.

    Use existing independently authorized sessions OR a separately approved
    source-free session factory. Factories are entered only AFTER immutable
    scope, package, explicit external-authorization and transfer preflight.
    The default without a provider is a truthful blocker with no side effects.
    This code never grants external permission, retries denied operations,
    or replays unresolved model requests.
    """
    if type(max_activities) is not int or not 1<=max_activities<=6:
        raise ValueError("V3_INVALID_BATCH_LIMIT")
    before=plan_v3_course_review(chapter_dir,repo_root,
        private_root=private_root,expected_sections=expected_sections)
    if before["dispatchStatus"]!="READY_FOR_AUTHORIZED_REVIEW_SESSIONS":
        return before
    if sessions is not None and session_factory is not None:
        raise ValueError("V3_CONFLICTING_REVIEW_TRANSPORTS")
    if sessions is None and (session_factory is None
                            or external_operation_authorized is not True):
        return {**before,"dispatchStatus":"BLOCKED_EXTERNAL_REVIEW_TRANSPORT"}
    if (isinstance(session_factory, V3ExistingLoginSessions)
        and session_factory.external_operation_authorized is not True):
        return {**before,"dispatchStatus":"BLOCKED_EXTERNAL_REVIEW_TRANSPORT"}
    if not generated_content_transfer_allowed:
        return {**before,"dispatchStatus":"BLOCKED_GENERATED_TEXT_TRANSFER"}
    section=before["nextSection"]
    # The previous read-only scope check already verifies the exact
    # immutable package SHA/count. Repeat the selected-byte identity here
    # before calling the preexisting authorized per-package engine.
    source=next(row for row in before["sectionProgress"]
                if row["section"]==section)
    package=chapter_dir/section/"package.json"
    if package.is_symlink() or not package.is_file():
        raise ValueError("V3_COURSE_SELECTED_PACKAGE_CHANGED")
    raw=package.read_bytes()
    if sha256(raw).hexdigest()!=source["packageSha256"]:
        raise ValueError("V3_COURSE_SELECTED_PACKAGE_CHANGED")
    if session_factory is None:
        advance_v3_generated_text(
            raw,sessions,private_root=private_root,
            generated_content_transfer_allowed=True,
            max_activities=max_activities)
    else:
        # Existing-login source-free providers already enforce their own
        # account/profile ownership checks and close only freshly owned tabs.
        # Never bootstrap before the verified frozen package is selected.
        with session_factory as provider:
            authorized_sessions=provider.open_pair(section)
            advance_v3_generated_text(
                raw,authorized_sessions,private_root=private_root,
                generated_content_transfer_allowed=True,
                max_activities=max_activities)
    after=plan_v3_course_review(chapter_dir,repo_root,
        private_root=private_root,expected_sections=expected_sections)
    return {**after,"selectedSection":section}

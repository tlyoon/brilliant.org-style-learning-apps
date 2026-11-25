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
from app_generator.validation.v3_response_recovery import (
    section_has_only_isolatable_uncertainty,
)


def plan_v3_course_review(
    chapter_dir: Path, repo_root: Path, *, private_root: Path | None = None,
    expected_sections: int = 6,
    section_numbers: tuple[int, ...] | None = None,
    continue_independent: bool = False,
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
    if continue_independent and progress["scopeSource"]=="FROZEN_CANDIDATE_MANIFEST":
        # BSA-20261116-173: inspect language script integrity BEFORE paid
        # Gemini dispatch, including every unreviewed frozen section. The
        # original frozen package is never changed or falsely marked PASS.
        import json
        from app_generator.validation.v3_locale_script_integrity import script_findings
        script_quarantined = {}
        for section_row in progress["sectionProgress"]:
            package = chapter_dir / section_row["section"] / "package.json"
            findings = script_findings(json.loads(package.read_text(encoding="utf-8")))
            if findings:
                script_quarantined[section_row["section"]] = len(findings)
        # BSA-20261114-165: isolate genuine provider/academic faults at the
        # section boundary. Never replay an uncertain activity or change its
        # immutable aggregate. Other frozen sections may be reviewed without
        # treating the original uncertainty as a PASS.
        # A received/hash-verified local JSON/rubric error is isolated to
        # the affected activity. It remains AI_UNCERTAIN and blocks RELEASE,
        # but later independent activities in that SAME frozen section may
        # proceed without replaying that old role or changing its verdict.
        # Historical AMBIGUOUS request, missing raw response, provider error
        # and scientific FAIL continue to quarantine their section.
        isolated_local = [
            row["section"] for row in progress["sectionProgress"]
            if (row["modelUncertainActivities"] > 0
                and row["unreconciledRoleClaims"] == 0
                and section_has_only_isolatable_uncertainty(
                    private_root, row["packageSha256"],
                    chapter_dir / row["section"] / "package.json"))
        ]
        quarantined = [
            row["section"] for row in progress["sectionProgress"]
            if (row["unreconciledRoleClaims"] > 0
                or (row["modelUncertainActivities"] > 0
                    and row["section"] not in isolated_local)
                or row["modelRepairRequiredActivities"] > 0
                or row["reviewerRequestsSkippedUnsent"] > 0
                or row["section"] in script_quarantined)
        ]
        eligible = [
            row for row in progress["sectionProgress"]
            if (row["section"] not in quarantined
                and row["activitiesAssessedRows"] < row["activitiesTotal"])
        ]
        result["quarantinedSections"] = quarantined
        result["scriptQuarantinedSections"] = script_quarantined
        result["isolatedLocalFailureSections"] = isolated_local
        result["independentContinuation"] = True
        # The per-package run lock is global to live request ownership.
        # Do not begin another section while an earlier review process may
        # still be in flight, even when that section is quarantined.
        if private_root is not None:
            for row in progress["sectionProgress"]:
                lock = (private_root /
                    ("v3-generated-" + row["packageSha256"]) /
                    ".active-review.lock")
                if lock.is_symlink():
                    raise ValueError("V3_UNSAFE_REVIEW_OWNERSHIP_LOCK")
                if lock.exists():
                    result["dispatchStatus"] = (
                        "STOP_ACTIVE_REVIEW_OWNERSHIP_UNCERTAIN")
                    result["publicationAuthorized"] = False
                    return result
        if eligible:
            # BSA-186: a different original section becoming eligible must
            # NOT route around earlier supplemental reviewer claims or an
            # uncertain PRE_CALL made by the independent original-tail queue.
            # Read-only; never opens a model or clears prior reviewer claims.
            if private_root is not None:
                from app_generator.runtime.v3_frozen_tail_forward import (
                    existing_frozen_original_tail_preflight,
                )
                tail_status = existing_frozen_original_tail_preflight(
                    chapter_dir, repo_root, private_root)
                if tail_status != "READY":
                    result["dispatchStatus"] = tail_status
                    result["publicationAuthorized"] = False
                    return result
            from app_generator.validation.v3_server_error_recovery import provider_capacity_gate
            result["nextSection"] = eligible[0]["section"]
            capacity = provider_capacity_gate(
                private_root, progress["sectionProgress"])
            result["providerCapacity"] = capacity
            result["dispatchStatus"] = (
                "READY_FOR_AUTHORIZED_REVIEW_SESSIONS" if
                capacity["status"] == "READY" else capacity["status"]
            )
        elif quarantined:
            result["dispatchStatus"] = (
                "STOP_VERSIONED_CONTENT_REPAIR_REQUIRED" if
                (progress["modelRepairRequiredActivities"] or script_quarantined) else
                "STOP_UNRECONCILED_MODEL_REVIEW"
            )
        elif progress["activitiesFullyModelReviewed"] == progress["activitiesTotal"]:
            result["dispatchStatus"] = "PENDING_DETERMINISTIC_RELEASE_EVIDENCE"
        else:
            result["dispatchStatus"] = "STOP_UNRECONCILED_MODEL_REVIEW"
        result["publicationAuthorized"] = False
        return result
    if progress["scopeSource"]!="FROZEN_CANDIDATE_MANIFEST":
        result["dispatchStatus"]="BLOCKED_NO_APPROVED_COURSE_SCOPE"
    elif progress.get("unreconciledRoleClaims",0)>0:
        # Hard interruption after an IN_FLIGHT claim but before the
        # per-activity aggregate must never open fresh model clients.
        result["dispatchStatus"]="STOP_UNRECONCILED_MODEL_REVIEW"
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
    continue_independent: bool = False,
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
        private_root=private_root,expected_sections=expected_sections,
        continue_independent=continue_independent)
    if before["dispatchStatus"]!="READY_FOR_AUTHORIZED_REVIEW_SESSIONS":
        return before
    if sessions is not None and session_factory is not None:
        raise ValueError("V3_CONFLICTING_REVIEW_TRANSPORTS")
    if (session_factory is not None and max_activities >
            getattr(session_factory, "max_activities_per_session", 6)):
        raise ValueError("V3_NATIVE_ONE_ACTIVITY_PER_BATCH_REQUIRED")
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
        # Explicit Gemini-only source-free providers already enforce their own
        # account/profile ownership checks and close only freshly owned tabs.
        # Never bootstrap before the verified frozen package is selected.
        with session_factory as provider:
            authorized_sessions=provider.open_pair(section)
            advance_v3_generated_text(
                raw,authorized_sessions,private_root=private_root,
                generated_content_transfer_allowed=True,
                max_activities=max_activities)
    after=plan_v3_course_review(chapter_dir,repo_root,
        private_root=private_root,expected_sections=expected_sections,
        continue_independent=continue_independent)
    return {**after,"selectedSection":section}

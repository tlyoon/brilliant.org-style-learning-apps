"""Yoga 6 BOSLA V3 normal recovery and finite forward-progress worker.

Default is read-only. --diagnose-only uses source-free models.get metadata,
not generation. --execute retains the historical ONE-activity mode.
--auto-advance additionally invokes a bounded in-process controller that
moves immediately to the next eligible frozen activity after each verified
result, without Windows Task Scheduler. Both paid-operation and generated-
text transfer flags are required. All existing claim and release gates stay
authoritative; it never replays an uncertain request or auto-publishes.
"""
from __future__ import annotations

import argparse
from contextlib import redirect_stdout
import io
import json
import os
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app_generator.runtime.native_workstation_guard import (
    require_authorized_native_review_host,
)
from app_generator.runtime.v3_course_review import plan_v3_course_review
from app_generator.runtime.v3_gemini_diagnostics import diagnose_model_metadata
from app_generator.runtime.v3_gemini_diagnostics import diagnose_declared_generation_support
from app_generator.runtime.v3_yoga6_recovery import (
    checked_private_root, coordinator_lock, gate_review_plan,
    persist_status, status_from_plan,
)
from scripts.run_v3_native_gemini_review import (
    AUTHORITY, _load_native_config,
)
from scripts import run_v3_native_gemini_review as native
from app_generator.runtime.v3_paid_review_authorization import (
    authorize_paid_v3_action,
)
from app_generator.runtime.v3_frozen_original_tail import (
    plan_frozen_original_tail,
)
from app_generator.runtime.v3_frozen_tail_forward import (
    advance_frozen_tail_until_boundary, supplemental_provider_preflight,
)
from app_generator.runtime.v3_source_free_forward import (
    advance_source_free_until_boundary,
)
from app_generator.runtime.v3_revised96_forward import (
    advance_post_revised96_science,
)
from app_generator.runtime.v3_provider_restoration import (
    plan_authorized_independent_recovery_trial,
    known_bsa196_source_claims_present,
)
from scripts.run_v3_yoga6_acceptance import (
    advance_real_candidate_browser_qa,
)

COURSE = ROOT / "content" / "chapter-9"


def _print(data: dict) -> None:
    print(json.dumps(data,sort_keys=True,separators=(",",":")))


def _complete_source_free_with_browser(private: Path, result: dict) -> dict:
    """Execute idempotent actual-candidate Chrome QA in the normal workflow.

    Browser QA cannot authorize paid reviews or publication. Failures are
    reported as independent acceptance blockers, not silently counted PASS.
    """
    try:
        qa=advance_real_candidate_browser_qa(ROOT,private,result)
    except Exception as exc:
        qa={"status":"STOP_NATIVE_REAL_CANDIDATE_BROWSER_QA",
            "errorClass":type(exc).__name__,
            "publicationAuthorized":False}
    science=None
    if result.get("section96ScienceIntegrated") is True:
        # BSA-207: both corrected activities have fresh two-Gemini PASS;
        # the main new 108-item roster now includes corrected idx9.
        # The main REAL 698 Chrome QA covers it; no separate old-parent
        # browser receipt can authorize this new roster.
        science={"status":"SCIENCE_INDEX9_INCLUDED_IN_FULL_CANDIDATE_BROWSER",
                 "publicationAuthorized":False}
    elif (result.get("scientificFailureRepair",{}).get("status") ==
            "NEW_SECTION96_SCIENCE_REPAIR_STAGED_REVIEW_NOT_AUTHORIZED"):
        # BSA-204: Check the separate NEW index9 version in ACTUAL Chrome.
        # A valid revision/renderer/source-bound receipt is reused at the
        # same head; never treat this as independent Gemini scientific QA.
        try:
            from app_generator.runtime.v3_science_candidate_browser import (
                advance_science_revision_browser_qa,
            )
            science=advance_science_revision_browser_qa(ROOT,COURSE,private)
        except Exception as exc:
            science={"status":"STOP_REAL_SCIENCE_REVISION_BROWSER_QA",
                     "errorClass":type(exc).__name__,
                     "publicationAuthorized":False}
    return {**result,"realCandidateBrowserAcceptance":qa,
            **({"scienceRevisionBrowserAcceptance":science}
               if science is not None else {})}


def _continue_revised96_source_free(private: Path, reviewed: dict) -> dict:
    """BSA208 normal dispatcher: bounded local work follows saved Gemini roles.

    Source-bound genuine role validation occurs in advance_revised96_reviews
    and independently in advance_source_free_until_boundary. No provider
    request or old-role replay is made by this continuation.
    """
    return advance_post_revised96_science(
        reviewed,lambda: _complete_source_free_with_browser(
            private,advance_source_free_until_boundary(COURSE,ROOT,private)))


def _advance_unchanged_frozen_tail(args, private: Path,
                                    argv: list[str] | None) -> int:
    """Normal authorized original-work fallback after an older role is uncertain.

    Never retries that role: each subsequent untouched original activity has a
    separate deterministic package SHA and immutable two-Gemini checkpoint.
    This is NOT a new versioned content replacement or release permission.
    """
    # Safe local development must not depend on success of a PAID
    # authorization preflight. Perform these verified independent stages
    # first, on the authorized Yoga6 host; never issue PRE_CALL or API I/O.
    require_authorized_native_review_host(AUTHORITY)
    offline = _complete_source_free_with_browser(
        private,advance_source_free_until_boundary(COURSE, ROOT, private))
    authorize_paid_v3_action(
        "FROZEN_ORIGINAL_ELIGIBLE_NEW_ACTIVITY",
        execute=args.execute,transfer=args.allow_generated_text_transfer,
        next_section="section-9-6",
        max_activities=args.max_forward_activities,
        max_elapsed_seconds=args.max_forward_seconds)
    # BSA-193: an old, exact-source unknown result stays unreconciled, but
    # a new separately authorized activity can enter ONE controlled trial.
    # Default provider circuit still stops unknowns, actual denials and
    # cooldowns. The restricted selector ignores at most the single
    # sha-verified known old role, never any new or other ambiguity.
    probation = plan_authorized_independent_recovery_trial(
        COURSE, ROOT, private)
    auth_capability = None
    # BSA-199: the user has migrated Standard to AQ Auth keys AFTER the
    # historical BSA-196 ClientErrors. Only an actual TWO-key, read-only
    # models.get action check may offer a one-NEW-activity probation.
    # All old checkpoint bytes and the ordinary provider STOP remain intact.
    if (probation["status"]=="STOP_NEW_INDEPENDENT_PROVIDER_TRIAL"
            and probation["originalProviderStatus"] ==
                "STOP_UNCLASSIFIED_PROVIDER_REVIEW"
            and known_bsa196_source_claims_present(private)):
        from app_generator.runtime.v3_gemini_diagnostics import (
            diagnose_declared_generation_support,
        )
        auth_capability = diagnose_declared_generation_support(
            _load_native_config())
        if (auth_capability["status"] ==
                "MODEL_GENERATION_ACTION_DECLARED_QUOTA_UNVERIFIED"):
            probation = plan_authorized_independent_recovery_trial(
                COURSE,ROOT,private,
                auth_migration_capability=auth_capability)
    migrated_claims=tuple(tuple(x) for x in probation.get(
        "quarantinedMigratedClientErrorClaims",[]))
    permitted = (
        "READY_ORDINARY_PROVIDER",
        "READY_ONE_NEW_AUTHORIZED_ACTIVITY_PROBATION",
        "READY_AFTER_INDEPENDENT_GEMINI_REVIEW",
    )
    if probation["status"] not in permitted:
        _print({"sourceFreeRecovery":offline,
                "status":(
                    "STOP_TAIL_PROVIDER_CAPACITY_STOP_UNCLASSIFIED_PROVIDER_REVIEW"
                    if probation["originalProviderStatus"] ==
                       "STOP_UNCLASSIFIED_PROVIDER_REVIEW"
                    else "STOP_TAIL_PROVIDER_"+probation["status"]),
                "providerRestoration":probation,
                "providerCapacity":probation["originalProviderCapacity"],
                "publicationAuthorized":False})
        return 3
    capacity = probation.get("currentCapacityAfterQuarantine")
    if capacity is None:
        from app_generator.validation.v3_course_readiness import course_readiness
        from app_generator.validation.v3_server_error_recovery import provider_capacity_gate
        capacity = provider_capacity_gate(private,course_readiness(
            COURSE,ROOT,private_root=private)["sectionProgress"])
    from app_generator.runtime.v3_yoga6_recovery import (
        MAX_FAILED_ACTIVITIES_PER_COURSE,
    )
    if capacity["serverErrorActivitiesHistorical"] >= (
            MAX_FAILED_ACTIVITIES_PER_COURSE):
        _print({"status":"STOP_TAIL_PROVIDER_RECOVERY_BUDGET",
                "sourceFreeRecovery":offline, "publicationAuthorized":False})
        return 3
    # BSA-186: the original course circuit is insufficient on its own.
    # Check all previously created, source-bound supplemental package claims
    # and orphan PRE_CALL records BEFORE metadata, SDK, credentials or new
    # paid transport; this remains mandatory across restarts.
    tail_plan = plan_frozen_original_tail(
        COURSE, ROOT, private, section="section-9-6")
    supplemental = supplemental_provider_preflight(
        private,tail_plan,migrated_clienterrors=migrated_claims)
    if supplemental != "READY":
        # Safely prepared before paid work was considered; do not repeat.
        _print({"status": supplemental, "sourceFreeRecovery": offline,
                "publicationAuthorized": False})
        return 3
    # Only independently READY original AND supplemental provider circuits
    # may bootstrap an SDK/client or run a metadata check.
    from app_generator.runtime.native_sdk_environment import (
        delegate_to_supported_sdk,
    )
    delegated = delegate_to_supported_sdk(
        ROOT, list(argv) if argv is not None else sys.argv[1:],
        entrypoint=Path(__file__))
    if delegated is not None:
        return delegated
    config = _load_native_config()
    if migrated_claims:
        # This one genuinely new, paid-review probation is strictly bounded:
        # at most two roles, each with 180s SDK timeout and ZERO SDK retries.
        # A timeout is AMBIGUOUS and must never trigger role replay.
        from dataclasses import replace
        config = replace(
            config,gemini_api_timeout_seconds=min(
                config.gemini_api_timeout_seconds,180))
    # Source-free metadata-only probe; must pass BEFORE any durable PRE_CALL
    # or possible paid request. The historical failure count selects only
    # a future NEW original-activity credential, never a replay.
    diagnostic = diagnose_model_metadata(
        config,preferred_offset=capacity["serverErrorActivitiesHistorical"])
    if diagnostic.get("status") != "READY_SOURCE_FREE_ONLY":
        _print({"status":"STOP_TAIL_PROVIDER_METADATA_NOT_READY",
                "diagnosticStatus":diagnostic.get("status"),
                "publicationAuthorized":False})
        return 3
    candidate = diagnostic["selectedCandidateIndex"]
    from app_generator.gemini.v3_native_api_reviewers import (
        V3NativeGeminiApiSessions,
    )
    from app_generator.runtime.v3_authorized_review import (
        advance_v3_generated_text,
    )
    def review_one(raw: bytes, manifest: dict) -> dict:
        factory = V3NativeGeminiApiSessions(
            config,operation_authorized=True,
            generated_content_transfer_allowed=True,
            candidate_offset=candidate)
        with factory as provider:
            sessions = provider.open_pair(manifest["activityId"])
            return advance_v3_generated_text(
                raw,sessions,private_root=private,
                generated_content_transfer_allowed=True,max_activities=1)
    began = time.monotonic()
    if probation["status"] == "READY_ONE_NEW_AUTHORIZED_ACTIVITY_PROBATION":
        # One genuine new role pair, then read the immutable reviewer
        # aggregate: no simulated provider-ready certificate is accepted.
        first = advance_frozen_tail_until_boundary(
            COURSE,ROOT,private,review_one,section="section-9-6",
            max_activities=1,max_elapsed_seconds=args.max_forward_seconds,
            migrated_clienterrors=migrated_claims)
        if (first["attemptedThisInvocation"] != 1
                or first["verifiedNewSupplementalRowsThisInvocation"] != 1
                or first["supplemental"]["passed"] !=
                    probation["previousIndependentGeminiPasses"] + 1):
            _print({**first, "status":"STOP_PROBATION_WITHOUT_GENUINE_NEW_PASS",
                    "providerRestoration":"NO_GENUINE_NEW_HEALTH_PROOF",
                    "publicationAuthorized":False})
            return 3
        if args.max_forward_activities == 1:
            _print({**first, "providerRestoration":
                    "PROBATION_PASSED_ONE_GENUINE_NEW_ACTIVITY"})
            return 0
        reread = plan_authorized_independent_recovery_trial(
            COURSE,ROOT,private,
            auth_migration_capability=auth_capability)
        remaining = args.max_forward_seconds - int(time.monotonic()-began)
        if (reread["status"] != "READY_AFTER_INDEPENDENT_GEMINI_REVIEW"
                or remaining < 30):
            _print({**first, "status":"STOP_POST_PROBATION_PREFLIGHT",
                    "providerRestoration":reread["status"],
                    "publicationAuthorized":False})
            return 3
        result = advance_frozen_tail_until_boundary(
            COURSE,ROOT,private,review_one,section="section-9-6",
            max_activities=args.max_forward_activities-1,
            max_elapsed_seconds=min(900,remaining),
            migrated_clienterrors=migrated_claims)
        result = {
            **result,
            "attemptedThisInvocation": (
                first["attemptedThisInvocation"] +
                result["attemptedThisInvocation"]),
            "verifiedNewSupplementalRowsThisInvocation": (
                first["verifiedNewSupplementalRowsThisInvocation"] +
                result["verifiedNewSupplementalRowsThisInvocation"]),
            "providerRestoration":"PROBATION_PASSED_CONTINUED_NEW_WORK",
            "historicalRoleReconciled":False,
        }
    else:
        result = advance_frozen_tail_until_boundary(
            COURSE,ROOT,private,review_one,section="section-9-6",
            max_activities=args.max_forward_activities,
            max_elapsed_seconds=args.max_forward_seconds,
            migrated_clienterrors=migrated_claims)
        result["historicalRoleReconciled"] = False
    _print(result)
    return (0 if result["status"] in (
        "STOP_TAIL_ACTIVITY_BUDGET_REACHED",
        "STOP_TAIL_NO_ELIGIBLE_ORIGINAL_REVIEW",
        "STOP_TAIL_ELAPSED_BUDGET",
    ) else 3)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--private-root", type=Path)
    parser.add_argument("--diagnose-only", action="store_true")
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--allow-generated-text-transfer", action="store_true")
    parser.add_argument("--auto-advance", action="store_true",
                        help="Within one authorized invocation, advance across "
                             "new eligible activities without a scheduler.")
    parser.add_argument("--advance-revised-96", action="store_true",
                        help="Exact two changed Section9.6 source-SHA Gemini QA "
                             "under separate owner charter; never old-role replay.")
    parser.add_argument("--advance-new-four", action="store_true",
                        help="Exactly four untouched original Section9.2 items, "
                             "two independent Gemini roles each, max 8 calls.")
    parser.add_argument("--standing-science", action="store_true",
                        help="Standing owner Gemini consent for NEW untouched "
                             "source-bound Section9.1 activities; finite 4/8 "
                             "per invocation, never replay old role claims.")
    parser.add_argument("--final-two-science", action="store_true",
                        help="Two NEW trilingual reviewed content versions for "
                             "the distinct historical unknown Section9.1 idx0 "
                             "and Section9.6 idx6 identities, at most four Gemini calls.")
    parser.add_argument("--source-free-advance", action="store_true",
                        help="Advance registered local repair, immutable QA "
                             "handoffs and untouched-original staging with "
                             "zero model requests or paid authorization.")
    parser.add_argument("--max-forward-activities", type=int, default=4)
    parser.add_argument("--max-forward-seconds", type=int, default=900)
    args = parser.parse_args(argv)
    if args.final_two_science and (
            args.source_free_advance or args.diagnose_only or args.auto_advance
            or args.advance_new_four or args.advance_revised_96
            or args.standing_science):
        _print({"status":"STOP_FINAL_TWO_MODE_CONFLICT",
                "publicationAuthorized":False})
        return 2
    if args.standing_science and (
            args.source_free_advance or args.diagnose_only or args.auto_advance
            or args.advance_new_four or args.advance_revised_96
            or args.final_two_science):
        _print({"status":"STOP_STANDING_SCIENCE_MODE_CONFLICT",
                "publicationAuthorized":False})
        return 2
    if args.advance_revised_96 and (
            args.source_free_advance or args.diagnose_only or args.auto_advance
            or args.advance_new_four or args.standing_science):
        _print({"status":"STOP_REVISED96_MODE_CONFLICT",
                "publicationAuthorized":False})
        return 2
    if args.advance_new_four and (
            args.source_free_advance or args.diagnose_only or args.auto_advance
            or args.advance_revised_96 or args.standing_science):
        _print({"status":"STOP_NEW4_MODE_CONFLICT",
                "publicationAuthorized":False})
        return 2
    if args.source_free_advance and (
            args.execute or args.diagnose_only or args.auto_advance):
        _print({"status":"STOP_SOURCE_FREE_MODE_MUST_NOT_REQUEST_PROVIDER",
                "publicationAuthorized":False})
        return 2
    if args.auto_advance and (not args.execute or args.diagnose_only):
        _print({"status":"STOP_FORWARD_EXECUTION_AUTHORIZATION_REQUIRED",
                "publicationAuthorized":False})
        return 2
    if args.diagnose_only and args.execute:
        parser.error("choose --diagnose-only or --execute, not both")
    if args.execute and not args.allow_generated_text_transfer:
        _print({"status":"STOP_GENERATED_TEXT_TRANSFER_NOT_AUTHORIZED",
                "publicationAuthorized":False})
        return 2
    local = os.environ.get("LOCALAPPDATA")
    if not local:
        _print({"status":"STOP_LOCALAPPDATA_MISSING",
                "publicationAuthorized":False})
        return 3
    base = Path(local) / "Microvid"
    chosen = args.private_root if args.private_root is not None else (
        base / "BoslaV3ReviewYoga6"
    )
    try:
        private = checked_private_root(chosen,localappdata=Path(local))
        if args.final_two_science:
            # BSA218: v7 continuous progression with immutable history.
            require_authorized_native_review_host(AUTHORITY)
            from app_generator.runtime.v3_final_two_science import (
                stage_final_two_new_inputs,advance_final_two_new_science,
                verified_final_two_science,
            )
            from app_generator.runtime.v3_standing_paid_science import (
                authorize_standing,
            )
            exact=stage_final_two_new_inputs(COURSE,ROOT,private)
            if not args.execute:
                _print({"status":"READY_FINAL_TWO_DISTINCT_NEW_SCIENCE_INPUTS",
                        "reviewInputs":[{"section":e["section"],
                                         "index":e["index"],
                                         "sha":e["sha"],
                                         "candidateSha256":e["candidateSha256"]}
                                        for e in exact],
                        "standingConsent":True,"paidGeminiCalls":0,
                        "historicalUnknownRolesReplayed":False,
                        "publicationAuthorized":False})
                return 0
            if args.max_forward_activities<2:
                _print({"status":"STOP_FINAL_TWO_INVOCATION_ACTIVITIES_TOO_SMALL",
                        "publicationAuthorized":False})
                return 2
            grant=authorize_standing(
                execute=args.execute,transfer=args.allow_generated_text_transfer,
                activities=2,seconds=args.max_forward_seconds)
            pre=_complete_source_free_with_browser(
                private,advance_source_free_until_boundary(COURSE,ROOT,private))
            before=pre.get("realCandidateBrowserAcceptance",{})
            if (pre.get("section96ScienceIntegrated") is not True
                    or pre.get("paidGeminiCalls")!=0
                    or before.get("status")!=
                        "ACTUAL_UNADMITTED_CHAPTER9_BROWSER_QA_PASS"
                    or before.get("renderedChecks")!=698
                    or before.get("all108ActivitiesVisited") is not True
                    or before.get("proposalSha256")!=pre.get("proposalSha256")):
                _print({"status":"STOP_FINAL_TWO_GENUINE_BROWSER_PREFLIGHT",
                        "publicationAuthorized":False})
                return 3
            from app_generator.runtime.native_sdk_environment import (
                delegate_to_supported_sdk,
            )
            delegated=delegate_to_supported_sdk(
                ROOT,list(argv) if argv is not None else sys.argv[1:],
                entrypoint=Path(__file__))
            if delegated is not None:
                return delegated
            from app_generator.gemini.v3_native_api_reviewers import (
                V3NativeGeminiApiSessions,
            )
            from app_generator.runtime.v3_authorized_review import (
                advance_v3_generated_text,
            )
            cfg=_load_native_config()
            capability=diagnose_declared_generation_support(cfg)
            def review_one(raw,activity_id,private_root):
                with V3NativeGeminiApiSessions(
                    cfg,operation_authorized=True,
                    generated_content_transfer_allowed=True,
                    candidate_offset=0) as reviewer:
                    return advance_v3_generated_text(
                        raw,reviewer.open_pair(activity_id),
                        private_root=private_root,
                        generated_content_transfer_allowed=True,
                        max_activities=1)
            science=advance_final_two_new_science(
                COURSE,ROOT,private,execute=True,
                transfer=args.allow_generated_text_transfer,
                max_seconds=args.max_forward_seconds,
                capability=capability,review_one=review_one)
            if (science.get("status")!="FINAL_TWO_STANDING_SCIENCE_COMPLETED"
                    or science.get("allNewScientificPass") is not True):
                _print({**science,
                    "postReviewAutomaticContinuation":{
                        "status":"STOP_FINAL_TWO_SCIENCE_NOT_ACCEPTED",
                        "publicationAuthorized":False}})
                return 3
            # Independent immutable two-role proof must precede staging.
            reviewed=verified_final_two_science(COURSE,ROOT,private)
            if reviewed is None:
                raise ValueError("V3_FINAL_TWO_NO_REAL_INDEPENDENT_PROOF")
            post=_complete_source_free_with_browser(
                private,advance_source_free_until_boundary(COURSE,ROOT,private))
            after=post.get("realCandidateBrowserAcceptance",{})
            done=(post.get("paidGeminiCalls")==0
                  and post.get("section96ScienceIntegrated") is True
                  and after.get("status")==
                      "ACTUAL_UNADMITTED_CHAPTER9_BROWSER_QA_PASS"
                  and after.get("all108ActivitiesVisited") is True
                  and after.get("renderedChecks")==698
                  and after.get("proposalSha256")==post.get("proposalSha256")
                  and post.get("finalTwoScienceIntegrated") is True)
            _print({**science,"standingAuthorization":grant,
                    "postReviewAutomaticContinuation":{
                        "status":("FINAL_TWO_AUTOMATICALLY_ADVANCED_BROWSER_PASS"
                                  if done else "STOP_FINAL_TWO_BROWSER_OR_SCIENCE"),
                        "proposalSha256":post.get("proposalSha256"),
                        "paidGeminiCalls":0,"publicationAuthorized":False}})
            return 0 if done else 3
        if args.standing_science:
            # BSA217: standing owner Gemini consent for any NEW eligible
            # review identity, currently Section9.1 untouched siblings.
            # This is a finite batch, not a renewed old paid charter.
            require_authorized_native_review_host(AUTHORITY)
            from app_generator.runtime.v3_standing_paid_science import (
                authorize_standing,section91_evidence,advance_standing_science,
            )
            preflight=section91_evidence(COURSE,ROOT,private)
            eligible=[{"index":e["index"],"activityId":e["activityId"],
                       "sha":e["sha"]} for e in preflight["items"]
                      if e["originalReviewState"]=="UNREVIEWED_ELIGIBLE"]
            if not args.execute:
                _print({"status":"READY_STANDING_NEW_SCIENTIFIC_INPUTS",
                        "standingConsent":True,"nextUnreviewed":eligible[:4],
                        "remainingNewEligible":len(eligible),"paidGeminiCalls":0,
                        "publicationAuthorized":False})
                return 0
            grant=authorize_standing(execute=args.execute,
                transfer=args.allow_generated_text_transfer,
                activities=args.max_forward_activities,
                seconds=args.max_forward_seconds)
            # Genuine source-free/browser baseline before ANY paid provider.
            offline=_complete_source_free_with_browser(
                private,advance_source_free_until_boundary(COURSE,ROOT,private))
            browser=offline.get("realCandidateBrowserAcceptance",{})
            if (offline.get("section96ScienceIntegrated") is not True
                    or offline.get("paidGeminiCalls")!=0
                    or browser.get("status")!=
                        "ACTUAL_UNADMITTED_CHAPTER9_BROWSER_QA_PASS"
                    or browser.get("renderedChecks")!=698
                    or browser.get("all108ActivitiesVisited") is not True
                    or browser.get("proposalSha256")!=offline.get("proposalSha256")):
                _print({"status":"STOP_STANDING_PREPAID_BROWSER_PREFLIGHT",
                        "publicationAuthorized":False})
                return 3
            from app_generator.runtime.native_sdk_environment import (
                delegate_to_supported_sdk,
            )
            delegated=delegate_to_supported_sdk(
                ROOT,list(argv) if argv is not None else sys.argv[1:],
                entrypoint=Path(__file__))
            if delegated is not None:
                return delegated
            from app_generator.gemini.v3_native_api_reviewers import (
                V3NativeGeminiApiSessions,
            )
            from app_generator.runtime.v3_authorized_review import (
                advance_v3_generated_text,
            )
            config=_load_native_config()
            capability=diagnose_declared_generation_support(config)
            def review_one(raw,activity_id,private_root):
                with V3NativeGeminiApiSessions(
                    config,operation_authorized=True,
                    generated_content_transfer_allowed=True,
                    candidate_offset=0) as reviewer:
                    return advance_v3_generated_text(
                        raw,reviewer.open_pair(activity_id),
                        private_root=private_root,
                        generated_content_transfer_allowed=True,
                        max_activities=1)
            reviewed=advance_standing_science(
                COURSE,ROOT,private,execute=True,
                transfer=args.allow_generated_text_transfer,
                max_activities=args.max_forward_activities,
                max_seconds=args.max_forward_seconds,
                capability=capability,review_one=review_one)
            # Same-run source-free staging and REAL 108/698 browser after
            # independent model work; new evidence is never itself a release.
            post=_complete_source_free_with_browser(
                private,advance_source_free_until_boundary(COURSE,ROOT,private))
            after=post.get("realCandidateBrowserAcceptance",{})
            status=("STANDING_AUTOMATICALLY_ADVANCED_BROWSER_PASS"
                    if reviewed.get("status")=="STANDING_BOUNDED_BATCH_COMPLETED"
                       and reviewed.get("allNewScientificPass") is True
                       and post.get("section96ScienceIntegrated") is True
                       and post.get("paidGeminiCalls")==0
                       and after.get("status")==
                           "ACTUAL_UNADMITTED_CHAPTER9_BROWSER_QA_PASS"
                       and after.get("all108ActivitiesVisited") is True
                       and after.get("renderedChecks")==698
                       and after.get("proposalSha256")==post.get("proposalSha256")
                    else "STANDING_STOP_SCIENCE_OR_BROWSER_NOT_ACCEPTED")
            _print({**reviewed,"standingAuthorization":grant,
                    "postReviewAutomaticContinuation":{
                        "status":status,"proposalSha256":post.get("proposalSha256"),
                        "browserReceiptSha256":after.get("integritySha256"),
                        "paidGeminiCalls":0,"publicationAuthorized":False}})
            return 0 if status=="STANDING_AUTOMATICALLY_ADVANCED_BROWSER_PASS" else 3
        if args.advance_new_four:
            # BSA209: separately owner-authorized 4 *new* original 9.2
            # activity identities. The OLD science-failed idx13 and earlier
            # ambiguous 9.1 roles are never revisited.
            require_authorized_native_review_host(AUTHORITY)
            from app_generator.runtime.v3_four_new92_review import (
                authorize_four_new, exact_four_unreviewed,
                advance_four_new, continue_four_to_browser,
            )
            inputs = exact_four_unreviewed(COURSE, ROOT, private)
            if not args.execute:
                _print({"status":"READY_FOUR_UNTOUCHED_SECTION92_INPUTS",
                        "reviewInputs":[{"index":x["index"],
                                         "sha":x["sha"]} for x in inputs],
                        "maximumGeminiCalls":8,"paidGeminiCalls":0,
                        "publicationAuthorized":False})
                return 0
            authorize_four_new(
                execute=args.execute,transfer=args.allow_generated_text_transfer,
                activities=args.max_forward_activities,
                seconds=args.max_forward_seconds)
            # Browser and source staging are independently valid, and must
            # succeed BEFORE any potentially paid provider call.
            offline = _complete_source_free_with_browser(
                private,advance_source_free_until_boundary(COURSE,ROOT,private))
            qa = offline.get("realCandidateBrowserAcceptance",{})
            if (offline.get("section96ScienceIntegrated") is not True
                    or offline.get("paidGeminiCalls") != 0
                    or qa.get("status") !=
                        "ACTUAL_UNADMITTED_CHAPTER9_BROWSER_QA_PASS"
                    or qa.get("renderedChecks") != 698
                    or qa.get("all108ActivitiesVisited") is not True
                    or qa.get("proposalSha256") != offline.get("proposalSha256")):
                _print({"status":"STOP_NEW4_SOURCEFREE_PREFLIGHT_FAILED",
                        "sourceFreeRecovery":offline,
                        "publicationAuthorized":False})
                return 3
            from app_generator.runtime.native_sdk_environment import (
                delegate_to_supported_sdk,
            )
            delegated=delegate_to_supported_sdk(
                ROOT,list(argv) if argv is not None else sys.argv[1:],
                entrypoint=Path(__file__))
            if delegated is not None:
                return delegated
            from app_generator.gemini.v3_native_api_reviewers import (
                V3NativeGeminiApiSessions,
            )
            from app_generator.runtime.v3_authorized_review import (
                advance_v3_generated_text,
            )
            cfg=_load_native_config()
            capability=diagnose_declared_generation_support(cfg)
            def review_one(raw,activity_id,private_root):
                with V3NativeGeminiApiSessions(
                    cfg,operation_authorized=True,
                    generated_content_transfer_allowed=True,
                    candidate_offset=0,
                ) as reviewer:
                    return advance_v3_generated_text(
                        raw,reviewer.open_pair(activity_id),
                        private_root=private_root,
                        generated_content_transfer_allowed=True,
                        max_activities=1)
            result=advance_four_new(
                COURSE,ROOT,private,execute=True,
                transfer=args.allow_generated_text_transfer,
                max_activities=args.max_forward_activities,
                max_seconds=args.max_forward_seconds,
                capability=capability,review_one=review_one)
            post=continue_four_to_browser(
                result,lambda: _complete_source_free_with_browser(
                    private,advance_source_free_until_boundary(COURSE,ROOT,private)))
            _print({**result,"preflightBrowser":qa.get("status"),
                    "postReviewAutomaticContinuation":post})
            return 0 if (
                result["status"]=="NEW4_AUTHORIZED_BATCH_COMPLETED"
                and post["status"]=="NEW4_AUTOMATICALLY_ADVANCED_108_BROWSER_PASS"
            ) else 3
        if args.advance_revised_96:
            require_authorized_native_review_host(AUTHORITY)
            from app_generator.runtime.v3_section96_authorized_revised_qa import (
                authorize_revised96, stage_and_verify_two_new_inputs,
                advance_revised96_reviews,
            )
            # Reuse registered source-bound BSA201 and BSA204/205 REAL Chrome
            # checks. No new paid request can bypass scientific/visual
            # preflight, existing old no-replay witnesses, or owner charter.
            inputs=stage_and_verify_two_new_inputs(COURSE,ROOT,private)
            if not args.execute:
                _print({"status":"READY_TWO_NEW_SOURCE_BOUND_SECTION96_REVISIONS",
                        "reviewInputs":[{"index":x["index"],"sha":x["sha"]}
                                        for x in inputs],
                        "paidGeminiCalls":0,
                        "publicationAuthorized":False})
                return 0
            authorize_revised96(
                execute=args.execute,transfer=args.allow_generated_text_transfer,
                activities=args.max_forward_activities,
                seconds=args.max_forward_seconds)
            offline=_complete_source_free_with_browser(
                private,advance_source_free_until_boundary(COURSE,ROOT,private))
            old_browser=offline.get("realCandidateBrowserAcceptance",{})
            new_browser=offline.get("scienceRevisionBrowserAcceptance",{})
            if (old_browser.get("status")!=
                    "ACTUAL_UNADMITTED_CHAPTER9_BROWSER_QA_PASS"
                    or old_browser.get("renderedChecks")!=698
                    or not (
                        (new_browser.get("status")==
                            "ACTUAL_INDEX9_SCIENCE_REVISION_BROWSER_QA_PASS_NOT_SCIENTIFIC_QA"
                         and new_browser.get("renderedChecks")==698)
                        or (offline.get("section96ScienceIntegrated") is True
                            and new_browser.get("status")==
                                "SCIENCE_INDEX9_INCLUDED_IN_FULL_CANDIDATE_BROWSER")
                    )):
                _print({"status":"STOP_REVISED96_REAL_BROWSER_NOT_VERIFIED",
                        "sourceFreeRecovery":offline,
                        "publicationAuthorized":False})
                return 3
            from app_generator.runtime.native_sdk_environment import (
                delegate_to_supported_sdk,
            )
            delegated=delegate_to_supported_sdk(
                ROOT,list(argv) if argv is not None else sys.argv[1:],
                entrypoint=Path(__file__))
            if delegated is not None:
                return delegated
            # BSA211: use the existing module-level diagnostic import.
            # Re-importing this name only in this later branch makes Python
            # treat it as local throughout main(), breaking --advance-new-four.
            from app_generator.gemini.v3_native_api_reviewers import (
                V3NativeGeminiApiSessions,
            )
            from app_generator.runtime.v3_authorized_review import (
                advance_v3_generated_text,
            )
            config=_load_native_config()
            capability=diagnose_declared_generation_support(config)
            def review_one(raw,activity_id,private_root):
                with V3NativeGeminiApiSessions(
                    config,operation_authorized=True,
                    generated_content_transfer_allowed=True,
                    candidate_offset=0,
                ) as reviewer:
                    pair=reviewer.open_pair(activity_id)
                    return advance_v3_generated_text(
                        raw,pair,private_root=private_root,
                        generated_content_transfer_allowed=True,
                        max_activities=1)
            result=advance_revised96_reviews(
                COURSE,ROOT,private,
                execute=True,transfer=args.allow_generated_text_transfer,
                max_activities=args.max_forward_activities,
                max_seconds=args.max_forward_seconds,
                capability=capability,review_one=review_one)
            # BSA208: complete the next safe local stage in THIS authorized
            # invocation. The verified old roles cannot be replayed; a
            # "batch completed" with genuine science FAIL must not advance.
            post=_continue_revised96_source_free(private,result)
            _print({**result,"sourceFreeBrowserOriginal":
                    old_browser.get("status"),"sourceFreeBrowserScienceRevision":
                    new_browser.get("status"),
                    "postReviewAutomaticContinuation":post})
            return 0 if (
                result["status"]=="REVISED96_AUTHORIZED_BATCH_COMPLETED"
                and post["status"]==
                    "REVISED96_AUTOMATICALLY_ADVANCED_TO_108_BROWSER_PASS"
            ) else 3
        if args.source_free_advance:
            require_authorized_native_review_host(AUTHORITY)
            result=_complete_source_free_with_browser(
                private,advance_source_free_until_boundary(COURSE,ROOT,private))
            qa=result.get("realCandidateBrowserAcceptance",{})
            has_proposal=isinstance(result.get("proposalSha256"),str)
            genuine=(qa.get("status")==
                       "ACTUAL_UNADMITTED_CHAPTER9_BROWSER_QA_PASS"
                     and qa.get("proposalSha256")==result.get("proposalSha256")
                     and qa.get("renderedChecks")==698
                     and qa.get("all108ActivitiesVisited") is True
                     and qa.get("allLocaleViewportPromptChecks")==648)
            no_proposal=(not has_proposal and qa.get("status")==
                         "NO_NEW_REAL_CANDIDATE_FOR_BROWSER_QA")
            # BSA220: immediately transition a fully authenticated sourcefree
            # browser milestone to the *independent* versioned admission
            # readiness check. No new API calls or publication side effect.
            if genuine and result.get("finalTwoScienceIntegrated") is True:
                from app_generator.runtime.v3_versioned_readiness import (
                    evaluate_current_versioned_evidence,
                )
                result["versionedEvidenceReadiness"]=(
                    evaluate_current_versioned_evidence(ROOT,private))
            _print(result)
            # BSA219: the previous worker unconditionally returned exit0
            # even after a real Chrome STOP. An unsuccessful browser check
            # is a live blocker, not a verified checkpoint for paid science.
            return 0 if (result.get("paidGeminiCalls")==0
                         and result.get("publicationAuthorized") is False
                         and (genuine if has_proposal else no_proposal)) else 3
        if args.auto_advance:
            ready = plan_v3_course_review(
                COURSE, ROOT, private_root=private,
                continue_independent=True)
            if (ready["dispatchStatus"] != "READY_FOR_AUTHORIZED_REVIEW_SESSIONS"
                    and "section-9-6" in ready.get("quarantinedSections", [])):
                # BSA-185: the original activity at index5 remains forever
                # AMBIGUOUS, but untouched frozen original indices6..17 have
                # NEVER been submitted. Continue those with distinct exact
                # one-activity identities under the existing original-only
                # paid authorization, not a new content replacement scope.
                tail = plan_frozen_original_tail(
                    COURSE,ROOT,private,section="section-9-6")
                if (tail["status"] ==
                        "READY_FOR_AUTHORIZED_FROZEN_ORIGINAL_TAIL_REVIEW"):
                    return _advance_unchanged_frozen_tail(args,private,argv)
            if ready["dispatchStatus"] != "READY_FOR_AUTHORIZED_REVIEW_SESSIONS":
                require_authorized_native_review_host(AUTHORITY)
                offline = _complete_source_free_with_browser(
                    private,advance_source_free_until_boundary(
                        COURSE,ROOT,private))
                _print({**status_from_plan(
                    ready,status=ready["dispatchStatus"]),
                        "sourceFreeRecovery":offline})
                return 0
            # BSA-189: the ordinary READY course path also needs independent
            # source-free recovery BEFORE paid authorization. Previously a
            # denied paid charter stranded registered local repair/QA even
            # when no provider transmission was needed. Keep the independent
            # reviewer permission gate fully authoritative AFTER staging.
            require_authorized_native_review_host(AUTHORITY)
            _complete_source_free_with_browser(
                private,advance_source_free_until_boundary(COURSE,ROOT,private))
            authorize_paid_v3_action(
                "FROZEN_ORIGINAL_ELIGIBLE_NEW_ACTIVITY",
                execute=args.execute,
                transfer=args.allow_generated_text_transfer,
                next_section=ready.get("nextSection"),
                max_activities=args.max_forward_activities,
                max_elapsed_seconds=args.max_forward_seconds)
            # This is part of this existing normal entrypoint, not a new
            # scheduled task. Each iteration invokes the unchanged
            # one-activity reviewer and its original permission/claim gates.
            require_authorized_native_review_host(AUTHORITY)
            from app_generator.runtime.v3_forward_progress import (
                advance_until_boundary,
            )
            from app_generator.runtime.v3_recovery_policy import (
                apply_registered_recovery,
            )
            def read_plan():
                return plan_v3_course_review(
                    COURSE, ROOT, private_root=private,
                    continue_independent=True)
            def execute_one():
                output = io.StringIO()
                with redirect_stdout(output):
                    return main([
                        "--private-root", str(private),
                        "--execute", "--allow-generated-text-transfer"])
            report = advance_until_boundary(
                private, read_plan, execute_one,
                operation_authorized=args.execute,
                transfer_authorized=args.allow_generated_text_transfer,
                max_activities=args.max_forward_activities,
                max_elapsed_seconds=args.max_forward_seconds,
                source_free_recovery=lambda plan: apply_registered_recovery(
                    COURSE, private, plan))
            _print(report)
            return 0 if report["status"] in (
                "STOP_FORWARD_ACTIVITY_BUDGET_REACHED",
                "STOP_DETERMINISTIC_RELEASE_QA_PENDING",
                "STOP_VERSIONED_CONTENT_REPAIR_REQUIRED",
                "STOP_UNRECONCILED_CLAIM_NO_REPLAY",
                "STOP_PROVIDER_CIRCUIT_OPEN",
                "STOP_PROVIDER_RECOVERY_BUDGET",
                "STOP_FORWARD_ELAPSED_BOUND") else 3
        before = plan_v3_course_review(COURSE,ROOT,private_root=private,
                                       continue_independent=True)
        if not (args.execute or args.diagnose_only):
            _print(status_from_plan(before,status="DRY_RUN_NO_PROVIDER_REQUEST"))
            return 0
        if (args.execute and before["dispatchStatus"] ==
                "READY_FOR_AUTHORIZED_REVIEW_SESSIONS"):
            authorize_paid_v3_action(
                "FROZEN_ORIGINAL_ELIGIBLE_NEW_ACTIVITY",
                execute=True,
                transfer=args.allow_generated_text_transfer,
                next_section=before.get("nextSection"),
                max_activities=1,
                max_elapsed_seconds=900)
        # No credential access, SDK setup, or private review state on HP.
        require_authorized_native_review_host(AUTHORITY)
        # Reuse BSA-164's bounded isolated SDK bootstrap on Yoga 6 only.
        # A child is started BEFORE holding the coordinator lock; otherwise
        # its own legitimate lock acquisition would appear to conflict.
        from app_generator.runtime.native_sdk_environment import delegate_to_supported_sdk
        if args.diagnose_only or gate_review_plan(before) == "READY_FOR_SOURCE_FREE_METADATA_CHECK":
            delegated = delegate_to_supported_sdk(
                ROOT, list(argv) if argv is not None else sys.argv[1:],
                entrypoint=Path(__file__))
            if delegated is not None:
                return delegated
        with coordinator_lock(private):
            # Re-plan after obtaining exclusive worker ownership.
            before = plan_v3_course_review(COURSE,ROOT,private_root=private,
                                           continue_independent=True)
            gated = gate_review_plan(before)
            if not args.diagnose_only and gated != "READY_FOR_SOURCE_FREE_METADATA_CHECK":
                receipt = status_from_plan(before,status=gated)
                persist_status(private,receipt)
                _print(receipt)
                return 0
            config = _load_native_config()
            preferred = (before.get("providerCapacity") or {}).get(
                "serverErrorActivitiesHistorical",0)
            diagnostic = diagnose_model_metadata(
                config,preferred_offset=preferred)
            if args.diagnose_only:
                # Historical BSA-196: model metadata may return 200 on
                # both keys while generation is refused. Check the declared
                # model action on both slots, but never claim a working
                # provider, project tier, quota or permission from this.
                capability = (
                    diagnose_declared_generation_support(config)
                    if diagnostic["status"] == "READY_SOURCE_FREE_ONLY"
                    else {
                        "status":"SKIPPED_AFTER_METADATA_FAILURE",
                        "sourceFree":True,
                        "generationPermissionVerified":False,
                        "projectQuotaVerified":False,
                        "paidModelCalls":0,
                    })
                final_diagnostic_status = (
                    "DIAGNOSTIC_"+capability["status"]
                    if diagnostic["status"]=="READY_SOURCE_FREE_ONLY"
                    and capability["status"] !=
                        "MODEL_GENERATION_ACTION_DECLARED_QUOTA_UNVERIFIED"
                    else "DIAGNOSTIC_"+diagnostic["status"]
                )
                receipt = status_from_plan(
                    before,status=final_diagnostic_status,
                    diagnostic=diagnostic)
                receipt["generationCapabilityMetadata"] = capability
                receipt["generationPermissionVerified"] = False
                receipt["projectQuotaVerified"] = False
                persist_status(private,receipt)
                _print(receipt)
                return 0 if (diagnostic["status"]=="READY_SOURCE_FREE_ONLY"
                             and capability["status"] ==
                                 "MODEL_GENERATION_ACTION_DECLARED_QUOTA_UNVERIFIED") else 3
            if diagnostic["status"]!="READY_SOURCE_FREE_ONLY":
                receipt = status_from_plan(
                    before,status=diagnostic["status"],diagnostic=diagnostic)
                persist_status(private,receipt)
                _print(receipt)
                return 3
            index = diagnostic["selectedCandidateIndex"]
            # This is a NEW frozen activity only: normal V3 course dispatcher
            # first enforces immutable per-role claims and source hash scope.
            command = ["--private-root",str(private),"--batch-size","1",
                       "--max-batches","1","--candidate-offset",str(index),
                       "--execute","--allow-generated-text-transfer"]
            output = io.StringIO()
            with redirect_stdout(output):
                native_exit = native.main(command)
            # Avoid returning raw provider replies. Only the verified frozen
            # read-only planner can supply the post-invocation status.
            after = plan_v3_course_review(COURSE,ROOT,private_root=private,
                                          continue_independent=True)
            receipt = status_from_plan(
                after,status=("NEW_ACTIVITY_COMPLETED" if
                    after["activitiesFullyModelReviewed"] >
                    before["activitiesFullyModelReviewed"] else
                    "NO_NEW_FULLY_REVIEWED_ACTIVITY"),
                diagnostic=diagnostic,native_exit_code=native_exit)
            persist_status(private,receipt)
            _print(receipt)
            return 0 if native_exit==0 else 3
    except Exception as exc:
        # No provider text, API secrets, user data or filenames from errors.
        _print({"status":"STOP_YOGA6_RECOVERY_WORKER",
                "reasonClass":type(exc).__name__,"publicationAuthorized":False})
        return 3


if __name__=="__main__":
    raise SystemExit(main())

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
    """BSA254: serialize the ENTIRE source-free worker across ChatGPT sessions.

    Reuse the historically tested BSA Yoga6 OS-released coordinator lock.
    Hold it before ANY source-free activity, PDF, Chrome or signed checkpoint.
    The lock path is invariant even if an alternate valid private root is
    supplied; the pinned-Selenium launcher re-execs BEFORE calling main().
    """
    args = list(sys.argv[1:] if argv is None else argv)
    if "--source-free-advance" not in args:
        return _main_unlocked(args)
    local = os.environ.get("LOCALAPPDATA")
    if not local:
        return _main_unlocked(args)
    parse = argparse.ArgumentParser(add_help=False)
    parse.add_argument("--private-root", type=Path)
    try:
        options, _ = parse.parse_known_args(args)
    except SystemExit:
        return _main_unlocked(args)
    try:
        if options.private_root is not None:
            checked_private_root(options.private_root, localappdata=Path(local))
        # All source-free runs on this owner PC contend for ONE native
        # coordinator; never derive the lock from a changeable --private-root.
        # BSA254 real Yoga6 regression: the V3 source-free forward stage
        # ALSO takes the existing non-reentrant coordinator_lock(private).
        # Reusing that exact lock at the outer boundary deadlocks itself.
        # Preserve its immutable inner ownership and use a DIFFERENT,
        # fixed OS-backed whole-session lock scope for all source-free runs.
        lock_root = checked_private_root(
            Path(local) / "Microvid" / "BoslaV3ReviewYoga6"
            / ".source-free-singleflight",
            localappdata=Path(local))
        with coordinator_lock(lock_root):
            return _main_unlocked(args)
    except RuntimeError as exc:
        if str(exc) == "V3_WORKER_ALREADY_RUNNING":
            _print({"status":"STOP_YOGA6_SOURCE_FREE_ALREADY_RUNNING",
                    "publicationAuthorized":False})
            return 3
        _print({"status":"STOP_YOGA6_SOURCE_FREE_LOCK_ERROR",
                "reasonClass":type(exc).__name__,
                "publicationAuthorized":False})
        return 3
    except (ValueError, OSError) as exc:
        _print({"status":"STOP_YOGA6_SOURCE_FREE_LOCK_ERROR",
                "reasonClass":type(exc).__name__,
                "publicationAuthorized":False})
        return 3


def _main_unlocked(argv: list[str] | None = None) -> int:
    """Original worker stages; entrypoint owns source-free single-flight."""
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
                # Owner Decision0078: V1-V5 must follow the genuine source-
                # bound readiness in the SAME normal sourcefree invocation.
                # Its own proof gate is mandatory; never fill in a result
                # when the hosted CI/source revision is not yet accepted.
                ready=result["versionedEvidenceReadiness"]
                # BSA224: hosted GitHub CI may still run when real Chrome
                # finishes. Do not falsely return normal success or depend
                # on a second manual 'proceed'. Bounded source-free polling
                # followed by full source/browser/CI revalidation and the
                # SAME normal V1-V6 handoff; never request Gemini/PDF.
                if ready.get("status")==(
                        "VERSIONED_SCIENCE_BROWSER_VERIFIED_WAIT_EXACT_HEAD_CI"):
                    from app_generator.runtime.v3_ci_resume import (
                        await_exact_ci_and_resume,
                    )
                    recovered=await_exact_ci_and_resume(ROOT,private,ready)
                    # BSA226: CI polling metadata describes an operation,
                    # never part of the immutable source-bound readiness.
                    # Preserve the genuine saved readiness byte-for-byte
                    # for V1-V7's strict exact-evidence admission gates.
                    marker={"ciRecoveryPolls","ciRecoveredInSameInvocation"}
                    if (recovered.get("status")==
                            "VERSIONED_SCIENCE_BROWSER_AND_CI_VERIFIED_UNADMITTED"
                            and marker.intersection(recovered)):
                        polls=recovered.get("ciRecoveryPolls")
                        if (recovered.get("ciRecoveredInSameInvocation") is not True
                                or type(polls) is not int
                                or not 1<=polls<=25):
                            raise ValueError("V3_CI_RECOVERY_UNSAFE_POLL_METADATA")
                        result["exactHostedCiRecovery"]={
                            "status":"EXACT_HEAD_CI_RECOVERED_IN_NORMAL_WORKER",
                            "polls":polls,"paidGeminiCalls":0,
                            "publicationAuthorized":False}
                        ready={k:v for k,v in recovered.items()
                               if k not in marker}
                    else:
                        ready=recovered
                    result["versionedEvidenceReadiness"]=ready
                if (ready.get("status")!=
                        "VERSIONED_SCIENCE_BROWSER_AND_CI_VERIFIED_UNADMITTED"
                        or ready.get("exactHeadHostedCiSuccess") is not True):
                    result["automaticCiRecoveryBoundary"]={
                        "status":ready.get("status"),
                        "publicationAuthorized":False,"paidGeminiCalls":0}
                    _print(result)
                    return 3
                from app_generator.runtime.v3_five_stage_completion import (
                    advance_five_stage_on_pinned_browser,
                )
                result["fiveStageAutonomousCompletion"]=(
                    advance_five_stage_on_pinned_browser(ROOT,private,ready))
                # BSA225/v7.1: a V6 checkpoint is a CONTINUE event. Dispatch
                # the actual production release builder on all six genuine
                # exact-HMAC packages privately, in THIS same normal run.
                # Never call public Git/Pages publisher or model/PDF API.
                completed=result["fiveStageAutonomousCompletion"]
                if completed.get("status")==(
                        "FIVE_STAGE_PRIVATE_TECHNICAL_PATH_COMPLETE_NO_PUBLICATION"):
                    from app_generator.runtime.v3_public_bundle_handoff import (
                        dispatch_private_public_bundle_build,
                    )
                    result["realPublicBundleBuildHandoff"]=(
                        dispatch_private_public_bundle_build(
                            ROOT,private,ready,completed))
                    # BSA227: continue past the genuine V7 checkpoint into
                    # read-only authenticated public destination scope.
                    # This only clones/compares and checks GitHub permissions,
                    # and NEVER runs a push, PR merge, or public deploy.
                    from app_generator.runtime.v3_public_deployment_scope import (
                        verify_public_deployment_scope,
                    )
                    result["publicDeploymentScopeAudit"]=(
                        verify_public_deployment_scope(
                            ROOT,private,ready,
                            result["realPublicBundleBuildHandoff"]))
                    # BSA229: a genuine V8 checkpoint dispatches three
                    # production release bundles into an immutable local
                    # proposal. No Git push, PR, merge or public deployment.
                    from app_generator.runtime.v3_pinned_public_release_proposal import (
                        stage_pinned_private_public_proposal,
                    )
                    result["pinnedPrivateReleaseProposal"]=(
                        stage_pinned_private_public_proposal(
                            ROOT,private,ready,
                            result["publicDeploymentScopeAudit"]))
                    # BSA230: follow a real V9 private production release
                    # with actual localhost Selenium Chrome acceptance on
                    # all three bundles. Never use any public Git writes.
                    from app_generator.runtime.v3_public_release_browser_acceptance import (
                        run_private_release_browser_acceptance,
                    )
                    result["privateReleaseBrowserAcceptance"]=(
                        run_private_release_browser_acceptance(
                            ROOT,private,ready,
                            result["pinnedPrivateReleaseProposal"]))
                    # BSA232: auto-dispatch V10 success into a read-only
                    # pinned GitHub Pages patch rehearsal. Only a local
                    # 3-route Git diff and immutable receipt are written.
                    from app_generator.runtime.v3_private_public_patch_rehearsal import (
                        stage_exact_private_public_patch,
                    )
                    result["privatePinnedPublicPatch"]=(
                        stage_exact_private_public_patch(
                            ROOT,private,ready,
                            result["pinnedPrivateReleaseProposal"],
                            result["privateReleaseBrowserAcceptance"]))
                    # BSA233: authenticated V11 success MUST dispatch
                    # a private non-merging PR readiness draft before
                    # the worker returns; no public Git operations.
                    from app_generator.runtime.v3_private_nonmerging_pr_readiness import (
                        stage_private_nonmerging_pr_draft,
                    )
                    result["privateNonmergingPrReadiness"]=(
                        stage_private_nonmerging_pr_draft(
                            ROOT,private,ready,
                            result["pinnedPrivateReleaseProposal"],
                            result["privatePinnedPublicPatch"]))
                    # BSA234: historical public PR branch/PR creator reused
                    # with deterministic exact-source branch and draft-only
                    # review. A PRE_CALL receipt + read-only GitHub
                    # reconciliation forbid blind duplicate external writes.
                    # NEVER auto-merge or deploy protected Chapter9.
                    from app_generator.runtime.v3_public_nonmerging_draft_pr import (
                        dispatch_scoped_nonmerging_public_pr,
                    )
                    result["scopedPublicDraftPr"]=(
                        dispatch_scoped_nonmerging_public_pr(
                            ROOT,private,ready,
                            result["pinnedPrivateReleaseProposal"],
                            result["privatePinnedPublicPatch"],
                            result["privateNonmergingPrReadiness"]))
                    # BSA235: V13 success automatically triggers independent
                    # Chrome on the exact authenticated PUBLIC review branch,
                    # including unchanged Chapter9 routes. Read-only GitHub.
                    from app_generator.runtime.v3_public_pr_independent_browser_acceptance import (
                        independent_public_pr_browser_acceptance,
                    )
                    result["independentPublicPrBrowserAcceptance"]=(
                        independent_public_pr_browser_acceptance(
                            ROOT,private,ready,
                            result["pinnedPrivateReleaseProposal"],
                            result["privatePinnedPublicPatch"],
                            result["privateNonmergingPrReadiness"],
                            result["scopedPublicDraftPr"]))
                    # BSA236: v7.1 global roadmap starts *actual* eligible
                    # independent read-only tasks after signed public PR V14.
                    # Per-task PRE_CALL and RESULT are persistent, bounded,
                    # allowlisted; errors do not strand unrelated tasks.
                    from app_generator.runtime.v3_global_post_pr_readonly_roadmap import (
                        run_global_readonly_roadmap,
                    )
                    result["globalReadonlyRoadmapHandoff"]=(
                        run_global_readonly_roadmap(
                            ROOT,private,ready,
                            result["pinnedPrivateReleaseProposal"],
                            result["privatePinnedPublicPatch"],
                            result["privateNonmergingPrReadiness"],
                            result["scopedPublicDraftPr"],
                            result["independentPublicPrBrowserAcceptance"]))
                    # BSA237: V15 must cause an actual V16 technical PR
                    # security/accessibility check on the pinned public branch.
                    # This is read-only and CANNOT grant release approval.
                    from app_generator.runtime.v3_public_pr_security_accessibility import (
                        run_public_pr_security_accessibility,
                    )
                    result["publicPrSecurityAccessibilityPreflight"]=(
                        run_public_pr_security_accessibility(
                            ROOT,private,ready,
                            result["pinnedPrivateReleaseProposal"],
                            result["privatePinnedPublicPatch"],
                            result["privateNonmergingPrReadiness"],
                            result["scopedPublicDraftPr"],
                            result["independentPublicPrBrowserAcceptance"],
                            result["globalReadonlyRoadmapHandoff"]))
                    # BSA241/V17: genuine V16 receipt dispatches two separate,
                    # source-free READONLY tasks on frozen C3 historical evidence:
                    # actual replay-safe manifest gate and real archived-draft
                    # Chrome+academic proof-gap audit. Never redo original PDF,
                    # paid provider, failed campaign or release operations.
                    from app_generator.runtime.v3_science_c3_independent_dispatch import (
                        run_post_v16_science_c3,
                    )
                    result["scienceC3PostV16IndependentDispatch"] = (
                        run_post_v16_science_c3(
                            ROOT, private, ready,
                            result["pinnedPrivateReleaseProposal"],
                            result["privatePinnedPublicPatch"],
                            result["privateNonmergingPrReadiness"],
                            result["publicPrSecurityAccessibilityPreflight"]))
                    # BSA244 V18: real, private, exactly ONE selected textbook
                    # source.pdf on Yoga6. Bind original physical-page passages
                    # to the genuine installed 9.1 activities, test bounded
                    # momentum mathematics, and preserve all unverified
                    # multilingual/visual and independent science QA gates.
                    # Never acquire/upload external PDFs or call a model.
                    from app_generator.runtime.v3_selected_textbook_scientific_provenance import (
                        run_post_v17_selected_textbook,
                    )
                    result["selectedTextbookSourceScientificProvenance"] = (
                        run_post_v17_selected_textbook(
                            ROOT, private, ready,
                            result["pinnedPrivateReleaseProposal"],
                            result["privatePinnedPublicPatch"],
                            result["privateNonmergingPrReadiness"],
                            result["scienceC3PostV16IndependentDispatch"]))
                    # BSA245/V19: automatically reuse exact, genuinely saved
                    # two-reviewer original claims after signed single-source
                    # V18. This is only evidence inventory, never academic PASS.
                    from app_generator.runtime.v3_original_reviewer_evidence_reuse import (
                        run_post_v18_original_review_reuse,
                    )
                    result["existingOriginalReviewerEvidenceReuse"] = (
                        run_post_v18_original_review_reuse(
                            ROOT, private, ready,
                            result["pinnedPrivateReleaseProposal"],
                            result["privatePinnedPublicPatch"],
                            result["privateNonmergingPrReadiness"],
                            result["selectedTextbookSourceScientificProvenance"]))
                    # BSA247/V20: execute the historical five-gate academic
                    # checker against the same original textbook and 18 items.
                    # No role replay, no false semantic/visual/translation PASS.
                    from app_generator.runtime.v3_historical_academic_audit import (
                        run_post_v19_historical_academic_audit,
                    )
                    result["historicalAcademicFiveGateAudit"] = (
                        run_post_v19_historical_academic_audit(
                            ROOT, private, ready,
                            result["pinnedPrivateReleaseProposal"],
                            result["privatePinnedPublicPatch"],
                            result["privateNonmergingPrReadiness"],
                            result["selectedTextbookSourceScientificProvenance"],
                            result["existingOriginalReviewerEvidenceReuse"]))
                    # BSA248/V21: replay-free independent PDF source
                    # reanchoring for the *revised* locale-only private
                    # candidate, keeping all five academic gates unapproved.
                    from app_generator.runtime.v3_revised_source_proof_rebinding import (
                        run_post_v20_revised_source_rebind,
                    )
                    result["revisedSourceProofRebinding"] = (
                        run_post_v20_revised_source_rebind(
                            ROOT, private, ready,
                            result["pinnedPrivateReleaseProposal"],
                            result["privatePinnedPublicPatch"],
                            result["privateNonmergingPrReadiness"],
                            result["selectedTextbookSourceScientificProvenance"],
                            result["existingOriginalReviewerEvidenceReuse"],
                            result["historicalAcademicFiveGateAudit"]))
                    # BSA249/V22: roll-forward only exact unchanged
                    # historical two-role reviews as advisory provenance.
                    # Stage changed source-bound items for NEW independent
                    # checks without Gemini, retry or publication.
                    from app_generator.runtime.v3_exact_revised_review_reconciliation import (
                        run_post_v21_exact_revised_history_reconciliation,
                    )
                    result["exactRevisedReviewReconciliation"] = (
                        run_post_v21_exact_revised_history_reconciliation(
                            ROOT, private, ready,
                            result["pinnedPrivateReleaseProposal"],
                            result["privatePinnedPublicPatch"],
                            result["privateNonmergingPrReadiness"],
                            result["existingOriginalReviewerEvidenceReuse"],
                            result["revisedSourceProofRebinding"]))
                    # BSA251/V24 architectural fix: normal pipeline
                    # automatically reuses historical verified handlers,
                    # rechecks actual single textbook and versioned content,
                    # then persists per-gate missing proofs or real defects.
                    # Two bounded rounds converge without model replay.
                    from app_generator.runtime.v3_autonomous_academic_recovery import (
                        run_post_v22_autonomous_academic_recovery,
                    )
                    result["autonomousAcademicRecovery"] = (
                        run_post_v22_autonomous_academic_recovery(
                            ROOT, private, ready,
                            result["pinnedPrivateReleaseProposal"],
                            result["privatePinnedPublicPatch"],
                            result["privateNonmergingPrReadiness"],
                            result["exactRevisedReviewReconciliation"]))
                    # BSA252 V25: actual independent Fraction-valued
                    # MCQ/distractor and interactive answer witnesses for
                    # ALL 18 activities, grounded in one exact textbook PDF.
                    # These bounded models do NOT certify full academic PASS.
                    from app_generator.runtime.v3_section91_formal_academic_dispatch import (
                        run_post_v24_formal_science,
                    )
                    result["formalSection91Physics"] = (
                        run_post_v24_formal_science(
                            ROOT, private, ready,
                            result["pinnedPrivateReleaseProposal"],
                            result["privatePinnedPublicPatch"],
                            result["privateNonmergingPrReadiness"],
                            result["autonomousAcademicRecovery"]))
                    # BSA253/V26 typed language and scientific claim
                    # analysis, all explanation and distractor surfaces.
                    # Preserve source-version and academic nonrelease gates.
                    from app_generator.runtime.v3_source_semantic_triage import (
                        run_post_v25_source_scientific_semantic_triage,
                    )
                    result["sourceScientificSemanticTriage"] = (
                        run_post_v25_source_scientific_semantic_triage(
                            ROOT, private, ready,
                            result["pinnedPrivateReleaseProposal"],
                            result["privatePinnedPublicPatch"],
                            result["privateNonmergingPrReadiness"],
                            result["formalSection91Physics"]))
                    # BSA253 V26: always queue full explanation, distractor,
                    # rendered visual, and EN/MS/ZH meaning proofs next.
                    # Generic planner binds each task to actual source and
                    # revised content; queue never promotes academic PASS.
                    from app_generator.runtime.v3_full_semantic_proof_dispatch import (
                        run_post_v25_full_semantic_queue,
                    )
                    result["fullSemanticProofQueue"] = (
                        run_post_v25_full_semantic_queue(
                            ROOT, private, ready,
                            result["pinnedPrivateReleaseProposal"],
                            result["privatePinnedPublicPatch"],
                            result["privateNonmergingPrReadiness"],
                            result["formalSection91Physics"]))
                    # BSA255/V27 historical false symbolic-drift recovery:
                    # reparse only the disputed formula tokens under the
                    # exact two V26 source-version-bound signed receipts.
                    # Matching literal math NEVER grants academic PASS.
                    from app_generator.runtime.v3_post_v26_bounded_symbolic_recovery import (
                        run_post_v26_bounded_symbolic_recovery,
                    )
                    result["boundedSymbolicRecovery"] = (
                        run_post_v26_bounded_symbolic_recovery(
                            ROOT, private, ready,
                            result["pinnedPrivateReleaseProposal"],
                            result["privatePinnedPublicPatch"],
                            result["privateNonmergingPrReadiness"],
                            result["sourceScientificSemanticTriage"],
                            result["fullSemanticProofQueue"]))
                    # BSA256 V28: independent five-channel bounded proof
                    # producers MUST run after source-signed genuine V27.
                    # Claim only independently established limited facts;
                    # all complete academic/visual meaning gates stay open.
                    from app_generator.runtime.v3_post_v27_five_proof_producers import (
                        run_post_v27_five_proof_producers,
                    )
                    result["fiveChannelProofProducers"] = (
                        run_post_v27_five_proof_producers(
                            ROOT, private, ready,
                            result["pinnedPrivateReleaseProposal"],
                            result["privatePinnedPublicPatch"],
                            result["privateNonmergingPrReadiness"],
                            result["boundedSymbolicRecovery"]))
                    # BSA257: proceed through *every registered and executable*
                    # source-free successor on the SAME normal worker run.
                    # Add later successors to the bounded dispatch registry;
                    # no further user approval to perform safe local work.
                    from app_generator.runtime.v3_auto_development_handoff import (
                        advance_eligible_verified_development_stages,
                    )
                    result["autonomousDevelopmentContinuation"] = (
                        advance_eligible_verified_development_stages(
                            repo=ROOT, private=private, ready=ready,
                            v9=result["pinnedPrivateReleaseProposal"],
                            v11=result["privatePinnedPublicPatch"],
                            v12=result["privateNonmergingPrReadiness"],
                            prior_stage=result["fiveChannelProofProducers"],
                            run_independent_lanes=True))
            _print(result)
            # BSA219: the previous worker unconditionally returned exit0
            # even after a real Chrome STOP. An unsuccessful browser check
            # is a live blocker, not a verified checkpoint for paid science.
            return 0 if (result.get("paidGeminiCalls")==0
                         and result.get("publicationAuthorized") is False
                         and (genuine if has_proposal else no_proposal)
                         and (
                            not (genuine and
                                 result.get("finalTwoScienceIntegrated") is True)
                            or result.get("fiveStageAutonomousCompletion",{}).get(
                                "status")==
                            "FIVE_STAGE_PRIVATE_TECHNICAL_PATH_COMPLETE_NO_PUBLICATION"
                            and result.get("realPublicBundleBuildHandoff",{}).get(
                                "status")==
                            "SIX_REAL_PUBLIC_BUNDLE_BUILDS_VERIFIED_PRIVATE_NO_DEPLOY"
                            and result.get("realPublicBundleBuildHandoff",{}).get(
                                "realOriginalPublicBuilderInvocations")==6
                            and result.get("publicDeploymentScopeAudit",{}).get(
                                "status")==
                            "EXISTING_PUBLIC_SIX_SECTION_SCOPE_AND_PERMISSION_VERIFIED_NO_DEPLOY"
                            and result.get("publicDeploymentScopeAudit",{}).get(
                                "packagesRequiringUpdates")==3
                            and result.get("publicDeploymentScopeAudit",{}).get(
                                "individualChangedActivities")==5
                            and result.get("publicDeploymentScopeAudit",{}).get(
                                "publicDeployExecuted") is False
                            and result.get("pinnedPrivateReleaseProposal",{}).get(
                                "status")==
                            "THREE_ROUTE_PRIVATE_PINNED_RELEASE_PROPOSAL_READY_NO_PUBLIC_WRITE"
                            and result.get("pinnedPrivateReleaseProposal",{}).get(
                                "productionReleaseBuilderInvocations")==3
                            and result.get("pinnedPrivateReleaseProposal",{}).get(
                                "publicDeployExecuted") is False
                            and result.get("privateReleaseBrowserAcceptance",{}).get(
                                "status")==
                            "THREE_PRIVATE_PRODUCTION_BUNDLES_REAL_CHROME_RENDERED_NO_PUBLIC_WRITE"
                            and result.get("privateReleaseBrowserAcceptance",{}).get(
                                "realHeadlessChromeRoutesPassed")==3
                            and result.get("privateReleaseBrowserAcceptance",{}).get(
                                "publicDeployExecuted") is False
                            and result.get("privatePinnedPublicPatch",{}).get(
                                "status")==
                            "PINNED_THREE_SECTION_PRIVATE_PUBLIC_PATCH_REHEARSED_NO_PUBLIC_WRITE"
                            and result.get("privatePinnedPublicPatch",{}).get(
                                "changedFileCount")==21
                            and result.get("privatePinnedPublicPatch",{}).get(
                                "publicDeployExecuted") is False
                            and result.get("privateNonmergingPrReadiness",{}).get(
                                "status")==
                            "PRIVATE_SCOPED_NONMERGING_PR_DRAFT_VERIFIED_NO_REMOTE_WRITE"
                            and result.get("privateNonmergingPrReadiness",{}).get(
                                "changedFileCount")==21
                            and result.get("privateNonmergingPrReadiness",{}).get(
                                "publicPRCreated") is False
                            and result.get("privateNonmergingPrReadiness",{}).get(
                                "publicDeployExecuted") is False
                            and result.get("scopedPublicDraftPr",{}).get(
                                "status")==
                            "SCOPED_PUBLIC_DRAFT_PR_OPEN_UNMERGED_MAIN_UNCHANGED"
                            and result.get("scopedPublicDraftPr",{}).get(
                                "publicPullRequestDraft") is True
                            and result.get("scopedPublicDraftPr",{}).get(
                                "publicMergeExecuted") is False
                            and result.get("scopedPublicDraftPr",{}).get(
                                "publicDeployExecuted") is False
                            and result.get("scopedPublicDraftPr",{}).get(
                                "publicBaseMainPinnedSha")==
                                "eb86fe8eb94ec33f8c0c055d2423b245e5898241"
                            and result.get("independentPublicPrBrowserAcceptance",{}).get(
                                "status")==
                            "PR_EXACT_PUBLIC_GIT_BRANCH_NINE_ROUTES_ACTUAL_CHROME_PASS"
                            and result.get("independentPublicPrBrowserAcceptance",{}).get(
                                "realChromeRoutesPassed")==9
                            and result.get("independentPublicPrBrowserAcceptance",{}).get(
                                "changedFileCount")==21
                            and result.get("independentPublicPrBrowserAcceptance",{}).get(
                                "publicPrDraft") is True
                            and result.get("independentPublicPrBrowserAcceptance",{}).get(
                                "publicMergeExecuted") is False
                            and result.get("independentPublicPrBrowserAcceptance",{}).get(
                                "publicDeployExecuted") is False
                            and result.get("globalReadonlyRoadmapHandoff",{}).get(
                                "status")==
                                "POST_PR_GLOBAL_READONLY_TASKS_EXECUTED_NO_RELEASE"
                            and result.get("globalReadonlyRoadmapHandoff",{}).get(
                                "taskDispatchCount")==3
                            and result.get("globalReadonlyRoadmapHandoff",{}).get(
                                "nextTaskDispatchActuallyExecuted") is True
                            and result.get("globalReadonlyRoadmapHandoff",{}).get(
                                "quarantinedTaskIds")==[]
                            and result.get("globalReadonlyRoadmapHandoff",{}).get(
                                "publicMergeExecuted") is False
                            and result.get("globalReadonlyRoadmapHandoff",{}).get(
                                "publicDeployExecuted") is False
                            and result.get("publicPrSecurityAccessibilityPreflight",{}).get(
                                "status")==
                                "SOURCE_PINNED_PR_SECURITY_A11Y_TECHNICAL_PREFLIGHT_NO_RELEASE"
                            and result.get("publicPrSecurityAccessibilityPreflight",{}).get(
                                "technicalEvidence",{}).get("changedFileCount")==21
                            and result.get("publicPrSecurityAccessibilityPreflight",{}).get(
                                "technicalEvidence",{}).get("totalActivities")==54
                            and result.get("publicPrSecurityAccessibilityPreflight",{}).get(
                                "publicationAuthorized") is False
                            and result.get("publicPrSecurityAccessibilityPreflight",{}).get(
                                "publicMergeExecuted") is False
                            and result.get("publicPrSecurityAccessibilityPreflight",{}).get(
                                "publicDeployExecuted") is False
                            and result.get("scienceC3PostV16IndependentDispatch",{}).get(
                                "status")==
                                "V17_REAL_SCIENCE_C3_GAP_AUDITS_EXECUTED_NO_RELEASE"
                            and result.get("scienceC3PostV16IndependentDispatch",{}).get(
                                "taskDispatchActuallyExecuted") is True
                            and result.get("scienceC3PostV16IndependentDispatch",{}).get(
                                "quarantinedTaskIds")==[]
                            and result.get("scienceC3PostV16IndependentDispatch",{}).get(
                                "historicalC3")=="FAILED_LIMITED_CAMPAIGN"
                            and result.get("scienceC3PostV16IndependentDispatch",{}).get(
                                "publicationAuthorized") is False
                            and result.get("selectedTextbookSourceScientificProvenance",{}).get(
                                "status")==
                                "V18_SINGLE_TEXTBOOK_REAL_PDF_EVIDENCE_VERIFIED_SCIENCE_STILL_PARTIAL"
                            and result.get("selectedTextbookSourceScientificProvenance",{}).get(
                                "realSingleTextbookPdfOpened") is True
                            and result.get("selectedTextbookSourceScientificProvenance",{}).get(
                                "nextTaskDispatchActuallyExecuted") is True
                            and isinstance(result.get(
                                "selectedTextbookSourceScientificProvenance",{}).get(
                                "academicGapAuditReceiptSha256"),str)
                            and result.get("selectedTextbookSourceScientificProvenance",{}).get(
                                "additionalExternalPdfsRequired") is False
                            and result.get("selectedTextbookSourceScientificProvenance",{}).get(
                                "newModelCalls")==0
                            and result.get("selectedTextbookSourceScientificProvenance",{}).get(
                                "publicationAuthorized") is False
                            and result.get("existingOriginalReviewerEvidenceReuse",{}).get(
                                "status")==
                                "V19_17_EXISTING_REVIEW_PAIRS_RECONCILED_ACADEMIC_PROOFS_STILL_OPEN"
                            and result.get("existingOriginalReviewerEvidenceReuse",{}).get(
                                "nextTaskDispatchActuallyExecuted") is True
                            and result.get("existingOriginalReviewerEvidenceReuse",{}).get(
                                "reusedIndependentTwoRolePairs")==17
                            and result.get("existingOriginalReviewerEvidenceReuse",{}).get(
                                "oldUncertainRoleReplayed") is False
                            and result.get("existingOriginalReviewerEvidenceReuse",{}).get(
                                "independentAcademicProofsStillOpen")==90
                            and result.get("existingOriginalReviewerEvidenceReuse",{}).get(
                                "independentScientificAcceptanceComplete") is False
                            and result.get("existingOriginalReviewerEvidenceReuse",{}).get(
                                "newModelCalls")==0
                            and result.get("existingOriginalReviewerEvidenceReuse",{}).get(
                                "publicationAuthorized") is False
                            and result.get("historicalAcademicFiveGateAudit",{}).get(
                                "status")==
                                "V20_REAL_ORIGINAL_FIVE_GATE_ACADEMIC_AUDIT_EXECUTED_NO_RELEASE"
                            and result.get("historicalAcademicFiveGateAudit",{}).get(
                                "historicFiveGateVerifierActuallyExecuted") is True
                            and result.get("historicalAcademicFiveGateAudit",{}).get(
                                "verifiedOriginalSourceLocations")==18
                            and result.get("historicalAcademicFiveGateAudit",{}).get(
                                "verifiedActivityGateEvaluations")==90
                            and result.get("historicalAcademicFiveGateAudit",{}).get(
                                "formalAcademicPASS")==0
                            and result.get("historicalAcademicFiveGateAudit",{}).get(
                                "historicalUncertainReviewerReplayed") is False
                            and result.get("historicalAcademicFiveGateAudit",{}).get(
                                "newModelCalls")==0
                            and result.get("historicalAcademicFiveGateAudit",{}).get(
                                "publicationAuthorized") is False
                            and result.get("revisedSourceProofRebinding",{}).get(
                                "status")==
                                "V21_REVISED_18_SOURCE_LOCATIONS_REVERIFIED_SEMANTIC_PROOFS_OPEN"
                            and result.get("revisedSourceProofRebinding",{}).get(
                                "candidateSourceLocationsActuallyReverified")==18
                            and result.get("revisedSourceProofRebinding",{}).get(
                                "changedActivitiesReverified")==4
                            and result.get("revisedSourceProofRebinding",{}).get(
                                "priorModelReviewerClaimsTransferred")==0
                            and result.get("revisedSourceProofRebinding",{}).get(
                                "candidateFormalAcademicPASS")==0
                            and result.get("revisedSourceProofRebinding",{}).get(
                                "candidateDeterministicFAIL")==0
                            and result.get("revisedSourceProofRebinding",{}).get(
                                "newGeminiCalls")==0
                            and result.get("revisedSourceProofRebinding",{}).get(
                                "publicationAuthorized") is False
                            and result.get("exactRevisedReviewReconciliation",{}).get(
                                "status")==
                                "V22_13_UNCHANGED_REVIEW_PAIRS_VERIFIED_4_NEW_SCOPED_NOT_SUBMITTED"
                            and result.get("exactRevisedReviewReconciliation",{}).get(
                                "unchangedReviewerPairsReusedAsAdvisoryEvidence")==13
                            and result.get("exactRevisedReviewReconciliation",{}).get(
                                "revisedReviewerPairsThatRequireFreshAssessment")==4
                            and result.get("exactRevisedReviewReconciliation",{}).get(
                                "oldUncertainRoleReplayed") is False
                            and result.get("exactRevisedReviewReconciliation",{}).get(
                                "fourPrivateReviewInputsStaged") is True
                            and result.get("exactRevisedReviewReconciliation",{}).get(
                                "remainingIndependentAcademicProofSlots")==90
                            and result.get("exactRevisedReviewReconciliation",{}).get(
                                "formalAcademicPASS")==0
                            and result.get("exactRevisedReviewReconciliation",{}).get(
                                "newGeminiCalls")==0
                            and result.get("exactRevisedReviewReconciliation",{}).get(
                                "publicationAuthorized") is False
                            and result.get("autonomousAcademicRecovery",{}).get(
                                "status")==
                                "V24_BOUNDED_HISTORY_FIRST_ACADEMIC_DISPATCH_EXECUTED_PROOFS_OPEN"
                            and result.get("autonomousAcademicRecovery",{}).get(
                                "historicalRemedyHandlersActuallyExecuted")==6
                            and result.get("autonomousAcademicRecovery",{}).get(
                                "genuineTextbookPageRechecks")==18
                            and result.get("autonomousAcademicRecovery",{}).get(
                                "completeAcademicProofGapsStillOpen")==90
                            and result.get("autonomousAcademicRecovery",{}).get(
                                "autoRecoveryRounds")==2
                            and result.get("autonomousAcademicRecovery",{}).get(
                                "academicFixedPointReached") is True
                            and result.get("autonomousAcademicRecovery",{}).get(
                                "externalGeminiCalls")==0
                            and result.get("autonomousAcademicRecovery",{}).get(
                                "academicPASS")==0
                            and result.get("autonomousAcademicRecovery",{}).get(
                                "publicationAuthorized") is False
                            and result.get("formalSection91Physics",{}).get(
                                "status")==
                                "V25_ALL_18_REAL_SOURCE_BOUND_FORMAL_ANSWER_MODELS_VERIFIED_PARTIAL_ACADEMIC"
                            and result.get("formalSection91Physics",{}).get(
                                "independentlyReextractedTextbookPhysicsPremises")==9
                            and result.get("formalSection91Physics",{}).get(
                                "boundedFormalAnswerItemWitnesses")==68
                            and result.get("formalSection91Physics",{}).get(
                                "formalModelledActivities")==18
                            and result.get("formalSection91Physics",{}).get(
                                "academicProofGatesStillOpen")==90
                            and result.get("formalSection91Physics",{}).get(
                                "formalAcademicPASS")==0
                            and result.get("formalSection91Physics",{}).get(
                                "newGeminiCalls")==0
                            and result.get("formalSection91Physics",{}).get(
                                "externalPdfAcquisition") is False
                            and result.get("formalSection91Physics",{}).get(
                                "publicationAuthorized") is False
                            and result.get("sourceScientificSemanticTriage",{}).get(
                                "status")==
                                "V26_SOURCE_BOUND_EXPLANATION_AND_TRILINGUAL_CUE_TRIAGE_COMPLETE_NO_RELEASE"
                            and result.get("sourceScientificSemanticTriage",{}).get(
                                "activitiesChecked")==18
                            and result.get("sourceScientificSemanticTriage",{}).get(
                                "scientificLocalizedFieldsChecked")==222
                            and result.get("sourceScientificSemanticTriage",{}).get(
                                "deterministicScienceDefects")==0
                            and result.get("sourceScientificSemanticTriage",{}).get(
                                "renderedDiagramSemanticsVerified") is False
                            and result.get("sourceScientificSemanticTriage",{}).get(
                                "academicProofGatesStillOpen")==90
                            and result.get("sourceScientificSemanticTriage",{}).get(
                                "formalAcademicPASS")==0
                            and result.get("sourceScientificSemanticTriage",{}).get(
                                "newGeminiCalls")==0
                            and result.get("sourceScientificSemanticTriage",{}).get(
                                "publicationAuthorized") is False
                            and result.get("fullSemanticProofQueue",{}).get(
                                "status") ==
                                "V26_FULL_EXPLANATION_DISTRACTOR_DIAGRAM_TRILINGUAL_TASKS_QUEUED"
                            and result.get("fullSemanticProofQueue",{}).get(
                                "activityCount")==18
                            and result.get("fullSemanticProofQueue",{}).get(
                                "completeAcademicGateSlotsStillOpen")==90
                            and result.get("fullSemanticProofQueue",{}).get(
                                "independentSemanticPASS")==0
                            and result.get("fullSemanticProofQueue",{}).get(
                                "newProviderCalls")==0
                            and result.get("fullSemanticProofQueue",{}).get(
                                "externalPdfAcquisition") is False
                            and result.get("fullSemanticProofQueue",{}).get(
                                "publicationAuthorized") is False
                            and result.get("boundedSymbolicRecovery",{}).get(
                                "status")==
                                "V27_FIVE_FALSE_POSITIVE_SYMBOLIC_FLAGS_BOUNDED_NO_ACADEMIC_PASS"
                            and result.get("boundedSymbolicRecovery",{}).get(
                                "boundedParserFalsePositivesResolved")==5
                            and result.get("boundedSymbolicRecovery",{}).get(
                                "remainingAmbiguousSymbolicFields")==3
                            and result.get("boundedSymbolicRecovery",{}).get(
                                "remainingTechnicalReviewFlags")==21
                            and result.get("boundedSymbolicRecovery",{}).get(
                                "completeIndependentAcademicProofSlotsStillOpen")==90
                            and result.get("boundedSymbolicRecovery",{}).get(
                                "fullAcademicPASS")==0
                            and result.get("boundedSymbolicRecovery",{}).get(
                                "newGeminiCalls")==0
                            and result.get("boundedSymbolicRecovery",{}).get(
                                "outsideSourcePdfsRequired") is False
                            and result.get("boundedSymbolicRecovery",{}).get(
                                "publicationAuthorized") is False
                            and result.get("fiveChannelProofProducers",{}).get(
                                "status")==
                                "V28_FIVE_BOUNDED_PROOF_PRODUCERS_REAL_EXECUTION_NOT_FULL_ACADEMIC_PASS"
                            and result.get("fiveChannelProofProducers",{}).get(
                                "realSourcePageAnchors")==18
                            and result.get("fiveChannelProofProducers",{}).get(
                                "boundedScientificAnswerWitnesses")==68
                            and result.get("fiveChannelProofProducers",{}).get(
                                "falseMcqOptionsProvenAgainstFormalModels")==27
                            and result.get("fiveChannelProofProducers",{}).get(
                                "trilingualSurfacesNumericLiteralChecked")==222
                            and result.get("fiveChannelProofProducers",{}).get(
                                "actualDiagramsAbsent")==18
                            and result.get("fiveChannelProofProducers",{}).get(
                                "independentMeaningMicroproofsPending")==429
                            and result.get("fiveChannelProofProducers",{}).get(
                                "completeAcademicProofGatesStillOpen")==90
                            and result.get("fiveChannelProofProducers",{}).get(
                                "formalAcademicPASS")==0
                            and result.get("fiveChannelProofProducers",{}).get(
                                "newProviderCalls")==0
                            and result.get("fiveChannelProofProducers",{}).get(
                                "publicationAuthorized") is False
                            and result.get("autonomousDevelopmentContinuation",{}).get(
                                "status")==
                                "AUTONOMOUSLY_ADVANCED_ALL_REGISTERED_SAFE_STAGES_TO_CURRENT_BOUNDARY"
                            and result.get("autonomousDevelopmentContinuation",{}).get(
                                "stagesExecutedThisRun")>=1
                            and result.get("autonomousDevelopmentContinuation",{}).get(
                                "academicPASS")==0
                            and result.get("autonomousDevelopmentContinuation",{}).get(
                                "publicationAuthorized") is False
                            and result.get("autonomousDevelopmentContinuation",{}).get(
                                "newModelCalls")==0
                            and result.get("autonomousDevelopmentContinuation",{}).get(
                                "privateSourceVisualPilot",{}).get("status")==
                                "V29_ACTUAL_SOURCE_BOUND_PRIVATE_VECTOR_RENDERER_RECHECKED_NO_PUBLICATION"
                            and result.get("autonomousDevelopmentContinuation",{}).get(
                                "privateSourceVisualPilot",{}).get(
                                "actualSourceGroundedDraftCount")==1
                            and result.get("autonomousDevelopmentContinuation",{}).get(
                                "privateSourceVisualPilot",{}).get(
                                "actualRenderedSvgArrowsVerified")==6
                            and result.get("autonomousDevelopmentContinuation",{}).get(
                                "privateSourceVisualPilot",{}).get("fullAcademicPASS")==0
                            and result.get("autonomousDevelopmentContinuation",{}).get(
                                "privateSourceVisualPilot",{}).get(
                                "publicationAuthorized") is False
                            # BSA258/BSA259: the source-free worker must not exit
                            # success without genuinely executing BOTH new
                            # real-browser pixels and bounded MCQ semantics.
                            and result.get("autonomousDevelopmentContinuation",{}).get(
                                "stagesExecutedThisRun")>=3
                            and result.get("autonomousDevelopmentContinuation",{}).get(
                                "privateBrowserPixelPilot",{}).get("status")==
                                "V30_REAL_BROWSER_SOURCE_BOUND_THREE_LOCALE_PIXELS_PRIVATE_NO_RELEASE"
                            and result.get("autonomousDevelopmentContinuation",{}).get(
                                "privateBrowserPixelPilot",{}).get(
                                "realChromeScreenshotPixelEvidenceCount")==3
                            and result.get("autonomousDevelopmentContinuation",{}).get(
                                "privateBrowserPixelPilot",{}).get(
                                "realChromeScreenshotVelocityArrowsVerified")==6
                            and result.get("autonomousDevelopmentContinuation",{}).get(
                                "privateMcqSemanticsPilot",{}).get("status")==
                                "V31_BOUNDED_SOURCE_THREE_LOCALE_MCQ_SEMANTIC_WITNESS_PRIVATE"
                            and result.get("autonomousDevelopmentContinuation",{}).get(
                                "privateMcqSemanticsPilot",{}).get(
                                "sourceBoundVerifiedMcqOptionLocalePairs")==12
                            and result.get("autonomousDevelopmentContinuation",{}).get(
                                "privateMcqSemanticsPilot",{}).get(
                                "sourceBoundCounterexampledFalseChoices")==3
                            and result.get("autonomousDevelopmentContinuation",{}).get(
                                "privateMcqSemanticsPilot",{}).get("fullAcademicPASS")==0
                            and result.get("autonomousDevelopmentContinuation",{}).get(
                                "privateMcqSemanticsPilot",{}).get(
                                "publicationAuthorized") is False
                            # BSA260: the other eight MCQ science/locale roles
                            # must be proven and signed in the SAME normal run.
                            and result.get("autonomousDevelopmentContinuation",{}).get(
                                "stagesExecutedThisRun")>=4
                            and result.get("autonomousDevelopmentContinuation",{}).get(
                                "privateOtherMcqWitnessPilot",{}).get("status")==
                                "V32_OTHER_EIGHT_MCQS_SOURCE_BOUND_96_LOCALE_OPTION_CUES_PRIVATE"
                            and result.get("autonomousDevelopmentContinuation",{}).get(
                                "privateOtherMcqWitnessPilot",{}).get(
                                "allNineMcqLocalizedOptionRolesChecked")==108
                            and result.get("autonomousDevelopmentContinuation",{}).get(
                                "privateOtherMcqWitnessPilot",{}).get(
                                "allNineMcqFormalFalseAlternativeCounterexamples")==27
                            and result.get("autonomousDevelopmentContinuation",{}).get(
                                "privateOtherMcqWitnessPilot",{}).get("fullAcademicPASS")==0
                            and result.get("autonomousDevelopmentContinuation",{}).get(
                                "privateOtherMcqWitnessPilot",{}).get(
                                "publicationAuthorized") is False
                            # BSA262: V34 checks every interactive answer model,
                            # rejects deliberately wrong solutions and binds three
                            # localized item/prompt/explanation surfaces to source.
                            and result.get("autonomousDevelopmentContinuation",{}).get(
                                "stagesExecutedThisRun")>=5
                            and result.get("autonomousDevelopmentContinuation",{}).get(
                                "privateInteractiveMutationPilot",{}).get("status")==
                                "V34_NINE_SOURCE_BOUND_INTERACTIVE_MUTANTS_REJECTED_PRIVATE_NO_RELEASE"
                            and result.get("autonomousDevelopmentContinuation",{}).get(
                                "privateInteractiveMutationPilot",{}).get(
                                "independentlyRejectedWrongAnswerMutants")==9
                            and result.get("autonomousDevelopmentContinuation",{}).get(
                                "privateInteractiveMutationPilot",{}).get("fullAcademicPASS")==0
                            and result.get("autonomousDevelopmentContinuation",{}).get(
                                "privateInteractiveMutationPilot",{}).get("publicationAuthorized") is False
                            # BSA263: the new source-pinned V35 trilingual
                            # interactive science-role proof must also execute.
                            and result.get("autonomousDevelopmentContinuation",{}).get(
                                "stagesExecutedThisRun")>=6
                            and result.get("autonomousDevelopmentContinuation",{}).get(
                                "privateInteractiveSourceRolesPilot",{}).get("status")==
                                "V35_REAL_NINE_INTERACTIVE_TRILINGUAL_SOURCE_ROLE_CUES_PRIVATE"
                            and result.get("autonomousDevelopmentContinuation",{}).get(
                                "privateInteractiveSourceRolesPilot",{}).get(
                                "trilingualPromptRoleCuesChecked")==27
                            and result.get("autonomousDevelopmentContinuation",{}).get(
                                "privateInteractiveSourceRolesPilot",{}).get(
                                "trilingualFirstItemRoleCuesChecked")==27
                            and result.get("autonomousDevelopmentContinuation",{}).get(
                                "privateInteractiveSourceRolesPilot",{}).get("fullAcademicPASS")==0
                            and result.get("autonomousDevelopmentContinuation",{}).get(
                                "privateInteractiveSourceRolesPilot",{}).get("publicationAuthorized") is False
                            # BSA261: unrelated content/regression/readback
                            # work must execute even when one eligible lane
                            # fails. Never turn a quarantined lane into exit0.
                            and result.get("autonomousDevelopmentContinuation",{}).get(
                                "isolatedDevelopmentLanes",{}).get("status")==
                                "INDEPENDENT_SAFE_LANES_ALL_VERIFIED"
                            and result.get("autonomousDevelopmentContinuation",{}).get(
                                "isolatedDevelopmentLanes",{}).get(
                                "independentlyVerifiedLanes")==3
                            and result.get("autonomousDevelopmentContinuation",{}).get(
                                "isolatedDevelopmentLanes",{}).get(
                                "quarantinedLaneCount")==0
                            and result.get("autonomousDevelopmentContinuation",{}).get(
                                "isolatedDevelopmentLanes",{}).get("fullAcademicPASS")==0
                            and result.get("autonomousDevelopmentContinuation",{}).get(
                                "isolatedDevelopmentLanes",{}).get(
                                "publicationAuthorized") is False
                         )) else 3
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


def _run_native_browser_entrypoint(
    argv: list[str] | None = None, *, is_windows: bool | None = None,
    selenium_available: bool | None = None,
) -> int:
    """BSA246: relaunch Windows source-free work BEFORE any stateful stage.

    A second invocation under a valid Selenium venv reaches main() normally.
    Other modes retain their existing authorization and safety checks.
    """
    args = list(sys.argv[1:] if argv is None else argv)
    windows = (os.name == "nt") if is_windows is None else is_windows
    if not windows or "--source-free-advance" not in args:
        return main(args)
    import importlib.util
    import subprocess
    from app_generator.runtime.v3_native_browser_python import (
        select_source_free_browser_interpreter,
    )
    available = (
        importlib.util.find_spec("selenium") is not None
        if selenium_available is None else selenium_available
    )
    status, candidate = select_source_free_browser_interpreter(
        repo=ROOT,
        current=Path(sys.executable),
        windows=windows,
        source_free=True,
        selenium_available=available,
    )
    if status == "USE_CURRENT_PYTHON":
        return main(args)
    if status != "REEXEC_PINNED_BROWSER_PYTHON" or candidate is None:
        _print({"status":"STOP_PINNED_BROWSER_RUNTIME_MISSING",
                "publicationAuthorized":False})
        return 3
    # Probe only the exact pinned interpreter, without a download, pip
    # installation, provider request, or any project checkpoint mutation.
    try:
        probe=subprocess.run(
            [str(candidate),"-c","import selenium"],
            check=False,capture_output=True,text=True,timeout=20,
        )
        if probe.returncode != 0:
            raise RuntimeError("PINNED_BROWSER_IMPORT_UNAVAILABLE")
        result=subprocess.run(
            [str(candidate),str(Path(__file__).resolve()),*args],
            check=False,timeout=1200,
        )
        return result.returncode
    except (OSError,RuntimeError,subprocess.TimeoutExpired):
        _print({"status":"STOP_PINNED_BROWSER_RUNTIME_RELAUNCH_FAILED",
                "publicationAuthorized":False})
        return 3


if __name__=="__main__":
    raise SystemExit(_run_native_browser_entrypoint())

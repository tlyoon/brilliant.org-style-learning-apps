"""BOSLA V3 one-activity revised-content reviewer (Yoga 6 only).

Dry-run by default: exact-hash private preflight, NO Gemini request.
Actual two-context Gemini API review requires BOTH --execute and
--allow-generated-text-transfer and the existing native Yoga 6 host,
provider capacity, SDK, lock, role claim, finite budget and QA policy.
Never re-reviews the original frozen 18-activity package. No course scope
admission, release, scheduler or uncertain request replay is performed.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app_generator.runtime.v3_auto_repair import _CANDIDATE, _ACTIVITY
from app_generator.runtime.v3_course_review import plan_v3_course_review
from app_generator.runtime.v3_isolated_repair_review import (
    stage_isolated_review_slice, verify_isolated_review_slice,
)
from app_generator.runtime.v3_yoga6_recovery import (
    checked_private_root, coordinator_lock, gate_review_plan,
)
from app_generator.validation.autonomous_completion import assessment_progress
from scripts.run_v3_native_gemini_review import AUTHORITY, _load_native_config
from app_generator.runtime.v3_paid_review_authorization import (
    authorize_paid_v3_action,
)

COURSE = ROOT / "content" / "chapter-9"


def _output(value: dict) -> None:
    print(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True))


def _saved_progress(private: Path, raw: bytes, slice_sha: str) -> dict | None:
    path = (private / ("v3-generated-" + slice_sha) / "batches" /
            ("v3-assessment-" + slice_sha + ".json"))
    if path.is_symlink() or (path.exists() and
            (not path.is_file() or path.stat().st_size > 200_000)):
        raise ValueError("V3_REVISED_UNSAFE_PREVIOUS_MODEL_EVIDENCE")
    if not path.exists():
        return None
    try:
        prior = json.loads(path.read_text(encoding="utf8"))
    except (OSError, UnicodeError, ValueError):
        raise ValueError("V3_REVISED_CORRUPT_PREVIOUS_MODEL_EVIDENCE") from None
    # Trust existing V3 full-schema, exact-package, two-role validator rather
    # than guessing PASS from a private file or model-supplied status.
    return assessment_progress(raw, prior)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--private-root", type=Path)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--allow-generated-text-transfer", action="store_true")
    args = parser.parse_args(argv)
    if args.execute and not args.allow_generated_text_transfer:
        _output({"status": "STOP_GENERATED_TEXT_TRANSFER_NOT_AUTHORIZED",
                 "publicationAuthorized": False})
        return 2
    local = os.environ.get("LOCALAPPDATA")
    if not local:
        _output({"status": "STOP_LOCALAPPDATA_MISSING",
                 "publicationAuthorized": False})
        return 3
    chosen = (args.private_root if args.private_root is not None else
              Path(local) / "Microvid" / "BoslaV3ReviewYoga6")
    try:
        private = checked_private_root(chosen, localappdata=Path(local))
        stage = stage_isolated_review_slice(COURSE, private, _CANDIDATE)
        raw = verify_isolated_review_slice(
            COURSE, private, _CANDIDATE, stage["reviewSliceSha256"])
        prior = _saved_progress(private, raw, stage["reviewSliceSha256"])
        if prior and prior["activitiesAssessed"] == 1:
            _output({
                "status": "ALREADY_RECORDED_ISOLATED_REVIEW_NO_REPLAY",
                "reviewSliceSha256": stage["reviewSliceSha256"],
                "activitiesFullyModelReviewed": prior["activitiesFullyModelReviewed"],
                "modelConsensusPassActivities": prior["modelConsensusPassActivities"],
                "modelRepairRequiredActivities": prior["modelRepairRequiredActivities"],
                "modelUncertainActivities": prior["modelUncertainActivities"],
                "wholeCourseScopeAccepted": False,
                "publicationAuthorized": False,
            })
            return 0
        if not args.execute:
            _output({
                "status": "READY_FOR_SEPARATELY_AUTHORIZED_SINGLE_ACTIVITY_GEMINI_REVIEW",
                "reviewSliceSha256": stage["reviewSliceSha256"],
                "parentCandidateSha256": _CANDIDATE,
                "activityId": _ACTIVITY,
                "activityCount": 1,
                "requiredReviewerContexts": 2,
                "actualGeminiResponses": 0,
                "wholeCourseScopeAccepted": False,
                "publicationAuthorized": False,
            })
            return 0
        authorize_paid_v3_action(
            "ISOLATED_CORRECTED_SECTION_9_2_ACTIVITY",
            execute=args.execute,
            transfer=args.allow_generated_text_transfer,
            corrected_candidate_sha256=_CANDIDATE,
            max_activities=1,
            max_elapsed_seconds=900)
        # No key/model initialization until AFTER both permissions and the
        # workstation authorization. Same provider capacity and cost circuit
        # as the normal frozen Section 9.5 worker.
        from app_generator.runtime.native_workstation_guard import (
            require_authorized_native_review_host,
        )
        require_authorized_native_review_host(AUTHORITY)
        from app_generator.runtime.native_sdk_environment import (
            delegate_to_supported_sdk,
        )
        delegated = delegate_to_supported_sdk(
            ROOT, list(argv) if argv is not None else sys.argv[1:],
            entrypoint=Path(__file__))
        if delegated is not None:
            return delegated
        with coordinator_lock(private):
            plan = plan_v3_course_review(
                COURSE, ROOT, private_root=private,
                continue_independent=True)
            if gate_review_plan(plan) != "READY_FOR_SOURCE_FREE_METADATA_CHECK":
                _output({"status": "STOP_V3_PROVIDER_OR_COURSE_GATE",
                         "publicationAuthorized": False})
                return 3
            raw = verify_isolated_review_slice(
                COURSE, private, _CANDIDATE, stage["reviewSliceSha256"])
            prior = _saved_progress(private, raw, stage["reviewSliceSha256"])
            if prior is not None:
                _output({"status": "STOP_PRIOR_REVISED_MODEL_REVIEW_NO_REPLAY",
                         "publicationAuthorized": False})
                return 3
            from app_generator.gemini.v3_native_api_reviewers import (
                V3NativeGeminiApiSessions,
            )
            from app_generator.runtime.v3_authorized_review import (
                advance_v3_generated_text,
            )
            config = _load_native_config()
            from app_generator.runtime.v3_gemini_diagnostics import (
                diagnose_model_metadata,
            )
            # Recycle the ordinary Yoga 6 provider-capacity remedy rather
            # than resetting to candidate key #0 for a revised activity.
            previous_failures = (plan.get("providerCapacity") or {}).get(
                "serverErrorActivitiesHistorical")
            if type(previous_failures) is not int or not 0 <= previous_failures < 2:
                raise ValueError("V3_REVISED_INVALID_PROVIDER_RECOVERY_BUDGET")
            diagnostic = diagnose_model_metadata(
                config, preferred_offset=previous_failures)
            if diagnostic.get("status") != "READY_SOURCE_FREE_ONLY":
                _output({"status": "STOP_REVISED_PROVIDER_DIAGNOSTIC",
                         "publicationAuthorized": False})
                return 3
            selected_key = diagnostic.get("selectedCandidateIndex")
            if type(selected_key) is not int or not 0 <= selected_key < 8:
                raise ValueError("V3_REVISED_INVALID_SELECTED_CREDENTIAL_INDEX")
            # One bounded activity / two independent reviewer contexts only.
            # The ordinary engine atomically owns all role claims and
            # independently records ambiguous operations without replay.
            with V3NativeGeminiApiSessions(
                    config, operation_authorized=True,
                    generated_content_transfer_allowed=True,
                    candidate_offset=selected_key) as sessions:
                pair = sessions.open_pair(_ACTIVITY)
                report = advance_v3_generated_text(
                    raw, pair, private_root=private,
                    generated_content_transfer_allowed=True,
                    max_activities=1)
            _output({
                "status": "ISOLATED_MODEL_REVIEW_RECORDED_NOT_COURSE_ACCEPTANCE",
                "reviewSliceSha256": stage["reviewSliceSha256"],
                "activitiesAssessed": report["activitiesAssessed"],
                "activitiesFullyModelReviewed":
                    report["activitiesFullyModelReviewed"],
                "modelConsensusPassActivities":
                    report["modelConsensusPassActivities"],
                "modelRepairRequiredActivities":
                    report["modelRepairRequiredActivities"],
                "modelUncertainActivities": report["modelUncertainActivities"],
                "wholeCourseScopeAccepted": False,
                "publicationAuthorized": False,
            })
            return 0
    except Exception as exc:
        # No raw exception message (it may contain private prompt/provider
        # content). The exact reason remains in private local diagnostics.
        _output({"status": "STOP_ISOLATED_REVIEW_" + type(exc).__name__,
                 "publicationAuthorized": False})
        return 3


if __name__ == "__main__":
    raise SystemExit(main())

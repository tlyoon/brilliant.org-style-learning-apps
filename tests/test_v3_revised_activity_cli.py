"""No-paid-call CLI safeguards for isolated versioned correction review."""
from __future__ import annotations

from contextlib import redirect_stdout
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from scripts import run_v3_revised_activity_review as target


class RevisedActivityCliTests(unittest.TestCase):
    def setUp(self):
        t = tempfile.TemporaryDirectory()
        self.addCleanup(t.cleanup)
        self.root = Path(t.name)
        self.localappdata = self.root / "Local"
        self.private = self.localappdata / "Microvid" / "BoslaV3ReviewYoga6"
        self.private.mkdir(parents=True)
        self.original_read = target._saved_progress
        stage = patch.object(target, "stage_isolated_review_slice",
                             return_value={"reviewSliceSha256": "1"*64})
        verify = patch.object(target, "verify_isolated_review_slice",
                              return_value=b'{"activities": []}')
        prior = patch.object(target, "_saved_progress", return_value=None)
        for handler in (stage, verify, prior):
            handler.start()
            self.addCleanup(handler.stop)
        self.addCleanup(patch.stopall)

    def run_main(self, argv):
        out = io.StringIO()
        with patch.dict(os.environ, {"LOCALAPPDATA": str(self.localappdata)}):
            with redirect_stdout(out):
                status = target.main(argv)
        return status, json.loads(out.getvalue())

    def test_dry_run_never_opens_sdk_or_review_sessions(self):
        with patch("app_generator.runtime.native_workstation_guard.require_authorized_native_review_host",
                   side_effect=AssertionError("dry run should not open provider")):
            code, report = self.run_main([])
        self.assertEqual(code, 0)
        self.assertEqual(
            report["status"],
            "READY_FOR_SEPARATELY_AUTHORIZED_SINGLE_ACTIVITY_GEMINI_REVIEW")
        self.assertEqual(report["activityCount"], 1)
        self.assertEqual(report["requiredReviewerContexts"], 2)
        self.assertEqual(report["actualGeminiResponses"], 0)
        self.assertFalse(report["publicationAuthorized"])

    def test_paid_execution_without_explicit_transfer_flag_never_stages(self):
        with patch.object(target, "stage_isolated_review_slice",
                          side_effect=AssertionError("unauthorized stage called")):
            code, report = self.run_main(["--execute"])
        self.assertEqual(code, 2)
        self.assertEqual(report["status"],
                         "STOP_GENERATED_TEXT_TRANSFER_NOT_AUTHORIZED")

    def test_already_recorded_verdict_is_not_replayed(self):
        with patch.object(target, "_saved_progress", return_value={
                "activitiesAssessed": 1,
                "activitiesFullyModelReviewed": 1,
                "modelConsensusPassActivities": 1,
                "modelRepairRequiredActivities": 0,
                "modelUncertainActivities": 0}):
            with patch("app_generator.runtime.native_workstation_guard.require_authorized_native_review_host",
                       side_effect=AssertionError("no new paid call")):
                code, report = self.run_main(
                    ["--execute", "--allow-generated-text-transfer"])
        self.assertEqual(code, 0)
        self.assertEqual(report["status"],
                         "ALREADY_RECORDED_ISOLATED_REVIEW_NO_REPLAY")
        self.assertFalse(report["wholeCourseScopeAccepted"])

    def test_host_guard_runs_before_sdk_or_model(self):
        with patch("app_generator.runtime.native_workstation_guard.require_authorized_native_review_host",
                   side_effect=ValueError("wrong workstation")):
            with patch.object(target, "_load_native_config",
                              side_effect=AssertionError("SDK/credentials accessed")):
                code, report = self.run_main(
                    ["--execute", "--allow-generated-text-transfer"])
        self.assertEqual(code, 3)
        self.assertEqual(report["status"], "STOP_ISOLATED_REVIEW_ValueError")
        self.assertNotIn("wrong workstation", json.dumps(report))
        self.assertFalse(report["publicationAuthorized"])

    def test_corrupt_prior_evidence_stops_not_fallback_to_fresh_model(self):
        directory = self.private / ("v3-generated-"+"1"*64) / "batches"
        directory.mkdir(parents=True)
        receipt = directory / ("v3-assessment-"+"1"*64+".json")
        receipt.write_text("{forged}", encoding="utf8")
        # Use the real checkpoint reader. A malformed receipt must not cause
        # the CLI to begin a new request under the same role identity.
        with patch.object(target, "_saved_progress", side_effect=self.original_read):
            with patch("app_generator.runtime.native_workstation_guard.require_authorized_native_review_host",
                       side_effect=AssertionError("no paid call")):
                code, report = self.run_main(
                    ["--execute", "--allow-generated-text-transfer"])
        self.assertEqual(code, 3)
        self.assertEqual(report["status"], "STOP_ISOLATED_REVIEW_ValueError")
        self.assertFalse(report["publicationAuthorized"])


    def _authorized_mock_preflight(self):
        from contextlib import ExitStack
        stack = ExitStack()
        self.addCleanup(stack.close)
        stack.enter_context(patch(
            "app_generator.runtime.native_workstation_guard.require_authorized_native_review_host"))
        stack.enter_context(patch(
            "app_generator.runtime.native_sdk_environment.delegate_to_supported_sdk",
            return_value=None))
        stack.enter_context(patch.object(
            target, "plan_v3_course_review",
            return_value={"dispatchStatus": "READY_FOR_AUTHORIZED_REVIEW_SESSIONS",
                          "providerCapacity": {"serverErrorActivitiesHistorical": 1}}))
        stack.enter_context(patch.object(
            target, "gate_review_plan",
            return_value="READY_FOR_SOURCE_FREE_METADATA_CHECK"))
        stack.enter_context(patch.object(
            target, "_load_native_config", return_value=object()))
        return stack

    def test_revised_provider_diagnostic_failure_stops_without_model(self):
        self._authorized_mock_preflight()
        with patch("app_generator.runtime.v3_gemini_diagnostics.diagnose_model_metadata",
                   return_value={"status": "STOP_PROVIDER_SERVER_ERROR"}):
            with patch("app_generator.gemini.v3_native_api_reviewers.V3NativeGeminiApiSessions",
                       side_effect=AssertionError("failed metadata cannot call model")):
                code, report = self.run_main(
                    ["--execute", "--allow-generated-text-transfer"])
        self.assertEqual(code, 3)
        self.assertEqual(report["status"], "STOP_REVISED_PROVIDER_DIAGNOSTIC")
        self.assertFalse(report["publicationAuthorized"])

    def test_revised_key_selection_recycles_existing_capacity_strategy(self):
        self._authorized_mock_preflight()
        used = []
        class SyntheticNativeSessions:
            def __init__(self, config, **kw):
                used.append(kw)
            def __enter__(self):
                return self
            def __exit__(self, *args):
                pass
            def open_pair(self, activity_id):
                used.append({"selectedActivity": activity_id})
                return ("SYNTHETIC-physics", "SYNTHETIC-semantics")
        with patch("app_generator.runtime.v3_gemini_diagnostics.diagnose_model_metadata",
                   return_value={"status": "READY_SOURCE_FREE_ONLY",
                                 "selectedCandidateIndex": 3}) as diagnostic:
            with patch("app_generator.gemini.v3_native_api_reviewers.V3NativeGeminiApiSessions",
                       SyntheticNativeSessions):
                with patch("app_generator.runtime.v3_authorized_review.advance_v3_generated_text",
                           return_value={
                               "activitiesAssessed": 1,
                               "activitiesFullyModelReviewed": 1,
                               "modelConsensusPassActivities": 1,
                               "modelRepairRequiredActivities": 0,
                               "modelUncertainActivities": 0,
                           }) as synthetic_review:
                    code, report = self.run_main(
                        ["--execute", "--allow-generated-text-transfer"])
        self.assertEqual(code, 0)
        self.assertEqual(report["status"],
                         "ISOLATED_MODEL_REVIEW_RECORDED_NOT_COURSE_ACCEPTANCE")
        diagnostic.assert_called_once()
        self.assertEqual(diagnostic.call_args.kwargs["preferred_offset"], 1)
        self.assertEqual(used[0]["candidate_offset"], 3)
        self.assertEqual(used[1]["selectedActivity"], "act-int-iso-05")
        self.assertEqual(synthetic_review.call_args.kwargs["max_activities"], 1)
        self.assertFalse(report["publicationAuthorized"])
        self.assertFalse(report["wholeCourseScopeAccepted"])

if __name__ == "__main__":
    unittest.main()

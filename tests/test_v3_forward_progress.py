"""Source-free adversarial tests for automatic forward progression without cron.

Simulate actual BSA-166/168 ServerError ambiguity, BSA-171 Batch identity
uncertainty, Section 9.2 V3 language FAIL, process crashes, stale checkpoint,
quota, cost permissions and genuine restart conditions.
"""
from __future__ import annotations

from contextlib import redirect_stdout
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from app_generator.runtime.v3_forward_progress import (
    advance_until_boundary, classify, read_checkpoint,
    save_checkpoint, snapshot,
)
from app_generator.runtime.v3_yoga6_recovery import coordinator_lock


class FakeCourse:
    def __init__(self):
        self.assessed = 0
        self.passed = 0
        self.repair = 0
        self.uncertain = 0
        self.status = "READY_FOR_AUTHORIZED_REVIEW_SESSIONS"
        self.failures = 0
        self.package_salt = ""
        self.reads = 0
        self.next_override = None
        self.quarantined = []

    def plan(self):
        self.reads += 1
        roster = [
            {"section": f"section-9-{i}",
             "packageSha256": f"{i}{self.package_salt}".ljust(64, "a"),
             "activitiesTotal": 18}
            for i in range(1, 7)
        ]
        # A prior section can be quarantined. Only an eligible new section
        # is advanced; the aggregate history remains unchanged.
        if self.assessed == 108:
            self.status = "PENDING_DETERMINISTIC_RELEASE_EVIDENCE"
        section = f"section-9-{min(1 + self.assessed // 18, 6)}"
        return {
            "sectionProgress": roster,
            "activitiesTotal": 108,
            "activitiesAssessedRows": self.assessed,
            "activitiesFullyModelReviewed": self.assessed - self.uncertain,
            "modelConsensusPassActivities": self.passed,
            "modelRepairRequiredActivities": self.repair,
            "modelUncertainActivities": self.uncertain,
            "dispatchStatus": self.status,
            "nextSection": (self.next_override or section) if self.status ==
                            "READY_FOR_AUTHORIZED_REVIEW_SESSIONS" else None,
            "quarantinedSections": list(self.quarantined),
            "providerCapacity": {"serverErrorActivitiesHistorical": self.failures},
            "publicationAuthorized": False,
        }

    def pass_one(self):
        self.assessed += 1
        self.passed += 1
        return 0


class ForwardControllerTests(unittest.TestCase):
    def setUp(self):
        t = tempfile.TemporaryDirectory()
        self.addCleanup(t.cleanup)
        self.root = Path(t.name) / "Microvid" / "BoslaV3ReviewYoga6"
        self.course = FakeCourse()

    def run_auto(self, runner=None, *, max_activities=4, **kwargs):
        return advance_until_boundary(
            self.root, self.course.plan,
            runner if runner is not None else self.course.pass_one,
            operation_authorized=True, transfer_authorized=True,
            max_activities=max_activities, **kwargs)

    def test_immediately_dispatches_four_next_activities_without_scheduler(self):
        observed = []
        def run():
            observed.append(self.course.assessed)
            return self.course.pass_one()
        report = self.run_auto(run)
        self.assertEqual(observed, [0, 1, 2, 3])
        self.assertEqual(report["advancedActivitiesThisInvocation"], 4)
        self.assertEqual(report["activitiesAssessedRows"], 4)
        self.assertEqual(report["modelConsensusPassActivities"], 4)
        self.assertFalse(report["publicationAuthorized"])
        self.assertEqual("STOP_FORWARD_ACTIVITY_BUDGET_REACHED", report["status"])
        self.assertEqual("STOPPED", read_checkpoint(self.root)["phase"])

    def test_fresh_authorized_invocation_resumes_after_bounded_stop(self):
        self.run_auto(max_activities=4)
        report = self.run_auto(max_activities=2)
        self.assertEqual(6, report["activitiesAssessedRows"])
        self.assertEqual(2, report["advancedActivitiesThisInvocation"])
        self.assertEqual(6, read_checkpoint(self.root)["last"]["activitiesAssessedRows"])

    def test_no_auth_no_paid_calls_no_persistence(self):
        calls = []
        result = advance_until_boundary(
            self.root, self.course.plan, lambda: calls.append("bad"),
            operation_authorized=False, transfer_authorized=True)
        self.assertEqual(result["status"], "STOP_PAID_OR_TRANSFER_AUTHORIZATION_MISSING")
        self.assertEqual(calls, [])
        self.assertIsNone(read_checkpoint(self.root))
        result = advance_until_boundary(
            self.root, self.course.plan, lambda: calls.append("bad"),
            operation_authorized=True, transfer_authorized=False)
        self.assertEqual(result["status"], "STOP_PAID_OR_TRANSFER_AUTHORIZATION_MISSING")
        self.assertEqual(calls, [])

    def test_crash_after_pre_call_without_evidence_stops_and_never_resends(self):
        state = snapshot(self.course.plan())
        save_checkpoint(self.root, "PRE_CALL", state, state,
                        "PREPARED_SINGLE_ELIGIBLE_ACTIVITY")
        calls = []
        first = self.run_auto(lambda: calls.append(1))
        second = self.run_auto(lambda: calls.append(2))
        self.assertEqual(first["status"], "STOP_UNRECONCILED_PREVIOUS_CALL_NO_REPLAY")
        self.assertEqual(second["status"], first["status"])
        self.assertEqual(calls, [])
        self.assertEqual("PRE_CALL", read_checkpoint(self.root)["phase"])

    def test_crash_after_real_model_aggregate_recovers_then_advances(self):
        state = snapshot(self.course.plan())
        save_checkpoint(self.root, "PRE_CALL", state, state,
                        "PREPARED_SINGLE_ELIGIBLE_ACTIVITY")
        self.course.pass_one()  # genuinely persisted reviewer result
        completed = self.run_auto(max_activities=2)
        self.assertEqual(completed["activitiesAssessedRows"], 3)
        self.assertEqual(completed["advancedActivitiesThisInvocation"], 2)
        self.assertEqual(completed["modelConsensusPassActivities"], 3)
        self.assertEqual("STOPPED", read_checkpoint(self.root)["phase"])

    def test_worker_error_without_durable_progress_cannot_retry(self):
        calls = []
        def broken():
            calls.append("before possible provider submission")
            raise TimeoutError("secret API error and possibly sent request")
        first = self.run_auto(broken)
        self.assertEqual(first["status"], "STOP_UNRECONCILED_WORKER_EXCEPTION_NO_REPLAY")
        self.assertEqual(calls, ["before possible provider submission"])
        second = self.run_auto(broken)
        self.assertEqual(second["status"], "STOP_UNRECONCILED_PREVIOUS_CALL_NO_REPLAY")
        self.assertEqual(len(calls), 1)
        self.assertNotIn("secret", json.dumps(first))

    def test_normal_return_without_progress_is_no_replay_stop(self):
        calls = []
        first = self.run_auto(lambda: calls.append(1) or 0)
        self.assertEqual(first["status"], "STOP_NO_VERIFIED_PROGRESS_NO_REPLAY")
        second = self.run_auto(lambda: calls.append(2) or 0)
        self.assertEqual(second["status"], "STOP_UNRECONCILED_PREVIOUS_CALL_NO_REPLAY")
        self.assertEqual(calls, [1])

    def test_genuine_trilingual_failure_continues_an_independent_next_stage(self):
        # Simulates Section 9.2 activity 14. No fake academic promotion.
        def language_fail():
            self.course.assessed += 1
            self.course.repair += 1
            return 0
        def next_pass():
            self.course.assessed += 1
            self.course.passed += 1
            return 0
        calls = [language_fail, next_pass]
        result = self.run_auto(lambda: calls.pop(0)(), max_activities=2)
        self.assertEqual(result["activitiesAssessedRows"], 2)
        self.assertEqual(result["modelConsensusPassActivities"], 1)
        self.assertEqual(result["modelRepairRequiredActivities"], 1)
        self.assertFalse(result["publicationAuthorized"])
        self.assertEqual(calls, [])

    def test_genuine_servererror_uncertain_is_preserved_not_retried(self):
        def server_error():
            self.course.assessed += 1
            self.course.uncertain += 1
            return 3
        first = [server_error, self.course.pass_one]
        report = self.run_auto(lambda: first.pop(0)(), max_activities=2)
        self.assertEqual(report["activitiesAssessedRows"], 2)
        self.assertEqual(report["modelUncertainActivities"], 1)
        self.assertEqual(report["modelConsensusPassActivities"], 1)
        self.assertFalse(report["publicationAuthorized"])

    def test_circuit_and_quota_stop_before_provider(self):
        self.course.failures = 2
        calls = []
        report = self.run_auto(lambda: calls.append(1))
        self.assertEqual(report["status"], "STOP_PROVIDER_RECOVERY_BUDGET")
        self.assertEqual(calls, [])
        self.assertEqual("STOPPED", read_checkpoint(self.root)["phase"])

    def test_ineligible_release_gate_never_publishes(self):
        self.course.status = "PENDING_DETERMINISTIC_RELEASE_EVIDENCE"
        calls = []
        report = self.run_auto(lambda: calls.append(1))
        self.assertEqual(report["status"], "STOP_DETERMINISTIC_RELEASE_QA_PENDING")
        self.assertFalse(report["publicationAuthorized"])
        self.assertEqual(calls, [])

    def test_versioned_repair_stops_no_fake_model_pass(self):
        self.course.status = "STOP_VERSIONED_CONTENT_REPAIR_REQUIRED"
        report = self.run_auto(lambda: self.fail("provider invoked"))
        self.assertEqual(report["status"], "STOP_VERSIONED_CONTENT_REPAIR_REQUIRED")

    def test_roster_changed_across_restart_fails_closed(self):
        self.run_auto(max_activities=1)
        self.course.package_salt = "b"
        with self.assertRaisesRegex(ValueError, "ROSTER_CHANGED"):
            self.run_auto(max_activities=1)

    def test_tampered_checkpoint_fails_before_any_paid_call(self):
        self.run_auto(max_activities=1)
        target = self.root / "v3-forward-progress-checkpoint.json"
        data = json.loads(target.read_text(encoding="utf-8"))
        data["last"]["activitiesAssessedRows"] = 108
        target.write_text(json.dumps(data), encoding="utf-8")
        calls = []
        with self.assertRaisesRegex(ValueError, "INTEGRITY_MISMATCH"):
            self.run_auto(lambda: calls.append(1))
        self.assertEqual(calls, [])

    def test_existing_os_lock_prevents_concurrent_orchestrators(self):
        with coordinator_lock(self.root / "forward-driver"):
            with self.assertRaisesRegex(RuntimeError, "ALREADY_RUNNING"):
                self.run_auto()

    def test_finite_forward_budget_rejects_unbounded_calls(self):
        for n in (0, 7, -1, 1.5):
            with self.subTest(value=n), self.assertRaisesRegex(
                    ValueError, "INVALID_BOUNDED_BUDGET"):
                self.run_auto(max_activities=n)
        self.assertIsNone(read_checkpoint(self.root))

    def test_elapsed_bound_is_honored_between_operations(self):
        clock = iter([0, 0, 31])
        report = self.run_auto(monotonic=lambda: next(clock),
                               max_elapsed_seconds=30)
        self.assertEqual("STOP_FORWARD_ELAPSED_BOUND", report["status"])
        self.assertEqual(1, report["advancedActivitiesThisInvocation"])

    def test_unknown_dispatch_never_becomes_eligible(self):
        self.course.status = "UNKNOWN_UNTRUSTED_PROVIDER"
        report = self.run_auto(lambda: self.fail("untrusted dispatch sent"))
        self.assertEqual(report["status"], "STOP_UNCLASSIFIED_DISPATCH")

    def test_script_cli_requires_explicit_paid_and_transfer_flags(self):
        from scripts import run_v3_yoga6_recovery_worker as worker
        output = io.StringIO()
        with redirect_stdout(output):
            code = worker.main(["--auto-advance"])
        self.assertEqual(code, 2)
        self.assertEqual(
            json.loads(output.getvalue())["status"],
            "STOP_FORWARD_EXECUTION_AUTHORIZATION_REQUIRED")

    def test_script_dispatches_controller_from_normal_entrypoint(self):
        from scripts import run_v3_yoga6_recovery_worker as worker
        output = io.StringIO()
        with patch.dict(os.environ, {"LOCALAPPDATA": str(self.root.parent.parent)}), \
             patch.object(worker, "plan_v3_course_review",
                          return_value={
                              "nextSection": "section-9-5",
                              "dispatchStatus": "READY_FOR_AUTHORIZED_REVIEW_SESSIONS",
                              "quarantinedSections": [],
                              "publicationAuthorized": False,
                          }), \
             patch.object(worker, "require_authorized_native_review_host"), \
             patch.object(worker, "advance_source_free_until_boundary",
                          return_value={"status": "SOURCE_FREE_BOUNDARIES_STAGED",
                                        "publicationAuthorized": False,
                                        "paidGeminiCalls": 0}) as offline, \
             patch("app_generator.runtime.v3_forward_progress.advance_until_boundary",
                   return_value={"status": "STOP_FORWARD_ACTIVITY_BUDGET_REACHED",
                                 "publicationAuthorized": False}) as controller, \
             redirect_stdout(output):
            code = worker.main([
                "--auto-advance", "--execute", "--allow-generated-text-transfer",
                "--max-forward-activities", "3",
                "--private-root", str(self.root)])
        self.assertEqual(code, 0)
        # BSA-190: this is intentionally a mocked READY plan without six
        # real packages, so the independent source-free controller must be
        # stubbed, not asked to invent historical source or model evidence.
        # BSA-189's separate real-shaped paid-denial test executes offline.
        offline.assert_called_once_with(worker.COURSE, worker.ROOT, self.root)
        self.assertEqual(controller.call_count, 1)
        self.assertEqual(controller.call_args.kwargs["max_activities"], 3)
        self.assertTrue(controller.call_args.kwargs["operation_authorized"])
        self.assertTrue(controller.call_args.kwargs["transfer_authorized"])
        self.assertTrue(callable(
            controller.call_args.kwargs["source_free_recovery"]))
        self.assertFalse(json.loads(output.getvalue())["publicationAuthorized"])


    def test_six_section_108_activity_restart_stress_reaches_qa_gate(self):
        # A new, explicit finite budget is needed for each resumed invocation.
        # The original immutable model results are the only progress source.
        for round_index in range(18):
            report = self.run_auto(max_activities=6)
            self.assertEqual(report["activitiesAssessedRows"],
                             6 * (round_index + 1))
            self.assertEqual(report["modelConsensusPassActivities"],
                             6 * (round_index + 1))
            self.assertFalse(report["publicationAuthorized"])
            if round_index == 17:
                self.assertEqual(report["status"],
                                 "STOP_DETERMINISTIC_RELEASE_QA_PENDING")
        calls = []
        final = self.run_auto(lambda: calls.append("should-not-call"), max_activities=6)
        self.assertEqual(calls, [])
        self.assertEqual(final["status"],
                         "STOP_DETERMINISTIC_RELEASE_QA_PENDING")
        self.assertEqual(final["activitiesAssessedRows"], 108)
        self.assertFalse(final["publicationAuthorized"])

    def test_retired_schedule_cannot_be_reinstalled_by_legacy_script(self):
        installer = (Path(__file__).resolve().parents[1] / "scripts" /
                     "install_yoga6_v3_recovery.ps1")
        text = installer.read_text(encoding="utf-8")
        self.assertIn("BOSLA_V3_SCHEDULING_RETIRED_USE_AUTO_ADVANCE", text)
        self.assertNotIn("Register-ScheduledTask", text)
        self.assertNotIn("New-ScheduledTaskTrigger", text)
        self.assertIn("Unregister-ScheduledTask", text)

    def test_uncertain_orphan_claim_quarantines_section_and_advances_next(self):
        # Actual BSA-162/165/166 failure pattern: request might have been
        # accepted, no aggregate yet, but the old section is quarantined.
        def ambiguous():
            self.course.quarantined = ["section-9-1"]
            self.course.next_override = "section-9-2"
            return 3
        calls = [ambiguous, self.course.pass_one]
        outcome = self.run_auto(lambda: calls.pop(0)(), max_activities=2)
        self.assertEqual(outcome["advancedActivitiesThisInvocation"], 1)
        self.assertEqual(outcome["workerInvocationsThisRun"], 2)
        self.assertEqual(outcome["activitiesAssessedRows"], 1)
        self.assertEqual(outcome["modelConsensusPassActivities"], 1)
        self.assertEqual(calls, [])
        self.assertFalse(outcome["publicationAuthorized"])

    def test_crash_resume_can_skip_only_proven_quarantined_section(self):
        initial = snapshot(self.course.plan())
        save_checkpoint(self.root, "PRE_CALL", initial, initial,
                        "PREPARED_SINGLE_ELIGIBLE_ACTIVITY")
        self.course.next_override = "section-9-2"
        self.course.quarantined = ["section-9-1"]
        outcome = self.run_auto(max_activities=1)
        self.assertEqual(outcome["activitiesAssessedRows"], 1)
        self.assertEqual(outcome["advancedActivitiesThisInvocation"], 1)

    def test_next_section_change_without_quarantine_never_retries(self):
        initial = snapshot(self.course.plan())
        save_checkpoint(self.root, "PRE_CALL", initial, initial,
                        "PREPARED_SINGLE_ELIGIBLE_ACTIVITY")
        self.course.next_override = "section-9-2"
        calls = []
        outcome = self.run_auto(lambda: calls.append("unsafe"))
        self.assertEqual(calls, [])
        self.assertEqual(outcome["status"],
                         "STOP_UNRECONCILED_PREVIOUS_CALL_NO_REPLAY")

    def test_symlink_driver_folder_fails_before_worker(self):
        if not hasattr(os, "symlink"):
            self.skipTest("OS does not support symlinks")
        self.root.mkdir(parents=True)
        redirect = self.root / "other-folder"
        redirect.mkdir()
        try:
            (self.root / "forward-driver").symlink_to(redirect, target_is_directory=True)
        except (OSError, NotImplementedError):
            self.skipTest("Creating symlinks not permitted")
        with self.assertRaisesRegex(ValueError, "UNSAFE_DRIVER_LOCK"):
            self.run_auto(lambda: self.fail("unexpected dispatch"))

    def test_source_free_repair_stages_then_immediately_reviews_eligible_section(self):
        sequence = []
        def repair(plan):
            sequence.append(("repair", plan["activitiesAssessedRows"]))
            return {
                "repairStatus": "PRIVATE_REPAIR_STAGED_PENDING_TWO_GEMINI_REVIEWS",
                "repairStaged": True, "publicationAuthorized": False,
            }
        def review():
            sequence.append(("review", self.course.assessed))
            return self.course.pass_one()
        result = self.run_auto(
            review, max_activities=3, source_free_recovery=repair)
        self.assertEqual(sequence,
                         [("repair", 0), ("review", 0),
                          ("review", 1), ("review", 2)])
        self.assertEqual(result["modelConsensusPassActivities"], 3)
        self.assertEqual(result["advancedActivitiesThisInvocation"], 3)
        self.assertFalse(result["publicationAuthorized"])

    def test_source_free_repair_is_never_executed_without_both_permissions(self):
        calls = []
        report = advance_until_boundary(
            self.root, self.course.plan, lambda: calls.append("paid"),
            source_free_recovery=lambda p: calls.append("repair"),
            operation_authorized=False, transfer_authorized=True)
        self.assertEqual(report["status"],
                         "STOP_PAID_OR_TRANSFER_AUTHORIZATION_MISSING")
        self.assertEqual(calls, [])
        self.assertIsNone(read_checkpoint(self.root))

    def test_unknown_or_promoted_repair_receipt_blocks_before_any_model_call(self):
        for invalid in (
            {"repairStaged": True, "repairStatus": "REPAIR_APPROVED"},
            {"repairStaged": True,
             "repairStatus": "PRIVATE_REPAIR_STAGED_PENDING_TWO_GEMINI_REVIEWS",
             "publicationAuthorized": True},
        ):
            with self.subTest(invalid=invalid):
                with self.assertRaisesRegex(ValueError, "RECOVERY_OUTCOME|REPAIR_STATE"):
                    self.run_auto(source_free_recovery=lambda plan: invalid)
                self.assertIsNone(read_checkpoint(self.root))
                self.assertEqual(self.course.assessed, 0)

    def test_source_free_recovery_after_crash_stays_no_replay(self):
        calls = []
        def repair(plan):
            calls.append("repair")
            return {
                "repairStaged": True,
                "repairStatus": "PRIVATE_REPAIR_STAGED_PENDING_TWO_GEMINI_REVIEWS",
            }
        def unknown_exit():
            calls.append("worker")
            raise TimeoutError("provider acceptance unknown")
        result = self.run_auto(
            unknown_exit, source_free_recovery=repair, max_activities=2)
        self.assertEqual(
            result["status"], "STOP_UNRECONCILED_WORKER_EXCEPTION_NO_REPLAY")
        second = self.run_auto(
            unknown_exit, source_free_recovery=repair, max_activities=2)
        self.assertEqual(
            second["status"], "STOP_UNRECONCILED_PREVIOUS_CALL_NO_REPLAY")
        self.assertEqual(calls, ["repair", "worker"])
        self.assertEqual(read_checkpoint(self.root)["phase"], "PRE_CALL")

if __name__ == "__main__":
    unittest.main()

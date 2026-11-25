"""V6 executable recovery registry checks: real normal-path source-free policy.

Historical signatures are policy data, never instructions to import or eval.
All tested provider outcomes are synthetic; no model requests are made.
"""
from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from app_generator.runtime.v3_recovery_policy import (
    _DEFAULT_REGISTRY, _registered, apply_registered_recovery,
    read_policy_state, persist_policy_state,
)

_CANDIDATE = "49a7f18c7cc2b7c00e0b6b23838cca1ed7fe52262384e0c26bbc8360fa3e9174"
_ARCHIVE = "cfe7bab820aa01ce71bd7a6a334c742101ebd10d8895cccd5f05d599030f971c"
_TRIGGER = "BSA-20261116-173"
_REMEDY = "BSA-20261116-174"
_REFS = {_TRIGGER, _REMEDY, "BSA-20261116-175", "BSA-20261116-176"}


def good_result():
    return {
        "repairStaged": True,
        "repairStatus": "PRIVATE_REPAIR_STAGED_PENDING_TWO_GEMINI_REVIEWS",
        "archivalParentSha256": _ARCHIVE,
        "candidateSha256": _CANDIDATE,
        "publicationAuthorized": False,
    }


class RegistryRecoveryV6Tests(unittest.TestCase):
    def setUp(self):
        t = tempfile.TemporaryDirectory()
        self.addCleanup(t.cleanup)
        self.root = Path(t.name)
        self.private = self.root / "Microvid" / "BoslaV3ReviewYoga6"
        self.course = self.root / "course"
        self.course.mkdir()
        self.plan = {
            "scriptQuarantinedSections": {"section-9-2": 2},
            "dispatchStatus": "READY_FOR_AUTHORIZED_REVIEW_SESSIONS",
            "nextSection": "section-9-5",
            "publicationAuthorized": False,
        }
        full = json.loads(_DEFAULT_REGISTRY.read_text(encoding="utf8"))
        self.registry = self.root / "recurrence-registry.json"
        full["incidents"] = [x for x in full["incidents"] if x["id"] in _REFS]
        self.data = full
        self.write_registry()
        # Tests here isolate registry selection; independent exact-candidate
        # source-free handoff logic has its own adversarial module.
        handoff = patch(
            "app_generator.runtime.v3_recovery_policy.stage_changed_activity_review_handoff",
            return_value={
                "handoffStatus": "PENDING_AUTHORIZED_TWO_GEMINI_REVIEW",
                "handoffSha256": "a"*64,
                "actualGeminiResponses": 0,
                "wholeCourseScopeAccepted": False,
                "publicationAuthorized": False,
            })
        handoff.start()
        self.addCleanup(handoff.stop)
        slice_preflight = patch(
            "app_generator.runtime.v3_recovery_policy.stage_isolated_review_slice",
            return_value={
                "status": "PENDING_AUTHORIZED_ISOLATED_TWO_GEMINI_REVIEW",
                "reviewSliceSha256": "b"*64,
                "activityCount": 1,
                "reviewerCountRequired": 2,
                "actualGeminiResponses": 0,
                "wholeCourseScopeAccepted": False,
                "publicationAuthorized": False,
            })
        slice_preflight.start()
        self.addCleanup(slice_preflight.stop)
        proposal = patch(
            "app_generator.runtime.v3_recovery_policy.prepare_versioned_course_proposal",
            return_value={
                "status": "VERSIONED_COURSE_PROPOSAL_STAGED_NOT_ADMITTED",
                "proposalSha256": "c"*64,
                "versionedScopeAdmitted": False,
                "publicationAuthorized": False,
            })
        proposal.start()
        self.addCleanup(proposal.stop)

    def write_registry(self):
        self.registry.write_text(
            json.dumps(self.data, ensure_ascii=True), encoding="utf8")

    def apply(self):
        return apply_registered_recovery(
            self.course, self.private, self.plan, registry_path=self.registry)

    def test_known_signature_selects_verified_handler_and_atomic_audit(self):
        observed = []
        def repair(course, private, plan):
            observed.append((course, private, plan["nextSection"]))
            return good_result()
        with patch("app_generator.runtime.v3_recovery_policy.stage_known_language_repair",
                   side_effect=repair):
            result = self.apply()
        self.assertEqual(observed, [(self.course, self.private, "section-9-5")])
        self.assertTrue(result["repairStaged"])
        record = read_policy_state(self.private)
        self.assertEqual(record["triggerIncident"], _TRIGGER)
        self.assertEqual(record["remedyIncident"], _REMEDY)
        self.assertEqual(record["candidateSha256"], _CANDIDATE)
        self.assertEqual(record["remainingAutomaticRetries"], 0)
        self.assertIs(record["publicationAuthorized"], False)

    def test_restart_idempotent_policy_audit_preserves_provenance(self):
        with patch("app_generator.runtime.v3_recovery_policy.stage_known_language_repair",
                   return_value=good_result()):
            first = self.apply()
            previous = read_policy_state(self.private)
            second = self.apply()
            current = read_policy_state(self.private)
        self.assertEqual(first, second)
        self.assertEqual(previous["revision"]+1, current["revision"])
        self.assertEqual(previous["candidateSha256"], current["candidateSha256"])

    def test_no_issue_no_handler_or_paid_io(self):
        self.plan["scriptQuarantinedSections"] = {}
        with patch("app_generator.runtime.v3_recovery_policy.stage_known_language_repair",
                   side_effect=AssertionError("no handler should run")):
            out = self.apply()
        self.assertEqual(out["repairStatus"], "NO_SCRIPT_BLOCKER")
        self.assertIsNone(read_policy_state(self.private))

    def test_unknown_failure_is_logged_not_assumed_to_be_fixed(self):
        self.plan["scriptQuarantinedSections"] = {"section-9-4": 2}
        with patch("app_generator.runtime.v3_recovery_policy.stage_known_language_repair",
                   side_effect=AssertionError("must not guess")):
            result = self.apply()
        self.assertFalse(result["repairStaged"])
        self.assertEqual(result["repairStatus"], "STOP_UNKNOWN_SCRIPT_SIGNATURE")
        record = read_policy_state(self.private)
        self.assertEqual(record["failureClass"], "NO_RECOGNIZED_RECOVERY")
        self.assertEqual(record["candidateSha256"], None)

    def test_retired_remedy_disabled_without_disabling_other_sections(self):
        item = next(x for x in self.data["incidents"] if x["id"] == _REMEDY)
        item["status"] = "retired"
        self.write_registry()
        with patch("app_generator.runtime.v3_recovery_policy.stage_known_language_repair",
                   side_effect=AssertionError("retired handler invoked")):
            result = self.apply()
        self.assertEqual(result["repairStatus"], "STOP_REGISTERED_REMEDY_RETIRED")
        self.assertEqual(self.plan["nextSection"], "section-9-5")
        record = read_policy_state(self.private)
        self.assertIs(record["publicationAuthorized"], False)

    def test_replaced_handler_or_duplicate_registry_fails_closed(self):
        victim = next(x for x in self.data["incidents"] if x["id"] == _REMEDY)
        victim["automaticRemedy"]["runtimePath"] = "malicious/override.py"
        self.write_registry()
        with self.assertRaisesRegex(ValueError, "HANDLER_IDENTITY_MISMATCH"):
            self.apply()
        self.assertIsNone(read_policy_state(self.private))
        victim["automaticRemedy"]["runtimePath"] = (
            "app_generator/runtime/v3_auto_repair.py")
        self.data["incidents"].append(deepcopy(victim))
        self.write_registry()
        with self.assertRaisesRegex(ValueError, "INCIDENT_UNREGISTERED"):
            self.apply()

    def test_durable_receipt_tamper_stops_before_any_repeat(self):
        with patch("app_generator.runtime.v3_recovery_policy.stage_known_language_repair",
                   return_value=good_result()):
            self.apply()
        path = self.private / "v3-recovery-policy-state.json"
        data = json.loads(path.read_text(encoding="utf8"))
        data["candidateSha256"] = "0"*64
        path.write_text(json.dumps(data), encoding="utf8")
        calls = []
        with patch("app_generator.runtime.v3_recovery_policy.stage_known_language_repair",
                   side_effect=lambda *args: calls.append("bad")):
            with self.assertRaisesRegex(ValueError, "INTEGRITY_MISMATCH"):
                self.apply()
        self.assertEqual(calls, [])

    def test_unknown_or_fabricated_handler_result_cannot_mark_qa_pass(self):
        for forged in (
            {"repairStaged": True, "repairStatus": "AI_CONSENSUS_PASS",
             "candidateSha256": _CANDIDATE},
            {"repairStaged": True,
             "repairStatus": "PRIVATE_REPAIR_STAGED_PENDING_TWO_GEMINI_REVIEWS",
             "candidateSha256": "0"*64, "archivalParentSha256": _ARCHIVE},
            {"repairStaged": True,
             "repairStatus": "PRIVATE_REPAIR_STAGED_PENDING_TWO_GEMINI_REVIEWS",
             "candidateSha256": _CANDIDATE,
             "archivalParentSha256": _ARCHIVE,
             "publicationAuthorized": True},
        ):
            with self.subTest(forged=forged):
                with patch(
                    "app_generator.runtime.v3_recovery_policy.stage_known_language_repair",
                    return_value=forged):
                    with self.assertRaisesRegex(
                            ValueError, "UNVERIFIED_HANDLER_RESULT|HANDLER_RESULT_NOT_VERIFIED"):
                        self.apply()
                self.assertIsNone(read_policy_state(self.private))

    def test_missing_persistent_registry_blocks_verified_repair_execution(self):
        self.registry.unlink()
        with self.assertRaisesRegex(ValueError, "UNREADABLE_REGISTRY"):
            self.apply()
        self.assertIsNone(read_policy_state(self.private))

    def test_v6_normal_entrypoint_wires_registry_not_oneoff_repair(self):
        from scripts import run_v3_yoga6_recovery_worker as worker
        import inspect
        # BSA254: the source-free public entry now takes the historic OS
        # coordinator BEFORE entering the original V3 recovery dispatcher.
        # Verify BOTH executable functions rather than requiring the entire
        # long worker body to remain inside one inspect.getsource() span.
        entry = inspect.getsource(worker.main)
        self.assertIn("with coordinator_lock(lock_root):", entry)
        self.assertIn("return _main_unlocked(args)", entry)
        source = inspect.getsource(worker._main_unlocked)
        self.assertIn("apply_registered_recovery(", source)
        self.assertIn("--auto-advance", source)
        self.assertIn("operation_authorized=args.execute", source)
        self.assertIn("transfer_authorized=args.allow_generated_text_transfer",
                      source)


    def test_v6_end_to_end_known_repair_then_auto_next_eligible_stage(self):
        from app_generator.runtime.v3_forward_progress import (
            advance_until_boundary, read_checkpoint)
        from tests.test_v3_forward_progress import FakeCourse
        course = FakeCourse()
        course.next_override = "section-9-5"
        def plan():
            current = course.plan()
            current["scriptQuarantinedSections"] = {"section-9-2": 2}
            current["quarantinedSections"] = ["section-9-2"]
            return current
        order = []
        def recover(p):
            order.append("source-free-remedy")
            return apply_registered_recovery(
                self.course, self.private, p, registry_path=self.registry)
        def review():
            order.append("next-independent-review")
            return course.pass_one()
        with patch("app_generator.runtime.v3_recovery_policy.stage_known_language_repair",
                   return_value=good_result()):
            report = advance_until_boundary(
                self.private, plan, review, source_free_recovery=recover,
                max_activities=2, operation_authorized=True,
                transfer_authorized=True)
        self.assertEqual(order, [
            "source-free-remedy", "next-independent-review",
            "next-independent-review"])
        self.assertEqual(report["advancedActivitiesThisInvocation"], 2)
        self.assertEqual(report["modelConsensusPassActivities"], 2)
        self.assertEqual(read_checkpoint(self.private)["phase"], "STOPPED")
        self.assertEqual(read_policy_state(self.private)["candidateSha256"],
                         _CANDIDATE)
        self.assertFalse(report["publicationAuthorized"])

    def test_v6_crash_after_recovery_before_next_stage_then_restart(self):
        from app_generator.runtime.v3_forward_progress import (
            advance_until_boundary, read_checkpoint)
        from tests.test_v3_forward_progress import FakeCourse
        course = FakeCourse()
        course.next_override = "section-9-5"
        hits = [0]
        actual_reviews = []
        def flaky_plan():
            hits[0] += 1
            if hits[0] == 2:
                raise KeyboardInterrupt("synthetic crash after verified repair")
            row = course.plan()
            row["scriptQuarantinedSections"] = {"section-9-2": 2}
            row["quarantinedSections"] = ["section-9-2"]
            return row
        def normal_plan():
            row = course.plan()
            row["scriptQuarantinedSections"] = {"section-9-2": 2}
            row["quarantinedSections"] = ["section-9-2"]
            return row
        def recover(p):
            return apply_registered_recovery(
                self.course, self.private, p, registry_path=self.registry)
        def review():
            actual_reviews.append(1)
            return course.pass_one()
        with patch("app_generator.runtime.v3_recovery_policy.stage_known_language_repair",
                   return_value=good_result()):
            with self.assertRaises(KeyboardInterrupt):
                advance_until_boundary(
                    self.private, flaky_plan, review,
                    source_free_recovery=recover,
                    operation_authorized=True, transfer_authorized=True,
                    max_activities=2)
            first = read_checkpoint(self.private)
            self.assertEqual(first["status"],
                             "STAGED_VERSIONED_CANDIDATE_PENDING_FRESH_MODEL_QA")
            self.assertEqual(actual_reviews, [])
            self.assertEqual(read_policy_state(self.private)["revision"], 1)
            # A fresh, explicitly authorized process can safely reuse the
            # verified idempotent remedy and move to the next eligible stage.
            resumed = advance_until_boundary(
                self.private, normal_plan, review,
                source_free_recovery=recover,
                operation_authorized=True, transfer_authorized=True,
                max_activities=1)
        self.assertEqual(resumed["advancedActivitiesThisInvocation"], 1)
        self.assertEqual(actual_reviews, [1])
        self.assertEqual(read_policy_state(self.private)["revision"], 2)
        self.assertFalse(resumed["publicationAuthorized"])

    def test_v6_unreconciled_content_repair_does_not_block_other_safe_work(self):
        from app_generator.runtime.v3_forward_progress import advance_until_boundary
        from tests.test_v3_forward_progress import FakeCourse
        course = FakeCourse()
        course.next_override = "section-9-5"
        def plan():
            p = course.plan()
            p["scriptQuarantinedSections"] = {"section-9-2": 2}
            p["quarantinedSections"] = ["section-9-2"]
            return p
        def verify(p):
            return apply_registered_recovery(
                self.course, self.private, p, registry_path=self.registry)
        with patch(
            "app_generator.runtime.v3_recovery_policy.stage_known_language_repair",
            return_value={
                "repairStaged": False,
                "repairStatus": "STOP_NO_GENUINE_REVIEW_EVIDENCE",
                "publicationAuthorized": False}):
            result = advance_until_boundary(
                self.private, plan, course.pass_one,
                source_free_recovery=verify,
                operation_authorized=True, transfer_authorized=True,
                max_activities=1)
        self.assertEqual(result["advancedActivitiesThisInvocation"], 1)
        self.assertEqual(read_policy_state(self.private)["status"],
                         "STOP_NO_GENUINE_REVIEW_EVIDENCE")
        self.assertFalse(result["publicationAuthorized"])

    def test_tampered_audit_blocks_future_work_even_if_issue_disappears(self):
        with patch("app_generator.runtime.v3_recovery_policy.stage_known_language_repair",
                   return_value=good_result()):
            self.apply()
        target = self.private / "v3-recovery-policy-state.json"
        state = json.loads(target.read_text(encoding="utf8"))
        state["status"] = "STOP_NO_GENUINE_REVIEW_EVIDENCE"
        target.write_text(json.dumps(state), encoding="utf8")
        self.plan["scriptQuarantinedSections"] = {}
        with self.assertRaisesRegex(ValueError, "INTEGRITY_MISMATCH"):
            self.apply()

    def test_source_free_receipt_rejects_untrusted_log_text(self):
        with self.assertRaisesRegex(ValueError, "UNSAFE_STATUS"):
            persist_policy_state(self.private, {
                "repairStatus": "EXPOSED_API_KEY_OR_SOURCE_TEXT",
                "repairStaged": False,
                "publicationAuthorized": False})
        self.assertIsNone(read_policy_state(self.private))

    def test_all_historical_remedies_link_through_real_indirect_dispatch(self):
        data = json.loads(_DEFAULT_REGISTRY.read_text(encoding="utf8"))
        known = {x["id"]: x for x in data["incidents"]}
        policy = (Path(__file__).resolve().parents[1] /
                  "app_generator/runtime/v3_recovery_policy.py")
        source = policy.read_text(encoding="utf8")
        for incident in ("BSA-20261116-174", "BSA-20261116-176"):
            with self.subTest(incident=incident):
                entry = known[incident]["automaticRemedy"]["normalEntryPoints"][0]
                self.assertEqual(entry["path"],
                                 "app_generator/runtime/v3_recovery_policy.py")
                self.assertIn(entry["marker"], source)
        self.assertEqual(
            known["BSA-20261116-177"]["automaticRemedy"]["normalEntryPoints"][0]["path"],
            "scripts/run_v3_yoga6_recovery_worker.py")

if __name__ == "__main__":
    unittest.main()

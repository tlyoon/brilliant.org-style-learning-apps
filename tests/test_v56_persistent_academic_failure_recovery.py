"""BSA280 adversarial owner-academic failure/independent-code-repair gates."""
from __future__ import annotations
import os
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch
from app_generator.runtime.v3_persistent_academic_failure_recovery import (
    classify_owner_failure,classify_codegen_failure,owner_recovery_plan,
    should_skip_unchanged_owner,needs_coding_recovery,
)
from scripts import bosla_persistent_development as worker

H="a"*40

class OwnerFailureRecoveryTests(TestCase):
    def test_source_tamper_overrides_apparent_transient(self):
        verdict=classify_owner_failure(
            exit_code=124,log_excerpt="HTTP 503 SOURCE_SHA256_MISMATCH")
        self.assertEqual(verdict,"SOURCE_OR_SIGNATURE_UNTRUSTED")

    def test_missing_producer_classified_as_code_needed(self):
        self.assertEqual(classify_owner_failure(
            exit_code=2,
            log_excerpt="NEW_SOURCE_SPECIFIC_PROOF_PRODUCER_REQUIRED"),
            "MISSING_SCIENCE_PRODUCER")

    def test_local_bug_creates_independent_repair_lane(self):
        state={}
        p=owner_recovery_plan(
            state=state,head=H,exit_code=1,
            log_excerpt="Traceback: ModuleNotFoundError")
        self.assertEqual(p["mode"],
                         "DISPATCH_INDEPENDENT_SOURCE_SAFE_CODE_REPAIR")
        self.assertFalse(p["academicPASS"])
        self.assertFalse(p["replayUnknownProviderRequests"])
        self.assertTrue(should_skip_unchanged_owner(state,H))
        self.assertFalse(should_skip_unchanged_owner(state,"b"*40))
        self.assertNotIn("Traceback",str(state))

    def test_first_transient_retries_once_then_escalates(self):
        state={}
        first=owner_recovery_plan(
            state=state,head=H,exit_code=124,
            log_excerpt="HTTP 503: connection unavailable")
        second=owner_recovery_plan(
            state=state,head=H,exit_code=124,
            log_excerpt="HTTP 503: connection unavailable")
        self.assertEqual(first["mode"],"BOUNDED_RETRY_ON_NEXT_SCHEDULE")
        self.assertEqual(second["mode"],
                         "DISPATCH_INDEPENDENT_SOURCE_SAFE_CODE_REPAIR")
        self.assertEqual(second["count"],2)

    def test_changing_timestamps_cannot_reset_transient_retry_budget(self):
        state={}
        first=owner_recovery_plan(
            state=state,head=H,exit_code=124,
            log_excerpt="HTTP 503 at 11:15:05 child PID 11234")
        second=owner_recovery_plan(
            state=state,head=H,exit_code=124,
            log_excerpt="HTTP 503 at 11:30:45 child PID 99382")
        self.assertEqual(first["fingerprint"],second["fingerprint"])
        self.assertEqual(second["count"],2)
        self.assertEqual(second["mode"],
                         "DISPATCH_INDEPENDENT_SOURCE_SAFE_CODE_REPAIR")

    def test_source_untrusted_never_dispatches_repair_or_retry(self):
        state={}
        p=owner_recovery_plan(state=state,head=H,exit_code=2,
                              log_excerpt="SIGNATURE_INVALID")
        self.assertEqual(p["mode"],
                         "QUARANTINE_ACADEMIC_ACCEPTANCE_AND_SOURCE_WRITES")
        self.assertFalse(should_skip_unchanged_owner(state,H))

    def test_unclassified_failure_does_not_invent_academic_pass(self):
        state={}
        p=owner_recovery_plan(state=state,head=H,exit_code=9,
                              log_excerpt="")
        self.assertEqual(p["classification"],"UNCLASSIFIED_OWNER_FAILURE")
        self.assertFalse(p["academicPASS"])
        self.assertFalse(p["publicationAuthorized"])

    def test_no_pass_for_bad_input_or_owner_success_without_readback(self):
        with self.assertRaisesRegex(ValueError,"AUTHENTIC_OWNER_HEAD"):
            owner_recovery_plan(state={},head="invalid",exit_code=1,
                                log_excerpt="")
        self.assertEqual(classify_owner_failure(
            exit_code=0,log_excerpt="PASS"),
            "OWNER_SUCCESS_VERIFY_SEPARATELY")

    def test_codex_windows_write_denial_is_engineering_not_science(self):
        err="helper_unknown_error: setup refresh had errors"
        self.assertEqual(classify_codegen_failure(
            exit_code=0,log_excerpt=err,changed_files=False),
            "CODEX_LOCAL_SANDBOX_WRITE_OR_EXEC_FAILURE")
        self.assertTrue(needs_coding_recovery(
            classification="CODEX_LOCAL_SANDBOX_WRITE_OR_EXEC_FAILURE",
            previous_failures=1))
        self.assertFalse(needs_coding_recovery(
            classification="CODEX_CODE_CHANGED_TESTS_AND_REVIEW_REQUIRED",
            previous_failures=1))

    def test_normal_cycle_automatically_repairs_owner_failure(self):
        with TemporaryDirectory() as t:
            private=Path(t)
            def owner(state):
                state["academicFailure"]={
                    "head":H,
                    "mode":"DISPATCH_INDEPENDENT_SOURCE_SAFE_CODE_REPAIR",
                    "classification":"LOCAL_OWNER_IMPLEMENTATION_DEFECT"}
                return False
            with (patch.object(worker,"PRIVATE",private),
                  patch.object(worker,"STATE",private/"state.json"),
                  patch.object(worker,"JOURNAL",private/"events.jsonl"),
                  patch.dict(os.environ,{"COMPUTERNAME":"YOGA6"}),
                  patch.object(worker,"SingleFlight"),
                  patch.object(worker,"_head",return_value=H),
                  patch.object(worker,"_branch",
                               return_value=worker.MAIN_BRANCH),
                  patch.object(worker,"_promote_known",return_value=False),
                  patch.object(worker,"_owner_stage",side_effect=owner),
                  patch.object(worker,"_codex_stage") as codegen):
                r=worker.cycle()
                codegen.assert_called_once()
                self.assertEqual(r["status"],
                    "BSA280_ACADEMIC_FAILURE_ISOLATED_CODE_REPAIR_DISPATCH")
                self.assertNotIn("lastOwnerHead",r)
                self.assertNotIn("academicProofTasksAccepted",r)

    def test_source_untrusted_does_not_launch_codex(self):
        with TemporaryDirectory() as t:
            private=Path(t)
            def owner(state):
                state["academicFailure"]={
                    "head":H,
                    "mode":"QUARANTINE_ACADEMIC_ACCEPTANCE_AND_SOURCE_WRITES"}
                return False
            with (patch.object(worker,"PRIVATE",private),
                  patch.object(worker,"STATE",private/"state.json"),
                  patch.object(worker,"JOURNAL",private/"events.jsonl"),
                  patch.dict(os.environ,{"COMPUTERNAME":"YOGA6"}),
                  patch.object(worker,"SingleFlight"),
                  patch.object(worker,"_head",return_value=H),
                  patch.object(worker,"_branch",
                               return_value=worker.MAIN_BRANCH),
                  patch.object(worker,"_promote_known",return_value=False),
                  patch.object(worker,"_owner_stage",side_effect=owner),
                  patch.object(worker,"_codex_stage") as codegen):
                r=worker.cycle()
                codegen.assert_not_called()
                self.assertEqual(r["academicFailure"]["mode"],
                    "QUARANTINE_ACADEMIC_ACCEPTANCE_AND_SOURCE_WRITES")

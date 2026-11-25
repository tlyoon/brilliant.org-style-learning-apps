"""Synthetic negative controls; no browser, network, remote machine or secrets."""
from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import tempfile
import unittest

from app_generator.validation.execution_access_recovery import (
    TASK_DEPENDENCIES, add_event, new_checkpoint, operation_fingerprint,
    safe_plan,
)
from scripts.plan_external_execution_recovery import main as cli_main


class ExecutionAccessRecoveryTests(unittest.TestCase):
    S = "a" * 64
    P = "b" * 64

    def setUp(self):
        self.state = new_checkpoint(self.S, self.P)

    def receipt(self, task: str, event: str):
        self.state = add_event(self.state, task_id=task, event_id=event,
                               outcome="RECEIPT_RECORDED", receipt_sha256="e" * 64)
        return self.state

    def deny(self, task: str, event: str):
        self.state = add_event(self.state, task_id=task, event_id=event,
                               outcome="BLOCKED_EXTERNAL", denial_class="SECURITY_CONTROL",
                               tool_class="REMOTE_DESKTOP")
        return self.state

    def test_initial_plan_has_no_authorization_or_publication(self):
        result = safe_plan(self.state)
        self.assertEqual(["source_verify"], result["readyForSeparateAuthorizationCheck"])
        self.assertFalse(result["externalAuthorizationGranted"])
        self.assertFalse(result["publicationAuthorized"])
        self.assertFalse(result["automaticallyRetriesDeniedOperations"])

    def test_blocked_action_immutable(self):
        self.receipt("source_verify", "src00001")
        self.deny("visual_receipt_verify", "visual00001")
        with self.assertRaisesRegex(ValueError, "already attempted"):
            self.deny("visual_receipt_verify", "visual00002")
        with self.assertRaisesRegex(ValueError, "already attempted"):
            self.receipt("visual_receipt_verify", "visual00003")

    def test_denying_visual_leaves_independent_tasks_ready(self):
        self.receipt("source_verify", "src00001")
        self.deny("visual_receipt_verify", "visual00001")
        plan = safe_plan(self.state)
        self.assertIn("review_claim_reconcile", plan["readyForSeparateAuthorizationCheck"])
        self.assertIn("partial_evidence_inventory", plan["readyForSeparateAuthorizationCheck"])
        self.assertIn("science_meaning_verify", plan["readyForSeparateAuthorizationCheck"])
        self.assertIn("multilingual_meaning_verify", plan["readyForSeparateAuthorizationCheck"])
        self.assertNotIn("visual_receipt_verify", plan["readyForSeparateAuthorizationCheck"])
        self.assertTrue(next(x for x in plan["waitingForDependencies"]
                             if x["taskId"] == "pilot_acceptance")["hasDeniedDependency"])

    def test_no_alias_for_denied_operation(self):
        with self.assertRaisesRegex(ValueError, "unknown canonical task"):
            operation_fingerprint(self.S, self.P, "visual_receipt_verify_second_attempt")
        with self.assertRaises(ValueError):
            add_event(self.state, task_id="try_visual_qa_again", event_id="event00001",
                      outcome="BLOCKED_EXTERNAL", denial_class="SECURITY_CONTROL",
                      tool_class="REMOTE_DESKTOP")

    def test_repeated_event_id_rejected(self):
        self.receipt("source_verify", "event00001")
        with self.assertRaisesRegex(ValueError, "event ID"):
            self.receipt("mcq_model_verify", "event00001")

    def test_invalid_boolean_count_and_unauthorized_outcomes(self):
        with self.assertRaises(ValueError):
            add_event(self.state, task_id="source_verify", event_id="event00001",
                      outcome="AUTHORIZED")
        bad = deepcopy(self.state)
        bad["schemaVersion"] = True
        with self.assertRaises(ValueError):
            safe_plan(bad)

    def test_blocked_cannot_claim_success_receipt(self):
        with self.assertRaisesRegex(ValueError, "cannot be marked successful"):
            add_event(self.state, task_id="source_verify", event_id="event00001",
                      outcome="BLOCKED_EXTERNAL", receipt_sha256="a" * 64,
                      denial_class="SECURITY_CONTROL", tool_class="REMOTE_DESKTOP")

    def test_success_requires_documented_receipt(self):
        with self.assertRaisesRegex(ValueError, "receiptSha256"):
            add_event(self.state, task_id="source_verify", event_id="event00001",
                      outcome="RECEIPT_RECORDED", receipt_sha256="not-a-sha")

    def test_downstream_success_blocked_until_dependencies_complete(self):
        with self.assertRaises(ValueError):
            self.receipt("pilot_acceptance", "pilot00001")
        self.receipt("source_verify", "src00001")
        with self.assertRaises(ValueError):
            self.receipt("pilot_acceptance", "pilot00002")

    def test_stable_fingerprint_separates_versions(self):
        a = operation_fingerprint(self.S, self.P, "source_verify")
        self.assertEqual(a, operation_fingerprint(self.S, self.P, "source_verify"))
        self.assertNotEqual(a, operation_fingerprint("c" * 64, self.P, "source_verify"))
        self.assertNotEqual(a, operation_fingerprint(self.S, "d" * 64, "source_verify"))

    def test_event_log_chain_detects_tamper(self):
        self.receipt("source_verify", "src00001")
        tampered = deepcopy(self.state)
        tampered["events"][0]["receiptSha256"] = "f" * 64
        with self.assertRaisesRegex(ValueError, "checksum"):
            safe_plan(tampered)

    def test_chain_reordering_or_truncation_detected_by_head_when_pinned(self):
        self.receipt("source_verify", "src00001")
        self.receipt("mcq_model_verify", "mcq00001")
        expected_head = safe_plan(self.state)["eventChainHead"]
        reordered = deepcopy(self.state)
        reordered["events"] = list(reversed(reordered["events"]))
        with self.assertRaises(ValueError):
            safe_plan(reordered)
        truncated = deepcopy(self.state)
        truncated["events"].pop()
        self.assertNotEqual(expected_head, safe_plan(truncated)["eventChainHead"])

    def test_extra_command_or_secret_fields_rejected(self):
        self.receipt("source_verify", "src00001")
        for injected in ({"command": "invoke private shell"},
                         {"api_key": "SECRET"}, {"sourceText": "COPY"}):
            with self.subTest(field=tuple(injected)):
                state = deepcopy(self.state)
                state["events"][0].update(injected)
                with self.assertRaisesRegex(ValueError, "private/command"):
                    safe_plan(state)
        state = deepcopy(self.state)
        state["opaque_blob"] = "secret"
        with self.assertRaises(ValueError):
            safe_plan(state)

    def test_external_denial_has_strict_enum(self):
        with self.assertRaises(ValueError):
            add_event(self.state, task_id="source_verify", event_id="event00001",
                      outcome="BLOCKED_EXTERNAL", denial_class="UNKNOWN_BYPASS",
                      tool_class="REMOTE_DESKTOP")

    def test_invalid_event_id_rejected(self):
        with self.assertRaises(ValueError):
            self.receipt("source_verify", "C:\\PRIVATE\\my-token.txt")

    def test_function_does_not_mutate_caller_checkpoint(self):
        old = deepcopy(self.state)
        self.receipt("source_verify", "src00001")
        self.assertEqual(old, new_checkpoint(self.S, self.P))

    def test_recorded_completion_is_not_scientific_pass(self):
        self.receipt("source_verify", "src00001")
        result = safe_plan(self.state)
        self.assertFalse(result["scientificApproval"])
        self.assertFalse(result["publicationAuthorized"])

    def test_cli_exclusively_creates_private_file_and_cannot_overwrite(self):
        with tempfile.TemporaryDirectory() as td:
            initial = Path(td) / "run0.json"
            self.assertEqual(0, cli_main(["init", "--source-sha256", self.S,
                                          "--package-sha256", self.P, "--out", str(initial)]))
            self.assertEqual(2, cli_main(["init", "--source-sha256", self.S,
                                          "--package-sha256", self.P, "--out", str(initial)]))
            next_file = Path(td) / "run1.json"
            self.assertEqual(0, cli_main(["deny", "--state", str(initial), "--out", str(next_file),
                                          "--task", "source_verify", "--event-id", "block00001",
                                          "--denial-class", "SECURITY_CONTROL",
                                          "--tool-class", "REMOTE_DESKTOP"]))
            self.assertEqual(2, cli_main(["deny", "--state", str(next_file),
                                          "--out", str(Path(td) / "run2.json"),
                                          "--task", "source_verify", "--event-id", "block00002",
                                          "--denial-class", "SECURITY_CONTROL",
                                          "--tool-class", "REMOTE_DESKTOP"]))

    def test_existing_event_cannot_be_rekeyed_to_another_source(self):
        self.receipt("source_verify", "src00001")
        changed = deepcopy(self.state)
        changed["sourceSha256"] = "c" * 64
        with self.assertRaises(ValueError):
            safe_plan(changed)

    def test_cli_rejects_checkpoint_written_inside_code_repository(self):
        forbidden = Path(__file__).resolve().parents[1] / "private-checkpoint-do-not-create.json"
        try:
            self.assertEqual(2, cli_main(["init", "--source-sha256", self.S,
                                          "--package-sha256", self.P,
                                          "--out", str(forbidden)]))
            self.assertFalse(forbidden.exists())
        finally:
            if forbidden.exists():
                forbidden.unlink()

    def test_task_registry_is_known_and_non_executable(self):
        self.assertEqual(10, len(TASK_DEPENDENCIES))
        self.assertTrue(all(" " not in task for task in TASK_DEPENDENCIES))
        self.assertFalse(any("command" in task for task in TASK_DEPENDENCIES))


if __name__ == "__main__":
    unittest.main()

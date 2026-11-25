"""Real normal-path V3 recovery tests using a completely offline Gemini SDK fake.

Every test goes through V3NativeGeminiApiSessions, the ordinary course
dispatcher, the on-disk immutable checkpoint and the real four-dimension
scientific rubric. No Google credentials/API calls, no fake PASS in real data.
"""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest
from unittest.mock import patch

from app_generator.runtime.run_context import RunContext
from app_generator.runtime.v3_course_review import (
    advance_v3_course_review, plan_v3_course_review,
)
from app_generator.validation.autonomous_completion import package_identity
from app_generator.gemini.v3_native_api_reviewers import V3NativeGeminiApiSessions
from tests.test_v3_course_review_dispatch import synthetic_course
from tests.test_v3_native_gemini_api_reviewers import FakeTypes, config
from tests.test_v3_authorized_execution_bridge import FakeReviewer


class OfflineModels:
    def __init__(self, mode: str):
        self.mode = mode
        self.calls = []

    def generate_content(self, *, model, contents, config):
        self.calls.append((model, contents, config))
        if self.mode == "unreconciled":
            raise TimeoutError("SYNTHETIC provider returned nothing")
        valid = FakeReviewer().ask(contents, stage="academic-v3-autonomous")
        if self.mode == "parse":
            valid = "{not-json"
        elif self.mode == "fenced":
            marker = chr(96) * 3
            valid = marker + "json\n" + valid + "\n" + marker
        elif self.mode in ("rubric", "scientific-fail"):
            response = json.loads(valid)
            if self.mode == "rubric":
                response["rationales"]["physicsAnswer"] = "short"
            else:
                response["dimensions"]["physicsAnswer"] = "FAIL"
                response["concern"] = "SYNTHETIC physics counterexample fails."
            valid = json.dumps(response)
        return SimpleNamespace(text=valid)


class OfflineClient:
    def __init__(self, mode: str):
        self.models = OfflineModels(mode)
        self.closed = False

    def close(self):
        self.closed = True


class V3ResponseRecoveryEndToEnd(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        base = Path(temp.name)
        self.repo = base / "repo"
        self.chapter = synthetic_course(self.repo, n=6, activities=2)
        self.private = base / "PRIVATE_DO_NOT_PUBLISH"
        self.clients = []
        self.digest, self.activities = package_identity(
            (self.chapter / "section-7-1/package.json").read_bytes())

    def factory(self, modes=("valid", "valid")):
        calls = len(self.clients)
        def make(role):
            index = len(self.clients) - calls
            client = OfflineClient(modes[index])
            self.clients.append(client)
            return client
        return V3NativeGeminiApiSessions(
            config(), operation_authorized=True,
            generated_content_transfer_allowed=True,
            sdk_client_factory=make, sdk_types=FakeTypes,
        )

    def dispatch(self, modes=("valid", "valid")):
        return advance_v3_course_review(
            self.chapter, self.repo, private_root=self.private,
            session_factory=self.factory(modes),
            external_operation_authorized=True,
            generated_content_transfer_allowed=True,
            continue_independent=True, max_activities=1,
        )

    def plan(self):
        return plan_v3_course_review(
            self.chapter, self.repo, private_root=self.private,
            continue_independent=True,
        )

    def role_path(self, index, role):
        name = f"v3-review-{self.digest[:12]}-{index:03d}-{role}"
        return (self.private / ("v3-generated-" + self.digest) /
                "batches" / (name + ".json"))

    def response_path(self, index, role):
        return self.role_path(index, role).with_suffix(".response.txt")

    def test_pre_fix_negative_control_no_response_is_not_replayed(self):
        first = self.dispatch(("unreconciled", "valid"))
        self.assertEqual(first["activitiesAssessedRows"], 1)
        self.assertEqual(first["modelUncertainActivities"], 1)
        self.assertEqual(first["quarantinedSections"], ["section-7-1"])
        self.assertEqual(self.plan()["nextSection"], "section-7-2")
        self.assertEqual(json.loads(self.role_path(0,0).read_text())["state"], "AMBIGUOUS")
        self.assertFalse(self.response_path(0,0).exists())
        again = self.plan()
        self.assertNotIn("section-7-1", again["isolatedLocalFailureSections"])
        self.assertEqual(len(self.clients), 2)

    def test_real_normal_dispatch_captures_malformed_then_advances_same_section(self):
        first = self.dispatch(("parse", "valid"))
        self.assertEqual(first["modelUncertainActivities"], 1)
        self.assertEqual(first["modelConsensusPassActivities"], 0)
        self.assertEqual(first["nextSection"], "section-7-1")
        self.assertEqual(first["isolatedLocalFailureSections"], ["section-7-1"])
        role = json.loads(self.role_path(0,0).read_text())
        self.assertEqual(role["state"], "PARSE_FAILED")
        self.assertEqual(role["reasonCode"], "V3_CAPTURED_PARSE_FAILED")
        self.assertEqual(self.response_path(0,0).read_text(encoding="utf8"),
                         "{not-json")
        self.assertEqual(role["responseSha256"], sha256(b"{not-json").hexdigest())
        second = self.dispatch()
        self.assertEqual(second["modelConsensusPassActivities"], 1)
        self.assertEqual(second["modelUncertainActivities"], 1)
        self.assertEqual(second["activitiesAssessedRows"], 2)
        self.assertEqual(len(self.clients), 4)
        self.assertTrue(all(len(x.models.calls) == 1 for x in self.clients))
        self.assertEqual(json.loads(self.role_path(0,0).read_text())["state"],
                         "PARSE_FAILED")
        self.assertFalse(second["publicationAuthorized"])

    def test_rubric_failure_is_retained_not_fabricated(self):
        first = self.dispatch(("rubric", "valid"))
        self.assertEqual(first["modelUncertainActivities"], 1)
        self.assertEqual(json.loads(self.role_path(0,0).read_text())["state"],
                         "RUBRIC_FAILED")
        self.assertEqual(first["nextSection"], "section-7-1")
        self.assertEqual(self.dispatch()["modelConsensusPassActivities"], 1)

    def test_exact_fenced_response_locally_normalized_but_original_saved(self):
        data = self.dispatch(("fenced", "valid"))
        self.assertEqual(data["modelConsensusPassActivities"], 1)
        raw = self.response_path(0,0).read_text(encoding="utf8")
        self.assertTrue(raw.startswith(chr(96)*3 + "json\n"))
        self.assertTrue(raw.endswith("\n" + chr(96)*3))
        self.assertEqual(sha256(raw.encode()).hexdigest(),
                         json.loads(self.role_path(0,0).read_text())["responseSha256"])
        self.assertFalse(data["publicationAuthorized"])

    def test_after_response_capture_crash_restarts_without_reissuing_role_zero(self):
        original = RunContext.save_stage
        fired = [False]
        def crash_after_captured(context, name, document, raw_response=None):
            if (not fired[0] and name.endswith("-000-0")
                    and isinstance(document, dict)
                    and document.get("state") == "COMPLETE"):
                fired[0] = True
                raise KeyboardInterrupt("SYNTHETIC local crash after capture")
            return original(context, name, document, raw_response)
        with patch.object(RunContext, "save_stage", crash_after_captured):
            with self.assertRaisesRegex(KeyboardInterrupt, "SYNTHETIC local crash"):
                self.dispatch()
        self.assertEqual(len(self.clients),2)
        self.assertEqual(len(self.clients[0].models.calls),1)
        self.assertEqual(len(self.clients[1].models.calls),0)
        self.assertEqual(json.loads(self.role_path(0,0).read_text())["state"],
                         "RESPONSE_CAPTURED")
        self.assertTrue(self.response_path(0,0).is_file())
        resumed = self.dispatch()
        self.assertEqual(resumed["modelConsensusPassActivities"],1)
        self.assertEqual(resumed["activitiesFullyModelReviewed"],1)
        self.assertEqual(len(self.clients),4)
        self.assertEqual([len(c.models.calls) for c in self.clients],
                         [1,0,0,1])
        self.assertEqual(json.loads(self.role_path(0,0).read_text())["state"],
                         "COMPLETE")

    def test_hash_tamper_cannot_turn_uncertainty_into_progress(self):
        self.dispatch(("parse","valid"))
        self.response_path(0,0).write_text(
            "SYNTHETIC_TAMPER",encoding="utf8")
        plan = self.plan()
        self.assertNotIn("section-7-1", plan["isolatedLocalFailureSections"])
        self.assertIn("section-7-1",plan["quarantinedSections"])
        self.assertEqual(plan["nextSection"],"section-7-2")

    def test_current_legacy_valueerror_ambiguity_stays_quarantined(self):
        self.dispatch(("unreconciled","valid"))
        claim = self.role_path(0,0)
        data = json.loads(claim.read_text())
        data["reasonCode"] = "ValueError"
        claim.write_text(json.dumps(data), encoding="utf8")
        plan=self.plan()
        self.assertIn("section-7-1",plan["quarantinedSections"])
        self.assertEqual(plan["nextSection"],"section-7-2")
        self.assertFalse(plan["publicationAuthorized"])


    def test_prompt_identity_tamper_prevents_same_section_continuation(self):
        self.dispatch(("parse", "valid"))
        claim = self.role_path(0, 0)
        record = json.loads(claim.read_text(encoding="utf8"))
        record["promptSha256"] = "0" * 64
        claim.write_text(json.dumps(record), encoding="utf8")
        plan = self.plan()
        self.assertIn("section-7-1", plan["quarantinedSections"])
        self.assertNotIn("section-7-1", plan["isolatedLocalFailureSections"])
        self.assertEqual(plan["nextSection"], "section-7-2")

    def test_no_response_capture_write_fails_closed_without_replay(self):
        with patch.object(RunContext, "save_raw_response",
                          side_effect=OSError("SYNTHETIC disk cannot persist reply")):
            first = self.dispatch()
        self.assertEqual(first["modelUncertainActivities"], 1)
        self.assertIn("section-7-1", first["quarantinedSections"])
        self.assertEqual(json.loads(self.role_path(0,0).read_text())["state"],
                         "AMBIGUOUS")
        self.assertFalse(self.response_path(0,0).exists())
        self.assertEqual(len(self.clients), 2)
        self.assertEqual(self.plan()["nextSection"], "section-7-2")

    def test_actual_model_scientific_fail_is_never_repaired_to_pass(self):
        first = self.dispatch(("scientific-fail", "valid"))
        self.assertEqual(first["modelRepairRequiredActivities"], 1)
        self.assertEqual(first["modelConsensusPassActivities"], 0)
        self.assertIn("section-7-1", first["quarantinedSections"])
        self.assertNotIn("section-7-1", first["isolatedLocalFailureSections"])
        self.assertEqual(json.loads(self.role_path(0,0).read_text())["state"],
                         "COMPLETE")
        self.assertTrue(self.response_path(0,0).is_file())
        self.assertFalse(first["publicationAuthorized"])

    def test_complete_captured_response_identity_tamper_fail_closed(self):
        self.dispatch(("parse", "valid"))
        path = self.role_path(0,0)
        claim = json.loads(path.read_text(encoding="utf8"))
        claim["responseSha256"] = "f" * 64
        path.write_text(json.dumps(claim), encoding="utf8")
        plan = self.plan()
        self.assertIn("section-7-1", plan["quarantinedSections"])
        self.assertNotIn("section-7-1", plan["isolatedLocalFailureSections"])

    def test_full_eighteen_activity_section_proceeds_past_one_local_failure(self):
        # Regression against the historical section-wide quarantine: one
        # syntactically invalid but RECEIVED response must not strand 17
        # independent activities or silently erase the uncertain result.
        repo = self.repo.parent / "wide_repo"
        chapter = synthetic_course(repo, n=6, activities=18)
        private = self.private.parent / "wide_private"
        clients = []
        for index in range(18):
            start = len(clients)
            def make(role):
                slot = len(clients) - start
                mode = "parse" if index == 0 and slot == 0 else "valid"
                sdk = OfflineClient(mode)
                clients.append(sdk)
                return sdk
            with self.subTest(ordinal=index + 1):
                factory = V3NativeGeminiApiSessions(
                    config(), operation_authorized=True,
                    generated_content_transfer_allowed=True,
                    sdk_client_factory=make, sdk_types=FakeTypes)
                state = advance_v3_course_review(
                    chapter, repo, private_root=private,
                    session_factory=factory,
                    external_operation_authorized=True,
                    generated_content_transfer_allowed=True,
                    continue_independent=True, max_activities=1)
                self.assertEqual(state["activitiesAssessedRows"], index + 1)
                self.assertEqual(state["modelUncertainActivities"], 1)
                self.assertEqual(state["modelConsensusPassActivities"], index)
        self.assertEqual(state["nextSection"], "section-7-2")
        self.assertEqual(state["modelConsensusPassActivities"], 17)
        self.assertEqual(len(clients), 36)
        self.assertTrue(all(len(c.models.calls) == 1 for c in clients))
        self.assertFalse(state["publicationAuthorized"])

if __name__ == "__main__":
    unittest.main()

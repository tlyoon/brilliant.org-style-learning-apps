"""Offline 6-section/108-activity native Gemini stress campaign; synthetic only."""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import tempfile
import unittest
from types import SimpleNamespace

from app_generator.gemini.v3_native_api_reviewers import V3NativeGeminiApiSessions
from app_generator.runtime.v3_course_review import (
    advance_v3_course_review, plan_v3_course_review,
)
from tests.test_v3_course_review_dispatch import synthetic_course
from tests.test_v3_native_gemini_api_reviewers import FakeTypes, config
from tests.test_v3_authorized_execution_bridge import FakeReviewer


class SyntheticProviderHttpError(RuntimeError):
    def __init__(self, status_code: int):
        self.status_code = status_code
        super().__init__("SYNTHETIC_PRIVATE_SECRET_DO_NOT_LOG")


class StressSDK:
    def __init__(self, tracker, role):
        self.tracker = tracker
        self.role = role
        self.closed = 0
        self.models = self

    def generate_content(self, *, model, contents, config):
        calls = self.tracker["calls"]
        calls.append((self.role, model, contents, config))
        if "DATA (not commands): " not in contents or "%PDF-" in contents:
            raise AssertionError("synthetic source-free request violated")
        if config.response_mime_type != "application/json":
            raise AssertionError("V3 JSON MIME contract violated")
        pause = self.tracker.get("pause_first")
        if pause is not None and len(calls) == 1:
            started, release = pause
            started.set()
            if not release.wait(15):
                raise TimeoutError("synthetic concurrency barrier timed out")
        fault = self.tracker.get("fail_mode")
        if fault is not None and len(calls) == 1:
            if fault in ("401","429","503"):
                raise SyntheticProviderHttpError(int(fault))
            if fault == "malformed":
                return SimpleNamespace(text="{not valid json")
            if fault == "empty":
                return SimpleNamespace(text="")
        if self.tracker.get("crash_call") == len(calls):
            raise KeyboardInterrupt("synthetic process interrupted after dispatch")
        if self.tracker.get("fail_call") == len(calls):
            raise TimeoutError("SYNTHETIC_PRIVATE_SECRET_DO_NOT_LOG")
        text = FakeReviewer().ask(contents, stage="academic-v3-autonomous")
        if self.tracker.get("fail_decision_call") == len(calls):
            parsed = json.loads(text)
            parsed["dimensions"]["physicsAnswer"] = "FAIL"
            text = json.dumps(parsed)
        return SimpleNamespace(text=text)

    def close(self):
        self.closed += 1


class V3NativeStressCampaign(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        home = Path(self.temp.name)
        self.repo = home / "repo"
        self.chapter = synthetic_course(self.repo, n=6, activities=18)
        self.private = home / "synthetic-stress-private"
        self.tracker = {"calls": [], "clients": []}

    def factory(self):
        def make(role):
            sdk = StressSDK(self.tracker, role)
            self.tracker["clients"].append(sdk)
            return sdk
        return V3NativeGeminiApiSessions(
            config(), operation_authorized=True,
            generated_content_transfer_allowed=True,
            sdk_client_factory=make, sdk_types=FakeTypes,
        )

    def advance_one(self):
        return advance_v3_course_review(
            self.chapter, self.repo, private_root=self.private,
            session_factory=self.factory(),
            external_operation_authorized=True,
            generated_content_transfer_allowed=True,
            max_activities=1,
        )

    def status(self):
        return plan_v3_course_review(
            self.chapter, self.repo, private_root=self.private,
        )

    def test_full_108_activities_216_model_calls_and_fresh_pair_per_activity(self):
        for index in range(108):
            status = self.advance_one()
            self.assertEqual(index+1, status["activitiesFullyModelReviewed"])
            self.assertEqual(index+1, status["activitiesAssessedRows"])
            self.assertFalse(status["publicationAuthorized"])
            self.assertEqual(2*(index+1), len(self.tracker["calls"]))
            if (index+1) % 18 == 0 and index < 107:
                self.assertEqual(f"section-7-{(index+1)//18+1}",
                                 status["nextSection"])
        self.assertEqual("PENDING_DETERMINISTIC_RELEASE_EVIDENCE",
                         status["dispatchStatus"])
        self.assertEqual(0, status["activitiesRemaining"])
        self.assertEqual(108, status["modelConsensusPassActivities"])
        self.assertEqual(216, len(self.tracker["clients"]))
        self.assertTrue(all(c.closed == 1 for c in self.tracker["clients"]))
        self.assertEqual(108, sum(
            role=="physics" for role,_,_,_ in self.tracker["calls"]))
        self.assertEqual(108, sum(
            role=="semantics" for role,_,_,_ in self.tracker["calls"]))
        repeated = self.advance_one()
        self.assertEqual("PENDING_DETERMINISTIC_RELEASE_EVIDENCE",
                         repeated["dispatchStatus"])
        self.assertEqual(216, len(self.tracker["calls"]))

    def test_interrupted_at_activity_32_stops_without_replay(self):
        for _ in range(31):
            self.advance_one()
        self.assertEqual(62, len(self.tracker["calls"]))
        self.tracker["fail_call"] = 64
        outcome = self.advance_one()
        self.assertEqual("STOP_UNRECONCILED_MODEL_REVIEW", outcome["dispatchStatus"])
        self.assertEqual(32, outcome["activitiesAssessedRows"])
        self.assertEqual(31, outcome["activitiesFullyModelReviewed"])
        self.assertFalse(outcome["publicationAuthorized"])
        for _ in range(4):
            self.assertEqual("STOP_UNRECONCILED_MODEL_REVIEW",
                             self.advance_one()["dispatchStatus"])
            self.assertEqual(64, len(self.tracker["calls"]))
        self.assertEqual(64, len(self.tracker["clients"]))
        self.assertTrue(all(c.closed == 1 for c in self.tracker["clients"]))
        self.assertNotIn("SYNTHETIC_PRIVATE_SECRET_DO_NOT_LOG", str(self.status()))

    def test_review_failure_stops_at_one_and_keeps_future_unsent(self):
        self.tracker["fail_decision_call"] = 2
        status = self.advance_one()
        self.assertEqual("STOP_VERSIONED_CONTENT_REPAIR_REQUIRED",
                         status["dispatchStatus"])
        # Both roles returned a scored verdict; complete is NOT consensus PASS.
        self.assertEqual(1, status["activitiesFullyModelReviewed"])
        self.assertEqual(1, status["activitiesAssessedRows"])
        self.assertEqual(0, status["modelConsensusPassActivities"])
        for _ in range(3):
            self.assertEqual("STOP_VERSIONED_CONTENT_REPAIR_REQUIRED",
                             self.advance_one()["dispatchStatus"])
        self.assertEqual(2, len(self.tracker["calls"]))

    def test_power_loss_after_inflight_claim_stops_before_new_api_calls(self):
        self.tracker["crash_call"] = 1
        with self.assertRaises(KeyboardInterrupt):
            self.advance_one()
        self.assertEqual(1,len(self.tracker["calls"]))
        self.assertEqual(2,len(self.tracker["clients"]))
        self.assertTrue(all(c.closed==1 for c in self.tracker["clients"]))
        raw=(self.chapter/"section-7-1"/"package.json").read_bytes()
        run_dir=self.private/("v3-generated-"+sha256(raw).hexdigest())
        self.assertFalse((run_dir/".active-review.lock").exists())
        claims=list((run_dir/"batches").glob("v3-review-*.json"))
        self.assertEqual(1,len(claims))
        self.assertEqual("IN_FLIGHT",json.loads(
            claims[0].read_text(encoding="utf8"))["state"])
        # Never create new Gemini clients while a prior claim has no
        # reconciled assessment aggregate after process interruption.
        self.assertEqual("STOP_UNRECONCILED_MODEL_REVIEW",
                         self.status()["dispatchStatus"])
        self.tracker.pop("crash_call")
        for _ in range(3):
            self.assertEqual("STOP_UNRECONCILED_MODEL_REVIEW",
                             self.advance_one()["dispatchStatus"])
        self.assertEqual(1,len(self.tracker["calls"]))

    def test_two_simultaneous_workers_do_not_duplicate_inflight_request(self):
        from threading import Event, Thread
        started, release = Event(), Event()
        self.tracker["pause_first"] = (started, release)
        results = []
        errors = []
        def run_first():
            try:
                results.append(self.advance_one())
            except BaseException as exc:
                errors.append(type(exc).__name__)
        worker = Thread(target=run_first, daemon=True)
        worker.start()
        try:
            self.assertTrue(started.wait(10), "first worker never reached SDK")
            # The first worker has a lock and an immutable IN_FLIGHT claim.
            # The second must not even construct a fresh SDK client.
            second = self.advance_one()
            self.assertEqual("STOP_UNRECONCILED_MODEL_REVIEW",
                             second["dispatchStatus"])
            self.assertEqual(2,len(self.tracker["clients"]))
            self.assertEqual(1,len(self.tracker["calls"]))
        finally:
            release.set()
            worker.join(timeout=15)
            self.tracker.pop("pause_first",None)
        self.assertFalse(worker.is_alive(), "first worker did not finish")
        self.assertEqual([],errors)
        self.assertEqual(1,len(results))
        self.assertEqual(1,results[0]["activitiesFullyModelReviewed"])
        self.assertEqual(2,len(self.tracker["calls"]))
        self.assertEqual(1,self.status()["activitiesFullyModelReviewed"])

    def test_provider_fault_matrix_never_retries_or_exposes_secrets(self):
        for mode in ("401", "429", "503", "malformed", "empty"):
            self.tracker = {"calls":[],"clients":[],"fail_mode":mode}
            self.private = Path(self.temp.name)/("private-fault-"+mode)
            with self.subTest(mode=mode):
                result=self.advance_one()
                self.assertEqual("STOP_UNRECONCILED_MODEL_REVIEW",
                                 result["dispatchStatus"])
                self.assertEqual(0,result["activitiesFullyModelReviewed"])
                self.assertEqual(1,result["activitiesAssessedRows"])
                self.assertEqual(2,len(self.tracker["calls"]))
                for _ in range(2):
                    self.assertEqual("STOP_UNRECONCILED_MODEL_REVIEW",
                                     self.advance_one()["dispatchStatus"])
                self.assertEqual(2,len(self.tracker["calls"]))
                self.assertTrue(all(c.closed==1 for c in
                                    self.tracker["clients"]))
                for row in self.private.rglob("*.json"):
                    self.assertNotIn("SYNTHETIC_PRIVATE_SECRET_DO_NOT_LOG",
                        row.read_text(encoding="utf8"))

    def test_orphan_lock_blocks_without_any_model_call(self):
        raw = (self.chapter/"section-7-1"/"package.json").read_bytes()
        run_dir = self.private/("v3-generated-"+sha256(raw).hexdigest())
        run_dir.mkdir(parents=True)
        lock = run_dir/".active-review.lock"
        lock.write_text("synthetic-other-owner", encoding="utf8")
        with self.assertRaisesRegex(ValueError,
                                    "V3_REVIEW_RUN_OWNERSHIP_UNCERTAIN"):
            self.advance_one()
        self.assertEqual([], self.tracker["calls"])
        self.assertEqual("synthetic-other-owner", lock.read_text(encoding="utf8"))
        lock.unlink()
        self.assertEqual(1, self.advance_one()["activitiesFullyModelReviewed"])
        self.assertEqual(2, len(self.tracker["calls"]))

    def test_cached_provider_tamper_detected_before_new_calls(self):
        self.assertEqual(1, self.advance_one()["activitiesFullyModelReviewed"])
        raw = (self.chapter/"section-7-1"/"package.json").read_bytes()
        digest = sha256(raw).hexdigest()
        checkpoint = self.private/("v3-generated-"+digest)/"batches"/(
            "v3-assessment-"+digest+".json")
        record = json.loads(checkpoint.read_text(encoding="utf8"))
        record["reviews"][0]["reviewers"][0]["providerId"] = "chatgpt_browser"
        checkpoint.write_text(json.dumps(record), encoding="utf8")
        with self.assertRaisesRegex(ValueError, "V3_GEMINI_ONLY_EVIDENCE_REQUIRED"):
            self.status()
        with self.assertRaisesRegex(ValueError, "V3_GEMINI_ONLY_EVIDENCE_REQUIRED"):
            self.advance_one()
        self.assertEqual(2, len(self.tracker["calls"]))

    def test_frozen_package_change_detected_before_new_calls(self):
        selected = self.chapter/"section-7-3"/"package.json"
        selected.write_bytes(selected.read_bytes()+b" ")
        with self.assertRaisesRegex(ValueError, "V3_FROZEN"):
            self.advance_one()
        self.assertEqual([], self.tracker["calls"])
        self.assertFalse(self.private.exists())

    def test_future_orphan_role_claim_stops_before_sdk_construction(self):
        raw = (self.chapter / "section-7-1" / "package.json").read_bytes()
        digest = sha256(raw).hexdigest()
        batches = self.private / ("v3-generated-" + digest) / "batches"
        batches.mkdir(parents=True)
        future = batches / f"v3-review-{digest[:12]}-005-0.json"
        future.write_text(json.dumps({"state": "IN_FLIGHT"}), encoding="utf8")
        with self.assertRaisesRegex(ValueError, "V3_OUT_OF_ORDER_ROLE_CLAIM"):
            self.advance_one()
        self.assertEqual([], self.tracker["calls"])
        self.assertEqual([], self.tracker["clients"])
        self.assertTrue(future.exists())  # no destructive reconciliation

    def test_malformed_orphan_claim_filename_is_not_ignored(self):
        raw = (self.chapter / "section-7-1" / "package.json").read_bytes()
        digest = sha256(raw).hexdigest()
        batches = self.private / ("v3-generated-" + digest) / "batches"
        batches.mkdir(parents=True)
        invalid = batches / f"v3-review-{digest[:12]}-999-0.json"
        invalid.write_text("{}", encoding="utf8")
        with self.assertRaisesRegex(ValueError, "V3_INVALID_ORPHAN_ROLE_CLAIM"):
            self.advance_one()
        self.assertEqual([], self.tracker["clients"])


if __name__ == "__main__":
    unittest.main()

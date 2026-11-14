"""Source-free no-replay isolation and provider-capacity circuit regressions."""
from __future__ import annotations

import json
import os
from pathlib import Path
import tempfile
import time
import unittest
from types import SimpleNamespace

from app_generator.runtime.v3_course_review import (
    plan_v3_course_review, advance_v3_course_review,
)
from app_generator.validation.v3_server_error_recovery import (
    provider_capacity_gate, COOLDOWN_SECONDS, BURST_WINDOW_SECONDS,
)
from tests.test_v3_course_review_dispatch import synthetic_course
from tests.test_v3_authorized_execution_bridge import pair


class ServerError(Exception):
    pass


class FaultReviewer:
    def __init__(self):
        self.calls = 0

    def ask(self, prompt, *, stage=None):
        self.calls += 1
        raise ServerError("SYNTHETIC_SECRET_NEVER_LOG")


class V3ServerRecoveryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        base = Path(self.temp.name)
        self.repo = base / "repo"
        self.chapter = synthetic_course(self.repo, n=6, activities=2)
        self.private = base / "private"

    def run_fault(self):
        sessions, good_a, good_b = pair()
        failed = FaultReviewer()
        bad = SimpleNamespace(
            reviewer_id=sessions[0].reviewer_id,
            session_id=sessions[0].session_id,
            provider_id=sessions[0].provider_id,
            conversation=failed,
        )
        result = advance_v3_course_review(
            self.chapter, self.repo, private_root=self.private,
            sessions=(bad, sessions[1]),
            generated_content_transfer_allowed=True, max_activities=1,
            continue_independent=True,
        )
        self.assertEqual(1, failed.calls)
        self.assertEqual(1, good_b.calls)
        self.assertEqual(0, good_a.calls)
        return result

    def plan(self):
        return plan_v3_course_review(
            self.chapter, self.repo, private_root=self.private,
            continue_independent=True,
        )

    def claims(self):
        return list(self.private.glob("v3-generated-*/batches/v3-review-*.json"))

    def make_claims_old(self, *, seconds=COOLDOWN_SECONDS + 120):
        for p in self.claims():
            if json.loads(p.read_text(encoding="utf8")).get("reasonCode") == "ServerError":
                old = time.time() - seconds
                os.utime(p, (old, old))

    def test_realistic_server_error_quarantines_section_preserving_checkpoint(self):
        result = self.run_fault()
        self.assertEqual("WAIT_PROVIDER_COOLDOWN", result["dispatchStatus"])
        self.assertEqual("section-7-2", result["nextSection"])
        self.assertEqual(["section-7-1"], result["quarantinedSections"])
        self.assertEqual(1, result["modelUncertainActivities"])
        self.assertEqual(0, result["activitiesFullyModelReviewed"])
        self.assertFalse(result["publicationAuthorized"])
        self.assertEqual("STOP_UNRECONCILED_MODEL_REVIEW",
                         plan_v3_course_review(self.chapter, self.repo,
                               private_root=self.private)["dispatchStatus"])
        self.assertEqual(2, len(self.claims()))
        self.assertEqual({"AMBIGUOUS", "COMPLETE"}, {
            json.loads(p.read_text(encoding="utf8"))["state"]
            for p in self.claims()})
        self.make_claims_old()
        resumed = self.plan()
        self.assertEqual("READY_FOR_AUTHORIZED_REVIEW_SESSIONS",
                         resumed["dispatchStatus"])
        self.assertEqual("section-7-2", resumed["nextSection"])
        sessions, a, b = pair()
        completed = advance_v3_course_review(
            self.chapter, self.repo, private_root=self.private,
            sessions=sessions, generated_content_transfer_allowed=True,
            max_activities=1, continue_independent=True)
        self.assertEqual("section-7-2", completed["selectedSection"])
        self.assertEqual((1, 1), (a.calls, b.calls))
        self.assertEqual(1, completed["modelUncertainActivities"])
        self.assertEqual(1, completed["activitiesFullyModelReviewed"])
        self.assertFalse(completed["publicationAuthorized"])
        self.assertEqual(4, len(self.claims()))
        self.assertEqual(1, sum(
            json.loads(p.read_text(encoding="utf8"))["state"] == "AMBIGUOUS"
            for p in self.claims()))

    def test_cooldown_refuses_to_construct_new_model_sessions(self):
        self.run_fault()
        sessions, a, b = pair()
        outcome = advance_v3_course_review(
            self.chapter, self.repo, private_root=self.private,
            sessions=sessions, generated_content_transfer_allowed=True,
            max_activities=1, continue_independent=True)
        self.assertEqual("WAIT_PROVIDER_COOLDOWN", outcome["dispatchStatus"])
        self.assertEqual((0, 0), (a.calls, b.calls))
        self.assertEqual(2, len(self.claims()))

    def test_two_recent_server_failures_open_rolling_circuit(self):
        self.run_fault()
        self.make_claims_old(seconds=COOLDOWN_SECONDS+120)
        second = self.run_fault()
        self.assertEqual("STOP_PROVIDER_CIRCUIT_OPEN", second["dispatchStatus"])
        self.assertEqual(["section-7-1","section-7-2"],second["quarantinedSections"])
        self.assertEqual("section-7-3",second["nextSection"])
        sessions,a,b = pair()
        stopped = advance_v3_course_review(
            self.chapter,self.repo,private_root=self.private,
            sessions=sessions,generated_content_transfer_allowed=True,
            max_activities=1,continue_independent=True)
        self.assertEqual("STOP_PROVIDER_CIRCUIT_OPEN",stopped["dispatchStatus"])
        self.assertEqual((0,0),(a.calls,b.calls))
        self.assertEqual(2,stopped["modelUncertainActivities"])

    def test_non_server_error_is_quarantined_without_false_provider_circuit(self):
        from app_generator.errors import UiContractError
        class UIError:
            def ask(self,prompt,*,stage=None):
                raise UiContractError("SYNTHETIC")
        sessions,a,b = pair()
        bad = SimpleNamespace(
            reviewer_id=sessions[0].reviewer_id,
            session_id=sessions[0].session_id,
            provider_id=sessions[0].provider_id,
            conversation=UIError())
        advance_v3_course_review(
            self.chapter,self.repo,private_root=self.private,
            sessions=(bad,sessions[1]),
            generated_content_transfer_allowed=True,max_activities=1)
        state=self.plan()
        self.assertEqual(["section-7-1"], state["quarantinedSections"])
        self.assertEqual("section-7-2",state["nextSection"])
        self.assertEqual("READY_FOR_AUTHORIZED_REVIEW_SESSIONS",state["dispatchStatus"])

    def test_quarantine_never_fabricates_global_completion(self):
        self.run_fault()
        self.make_claims_old()
        # Complete every eligible section; the quarantined section is untouched.
        for _ in range(10):
            sessions,a,b=pair()
            advance_v3_course_review(
                self.chapter,self.repo,private_root=self.private,
                sessions=sessions,generated_content_transfer_allowed=True,
                max_activities=1,continue_independent=True)
        result=self.plan()
        self.assertEqual("STOP_UNRECONCILED_MODEL_REVIEW",result["dispatchStatus"])
        self.assertEqual(10,result["activitiesFullyModelReviewed"])
        self.assertEqual(1,result["modelUncertainActivities"])
        self.assertEqual(0,result["modelConsensusPassActivities"]-10)
        self.assertFalse(result["publicationAuthorized"])


    def test_live_or_orphaned_review_lock_blocks_all_new_sections(self):
        self.run_fault()
        self.make_claims_old()
        lock_dir = next(self.private.glob("v3-generated-*"))
        lock = lock_dir / ".active-review.lock"
        lock.write_text("synthetic-other-worker", encoding="utf8")
        sessions,a,b = pair()
        blocked = advance_v3_course_review(
            self.chapter, self.repo, private_root=self.private,
            sessions=sessions, generated_content_transfer_allowed=True,
            max_activities=1, continue_independent=True)
        self.assertEqual("STOP_ACTIVE_REVIEW_OWNERSHIP_UNCERTAIN",
                         blocked["dispatchStatus"])
        self.assertEqual((0,0),(a.calls,b.calls))
        self.assertEqual("synthetic-other-worker",
                         lock.read_text(encoding="utf8"))
        lock.unlink()  # remove only our disposable test lock
        self.assertEqual("section-7-2",self.plan()["nextSection"])
        self.assertEqual("READY_FOR_AUTHORIZED_REVIEW_SESSIONS",
                         self.plan()["dispatchStatus"])

    def test_future_timestamp_quarantine_fails_closed(self):
        self.run_fault()
        for p in self.claims():
            if json.loads(p.read_text(encoding="utf8")).get("reasonCode") == "ServerError":
                future=time.time()+600
                os.utime(p,(future,future))
        with self.assertRaisesRegex(ValueError,
                "V3_PROVIDER_CAPACITY_FUTURE_TIMESTAMP"):
            self.plan()


if __name__ == "__main__":
    unittest.main()

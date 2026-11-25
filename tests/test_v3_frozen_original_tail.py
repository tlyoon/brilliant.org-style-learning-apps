"""No-network end-to-end V3 original-tail queue tests.

Protected earlier ambiguous physics role is never retried. Other originally
UNREVIEWED frozen activities can receive distinct deterministic slice reviews
using the existing scientific rubric. Synthetic verdicts are not real Gemini.
"""
from __future__ import annotations

from hashlib import sha256
from contextlib import redirect_stdout
import io
import json
import os
from pathlib import Path
import shutil
import tempfile
import time
import unittest
from unittest.mock import patch

from app_generator.runtime.run_context import RunContext
from app_generator.runtime.v3_authorized_review import advance_v3_generated_text
from app_generator.runtime.v3_frozen_original_tail import (
    plan_frozen_original_tail, stage_frozen_original_tail_slice,
    reserve_frozen_original_tail_attempt,
)
from app_generator.runtime.v3_frozen_tail_forward import (
    advance_frozen_tail_until_boundary,
)
from app_generator.validation.autonomous_completion import (
    assess_with_models, package_identity,
)
from tests.test_v3_authorized_execution_bridge import FakeReviewer, pair
from tests.test_v3_course_review_dispatch import synthetic_course


class UnconfirmedSixthReviewer(FakeReviewer):
    def ask(self, prompt, *, stage=None):
        self.calls += 1
        if self.calls == 6:
            raise TimeoutError("SYNTHETIC_UNCONFIRMED_NO_REPLAY")
        self.calls -= 1
        return super().ask(prompt, stage=stage)


class FrozenOriginalIndependentTailTests(unittest.TestCase):
    def setUp(self):
        t=tempfile.TemporaryDirectory()
        self.addCleanup(t.cleanup)
        self.home=Path(t.name)
        self.repo=self.home/"repo"
        self.course=synthetic_course(self.repo,n=6,activities=18)
        self.section="section-7-6"
        self.private=self.home/"private"
        self.source=(self.course/self.section/"package.json").read_bytes()
        self.digest,self.items=package_identity(self.source)
        cp=RunContext.create(self.private,"v3-generated-"+self.digest)
        fake_a=UnconfirmedSixthReviewer()
        fake_b=FakeReviewer()
        from types import SimpleNamespace
        sessions=(
            SimpleNamespace(reviewer_id="physics",session_id="physics-s",
                            provider_id="gemini_api",conversation=fake_a),
            SimpleNamespace(reviewer_id="semantics",session_id="semantic-s",
                            provider_id="gemini_api",conversation=fake_b),
        )
        report=assess_with_models(
            self.source,sessions,checkpoint=cp,
            generated_content_transfer_allowed=True,max_activities=6)
        self.assertEqual(len(report["reviews"]),6)
        self.assertEqual([r["status"] for r in report["reviews"]],
                         ["AI_CONSENSUS_PASS"]*5+["AI_UNCERTAIN"])

    def plan(self):
        return plan_frozen_original_tail(
            self.course,self.repo,self.private,section=self.section)

    def stage(self,index=6):
        return stage_frozen_original_tail_slice(
            self.course,self.repo,self.private,
            section=self.section,index=index)

    def test_readonly_plan_keeps_ambiguous_and_finds_twelve_untouched(self):
        old=self.source
        p=self.plan()
        self.assertEqual(p["status"],
                         "READY_FOR_AUTHORIZED_FROZEN_ORIGINAL_TAIL_REVIEW")
        self.assertEqual(p["next"]["index"],6)
        self.assertEqual(p["supplemental"]["eligible"],12)
        self.assertEqual(p["originalAssessedUnchanged"],6)
        self.assertEqual(p["originalModelConsensusPassesUnchanged"],5)
        self.assertFalse((self.private/"frozen-original-review-slices").exists())
        self.assertFalse(p["publicationAuthorized"])
        self.assertEqual((self.course/self.section/"package.json").read_bytes(),old)

    def test_immutable_slice_is_original_and_idempotent(self):
        raw,meta=self.stage()
        sha,items=package_identity(raw)
        self.assertEqual(sha,meta["slicePackageSha256"])
        self.assertEqual(items,[self.items[6]])
        self.assertEqual(meta["sourcePackageSha256"],self.digest)
        self.assertEqual(meta["originalActivitySha256"],sha256(
            json.dumps(self.items[6],sort_keys=True,ensure_ascii=False,
                       separators=(",",":")).encode("utf8")).hexdigest())
        self.assertEqual(self.stage(),(raw,meta))
        staged=(self.private/"frozen-original-review-slices"/sha)
        self.assertTrue((staged/"package.json").is_file())
        self.assertTrue((staged/"review-slice.json").is_file())

    def test_reserved_attempt_cannot_be_submitted_twice_and_skips_forward(self):
        _,meta=self.stage()
        reserve_frozen_original_tail_attempt(
            self.private,source_sha=self.digest,index=6,
            slice_sha=meta["slicePackageSha256"])
        with self.assertRaisesRegex(ValueError,"NO_REPLAY"):
            reserve_frozen_original_tail_attempt(
                self.private,source_sha=self.digest,index=6,
                slice_sha=meta["slicePackageSha256"])
        state=self.plan()
        self.assertEqual(state["next"]["index"],7)
        self.assertEqual(state["supplemental"]["reserved"],1)
        self.assertEqual(state["supplemental"]["eligible"],11)
        with self.assertRaisesRegex(ValueError,"NO_REPLAY"):
            self.stage(6)

    def test_normal_checkpoint_reviewer_completed_tail_is_separate_from_original(self):
        raw,meta=self.stage(6)
        reserve_frozen_original_tail_attempt(
            self.private,source_sha=self.digest,index=6,
            slice_sha=meta["slicePackageSha256"])
        sessions,first,second=pair()
        result=advance_v3_generated_text(
            raw,sessions,private_root=self.private,
            generated_content_transfer_allowed=True,max_activities=1)
        self.assertEqual(result["modelConsensusPassActivities"],1)
        self.assertEqual((first.calls,second.calls),(1,1))
        state=self.plan()
        self.assertEqual(state["supplemental"]["passed"],1)
        self.assertEqual(state["next"]["index"],7)
        self.assertEqual(state["originalAssessedUnchanged"],6)
        self.assertEqual(state["originalModelConsensusPassesUnchanged"],5)
        self.assertEqual((self.course/self.section/"package.json").read_bytes(),
                         self.source)
        with self.assertRaisesRegex(ValueError,"NO_REPLAY"):
            self.stage(6)
        self.assertFalse(state["publicationAuthorized"])

    def test_historical_unknown_provider_claim_is_not_recovered_or_rewritten(self):
        before=self.plan()
        old=(self.private/("v3-generated-"+self.digest)/"batches"
             /f"v3-review-{self.digest[:12]}-005-0.json")
        self.assertEqual(json.loads(old.read_text())["state"],"AMBIGUOUS")
        self.stage(6)
        after=self.plan()
        self.assertEqual(before["next"]["index"],after["next"]["index"])
        self.assertEqual(json.loads(old.read_text())["state"],"AMBIGUOUS")
        self.assertFalse(old.with_suffix(".response.txt").exists())

    def test_source_changed_or_foreign_role_rejects_tail(self):
        orig=self.source
        data=json.loads(orig)
        data["activities"][6]["prompt"]["en"]="SYNTHETIC altered"
        (self.course/self.section/"package.json").write_text(
            json.dumps(data),encoding="utf8")
        with self.assertRaises(ValueError):
            self.plan()

    def test_exact_old_full_role_for_unreviewed_index_is_not_resubmitted(self):
        base=self.private/("v3-generated-"+self.digest)/"batches"
        role=base/f"v3-review-{self.digest[:12]}-006-0.json"
        role.write_text("{}",encoding="utf8")
        # The independent queue cannot bypass the existing original-course
        # role-claim validator: malformed/out-of-order claims fail CLOSED.
        with self.assertRaisesRegex(ValueError,"V3_INVALID_ORPHAN_ROLE_CLAIM"):
            self.plan()

    def test_original_uncertain_absent_prevents_tail_work(self):
        base=self.private/("v3-generated-"+self.digest)/"batches"
        report_file=base/("v3-assessment-"+self.digest+".json")
        report=json.loads(report_file.read_text())
        report["reviews"].pop()
        report_file.write_text(json.dumps(report),encoding="utf8")
        with self.assertRaises(ValueError):
            self.plan()



    def test_finite_normal_tail_controller_advances_four_real_checkpoint_rows(self):
        calls=[]
        def reviewer(raw, manifest):
            sessions,a,b=pair()
            result=advance_v3_generated_text(
                raw,sessions,private_root=self.private,
                generated_content_transfer_allowed=True,max_activities=1)
            calls.append((manifest["sourceActivityIndex"],a.calls,b.calls))
            return result
        report=advance_frozen_tail_until_boundary(
            self.course,self.repo,self.private,reviewer,
            section=self.section,max_activities=4,max_elapsed_seconds=900)
        self.assertEqual(report["status"],"STOP_TAIL_ACTIVITY_BUDGET_REACHED")
        self.assertEqual(report["verifiedNewSupplementalRowsThisInvocation"],4)
        self.assertEqual(report["supplemental"]["passed"],4)
        self.assertEqual(report["nextOriginalIndex"],10)
        self.assertEqual(calls,[(i,1,1) for i in range(6,10)])
        self.assertEqual(report["originalAssessedUnchanged"],6)
        self.assertEqual(report["originalModelConsensusPassesUnchanged"],5)
        self.assertFalse(report["publicationAuthorized"])

    def test_failure_after_persistent_reservation_never_replays_on_resume(self):
        calls=[]
        def fault(_raw,manifest):
            calls.append(manifest["sourceActivityIndex"])
            raise TimeoutError("SYNTHETIC_REQUEST_MAY_HAVE_BEEN_SUBMITTED")
        first=advance_frozen_tail_until_boundary(
            self.course,self.repo,self.private,fault,
            section=self.section,max_activities=4)
        self.assertEqual(first["status"],"STOP_TAIL_WORKER_EXCEPTION_NO_REPLAY")
        self.assertEqual(first["attemptedThisInvocation"],1)
        self.assertEqual(first["verifiedNewSupplementalRowsThisInvocation"],0)
        self.assertEqual(self.plan()["next"]["index"],7)
        seen=[]
        def review(raw,manifest):
            sessions,a,b=pair()
            seen.append(manifest["sourceActivityIndex"])
            return advance_v3_generated_text(
                raw,sessions,private_root=self.private,
                generated_content_transfer_allowed=True,max_activities=1)
        second=advance_frozen_tail_until_boundary(
            self.course,self.repo,self.private,review,
            section=self.section,max_activities=2)
        # Unlike an independently proven local parser fault, this callback
        # exception may have reached Google; source-free evidence cannot
        # establish its delivery. Preserve the reservation and stop globally.
        self.assertEqual(second["status"],
                         "STOP_TAIL_UNCONFIRMED_PRIOR_ATTEMPT")
        self.assertEqual(second["supplemental"]["reserved"],1)
        self.assertEqual(second["supplemental"]["passed"],0)
        self.assertEqual(seen,[])
        self.assertEqual(calls,[6])
        self.assertEqual(second["nextOriginalIndex"],7)

    def test_no_checkpoint_result_cannot_count_as_review(self):
        called=[]
        def fake_return(_raw,manifest):
            called.append(manifest["sourceActivityIndex"])
            return {"modelConsensusPassActivities":1,
                    "publicationAuthorized":True}  # ignored, NOT real evidence
        result=advance_frozen_tail_until_boundary(
            self.course,self.repo,self.private,fake_return,
            section=self.section,max_activities=3)
        self.assertEqual(result["status"],
                         "STOP_TAIL_PRE_CALL_WITHOUT_VERIFIED_RESULT_NO_REPLAY")
        self.assertEqual(result["attemptedThisInvocation"],1)
        self.assertEqual(result["verifiedNewSupplementalRowsThisInvocation"],0)
        self.assertEqual(self.plan()["next"]["index"],7)
        self.assertEqual(called,[6])
        self.assertFalse(result["publicationAuthorized"])

    def test_elapsed_budget_prevents_any_reservation_or_model_call(self):
        calls=[]
        result=advance_frozen_tail_until_boundary(
            self.course,self.repo,self.private,
            lambda *_: calls.append("FORBIDDEN"),
            section=self.section,max_activities=4,max_elapsed_seconds=30,
            monotonic=iter((0,31)).__next__)
        self.assertEqual(result["status"],"STOP_TAIL_ELAPSED_BUDGET")
        self.assertEqual(result["attemptedThisInvocation"],0)
        self.assertEqual(calls,[])
        self.assertEqual(self.plan()["supplemental"]["eligible"],12)


    def _normal_worker_fixture(self):
        """Rename the fully frozen synthetic Chapter 7 to a Chapter 9 copy."""
        chapter9=self.repo/"content"/"chapter-9"
        self.course.rename(chapter9)
        for i in range(1,7):
            (chapter9/f"section-7-{i}").rename(chapter9/f"section-9-{i}")
        old=self.repo/"docs"/"acceptance_closure_chapter7.json"
        charter=json.loads(old.read_text(encoding="utf8"))
        for i,row in enumerate(charter["frozenCandidates"],1):
            row["section"]=f"9.{i}"
        (self.repo/"docs"/"acceptance_closure_chapter9.json").write_text(
            json.dumps(charter),encoding="utf8")
        old.unlink()
        local=self.home/"LocalAppData"
        private=local/"Microvid"/"BoslaFakeOriginalTail"
        private.parent.mkdir(parents=True,exist_ok=True)
        shutil.copytree(self.private,private)
        self.assertEqual(plan_frozen_original_tail(
            chapter9,self.repo,private,section="section-9-6")["next"]["index"],6)
        return chapter9,local,private

    def _set_synthetic_sixth_failure_to_cooled_servererror(self,private):
        # TEMP synthetic fixture only. An historical ServerError with fully
        # expired cooldown permits a *new* original activity. Never adjust
        # real owner claims, and retain unknown ValueError as a global STOP.
        batches=(private/("v3-generated-"+self.digest)/"batches")
        role=batches/f"v3-review-{self.digest[:12]}-005-0.json"
        row=json.loads(role.read_text(encoding="utf8"))
        self.assertEqual(row["state"],"AMBIGUOUS")
        row["reasonCode"]="ServerError"
        role.write_text(json.dumps(row),encoding="utf8")
        report=batches/("v3-assessment-"+self.digest+".json")
        payload=json.loads(report.read_text(encoding="utf8"))
        payload["reviews"][5]["reviewers"][0]["reasonCode"]="ServerError"
        report.write_text(json.dumps(payload),encoding="utf8")
        old=time.time()-4000
        os.utime(role,(old,old))

    def test_actual_yoga6_normal_worker_auto_advance_fallback_fake_sdk(self):
        # This is the SAME normal paid entrypoint using the genuine
        # authorization validator, but Google SDK/network/host are stubbed.
        from scripts import run_v3_yoga6_recovery_worker as worker
        from app_generator.gemini.v3_native_api_reviewers import (
            V3NativeGeminiApiSessions,
        )
        from app_generator.gemini import v3_native_api_reviewers as sdk_module
        from tests.test_v3_native_gemini_api_reviewers import (
            FakeClient, FakeTypes, config,
        )
        chapter,local,private=self._normal_worker_fixture()
        self._set_synthetic_sixth_failure_to_cooled_servererror(private)
        clients=[]
        def fake_session_factory(configured, **kwargs):
            def client_for(role):
                client=FakeClient("valid")
                clients.append(client)
                return client
            return V3NativeGeminiApiSessions(
                configured, sdk_client_factory=client_for,
                sdk_types=FakeTypes, **kwargs)
        stopped={
            "dispatchStatus":"STOP_VERSIONED_CONTENT_REPAIR_REQUIRED",
            "quarantinedSections":["section-9-1","section-9-2","section-9-6"],
            "publicationAuthorized":False,
        }
        output=io.StringIO()
        from app_generator.runtime import native_sdk_environment
        with (patch.dict(os.environ,{"LOCALAPPDATA":str(local)}),
              patch.object(worker,"ROOT",self.repo),
              patch.object(worker,"COURSE",chapter),
              patch.object(worker,"plan_v3_course_review",
                           return_value=stopped),
              patch.object(worker,"require_authorized_native_review_host"),
              patch.object(native_sdk_environment,
                           "delegate_to_supported_sdk",return_value=None),
              patch.object(worker,"_load_native_config",return_value=config()),
              patch.object(worker,"diagnose_model_metadata",
                           return_value={"status":"READY_SOURCE_FREE_ONLY",
                                         "selectedCandidateIndex":0}),
              patch.object(sdk_module,"V3NativeGeminiApiSessions",
                           side_effect=fake_session_factory),
              redirect_stdout(output)):
            exit_code=worker.main([
                "--private-root",str(private),
                "--auto-advance","--execute","--allow-generated-text-transfer",
                "--max-forward-activities","2","--max-forward-seconds","900",
            ])
        self.assertEqual(exit_code,0,output.getvalue())
        result=json.loads(output.getvalue())
        self.assertEqual(result["status"],"STOP_TAIL_ACTIVITY_BUDGET_REACHED")
        self.assertEqual(result["verifiedNewSupplementalRowsThisInvocation"],2)
        self.assertEqual(result["supplemental"]["passed"],2)
        self.assertEqual(result["nextOriginalIndex"],8)
        self.assertEqual(result["originalAssessedUnchanged"],6)
        self.assertFalse(result["publicationAuthorized"])
        self.assertEqual(len(clients),4)
        self.assertEqual([len(x.models.calls) for x in clients],[1,1,1,1])
        self.assertEqual((chapter/"section-9-6"/"package.json").read_bytes(),
                         self.source)

    def test_normal_worker_unknown_valueerror_globally_stops_before_sdk(self):
        # Mimics the ACTUAL Yoga6 old ambiguity: a provider-side ValueError
        # with no original raw response/request ID. Section9.6 index6 is new
        # and unchanged, but Decisions0040/41 still prohibit another call.
        from scripts import run_v3_yoga6_recovery_worker as worker
        from app_generator.runtime import native_sdk_environment
        chapter,local,private=self._normal_worker_fixture()
        prior=(private/("v3-generated-"+self.digest)/"batches"
               /f"v3-review-{self.digest[:12]}-005-0.json")
        record=json.loads(prior.read_text(encoding="utf8"))
        record["reasonCode"]="ValueError"
        prior.write_text(json.dumps(record),encoding="utf8")
        # Also retain matching original two-reviewer aggregate state.
        aggregate=(private/("v3-generated-"+self.digest)/"batches"
                   /("v3-assessment-"+self.digest+".json"))
        rows=json.loads(aggregate.read_text(encoding="utf8"))
        rows["reviews"][5]["reviewers"][0]["reasonCode"]="ValueError"
        aggregate.write_text(json.dumps(rows),encoding="utf8")
        stopped={
            "dispatchStatus":"STOP_VERSIONED_CONTENT_REPAIR_REQUIRED",
            "quarantinedSections":["section-9-6"],
            "publicationAuthorized":False,
        }
        output=io.StringIO()
        with (patch.dict(os.environ,{"LOCALAPPDATA":str(local)}),
              patch.object(worker,"ROOT",self.repo),
              patch.object(worker,"COURSE",chapter),
              patch.object(worker,"plan_v3_course_review",
                           return_value=stopped),
              patch.object(worker,"require_authorized_native_review_host"),
              patch.object(native_sdk_environment,
                           "delegate_to_supported_sdk") as bootstrap,
              patch.object(worker,"_load_native_config") as config_loader,
              patch.object(worker,"diagnose_model_metadata") as metadata,
              redirect_stdout(output)):
            code=worker.main([
                "--private-root",str(private),
                "--auto-advance","--execute","--allow-generated-text-transfer",
                "--max-forward-activities","2","--max-forward-seconds","900",
            ])
        self.assertEqual(code,3,output.getvalue())
        message=json.loads(output.getvalue())
        self.assertEqual(message["status"],
                         "STOP_TAIL_PROVIDER_CAPACITY_STOP_UNCLASSIFIED_PROVIDER_REVIEW")
        self.assertFalse(message["publicationAuthorized"])
        self.assertEqual(message["providerCapacity"]["serverErrorsLastHour"],0)
        bootstrap.assert_not_called()
        config_loader.assert_not_called()
        metadata.assert_not_called()
        self.assertEqual(json.loads(prior.read_text())["state"],"AMBIGUOUS")
        self.assertFalse((private/"frozen-original-review-attempts").exists())
        # BSA-187: the normal paid worker proactively completes independent
        # source-free preparation even when provider-wide no-replay STOPs.
        offline = message["sourceFreeRecovery"]
        self.assertEqual(offline["paidGeminiCalls"], 0)
        self.assertEqual(offline["stagedImmutableOriginalTailSlices"], 12)
        self.assertEqual(offline["providerCapacity"],
                         "STOP_UNCLASSIFIED_PROVIDER_REVIEW")
        self.assertEqual(len(list((private/"frozen-original-review-slices").iterdir())),12)
        self.assertFalse(offline["publicationAuthorized"])

    def test_normal_worker_paid_auth_denial_stops_before_any_claim(self):
        from scripts import run_v3_yoga6_recovery_worker as worker
        chapter,local,private=self._normal_worker_fixture()
        stopped={
            "dispatchStatus":"STOP_UNRECONCILED_MODEL_REVIEW",
            "quarantinedSections":["section-9-6"],
            "publicationAuthorized":False,
        }
        output=io.StringIO()
        with (patch.dict(os.environ,{"LOCALAPPDATA":str(local)}),
              patch.object(worker,"ROOT",self.repo),
              patch.object(worker,"COURSE",chapter),
              patch.object(worker,"plan_v3_course_review",
                           return_value=stopped),
              patch.object(worker,"authorize_paid_v3_action",
                           side_effect=ValueError("SYNTHETIC_NOT_AUTHORIZED")),
              patch.object(worker,"require_authorized_native_review_host") as host,
              redirect_stdout(output)):
            exit_code=worker.main([
                "--private-root",str(private),
                "--auto-advance","--execute","--allow-generated-text-transfer",
                "--max-forward-activities","2","--max-forward-seconds","900",
            ])
        self.assertEqual(exit_code,3)
        self.assertEqual(json.loads(output.getvalue())["status"],
                         "STOP_YOGA6_RECOVERY_WORKER")
        host.assert_called_once()
        # Authorization denial prohibits MODEL transport but does not undo
        # independently permitted source-free package preparation.
        self.assertEqual(len(list(
            (private/"frozen-original-review-slices").iterdir())),12)
        self.assertFalse(
            (private/"frozen-original-review-attempts").exists())
        self.assertTrue(
            (private/"v3-source-free-forward-checkpoint.json").is_file())


    def test_supplemental_unknown_provider_fault_stops_next_original(self):
        # A failed slice is NOT in the frozen sectionProgress roster.
        # Earlier code skipped its unknown provider claim on restart.
        from types import SimpleNamespace
        from app_generator.validation.v3_course_readiness import course_readiness
        from app_generator.validation.v3_server_error_recovery import provider_capacity_gate

        raw, meta = self.stage(6)
        reserve_frozen_original_tail_attempt(
            self.private, source_sha=self.digest, index=6,
            slice_sha=meta["slicePackageSha256"])

        class Unclassified:
            def ask(self, prompt, *, stage=None):
                raise ValueError("SYNTHETIC_UNKNOWN_PROVIDER")

        sessions, _, _ = pair()
        failure = SimpleNamespace(
            reviewer_id=sessions[0].reviewer_id,
            session_id=sessions[0].session_id,
            provider_id=sessions[0].provider_id,
            conversation=Unclassified())
        review = advance_v3_generated_text(
            raw, (failure, sessions[1]), private_root=self.private,
            generated_content_transfer_allowed=True, max_activities=1)
        self.assertEqual(review["modelUncertainActivities"], 1)
        section_progress = course_readiness(
            self.course, self.repo, private_root=self.private)["sectionProgress"]
        # This tests the corrected provider gate directly, independent of SDK.
        check = provider_capacity_gate(
            self.private, section_progress,
            additional_package_shas=[meta["slicePackageSha256"]])
        self.assertEqual(check["status"], "STOP_UNCLASSIFIED_PROVIDER_REVIEW")
        unseen = []
        stopped = advance_frozen_tail_until_boundary(
            self.course, self.repo, self.private,
            lambda *_: unseen.append("FORBIDDEN"), section=self.section)
        self.assertEqual(stopped["status"],
                         "STOP_TAIL_SUPPLEMENTAL_PROVIDER_STOP_UNCLASSIFIED_PROVIDER_REVIEW")
        self.assertEqual(unseen, [])
        self.assertEqual(self.plan()["next"]["index"], 7)

    def test_orphan_precall_must_stop_new_slice_until_reconciled(self):
        _, meta = self.stage(6)
        reserve_frozen_original_tail_attempt(
            self.private, source_sha=self.digest, index=6,
            slice_sha=meta["slicePackageSha256"])
        unseen = []
        stopped = advance_frozen_tail_until_boundary(
            self.course, self.repo, self.private,
            lambda *_: unseen.append("FORBIDDEN"), section=self.section)
        self.assertEqual(stopped["status"],
                         "STOP_TAIL_UNCONFIRMED_PRIOR_ATTEMPT")
        self.assertEqual(unseen, [])
        self.assertEqual(self.plan()["next"]["index"], 7)

    def test_normal_worker_supplemental_provider_failure_stops_before_sdk(self):
        # Full normal Yoga6 entrypoint, cooled old original (independently
        # READY) but a previously attempted supplemental ValueError (unsafe).
        from types import SimpleNamespace
        from scripts import run_v3_yoga6_recovery_worker as worker
        from app_generator.runtime import native_sdk_environment

        chapter, local, private = self._normal_worker_fixture()
        self._set_synthetic_sixth_failure_to_cooled_servererror(private)
        raw, meta = stage_frozen_original_tail_slice(
            chapter, self.repo, private, section="section-9-6", index=6)
        reserve_frozen_original_tail_attempt(
            private, source_sha=self.digest, index=6,
            slice_sha=meta["slicePackageSha256"])

        class Unclassified:
            def ask(self, prompt, *, stage=None):
                raise ValueError("SYNTHETIC_UNKNOWN_GOOGLE_OUTCOME")

        reviewers, _, _ = pair()
        bad = SimpleNamespace(
            reviewer_id=reviewers[0].reviewer_id,
            session_id=reviewers[0].session_id,
            provider_id=reviewers[0].provider_id,
            conversation=Unclassified())
        advance_v3_generated_text(
            raw, (bad, reviewers[1]), private_root=private,
            generated_content_transfer_allowed=True, max_activities=1)
        old_plan = {
            "dispatchStatus": "STOP_VERSIONED_CONTENT_REPAIR_REQUIRED",
            "quarantinedSections": ["section-9-6"],
            "publicationAuthorized": False,
        }
        output = io.StringIO()
        with (patch.dict(os.environ, {"LOCALAPPDATA": str(local)}),
              patch.object(worker, "ROOT", self.repo),
              patch.object(worker, "COURSE", chapter),
              patch.object(worker, "plan_v3_course_review",
                           return_value=old_plan),
              patch.object(worker, "require_authorized_native_review_host"),
              patch.object(native_sdk_environment,
                           "delegate_to_supported_sdk") as bootstrap,
              patch.object(worker, "_load_native_config") as credential,
              patch.object(worker, "diagnose_model_metadata") as metadata,
              redirect_stdout(output)):
            code = worker.main([
                "--private-root", str(private),
                "--auto-advance", "--execute",
                "--allow-generated-text-transfer",
                "--max-forward-activities", "2",
            ])
        self.assertEqual(code, 3, output.getvalue())
        message = json.loads(output.getvalue())
        self.assertEqual(message["status"],
                         "STOP_TAIL_SUPPLEMENTAL_PROVIDER_STOP_UNCLASSIFIED_PROVIDER_REVIEW")
        self.assertFalse(message["publicationAuthorized"])
        self.assertEqual(message["sourceFreeRecovery"]
                         ["stagedImmutableOriginalTailSlices"], 11)
        self.assertEqual(message["sourceFreeRecovery"]["paidGeminiCalls"], 0)
        # A source-free receipt must reflect the *shared* provider circuit.
        # The original claims alone are READY; supplemental ValueError is not.
        self.assertEqual(
            message["sourceFreeRecovery"]["providerCapacity"],
            "STOP_TAIL_SUPPLEMENTAL_PROVIDER_STOP_UNCLASSIFIED_PROVIDER_REVIEW")
        self.assertEqual(
            message["sourceFreeRecovery"]["status"],
            "SOURCE_FREE_BOUNDARIES_STAGED_PROVIDER_STILL_BLOCKED")
        bootstrap.assert_not_called()
        credential.assert_not_called()
        metadata.assert_not_called()
        self.assertFalse(message["sourceFreeRecovery"]["publicationAuthorized"])
        self.assertEqual(plan_frozen_original_tail(
            chapter, self.repo, private,
            section="section-9-6")["next"]["index"], 7)

    def test_missing_captured_local_response_fails_closed_on_restart(self):
        from tests.test_autonomous_completion_v3 import FakeModel, sessions
        raw, meta = self.stage(6)
        reserve_frozen_original_tail_attempt(
            self.private, source_sha=self.digest, index=6,
            slice_sha=meta["slicePackageSha256"])
        advance_v3_generated_text(
            raw, sessions(FakeModel(malformed=True), FakeModel()),
            private_root=self.private, generated_content_transfer_allowed=True,
            max_activities=1)
        self.assertEqual(self.plan()["rows"][0]["state"],
                         "SUPPLEMENTAL_UNCERTAIN_NO_REPLAY")
        folder = (self.private / ("v3-generated-" + meta["slicePackageSha256"])
                  / "batches")
        digest = meta["slicePackageSha256"]
        claim_files = sorted(folder.glob(
            f"v3-review-{digest[:12]}-000-*.json"))
        local_failure_claims = [
            file for file in claim_files
            if json.loads(file.read_text(encoding="utf8")).get("state")
            in {"PARSE_FAILED", "RUBRIC_FAILED"}
        ]
        # Locate the exact failed role by its immutable claim, never by
        # glob iteration order (which differs on Windows and Linux CI).
        self.assertEqual(len(local_failure_claims), 1)
        capture = local_failure_claims[0].with_suffix(".response.txt")
        self.assertTrue(capture.is_file())
        # Test-only deletion in a disposable private fixture; never alter
        # owner-owned immutable original or real provider evidence.
        capture.unlink()
        called = []
        stopped = advance_frozen_tail_until_boundary(
            self.course, self.repo, self.private,
            lambda *_: called.append("FORBIDDEN"), section=self.section)
        self.assertEqual(stopped["status"],
                         "STOP_TAIL_UNVERIFIED_SUPPLEMENTAL_UNCERTAINTY")
        self.assertEqual(called, [])

    def test_verified_local_capture_can_continue_on_restart(self):
        from tests.test_autonomous_completion_v3 import FakeModel, sessions
        raw, meta = self.stage(6)
        reserve_frozen_original_tail_attempt(
            self.private, source_sha=self.digest, index=6,
            slice_sha=meta["slicePackageSha256"])
        advance_v3_generated_text(
            raw, sessions(FakeModel(malformed=True), FakeModel()),
            private_root=self.private, generated_content_transfer_allowed=True,
            max_activities=1)
        seen = []
        def valid_next(raw, manifest):
            seen.append(manifest["sourceActivityIndex"])
            pair = sessions(FakeModel(), FakeModel())
            return advance_v3_generated_text(
                raw, pair, private_root=self.private,
                generated_content_transfer_allowed=True, max_activities=1)
        progressed = advance_frozen_tail_until_boundary(
            self.course, self.repo, self.private, valid_next,
            section=self.section, max_activities=1)
        self.assertEqual(progressed["supplemental"]["uncertain"], 1)
        self.assertEqual(progressed["supplemental"]["passed"], 1)
        self.assertEqual(seen, [7])
        self.assertFalse(progressed["publicationAuthorized"])

    def test_ordinary_course_dispatcher_checks_supplemental_unknown(self):
        # Section 9.1 is independently eligible, yet an earlier frozen-tail
        # provider-wide unknown failure must prohibit a NEW model request.
        from types import SimpleNamespace
        from app_generator.runtime.v3_course_review import plan_v3_course_review
        chapter, local, private = self._normal_worker_fixture()
        self._set_synthetic_sixth_failure_to_cooled_servererror(private)
        raw, meta = stage_frozen_original_tail_slice(
            chapter, self.repo, private, section="section-9-6", index=6)
        reserve_frozen_original_tail_attempt(
            private, source_sha=self.digest, index=6,
            slice_sha=meta["slicePackageSha256"])

        class Unclassified:
            def ask(self, prompt, *, stage=None):
                raise ValueError("SYNTHETIC_UNCLASSIFIED_PROVIDER")

        pair_sessions, _, _ = pair()
        bad = SimpleNamespace(
            reviewer_id=pair_sessions[0].reviewer_id,
            session_id=pair_sessions[0].session_id,
            provider_id=pair_sessions[0].provider_id,
            conversation=Unclassified())
        advance_v3_generated_text(
            raw, (bad, pair_sessions[1]), private_root=private,
            generated_content_transfer_allowed=True, max_activities=1)
        plan = plan_v3_course_review(
            chapter, self.repo, private_root=private, continue_independent=True)
        self.assertEqual(plan["dispatchStatus"],
                         "STOP_TAIL_SUPPLEMENTAL_PROVIDER_STOP_UNCLASSIFIED_PROVIDER_REVIEW")
        self.assertFalse(plan["publicationAuthorized"])

    def test_normal_worker_source_free_advance_without_paid_authorization(self):
        from scripts import run_v3_yoga6_recovery_worker as worker
        from app_generator.runtime.v3_source_free_forward import (
            read_source_free_checkpoint,
        )
        chapter, local, private = self._normal_worker_fixture()
        before = (chapter/"section-9-6"/"package.json").read_bytes()
        original = (private/("v3-generated-"+self.digest)/"batches"
                    /f"v3-review-{self.digest[:12]}-005-0.json")
        claim_before = original.read_bytes()
        out = io.StringIO()
        with (patch.dict(os.environ, {"LOCALAPPDATA":str(local)}),
              patch.object(worker,"ROOT",self.repo),
              patch.object(worker,"COURSE",chapter),
              patch.object(worker,"require_authorized_native_review_host"),
              patch.object(worker,"_load_native_config") as credentials,
              patch.object(worker,"diagnose_model_metadata") as metadata,
              patch.object(worker.native,"main") as paid,
              redirect_stdout(out)):
            code=worker.main(["--private-root",str(private),
                              "--source-free-advance"])
        self.assertEqual(code,0,out.getvalue())
        result=json.loads(out.getvalue())
        self.assertEqual(result["status"],
                         "SOURCE_FREE_BOUNDARIES_STAGED_PROVIDER_STILL_BLOCKED")
        self.assertEqual(result["stagedImmutableOriginalTailSlices"],12)
        self.assertEqual(result["repairStatus"],"NO_SCRIPT_BLOCKER")
        self.assertEqual(result["paidGeminiCalls"],0)
        self.assertEqual(result["originalAssessedUnchanged"],6)
        self.assertFalse(result["publicationAuthorized"])
        self.assertFalse(result["versionedScopeAdmitted"])
        self.assertFalse((private/"frozen-original-review-attempts").exists())
        self.assertEqual(original.read_bytes(),claim_before)
        self.assertEqual((chapter/"section-9-6"/"package.json").read_bytes(),
                         before)
        self.assertEqual(read_source_free_checkpoint(private)
                         ["integritySha256"],result["checkpointIntegritySha256"])
        credentials.assert_not_called()
        metadata.assert_not_called()
        paid.assert_not_called()

        # Repeat normal source-free execution. Twelve immutable slices are
        # verified idempotently; no paid claim or duplicate model verdict.
        again=io.StringIO()
        with (patch.dict(os.environ, {"LOCALAPPDATA":str(local)}),
              patch.object(worker,"ROOT",self.repo),
              patch.object(worker,"COURSE",chapter),
              patch.object(worker,"require_authorized_native_review_host"),
              redirect_stdout(again)):
            self.assertEqual(worker.main(["--private-root",str(private),
                                          "--source-free-advance"]),0)
        repeat=json.loads(again.getvalue())
        self.assertEqual(repeat["checkpointIntegritySha256"],
                         result["checkpointIntegritySha256"])
        self.assertEqual(len(list(
            (private/"frozen-original-review-slices").iterdir())),12)
        self.assertFalse((private/"frozen-original-review-attempts").exists())

    def test_source_free_checkpoint_tamper_blocks_restart_without_provider(self):
        from scripts import run_v3_yoga6_recovery_worker as worker
        chapter, local, private = self._normal_worker_fixture()
        def invoke():
            output=io.StringIO()
            with (patch.dict(os.environ, {"LOCALAPPDATA":str(local)}),
                  patch.object(worker,"ROOT",self.repo),
                  patch.object(worker,"COURSE",chapter),
                  patch.object(worker,"require_authorized_native_review_host"),
                  patch.object(worker,"_load_native_config") as credential,
                  patch.object(worker.native,"main") as paid,
                  redirect_stdout(output)):
                code=worker.main(["--private-root",str(private),
                                  "--source-free-advance"])
            credential.assert_not_called()
            paid.assert_not_called()
            return code, json.loads(output.getvalue())
        code, report=invoke()
        self.assertEqual(code,0,report)
        checkpoint=private/"v3-source-free-forward-checkpoint.json"
        record=json.loads(checkpoint.read_text(encoding="utf8"))
        record["originalPasses"]=108
        checkpoint.write_text(json.dumps(record),encoding="utf8")
        code, rejected=invoke()
        self.assertEqual(code,3)
        self.assertEqual(rejected["status"],"STOP_YOGA6_RECOVERY_WORKER")
        self.assertEqual(rejected["reasonClass"],"ValueError")
        self.assertFalse(rejected["publicationAuthorized"])

    def test_source_free_mode_rejects_paid_execution_and_transfer(self):
        from scripts import run_v3_yoga6_recovery_worker as worker
        local=self.home/"FakeLocalAppData"
        local.mkdir(exist_ok=True)
        output=io.StringIO()
        with (patch.dict(os.environ,{"LOCALAPPDATA":str(local)}),
              patch.object(worker,"_load_native_config") as credential,
              patch.object(worker.native,"main") as paid,
              redirect_stdout(output)):
            code=worker.main(["--source-free-advance","--execute",
                              "--allow-generated-text-transfer"])
        self.assertEqual(code,2)
        self.assertEqual(json.loads(output.getvalue())["status"],
                         "STOP_SOURCE_FREE_MODE_MUST_NOT_REQUEST_PROVIDER")
        credential.assert_not_called()
        paid.assert_not_called()

    def test_source_free_orphan_precall_not_reported_provider_ready(self):
        from app_generator.runtime.v3_source_free_forward import (
            advance_source_free_until_boundary,
        )
        chapter, local, private = self._normal_worker_fixture()
        self._set_synthetic_sixth_failure_to_cooled_servererror(private)
        _, manifest = stage_frozen_original_tail_slice(
            chapter, self.repo, private, section="section-9-6", index=6)
        reserve_frozen_original_tail_attempt(
            private, source_sha=self.digest, index=6,
            slice_sha=manifest["slicePackageSha256"])
        result = advance_source_free_until_boundary(chapter,self.repo,private)
        self.assertEqual(result["providerCapacity"],
                         "STOP_TAIL_UNCONFIRMED_PRIOR_ATTEMPT")
        self.assertEqual(result["status"],
                         "SOURCE_FREE_BOUNDARIES_STAGED_PROVIDER_STILL_BLOCKED")
        self.assertEqual(result["stagedImmutableOriginalTailSlices"],11)
        self.assertFalse(result["publicationAuthorized"])
        self.assertEqual(result["paidGeminiCalls"],0)

    def test_source_free_checkpoint_rejects_assessment_rollback(self):
        from hashlib import sha256
        from app_generator.runtime.v3_source_free_forward import (
            advance_source_free_until_boundary, _encode,
        )
        chapter, local, private = self._normal_worker_fixture()
        first = advance_source_free_until_boundary(chapter,self.repo,private)
        self.assertEqual(first["originalAssessedUnchanged"],6)
        receipt_file = private/"v3-source-free-forward-checkpoint.json"
        older = json.loads(receipt_file.read_text(encoding="utf8"))
        # Simulate a legitimate later checkpoint witnessing newer original
        # evidence, followed by a stale/rolled-back assessment folder. The
        # receipt has a *correctly recomputed* digest; not simple corruption.
        newer = {k:v for k,v in older.items() if k!="integritySha256"}
        newer["originalAssessed"]=7
        newer["originalPasses"]=6
        newer["integritySha256"] = sha256(_encode(newer)).hexdigest()
        receipt_file.write_text(json.dumps(newer),encoding="utf8")
        with self.assertRaisesRegex(ValueError,"ORIGINAL_EVIDENCE_ROLLBACK"):
            advance_source_free_until_boundary(chapter,self.repo,private)
        self.assertEqual(json.loads(receipt_file.read_text(encoding="utf8")),
                         newer)
        self.assertFalse((private/"frozen-original-review-attempts").exists())

    def test_normal_ready_paid_denial_does_not_strand_source_free_work(self):
        # BSA-189: normal READY branch previously rejected paid authorization
        # BEFORE running registered source-free repair. A denied permission
        # cannot authorize Gemini, but must not strand independent local QA.
        from scripts import run_v3_yoga6_recovery_worker as worker
        chapter, local, private = self._normal_worker_fixture()
        ready = {
            "dispatchStatus": "READY_FOR_AUTHORIZED_REVIEW_SESSIONS",
            "nextSection": "section-9-5",
            "publicationAuthorized": False,
        }
        output=io.StringIO()
        with (patch.dict(os.environ, {"LOCALAPPDATA":str(local)}),
              patch.object(worker,"ROOT",self.repo),
              patch.object(worker,"COURSE",chapter),
              patch.object(worker,"plan_v3_course_review",return_value=ready),
              patch.object(worker,"authorize_paid_v3_action",
                           side_effect=ValueError("SYNTHETIC_PAID_PERMISSION_DENIED")),
              patch.object(worker,"require_authorized_native_review_host"),
              patch.object(worker.native,"main") as model,
              patch.object(worker,"_load_native_config") as credentials,
              patch.object(worker,"diagnose_model_metadata") as metadata,
              redirect_stdout(output)):
            code=worker.main(
                ["--private-root",str(private),"--auto-advance",
                 "--execute","--allow-generated-text-transfer"])
        self.assertEqual(code,3)
        self.assertEqual(json.loads(output.getvalue())["status"],
                         "STOP_YOGA6_RECOVERY_WORKER")
        self.assertTrue((private/"frozen-original-review-slices").is_dir())
        self.assertEqual(
            len(list((private/"frozen-original-review-slices").iterdir())),12)
        self.assertTrue((private/"v3-source-free-forward-checkpoint.json")
                        .is_file())
        self.assertFalse((private/"frozen-original-review-attempts").exists())
        model.assert_not_called()
        credentials.assert_not_called()
        metadata.assert_not_called()

    def test_source_free_ready_positive_control_has_no_false_provider_stop(self):
        from app_generator.runtime.v3_source_free_forward import (
            advance_source_free_until_boundary,
        )
        chapter, local, private = self._normal_worker_fixture()
        self._set_synthetic_sixth_failure_to_cooled_servererror(private)
        verified = advance_source_free_until_boundary(
            chapter,self.repo,private)
        self.assertEqual(verified["providerCapacity"],"READY")
        self.assertEqual(verified["originalProviderCapacity"],"READY")
        self.assertEqual(verified["supplementalProviderPreflight"],"READY")
        self.assertEqual(verified["status"],"SOURCE_FREE_BOUNDARIES_STAGED")
        self.assertEqual(verified["stagedImmutableOriginalTailSlices"],12)
        self.assertEqual(verified["paidGeminiCalls"],0)
        self.assertFalse(verified["publicationAuthorized"])
        self.assertFalse((private/"frozen-original-review-attempts").exists())

    def test_source_free_exclusive_owner_lock_prevents_concurrent_entrypoint(self):
        from app_generator.runtime.v3_source_free_forward import (
            advance_source_free_until_boundary,
        )
        from app_generator.runtime.v3_yoga6_recovery import coordinator_lock
        chapter, local, private = self._normal_worker_fixture()
        with coordinator_lock(private):
            with self.assertRaisesRegex(RuntimeError,"V3_WORKER_ALREADY_RUNNING"):
                advance_source_free_until_boundary(chapter,self.repo,private)
        self.assertFalse((private/"frozen-original-review-attempts").exists())
        self.assertFalse((private/"v3-source-free-forward-checkpoint.json")
                         .exists())

    def test_source_free_repeated_crashes_at_first_middle_last_stage(self):
        from app_generator.runtime import v3_source_free_forward as offline
        from scripts import run_v3_yoga6_recovery_worker as worker
        chapter, local, private = self._normal_worker_fixture()
        source_before=(chapter/"section-9-6"/"package.json").read_bytes()
        original=(private/("v3-generated-"+self.digest)/"batches"
                  /f"v3-review-{self.digest[:12]}-005-0.json")
        old_role=original.read_bytes()
        stage=offline.stage_frozen_original_tail_slice

        def invoke():
            out=io.StringIO()
            with (patch.dict(os.environ,{"LOCALAPPDATA":str(local)}),
                  patch.object(worker,"ROOT",self.repo),
                  patch.object(worker,"COURSE",chapter),
                  patch.object(worker,"require_authorized_native_review_host"),
                  patch.object(worker.native,"main") as paid,
                  patch.object(worker,"_load_native_config") as credential,
                  redirect_stdout(out)):
                exit_code=worker.main(
                    ["--private-root",str(private),"--source-free-advance"])
            paid.assert_not_called()
            credential.assert_not_called()
            return exit_code,json.loads(out.getvalue())

        for stop_at in (6,11,17):
            def crash(*args, **kwargs):
                if kwargs["index"]==stop_at:
                    raise RuntimeError("SYNTHETIC_CRASH_BOUNDARY")
                return stage(*args,**kwargs)
            with (self.subTest(stop_at=stop_at),
                  patch.object(offline,"stage_frozen_original_tail_slice",
                               side_effect=crash)):
                exit_code,report=invoke()
                self.assertEqual(exit_code,3)
                self.assertEqual(report["status"],"STOP_YOGA6_RECOVERY_WORKER")
                expected=stop_at-6
                slices=private/"frozen-original-review-slices"
                found=len(list(slices.iterdir())) if slices.exists() else 0
                self.assertEqual(found,expected)
                self.assertFalse(
                    (private/"v3-source-free-forward-checkpoint.json").exists())
                self.assertFalse(
                    (private/"frozen-original-review-attempts").exists())
        exit_code,report=invoke()
        self.assertEqual(exit_code,0,report)
        self.assertEqual(report["stagedImmutableOriginalTailSlices"],12)
        self.assertEqual(report["paidGeminiCalls"],0)
        self.assertEqual(len(list(
            (private/"frozen-original-review-slices").iterdir())),12)
        self.assertEqual(original.read_bytes(),old_role)
        self.assertEqual(
            (chapter/"section-9-6"/"package.json").read_bytes(),source_before)
        self.assertFalse(report["publicationAuthorized"])
        self.assertFalse(report["versionedScopeAdmitted"])

    def test_source_free_tail_crash_resumes_without_paid_or_duplicate(self):
        from scripts import run_v3_yoga6_recovery_worker as worker
        from app_generator.runtime import v3_source_free_forward as offline
        chapter, local, private = self._normal_worker_fixture()
        real_stage = offline.stage_frozen_original_tail_slice
        seen = []
        def fail_at_third(*args, **kwargs):
            seen.append(kwargs["index"])
            if len(seen) == 3:
                raise RuntimeError("SYNTHETIC_SOURCE_FREE_DISK_INTERRUPTION")
            return real_stage(*args, **kwargs)
        def invoke():
            output=io.StringIO()
            with (patch.dict(os.environ,{"LOCALAPPDATA":str(local)}),
                  patch.object(worker,"ROOT",self.repo),
                  patch.object(worker,"COURSE",chapter),
                  patch.object(worker,"require_authorized_native_review_host"),
                  patch.object(worker.native,"main") as paid,
                  patch.object(worker,"_load_native_config") as credential,
                  redirect_stdout(output)):
                code=worker.main(["--private-root",str(private),
                                  "--source-free-advance"])
            paid.assert_not_called()
            credential.assert_not_called()
            return code,json.loads(output.getvalue())
        with patch.object(offline,"stage_frozen_original_tail_slice",
                          side_effect=fail_at_third):
            code,stopped=invoke()
        self.assertEqual(code,3)
        self.assertEqual(stopped["status"],"STOP_YOGA6_RECOVERY_WORKER")
        self.assertEqual(seen,[6,7,8])
        self.assertEqual(len(list((private/"frozen-original-review-slices")
                                  .iterdir())),2)
        self.assertFalse((private/"frozen-original-review-attempts").exists())
        self.assertFalse((private/"v3-source-free-forward-checkpoint.json")
                         .exists())
        code,resumed=invoke()
        self.assertEqual(code,0,resumed)
        self.assertEqual(resumed["stagedImmutableOriginalTailSlices"],12)
        self.assertEqual(len(list((private/"frozen-original-review-slices")
                                  .iterdir())),12)
        self.assertFalse((private/"frozen-original-review-attempts").exists())
        self.assertEqual(resumed["paidGeminiCalls"],0)
        self.assertFalse(resumed["publicationAuthorized"])

    def test_locally_captured_malformed_role_isolated_and_next_original_advances(self):
        from tests.test_autonomous_completion_v3 import FakeModel, sessions
        attempted=[]
        def reviewer(raw,manifest):
            index=manifest["sourceActivityIndex"]
            attempted.append(index)
            pair=(sessions(FakeModel(malformed=True),FakeModel())
                  if index==6 else sessions(FakeModel(),FakeModel()))
            return advance_v3_generated_text(
                raw,pair,private_root=self.private,
                generated_content_transfer_allowed=True,max_activities=1)
        result=advance_frozen_tail_until_boundary(
            self.course,self.repo,self.private,reviewer,
            section=self.section,max_activities=2)
        self.assertEqual(result["status"],"STOP_TAIL_ACTIVITY_BUDGET_REACHED")
        self.assertEqual(result["supplemental"]["uncertain"],1)
        self.assertEqual(result["supplemental"]["passed"],1)
        self.assertEqual(result["verifiedNewSupplementalRowsThisInvocation"],2)
        self.assertEqual(result["nextOriginalIndex"],8)
        self.assertEqual(attempted,[6,7])
        self.assertEqual(result["originalAssessedUnchanged"],6)
        self.assertFalse(result["publicationAuthorized"])


if __name__=="__main__":
    unittest.main()

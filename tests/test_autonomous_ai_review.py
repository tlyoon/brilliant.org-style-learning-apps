"""Source-free adversarial tests for AI-only academic followup."""
import json
import tempfile
import unittest
from pathlib import Path

from app_generator.runtime.run_context import RunContext
from app_generator.runtime.autonomous_academic import review_batch_autonomously
from app_generator.validation.autonomous_ai_review import (
    ReviewerSession, review_activity, plan_automated_followup,
)

A="a"*64
B="b"*64

class Model:
    def __init__(self, verdict="SUPPORTED", fail=False):
        self.verdict=verdict
        self.fail=fail
        self.calls=0

    def ask(self, prompt, *, stage=None):
        self.calls+=1
        if self.fail:
            raise TimeoutError("ambiguous remote request")
        gate=stage.split("academic-",1)[1]
        return "BEGIN_JSON\n"+json.dumps({
            "gate":gate,"verdict":self.verdict,
            "rationale":"Independently checked numerical physical counterexamples.",
            "sourcePage":2,
            "issue":"Invalid net external impulse premise" if self.verdict=="CONTRADICTED" else "",
        })+"\nEND_JSON"

def pair(a=None,b=None):
    return (ReviewerSession("physics","session-physics",a or Model()),
            ReviewerSession("language","session-language",b or Model()))

class AutonomousReviewTests(unittest.TestCase):
    def setUp(self):
        self.activity={"id":"collision-one","prompt":{"en":"Conservation?"}}
        self.source={"verifiedPages":[2],"sourceEvidence":"A private controlled textbook passage describing the conditions of momentum conservation in the collision.","sourceSha256":B}

    def test_consensus_has_no_manual_approval_and_no_unsupported_academic_pass(self):
        s=pair()
        report=review_activity(self.activity,self.source,s,
                               package_sha256=A,source_sha256=B)
        self.assertEqual("AUTO_CONTINUE",report["nextAction"])
        self.assertEqual(5,len(report["gates"]))
        self.assertEqual(5,s[0].conversation.calls)
        self.assertEqual(5,s[1].conversation.calls)
        self.assertEqual("REVIEW_REQUIRED",report["academicQA"])
        self.assertFalse(report["humanReviewRequired"])
        self.assertFalse(report["publicationAuthorized"])

    def test_ai_objection_dispatches_automatic_repair(self):
        report=review_activity(self.activity,self.source,pair(Model("CONTRADICTED"),Model()),
                               package_sha256=A,source_sha256=B,
                               gates=("physics_consistency",))
        self.assertEqual("AUTO_REPAIR",report["nextAction"])
        self.assertFalse(plan_automated_followup(report)["requiresHumanAcademicApproval"])

    def test_timeout_held_and_no_duplicate_send_on_resumption(self):
        first,second=pair(Model(fail=True),Model())
        with tempfile.TemporaryDirectory() as t:
            ctx=RunContext.create(Path(t))
            r=review_activity(self.activity,self.source,(first,second),
                              package_sha256=A,source_sha256=B,
                              gates=("answer_correctness",),
                              checkpoint=ctx,claim_prefix="test-request")
            self.assertEqual("AUTO_RETRY",r["nextAction"])
            self.assertEqual(1,first.conversation.calls)
            next_pair=pair(Model(),Model())
            r2=review_activity(self.activity,self.source,next_pair,
                               package_sha256=A,source_sha256=B,
                               gates=("answer_correctness",),
                               checkpoint=ctx,claim_prefix="test-request")
            self.assertEqual("AUTO_RETRY",r2["nextAction"])
            self.assertEqual(0,next_pair[0].conversation.calls)
            self.assertEqual(0,next_pair[1].conversation.calls)
            self.assertFalse(r2["publicationAuthorized"])

    def test_crash_claim_cannot_resubmit(self):
        with tempfile.TemporaryDirectory() as t:
            ctx=RunContext.create(Path(t))
            source=pair()
            r=review_activity(self.activity,self.source,source,
                              package_sha256=A,source_sha256=B,
                              gates=("source_fidelity",),
                              checkpoint=ctx,claim_prefix="claims")
            self.assertEqual("AUTO_CONTINUE",r["nextAction"])
            self.assertEqual(1,source[0].conversation.calls)
            new=pair()
            review_activity(self.activity,self.source,new,
                            package_sha256=A,source_sha256=B,
                            gates=("source_fidelity",),
                            checkpoint=ctx,claim_prefix="claims")
            self.assertEqual(0,new[0].conversation.calls)
            self.assertEqual(0,new[1].conversation.calls)
            self.assertFalse(r["publicationAuthorized"])

    def test_independent_sessions_and_verified_page_boundaries(self):
        same=Model()
        with self.assertRaisesRegex(ValueError,"independent reviewer connections"):
            review_activity(self.activity,self.source,pair(same,same),
                            package_sha256=A,source_sha256=B)
        bad_source={"verifiedPages":[2,2],"sourceSha256":B,
                    "sourceEvidence":self.source["sourceEvidence"]}
        with self.assertRaisesRegex(ValueError,"unique PDF"):
            review_activity(self.activity,bad_source,pair(),
                            package_sha256=A,source_sha256=B)
        with self.assertRaisesRegex(ValueError,"SHA-256"):
            review_activity(self.activity,self.source,pair(),
                            package_sha256="wrong",source_sha256=B)

    def test_batch_resume_no_duplicate_requests_and_stale_hash_rejected(self):
        a=self.activity
        b={"id":"collision-two","prompt":{"en":"New question"}}
        with tempfile.TemporaryDirectory() as temp:
            context=RunContext.create(Path(temp))
            calls=[]
            def factory(activity_id):
                calls.append(activity_id)
                a,b=pair()
                return (ReviewerSession(a.reviewer_id,a.session_id+"-"+activity_id,a.conversation),
                        ReviewerSession(b.reviewer_id,b.session_id+"-"+activity_id,b.conversation))
            report=review_batch_autonomously(
                context,{"activities":[a,b]},
                package_sha256=A,source_sha256=B,
                authorized_source={a["id"]:self.source,b["id"]:self.source},
                reviewer_factory=factory)
            self.assertEqual(2,report["aiReviewedActivities"])
            self.assertEqual(2,report["followupCounts"]["AUTO_CONTINUE"])
            report_again=review_batch_autonomously(
                context,{"activities":[a,b]},package_sha256=A,source_sha256=B,
                authorized_source={a["id"]:self.source,b["id"]:self.source},
                reviewer_factory=factory)
            self.assertEqual(2,len(calls))
            self.assertEqual(report["followups"],report_again["followups"])
            with self.assertRaisesRegex(ValueError,"stale or conflicting"):
                review_batch_autonomously(
                    context,{"activities":[a,b]},package_sha256=B,source_sha256=B,
                    authorized_source={a["id"]:self.source,b["id"]:self.source},
                    reviewer_factory=factory)

    def test_fresh_inflight_stale_claim_never_sends_and_requires_reconciliation(self):
        with tempfile.TemporaryDirectory() as t:
            context=RunContext.create(Path(t))
            session=pair()
            from app_generator.validation.autonomous_ai_review import (
                canonical_digest,independent_review_prompt
            )
            import hashlib
            prompt=independent_review_prompt(self.activity,"source_fidelity",self.source,
                perspective="Independently seek factual errors, physical counterexamples, invalid keys and unsupported assertions.")
            claim={
                "activityId":self.activity["id"],
                "activityHash":canonical_digest(self.activity),
                "sourceHash":B,"packageHash":A,
                "sourceContextHash":canonical_digest(self.source),
                "promptHash":hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
                "roleIndex":0,"gate":"source_fidelity","state":"IN_FLIGHT"
            }
            context.save_stage("hold-source-fidelity-0",claim)
            result=review_activity(self.activity,self.source,session,
                    package_sha256=A,source_sha256=B,
                    gates=("source_fidelity",),checkpoint=context,claim_prefix="hold")
            self.assertEqual("AUTO_SOURCE_CHECK",result["nextAction"])
            self.assertEqual(0,session[0].conversation.calls)
            self.assertEqual(1,session[1].conversation.calls)

    def test_untrusted_page_claim_cannot_gain_fidelity_pass(self):
        class UnsupportedPage(Model):
            def ask(self, prompt, *, stage=None):
                self.calls+=1
                return "BEGIN_JSON\n"+json.dumps({
                    "gate":"source_fidelity","verdict":"SUPPORTED",
                    "rationale":"This unsupported page is invented by model.",
                    "sourcePage":999,"issue":"",
                })+"\nEND_JSON"
        bad=review_activity(self.activity,self.source,
            pair(UnsupportedPage(),Model()),package_sha256=A,source_sha256=B,
            gates=("source_fidelity",))
        self.assertEqual("AUTO_SOURCE_CHECK",bad["nextAction"])
        self.assertEqual("REVIEW_REQUIRED",bad["academicQA"])

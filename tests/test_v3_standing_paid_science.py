"""BSA217 standing paid Gemini consent, source-bound finite campaigns, no replay.

All review callbacks here are fake. No external provider call is made by tests.
"""
from contextlib import ExitStack
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from app_generator.runtime import v3_standing_paid_science as standing
from app_generator.validation.autonomous_completion import package_identity

REAL_COURSE=Path(__file__).resolve().parents[1]/"content"/"chapter-9"


class StandingPaidScienceTests(unittest.TestCase):
    def setUp(self):
        context=tempfile.TemporaryDirectory()
        self.addCleanup(context.cleanup)
        base=Path(context.name)
        self.repo=base/"repo"
        self.course=self.repo/"content"/"chapter-9"
        target=self.course/"section-9-1"/"package.json"
        target.parent.mkdir(parents=True)
        raw=(REAL_COURSE/"section-9-1"/"package.json").read_bytes()
        target.write_bytes(raw)
        self.parent,self.items=package_identity(raw)
        self.private=base/"private"
        self.private.mkdir()
        original=self.private/("v3-generated-"+self.parent)/"batches"
        original.mkdir(parents=True)
        (original/("v3-assessment-"+self.parent+".json")).write_text(
            json.dumps({"reviews":[{"status":"AI_UNCERTAIN",
                                    "activityId":self.items[0]["id"]}]}),
            encoding="utf8")
        self.fake_progress={
            "scopeSource":"FROZEN_CANDIDATE_MANIFEST",
            "sectionsTotal":6,
            "publicationAuthorized":False,
            "sectionProgress":[{
                "section":"section-9-1","packageSha256":self.parent,
                "activitiesTotal":18,"activitiesAssessedRows":1,
                "modelConsensusPassActivities":0,
                "modelUncertainActivities":1,
                "modelRepairRequiredActivities":0,
                "unreconciledRoleClaims":0,
            }],
        }

    def fixtures(self,*,seen=None):
        stack=ExitStack()
        self.addCleanup(stack.close)
        stack.enter_context(patch.object(
            standing,"course_readiness",return_value=self.fake_progress))
        stack.enter_context(patch.object(
            standing,"assessment_progress",
            return_value={"activitiesAssessed":1,"modelUncertainActivities":1}))
        def source_state(private,parent,index,sha):
            if index==0:
                return "ORIGINAL_ROLE_CLAIM_PRESENT_DO_NOT_REPLAY"
            if seen and index in seen:
                return seen[index]
            return "UNREVIEWED_ELIGIBLE"
        stack.enter_context(patch.object(standing,"_safe_evidence",
                                        side_effect=source_state))
        return stack

    def test_standing_permission_not_exhausted_and_budget_bounded_each_invocation(self):
        a=standing.authorize_standing(execute=True,transfer=True,
                                      activities=4,seconds=900)
        b=standing.authorize_standing(execute=True,transfer=True,
                                      activities=4,seconds=900)
        self.assertEqual(a,b)
        self.assertTrue(a["standingConsent"])
        self.assertEqual(a["maxPaidGeminiCalls"],8)
        self.assertFalse(a["publicationAuthorized"])
        for count,seconds in ((5,900),(0,900),(4,901),(4,0)):
            with self.subTest(count=count,seconds=seconds):
                with self.assertRaisesRegex(ValueError,"BUDGET_EXCEEDED"):
                    standing.authorize_standing(
                        execute=True,transfer=True,
                        activities=count,seconds=seconds)

    def test_executable_grant_tamper_and_missing_transfer_stop(self):
        with self.assertRaisesRegex(ValueError,"EXECUTE_AND_TRANSFER"):
            standing.authorize_standing(execute=True,transfer=False)
        grant=json.loads(standing.CONTRACT.read_text(encoding="utf8"))
        grant["neverReplaySubmittedOrAmbiguousRoles"]=False
        fake=self.private/"tamper.json"
        fake.write_text(json.dumps(grant),encoding="utf8")
        with self.assertRaisesRegex(ValueError,"SCOPE_TAMPERED"):
            standing.authorize_standing(execute=True,transfer=True,contract=fake)

    def test_real_section91_old_unknown_preserved_and_new_source_digest_bound(self):
        self.fixtures()
        before=(self.course/"section-9-1"/"package.json").read_bytes()
        verified=standing.section91_evidence(
            self.course,self.repo,self.private)
        self.assertEqual(verified["oldUncertainIndex"],0)
        self.assertEqual(verified["parentSha256"],self.parent)
        self.assertEqual(len(verified["items"]),17)
        self.assertEqual(
            [e["index"] for e in verified["items"][:4]],[1,2,3,4])
        self.assertEqual([e["originalReviewState"] for e in verified["items"]],
                         ["UNREVIEWED_ELIGIBLE"]*17)
        self.assertEqual(before,
                         (self.course/"section-9-1"/"package.json").read_bytes())

    def test_historical_original_uncertainty_change_is_rejected(self):
        self.fixtures()
        prior=(self.private/("v3-generated-"+self.parent)/"batches"/
               ("v3-assessment-"+self.parent+".json"))
        prior.write_text(json.dumps({"reviews":[{"status":"AI_CONSENSUS_PASS"}]}),
                         encoding="utf8")
        with self.assertRaisesRegex(ValueError,"OLD_UNCERTAIN_REVIEW_CHANGED"):
            standing.section91_evidence(self.course,self.repo,self.private)

    def test_private_staging_idempotent_and_tamper_fails_closed(self):
        self.fixtures()
        e=standing.section91_evidence(self.course,self.repo,self.private)["items"][0]
        standing.stage_standing_one(self.private,e)
        standing.stage_standing_one(self.private,e)
        dest=self.private/"standing-new-source-review-slices"/e["sha"]
        (dest/"package.json").write_text("fake",encoding="utf8")
        with self.assertRaisesRegex(ValueError,"SAVED_SLICE_CHANGED"):
            standing.stage_standing_one(self.private,e)

    def test_fake_callback_cannot_claim_independent_gemini_success(self):
        self.fixtures()
        with patch.object(standing,"verified_new_provider_capability",
                          return_value=True):
            with self.assertRaisesRegex(ValueError,"MISSING_DURABLE_ASSESSMENT"):
                standing.advance_standing_science(
                    self.course,self.repo,self.private,
                    execute=True,transfer=True,max_activities=1,
                    capability={"status":"fake"},
                    review_one=lambda raw,id,private:{
                        "activitiesAssessed":1})
        self.assertTrue((self.private/"standing-new-source-review-slices").exists())

    def test_bounded_four_review_callbacks_only_and_stop_on_uncertainty(self):
        self.fixtures()
        calls=[]
        with patch.object(standing,"verified_new_provider_capability",
                          return_value=True),patch.object(
             standing,"verify_persisted_two_role_science",
             return_value={"pass":True,"repair":False,"uncertain":False}):
            report=standing.advance_standing_science(
                self.course,self.repo,self.private,execute=True,transfer=True,
                max_activities=4,capability={},
                review_one=lambda raw,id,private:
                    (calls.append(id) or {"activitiesAssessed":1}))
        self.assertEqual(len(calls),4)
        self.assertEqual(report["status"],"STANDING_BOUNDED_BATCH_COMPLETED")
        self.assertTrue(report["allNewScientificPass"])
        self.assertEqual(report["maximumGeminiCalls"],8)
        self.assertTrue(all(1<=row["index"]<=4 for row in report["outcomes"]))

    def test_uncertain_first_role_stops_further_paid_work(self):
        self.fixtures()
        calls=[]
        with patch.object(standing,"verified_new_provider_capability",
                          return_value=True),patch.object(
             standing,"verify_persisted_two_role_science",
             return_value={"pass":False,"repair":False,"uncertain":True}):
            report=standing.advance_standing_science(
                self.course,self.repo,self.private,execute=True,transfer=True,
                max_activities=4,capability={},
                review_one=lambda raw,id,private:
                    (calls.append(id) or {"activitiesAssessed":1}))
        self.assertEqual(len(calls),1)
        self.assertEqual(report["status"],"STANDING_STOP_REVIEW_BOUNDARY")
        self.assertFalse(report["allNewScientificPass"])

    def test_any_prior_incomplete_role_is_not_replayed_but_new_siblings_advance(self):
        self.fixtures(seen={1:"ROLE_CLAIM_PRESENT_DO_NOT_REPLAY"})
        calls=[]
        with patch.object(standing,"verified_new_provider_capability",
                          return_value=True),patch.object(
             standing,"verify_persisted_two_role_science",
             return_value={"pass":True,"repair":False,"uncertain":False}):
            report=standing.advance_standing_science(
                self.course,self.repo,self.private,execute=True,transfer=True,
                max_activities=4,capability={},
                review_one=lambda raw,id,private:
                    (calls.append(id) or {"activitiesAssessed":1}))
        self.assertEqual(len(calls),4)
        self.assertNotIn(self.items[1]["id"],calls)
        self.assertEqual([x["index"] for x in report["outcomes"]],[2,3,4,5])
        self.assertEqual(report["quarantinedUncertainOrIncompleteIndices"],[1])
        self.assertEqual(report["status"],"STANDING_BOUNDED_BATCH_COMPLETED")

    def test_no_saved_standing_roles_never_create_supplemental_pass(self):
        self.assertEqual(standing.verified_section91_standing_passes(
            self.course,self.repo,self.private),[])


if __name__=="__main__":
    unittest.main()

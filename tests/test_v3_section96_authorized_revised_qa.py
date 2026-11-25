"""BSA206: exact new-version paid scope, synthetic reviewer fault injection.

These tests use NO actual Gemini calls. The real Yoga6 live runner separately
exercises two-source SHA-bound independent Gemini roles and private claims.
"""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from app_generator.runtime.v3_section96_authorized_revised_qa import (
    _EXPECTED_CONTRACT,_EXPECTED_SLICES,authorize_revised96,
    stage_and_verify_two_new_inputs,unsent_revised_input,
    verified_new_provider_capability,advance_revised96_reviews,
)

class Revised96PaidTests(unittest.TestCase):
    def setUp(self):
        handle=tempfile.TemporaryDirectory()
        self.addCleanup(handle.cleanup)
        self.repo=Path(handle.name)/"repo"
        self.repo.mkdir()
        self.course=self.repo/"content"/"chapter-9"
        self.course.mkdir(parents=True)
        self.private=Path(handle.name)/"private"
        self.private.mkdir()
        for index,activity,parent,sha,folder in _EXPECTED_SLICES:
            path=self.private/folder/"section-9-6"/sha
            path.mkdir(parents=True)
            fields={"schema":"MOCK_ONLY","sourceSection":"section-9-6",
                    "sourceActivityIndex":index,
                    "parentPackageSha256":(parent if index==9 else
                        "1620d15e1d645c81301997f0e42d0efbad0a7b2d123eb6b11cba9ec8c04b027f"),
                    "activities":[{"id":activity}]}
            if index==5:
                fields["candidatePackageSha256"]=parent
            (path/"package.json").write_text(json.dumps(fields),encoding="utf8")

    def test_exact_authorization_and_unchanged_old_paid_charter(self):
        old=Path("docs/v3_paid_gemini_review_authorization_20261117.json").read_bytes()
        a=authorize_revised96(execute=True,transfer=True,
                              activities=2,seconds=900)
        self.assertEqual(a["callLimit"],4)
        self.assertFalse(a["publicationAuthorized"])
        self.assertEqual(old,Path(
            "docs/v3_paid_gemini_review_authorization_20261117.json").read_bytes())

    def test_tampered_new_paid_charter_and_excess_paid_calls_fail_closed(self):
        for flag in ("publicationAuthorized","allowBatchJobCreation",
                     "allowAutomatedScheduler","allowSourcePDFUpload",
                     "versionedCourseAdmissionAuthorized"):
            with self.subTest(flag=flag):
                data=dict(_EXPECTED_CONTRACT)
                data[flag]=True
                fake=self.private/"auth.json"
                fake.write_text(json.dumps(data))
                with self.assertRaisesRegex(ValueError,"OWNER_SCOPE_CHANGED"):
                    authorize_revised96(execute=True,transfer=True,
                        activities=1,seconds=900,file=fake)
        for n,seconds in [(3,900),(1,901),(0,900),(1,5)]:
            with self.assertRaisesRegex(ValueError,"BUDGET_EXCEEDED"):
                authorize_revised96(execute=True,transfer=True,
                                     activities=n,seconds=seconds)
        for execute,transfer in [(False,True),(True,False),(False,False)]:
            with self.assertRaisesRegex(ValueError,"NOT_AUTHORIZED"):
                authorize_revised96(execute=execute,transfer=transfer,
                                    activities=1,seconds=900)

    def mocks(self):
        from unittest.mock import patch
        from app_generator.runtime.v3_section96_authorized_revised_qa import _OLD
        def pkg(raw):
            item=json.loads(raw)["activities"][0]
            for index,activity,parent,sha,folder in _EXPECTED_SLICES:
                if item["id"]==activity:
                    return sha,[item]
            raise ValueError("UNKNOWN_TEST_CONTENT")
        tail={
            "sourcePackageSha256":_OLD,
            "originalAssessedUnchanged":6,
            "originalModelConsensusPassesUnchanged":5,
            "supplemental":{"passed":10,"uncertain":1,"failed":1,
                            "reserved":0,"eligible":0},
            "next":None,
            "rows":[
                {"index":6,"state":"SUPPLEMENTAL_UNCERTAIN_NO_REPLAY"},
                {"index":9,"state":"SUPPLEMENTAL_SCIENTIFIC_REPAIR_REQUIRED"}
            ],
        }
        old={"status":"NEW_VERSIONED_SECTION96_REPAIR_STAGED_QA_NOT_AUTHORIZED",
             "parentPackageSha256":_OLD,
             "isolatedReviewInputSha256":_EXPECTED_SLICES[0][3],
             "oldAmbiguousProviderRolePreserved":True}
        new={"status":"NEW_SECTION96_SCIENCE_REPAIR_STAGED_REVIEW_NOT_AUTHORIZED",
             "isolatedReviewInputSha256":_EXPECTED_SLICES[1][3],
             "oldScientificFailurePreserved":True,
             "oldProviderUncertaintyPreserved":True}
        return [
            patch("app_generator.runtime.v3_section96_authorized_revised_qa."
                  "stage_known_unrecoverable_section96",return_value=old),
            patch("app_generator.runtime.v3_section96_authorized_revised_qa."
                  "stage_known_section96_scientific_failure",return_value=new),
            patch("app_generator.runtime.v3_section96_authorized_revised_qa."
                  "plan_frozen_original_tail",return_value=tail),
            patch("app_generator.runtime.v3_section96_authorized_revised_qa."
                  "known_bsa196_source_claims_present",return_value=True),
            patch("app_generator.runtime.v3_section96_authorized_revised_qa."
                  "package_identity",side_effect=pkg),
        ]

    def test_two_exact_new_version_inputs_verified_no_old_role_replay(self):
        from contextlib import ExitStack
        with ExitStack() as stack:
            for p in self.mocks():stack.enter_context(p)
            inputs=stage_and_verify_two_new_inputs(
                self.course,self.repo,self.private)
        self.assertEqual(
            [(x["index"],x["activityId"],x["sha"]) for x in inputs],
            [(i,a,sha) for i,a,parent,sha,folder in _EXPECTED_SLICES])
        self.assertFalse(any(
            (self.private/("v3-generated-"+x["sha"])).exists()
            for x in inputs))

    def test_source_id_or_prior_submitted_identity_is_not_replayed(self):
        from contextlib import ExitStack
        i,activity,parent,sha,folder=_EXPECTED_SLICES[1]
        path=self.private/folder/"section-9-6"/sha/"package.json"
        original=path.read_bytes()
        try:
            item=json.loads(original)
            item["sourceActivityIndex"]=5
            path.write_text(json.dumps(item))
            with ExitStack() as stack:
                for p in self.mocks():stack.enter_context(p)
                with self.assertRaisesRegex(ValueError,"SOURCE_IDENTITY"):
                    stage_and_verify_two_new_inputs(
                        self.course,self.repo,self.private)
        finally:
            path.write_bytes(original)
        self.assertTrue(unsent_revised_input(self.private,sha))
        (self.private/("v3-generated-"+sha)).mkdir()
        self.assertFalse(unsent_revised_input(self.private,sha))
        with self.assertRaisesRegex(ValueError,"UNSAFE_OLD_REQUEST_DIRECTORY"):
            with patch("pathlib.Path.is_symlink",side_effect=lambda *_:True):
                unsent_revised_input(self.private,sha)

    def test_real_two_role_callback_never_exceeds_four_calls(self):
        from contextlib import ExitStack
        calls=[]
        def reviewer(raw,activity,private):
            calls.append(activity)
            self.assertLessEqual(len(calls),2)
            return {"activitiesAssessed":1,
                    "modelConsensusPassActivities":1,
                    "modelRepairRequiredActivities":0,
                    "modelUncertainActivities":0}
        with ExitStack() as stack:
            for p in self.mocks():stack.enter_context(p)
            stack.enter_context(patch(
                "app_generator.runtime.v3_section96_authorized_revised_qa."
                "verified_new_provider_capability",return_value=True))
            stack.enter_context(patch(
                "app_generator.runtime.v3_section96_authorized_revised_qa."
                "verify_persisted_two_role_science",
                return_value={"pass":True,"repair":False,"uncertain":False}))
            result=advance_revised96_reviews(
                self.course,self.repo,self.private,
                execute=True,transfer=True,max_activities=2,
                max_seconds=900,capability={"sourceFree":True},
                review_one=reviewer)
        self.assertEqual(result["status"],"REVISED96_AUTHORIZED_BATCH_COMPLETED")
        self.assertEqual(len(calls),2)
        self.assertEqual(result["maxGeminiReviewerCalls"],4)
        self.assertTrue(all(x["newConsensusPass"] for x in result["outcomes"]))
        self.assertFalse(result["publicationAuthorized"])

    def test_uncertain_first_role_halts_other_new_activity(self):
        from contextlib import ExitStack
        calls=[]
        def reviewer(raw,activity,private):
            calls.append(activity)
            return {"activitiesAssessed":1,
                    "modelConsensusPassActivities":0,
                    "modelRepairRequiredActivities":0,
                    "modelUncertainActivities":1}
        with ExitStack() as stack:
            for p in self.mocks():stack.enter_context(p)
            stack.enter_context(patch(
                "app_generator.runtime.v3_section96_authorized_revised_qa."
                "verified_new_provider_capability",return_value=True))
            stack.enter_context(patch(
                "app_generator.runtime.v3_section96_authorized_revised_qa."
                "verify_persisted_two_role_science",
                return_value={"pass":False,"repair":False,"uncertain":True}))
            result=advance_revised96_reviews(
                self.course,self.repo,self.private,
                execute=True,transfer=True,max_activities=2,
                max_seconds=900,capability={"sourceFree":True},
                review_one=reviewer)
        self.assertEqual(len(calls),1)
        self.assertEqual(result["status"],"REVISED96_STOPPED_AT_REVIEW_BOUNDARY")
        self.assertTrue(result["outcomes"][0]["newUncertain"])

    def test_callback_cannot_forge_two_gemini_pass_without_saved_claims(self):
        from app_generator.runtime.v3_section96_authorized_revised_qa import (
            verify_persisted_two_role_science,
        )
        sha=_EXPECTED_SLICES[0][3]
        activity=_EXPECTED_SLICES[0][1]
        fake={"activitiesAssessed":1,"modelConsensusPassActivities":1,
              "modelRepairRequiredActivities":0,"modelUncertainActivities":0}
        with self.assertRaisesRegex(ValueError,"MISSING_DURABLE_ASSESSMENT"):
            verify_persisted_two_role_science(
                self.private,b"synthetic",activity,sha,fake)
        batch=self.private/("v3-generated-"+sha)/"batches"
        batch.mkdir(parents=True)
        (batch/("v3-assessment-"+sha+".json")).write_text("{}")
        with patch(
            "app_generator.runtime.v3_section96_authorized_revised_qa."
            "assessment_progress",return_value=fake):
            with self.assertRaisesRegex(ValueError,"INCOMPLETE_TWO_ROLE_EVIDENCE"):
                verify_persisted_two_role_science(
                    self.private,b"synthetic",activity,sha,fake)

    def test_restart_reuses_completed_first_and_reviews_only_new_second(self):
        from contextlib import ExitStack
        first=_EXPECTED_SLICES[0][3]
        (self.private/("v3-generated-"+first)).mkdir()
        calls=[]
        def reviewer(raw,activity,private):
            calls.append(activity)
            return {"activitiesAssessed":1,
                    "modelConsensusPassActivities":1,
                    "modelRepairRequiredActivities":0,
                    "modelUncertainActivities":0}
        with ExitStack() as stack:
            for p in self.mocks():stack.enter_context(p)
            stack.enter_context(patch(
                "app_generator.runtime.v3_section96_authorized_revised_qa."
                "verified_new_provider_capability",return_value=True))
            stack.enter_context(patch(
                "app_generator.runtime.v3_section96_authorized_revised_qa."
                "read_prior_two_role_science",
                return_value={"pass":True,"repair":False,"uncertain":False}))
            stack.enter_context(patch(
                "app_generator.runtime.v3_section96_authorized_revised_qa."
                "verify_persisted_two_role_science",
                return_value={"pass":True,"repair":False,"uncertain":False}))
            result=advance_revised96_reviews(
                self.course,self.repo,self.private,
                execute=True,transfer=True,max_activities=2,
                max_seconds=900,capability={"sourceFree":True},
                review_one=reviewer)
        self.assertEqual(calls,[_EXPECTED_SLICES[1][1]])
        self.assertEqual(result["status"],"REVISED96_AUTHORIZED_BATCH_COMPLETED")
        self.assertTrue(result["outcomes"][0]["reusedPreviouslyVerifiedRoles"])
        self.assertFalse(result["outcomes"][1]["reusedPreviouslyVerifiedRoles"])
        self.assertFalse(result["publicationAuthorized"])

    def test_uncertain_prior_version_does_not_trigger_other_paid_request(self):
        from contextlib import ExitStack
        first=_EXPECTED_SLICES[0][3]
        (self.private/("v3-generated-"+first)).mkdir()
        with ExitStack() as stack:
            for p in self.mocks():stack.enter_context(p)
            stack.enter_context(patch(
                "app_generator.runtime.v3_section96_authorized_revised_qa."
                "verified_new_provider_capability",return_value=True))
            stack.enter_context(patch(
                "app_generator.runtime.v3_section96_authorized_revised_qa."
                "read_prior_two_role_science",
                return_value={"pass":False,"repair":False,"uncertain":True}))
            result=advance_revised96_reviews(
                self.course,self.repo,self.private,
                execute=True,transfer=True,max_activities=2,
                max_seconds=900,capability={"sourceFree":True},
                review_one=lambda *args:self.fail("should not generate"))
        self.assertEqual(result["status"],"REVISED96_STOPPED_AT_REVIEW_BOUNDARY")
        self.assertEqual(len(result["outcomes"]),1)
        self.assertTrue(result["outcomes"][0]["newUncertain"])

    def test_auth_migration_bypass_is_not_metadata_only(self):
        from app_generator.runtime.v3_provider_restoration import _OLD_CLIENTERROR_ROLES
        with patch(
            "app_generator.runtime.v3_section96_authorized_revised_qa."
            "_verified_migrated_auth_keys",return_value=()):
            self.assertFalse(verified_new_provider_capability(self.private,{
                "status":"MODEL_GENERATION_ACTION_DECLARED_QUOTA_UNVERIFIED",
                "sourceFree":True,"paidModelCalls":0}))
        with patch(
            "app_generator.runtime.v3_section96_authorized_revised_qa."
            "_verified_migrated_auth_keys",return_value=_OLD_CLIENTERROR_ROLES):
            self.assertTrue(verified_new_provider_capability(self.private,{
                "status":"MODEL_GENERATION_ACTION_DECLARED_QUOTA_UNVERIFIED",
                "sourceFree":True,"paidModelCalls":0}))
        self.assertFalse(verified_new_provider_capability(self.private,{
            "status":"STOP_AUTH_OR_PROJECT_DENIED",
            "sourceFree":True,"paidModelCalls":0}))

if __name__=="__main__":
    unittest.main()

"""BSA218: source-revised independent science: old unknowns cannot be replayed.

Synthetic fixtures never submit to Gemini or create real provider verdicts.
"""
from contextlib import ExitStack
from copy import deepcopy
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from app_generator.runtime import v3_final_two_science as subject
from app_generator.runtime.v3_frozen_original_tail import _bytes
from app_generator.validation.autonomous_completion import package_identity


COURSE=Path(__file__).resolve().parents[1]/"content"/"chapter-9"


class FinalTwoScienceTests(unittest.TestCase):
    def setUp(self):
        ctx=TemporaryDirectory()
        self.addCleanup(ctx.cleanup)
        self.repo=Path(ctx.name)/"repo"
        self.course=self.repo/"content"/"chapter-9"
        self.private=Path(ctx.name)/"private"
        self.private.mkdir()
        for section in ("section-9-1","section-9-6"):
            target=self.course/section/"package.json"
            target.parent.mkdir(parents=True)
            target.write_bytes((COURSE/section/"package.json").read_bytes())
        original96=json.loads((self.course/"section-9-6"/"package.json").read_text(encoding="utf8"))
        parent=deepcopy(original96)
        parent["activities"][5]["prompt"]["en"]+=" Previously approved clarification."
        raw1=_bytes(parent)
        sha1,_=package_identity(raw1)
        revised=deepcopy(parent)
        revised["activities"][9]["prompt"]["en"]+=" Previously approved clarification."
        raw2=_bytes(revised)
        sha2,_=package_identity(raw2)
        for kind,sha,raw in (
                ("historical-role-rollforward",sha1,raw1),
                ("scientific-failure-rollforward",sha2,raw2)):
            folder=self.private/kind/"section-9-6"/sha
            folder.mkdir(parents=True)
            (folder/"package.json").write_bytes(raw)
        self.prevsha=sha1
        self.latestsha=sha2

    def historical(self):
        stack=ExitStack()
        self.addCleanup(stack.close)
        stack.enter_context(patch.object(
            subject,"section91_evidence",return_value={
                "oldUncertainIndex":0}))
        stack.enter_context(patch.object(
            subject,"verified_section91_standing_passes",
            return_value=[{"index":i} for i in range(1,18)]))
        stack.enter_context(patch.object(
            subject,"plan_frozen_original_tail",return_value={
                "rows":[{"index":6,"state":"SUPPLEMENTAL_UNCERTAIN_NO_REPLAY"},
                        {"index":9,"state":"SUPPLEMENTAL_SCIENTIFIC_REPAIR_REQUIRED"}],
                "originalUncertaintyPreserved":True}))
        stack.enter_context(patch.object(
            subject,"stage_known_unrecoverable_section96",return_value={
                "status":"NEW_VERSIONED_SECTION96_REPAIR_STAGED_QA_NOT_AUTHORIZED",
                "oldAmbiguousProviderRolePreserved":True,
                "candidatePackageSha256":self.prevsha}))
        stack.enter_context(patch.object(
            subject,"validated_section96_two_science_revision",return_value={
                "candidatePackageSha256":self.latestsha,
                "proofs":[{"source":"genuine-5"},{"source":"genuine-9"}]}))
        return stack

    def test_two_source_revisions_stage_without_original_mutation(self):
        self.historical()
        frozen={sec:(self.course/sec/"package.json").read_bytes()
                for sec in ("section-9-1","section-9-6")}
        staged=subject.stage_final_two_new_inputs(
            self.course,self.repo,self.private)
        self.assertEqual([(r["section"],r["index"]) for r in staged],
                         [("section-9-1",0),("section-9-6",6)])
        self.assertNotEqual(staged[0]["sha"],staged[1]["sha"])
        for row in staged:
            self.assertEqual(package_identity(row["raw"])[0],row["sha"])
            self.assertNotEqual(row["candidateSha256"],row["parentSha256"])
        self.assertEqual([r["sha"] for r in staged],
                         [r["sha"] for r in subject.stage_final_two_new_inputs(
                             self.course,self.repo,self.private)])
        self.assertEqual(frozen,{sec:(self.course/sec/"package.json").read_bytes()
                                 for sec in frozen})
        self.assertIsNone(subject.verified_final_two_science(
            self.course,self.repo,self.private))

    def test_invariant_17_genuine_sibling_passes_is_not_optional(self):
        stack=self.historical()
        stack.enter_context(patch.object(
            subject,"verified_section91_standing_passes",return_value=[]))
        with self.assertRaisesRegex(ValueError,"PREVIOUS_17_GEMINI"):
            subject.stage_final_two_new_inputs(
                self.course,self.repo,self.private)

    def test_prior_96_unknown_and_fail_cannot_be_erased(self):
        stack=self.historical()
        stack.enter_context(patch.object(
            subject,"plan_frozen_original_tail",return_value={
                "rows":[{"index":6,"state":"GENUINE_SUPPLEMENTAL_CONSENSUS_PASS"},
                        {"index":9,"state":"SUPPLEMENTAL_SCIENTIFIC_REPAIR_REQUIRED"}],
                "originalUncertaintyPreserved":True}))
        with self.assertRaisesRegex(ValueError,"HISTORIC_96_ROLES_CHANGED"):
            subject.stage_final_two_new_inputs(
                self.course,self.repo,self.private)

    def test_saved_stage_tamper_rejected_without_provider_contact(self):
        self.historical()
        rows=subject.stage_final_two_new_inputs(
            self.course,self.repo,self.private)
        file=(self.private/"final-two-science-review-inputs"/
              "section-9-1"/rows[0]["sha"]/"package.json")
        file.write_text("FORGED",encoding="utf8")
        with self.assertRaisesRegex(ValueError,"EXISTING_SOURCE_CHANGED"):
            subject.stage_final_two_new_inputs(
                self.course,self.repo,self.private)

    def test_fake_two_review_callback_cannot_forge_genuine_proof(self):
        self.historical()
        with patch.object(subject,"verified_new_provider_capability",return_value=True):
            with self.assertRaisesRegex(ValueError,"MISSING_DURABLE_ASSESSMENT"):
                subject.advance_final_two_new_science(
                    self.course,self.repo,self.private,
                    execute=True,transfer=True,capability={},
                    review_one=lambda raw,activity,private:{"activitiesAssessed":1})

    def test_one_unknown_stops_before_second_paid_call(self):
        self.historical()
        calls=[]
        with patch.object(subject,"verified_new_provider_capability",return_value=True),patch.object(
            subject,"verify_persisted_two_role_science",return_value={
                "pass":False,"repair":False,"uncertain":True}):
            report=subject.advance_final_two_new_science(
                self.course,self.repo,self.private,
                execute=True,transfer=True,capability={},
                review_one=lambda raw,activity,private:
                    (calls.append(activity) or {"activitiesAssessed":1}))
        self.assertEqual(len(calls),1)
        self.assertEqual(report["status"],"FINAL_TWO_STOP_UNCERTAIN_OR_BOUNDED")
        self.assertFalse(report["allNewScientificPass"])
        self.assertTrue(report["historicalUnknownProviderRolesReplayed"] is False)

    def test_incomplete_previous_new_role_stops_before_resubmission(self):
        self.historical()
        first=subject.stage_final_two_new_inputs(
            self.course,self.repo,self.private)[0]
        (self.private/("v3-generated-"+first["sha"])).mkdir()
        with patch.object(subject,"verified_new_provider_capability",return_value=True):
            with self.assertRaisesRegex(ValueError,"OLD_REQUEST_UNRESOLVED_NO_REPLAY"):
                subject.advance_final_two_new_science(
                    self.course,self.repo,self.private,
                    execute=True,transfer=True,capability={},
                    review_one=lambda raw,activity,private:
                        self.fail("No provider call permitted on uncertain prior claim"))


if __name__=="__main__":
    unittest.main()

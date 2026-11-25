"""BSA-201: actual frozen 9.6 source; synthetic independent scientific FAIL.

All provider responses in these tests are explicitly synthetic. They exercise
the same immutable production JSON/role/aggregate recovery path but NEVER
count as real Gemini scientific reviews.
"""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
from types import SimpleNamespace
import unittest

from app_generator.runtime.v3_section96_scientific_failure_repair import (
    stage_known_section96_scientific_failure,
    _INDEX, _ACTIVITY, _BAD_ZH, _CHANGED,
)
from app_generator.runtime.v3_frozen_original_tail import (
    plan_frozen_original_tail, stage_frozen_original_tail_slice,
    reserve_frozen_original_tail_attempt,
)
from app_generator.runtime.v3_authorized_review import advance_v3_generated_text
from app_generator.validation.autonomous_completion import package_identity
from tests.test_v3_historical_role_rollforward import RealSourceRollforwardTests
from tests.test_v3_authorized_execution_bridge import FakeReviewer


class SyntheticFloorAndTranslationFailure(FakeReviewer):
    def ask(self,prompt,*,stage=None):
        report=json.loads(super().ask(prompt,stage=stage))
        report["dimensions"]["physicsAnswer"]="FAIL"
        report["dimensions"]["trilingualMeaning"]="FAIL"
        report["rationales"]["physicsAnswer"]=(
            "SYNTHETIC: An off-centre push on a floor has opposing normal-force torque.")
        report["rationales"]["trilingualMeaning"]=(
            "SYNTHETIC: The Chinese uses an erroneous centre-of-mass term.")
        report["concern"]=(
            "SYNTHETIC floor contact forces and Chinese wording need correction.")
        return json.dumps(report)


class Section96ScientificFailureRepairTests(unittest.TestCase):
    def setUp(self):
        # Existing real-section content fixture creates an exact source-bound
        # old index5 AMBIGUOUS reviewer, with fake transport clearly marked.
        fx=RealSourceRollforwardTests(
            methodName="test_exact_authentic_section96_fork_and_restart")
        fx.setUp()
        self.addCleanup(fx.doCleanups)
        self.fx=fx
        self.repo=fx.repo
        self.course=fx.course
        self.private=fx.private
        self.original=fx.raw
        self.hist=fx.stage()
        raw,info=stage_frozen_original_tail_slice(
            self.course,self.repo,self.private,
            section="section-9-6",index=_INDEX)
        reserve_frozen_original_tail_attempt(
            self.private,source_sha=info["sourcePackageSha256"],
            index=_INDEX,slice_sha=info["slicePackageSha256"])
        sessions=(
            SimpleNamespace(reviewer_id="v3-gemini-api-physics",
                            session_id="synthetic-physics",
                            provider_id="gemini_api",
                            conversation=SyntheticFloorAndTranslationFailure()),
            SimpleNamespace(reviewer_id="v3-gemini-api-semantics",
                            session_id="synthetic-semantic",
                            provider_id="gemini_api",
                            conversation=SyntheticFloorAndTranslationFailure()),
        )
        results=advance_v3_generated_text(
            raw,sessions,private_root=self.private,
            generated_content_transfer_allowed=True,max_activities=1)
        self.assertEqual(results["modelRepairRequiredActivities"],1)
        tail=plan_frozen_original_tail(
            self.course,self.repo,self.private,section="section-9-6")
        row=next(x for x in tail["rows"] if x["index"]==_INDEX)
        self.assertEqual(row["state"],"SUPPLEMENTAL_SCIENTIFIC_REPAIR_REQUIRED")
        self.digest=info["slicePackageSha256"]
        self.batch=self.private/("v3-generated-"+self.digest)/"batches"
        self.files=tuple(
            self.batch/f"v3-review-{self.digest[:12]}-000-{i}.json"
            for i in (0,1))
        self.aggregate=self.batch/f"v3-assessment-{self.digest}.json"
        self.roles=tuple(sha256(x.read_bytes()).hexdigest() for x in self.files)
        self.report_sha=sha256(self.aggregate.read_bytes()).hexdigest()

    def stage(self):
        return stage_known_section96_scientific_failure(
            self.course,self.repo,self.private,
            expected_role_shas=self.roles,
            expected_aggregate_sha=self.report_sha)

    def test_real_original_source_scientific_repair_is_one_new_version(self):
        first=self.stage()
        self.assertEqual(first["status"],
                         "NEW_SECTION96_SCIENCE_REPAIR_STAGED_REVIEW_NOT_AUTHORIZED")
        self.assertEqual(first["paidGeminiCalls"],0)
        self.assertFalse(first["newModelConsensusPassClaimed"])
        self.assertFalse(first["versionedScopeAdmitted"])
        self.assertFalse(first["publicationAuthorized"])
        original_sha,old=package_identity(self.original)
        old_parent=self.private/"historical-role-rollforward"/"section-9-6"/(
            self.hist["candidatePackageSha256"])/"package.json"
        old_revision_sha,old_revision=package_identity(old_parent.read_bytes())
        new_file=(self.private/"scientific-failure-rollforward"/"section-9-6"/
                  first["candidatePackageSha256"]/"package.json")
        new_sha,new=package_identity(new_file.read_bytes())
        self.assertEqual(new_sha,first["candidatePackageSha256"])
        self.assertEqual([i for i,(a,b) in enumerate(zip(old,new)) if a!=b],
                         [5,_INDEX])
        self.assertEqual([i for i,(a,b) in enumerate(zip(old_revision,new))
                          if a!=b],[_INDEX])
        self.assertNotIn("floor",new[_INDEX]["prompt"]["en"])
        self.assertIn("floating freely",new[_INDEX]["prompt"]["en"])
        self.assertIn("terapung bebas",new[_INDEX]["prompt"]["ms"])
        self.assertNotIn(_BAD_ZH,json.dumps(new[_INDEX],ensure_ascii=False))
        self.assertEqual(
            old[_INDEX]["interaction"]["placements"],
            new[_INDEX]["interaction"]["placements"])
        self.assertEqual(self.stage(),first)
        self.assertEqual(self.original,
                         (self.course/"section-9-6"/"package.json").read_bytes())
        self.assertEqual(old_parent.read_bytes(),
                         old_parent.read_bytes())
        self.assertEqual(
            next(x for x in plan_frozen_original_tail(
                self.course,self.repo,self.private)["rows"]
                 if x["index"]==_INDEX)["state"],
            "SUPPLEMENTAL_SCIENTIFIC_REPAIR_REQUIRED")

    def test_new_one_activity_input_is_not_old_request_or_model_pass(self):
        state=self.stage()
        path=(self.private/"scientific-failure-review-inputs"/"section-9-6"/
              state["isolatedReviewInputSha256"]/"package.json")
        digest,one=package_identity(path.read_bytes())
        self.assertEqual(digest,state["isolatedReviewInputSha256"])
        self.assertEqual(len(one),1)
        self.assertEqual(one[0]["id"],_ACTIVITY)
        self.assertNotEqual(digest,self.digest)
        receipt=json.loads((path.parent/"review-required.json").read_text(
            encoding="utf8"))
        self.assertEqual(receipt["status"],"PENDING_SEPARATE_PAID_AUTHORIZATION")
        self.assertFalse(receipt["newModelConsensusPassClaimed"])
        self.assertFalse(receipt["publicationAuthorized"])
        self.assertEqual(list(self.private.glob("scientific-failure-review-inputs/section-9-6/*/package.json")),
                         [path])

    def test_change_both_old_reviewer_claims_refuses_without_repair(self):
        before=(self.private/"scientific-failure-rollforward")
        for file in self.files:
            original=file.read_bytes()
            try:
                file.write_bytes(original+b" ")
                with self.assertRaisesRegex(
                        ValueError,"ROLE_WITNESS_CHANGED"):
                    self.stage()
                self.assertFalse(before.exists())
            finally:
                file.write_bytes(original)

    def test_tampered_failed_aggregate_is_not_read_as_genuine_review(self):
        old=self.aggregate.read_bytes()
        self.aggregate.write_bytes(old+b" ")
        try:
            with self.assertRaises(ValueError):
                self.stage()
            self.assertFalse((self.private/"scientific-failure-rollforward").exists())
        finally:
            self.aggregate.write_bytes(old)

    def test_old_candidate_tampering_refuses_before_new_artifact(self):
        path=(self.private/"historical-role-rollforward"/"section-9-6"/
              self.hist["candidatePackageSha256"]/"package.json")
        original=path.read_bytes()
        path.write_bytes(original+b" ")
        try:
            with self.assertRaises(ValueError):
                self.stage()
            self.assertFalse((self.private/"scientific-failure-rollforward").exists())
        finally:
            path.write_bytes(original)

    def test_restage_rejects_modified_immutable_scientific_proposal(self):
        first=self.stage()
        file=(self.private/"scientific-failure-rollforward"/"section-9-6"/
              first["candidatePackageSha256"]/"package.json")
        file.write_bytes(file.read_bytes()+b" ")
        with self.assertRaisesRegex(
                ValueError,"EXISTING_IDENTITY_CONFLICT"):
            self.stage()

    def test_registered_scientific_repair_runs_in_normal_sourcefree_worker(self):
        from unittest.mock import patch
        from app_generator.runtime.v3_source_free_forward import (
            advance_source_free_until_boundary,read_source_free_checkpoint,
        )
        original_bytes=(self.course/"section-9-6"/"package.json").read_bytes()
        attempts=tuple(file.read_bytes() for file in self.files)
        reviewer_calls=[]
        def actual_sourcefree_stage(course,repo,private):
            reviewer_calls.append("sourcefree")
            return stage_known_section96_scientific_failure(
                course,repo,private,expected_role_shas=self.roles,
                expected_aggregate_sha=self.report_sha)
        def noop_recovery(course,private,plan):
            return {"publicationAuthorized":False,"repairStaged":False,
                    "repairStatus":"NO_NEW_SECTION92_REPAIR_IN_TEST_FIXTURE"}
        with patch(
            "app_generator.runtime.v3_source_free_forward.stage_known_section96_scientific_failure",
            side_effect=actual_sourcefree_stage
        ):
            first=advance_source_free_until_boundary(
                self.course,self.repo,self.private,repair=noop_recovery)
            second=advance_source_free_until_boundary(
                self.course,self.repo,self.private,repair=noop_recovery)
        self.assertEqual(reviewer_calls,["sourcefree","sourcefree"])
        self.assertEqual(first["scientificFailureRepair"]["status"],
                         "NEW_SECTION96_SCIENCE_REPAIR_STAGED_REVIEW_NOT_AUTHORIZED")
        self.assertEqual(second["scientificFailureRepair"],
                         first["scientificFailureRepair"])
        self.assertEqual(first["paidGeminiCalls"],0)
        self.assertFalse(first["publicationAuthorized"])
        self.assertFalse(first["versionedScopeAdmitted"])
        self.assertEqual(read_source_free_checkpoint(self.private)
                         ["publicationAuthorized"],False)
        self.assertEqual((self.course/"section-9-6"/"package.json").read_bytes(),
                         original_bytes)
        self.assertEqual(tuple(file.read_bytes() for file in self.files),
                         attempts)

    def test_forged_pass_role_does_not_justify_synthetic_failure_repair(self):
        original=self.files[1].read_bytes()
        old_hashes=self.roles
        try:
            claim=json.loads(original)
            claim["decision"]["dimensions"]["physicsAnswer"]="PASS"
            self.files[1].write_text(json.dumps(claim),encoding="utf8")
            self.roles=(
                old_hashes[0],
                sha256(self.files[1].read_bytes()).hexdigest())
            with self.assertRaises(ValueError):
                self.stage()
            self.assertFalse((self.private/"scientific-failure-rollforward").exists())
        finally:
            self.files[1].write_bytes(original)
            self.roles=old_hashes

    def test_verified_local_scientific_fail_not_mistaken_for_api_outage(self):
        from app_generator.runtime.v3_provider_restoration import (
            _verified_separate_scientific_fail_repair,
        )
        self.stage()
        tail=plan_frozen_original_tail(self.course,self.repo,self.private)
        def verified(report=tail):
            return _verified_separate_scientific_fail_repair(
                self.private,report,expected_role_shas=self.roles,
                expected_aggregate_sha=self.report_sha)
        self.assertTrue(verified())
        # Actual pinned hashes cannot be replaced by synthetic reviewer
        # claims, and the ordinary provider circuit must keep its STOP.
        self.assertFalse(_verified_separate_scientific_fail_repair(
            self.private,tail))
        bad={**tail,"supplemental":{**tail["supplemental"],"failed":2}}
        self.assertFalse(verified(bad))
        wrong_rows={**tail,"rows":[
            {**row,"state":"SUPPLEMENTAL_SCIENTIFIC_REPAIR_REQUIRED"}
            if row["index"]==8 else row for row in tail["rows"]]}
        self.assertFalse(verified(wrong_rows))
        file=(self.private/"scientific-failure-rollforward"/"section-9-6"/
              self.stage()["candidatePackageSha256"]/"review-required.json")
        prior=file.read_bytes()
        try:
            file.write_bytes(prior+b" ")
            self.assertFalse(verified())  # immutable receipt bytes must match
            file.write_text('{"publicationAuthorized":true}',encoding="utf8")
            self.assertFalse(verified())
        finally:
            file.write_bytes(prior)
        original=self.files[1].read_bytes()
        try:
            self.files[1].write_bytes(original+b" ")
            self.assertFalse(verified())
        finally:
            self.files[1].write_bytes(original)

    def test_no_failure_evidence_does_not_claim_repair(self):
        # The normal source-free path is safe for freshly unreviewed
        # Section9.6 content. Inject no role witness; model is never called.
        old=self.roles
        self.roles=("0"*64,"1"*64)
        try:
            with self.assertRaisesRegex(ValueError,"ROLE_WITNESS_CHANGED"):
                self.stage()
        finally:
            self.roles=old


if __name__=="__main__":
    unittest.main()

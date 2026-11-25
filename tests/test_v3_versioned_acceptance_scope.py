"""V3 corrected-course proposal: exact original real evidence, no new PASS.

This module runs only source-free tests using repository frozen packages.
Never borrows actual user model responses in test fixtures.
"""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from app_generator.runtime.v3_auto_repair import (
    _ACTIVITY, _CANDIDATE, _CHANGES,
)
from app_generator.runtime.v3_versioned_acceptance_scope import (
    prepare_versioned_course_proposal,
)
from app_generator.validation.v3_versioned_text_repair import (
    make_locale_repair, store_private_repair,
)

REPO = Path(__file__).resolve().parents[1]
COURSE = REPO / "content" / "chapter-9"
ORIGINAL = COURSE / "section-9-2" / "package.json"


class VersionedCourseProposalTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.private = Path(temp.name) / "private"
        parent = ORIGINAL.read_bytes()
        self.parent = parent
        candidate, receipt = make_locale_repair(
            parent, _ACTIVITY, "ms", _CHANGES)
        self.candidate = store_private_repair(
            self.private / "repair-proposals" / "section-9-2",
            candidate, receipt)

    def propose(self):
        return prepare_versioned_course_proposal(
            COURSE, REPO, self.private)

    def saved(self, result):
        file = (self.private / "versioned-course-proposals" /
                result["proposalSha256"] / "scope-proposal.json")
        return json.loads(file.read_text(encoding="utf8"))

    def test_six_section_proposal_pins_only_changed_one_activity(self):
        result = self.propose()
        self.assertEqual(result["status"],
                         "VERSIONED_COURSE_PROPOSAL_STAGED_NOT_ADMITTED")
        self.assertFalse(result["versionedScopeAdmitted"])
        self.assertFalse(result["publicationAuthorized"])
        self.assertEqual(result["remainingOriginalUnassessed"], 108)
        self.assertEqual(result["potentiallyReusableGenuinePasses"], 0)
        data = self.saved(result)
        self.assertEqual(sum(row["activities"] for row in data["sections"]), 108)
        self.assertEqual(len(data["sections"]), 6)
        self.assertEqual(data["correctedActivityId"], _ACTIVITY)
        self.assertEqual(data["correctedActivityIndex"], 13)
        self.assertEqual(data["correctedPackageSha256"], _CANDIDATE)
        self.assertNotEqual(data["oldRosterSha256"],
                            data["proposedRosterSha256"])
        self.assertEqual(
            [row["section"] for row in data["sections"]
             if row["proposedPackageSha256"] != row["originalPackageSha256"]],
            ["section-9-2"])
        self.assertEqual(len(data["potentiallyReusableOriginalPasses"]), 0)
        self.assertEqual(data["counts"]["correctedActivityNewGeminiConsensusPass"],0)
        self.assertIs(data["all108ReviewedAndApproved"], False)
        self.assertEqual(ORIGINAL.read_bytes(), self.parent)

    def test_identical_snapshot_is_idempotent(self):
        a = self.propose()
        b = self.propose()
        self.assertEqual(a,b)
        self.assertEqual(a["proposalSha256"],b["proposalSha256"])

    def test_corrupted_staged_receipt_fails_closed_not_overwritten(self):
        a = self.propose()
        path = (self.private / "versioned-course-proposals" /
                a["proposalSha256"] / "scope-proposal.json")
        path.write_text('{"publicationAuthorized": true}',encoding="utf8")
        with self.assertRaisesRegex(ValueError, "EXISTING_SNAPSHOT_CONFLICT"):
            self.propose()

    def test_stale_corrected_package_rejected_before_proposal(self):
        file = self.candidate / "package.json"
        file.write_bytes(file.read_bytes() + b" ")
        with self.assertRaisesRegex(ValueError, "CANDIDATE_CHANGED"):
            self.propose()
        self.assertFalse((self.private / "versioned-course-proposals").exists())

    def test_crash_before_proposal_promotion_restarts_cleanly(self):
        # Stage the dependencies first to guarantee the injected failure is
        # specifically in the new versioned acceptance proposal promotion.
        from app_generator.runtime.v3_isolated_repair_review import (
            stage_isolated_review_slice,
        )
        stage_isolated_review_slice(COURSE,self.private,_CANDIDATE)
        with patch(
                "app_generator.runtime.v3_versioned_acceptance_scope.Path.rename",
                side_effect=OSError("synthetic power loss at proposal commit")):
            with self.assertRaisesRegex(OSError, "synthetic power loss"):
                self.propose()
        root = self.private / "versioned-course-proposals"
        self.assertFalse(any(root.iterdir()))
        a=self.propose()
        self.assertTrue((root/a["proposalSha256"]/"scope-proposal.json").is_file())

    def test_forged_private_review_does_not_promote_inherited_passes(self):
        parent_sha = sha256(self.parent).hexdigest()
        file = (self.private / ("v3-generated-" + parent_sha) /
                "batches" / ("v3-assessment-" + parent_sha + ".json"))
        file.parent.mkdir(parents=True)
        file.write_text(json.dumps({
            "contract":"AUTONOMOUS_AI_TECHNICAL_COMPLETION_V3",
            "packageSha256": parent_sha,
            "reviews":[{"activityId":_ACTIVITY,"status":"AI_CONSENSUS_PASS"}],
        }))
        with self.assertRaises(ValueError):
            self.propose()
        self.assertFalse((self.private / "versioned-course-proposals").exists())

    def test_no_private_source_or_reviewer_rationale_saved_in_proposal(self):
        a=self.propose()
        path=(self.private / "versioned-course-proposals" /
              a["proposalSha256"]/"scope-proposal.json")
        raw=path.read_text(encoding="utf8")
        self.assertNotIn("sebuah kereta luncur",raw)
        self.assertNotIn("SYNTHETIC",raw)
        self.assertIn("VERSIONED_COURSE_PROPOSAL_V1",raw)
        self.assertNotIn("activityText", raw)
        self.assertFalse(self.saved(a)["publicationAuthorized"])

    def test_original_progress_is_not_inferred_from_new_private_slice(self):
        self.propose()
        # Pre-staging both new repair slice and proposed roster cannot change
        # original accepted package or its genuine reviewer counts.
        from app_generator.runtime.v3_course_review import plan_v3_course_review
        current=plan_v3_course_review(
            COURSE, REPO, private_root=self.private,
            continue_independent=True)
        self.assertEqual(current["activitiesAssessedRows"],0)
        self.assertEqual(current["modelConsensusPassActivities"],0)
        self.assertEqual(current["nextSection"],"section-9-1")


    def test_fresh_two_context_synthetic_model_pass_updates_only_proposal(self):
        from app_generator.runtime.v3_isolated_repair_review import (
            stage_isolated_review_slice,
        )
        from app_generator.runtime.v3_authorized_review import advance_v3_generated_text
        from app_generator.validation.autonomous_ai_review import ReviewerSession
        from tests.test_v3_isolated_repair_review import FakeGeminiConversation
        before = self.propose()
        self.assertEqual(before["correctedActivityNewGeminiConsensusPass"], 0)
        staged = stage_isolated_review_slice(COURSE,self.private,_CANDIDATE)
        single = (self.private / "single-activity-review-slices" /
                  staged["reviewSliceSha256"] / "package.json").read_bytes()
        pair = (
            ReviewerSession("v3-gemini-api-physics","SYNTHETIC-new-p",
                            FakeGeminiConversation(),provider_id="gemini_api"),
            ReviewerSession("v3-gemini-api-semantics","SYNTHETIC-new-s",
                            FakeGeminiConversation(),provider_id="gemini_api"),
        )
        reported = advance_v3_generated_text(
            single, pair, private_root=self.private,
            generated_content_transfer_allowed=True, max_activities=1)
        self.assertEqual(reported["modelConsensusPassActivities"],1)
        later=self.propose()
        self.assertNotEqual(before["proposalSha256"],later["proposalSha256"])
        self.assertEqual(later["correctedActivityNewGeminiConsensusPass"],1)
        self.assertEqual(later["correctedActivityScientificStatus"],
                         "GENUINE_CORRECTED_MODEL_PASS_PROPOSED_NOT_ADMITTED")
        snapshot=self.saved(later)
        self.assertEqual(snapshot["counts"]["correctedActivityFullyReviewed"],1)
        self.assertEqual(snapshot["potentiallyReusableOriginalPasses"],[])
        self.assertIs(snapshot["versionedScopeAdmitted"],False)
        self.assertIs(snapshot["publicationAuthorized"],False)
        self.assertEqual(ORIGINAL.read_bytes(), self.parent)

    def test_synthetic_revised_language_fail_preserved_as_not_accepted(self):
        from app_generator.runtime.v3_isolated_repair_review import (
            stage_isolated_review_slice,
        )
        from app_generator.runtime.v3_authorized_review import advance_v3_generated_text
        from app_generator.validation.autonomous_ai_review import ReviewerSession
        from tests.test_v3_isolated_repair_review import FakeGeminiConversation
        class FailingLanguage(FakeGeminiConversation):
            def ask(self, prompt, *, stage):
                reply=json.loads(super().ask(prompt,stage=stage))
                reply["dimensions"]["trilingualMeaning"]="FAIL"
                reply["concern"]="SYNTHETIC language error in test fixture"
                return json.dumps(reply)
        staged=stage_isolated_review_slice(COURSE,self.private,_CANDIDATE)
        single=(self.private/"single-activity-review-slices"/
                staged["reviewSliceSha256"]/"package.json").read_bytes()
        roles=(
            ReviewerSession("v3-gemini-api-physics","SYNTHETIC-p",
                            FailingLanguage(),provider_id="gemini_api"),
            ReviewerSession("v3-gemini-api-semantics","SYNTHETIC-s",
                            FailingLanguage(),provider_id="gemini_api"),
        )
        outcome=advance_v3_generated_text(
            single,roles,private_root=self.private,
            generated_content_transfer_allowed=True,max_activities=1)
        self.assertEqual(outcome["modelRepairRequiredActivities"],1)
        new=self.propose()
        self.assertEqual(new["correctedActivityNewGeminiConsensusPass"],0)
        self.assertEqual(new["correctedActivityScientificStatus"],
                         "REVISED_GEMINI_REPAIR_REQUIRED")
        self.assertFalse(new["publicationAuthorized"])

    def test_genuine_shaped_unchanged_tail_pass_updates_only_proposal(self):
        # Source-free model fixtures: NEVER counts as a real Google review.
        from app_generator.runtime.run_context import RunContext
        from app_generator.runtime.v3_frozen_original_tail import (
            stage_frozen_original_tail_slice, reserve_frozen_original_tail_attempt,
        )
        from app_generator.runtime.v3_authorized_review import advance_v3_generated_text
        from app_generator.validation.autonomous_completion import (
            assess_with_models, package_identity,
        )
        from tests.test_autonomous_completion_v3 import FakeModel, sessions
        source = (COURSE/"section-9-6"/"package.json").read_bytes()
        digest, original_items = package_identity(source)
        class SixthUncertain(FakeModel):
            def ask(self, prompt, *, stage=None):
                if self.calls == 5:
                    self.calls += 1
                    raise TimeoutError("SYNTHETIC_NO_PROVIDER_RESULT")
                return super().ask(prompt, stage=stage)
        original_cp=RunContext.create(
            self.private,"v3-generated-"+digest)
        original_evidence=assess_with_models(
            source,sessions(SixthUncertain(),FakeModel()),
            checkpoint=original_cp,generated_content_transfer_allowed=True,
            max_activities=6)
        self.assertEqual(len(original_evidence["reviews"]),6)
        self.assertEqual(original_evidence["reviews"][-1]["status"],"AI_UNCERTAIN")
        prior=self.propose()
        self.assertEqual(prior["potentiallyReusableGenuinePasses"],5)
        self.assertEqual(prior["verifiedSupplementalFrozenOriginalPasses"],0)
        raw,meta=stage_frozen_original_tail_slice(
            COURSE,REPO,self.private,index=6)
        reserve_frozen_original_tail_attempt(
            self.private,source_sha=digest,index=6,
            slice_sha=meta["slicePackageSha256"])
        new_result=advance_v3_generated_text(
            raw,sessions(FakeModel(),FakeModel()),private_root=self.private,
            generated_content_transfer_allowed=True,max_activities=1)
        self.assertEqual(new_result["modelConsensusPassActivities"],1)
        updated=self.propose()
        self.assertNotEqual(prior["proposalSha256"],updated["proposalSha256"])
        self.assertEqual(updated["potentiallyReusableGenuinePasses"],6)
        self.assertEqual(updated["verifiedSupplementalFrozenOriginalPasses"],1)
        self.assertEqual(updated["remainingOriginalUnassessed"],102)
        self.assertEqual(updated["remainingContentUnreviewedAfterSupplemental"],101)
        candidate=self.saved(updated)
        supplemental=candidate["supplementalFrozenOriginalReviews"]
        self.assertEqual(len(supplemental),1)
        self.assertEqual(supplemental[0]["originalActivityIndex"],6)
        self.assertEqual(supplemental[0]["activityId"],original_items[6]["id"])
        self.assertEqual(candidate["counts"]["originalGenuineConsensusPasses"],5)
        self.assertEqual(candidate["counts"]["supplementalFrozenOriginalConsensusPasses"],1)
        self.assertEqual(candidate["counts"]["potentiallyReusablePasses"],6)
        self.assertFalse(updated["versionedScopeAdmitted"])
        self.assertFalse(updated["publicationAuthorized"])
        self.assertEqual((COURSE/"section-9-6"/"package.json").read_bytes(),source)
        # Candidate manifest tampering cannot falsely preserve the PASS link.
        path=(self.private/"frozen-original-review-slices"
              /meta["slicePackageSha256"]/"review-slice.json")
        tampered=json.loads(path.read_text(encoding="utf8"))
        tampered["publicationAuthorized"]=True
        path.write_text(json.dumps(tampered),encoding="utf8")
        with self.assertRaisesRegex(ValueError,
                                   "V3_PROPOSAL_SUPPLEMENT_CHANGED_OR_MISSING"):
            self.propose()


if __name__ == "__main__":
    unittest.main()

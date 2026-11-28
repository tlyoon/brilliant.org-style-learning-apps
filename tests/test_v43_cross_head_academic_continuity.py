"""BSA272: preserve one accepted original-source academic proof across code HEADs.

Negative tests ensure old proof receipt cannot be copied blindly to a new
source/candidate, wrong task, or unsigned/foreign V36 predecessor.
CI uses bounded synthetic signed identity; real Yoga6 must re-open PDF and
recompute all math from the source under two genuine code revisions.
"""
from __future__ import annotations
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch

from app_generator.runtime import v3_academic_cross_head_continuity as continuity
from app_generator.runtime import v3_first_academic_proof_admission as academic

OLD={"gitHead":"a"*40,"proposalSha256":"b"*64}
NEW={"gitHead":"c"*40,"proposalSha256":"b"*64}
SHA_SOURCE=academic._SOURCE_SHA
SHA_CAND=academic._CANDIDATE_SHA


def latest(head=NEW):
    return {
        **head,
        "sourceSha256":SHA_SOURCE,
        "candidateSha256":SHA_CAND,
        "academicAcceptedProofTaskCount":0,
        "fullSemanticProofTasksStillOpen":429,
        "completeAcademicProofGatesStillOpen":90,
    }


def frontier(head=OLD):
    return {
        **head,
        "sourceSha256":SHA_SOURCE,
        "candidateSha256":SHA_CAND,
        "taskId":academic._ID,
        "proofReceiptSha256":"d"*64,
        "acceptedAcademicTaskCount":1,
        "fullSemanticProofTasksStillOpen":428,
        "completeAcademicProofGatesStillOpen":90,
    }


def admitted():
    return {
        "independentlyAcceptedAcademicTasks":1,
        "otherFullAcademicTasksStillOpen":428,
        "taskId":academic._ID,
        "completeAcademicProofGatesStillOpen":90,
        "proofReceiptSha256":"d"*64,
        "publicationAuthorized":False,
    }


class CrossHeadAcademicProof(TestCase):
    def run_guard(self,newproof=None,oldproof=None,source=None,overlay=None):
        proof={"taskId":academic._ID,"status":academic._CLAIM,
               "sourceSha256":SHA_SOURCE,"candidateSha256":SHA_CAND,
               "taskKind":"MCQ_DISTRACTOR_SCIENCE",
               "acceptedAcademicTaskCount":1,
               "remainingFullAcademicTasks":428,
               "completeAcademicProofGatesStillOpen":90,
               "otherTrilingualMeaningProofAccepted":False,
               "publicationAuthorized":False,
               "newGeminiCalls":0}
        real=proof if newproof is None else newproof
        prior=proof if oldproof is None else oldproof
        state=latest() if source is None else source
        signed_overlay=frontier() if overlay is None else overlay
        with (patch.object(continuity,"read_long_horizon_development",
                           return_value=state),
              patch.object(continuity,"_read_signed",
                           return_value=signed_overlay),
              patch.object(continuity,"verify_first_academic_frontier",
                           return_value=admitted()) as verifier,
              patch.object(continuity,"_bound_inputs",
                           return_value=(Path("/tmp"),
                                         {"semanticTasksAutomaticallyDispatched":429},
                                         {"activity":{"activityId":"act-mcq-01-vector-nature"}},
                                         Path("/tmp/source.pdf"),
                                         Path("/tmp/candidate.json"))) as new_binding,
              patch.object(continuity,"independent_distractor_science",
                           return_value=real),
              patch.object(continuity,"_signed",return_value={
                  "integritySha256":"d"*64,
                  "independentTaskProof":prior})):
            result=continuity.verify_academic_across_git_heads(
                private=Path("/tmp"))
        return result,verifier.call_args,new_binding.call_args

    def test_same_source_cross_git_head_preserves_single_accepted_task(self):
        result,verify,binding=self.run_guard()
        self.assertTrue(result["carriedAcrossGitHead"])
        self.assertEqual(result["acceptedAcademicTasks"],1)
        self.assertEqual(result["fullAcademicTasksStillOpen"],428)
        self.assertEqual(result["completeAcademicProofGatesStillOpen"],90)
        self.assertEqual(result["currentGitHead"],NEW["gitHead"])
        self.assertEqual(result["academicProofOriginGitHead"],OLD["gitHead"])
        self.assertEqual(verify.kwargs["ready"],OLD)
        self.assertTrue(verify.kwargs["allow_historical"])
        self.assertEqual(binding.args[1],NEW)

    def test_changed_textbook_in_current_revision_blocks_reuse(self):
        state=latest();state["sourceSha256"]="f"*64
        with self.assertRaisesRegex(ValueError,
                                    "ORIGINAL_TEXTBOOK_OR_CANDIDATE_CHANGED"):
            self.run_guard(source=state)

    def test_changed_frozen_candidate_blocks_reuse(self):
        state=latest();state["candidateSha256"]="f"*64
        with self.assertRaisesRegex(ValueError,
                                    "ORIGINAL_TEXTBOOK_OR_CANDIDATE_CHANGED"):
            self.run_guard(source=state)

    def test_old_receipt_must_recompute_to_exact_new_task(self):
        with self.assertRaisesRegex(ValueError,
                                    "NEW_HEAD_PROOF_NOT_SAME_SOURCE_BOUND_TASK"):
            self.run_guard(oldproof={"taskId":"forged"})

    def test_historical_signed_v36_receipt_required(self):
        proofstate=latest()
        origin_state={
            **OLD,
            "sourceSha256":SHA_SOURCE,
            "candidateSha256":SHA_CAND,
            "academicAcceptedProofTaskCount":0,
            "fullSemanticProofTasksStillOpen":429,
            "completeAcademicProofGatesStillOpen":90,
            "signedV36ReceiptSha256":"f"*64,
        }
        signed_v36={
            "status":academic._STATUS36,
            "sourceSha256":SHA_SOURCE,
            "revisedCandidateSha256":SHA_CAND,
            "semanticTasksAutomaticallyDispatched":429,
            "activitySignedPartitionCount":18,
            "fullAcademicProofTasksAccepted":0,
            "completeAcademicProofGatesStillOpen":90,
            "publicationAuthorized":False,
            "integritySha256":"d"*64,
        }
        with (patch.object(academic,"read_long_horizon_development",
                           return_value=proofstate),
              patch.object(academic,"_read_signed",return_value=origin_state),
              patch.object(academic,"_signed",return_value=signed_v36)):
            with self.assertRaisesRegex(ValueError,
                                        "HISTORICAL_SOURCE_FREE_RECEIPT_MISMATCH"):
                academic._bound_inputs(Path("/tmp"),OLD,allow_historical=True)

    def test_historical_receipt_forbidden_without_explicit_reverification(self):
        with patch.object(academic,"read_long_horizon_development",
                          return_value=latest()):
            with self.assertRaisesRegex(ValueError,
                                        "PRIOR_ACADEMIC_RECEIPT_REQUIRES_EXPLICIT_RECHECK"):
                academic._bound_inputs(Path("/tmp"),OLD)

    def test_frontier_reader_is_wired_to_cross_head_reverification(self):
        repo=Path(__file__).resolve().parents[1]
        src=(repo/"scripts"/"show_bosla_long_horizon.py").read_text(encoding="utf8")
        self.assertIn("verify_academic_across_git_heads(private=private)",src)
        cli=(repo/"scripts"/"run_bosla_first_academic_proof.py").read_text(encoding="utf8")
        self.assertIn("verify_academic_across_git_heads(private=private)",cli)

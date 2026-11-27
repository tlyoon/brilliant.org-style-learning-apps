"""BSA281 signed original-source MCQ05 academic admission isolation tests.

These mocks test security/ordering, not science acceptance. Genuine owner
source PDF + candidate, signed V36 partition 05, all earlier receipts and
private horizon readback are independently exercised on authorized Yoga6.
"""
from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch

from app_generator.runtime import v3_third_law_academic_batch_admission as admit

HEAD="a"*40
PROPOSAL="b"*64
IDS=list(admit._TASK_IDS.values())

def prior():
    return {
        "independentlyAcceptedAcademicTasks":12,
        "fullAcademicTasksStillOpen":417,
        "pendingMcqDistractorScienceTasks":15,
        "acceptedAcademicTaskIds":["prior-"+str(n) for n in range(12)],
        "gliderBatchReceiptSha256":"c"*64,
        "completeAcademicProofGatesStillOpen":90,
        "fullAcademicActivityPASS":0,
        "publicationAuthorized":False,
    }

class ThirdLawSignedAdmissionTests(TestCase):
    def test_prior_a1_a12_must_really_have_signed_twelve(self):
        for changed in (
            {"independentlyAcceptedAcademicTasks":11},
            {"fullAcademicTasksStillOpen":418},
            {"pendingMcqDistractorScienceTasks":16},
            {"fullAcademicActivityPASS":1},
            {"publicationAuthorized":True},
        ):
            with self.subTest(changed=changed):
                payload={**prior(),**changed}
                with patch.object(admit,"verify_paired_glider_batch_across_git_heads",
                                  return_value=payload):
                    with self.assertRaisesRegex(ValueError,"A1_A12"):
                        admit._prior_twelve(Path("private"))

    def test_live_admission_needs_authentic_old_proofs_before_sign(self):
        with TemporaryDirectory() as t:
            private=Path(t)
            with patch.object(admit,"_prior_twelve",
                              side_effect=ValueError("NO_PRIOR_SOURCE_PROOF")), \
                 patch.object(admit,"_v6_checkpoint") as sign:
                with self.assertRaisesRegex(ValueError,"NO_PRIOR_SOURCE_PROOF"):
                    admit.admit_third_law_batch(private=private)
                sign.assert_not_called()

    def test_live_admission_rejects_duplicate_task_ids_without_signature(self):
        with TemporaryDirectory() as t:
            private=Path(t)
            proofs=[
                {"taskId":IDS[0],"optionId":"opt-b"},
                {"taskId":IDS[1],"optionId":"opt-c"},
                {"taskId":"prior-1","optionId":"opt-d"},
            ]
            with (patch.object(admit,"_prior_twelve",return_value=prior()),
                  patch.object(admit,"read_long_horizon_development",
                    return_value={"gitHead":HEAD,"proposalSha256":PROPOSAL}),
                  patch.object(admit,"verify_registry_audit",
                    return_value={"gitHead":HEAD,"signedV36Sha256":"d"*64,
                                  "independentlyAcceptedAcademicTasks":2,
                                  "registryReceiptSha256":"e"*64}),
                  patch.object(admit,"_original_third_law_proofs",
                    return_value=({"integritySha256":"d"*64},
                                  {"integritySha256":"f"*64},proofs)),
                  patch.object(admit,"_v6_checkpoint") as sign):
                with self.assertRaisesRegex(ValueError,"TASK_DUPLICATE"):
                    admit.admit_third_law_batch(private=private)
                sign.assert_not_called()

    def test_existing_unverified_frontier_never_reissued_or_repaired_with_forgery(self):
        with TemporaryDirectory() as t:
            private=Path(t)
            path=private/"long-horizon-development"/admit._FRONTIER
            path.parent.mkdir(parents=True)
            path.write_text('{"cumulativeAcademicTasksAccepted":15}')
            with (patch.object(admit,"verify_third_law_batch_across_git_heads",
                               side_effect=ValueError("BAD_SIGNATURE")),
                  patch.object(admit,"_v6_checkpoint") as sign):
                with self.assertRaisesRegex(ValueError,"BAD_SIGNATURE"):
                    admit.admit_third_law_batch(private=private)
                sign.assert_not_called()

    def test_cross_head_verifier_rejects_nonzero_activity_pass(self):
        with TemporaryDirectory() as t:
            private=Path(t)
            frontier={
                "status":admit._FRONTIER_STATUS,
                "sourceSha256":admit._SOURCE_SHA,
                "candidateSha256":admit._CANDIDATE_SHA,
                "gitHead":HEAD,
                "proposalSha256":PROPOSAL,
                "cumulativeAcademicTasksAccepted":15,
                "fullAcademicTasksStillOpen":414,
                "pendingMcqDistractorScienceTasks":12,
                "completeAcademicProofGatesStillOpen":90,
                "fullAcademicActivityPASS":1,
                "publicationAuthorized":False,
            }
            with (patch.object(admit,"_read_signed",return_value=frontier),
                  patch.object(admit,"read_long_horizon_development",
                    return_value={
                        "gitHead":HEAD,"proposalSha256":PROPOSAL,
                        "sourceSha256":admit._SOURCE_SHA,
                        "candidateSha256":admit._CANDIDATE_SHA,
                    }),
                  patch.object(admit,"_verify_receipt") as verify):
                with self.assertRaisesRegex(ValueError,"FRONTIER_UNVERIFIED"):
                    admit.verify_third_law_batch_across_git_heads(private=private)
                verify.assert_not_called()

    def test_reviewer_cannot_turn_signed_proof_into_public_authorization(self):
        proof={
            "accepted":15,"newProviderCalls":0,
            "fullActivityPASS":0,"publicationAuthorized":False,
        }
        self.assertEqual(proof["accepted"],15)
        self.assertEqual(proof["fullActivityPASS"],0)
        self.assertFalse(proof["publicationAuthorized"])

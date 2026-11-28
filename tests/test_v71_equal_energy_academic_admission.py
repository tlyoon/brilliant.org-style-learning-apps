"""A19-A21 admission must rederive the signed source task partition."""
from __future__ import annotations

from pathlib import Path
from unittest import TestCase
from unittest.mock import patch

from app_generator.runtime import v3_equal_energy_academic_batch_admission as a


class EqualEnergyAdmission(TestCase):
    def test_prior_signed_eighteen_is_mandatory(self):
        good = {"independentlyAcceptedAcademicTasks": 18,
                "fullAcademicTasksStillOpen": 411,
                "pendingMcqDistractorScienceTasks": 9,
                "acceptedAcademicTaskIds": [str(i) for i in range(18)],
                "completeAcademicProofGatesStillOpen": 90,
                "fullAcademicActivityPASS": 0,
                "publicationAuthorized": False}
        with patch.object(a, "verify_equal_speed_batch_across_git_heads", return_value=good):
            self.assertEqual(a._prior_eighteen(None), good)
        for field, value in (("independentlyAcceptedAcademicTasks", 16),
                             ("fullAcademicActivityPASS", 1),
                             ("publicationAuthorized", True)):
            bad = {**good, field: value}
            with self.subTest(field=field), patch.object(
                    a, "verify_equal_speed_batch_across_git_heads", return_value=bad):
                with self.assertRaisesRegex(ValueError, "A1_A18_CHAIN"):
                    a._prior_eighteen(None)

    def test_partition_task_and_science_are_independently_rechecked(self):
        ready = {"gitHead": "a"*40, "proposalSha256": "b"*64}
        v36 = {"signedPartitionHashes": [{} for _ in range(18)],
               "semanticTasksAutomaticallyDispatched": 429,
               "fullAcademicProofTasksAccepted": 0,
               "completeAcademicProofGatesStillOpen": 90,
               "sourceSha256": a._SOURCE_SHA,
               "publicationAuthorized": False}
        v36["signedPartitionHashes"][6] = {
            "activityId": "act-mcq-07-equal-ke-momentum-relation",
            "signedEvidenceSha256": "signed-seventh"}
        ids={option: chr(97+i)*64 for i,option in enumerate(a._OPTIONS_ORDER)}
        rows = [{"taskId": task, "kind": "MCQ_DISTRACTOR_SCIENCE",
                 "status": "BOUNDED_SUPPORT_ONLY_REVIEW_REQUIRED",
                 "surfaceSha256": "surface-"+option}
                for option, task in ids.items()]
        partition = {"integritySha256": "signed-seventh",
                     "activity": {"activityId": "act-mcq-07-equal-ke-momentum-relation",
                                  "evidenceRows": rows},
                     "sourceSha256": a._SOURCE_SHA,
                     "candidateSha256": a._CANDIDATE_SHA,
                     "academicPASS": 0,
                     "publicationAuthorized": False}
        def producer(*, source_pdf, candidate_path, option_id):
            return {"taskId": ids[option_id], "optionId": option_id,
                    "surfaceSha256": "surface-"+option_id,
                    "sourceSha256": a._SOURCE_SHA,
                    "candidateSha256": a._CANDIDATE_SHA,
                    "newProviderCalls": 0, "publicationAuthorized": False}
        def run(part):
            with (patch.object(a, "_bound_inputs", return_value=(None, v36, None, "source", "candidate")),
                  patch.object(a, "_signed", return_value=part),
                  patch.object(a, "independently_prove_equal_energy_false_option", side_effect=producer),
                  patch.object(a, "independently_check_equal_energy_witness")):
                return a._original_equal_energy_proofs(private=Path("."), ready=ready, historical=False)
        _, _, proofs = run(partition)
        self.assertEqual([p["taskId"] for p in proofs], list(ids.values()))
        for changed in ("taskId", "surfaceSha256", "status"):
            altered = {**partition, "activity": {**partition["activity"],
                "evidenceRows": [dict(row) for row in rows]}}
            altered["activity"]["evidenceRows"][0][changed] = "forged"
            with self.subTest(changed=changed), self.assertRaisesRegex(
                    ValueError, "FALSE_OPTION_NOT_REPROVEN"):
                run(altered)
        wrong = {**partition, "integritySha256": "forged"}
        with self.assertRaisesRegex(ValueError, "PARTITION_CHANGED"):
            run(wrong)

    def test_cross_head_readback_rejects_changed_science_and_task_duplication(self):
        prior={"acceptedAcademicTaskIds":[str(i) for i in range(18)],
               "equalSpeedBatchReceiptSha256":"prior"}
        proofs=[{"taskId":chr(97+i)*64} for i in range(3)]
        frontier={"gitHead":"a"*40,"proposalSha256":"b"*64,
                  "status":a._FRONTIER_STATUS,"sourceSha256":a._SOURCE_SHA,
                  "candidateSha256":a._CANDIDATE_SHA,
                  "cumulativeAcademicTasksAccepted":21,
                  "fullAcademicTasksStillOpen":408,
                  "pendingMcqDistractorScienceTasks":6,
                  "completeAcademicProofGatesStillOpen":90,
                  "fullAcademicActivityPASS":0,"publicationAuthorized":False,
                  "newScientificBatchReceiptSha256":"signed",
                  "previousAcademicTaskIds":prior["acceptedAcademicTaskIds"],
                  "newAcceptedTaskIds":[p["taskId"] for p in proofs]}
        now={"gitHead":"c"*40,"proposalSha256":"d"*64,
             "sourceSha256":a._SOURCE_SHA,"candidateSha256":a._CANDIDATE_SHA}
        receipt={"integritySha256":"signed",
                 "previousEqualSpeedBatchReceiptSha256":"prior"}
        def check(recomputed, old=prior):
            with (patch.object(a,"_read_signed",return_value=frontier),
                  patch.object(a,"read_long_horizon_development",return_value=now),
                  patch.object(a,"_verify_receipt",return_value=(receipt,proofs)),
                  patch.object(a,"_original_equal_energy_proofs",return_value=({}, {}, recomputed)),
                  patch.object(a,"_prior_eighteen",return_value=old)):
                return a.verify_equal_energy_batch_across_git_heads(private=Path("."))
        self.assertTrue(check(proofs)["carriedAcrossGitHead"])
        with self.assertRaisesRegex(ValueError,"SCIENCE_CHANGED_ACROSS_CODE_HEADS"):
            check([{"taskId":"forged"},*proofs[1:]])
        duplicate={**prior,"acceptedAcademicTaskIds":[*prior["acceptedAcademicTaskIds"][:-1],
                                                  proofs[0]["taskId"]]}
        with self.assertRaisesRegex(ValueError,"SCIENCE_CHANGED_ACROSS_CODE_HEADS"):
            check(proofs,old=duplicate)

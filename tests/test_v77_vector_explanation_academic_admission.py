"""BSA292 owner admission and independent historical/current-head controls."""
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch

from app_generator.runtime import v3_vector_explanation_academic_admission as a


class VectorExplanationAdmission(TestCase):
    def test_prior_signed_twenty_seven_is_mandatory(self):
        good = {"independentlyAcceptedAcademicTasks": 27, "fullAcademicTasksStillOpen": 402,
                "pendingMcqDistractorScienceTasks": 0,
                "acceptedAcademicTaskIds": [str(i) for i in range(27)],
                "completeAcademicProofGatesStillOpen": 90, "fullAcademicActivityPASS": 0,
                "publicationAuthorized": False}
        with patch.object(a, "verify_spring_buffer_batch_across_git_heads", return_value=good):
            self.assertEqual(a._prior(None), good)
        for field, value in (("independentlyAcceptedAcademicTasks", 24),
                             ("fullAcademicActivityPASS", 1), ("publicationAuthorized", True)):
            with self.subTest(field=field), patch.object(
                a, "verify_spring_buffer_batch_across_git_heads", return_value={**good, field:value}
            ), self.assertRaisesRegex(ValueError, "A1_A27_CHAIN"):
                a._prior(None)

    def test_partition_task_and_science_are_independently_rechecked(self):
        ready = {"gitHead":"a"*40, "proposalSha256":"b"*64}
        v36 = {"signedPartitionHashes":[{} for _ in range(18)],
               "semanticTasksAutomaticallyDispatched":429, "fullAcademicProofTasksAccepted":0,
               "completeAcademicProofGatesStillOpen":90, "sourceSha256":a._SOURCE_SHA,
               "publicationAuthorized":False}
        v36["signedPartitionHashes"][0] = {"activityId":"act-mcq-01-vector-nature",
                                              "signedEvidenceSha256":"signed-first"}
        row = {"taskId":a._TASK, "kind":"COMPLETE_SCIENTIFIC_MEANING",
               "surfacePath":"explanation", "status":"BOUNDED_SUPPORT_ONLY_REVIEW_REQUIRED",
               "surfaceSha256":"surface"}
        partition = {"integritySha256":"signed-first",
                     "activity":{"activityId":"act-mcq-01-vector-nature", "evidenceRows":[row]},
                     "sourceSha256":a._SOURCE_SHA,"candidateSha256":a._CANDIDATE_SHA,
                     "academicPASS":0,"publicationAuthorized":False}
        proof = {"surfaceSha256":"surface", "newProviderCalls":0,"publicationAuthorized":False}
        def run(part):
            with (patch.object(a,"_bound_inputs",return_value=(None,v36,None,"source","candidate")),
                  patch.object(a,"_signed",return_value=part),
                  patch.object(a,"independently_prove_vector_explanation",return_value=proof),
                  patch.object(a,"independently_check_vector_explanation_witness")):
                return a._original_proof(private=Path("."),ready=ready,historical=False)
        self.assertEqual(run(partition)[2],proof)
        for field in ("taskId","surfaceSha256","status"):
            bad = {**partition,"activity":{**partition["activity"],"evidenceRows":[{**row,field:"forged"}]}}
            with self.subTest(field=field),self.assertRaisesRegex(ValueError,"SCIENCE_NOT_REPROVEN"):
                run(bad)
        with self.assertRaisesRegex(ValueError,"PARTITION_CHANGED"):
            run({**partition,"integritySha256":"forged"})

    def test_cross_head_readback_rejects_changed_science_and_duplicate(self):
        prior = {"acceptedAcademicTaskIds":[str(i) for i in range(27)],
                 "springBufferBatchReceiptSha256":"prior"}
        proof = {"taskId":a._TASK,"models":[{"mass":"2"}]}
        frontier = {"gitHead":"a"*40,"proposalSha256":"b"*64,
                    "status":a._FRONTIER_STATUS,"sourceSha256":a._SOURCE_SHA,
                    "candidateSha256":a._CANDIDATE_SHA,"cumulativeAcademicTasksAccepted":28,
                    "fullAcademicTasksStillOpen":401,"completeAcademicProofGatesStillOpen":90,
                    "fullAcademicActivityPASS":0,"publicationAuthorized":False,
                    "newScientificReceiptSha256":"signed",
                    "previousAcademicTaskIds":prior["acceptedAcademicTaskIds"],
                    "newAcceptedTaskId":a._TASK}
        now = {"gitHead":"c"*40,"proposalSha256":"d"*64,
               "sourceSha256":a._SOURCE_SHA,"candidateSha256":a._CANDIDATE_SHA}
        receipt = {"integritySha256":"signed","previousSpringBufferBatchReceiptSha256":"prior"}
        def check(recomputed,old=prior):
            with (patch.object(a,"_read_signed",return_value=frontier),
                  patch.object(a,"read_long_horizon_development",return_value=now),
                  patch.object(a,"_verify_receipt",return_value=(receipt,proof)),
                  patch.object(a,"_original_proof",return_value=({}, {}, recomputed)),
                  patch.object(a,"_prior",return_value=old)):
                return a.verify_vector_explanation_across_git_heads(private=Path("."))
        self.assertTrue(check(proof)["carriedAcrossGitHead"])
        with self.assertRaisesRegex(ValueError,"SCIENCE_CHANGED_ACROSS_CODE_HEADS"):
            check({"taskId":a._TASK,"models":[{"mass":"3"}]})
        duplicate = {**prior,"acceptedAcademicTaskIds":[*prior["acceptedAcademicTaskIds"][:-1],a._TASK]}
        with self.assertRaisesRegex(ValueError,"SCIENCE_CHANGED_ACROSS_CODE_HEADS"):
            check(proof,old=duplicate)

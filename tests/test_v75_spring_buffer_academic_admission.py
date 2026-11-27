"""BSA291 signed MCQ09 partition and cross-head readback controls."""
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch

from app_generator.runtime import v3_spring_buffer_academic_batch_admission as a


class SpringBufferAdmission(TestCase):
    def test_prior_signed_twenty_four_is_mandatory(self):
        good={"independentlyAcceptedAcademicTasks":24,"fullAcademicTasksStillOpen":405,
              "pendingMcqDistractorScienceTasks":3,
              "acceptedAcademicTaskIds":[str(i) for i in range(24)],
              "completeAcademicProofGatesStillOpen":90,"fullAcademicActivityPASS":0,
              "publicationAuthorized":False}
        with patch.object(a,"verify_isolated_pair_batch_across_git_heads",return_value=good):
            self.assertEqual(a._prior_twenty_four(None),good)
        for field,value in (("independentlyAcceptedAcademicTasks",21),
                            ("fullAcademicActivityPASS",1),("publicationAuthorized",True)):
            with self.subTest(field=field),patch.object(
                a,"verify_isolated_pair_batch_across_git_heads",return_value={**good,field:value}):
                with self.assertRaisesRegex(ValueError,"A1_A24_CHAIN"):
                    a._prior_twenty_four(None)

    def test_partition_task_and_science_are_independently_rechecked(self):
        ready={"gitHead":"a"*40,"proposalSha256":"b"*64}
        v36={"signedPartitionHashes":[{} for _ in range(18)],
             "semanticTasksAutomaticallyDispatched":429,"fullAcademicProofTasksAccepted":0,
             "completeAcademicProofGatesStillOpen":90,"sourceSha256":a._SOURCE_SHA,
             "publicationAuthorized":False}
        v36["signedPartitionHashes"][8]={"activityId":"act-mcq-09-no-momentum-conversion",
                                          "signedEvidenceSha256":"signed-ninth"}
        rows=[{"taskId":task,"kind":"MCQ_DISTRACTOR_SCIENCE",
               "status":"BOUNDED_SUPPORT_ONLY_REVIEW_REQUIRED",
               "surfaceSha256":"surface-"+option} for option,task in a._TASKS.items()]
        partition={"integritySha256":"signed-ninth",
                   "activity":{"activityId":"act-mcq-09-no-momentum-conversion","evidenceRows":rows},
                   "sourceSha256":a._SOURCE_SHA,"candidateSha256":a._CANDIDATE_SHA,
                   "academicPASS":0,"publicationAuthorized":False}
        def producer(*,source_pdf,candidate_path,option_id):
            return {"taskId":a._TASKS[option_id],"optionId":option_id,
                    "surfaceSha256":"surface-"+option_id,"sourceSha256":a._SOURCE_SHA,
                    "candidateSha256":a._CANDIDATE_SHA,"newProviderCalls":0,
                    "publicationAuthorized":False}
        def run(part):
            with (patch.object(a,"_bound_inputs",return_value=(None,v36,None,"source","candidate")),
                  patch.object(a,"_signed",return_value=part),
                  patch.object(a,"independently_prove_spring_buffer_false_option",side_effect=producer),
                  patch.object(a,"independently_check_spring_buffer_witness")):
                return a._original_spring_buffer_proofs(private=Path("."),ready=ready,historical=False)
        self.assertEqual(len(run(partition)[2]),3)
        for field in ("taskId","surfaceSha256","status"):
            altered={**partition,"activity":{**partition["activity"],
                "evidenceRows":[dict(row) for row in rows]}}
            altered["activity"]["evidenceRows"][0][field]="forged"
            with self.subTest(field=field),self.assertRaisesRegex(ValueError,"FALSE_OPTION_NOT_REPROVEN"):
                run(altered)
        with self.assertRaisesRegex(ValueError,"PARTITION_CHANGED"):
            run({**partition,"integritySha256":"forged"})

    def test_cross_head_readback_rejects_changed_science_and_task_duplication(self):
        prior={"acceptedAcademicTaskIds":[str(i) for i in range(24)],
               "isolatedPairBatchReceiptSha256":"prior"}
        proofs=[{"taskId":task} for task in a._TASKS.values()]
        frontier={"gitHead":"a"*40,"proposalSha256":"b"*64,
                  "status":a._FRONTIER_STATUS,"sourceSha256":a._SOURCE_SHA,
                  "candidateSha256":a._CANDIDATE_SHA,"cumulativeAcademicTasksAccepted":27,
                  "fullAcademicTasksStillOpen":402,"pendingMcqDistractorScienceTasks":0,
                  "completeAcademicProofGatesStillOpen":90,"fullAcademicActivityPASS":0,
                  "publicationAuthorized":False,"newScientificBatchReceiptSha256":"signed",
                  "previousAcademicTaskIds":prior["acceptedAcademicTaskIds"],
                  "newAcceptedTaskIds":[p["taskId"] for p in proofs]}
        now={"gitHead":"c"*40,"proposalSha256":"d"*64,
             "sourceSha256":a._SOURCE_SHA,"candidateSha256":a._CANDIDATE_SHA}
        receipt={"integritySha256":"signed","previousIsolatedPairBatchReceiptSha256":"prior"}
        def check(recomputed,old=prior):
            with (patch.object(a,"_read_signed",return_value=frontier),
                  patch.object(a,"read_long_horizon_development",return_value=now),
                  patch.object(a,"_verify_receipt",return_value=(receipt,proofs)),
                  patch.object(a,"_original_spring_buffer_proofs",return_value=({}, {}, recomputed)),
                  patch.object(a,"_prior_twenty_four",return_value=old)):
                return a.verify_spring_buffer_batch_across_git_heads(private=Path("."))
        self.assertTrue(check(proofs)["carriedAcrossGitHead"])
        with self.assertRaisesRegex(ValueError,"SCIENCE_CHANGED_ACROSS_CODE_HEADS"):
            check([{"taskId":"forged"},*proofs[1:]])
        duplicate={**prior,"acceptedAcademicTaskIds":[*prior["acceptedAcademicTaskIds"][:-1],proofs[0]["taskId"]]}
        with self.assertRaisesRegex(ValueError,"SCIENCE_CHANGED_ACROSS_CODE_HEADS"):
            check(proofs,old=duplicate)

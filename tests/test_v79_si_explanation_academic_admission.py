"""BSA293 owner admission and independent historical/current-head controls."""
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch

from app_generator.runtime import v3_si_explanation_academic_admission as a

_TASK = "c" * 64  # Test-only task identity; owner identity comes from the producer.


class SiExplanationAdmission(TestCase):
    def test_prior_signed_twenty_eight_is_mandatory(self):
        good = {"independentlyAcceptedAcademicTasks": 28, "fullAcademicTasksStillOpen": 401,
                "pendingMcqDistractorScienceTasks": 0,
                "acceptedAcademicTaskIds": [str(i) for i in range(28)],
                "completeAcademicProofGatesStillOpen": 90, "fullAcademicActivityPASS": 0,
                "publicationAuthorized": False}
        with patch.object(a, "verify_vector_explanation_across_git_heads", return_value=good):
            self.assertEqual(a._prior(None), good)
        for field, value in (("independentlyAcceptedAcademicTasks", 24),
                             ("fullAcademicActivityPASS", 1), ("publicationAuthorized", True)):
            with self.subTest(field=field), patch.object(
                a, "verify_vector_explanation_across_git_heads", return_value={**good, field:value}
            ), self.assertRaisesRegex(ValueError, "A1_A28_CHAIN"):
                a._prior(None)

    def test_partition_task_and_science_are_independently_rechecked(self):
        ready = {"gitHead":"a"*40, "proposalSha256":"b"*64}
        v36 = {"signedPartitionHashes":[{} for _ in range(18)],
               "semanticTasksAutomaticallyDispatched":429, "fullAcademicProofTasksAccepted":0,
               "completeAcademicProofGatesStillOpen":90, "sourceSha256":a._SOURCE_SHA,
               "publicationAuthorized":False}
        v36["signedPartitionHashes"][1] = {"activityId":"act-mcq-02-si-units",
                                              "signedEvidenceSha256":"signed-second"}
        row = {"taskId":_TASK, "kind":"COMPLETE_SCIENTIFIC_MEANING",
               "status":"BOUNDED_SUPPORT_ONLY_REVIEW_REQUIRED",
               "surfaceSha256":"surface"}
        partition = {"integritySha256":"signed-second",
                     "activity":{"activityId":"act-mcq-02-si-units", "evidenceRows":[row]},
                     "sourceSha256":a._SOURCE_SHA,"candidateSha256":a._CANDIDATE_SHA,
                     "academicPASS":0,"publicationAuthorized":False}
        proof = {"taskId":_TASK,"surfaceSha256":"surface", "newProviderCalls":0,"publicationAuthorized":False}
        def run(part):
            with (patch.object(a,"_bound_inputs",return_value=(None,v36,None,"source","candidate")),
                  patch.object(a,"_signed",return_value=part),
                  patch.object(a,"independently_prove_si_explanation",return_value=proof),
                  patch.object(a,"independently_check_si_explanation_witness")):
                return a._original_proof(private=Path("."),ready=ready,historical=False)
        self.assertEqual(run(partition)[2],proof)
        for field in ("taskId","surfaceSha256","status"):
            bad = {**partition,"activity":{**partition["activity"],"evidenceRows":[{**row,field:"forged"}]}}
            with self.subTest(field=field),self.assertRaisesRegex(ValueError,"SCIENCE_NOT_REPROVEN"):
                run(bad)
        duplicate = {**partition,"activity":{**partition["activity"],"evidenceRows":[row,row]}}
        with self.assertRaisesRegex(ValueError,"SCIENCE_NOT_REPROVEN"):
            run(duplicate)
        with self.assertRaisesRegex(ValueError,"PARTITION_CHANGED"):
            run({**partition,"integritySha256":"forged"})

    def test_cross_head_readback_rejects_changed_science_and_duplicate(self):
        prior = {"acceptedAcademicTaskIds":[str(i) for i in range(28)],
                 "vectorExplanationReceiptSha256":"prior"}
        proof = {"taskId":_TASK,"models":[{"mass":"2"}]}
        frontier = {"gitHead":"a"*40,"proposalSha256":"b"*64,
                    "status":a._FRONTIER_STATUS,"sourceSha256":a._SOURCE_SHA,
                    "candidateSha256":a._CANDIDATE_SHA,"cumulativeAcademicTasksAccepted":29,
                    "fullAcademicTasksStillOpen":400,"completeAcademicProofGatesStillOpen":90,
                    "fullAcademicActivityPASS":0,"publicationAuthorized":False,
                    "newScientificReceiptSha256":"signed",
                    "previousAcademicTaskIds":prior["acceptedAcademicTaskIds"],
                    "newAcceptedTaskId":_TASK}
        now = {"gitHead":"c"*40,"proposalSha256":"d"*64,
               "sourceSha256":a._SOURCE_SHA,"candidateSha256":a._CANDIDATE_SHA}
        receipt = {"integritySha256":"signed","previousVectorExplanationReceiptSha256":"prior"}
        def check(recomputed,old=prior):
            with (patch.object(a,"_read_signed",return_value=frontier),
                  patch.object(a,"read_long_horizon_development",return_value=now),
                  patch.object(a,"_verify_receipt",return_value=(receipt,proof)),
                  patch.object(a,"_original_proof",return_value=({}, {}, recomputed)),
                  patch.object(a,"_prior",return_value=old)):
                return a.verify_si_explanation_across_git_heads(private=Path("."))
        self.assertTrue(check(proof)["carriedAcrossGitHead"])
        with self.assertRaisesRegex(ValueError,"SCIENCE_CHANGED_ACROSS_CODE_HEADS"):
            check({"taskId":_TASK,"models":[{"mass":"3"}]})
        duplicate = {**prior,"acceptedAcademicTaskIds":[*prior["acceptedAcademicTaskIds"][:-1],_TASK]}
        with self.assertRaisesRegex(ValueError,"SCIENCE_CHANGED_ACROSS_CODE_HEADS"):
            check(proof,old=duplicate)

    def test_signed_receipt_requires_exact_prior_and_recomputed_proof(self):
        ready={"gitHead":"a"*40,"proposalSha256":"b"*64}
        old={"acceptedAcademicTaskIds":[str(i) for i in range(28)],
             "vectorExplanationReceiptSha256":"previous"}
        proof={"taskId":_TASK,"models":[{"massKg":"2"}]}
        v36={"integritySha256":"v36"}
        part={"integritySha256":"partition"}
        audit={"integritySha256":"audit","sourceBoundRegistryAudit":{
            "acceptedMcqDistractorTaskCount":2},
            "independentlyPreviouslyAcceptedAcademicTasks":2}
        receipt={"status":a._STATUS,"sourceSha256":a._SOURCE_SHA,
                 "candidateSha256":a._CANDIDATE_SHA,"signedV36Sha256":"v36",
                 "secondSignedV36PartitionSha256":"partition",
                 "signedRegistryAuditSha256":"audit",
                 "previousAcademicTaskIds":old["acceptedAcademicTaskIds"],
                 "previousVectorExplanationReceiptSha256":"previous",
                 "newScientificProof":proof,"newIndependentlyAdmittedAcademicTasks":1,
                 "totalAcademicTaskAcceptances":29,"fullAcademicTasksStillOpen":400,
                 "completeAcademicProofGatesStillOpen":90,"fullAcademicActivityPASS":0,
                 "newProviderCalls":0,"publicationAuthorized":False}
        def check(candidate):
            with (patch.object(a,"_original_proof",return_value=(v36,part,proof)),
                  patch.object(a,"_prior",return_value=old),
                  patch.object(a,"_signed",side_effect=[candidate,audit])):
                return a._verify_receipt(private=Path("."),ready=ready,historical=False)
        self.assertEqual(check(receipt)[0],receipt)
        for field,value in (("signedV36Sha256","forged"),
                            ("previousVectorExplanationReceiptSha256","forged"),
                            ("newScientificProof",{"taskId":_TASK,"models":[]})):
            with self.subTest(field=field),self.assertRaisesRegex(ValueError,"IMMUTABLE_RECEIPT_CHANGED"):
                check({**receipt,field:value})

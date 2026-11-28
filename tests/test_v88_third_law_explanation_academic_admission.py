"""BSA299 owner admission and independent historical/current-head controls."""
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch

from app_generator.runtime import v3_third_law_explanation_academic_admission as a


class ThirdLawExplanationAdmission(TestCase):
    def test_prior_signed_thirty_one_is_mandatory(self):
        good = {"independentlyAcceptedAcademicTasks": 31, "fullAcademicTasksStillOpen": 398,
                "pendingMcqDistractorScienceTasks": 0,
                "acceptedAcademicTaskIds": [str(i) for i in range(31)],
                "completeAcademicProofGatesStillOpen": 90, "fullAcademicActivityPASS": 0,
                "publicationAuthorized": False}
        with patch.object(a, "verify_glider_explanation_across_git_heads", return_value=good):
            self.assertEqual(a._prior(None), good)
        for field, value in (("independentlyAcceptedAcademicTasks", 24),
                             ("fullAcademicActivityPASS", 1), ("publicationAuthorized", True)):
            with self.subTest(field=field), patch.object(
                a, "verify_glider_explanation_across_git_heads", return_value={**good, field:value}
            ), self.assertRaisesRegex(ValueError, "A1_A31_CHAIN"):
                a._prior(None)

    def test_partition_task_and_science_are_independently_rechecked(self):
        ready = {"gitHead":"a"*40, "proposalSha256":"b"*64}
        v36 = {"signedPartitionHashes":[{} for _ in range(18)],
               "semanticTasksAutomaticallyDispatched":429, "fullAcademicProofTasksAccepted":0,
               "completeAcademicProofGatesStillOpen":90, "sourceSha256":a._SOURCE_SHA,
               "publicationAuthorized":False}
        v36["signedPartitionHashes"][4] = {"activityId":"act-mcq-05-third-law-connection",
                                              "signedEvidenceSha256":"signed-fifth"}
        row = {"taskId":"t"*64, "kind":"COMPLETE_SCIENTIFIC_MEANING",
               "surfacePath":"explanation", "status":"BOUNDED_SUPPORT_ONLY_REVIEW_REQUIRED",
               "surfaceSha256":"surface"}
        partition = {"integritySha256":"signed-fifth",
                     "activity":{"activityId":"act-mcq-05-third-law-connection", "evidenceRows":[row]},
                     "sourceSha256":a._SOURCE_SHA,"candidateSha256":a._CANDIDATE_SHA,
                     "academicPASS":0,"publicationAuthorized":False}
        proof = {"taskId":"t"*64, "surfaceSha256":"surface", "newProviderCalls":0,"publicationAuthorized":False}
        def run(part):
            with (patch.object(a,"_bound_inputs",return_value=(None,v36,None,"source","candidate")),
                  patch.object(a,"_signed",return_value=part),
                  patch.object(a,"independently_prove_third_law_explanation",return_value=proof),
                  patch.object(a,"independently_check_third_law_explanation_witness")):
                return a._original_proof(private=Path("."),ready=ready,historical=False)
        self.assertEqual(run(partition)[2],proof)
        for field in ("taskId","surfaceSha256","status"):
            bad = {**partition,"activity":{**partition["activity"],"evidenceRows":[{**row,field:"forged"}]}}
            with self.subTest(field=field),self.assertRaisesRegex(ValueError,"SCIENCE_NOT_REPROVEN"):
                run(bad)
        with self.assertRaisesRegex(ValueError,"PARTITION_CHANGED"):
            run({**partition,"integritySha256":"forged"})

    def test_cross_head_readback_rejects_changed_science_and_duplicate(self):
        prior = {"acceptedAcademicTaskIds":[str(i) for i in range(31)],
                 "gliderExplanationReceiptSha256":"prior"}
        proof = {"taskId":"t"*64,"models":[{"mass":"2"}]}
        frontier = {"gitHead":"a"*40,"proposalSha256":"b"*64,
                    "status":a._FRONTIER_STATUS,"sourceSha256":a._SOURCE_SHA,
                    "candidateSha256":a._CANDIDATE_SHA,"cumulativeAcademicTasksAccepted":32,
                    "fullAcademicTasksStillOpen":397,"completeAcademicProofGatesStillOpen":90,
                    "fullAcademicActivityPASS":0,"publicationAuthorized":False,
                    "newScientificReceiptSha256":"signed",
                    "previousAcademicTaskIds":prior["acceptedAcademicTaskIds"],
                    "newAcceptedTaskId":"t"*64}
        now = {"gitHead":"c"*40,"proposalSha256":"d"*64,
               "sourceSha256":a._SOURCE_SHA,"candidateSha256":a._CANDIDATE_SHA}
        receipt = {"integritySha256":"signed","previousGliderExplanationReceiptSha256":"prior"}
        def check(recomputed,old=prior):
            with (patch.object(a,"_read_signed",return_value=frontier),
                  patch.object(a,"read_long_horizon_development",return_value=now),
                  patch.object(a,"_verify_receipt",return_value=(receipt,proof)),
                  patch.object(a,"_original_proof",return_value=({}, {}, recomputed)),
                  patch.object(a,"_prior",return_value=old)):
                return a.verify_third_law_explanation_across_git_heads(private=Path("."))
        self.assertTrue(check(proof)["carriedAcrossGitHead"])
        with self.assertRaisesRegex(ValueError,"SCIENCE_CHANGED_ACROSS_CODE_HEADS"):
            check({"taskId":"t"*64,"models":[{"mass":"3"}]})
        duplicate = {**prior,"acceptedAcademicTaskIds":[*prior["acceptedAcademicTaskIds"][:-1],"t"*64]}
        with self.assertRaisesRegex(ValueError,"SCIENCE_CHANGED_ACROSS_CODE_HEADS"):
            check(proof,old=duplicate)

    def test_signed_receipt_requires_exact_prior_and_recomputed_proof(self):
        ready={"gitHead":"a"*40,"proposalSha256":"b"*64}
        old={"acceptedAcademicTaskIds":[str(i) for i in range(31)],
             "gliderExplanationReceiptSha256":"previous"}
        proof={"taskId":"t"*64,"models":[{"massKg":"2"}]}
        v36={"integritySha256":"v36"}
        part={"integritySha256":"partition"}
        audit={"integritySha256":"audit","sourceBoundRegistryAudit":{
            "acceptedMcqDistractorTaskCount":2},
            "independentlyPreviouslyAcceptedAcademicTasks":2}
        receipt={"status":a._STATUS,"sourceSha256":a._SOURCE_SHA,
                 "candidateSha256":a._CANDIDATE_SHA,"signedV36Sha256":"v36",
                 "fifthSignedV36PartitionSha256":"partition",
                 "signedRegistryAuditSha256":"audit",
                 "previousAcademicTaskIds":old["acceptedAcademicTaskIds"],
                 "previousGliderExplanationReceiptSha256":"previous",
                 "newScientificProof":proof,"newIndependentlyAdmittedAcademicTasks":1,
                 "totalAcademicTaskAcceptances":32,"fullAcademicTasksStillOpen":397,
                 "completeAcademicProofGatesStillOpen":90,"fullAcademicActivityPASS":0,
                 "newProviderCalls":0,"publicationAuthorized":False}
        def check(candidate):
            with (patch.object(a,"_original_proof",return_value=(v36,part,proof)),
                  patch.object(a,"_prior",return_value=old),
                  patch.object(a,"_signed",side_effect=[candidate,audit])):
                return a._verify_receipt(private=Path("."),ready=ready,historical=False)
        self.assertEqual(check(receipt)[0],receipt)
        for field,value in (("signedV36Sha256","forged"),
                            ("previousGliderExplanationReceiptSha256","forged"),
                            ("newScientificProof",{"taskId":"t"*64,"models":[]})):
            with self.subTest(field=field),self.assertRaisesRegex(ValueError,"IMMUTABLE_RECEIPT_CHANGED"):
                check({**receipt,field:value})

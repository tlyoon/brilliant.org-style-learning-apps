"""BSA273: signed V36 task reader, dual-receipt admission and cross-HEAD safety."""
from __future__ import annotations
import copy
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch

from app_generator.runtime import v3_second_academic_proof_admission as a

FIRST = "ce320185009e7c529840a5cf96c75a1f469ad2a5961b3cbbca2ac4f07d9f9d60"
SECOND = "8d0ca6feb05d1376db2898613d1cd17d4da61512da429f8d3d8922b3c2cb49df"
HEAD = "a"*40
PROPOSAL = "b"*64
READY = {"gitHead":HEAD,"proposalSha256":PROPOSAL}
PROOF = {
    "status":"BSA273_SECOND_FINITE_SEMANTIC_MCQ_DISTRACTOR_SCIENCE_ACCEPTED",
    "taskId":SECOND,
    "taskKind":"MCQ_DISTRACTOR_SCIENCE",
    "surfacePath":"answerKey/options/1/label",
    "surfaceSha256":"c"*64,
    "sourceSha256":a._SOURCE_SHA,
    "candidateSha256":a._CANDIDATE_SHA,
    "completeAcademicProofGatesStillOpen":90,
    "acceptedAcademicTaskCountForThisProof":1,
    "otherTrilingualMeaningProofAccepted":False,
    "publicationAuthorized":False,
    "newGeminiCalls":0,
    "exactRationalCounterexamples":[
        {"mass":"3","constantSpeed":"5","momentumForward":"15",
         "momentumBackward":"-15","momentumVectorsIdentical":False,
         "momentumMagnitudesEqual":True},
        {"mass":"9/2","constantSpeed":"4/3","momentumForward":"6",
         "momentumBackward":"-6","momentumVectorsIdentical":False,
         "momentumMagnitudesEqual":True},
    ],
}
V36 = {"integritySha256":"d"*64}
PARTITION = {
    "integritySha256":"e"*64,
    "activity":{"evidenceRows":[{
        "taskId":SECOND, "kind":"MCQ_DISTRACTOR_SCIENCE",
        "status":"BOUNDED_SUPPORT_ONLY_REVIEW_REQUIRED",
        "surfaceSha256":PROOF["surfaceSha256"],
        # Real signed V36 partition rows do not contain surfacePath.
    }]}
}


def receipt(proof=PROOF):
    return {
        **READY, "status":a._STATUS,
        "integritySha256":"f"*64,
        "signedV36Sha256":V36["integritySha256"],
        "signedV36FirstPartitionSha256":PARTITION["integritySha256"],
        "sourceSha256":a._SOURCE_SHA,
        "candidateSha256":a._CANDIDATE_SHA,
        "independentTaskProof":copy.deepcopy(proof),
        "academicTaskAcceptancesFromThisReceipt":1,
        "cumulativeAcceptedAcademicTasks":2,
        "fullAcademicTasksStillOpen":427,
        "completeAcademicProofGatesStillOpen":90,
        "fullAcademicActivityPASS":0,
        "newProviderCalls":0,
        "publicationAuthorized":False,
    }


def first():
    return {
        "independentlyAcceptedAcademicTasks":1, "taskId":FIRST,
        "proofReceiptSha256":"9"*64,
        "publicationAuthorized":False, "carriedAcrossGitHead":True,
    }


def frontier():
    return {
        **READY, "status":"BSA273_SECOND_PRIVATE_INDEPENDENT_TASK_ACCEPTED",
        "sourceSha256":a._SOURCE_SHA,
        "candidateSha256":a._CANDIDATE_SHA,
        "taskId":SECOND,
        "proofReceiptSha256":"f"*64,
        "cumulativeAcceptedAcademicTasks":2,
        "fullAcademicTasksStillOpen":427,
        "completeAcademicProofGatesStillOpen":90,
        "fullAcademicActivityPASS":0,
        "publicationAuthorized":False,
    }


class AcademicSecondProof(TestCase):
    def check(self, proof=PROOF, partition=PARTITION):
        with (patch.object(a,"_bound_inputs",return_value=(
                  Path("."),V36,partition,Path("pdf"),Path("candidate"))),
              patch.object(a,"independent_second_distractor_science",return_value=proof)):
            return a._check_task_and_source(private=Path("."),ready=READY)

    def test_original_signed_row_without_surface_path_is_accepted(self):
        self.assertEqual(self.check()[2]["taskId"],SECOND)

    def test_changed_signed_row_digest_or_task_status_is_refused(self):
        for key,value in (("surfaceSha256","0"*64),
                          ("status","ACCEPTED_WITHOUT_PROOF"),
                          ("kind","TRILINGUAL_MEANING_EQUIVALENCE")):
            altered=copy.deepcopy(PARTITION)
            altered["activity"]["evidenceRows"][0][key]=value
            with self.subTest(key=key),self.assertRaisesRegex(
                ValueError,"SECOND_SIGNED_V36_TASK_NOT_PENDING"):
                self.check(partition=altered)

    def test_second_must_be_distinct_from_original_and_exact_path(self):
        for key,value in (("taskId",FIRST),("surfacePath","prompt/en"),
                          ("completeAcademicProofGatesStillOpen",89),
                          ("publicationAuthorized",True)):
            forged=dict(PROOF);forged[key]=value
            p=copy.deepcopy(PARTITION)
            p["activity"]["evidenceRows"][0]["taskId"]=forged["taskId"]
            with self.subTest(key=key),self.assertRaises(ValueError):
                self.check(proof=forged,partition=p)

    def test_independent_receipt_reader_rejects_forged_vectors_and_counts(self):
        for modify in (
            lambda r: r["independentTaskProof"]["exactRationalCounterexamples"][0].update(
                {"momentumForward":"123"}),
            lambda r: r.update({"cumulativeAcceptedAcademicTasks":3}),
            lambda r: r.update({"fullAcademicTasksStillOpen":426}),
            lambda r: r.update({"publicationAuthorized":True}),
        ):
            val=receipt()
            modify(val)
            with (patch.object(a,"_check_task_and_source",
                               return_value=(V36,PARTITION,PROOF)),
                  patch.object(a,"_signed",return_value=val)):
                with self.assertRaisesRegex(ValueError,
                        "SECOND_IMMUTABLE_SOURCE_SCIENCE_RECEIPT_INVALID|INDEPENDENT_VECTOR_ARITHMETIC_FAILED"):
                    a._verify_receipt(private=Path("."),ready=READY)

    def test_first_proof_and_second_immutable_receipt_survive_readback(self):
        f=frontier()
        with (patch.object(a,"verify_academic_across_git_heads",return_value=first()),
              patch.object(a,"_read_signed",return_value=f),
              patch.object(a,"read_long_horizon_development",return_value={
                  **READY,"sourceSha256":a._SOURCE_SHA,
                  "candidateSha256":a._CANDIDATE_SHA}),
              patch.object(a,"_verify_receipt",return_value=(receipt(),PROOF)),
              patch.object(a,"_check_task_and_source",
                           return_value=(V36,PARTITION,PROOF))):
            out=a.verify_second_academic_across_git_heads(private=Path("."))
        self.assertEqual(out["independentlyAcceptedAcademicTasks"],2)
        self.assertEqual(out["fullAcademicTasksStillOpen"],427)
        self.assertEqual(out["acceptedAcademicTaskIds"],[FIRST,SECOND])
        self.assertEqual(out["completeAcademicProofGatesStillOpen"],90)

    def test_changed_current_textbook_is_not_reused(self):
        with (patch.object(a,"verify_academic_across_git_heads",return_value=first()),
              patch.object(a,"_read_signed",return_value=frontier()),
              patch.object(a,"read_long_horizon_development",return_value={
                  **READY,"sourceSha256":"0"*64,
                  "candidateSha256":a._CANDIDATE_SHA})):
            with self.assertRaisesRegex(ValueError,"SECOND_ACADEMIC_FRONTIER_UNTRUSTED"):
                a.verify_second_academic_across_git_heads(private=Path("."))

    def test_no_second_acceptance_without_the_first(self):
        broken=first()
        broken["independentlyAcceptedAcademicTasks"]=0
        with patch.object(a,"verify_academic_across_git_heads",return_value=broken):
            with self.assertRaisesRegex(ValueError,"FIRST_PROOF_NO_LONGER_VALID"):
                a.verify_second_academic_across_git_heads(private=Path("."))

    def test_duplicate_second_task_id_is_not_counted_twice(self):
        duplicate=dict(PROOF);duplicate["taskId"]=FIRST
        with (patch.object(a,"verify_academic_across_git_heads",return_value=first()),
              patch.object(a,"_read_signed",return_value=frontier()),
              patch.object(a,"read_long_horizon_development",return_value={
                  **READY,"sourceSha256":a._SOURCE_SHA,
                  "candidateSha256":a._CANDIDATE_SHA}),
              patch.object(a,"_verify_receipt",return_value=(receipt(duplicate),duplicate)),
              patch.object(a,"_check_task_and_source",
                           return_value=(V36,PARTITION,duplicate))):
            with self.assertRaisesRegex(ValueError,"CHANGED_OR_DUPLICATED"):
                a.verify_second_academic_across_git_heads(private=Path("."))

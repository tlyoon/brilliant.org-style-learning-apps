"""BSA278: signed original-source glider A10–A12 chain negative controls.

Synthetic signed fixtures check idempotence, exact original fourth V36 task,
independent previous nine receipt and tamper rejection. Genuine physics and
original Serway source were separately evaluated on owner Yoga6.
"""
from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch
import copy
import json

from app_generator.runtime import v3_paired_glider_academic_batch_admission as admission
from app_generator.runtime.v3_native_release_adapter import _v6_checkpoint

NOW={"gitHead":"a"*40,"proposalSha256":"b"*64}
V36={
    "integritySha256":"c"*64,
    "sourceSha256":admission._SOURCE_SHA,
    "semanticTasksAutomaticallyDispatched":429,
    "fullAcademicProofTasksAccepted":0,
    "completeAcademicProofGatesStillOpen":90,
    "publicationAuthorized":False,
    "signedPartitionHashes":[{"activityId":f"test-{i}",
                              "signedEvidenceSha256":"d"*64}
                             for i in range(18)],
}
V36["signedPartitionHashes"][3]={
    "activityId":"act-mcq-04-two-particle-opposite-momentum",
    "signedEvidenceSha256":"d"*64,
}
PART={
    **NOW,
    "integritySha256":"d"*64,
    "sourceSha256":admission._SOURCE_SHA,
    "candidateSha256":admission._CANDIDATE_SHA,
    "academicPASS":0,
    "publicationAuthorized":False,
    "activity":{
        "activityId":"act-mcq-04-two-particle-opposite-momentum",
        "evidenceRows":[{"taskId":tid,"kind":"MCQ_DISTRACTOR_SCIENCE",
                         "status":"BOUNDED_SUPPORT_ONLY_REVIEW_REQUIRED",
                         "surfaceSha256":str(i+3)*64}
                        for i,tid in enumerate(admission._TASK_IDS.values())],
    },
}
PROOFS=[
    {"optionId":opt,"taskId":tid,"surfaceSha256":str(i+3)*64,
     "independentScienceProof":{"taskId":tid,"optionId":opt,
        "surfaceSha256":str(i+3)*64,
        "sourceSha256":admission._SOURCE_SHA,
        "candidateSha256":admission._CANDIDATE_SHA,
        "newProviderCalls":0,"publicationAuthorized":False}}
    for i,(opt,tid) in enumerate(admission._TASK_IDS.items())
]
PRIOR={
    "independentlyAcceptedAcademicTasks":9,
    "fullAcademicTasksStillOpen":420,
    "acceptedAcademicTaskIds":[str(i)*64 for i in range(1,10)],
    "newtonBatchReceiptSha256":"a"*64,
    "completeAcademicProofGatesStillOpen":90,
    "fullAcademicActivityPASS":0,
    "publicationAuthorized":False,
}


class GliderImmutableAcceptance(TestCase):
    def stage(self,mutation=None):
        with TemporaryDirectory() as temporary:
            private=Path(temporary)
            folder=private/"owner-five-stage-completion"/NOW["gitHead"]/NOW["proposalSha256"]
            folder.mkdir(parents=True)
            (private/"long-horizon-development").mkdir()
            _v6_checkpoint(folder/admission._REGISTRY_RECEIPT,{
                **NOW,
                "sourceBoundRegistryAudit":{"acceptedMcqDistractorTaskCount":2},
                "independentlyPreviouslyAcceptedAcademicTasks":2,
                "publicationAuthorized":False,
            })
            old_registry=json.loads((folder/admission._REGISTRY_RECEIPT).read_text(encoding="utf8"))
            audit={
                **NOW,
                "registryReceiptSha256":old_registry["integritySha256"],
                "independentlyAcceptedAcademicTasks":2,
                "signedV36Sha256":V36["integritySha256"],
            }
            with (patch.object(admission,"_prior_nine",return_value=PRIOR),
                  patch.object(admission,"read_long_horizon_development",
                    return_value={
                        **NOW,"sourceSha256":admission._SOURCE_SHA,
                        "candidateSha256":admission._CANDIDATE_SHA,
                    }),
                  patch.object(admission,"verify_registry_audit",
                               return_value=audit),
                  patch.object(admission,"_recomputed_original_glider_proofs",
                               return_value=(V36,PART,copy.deepcopy(PROOFS)))):
                first=admission.admit_paired_glider_batch(private=private)
                self.assertEqual(first["independentlyAcceptedAcademicTasks"],12)
                self.assertEqual(first["fullAcademicTasksStillOpen"],417)
                self.assertEqual(first["pendingMcqDistractorScienceTasks"],15)
                self.assertEqual(first["completeAcademicProofGatesStillOpen"],90)
                self.assertFalse(first["publicationAuthorized"])
                self.assertEqual(first,admission.admit_paired_glider_batch(private=private))
                if mutation:
                    mutation(folder,private)
                    with self.assertRaises(ValueError):
                        admission.verify_paired_glider_batch_across_git_heads(
                            private=private)

    def test_three_distinct_glider_tasks_immutable_signed_and_restart_safe(self):
        self.stage()

    def test_corrupt_signed_receipt_blocked(self):
        def mutate(folder,private):
            f=folder/admission._RECEIPT
            raw=json.loads(f.read_text(encoding="utf8"))
            raw["totalAcademicTaskAcceptances"]=13
            f.write_text(json.dumps(raw),encoding="utf8")
        self.stage(mutate)

    def test_original_two_task_registry_cannot_be_rewritten(self):
        def mutate(folder,private):
            f=folder/admission._REGISTRY_RECEIPT
            raw=json.loads(f.read_text(encoding="utf8"))
            raw["independentlyPreviouslyAcceptedAcademicTasks"]=3
            f.write_text(json.dumps(raw),encoding="utf8")
        self.stage(mutate)

    def test_new_frontier_cannot_claim_unverified_extra_pass(self):
        def mutate(folder,private):
            f=private/"long-horizon-development"/admission._FRONTIER
            raw=json.loads(f.read_text(encoding="utf8"))
            raw["cumulativeAcademicTasksAccepted"]=13
            f.write_text(json.dumps(raw),encoding="utf8")
        self.stage(mutate)

    def test_missing_previous_nine_proofs_prevents_admission(self):
        with TemporaryDirectory() as temporary:
            with patch.object(admission,"_prior_nine",
                              side_effect=ValueError("MISSING_A1_A9")):
                with self.assertRaisesRegex(ValueError,"MISSING_A1_A9"):
                    admission.admit_paired_glider_batch(
                        private=Path(temporary))

    def test_forged_original_fourth_partition_rejected(self):
        with TemporaryDirectory() as temporary:
            fake=copy.deepcopy(PART)
            fake["activity"]["activityId"]="unknown"
            with (patch.object(admission,"_bound_inputs",
                               return_value=(
                                   Path(temporary),V36,PART,Path(temporary),
                                   Path(temporary))),
                  patch.object(admission,"_signed",return_value=fake)):
                with self.assertRaisesRegex(ValueError,"FOURTH_SIGNED"):
                    admission._recomputed_original_glider_proofs(
                        private=Path(temporary),ready=NOW,historical=False)

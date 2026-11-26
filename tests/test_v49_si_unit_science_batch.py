"""BSA276 independent SI-unit mathematical and immutable receipt negative tests.

CI tests use only synthetic source transport. Actual original selected Serway
PDF and frozen 18-activity EN/MS/ZH were separately tested on owner Yoga6.
"""
from __future__ import annotations

import copy
from fractions import Fraction as F
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch

from app_generator.validation import section91_si_unit_false_options_proof as proof
from app_generator.runtime import v3_si_units_academic_batch_admission as admit
from app_generator.runtime.v3_native_release_adapter import _v6_checkpoint

HEAD="a"*40
PROPOSAL="b"*64
NOW={"gitHead":HEAD,"proposalSha256":PROPOSAL}
V36={
    "integritySha256":"c"*64,
    "semanticTasksAutomaticallyDispatched":429,
    "completeAcademicProofGatesStillOpen":90,
    "fullAcademicProofTasksAccepted":0,
    "sourceSha256":admit._SOURCE_SHA,
    "signedPartitionHashes":[{"activityId":"a"+str(i),
                              "signedEvidenceSha256":"d"*64}
                             for i in range(18)],
}
V36["signedPartitionHashes"][1]={
    "activityId":"act-mcq-02-si-units","signedEvidenceSha256":"d"*64}
PART={
    **NOW,
    "integritySha256":"d"*64,
    "sourceSha256":admit._SOURCE_SHA,
    "candidateSha256":admit._CANDIDATE_SHA,
    "academicPASS":0,"publicationAuthorized":False,
    "activity":{"activityId":"act-mcq-02-si-units",
                "evidenceRows":[
                    {"taskId":tid,"kind":"MCQ_DISTRACTOR_SCIENCE",
                     "status":"BOUNDED_SUPPORT_ONLY_REVIEW_REQUIRED",
                     "surfaceSha256":(str(i+3)*64)[:64]}
                    for i,tid in enumerate(admit._TASK_IDS.values())]},
}
SOURCE_PROOFS=[
    {"optionId":opt,"taskId":tid,"surfaceSha256":(str(i+3)*64)[:64],
     "independentScienceProof":{"taskId":tid,"optionId":opt,
                                "surfaceSha256":(str(i+3)*64)[:64],
                                "sourceSha256":admit._SOURCE_SHA,
                                "candidateSha256":admit._CANDIDATE_SHA,
                                "newProviderCalls":0,"publicationAuthorized":False}}
    for i,(opt,tid) in enumerate(admit._TASK_IDS.items())
]
PRIOR={
    "independentlyAcceptedAcademicTasks":3,
    "fullAcademicTasksStillOpen":426,
    "acceptedAcademicTaskIds":["1"*64,"2"*64,"3"*64],
    "batchReceiptSha256":"4"*64,
    "completeAcademicProofGatesStillOpen":90,
    "fullAcademicActivityPASS":0,
    "publicationAuthorized":False,
}
AUDIT={
    **NOW,
    "registryReceiptSha256":"5"*64,
    "independentlyAcceptedAcademicTasks":2,
    "signedV36Sha256":V36["integritySha256"],
}


class ScienceDimensionalWitness(TestCase):
    def witness(self,opt="opt-b"):
        p={
            "proofFamily":"SI_DIMENSION_AND_VECTOR_MOMENTUM",
            "optionId":opt,
            "sourceSha256":proof._SOURCE_SHA,
            "candidateSha256":proof._CANDIDATE_SHA,
            "dimensionalWitness":proof._dimensional_witness(),
            "rationalVectorModels":proof._exact_vector_models(),
            "counterexampleClass":{
                "opt-b":"MOMENTUM_IS_NOT_SCALAR_MAGNITUDE_ALONE",
                "opt-c":"ENERGY_DIMENSIONS_DIFFER_FROM_MOMENTUM",
                "opt-d":"INVERSE_VELOCITY_DIMENSIONS_AND_PERPENDICULARITY_FALSE",
            }[opt],
            "independentScienceWitnessVerified":True,
            "academicTaskAccepted":False,
            "completeAcademicProofGatesStillOpen":90,
            "newProviderCalls":0,
            "publicationAuthorized":False,
        }
        return {**p,"witnessSha256":proof._digest(p)}

    def test_each_si_dimension_and_vector_claim_independently_rederived(self):
        for option in ("opt-b","opt-c","opt-d"):
            with self.subTest(option=option):
                proof.independently_verify_si_option_witness(
                    self.witness(option))
        self.assertEqual(proof._dimensional_witness()["momentum"],[1,1,-1])
        self.assertEqual(proof._dimensional_witness()["energy"],[1,2,-2])
        self.assertEqual(proof._dimensional_witness()["massDividedByVelocity"],
                         [1,-1,1])

    def test_exact_rational_witness_obeys_momentum_direction(self):
        for item in proof._exact_vector_models():
            m,s=F(item["mass"]),F(item["speed"])
            self.assertEqual(F(item["momentumForward"]),m*s)
            self.assertEqual(F(item["momentumBackward"]),-m*s)
            self.assertEqual(F(item["kineticEnergy"]),m*s*s/2)
            self.assertFalse(item["pPerpendicularToVelocity"])

    def test_forged_dimensions_are_rejected_even_with_rehashed_digest(self):
        forged=self.witness()
        forged["dimensionalWitness"]["momentum"]=[1,2,-2]
        forged["witnessSha256"]=proof._digest({
            k:v for k,v in forged.items() if k!="witnessSha256"})
        with self.assertRaisesRegex(ValueError,"DIMENSIONAL_ALGEBRA"):
            proof.independently_verify_si_option_witness(forged)

    def test_forged_physics_is_rejected_even_with_rehashed_digest(self):
        forged=self.witness()
        forged["rationalVectorModels"][0]["momentumForward"]="0"
        forged["witnessSha256"]=proof._digest({
            k:v for k,v in forged.items() if k!="witnessSha256"})
        with self.assertRaisesRegex(ValueError,"RATIONAL_VECTOR_ALGEBRA"):
            proof.independently_verify_si_option_witness(forged)

    def test_false_explicit_publication_or_fake_accepted_status_rejected(self):
        for k,v in (("publicationAuthorized",True),
                    ("academicTaskAccepted",True),
                    ("newProviderCalls",1)):
            with self.subTest(field=k):
                p=self.witness();p[k]=v
                with self.assertRaises(ValueError):
                    proof.independently_verify_si_option_witness(p)

    def test_incomplete_or_modified_language_constituent_rejected(self):
        from app_generator.validation.section91_first_distractor_proof import (
            _parse_complete,
        )
        for opt,locales in proof._OPTIONS.items():
            for lang,text in locales.items():
                _parse_complete(text,(text,),"BSA276_LANGUAGE")
                with self.subTest(option=opt,locale=lang):
                    with self.assertRaises(ValueError):
                        _parse_complete(text+" ",(text,),"BSA276_LANGUAGE")
                    with self.assertRaises(ValueError):
                        _parse_complete(text[:-1],(text,),"BSA276_LANGUAGE")


class ThreeSignedAdmissions(TestCase):
    def _fixture(self,folder:Path):
        folder.mkdir(parents=True,exist_ok=True)
        _v6_checkpoint(folder/admit._REGISTRY_RECEIPT,{
            **NOW,
            "sourceBoundRegistryAudit":{"acceptedMcqDistractorTaskCount":2},
            "independentlyPreviouslyAcceptedAcademicTasks":2,
            "publicationAuthorized":False,
        })

    def run_admit(self,mutate=None):
        with TemporaryDirectory() as temp:
            private=Path(temp)
            folder=private/"owner-five-stage-completion"/HEAD/PROPOSAL
            (private/"long-horizon-development").mkdir()
            self._fixture(folder)
            report=json.loads(
                (folder/admit._REGISTRY_RECEIPT).read_text(encoding="utf8"))
            registered={**AUDIT,"registryReceiptSha256":report["integritySha256"]}
            def take(**kwargs):
                return V36,PART,copy.deepcopy(SOURCE_PROOFS)
            with (patch.object(admit,"_prior_three",return_value=PRIOR),
                  patch.object(admit,"read_long_horizon_development",
                               return_value={**NOW,"sourceSha256":admit._SOURCE_SHA,
                                             "candidateSha256":admit._CANDIDATE_SHA}),
                  patch.object(admit,"verify_registry_audit",
                               return_value=registered),
                  patch.object(admit,"_current_v36_si_tasks",side_effect=take)):
                a=admit.admit_si_unit_science_batch(private=private)
                b=admit.verify_si_unit_batch_across_git_heads(private=private)
                self.assertEqual(a,b)
                self.assertEqual(a["independentlyAcceptedAcademicTasks"],6)
                self.assertEqual(a["fullAcademicTasksStillOpen"],423)
                self.assertEqual(a["pendingMcqDistractorScienceTasks"],21)
                self.assertEqual(a["completeAcademicProofGatesStillOpen"],90)
                self.assertFalse(a["publicationAuthorized"])
                self.assertEqual(admit.admit_si_unit_science_batch(private=private),a)
                if mutate is not None:
                    mutate(folder,private)
                    with self.assertRaises(ValueError):
                        admit.verify_si_unit_batch_across_git_heads(private=private)

    def test_three_independent_science_tasks_immutable_admission(self):
        self.run_admit()

    def test_corrupted_signed_receipt_fail_closed(self):
        def corrupt(folder,private):
            p=folder/admit._RECEIPT
            x=json.loads(p.read_text(encoding="utf8"))
            x["cumulativeAcceptedAcademicTasks"]=7
            p.write_text(json.dumps(x),encoding="utf8")
        self.run_admit(corrupt)

    def test_old_registry_receipt_cannot_be_rewritten(self):
        def corrupt(folder,private):
            p=folder/admit._REGISTRY_RECEIPT
            x=json.loads(p.read_text(encoding="utf8"))
            x["independentlyPreviouslyAcceptedAcademicTasks"]=3
            p.write_text(json.dumps(x),encoding="utf8")
        self.run_admit(corrupt)

    def test_signed_frontier_cannot_claim_a_fourth_new_task(self):
        def corrupt(folder,private):
            p=private/"long-horizon-development"/admit._FRONTIER
            x=json.loads(p.read_text(encoding="utf8"))
            x["acceptedAcademicTaskCount"]=7
            p.write_text(json.dumps(x),encoding="utf8")
        self.run_admit(corrupt)

    def test_missing_previous_three_prevents_any_new_admission(self):
        with TemporaryDirectory() as temp:
            private=Path(temp)
            (private/"long-horizon-development").mkdir()
            with patch.object(admit,"_prior_three",side_effect=
                              ValueError("MISSING_SIGNED_A3")):
                with self.assertRaisesRegex(ValueError,"MISSING_SIGNED_A3"):
                    admit.admit_si_unit_science_batch(private=private)

    def test_wrong_second_signed_mcq_partition_is_rejected(self):
        with TemporaryDirectory() as temp:
            p=Path(temp)
            forged=copy.deepcopy(PART)
            forged["activity"]["activityId"]="foreign-activity"
            with (patch.object(admit,"_bound_inputs",
                   return_value=(p,V36,PART,p,p)),
                  patch.object(admit,"_signed",return_value=forged)):
                with self.assertRaisesRegex(ValueError,"SECOND_SIGNED"):
                    admit._current_v36_si_tasks(
                        private=p,ready=NOW,historical=False)

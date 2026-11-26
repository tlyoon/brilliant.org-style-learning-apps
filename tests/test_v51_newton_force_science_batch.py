"""BSA277 negative controls for original-source Newton A7–A9 admissions.

Synthetic science in CI cannot replace genuine source-bound physics witnesses.
The original selected Serway source was independently reopened on Yoga6.
"""
from __future__ import annotations

from fractions import Fraction as F
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch
import copy
import json

from app_generator.runtime import v3_newton_force_academic_batch_admission as admission
from app_generator.validation import section91_newton_force_false_options_proof as science
from app_generator.runtime.v3_native_release_adapter import _v6_checkpoint

NOW={"gitHead":"a"*40,"proposalSha256":"b"*64}
V36={
    "integritySha256":"c"*64,
    "sourceSha256":admission._SOURCE_SHA,
    "semanticTasksAutomaticallyDispatched":429,
    "fullAcademicProofTasksAccepted":0,
    "completeAcademicProofGatesStillOpen":90,
    "publicationAuthorized":False,
    "signedPartitionHashes":[{"activityId":f"act-{i}",
                              "signedEvidenceSha256":"d"*64}
                             for i in range(18)],
}
V36["signedPartitionHashes"][2]={
    "activityId":"act-mcq-03-net-force-definition",
    "signedEvidenceSha256":"d"*64,
}
PART={
    **NOW,
    "integritySha256":"d"*64,
    "sourceSha256":admission._SOURCE_SHA,
    "candidateSha256":admission._CANDIDATE_SHA,
    "academicPASS":0,"publicationAuthorized":False,
    "activity":{
        "activityId":"act-mcq-03-net-force-definition",
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
    "independentlyAcceptedAcademicTasks":6,
    "fullAcademicTasksStillOpen":423,
    "acceptedAcademicTaskIds":[str(i)*64 for i in range(1,7)],
    "siUnitBatchReceiptSha256":"7"*64,
    "completeAcademicProofGatesStillOpen":90,
    "fullAcademicActivityPASS":0,
    "publicationAuthorized":False,
}


def mathematical_witness(opt:str)->dict:
    p={
        "optionId":opt,"sourceSha256":science._SOURCE_SHA,
        "candidateSha256":science._CANDIDATE_SHA,
        "proofFamily":"NEWTON_NET_FORCE_IS_RATE_OF_MOMENTUM",
        "counterexampleClass":science._CLAIMS[opt],
        "exactRationalNewtonModels":science._countermodels(),
        "dimensionProof":science._dimensions(),
        "independentScienceWitnessVerified":True,
        "academicTaskAccepted":False,
        "completeAcademicProofGatesStillOpen":90,
        "newProviderCalls":0,"publicationAuthorized":False,
    }
    return {**p,"witnessSha256":science._digest(p)}


class NewtonScienceModel(TestCase):
    def test_three_correctly_scoped_newton_misconceptions(self):
        for opt in ("opt-b","opt-c","opt-d"):
            with self.subTest(opt=opt):
                science.independently_verify_newton_force_witness(
                    mathematical_witness(opt))
        self.assertEqual(science._dimensions()["force"],[1,1,-2])
        self.assertEqual(science._dimensions()["momentum"],[1,1,-1])

    def test_two_positive_exact_rational_force_models(self):
        for w in science._countermodels():
            m,a,v,t=(F(w[k]) for k in
                ("mass","acceleration","initialVelocity","timeIncrement"))
            self.assertEqual(F(w["constantNonzeroNetForce"]),m*a)
            self.assertEqual(F(w["timeRateOfMomentumChange"]),m*a)
            self.assertEqual(F(w["finalMomentum"]),m*(v+a*t))
            self.assertGreater(F(w["initialMomentum"]),0)

    def test_independently_rederived_math_rejects_forged_countermodel(self):
        item=mathematical_witness("opt-b")
        item["exactRationalNewtonModels"][0]["finalMomentum"]="0"
        item["witnessSha256"]=science._digest({
            k:v for k,v in item.items() if k!="witnessSha256"})
        with self.assertRaisesRegex(ValueError,"INDEPENDENT_MOMENTUM_RATE"):
            science.independently_verify_newton_force_witness(item)

    def test_forged_dimensional_identity_fails_with_new_digest(self):
        item=mathematical_witness("opt-c")
        item["dimensionProof"]["force"]=[1,1,-1]
        item["witnessSha256"]=science._digest({
            k:v for k,v in item.items() if k!="witnessSha256"})
        with self.assertRaisesRegex(ValueError,"INDEPENDENT_MOMENTUM_RATE"):
            science.independently_verify_newton_force_witness(item)

    def test_semantic_negation_or_extra_clause_rejected(self):
        from app_generator.validation.section91_first_distractor_proof import _parse_complete
        for opt,locales in science._OPTIONS.items():
            for language,txt in locales.items():
                with self.subTest(opt=opt,language=language):
                    _parse_complete(txt,(txt,),"BSA277")
                    with self.assertRaises(ValueError):
                        _parse_complete(txt+" extra",(txt,),"BSA277")
                    with self.assertRaises(ValueError):
                        _parse_complete(txt[:-1],(txt,),"BSA277")

    def test_false_publication_new_calls_or_preaccepted_proof_rejected(self):
        for field,value in (("publicationAuthorized",True),
                            ("newProviderCalls",1),("academicTaskAccepted",True)):
            item=mathematical_witness("opt-d")
            item[field]=value
            with self.subTest(field=field),self.assertRaises(ValueError):
                science.independently_verify_newton_force_witness(item)


class NewtonImmutableAdmissions(TestCase):
    def run_signed(self,mutate=None):
        with TemporaryDirectory() as temporary:
            private=Path(temporary)
            folder=private/"owner-five-stage-completion"/NOW["gitHead"]/NOW["proposalSha256"]
            folder.mkdir(parents=True)
            (private/"long-horizon-development").mkdir()
            _v6_checkpoint(folder/admission._REGISTRY_RECEIPT,{
                **NOW,"sourceBoundRegistryAudit":{
                    "acceptedMcqDistractorTaskCount":2},
                "independentlyPreviouslyAcceptedAcademicTasks":2,
                "publicationAuthorized":False,
            })
            original=json.loads((folder/admission._REGISTRY_RECEIPT).read_text())
            audit={**NOW,
                   "registryReceiptSha256":original["integritySha256"],
                   "independentlyAcceptedAcademicTasks":2,
                   "signedV36Sha256":V36["integritySha256"]}
            with (patch.object(admission,"_prior_six",return_value=PRIOR),
                  patch.object(admission,"read_long_horizon_development",
                    return_value={**NOW,"sourceSha256":admission._SOURCE_SHA,
                                  "candidateSha256":admission._CANDIDATE_SHA}),
                  patch.object(admission,"verify_registry_audit",
                               return_value=audit),
                  patch.object(admission,"_recomputed_original_newton_proofs",
                    return_value=(V36,PART,copy.deepcopy(PROOFS)))):
                first=admission.admit_newton_source_bound_batch(private=private)
                self.assertEqual(first["independentlyAcceptedAcademicTasks"],9)
                self.assertEqual(first["fullAcademicTasksStillOpen"],420)
                self.assertEqual(first["pendingMcqDistractorScienceTasks"],18)
                self.assertEqual(first["fullAcademicActivityPASS"],0)
                second=admission.admit_newton_source_bound_batch(private=private)
                self.assertEqual(first,second)
                if mutate:
                    mutate(folder,private)
                    with self.assertRaises(ValueError):
                        admission.verify_newton_batch_across_git_heads(
                            private=private)

    def test_three_distinct_newton_tasks_signed_and_idempotent(self):
        self.run_signed()

    def test_mutated_immutable_batch_receipt_rejected(self):
        def mutate(folder,private):
            p=folder/admission._RECEIPT
            v=json.loads(p.read_text())
            v["totalAcademicTaskAcceptances"]=10
            p.write_text(json.dumps(v),encoding="utf8")
        self.run_signed(mutate)

    def test_rewritten_historical_registry_is_rejected(self):
        def mutate(folder,private):
            p=folder/admission._REGISTRY_RECEIPT
            v=json.loads(p.read_text())
            v["independentlyPreviouslyAcceptedAcademicTasks"]=3
            p.write_text(json.dumps(v),encoding="utf8")
        self.run_signed(mutate)

    def test_false_newton_frontier_cannot_claim_extra_task(self):
        def mutate(folder,private):
            p=private/"long-horizon-development"/admission._FRONTIER
            v=json.loads(p.read_text())
            v["cumulativeAcademicTasksAccepted"]=10
            p.write_text(json.dumps(v),encoding="utf8")
        self.run_signed(mutate)

    def test_missing_prior_six_never_creates_new_academic_pass(self):
        with TemporaryDirectory() as temp:
            with patch.object(admission,"_prior_six",
                              side_effect=ValueError("MISSING_SIX_PROOFS")):
                with self.assertRaisesRegex(ValueError,"MISSING_SIX_PROOFS"):
                    admission.admit_newton_source_bound_batch(
                        private=Path(temp))

    def test_wrong_original_signed_third_partition_rejected(self):
        with TemporaryDirectory() as temp:
            fake=copy.deepcopy(PART)
            fake["activity"]["activityId"]="foreign"
            with (patch.object(admission,"_bound_inputs",
                  return_value=(Path(temp),V36,PART,Path(temp),Path(temp))),
                  patch.object(admission,"_signed",return_value=fake)):
                with self.assertRaisesRegex(ValueError,"THIRD_SIGNED"):
                    admission._recomputed_original_newton_proofs(
                        private=Path(temp),ready=NOW,historical=False)

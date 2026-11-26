"""BSA275: signed academic batch admission guards, independent source/receipt.

Synthetic tests intentionally mock the original owner PDF *transport* and
historical A1/A2 signed private state, not scientific correctness. Separate
real Serway source/EN-MS-ZH/vector tests enforce actual original-source math.
"""
from __future__ import annotations
import copy
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch

from app_generator.runtime import v3_academic_science_batch_admission as admission
from app_generator.runtime.v3_native_release_adapter import _v6_checkpoint

HEAD="a"*40
PROPOSAL="b"*64
READY={"gitHead":HEAD,"proposalSha256":PROPOSAL}
FIRST="ce320185009e7c529840a5cf96c75a1f469ad2a5961b3cbbca2ac4f07d9f9d60"
SECOND="8d0ca6feb05d1376db2898613d1cd17d4da61512da429f8d3d8922b3c2cb49df"
THIRD=admission._ID
BASE={
    **READY,
    "sourceSha256":admission._SOURCE_SHA,
    "candidateSha256":admission._CANDIDATE_SHA,
}
V36={
    "integritySha256":"c"*64,
    "completeAcademicProofGatesStillOpen":90,
    "semanticTasksAutomaticallyDispatched":429,
    "fullAcademicProofTasksAccepted":0,
    "publicationAuthorized":False,
}
PART={
    "integritySha256":"d"*64,
    "sourceSha256":admission._SOURCE_SHA,
    "candidateSha256":admission._CANDIDATE_SHA,
    "activity":{"evidenceRows":[{
        "kind":"MCQ_DISTRACTOR_SCIENCE",
        "status":"BOUNDED_SUPPORT_ONLY_REVIEW_REQUIRED",
        "taskId":THIRD,
        "surfaceSha256":"e"*64,
    }]}
}
PROOF={
    "taskId":THIRD,
    "sourceSha256":admission._SOURCE_SHA,
    "candidateSha256":admission._CANDIDATE_SHA,
    "surfaceSha256":"e"*64,
    "witnessSha256":"f"*64,
    "independentScienceWitnessVerified":True,
    "academicTaskAccepted":False,
    "newProviderCalls":0,
    "publicationAuthorized":False,
    "completeAcademicProofGatesStillOpen":90,
}
TWO={
    "independentlyAcceptedAcademicTasks":2,
    "acceptedAcademicTaskIds":[FIRST,SECOND],
    "academicProofReceiptSha256s":["1"*64,"2"*64],
    "completeAcademicProofGatesStillOpen":90,
    "publicationAuthorized":False,
}


def reg(proof=PROOF, validator=lambda p:None):
    item=admission.ScienceAdmissionRegistry()
    item.register(admission.ScienceAdmissionHandler(
        "VECTOR_PARALLEL_NOT_PERPENDICULAR",THIRD,
        lambda source,candidate:proof,validator))
    return item


class SignedScienceBatch(TestCase):
    def source(self,proof=PROOF,rows=PART,verify=lambda p:None):
        adapter=reg(proof,verify)
        with patch.object(admission,"_bound_inputs",return_value=(
             Path("private"),V36,rows,Path("original.pdf"),Path("candidate.json"))):
            return admission._proofs_for_signed_v36(
                private=Path("."),ready=READY,historical=False,rules=adapter)

    def test_exact_pending_task_and_independent_science_verifier_required(self):
        v,part,proofs=self.source()
        self.assertEqual(v,V36)
        self.assertEqual(part,PART)
        self.assertEqual(proofs[0]["taskId"],THIRD)
        self.assertEqual(proofs[0]["independentScienceProof"],PROOF)

    def test_changed_signed_source_or_candidate_rejected(self):
        for key,val in (("taskId","0"*64),
                        ("surfaceSha256","0"*64),
                        ("candidateSha256","0"*64),
                        ("independentScienceWitnessVerified",False),
                        ("academicTaskAccepted",True),
                        ("completeAcademicProofGatesStillOpen",89),
                        ("publicationAuthorized",True)):
            forged={**PROOF,key:val}
            with self.subTest(field=key),self.assertRaisesRegex(
                ValueError,"SCIENCE_HANDLER_NOT_SIGNED_TASK"):
                self.source(proof=forged)

    def test_forged_v36_task_row_rejected(self):
        forged=copy.deepcopy(PART)
        forged["activity"]["evidenceRows"][0]["surfaceSha256"]="0"*64
        with self.assertRaisesRegex(ValueError,"SCIENCE_HANDLER_NOT_SIGNED_TASK"):
            self.source(rows=forged)

    def test_independent_scientific_validation_cannot_be_skipped(self):
        def reject(proof):
            raise ValueError("PHYSICS_VECTOR_COUNTERMODEL_FALSE")
        with self.assertRaisesRegex(ValueError,"PHYSICS_VECTOR_COUNTERMODEL_FALSE"):
            self.source(verify=reject)

    def test_duplicate_or_inert_registered_admission_handler_rejected(self):
        i=reg()
        with self.assertRaisesRegex(ValueError,"DUPLICATE_OR_UNTRUSTED"):
            i.register(admission.ScienceAdmissionHandler(
                "VECTOR_PARALLEL_NOT_PERPENDICULAR",THIRD,
                lambda x,y:PROOF,lambda p:None))
        with self.assertRaisesRegex(ValueError,"DUPLICATE_OR_UNTRUSTED"):
            i.register(admission.ScienceAdmissionHandler(
                "WRONG_EXTERNAL_EXECUTOR","b"*64,None,lambda p:None))

    def fixture(self,root,with_audit=True):
        root=Path(root)
        folder=root/"owner-five-stage-completion"/HEAD/PROPOSAL
        folder.mkdir(parents=True)
        (root/"long-horizon-development").mkdir(parents=True)
        if with_audit:
            _v6_checkpoint(folder/admission._REGISTRY_RECEIPT,{
                **READY,
                "status":"BSA274_PRIVATE_SIGNED_REGISTRY_TWO_REAL_PROOFS_25_PENDING",
                "sourceBoundRegistryAudit":{
                    "acceptedMcqDistractorTaskCount":2},
                "independentlyPreviouslyAcceptedAcademicTasks":2,
                "publicationAuthorized":False,
            })
        registry_receipt=(
            __import__("json").loads((folder/admission._REGISTRY_RECEIPT)
              .read_text(encoding="utf8")) if with_audit else {})
        audit={
            "gitHead":HEAD,
            "registryReceiptSha256":registry_receipt.get("integritySha256"),
            "independentlyAcceptedAcademicTasks":2,
            "signedV36Sha256":V36["integritySha256"],
        }
        return folder,audit

    def run_full(self,mutate_receipt=None):
        with TemporaryDirectory() as temp:
            private=Path(temp)
            folder,audit=self.fixture(private)
            with (patch.object(admission,"read_long_horizon_development",
                               return_value=BASE),
                  patch.object(admission,"_prior_two",return_value=TWO),
                  patch.object(admission,"verify_registry_audit",
                               return_value=audit),
                  patch.object(admission,"_proofs_for_signed_v36",
                               return_value=(V36,PART,[{
                                   "scienceFamily":"VECTOR_PARALLEL_NOT_PERPENDICULAR",
                                   "taskId":THIRD,
                                   "surfaceSha256":PROOF["surfaceSha256"],
                                   "independentScienceProof":PROOF,
                               }]))):
                first=admission.admit_new_scientific_batch(
                    private=private,rules=reg())
                self.assertEqual(first["independentlyAcceptedAcademicTasks"],3)
                self.assertEqual(first["fullAcademicTasksStillOpen"],426)
                self.assertEqual(first["completeAcademicProofGatesStillOpen"],90)
                self.assertEqual(first["fullAcademicActivityPASS"],0)
                second=admission.admit_new_scientific_batch(
                    private=private,rules=reg())
                self.assertEqual(first,second)
                if mutate_receipt:
                    mutate_receipt(folder,private)
                    with self.assertRaises(ValueError):
                        admission.verify_academic_batch_across_git_heads(
                            private=private,rules=reg())

    def test_immutable_three_task_admission_and_idempotent_readback(self):
        self.run_full()

    def test_mutated_signed_batch_receipt_fail_closed(self):
        def mutate(folder,private):
            path=folder/admission._RECEIPT
            t=__import__("json").loads(path.read_text(encoding="utf8"))
            t["fullAcademicTasksStillOpen"]=425
            path.write_text(__import__("json").dumps(t),encoding="utf8")
        self.run_full(mutate)

    def test_modified_original_audit_receipt_not_reusable(self):
        def mutate(folder,private):
            path=folder/admission._REGISTRY_RECEIPT
            t=__import__("json").loads(path.read_text(encoding="utf8"))
            t["independentlyPreviouslyAcceptedAcademicTasks"]=3
            path.write_text(__import__("json").dumps(t),encoding="utf8")
        self.run_full(mutate)

    def test_tampered_separate_frontier_rejected(self):
        def mutate(folder,private):
            path=private/"long-horizon-development"/admission._FRONTIER
            t=__import__("json").loads(path.read_text(encoding="utf8"))
            t["acceptedAcademicTaskCount"]=4
            path.write_text(__import__("json").dumps(t),encoding="utf8")
        self.run_full(mutate)

    def test_cannot_admit_without_signed_bsa274_audit(self):
        with TemporaryDirectory() as temp:
            private=Path(temp)
            self.fixture(private,with_audit=False)
            with (patch.object(admission,"read_long_horizon_development",
                               return_value=BASE),
                  patch.object(admission,"_prior_two",return_value=TWO),
                  patch.object(admission,"verify_registry_audit",
                               side_effect=ValueError("NO_PRIOR_SIGNED_REGISTRY"))):
                with self.assertRaisesRegex(ValueError,"NO_PRIOR_SIGNED_REGISTRY"):
                    admission.admit_new_scientific_batch(
                        private=private,rules=reg())

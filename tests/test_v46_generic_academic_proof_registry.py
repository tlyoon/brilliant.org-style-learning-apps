"""BSA274: registry is extensible but does not manufacture academic acceptance.

Source-free synthetic CI fixtures exercise only dispatch and tamper barriers.
The genuine original PDF, signed partition readback, historic A1/A2 receipts,
and exact rational science are separately required on the owner Yoga6.
"""
from __future__ import annotations

import copy
from hashlib import sha256
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch

from app_generator.runtime import v3_academic_proof_registry as reg
from app_generator.runtime import v3_academic_proof_registry_receipt as seal
from app_generator.validation.full_semantic_proof_queue import (
    plan_full_semantic_proofs,
)

ROOT=Path(__file__).resolve().parents[1]
CANDIDATE=ROOT/"content/chapter-9/section-9-1/package.json"
PACKAGE=json.loads(CANDIDATE.read_text(encoding="utf8"))
SOURCE=reg._SOURCE_SHA
CANDIDATE_SHA=reg._CANDIDATE_SHA
QUEUE=plan_full_semantic_proofs(package=PACKAGE,source_sha256=SOURCE)
TASKS=[x for x in QUEUE["tasks"] if x["kind"]=="MCQ_DISTRACTOR_SCIENCE"]
# Source-free CI uses the tracked public package, NOT the owner-private
# frozen candidate; its SHA-bound task IDs must be derived locally. NEVER
# replace the genuinely admitted A1/A2 original-source private task IDs.
FIRST,SECOND,THIRD=(t["taskId"] for t in TASKS[:3])
HEAD="a"*40
PROPOSAL="b"*64
READY={"gitHead":HEAD,"proposalSha256":PROPOSAL}


def sha(obj):
    return sha256(json.dumps(obj,sort_keys=True).encode("utf8")).hexdigest()


def fixture():
    part=[]
    index=[]
    for idx,activity in enumerate(PACKAGE["activities"]):
        rows=[{"taskId":x["taskId"],"kind":x["kind"],
               "surfaceSha256":x["surfaceSha256"],
               "status":"BOUNDED_SUPPORT_ONLY_REVIEW_REQUIRED"}
              for x in QUEUE["tasks"] if x["activityId"]==activity["id"]]
        integrity=sha({"id":idx})
        part.append({
            **READY,"sourceSha256":SOURCE,"candidateSha256":CANDIDATE_SHA,
            "integritySha256":integrity,"publicationAuthorized":False,
            "academicPASS":0,
            "activity":{"activityId":activity["id"],"evidenceRows":rows},
        })
        index.append({"activityId":activity["id"],"signedEvidenceSha256":integrity})
    v36={
        "integritySha256":"c"*64,
        "semanticTasksAutomaticallyDispatched":429,
        "activitySignedPartitionCount":18,
        "fullAcademicProofTasksAccepted":0,
        "completeAcademicProofGatesStillOpen":90,
        "publicationAuthorized":False,
        "signedPartitionHashes":index,
    }
    state={
        **READY, "sourceSha256":SOURCE,"candidateSha256":CANDIDATE_SHA,
        "academicAcceptedProofTaskCount":0,
        "completeAcademicProofGatesStillOpen":90,
    }
    return state,v36,part


def admission(task_id):
    return {
        "taskId":task_id,
        "proofReceiptSha256":sha({"receipt":task_id}),
        "originGitHead":"e"*40,
        "sourceSha256":SOURCE,
        "candidateSha256":CANDIDATE_SHA,
        "verifiedAcademicAcceptances":1,
        "providerCalls":0,
        "publicationAuthorized":False,
    }


def evidence_registry(ids=(FIRST,SECOND)):
    r=reg.AcademicProofRegistry()
    for i,task_id in enumerate(ids):
        r.register(reg.AcademicProofRule(
            "TEST_PROOF_"+str(i),task_id,"TEST_VECTOR_IDENTITY_"+str(i),
            "MCQ_DISTRACTOR_SCIENCE",
            lambda private,tid=task_id:admission(tid)))
    return r


class GenericProofRegistry(TestCase):
    def audit(self,registry=None,modify=None):
        state,v36,parts=fixture()
        if modify: modify(state,v36,parts)
        with (patch.object(reg,"read_long_horizon_development",
                           return_value=state),
              patch.object(reg,"_bound_inputs",return_value=(
                  Path("."),v36,parts[0],Path("original.pdf"),CANDIDATE)),
              patch.object(reg,"_signed",side_effect=lambda folder,name,ready:
                  parts[int(name.split("_")[-1].split(".")[0])-1])):
            return reg.audit_source_bound_academic_registry(
                private=Path("."),rules=registry or evidence_registry())

    def test_exact_27_original_mcq_tasks_with_two_distinct_acceptances(self):
        out=self.audit()
        self.assertEqual(out["fullSemanticTaskCount"],429)
        self.assertEqual(out["signedMcqPartitionCount"],9)
        self.assertEqual(out["acceptedMcqDistractorTaskCount"],2)
        self.assertEqual(out["pendingMcqDistractorTaskCount"],25)
        self.assertEqual(out["acceptedAcademicTaskIds"],[FIRST,SECOND])
        self.assertEqual(out["fullAcademicTasksStillOpen"],427)
        self.assertEqual(out["completeAcademicProofGatesStillOpen"],90)
        self.assertEqual(out["fullAcademicActivityPASS"],0)
        self.assertFalse(out["publicationAuthorized"])
        self.assertTrue(all(x["status"]=="REVIEW_REQUIRED"
                            for x in out["pendingMcqTasks"]))

    def test_new_genuine_evaluator_can_register_without_changing_dispatcher(self):
        out=self.audit(evidence_registry((FIRST,SECOND,THIRD)))
        self.assertEqual(out["acceptedMcqDistractorTaskCount"],3)
        self.assertEqual(out["pendingMcqDistractorTaskCount"],24)
        self.assertEqual(out["fullAcademicTasksStillOpen"],426)
        self.assertEqual(out["completeAcademicProofGatesStillOpen"],90)
        # Only a *mock* third independent readback is injected here; never a
        # real admission claim or production rule.

    def test_no_unregistered_task_can_be_accepted_by_queue_status(self):
        out=self.audit(evidence_registry((FIRST,)))
        self.assertEqual(out["acceptedMcqDistractorTaskCount"],1)
        self.assertEqual(out["pendingMcqDistractorTaskCount"],26)
        self.assertEqual(out["fullAcademicTasksStillOpen"],428)

    def test_invalid_or_duplicate_handler_registration_fails_closed(self):
        p=evidence_registry((FIRST,))
        for rule in (
            reg.AcademicProofRule("TEST_PROOF_0",THIRD,"TEST_SCIENCE",
                reg._KIND,lambda _:admission(THIRD)),
            reg.AcademicProofRule("DIFFERENT_ID",FIRST,"TEST_SCIENCE",
                reg._KIND,lambda _:admission(FIRST)),
            reg.AcademicProofRule("EXTRA_RULE",THIRD,"TEST_SCIENCE",
                "COMPLETE_SCIENTIFIC_MEANING",lambda _:admission(THIRD)),
            reg.AcademicProofRule("INVALID_RULE",THIRD,"TEST_SCIENCE",
                reg._KIND,None),
            reg.AcademicProofRule("../escape",THIRD,"TEST_SCIENCE",
                reg._KIND,lambda _:admission(THIRD)),
        ):
            with self.subTest(rule=rule.rule_id),self.assertRaises(ValueError):
                p.register(rule)

    def test_producer_claiming_pass_without_valid_receipt_fails(self):
        for field,val in (
            ("proofReceiptSha256","not-signed"),
            ("sourceSha256","0"*64),
            ("candidateSha256","1"*64),
            ("verifiedAcademicAcceptances",2),
            ("providerCalls",1),
            ("publicationAuthorized",True),
        ):
            r=reg.AcademicProofRegistry()
            def fake(private,field=field,val=val):
                x=admission(FIRST);x[field]=val;return x
            r.register(reg.AcademicProofRule("MUTANT_RULE",FIRST,
                "TEST_SCIENCE",reg._KIND,fake))
            with self.subTest(field=field),self.assertRaisesRegex(
                ValueError,"WITHOUT_INDEPENDENT_SIGNED_ACCEPTANCE"):
                self.audit(r)

    def test_unknown_or_forged_task_id_rejected(self):
        r=evidence_registry(("f"*64,))
        with self.assertRaisesRegex(ValueError,"NOT_IN_SIGNED_TASK_BACKLOG"):
            self.audit(r)

    def test_wrong_original_source_or_candidate_identity_rejected(self):
        for field,val in (("sourceSha256","0"*64),
                          ("candidateSha256","0"*64),
                          ("academicAcceptedProofTaskCount",2)):
            def modify(state,v36,part):
                state[field]=val
            with self.subTest(field=field),self.assertRaisesRegex(
                ValueError,"SOURCE_FREE_BASELINE"):
                self.audit(modify=modify)

    def test_signed_partition_digest_or_row_tampering_rejected(self):
        def badsha(state,v36,parts):
            v36["signedPartitionHashes"][1]["signedEvidenceSha256"]="0"*64
        with self.assertRaisesRegex(ValueError,"PARTITION_NOT_AUTHENTIC"):
            self.audit(modify=badsha)
        def badrow(state,v36,parts):
            next(r for r in parts[1]["activity"]["evidenceRows"]
                 if r["kind"]==reg._KIND)["surfaceSha256"]="0"*64
        with self.assertRaisesRegex(ValueError,"UNSIGNED_OR_FORGED"):
            self.audit(modify=badrow)

    def test_forged_v36_full_academic_acceptance_rejected(self):
        def forged(state,v36,parts):
            v36["fullAcademicProofTasksAccepted"]=2
        with self.assertRaisesRegex(ValueError,"SIGN ED|SIGNED_V36".replace(" ","")):
            self.audit(modify=forged)

    def test_failed_prior_verifier_stops_entire_registry_without_count(self):
        r=reg.AcademicProofRegistry()
        def failure(private):
            raise ValueError("ACADEMIC_A1_SIGNATURE_MISSING")
        r.register(reg.AcademicProofRule("FAILURE_RULE",FIRST,"TEST_SCIENCE",
                                       reg._KIND,failure))
        with self.assertRaisesRegex(ValueError,"ACADEMIC_A1_SIGNATURE_MISSING"):
            self.audit(r)

    def test_signed_registry_receipt_is_immutable_and_independently_recomputed(self):
        proof=self.audit()
        with TemporaryDirectory() as d:
            private=Path(d)
            folder=private/"owner-five-stage-completion"/HEAD/PROPOSAL
            folder.mkdir(parents=True)
            with (patch.object(seal,"_ready",return_value=READY),
                  patch.object(seal,"audit_source_bound_academic_registry",
                               return_value=proof)):
                first=seal.sign_registry_audit(private=private)
                second=seal.sign_registry_audit(private=private)
                self.assertEqual(first,second)
                self.assertEqual(first["independentlyAcceptedAcademicTasks"],2)
                self.assertEqual(first["pendingMcqDistractorScienceTasks"],25)
                receipt=folder/seal._RECEIPT
                saved=json.loads(receipt.read_text(encoding="utf8"))
                saved["sourceBoundRegistryAudit"]["acceptedMcqDistractorTaskCount"]=3
                receipt.write_text(json.dumps(saved),encoding="utf8")
                with self.assertRaises(ValueError):
                    seal.verify_registry_audit(private=private)

    def test_no_registry_receipt_can_claim_new_academic_acceptance(self):
        proof=self.audit()
        with TemporaryDirectory() as d:
            private=Path(d)
            folder=private/"owner-five-stage-completion"/HEAD/PROPOSAL
            folder.mkdir(parents=True)
            with (patch.object(seal,"_ready",return_value=READY),
                  patch.object(seal,"audit_source_bound_academic_registry",
                               return_value=proof)):
                seal.sign_registry_audit(private=private)
                saved=json.loads((folder/seal._RECEIPT).read_text(encoding="utf8"))
                saved["academicTasksAcceptedByThisRegistryAudit"]=1
                (folder/seal._RECEIPT).write_text(json.dumps(saved),encoding="utf8")
                with self.assertRaises(ValueError):
                    seal.verify_registry_audit(private=private)

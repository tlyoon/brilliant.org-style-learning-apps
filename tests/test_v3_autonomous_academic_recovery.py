"""BSA251 V24: test REAL normal dispatch semantics, not synthetic PASS."""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from app_generator.runtime import v3_autonomous_academic_recovery as m
from app_generator.runtime.v3_malay_auto_revision import _replace_in_malay
from app_generator.validation.malay_conservation_lexicon import ROOTS
from app_generator.validation.academic_qa import REQUIRED

ROOT=Path(__file__).resolve().parents[1]


class HistoryFirstAcademicRecoveryTests(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.folder=Path(tmp.name)
        self.pdf=self.folder/"source.pdf"
        self.pdf.write_bytes(b"%PDF-BSA251-controlled-test-pdf")
        self.source_sha=sha256(self.pdf.read_bytes()).hexdigest()
        self.old_raw=(ROOT/m._PACKAGE).read_bytes()
        self.old=json.loads(self.old_raw)
        self.old_sha=sha256(self.old_raw).hexdigest()
        paths=[];counts={s:0 for s,_,_ in ROOTS}
        self.new=_replace_in_malay(self.old,"",paths,counts)
        self.revised_file=self.folder/"revised.json"
        self.new_raw=(json.dumps(self.new,ensure_ascii=False,indent=2)+"\n").encode("utf8")
        self.revised_file.write_bytes(self.new_raw)
        self.new_sha=sha256(self.new_raw).hexdigest()
        self.history={a:b[0] for a,b in m._DISPATCH.items()}
        self.review={}
        for idx,a in enumerate(self.new["activities"]):
            self.review[a["id"]]=(
                "ORIGINAL_UNCERTAIN_NO_REPLAY" if idx==0
                else "NEW_MODEL_CONSENSUS_ADVISORY_ONLY"
                if a["id"] in {
                    "act-mcq-05-third-law-connection",
                    "act-mcq-08-isolated-subsystem-fallacy",
                    "act-int-05-newton-second-law-steps-order",
                    "act-int-08-conservation-validity-select",
                } else "HISTORIC_IDENTICAL_MODEL_EVIDENCE_ONLY")
        self.changed={aid for aid,status in self.review.items()
            if status=="NEW_MODEL_CONSENSUS_ADVISORY_ONLY"}
        self.metrics={"math":0,"answer":0,"numeric":0,"academic":0,"reanchor":0}

    def report(self, *, failure=None):
        rows=[]
        for a in self.new["activities"]:
            aid=a["id"]
            states={gate:"REVIEW_REQUIRED" for gate in REQUIRED}
            if aid==failure:
                states["physics_consistency"]="FAIL"
            rows.append({
                "activityId":aid,
                "activitySha256":sha256(json.dumps(
                    a,sort_keys=True,ensure_ascii=False,
                    separators=(",",":")).encode("utf8")).hexdigest(),
                "academicQA":"FAIL" if aid==failure else "REVIEW_REQUIRED",
                "gates":states,
                "sourceLocationVerified":True,
            })
        return {
            "packageSha256":self.new_sha,
            "sourceSha256":self.source_sha,
            "publicationAuthorized":False,
            "activities":rows,
            "counts":{"PASS":0,"FAIL":int(failure is not None),
                      "REVIEW_REQUIRED":18-int(failure is not None)},
        }

    def run_mocked(self, *, report=None):
        actual=self.report() if report is None else report
        def rebind(**kwargs):
            self.metrics["reanchor"]+=1
            self.assertEqual(kwargs["expected_changed_ids"],self.changed)
            return {"packets":{a["id"]:{} for a in self.new["activities"]}},sorted(self.changed)
        def audit(**kwargs):
            self.metrics["academic"]+=1
            self.assertEqual(kwargs["package_path"],self.revised_file)
            self.assertEqual(kwargs["source_sha256"],self.source_sha)
            return actual
        def math():
            self.metrics["math"]+=1
            return {f"identity-{i}":True for i in range(6)}
        def labels(_):
            self.metrics["answer"]+=1
            return {f"check-{i}":True for i in range(5)}
        def scan(_):
            self.metrics["numeric"]+=1
            return (9,[])
        with (patch.object(m,"independently_rebind_revision",side_effect=rebind),
              patch.object(m,"audit_activity_matrix",side_effect=audit),
              patch.object(m,"_bounded_math_witnesses",side_effect=math),
              patch.object(m,"_bounded_mcq_labels",side_effect=labels),
              patch.object(m,"_scan_activity",side_effect=scan)):
            return m.execute_academic_evidence_cycle(
                repo=ROOT,pdf=self.pdf,source_sha=self.source_sha,
                original=self.old,revised=self.new,
                original_sha=self.old_sha,revised_sha=self.new_sha,
                revised_path=self.revised_file,
                original_anchors=[],changed_ids=self.changed,
                previous_review=self.review,history=self.history)

    def test_full_ninety_proof_gaps_are_actions_not_software_errors(self):
        got=self.run_mocked()
        self.assertEqual(got["status"],
            "STOP_INDEPENDENT_ACADEMIC_PROOFS_NOT_YET_SUPPLIED")
        self.assertTrue(got["fixedPointReached"])
        self.assertEqual(got["roundsCompleted"],2)
        self.assertEqual(len(got["nextEvidenceWorkQueue"]),90)
        self.assertEqual(got["independentProofGaps"],90)
        self.assertEqual(got["formalAcademicPassedActivities"],0)
        self.assertFalse(got["publicationAuthorized"])
        self.assertEqual(self.metrics["academic"],2)
        self.assertEqual(self.metrics["reanchor"],2)
        self.assertEqual(self.metrics["math"],2)
        self.assertEqual(self.metrics["answer"],2)
        self.assertEqual(self.metrics["numeric"],36)
        self.assertEqual(got["rechecked"]["numericLocaleFieldsChecked"],162)
        self.assertEqual(len(set(got["verifierActionsActuallyExecuted"])),6)
        self.assertTrue(all(q["failureClass"]=="MISSING_INDEPENDENT_PROOF"
                            for q in got["nextEvidenceWorkQueue"]))
        self.assertTrue(all(q["publicationAuthorized"] is False
                            for q in got["nextEvidenceWorkQueue"]))

    def test_known_deterministic_failure_stops_without_fabricated_repair(self):
        got=self.run_mocked(report=self.report(
            failure="act-mcq-05-third-law-connection"))
        self.assertEqual(got["status"],
                         "STOP_UNHANDLED_VERSIONED_DETERMINISTIC_DEFECT")
        self.assertEqual(got["newDeterministicDefectSlots"],1)
        self.assertEqual(got["independentProofGaps"],89)
        row=next(q for q in got["nextEvidenceWorkQueue"]
                 if q["activityId"]=="act-mcq-05-third-law-connection"
                 and q["gate"]=="physics_consistency")
        self.assertEqual(row["failureClass"],"DETERMINISTIC_DEFECT")
        self.assertIn("STOP_EXACT_VERSION",row["nextAction"])
        self.assertFalse(got["publicationAuthorized"])

    def test_actual_registered_history_is_resolved_and_static(self):
        mapping=m._approved_history(ROOT)
        self.assertEqual(mapping,self.history)
        self.assertEqual(len(mapping),6)

    def test_retired_remedy_rejected_before_any_proof_claim(self):
        from copy import deepcopy
        doc=json.loads((ROOT/"docs/recurrence_registry.json").read_text(encoding="utf8"))
        for item in doc["incidents"]:
            if item.get("id")=="BSA-20261122-247":
                item["status"]="retired"
        with tempfile.TemporaryDirectory() as td:
            base=Path(td)
            (base/"docs").mkdir()
            (base/"docs/recurrence_registry.json").write_text(
                json.dumps(doc),encoding="utf8")
            with self.assertRaisesRegex(ValueError,"V24_HISTORICAL_REMEDY_RETIRED"):
                m._approved_history(base)

    def test_missing_or_tampered_source_never_reuses_prior_proof(self):
        self.pdf.write_bytes(b"%PDF-changed-original")
        with self.assertRaisesRegex(ValueError,"V24_REAL_REVISED_PACKAGE_OR_SOURCE"):
            self.run_mocked()

    def test_changed_private_activity_never_inherits_old_proofs(self):
        self.revised_file.write_bytes(self.revised_file.read_bytes()+b" ")
        with self.assertRaisesRegex(ValueError,"V24_REAL_REVISED_PACKAGE_OR_SOURCE"):
            self.run_mocked()

    def test_model_consensus_cannot_promote_any_complete_gate(self):
        q=m._safe_gate_queue(self.report(),self.new["activities"],
                             prior_review=self.review,action_history=self.history)
        for item in q:
            self.assertEqual(item["gateState"],"REVIEW_REQUIRED")
            self.assertEqual(item["failureClass"],"MISSING_INDEPENDENT_PROOF")
        status=set(x["historicalReviewStatus"] for x in q)
        self.assertEqual(status,{
            "ORIGINAL_UNCERTAIN_NO_REPLAY",
            "HISTORIC_IDENTICAL_MODEL_EVIDENCE_ONLY",
            "NEW_MODEL_CONSENSUS_ADVISORY_ONLY",
        })

    def test_forged_gate_activity_identity_cannot_enter_workqueue(self):
        report=self.report()
        report["activities"][0]["activitySha256"]="0"*64
        with self.assertRaisesRegex(ValueError,"V24_REVIEW_RESULT_ACTIVITY_VERSION_DRIFT"):
            m._safe_gate_queue(report,self.new["activities"],
                prior_review=self.review,action_history=self.history)

    def test_malformed_activity_gate_roster_cannot_lose_required_proof(self):
        report=self.report()
        del report["activities"][0]["gates"]["multilingual_meaning"]
        with self.assertRaisesRegex(ValueError,"V24_MISSING_ACADEMIC_GATE"):
            m._safe_gate_queue(report,self.new["activities"],
                prior_review=self.review,action_history=self.history)

    def test_proof_gap_queue_is_deterministic_on_restart(self):
        first=self.run_mocked()
        second=self.run_mocked()
        self.assertEqual(first,second)
        self.assertEqual(first["iterations"][0]["evidenceDigestSha256"],
                         first["iterations"][1]["evidenceDigestSha256"])

    def test_private_five_gate_workqueues_are_signed_split_and_restart_safe(self):
        result=self.run_mocked()
        identity={"gitHead":"a"*40,
                  "proposalSha256":"b"*64,
                  "publicationAuthorized":False}
        first=m._persist_private_gate_queues(self.folder,identity,result)
        self.assertEqual(len(first),5)
        self.assertEqual(sum(row["taskCount"] for row in first),90)
        self.assertEqual(m._persist_private_gate_queues(
            self.folder,identity,result),first)
        for row in first:
            file=self.folder/f"V24_GATE_{row['gate'].upper()}_PROOF_TASKS.json"
            self.assertLess(file.stat().st_size,12000)
            body=json.loads(file.read_text(encoding="utf8"))
            self.assertEqual(len(body["proofTasks"]),18)
            self.assertEqual(body["integritySha256"],row["signedQueueSha256"])
            self.assertNotIn("sourceEvidence",file.read_text(encoding="utf8"))
        changed=self.folder/f"V24_GATE_{REQUIRED[0].upper()}_PROOF_TASKS.json"
        forged=json.loads(changed.read_text(encoding="utf8"))
        forged["proofTasks"][0]["gateState"]="PASS"
        changed.write_text(json.dumps(forged),encoding="utf8")
        with self.assertRaisesRegex(ValueError,"V3_NATIVE_ADAPTER_V6_CHECKPOINT_CHANGED"):
            m._persist_private_gate_queues(self.folder,identity,result)

    def test_private_gate_queue_cannot_silently_drop_evidence_task(self):
        result=self.run_mocked()
        result["nextEvidenceWorkQueue"].pop()
        with self.assertRaisesRegex(ValueError,"V24_PRIVATE_NINETY"):
            m._persist_private_gate_queues(
                self.folder,{"gitHead":"a"*40,"proposalSha256":"b"*64},
                result)

    def test_worker_normal_execution_includes_v24(self):
        src=(ROOT/"scripts/run_v3_yoga6_recovery_worker.py").read_text(encoding="utf8")
        self.assertIn("run_post_v22_autonomous_academic_recovery(",src)
        self.assertIn('result["autonomousAcademicRecovery"]',src)
        self.assertIn('"historicalRemedyHandlersActuallyExecuted")==6',src)

    def test_absent_new_model_role_does_not_trigger_paid_or_replay(self):
        entries=[
            {"activityId":aid,"sha":str(i)*64}
            for i,aid in enumerate(sorted(self.changed),1)
        ]
        prior=[{"activityId":a["id"]} for a in self.old["activities"][1:]]
        with (patch.object(m,"fresh_revised91_inputs",
                           return_value={"stagedReviewInputs":entries}),
              patch.object(m,"section91_evidence",return_value={
                  "oldUncertainIndex":0}),
              patch.object(m,"verified_section91_standing_passes",
                           return_value=prior),
              patch.object(m,"unsent_revised_input",return_value=True),
              patch.object(m,"read_prior_two_role_science",
                           side_effect=AssertionError("MUST_NOT_READ_MISSING_CLAIM"))):
            status=m._review_inventory(ROOT,self.folder,"a"*40,
                                       "b"*64,self.new["activities"])
        self.assertEqual(len(status),18)
        self.assertTrue(all(status[aid]=="NEW_MODEL_REVIEW_NOT_YET_SUBMITTED"
                            for aid in self.changed))
        self.assertEqual(status[self.new["activities"][0]["id"]],
                         "ORIGINAL_UNCERTAIN_NO_REPLAY")

    def test_unknown_prior_inflight_role_remains_stop_not_retry(self):
        entries=[
            {"activityId":aid,"sha":str(i)*64}
            for i,aid in enumerate(sorted(self.changed),1)
        ]
        prior=[{"activityId":a["id"]} for a in self.old["activities"][1:]]
        with (patch.object(m,"fresh_revised91_inputs",
                           return_value={"stagedReviewInputs":entries}),
              patch.object(m,"section91_evidence",return_value={
                  "oldUncertainIndex":0}),
              patch.object(m,"verified_section91_standing_passes",
                           return_value=prior),
              patch.object(m,"unsent_revised_input",return_value=False),
              patch.object(m,"read_prior_two_role_science",
                           side_effect=ValueError("OLD_REQUEST_UNRESOLVED_NO_REPLAY"))):
            with self.assertRaisesRegex(ValueError,"OLD_REQUEST_UNRESOLVED_NO_REPLAY"):
                m._review_inventory(ROOT,self.folder,"a"*40,
                                     "b"*64,self.new["activities"])


if __name__=="__main__":
    unittest.main()

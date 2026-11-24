"""BSA261: isolate blocker to affected operation, continue independent work."""
from __future__ import annotations

from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from app_generator.runtime import v3_blocker_isolated_development as lanes
from app_generator.runtime import v3_auto_development_handoff as advance
from app_generator.runtime.v3_revised_source_proof_rebinding import _signed

ROOT=Path(__file__).resolve().parents[1]
READY={"gitHead":"b"*40,"proposalSha256":"a"*64,
       "publicationAuthorized":False}

class IsolatedDevelopmentTests(unittest.TestCase):
    def _place(self,base):
        private=Path(base)
        folder=private/"owner-five-stage-completion"/READY["gitHead"]/READY["proposalSha256"]
        folder.mkdir(parents=True)
        return private,folder

    def _lane(self,name,requires=(),outcome=None):
        def run(*args):
            if isinstance(outcome,Exception):
                raise outcome
            return {"status":"PASS_"+name.upper(),**(outcome or {})}
        return lanes.VerifiedLane(name,requires,run)

    def test_missing_academic_dependency_does_not_block_recovery_and_content(self):
        with tempfile.TemporaryDirectory() as td:
            private,folder=self._place(td)
            allow=(
                self._lane("regression"),
                self._lane("structure"),
                self._lane("science",("v32_source_chain",)),
            )
            with patch.object(lanes,"_LANES",allow):
                result=lanes.run_safe_isolated_development_lanes(
                    repo=ROOT,private=private,ready=READY,
                    completed_dependencies=set(),
                    blocked_operation="source_bound_academic_successor_chain")
            self.assertEqual(result["status"],
                             "INDEPENDENT_SAFE_LANES_ADVANCED_WITH_QUARANTINE")
            self.assertEqual(result["independentlyVerifiedLanes"],2)
            self.assertEqual(result["quarantinedLaneCount"],1)
            self.assertEqual(result["lanes"][2]["status"],"QUARANTINED_DEPENDENCY")
            self.assertEqual(result["lanes"][2]["missingPrerequisiteCodes"],
                             ["v32_source_chain"])
            self.assertEqual(result["blockedOperationCode"],
                             "source_bound_academic_successor_chain")
            self.assertEqual(len(list(folder.glob("V33_*.json"))),1)
            self.assertEqual(_signed(folder,result["privateSignedReceiptName"],READY)
                             ["integritySha256"],result["privateSignedReceiptSha256"])

    def test_one_lane_exception_does_not_strand_other_eligible_lanes(self):
        with tempfile.TemporaryDirectory() as td:
            private,_=self._place(td)
            with patch.object(lanes,"_LANES",(
                self._lane("first",outcome=RuntimeError("secret=DO_NOT_LOG")),
                self._lane("second"),
                self._lane("third"),
            )):
                result=lanes.run_safe_isolated_development_lanes(
                    repo=ROOT,private=private,ready=READY,
                    completed_dependencies=set())
            self.assertEqual(result["independentlyVerifiedLanes"],2)
            self.assertEqual(result["quarantinedLaneCount"],1)
            self.assertEqual(result["lanes"][0]["reasonClass"],"RuntimeError")
            self.assertEqual(result["lanes"][1]["status"],"VERIFIED_INDEPENDENT_PASS")
            self.assertEqual(result["lanes"][2]["status"],"VERIFIED_INDEPENDENT_PASS")
            self.assertNotIn("DO_NOT_LOG",str(result))

    def test_academic_claim_from_side_lane_is_rejected_not_accepted(self):
        with tempfile.TemporaryDirectory() as td:
            private,_=self._place(td)
            bad=self._lane("false_proof",
                           outcome={"fullAcademicPASS":1})
            with patch.object(lanes,"_LANES",(bad,self._lane("safe"))):
                result=lanes.run_safe_isolated_development_lanes(
                    repo=ROOT,private=private,ready=READY,
                    completed_dependencies=set())
            self.assertEqual(result["quarantinedLaneCount"],1)
            self.assertEqual(result["independentlyVerifiedLanes"],1)
            self.assertEqual(result["fullAcademicPASS"],0)
            self.assertFalse(result["publicationAuthorized"])

    def test_invalid_workstream_can_not_assert_publication(self):
        with tempfile.TemporaryDirectory() as td:
            private,_=self._place(td)
            bad=self._lane("public",outcome={"publicationAuthorized":True})
            with patch.object(lanes,"_LANES",(bad,self._lane("private"))):
                result=lanes.run_safe_isolated_development_lanes(
                    repo=ROOT,private=private,ready=READY,
                    completed_dependencies=set())
            self.assertEqual(result["quarantinedLaneCount"],1)
            self.assertFalse(result["publicationAuthorized"])

    def test_failed_then_repaired_lane_never_overwrites_failed_receipt(self):
        with tempfile.TemporaryDirectory() as td:
            private,folder=self._place(td)
            with patch.object(lanes,"_LANES",(self._lane("fail",outcome=ValueError("no")),)):
                before=lanes.run_safe_isolated_development_lanes(
                    repo=ROOT,private=private,ready=READY,
                    completed_dependencies=set())
            old=folder/before["privateSignedReceiptName"]
            old_bytes=old.read_bytes()
            with patch.object(lanes,"_LANES",(self._lane("fail"),)):
                after=lanes.run_safe_isolated_development_lanes(
                    repo=ROOT,private=private,ready=READY,
                    completed_dependencies=set())
            self.assertEqual(after["status"],"INDEPENDENT_SAFE_LANES_ALL_VERIFIED")
            self.assertNotEqual(before["privateSignedReceiptName"],
                                after["privateSignedReceiptName"])
            self.assertEqual(old.read_bytes(),old_bytes)
            self.assertEqual(len(list(folder.glob("V33_*.json"))),2)

    def test_identical_restart_receipt_is_idempotent(self):
        with tempfile.TemporaryDirectory() as td:
            private,folder=self._place(td)
            with patch.object(lanes,"_LANES",(self._lane("stable"),)):
                a=lanes.run_safe_isolated_development_lanes(
                    repo=ROOT,private=private,ready=READY,
                    completed_dependencies=set())
                b=lanes.run_safe_isolated_development_lanes(
                    repo=ROOT,private=private,ready=READY,
                    completed_dependencies=set())
            self.assertEqual(a["privateSignedReceiptSha256"],
                             b["privateSignedReceiptSha256"])
            self.assertEqual(len(list(folder.glob("V33_*.json"))),1)

    def test_unpinned_source_or_untrusted_dependencies_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            private,_=self._place(td)
            for ready in ({**READY,"gitHead":"../../bad"},
                          {**READY,"publicationAuthorized":True},
                          {**READY,"proposalSha256":"whatever"}):
                with self.assertRaisesRegex(ValueError,"UNPINNED"):
                    lanes.run_safe_isolated_development_lanes(
                        repo=ROOT,private=private,ready=ready,
                        completed_dependencies=set())
            with self.assertRaisesRegex(ValueError,"UNTRUSTED_DEPENDENCY"):
                lanes.run_safe_isolated_development_lanes(
                    repo=ROOT,private=private,ready=READY,
                    completed_dependencies={"fake_success"})

    def test_dependent_readback_does_not_run_on_quarantined_science(self):
        seen=[]
        def should_not_run(*args):
            seen.append("BAD")
            raise AssertionError("DO_NOT_EXECUTE")
        with tempfile.TemporaryDirectory() as td:
            private,_=self._place(td)
            with patch.object(lanes,"_LANES",(
                    self._lane("safe"),
                    lanes.VerifiedLane("source",("v32_source_chain",),
                                       should_not_run))):
                result=lanes.run_safe_isolated_development_lanes(
                    repo=ROOT,private=private,ready=READY,
                    completed_dependencies=set())
            self.assertEqual(seen,[])
            self.assertEqual(result["independentlyVerifiedLanes"],1)

    def test_after_academic_failure_safe_others_execute_before_reraise(self):
        predecessor={"status":advance._STATUS28,"newProviderCalls":0,
                     "publicationAuthorized":False,"formalAcademicPASS":0,
                     "completeAcademicProofGatesStillOpen":90}
        observed=[]
        def fail(*args):
            observed.append("science_failed")
            raise ValueError("SOURCE_ARTIFACT_CHANGED")
        def recovery(**kwargs):
            observed.append(("other_work_continues",
                             kwargs["completed_dependencies"],
                             kwargs["blocked_operation"]))
            return {"status":"INDEPENDENT_SAFE_LANES_ADVANCED_WITH_QUARANTINE"}
        with (patch.dict(advance._TRANSITIONS,{
            advance._STATUS28:(advance._STATUS29,"visual",fail)
        },clear=True),
              patch.object(advance,"run_safe_isolated_development_lanes",
                           side_effect=recovery)):
            with self.assertRaisesRegex(ValueError,"SOURCE_ARTIFACT_CHANGED"):
                advance.advance_eligible_verified_development_stages(
                    repo=ROOT,private=ROOT,ready=READY,
                    v9={},v11={},v12={},prior_stage=predecessor,
                    run_independent_lanes=True)
        self.assertEqual(observed,[
            "science_failed",("other_work_continues",set(),
                               "source_bound_academic_successor_chain")])

    def test_complete_main_chain_requires_all_isolated_lanes(self):
        predecessor={"status":advance._STATUS28,"newProviderCalls":0,
                     "publicationAuthorized":False,"formalAcademicPASS":0,
                     "completeAcademicProofGatesStillOpen":90}
        def success(status):
            return lambda *args: {
                "status":status,"publicationAuthorized":False,
                "fullAcademicPASS":0,"completeAcademicProofGatesStillOpen":90,
                "newModelCalls":0}
        transitions={
            advance._STATUS28:(advance._STATUS29,"v29",success(advance._STATUS29)),
            advance._STATUS29:(advance._STATUS30,"v30",success(advance._STATUS30)),
            advance._STATUS30:(advance._STATUS31,"v31",success(advance._STATUS31)),
            advance._STATUS31:(advance._STATUS32,"v32",success(advance._STATUS32)),
        }
        with patch.dict(advance._TRANSITIONS,transitions,clear=True):
            for state in ("INDEPENDENT_SAFE_LANES_ADVANCED_WITH_QUARANTINE",
                          "INDEPENDENT_SAFE_LANES_ALL_VERIFIED"):
                with patch.object(advance,"run_safe_isolated_development_lanes",
                                  return_value={"status":state}):
                    result=advance.advance_eligible_verified_development_stages(
                        repo=ROOT,private=ROOT,ready=READY,
                        v9={},v11={},v12={},prior_stage=predecessor,
                        run_independent_lanes=True)
                self.assertEqual(result["stagesExecutedThisRun"],4)
                self.assertEqual(result["status"],
                    ("AUTONOMOUSLY_ADVANCED_ALL_REGISTERED_SAFE_STAGES_TO_CURRENT_BOUNDARY"
                     if state=="INDEPENDENT_SAFE_LANES_ALL_VERIFIED" else
                     "AUTONOMOUSLY_ADVANCED_ELIGIBLE_LANES_WITH_QUARANTINE"))
                self.assertEqual(result["academicPASS"],0)

    def test_real_normal_worker_requires_lane_isolation_success(self):
        script=(ROOT/"scripts"/"run_v3_yoga6_recovery_worker.py").read_text(
            encoding="utf8")
        self.assertIn("run_independent_lanes=True",script)
        self.assertIn("INDEPENDENT_SAFE_LANES_ALL_VERIFIED",script)
        self.assertIn("isolatedDevelopmentLanes",script)

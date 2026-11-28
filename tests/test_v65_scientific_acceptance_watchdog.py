"""BSA285: negative controls for silent academic stagnation despite log activity."""
from __future__ import annotations

from copy import deepcopy
import json
from unittest import TestCase
from unittest.mock import patch
from scripts import bosla_persistent_development as worker

from app_generator.runtime.v3_scientific_acceptance_watchdog import (
    observe_signed_horizon,investigate_zero_academic_gain,
)

HEAD_A="a"*40
HEAD_B="b"*40
HEAD_C="c"*40
T0="2026-11-27T08:07:00+00:00"
T5="2026-11-27T08:12:00+00:00"
T70="2026-11-27T09:17:00+00:00"


def payload(head=HEAD_A,count=15):
    return json.dumps({
        "status":"BOSLA_LONG_HORIZON_THIRD_LAW_SCIENCE_BATCH_REVERIFIED",
        "gitHead":head,"academicAcceptancesSource":
            "FIFTEEN_SOURCE_BOUND_INDEPENDENT_ORIGINAL_SERWAY_SCIENCE_TASK_RECEIPTS",
        "acceptedProofCarriedAcrossGitHead":True,
        "academicProofReceiptSha256":"f"*64,
        "academicProofTasksAccepted":count,
        "fullAcademicProofTasksStillOpen":429-count,
        "completeAcademicProofGatesStillOpen":90,
        "publicationAuthorized":False,
    },sort_keys=True)


class IndependentScienceProgressTests(TestCase):
    def test_baseline_does_not_pretend_16_or_trigger_on_logs(self):
        st={}
        report=observe_signed_horizon(st,payload(),head=HEAD_A,now=T0,cycle=1)
        self.assertEqual(report["acceptedCount"],15)
        self.assertFalse(report["advancedThisObservation"])
        self.assertFalse(investigate_zero_academic_gain(st,now=T5,cycle=1)["triggered"])
        self.assertEqual(st["scienceAcceptance"]["evidence"],
                         "INDEPENDENT_SOURCE_BOUND_SIGNED_HORIZON_EXIT_ZERO")

    def test_zero_gain_two_distinct_verified_heads_triggers_root_cause_diagnosis(self):
        st={}
        observe_signed_horizon(st,payload(),head=HEAD_A,now=T0,cycle=1)
        observe_signed_horizon(st,payload(HEAD_B),head=HEAD_B,now=T5,cycle=2)
        first=investigate_zero_academic_gain(st,now=T5,cycle=2)
        self.assertFalse(first["triggered"])
        observe_signed_horizon(st,payload(HEAD_C),head=HEAD_C,now=T5,cycle=3)
        report=investigate_zero_academic_gain(st,now=T5,cycle=3)
        self.assertTrue(report["triggered"])
        self.assertEqual(report["acceptedCount"],15)
        self.assertEqual(report["classification"],"INDEPENDENT_PROOF_PRODUCER_AND_SIGNED_ADMISSION_GAP")
        self.assertFalse(report["publicationAuthorized"])

    def test_elapsed_threshold_with_completed_cycles_catches_busy_log_without_proof(self):
        st={}
        observe_signed_horizon(st,payload(),head=HEAD_A,now=T0,cycle=1)
        report=investigate_zero_academic_gain(st,now=T70,cycle=2)
        self.assertTrue(report["triggered"])
        self.assertEqual(report["pendingCount"],414)
        st["failedTest"]="CONTRACT"
        self.assertEqual(
            investigate_zero_academic_gain(st,now=T70,cycle=2)["classification"],
            "KNOWN_RECURRENCE_REGISTRY_CONTRACT_REPAIR")

    def test_real_16_clears_alert_and_automatic_next_task_can_be_selected(self):
        st={}
        observe_signed_horizon(st,payload(),head=HEAD_A,now=T0,cycle=1)
        st["scienceStall"]={"triggered":True}
        report=observe_signed_horizon(st,payload(HEAD_B,16),head=HEAD_B,now=T70,cycle=2)
        self.assertEqual(report["acceptedCount"],16)
        self.assertEqual(report["pendingCount"],413)
        self.assertTrue(report["advancedThisObservation"])
        self.assertNotIn("scienceStall",st)
        self.assertFalse(investigate_zero_academic_gain(st,now=T70,cycle=2)["triggered"])

    def test_no_log_or_false_source_free_ci_synthetic_pass(self):
        st={}
        for content in ("", "progress heartbeat\n", payload()+"\n"+payload()):
            with self.subTest(content=content[:18]),self.assertRaises(ValueError):
                observe_signed_horizon(st,content,head=HEAD_A,now=T0,cycle=1)
        fake=json.loads(payload())
        for field,value in (
            ("academicAcceptancesSource","SOURCE_FREE_CI_PASS"),
            ("acceptedProofCarriedAcrossGitHead",False),
            ("publicationAuthorized",True),
            ("gitHead",HEAD_B),
            ("fullAcademicProofTasksStillOpen",429)):
            modified=deepcopy(fake)
            modified[field]=value
            with self.subTest(field=field),self.assertRaises(ValueError):
                observe_signed_horizon(st,json.dumps(modified),head=HEAD_A,now=T0,cycle=1)
        self.assertNotIn("scienceAcceptance",st)

    def test_signed_count_rollback_is_detected_not_treated_as_retry(self):
        st={}
        observe_signed_horizon(st,payload(),head=HEAD_A,now=T0,cycle=1)
        with self.assertRaisesRegex(ValueError,"COUNT_ROLLBACK"):
            observe_signed_horizon(st,payload(HEAD_B,14),head=HEAD_B,now=T5,cycle=2)
        self.assertEqual(st["scienceAcceptance"]["acceptedCount"],15)

    def test_repeated_same_head_does_not_inflate_no_gain_attempts(self):
        st={}
        observe_signed_horizon(st,payload(),head=HEAD_A,now=T0,cycle=1)
        for cycle in (2,3,4):
            observe_signed_horizon(st,payload(),head=HEAD_A,now=T5,cycle=cycle)
        self.assertEqual(st["scienceAcceptance"]["noGainOwnerHeads"],0)
        self.assertFalse(investigate_zero_academic_gain(st,now=T5,cycle=4)["triggered"])

    def test_normal_owner_acceptance_requires_true_independent_receipt(self):
        st={"cycle":2,"currentHead":HEAD_B}
        with (patch.object(worker,"_head",return_value=HEAD_B),
              patch.object(worker,"_branch",return_value=worker.MAIN_BRANCH),
              patch.object(worker,"_clean",return_value=True),
              patch.object(worker,"_hosted_ci",return_value="CI_SUCCESS"),
              patch.object(worker,"_log_process",return_value=0),
              patch.object(worker,"_safe_last_log",return_value=payload(HEAD_B)),
              patch.object(worker,"_update",side_effect=lambda s,status,**kw:s.update(kw)),
              patch.object(worker,"_utc",return_value=T5)):
            self.assertTrue(worker._owner_stage(st))
        self.assertEqual(st["scienceAcceptance"]["acceptedCount"],15)
        self.assertEqual(st["lastOwnerHead"],HEAD_B)

    def test_normal_owner_rejects_independent_log_without_proof(self):
        st={"cycle":2,"currentHead":HEAD_B}
        with (patch.object(worker,"_head",return_value=HEAD_B),
              patch.object(worker,"_branch",return_value=worker.MAIN_BRANCH),
              patch.object(worker,"_clean",return_value=True),
              patch.object(worker,"_hosted_ci",return_value="CI_SUCCESS"),
              patch.object(worker,"_log_process",return_value=0),
              patch.object(worker,"_safe_last_log",return_value="progress reported but no receipt"),
              patch.object(worker,"_update",side_effect=lambda s,status,**kw:s.update(kw))):
            self.assertFalse(worker._owner_stage(st))
        self.assertNotIn("scienceAcceptance",st)
        self.assertNotIn("lastOwnerHead",st)
        self.assertIn("BSA285",st["scienceVerificationError"])

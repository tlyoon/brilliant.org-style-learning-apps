"""BSA303: signed-science progress survives failed later owner steps.

These synthetic tests NEVER award scientific credit. Yoga6-only real-source
test recomputes academic acceptance from original Serway signed evidence.
"""
from __future__ import annotations

from contextlib import redirect_stdout
from hashlib import sha256
from io import StringIO
import json
import os
from pathlib import Path
from unittest import TestCase,skipUnless
from unittest.mock import patch

from app_generator.runtime import v3_incremental_signed_science_progress as progress
from app_generator.runtime.v3_persistent_academic_failure_recovery import (
    exact_owner_failure_code,
)
from scripts import auto_advance_bosla_academic_frontier as cli


class SignedScienceReliability(TestCase):
    HEAD="a"*40
    NOW="2026-11-28T01:40:00+00:00"

    def signed_result(self,n=21):
        return {"status":"BSA289_THREE_EQUAL_ENERGY_SCIENCE_TASKS_GENUINELY_REVERIFIED",
                "currentGitHead":self.HEAD,"batchProofOriginGitHead":"b"*40,
                "independentlyAcceptedAcademicTasks":n,
                "fullAcademicTasksStillOpen":429-n,
                "acceptedAcademicTaskIds":[format(i,"064x") for i in range(n)],
                "completeAcademicProofGatesStillOpen":90,
                "fullAcademicActivityPASS":0,"newProviderCalls":0,
                "publicationAuthorized":False}

    def test_incremental_signed_stage_persists_even_if_next_task_fails(self):
        result=progress.validate_independent_stage(
            result=self.signed_result(),head=self.HEAD,expected_count=21)
        state={"scienceAcceptance":{"acceptedCount":15,
                "lastIncreaseAt":"2026-11-27T09:00:00+00:00"}}
        accepted=progress.apply_independent_progress(
            state=state,verified=result,head=self.HEAD,now=self.NOW,cycle=75)
        self.assertEqual(accepted["acceptedCount"],21)
        self.assertEqual(accepted["pendingCount"],408)
        self.assertEqual(state["scientificProgress"]["accepted"],21)
        self.assertFalse(state["scientificProgress"]["publicationAuthorized"])
        self.assertTrue(accepted["advancedThisObservation"])
        # Later A22 failure must not rewrite the signed A21 milestone.
        self.assertEqual(state["scienceAcceptance"]["acceptedCount"],21)

    def test_replay_no_gain_and_rollback_rejected(self):
        signed=progress.validate_independent_stage(
            result=self.signed_result(),head=self.HEAD,expected_count=21)
        state={}
        first=progress.apply_independent_progress(
            state=state,verified=signed,head=self.HEAD,now=self.NOW,cycle=74)
        second=progress.apply_independent_progress(
            state=state,verified=signed,head=self.HEAD,now=self.NOW,cycle=75)
        self.assertEqual(first["acceptedCount"],21)
        self.assertFalse(second["advancedThisObservation"])
        self.assertEqual(second["lastIncreaseAt"],first["lastIncreaseAt"])
        low={**signed,"acceptedCount":18,"pendingCount":411}
        with self.assertRaisesRegex(ValueError,"ROLLBACK"):
            progress.apply_independent_progress(
                state=state,verified=low,head=self.HEAD,now=self.NOW,cycle=76)
        self.assertEqual(state["scientificProgress"]["accepted"],21)

    def test_forged_ids_count_wrong_head_missing_source_and_false_pass_rejected(self):
        variants=(
            {"acceptedAcademicTaskIds":["0"*64]*21},
            {"fullAcademicTasksStillOpen":407},
            {"currentGitHead":"c"*40},
            {"fullAcademicActivityPASS":1},
            {"publicationAuthorized":True},
            {"newProviderCalls":1},
            {"status":"UNVERIFIED_SOURCE_FREE_CI_PASS"},
        )
        for edit in variants:
            with self.subTest(edit=edit):
                with self.assertRaisesRegex(ValueError,"NOT_INDEPENDENT"):
                    progress.validate_independent_stage(
                        result={**self.signed_result(),**edit},
                        head=self.HEAD,expected_count=21)

    def test_precise_keyerror_field_and_unsafe_material_redacted(self):
        with patch.object(cli,"advance_all_eligible_academic_actions",
                          side_effect=KeyError("fullAcademicTasksStillOpen")):
            buf=StringIO()
            with redirect_stdout(buf):
                rc=cli.main(["--max-steps","1"])
            self.assertEqual(rc,2)
            data=json.loads(buf.getvalue())
            self.assertEqual(data["errorClass"],"KeyError")
            self.assertEqual(data["errorCode"],
                             "BSA303_KEY_ERROR_FULLACADEMICTASKSSTILLOPEN")
            self.assertEqual(
                exact_owner_failure_code(buf.getvalue()),
                data["errorCode"])
            self.assertFalse(data["publicationAuthorized"])
        with patch.object(cli,"advance_all_eligible_academic_actions",
                          side_effect=KeyError("student private text!")):
            buf=StringIO()
            with redirect_stdout(buf):
                cli.main([])
            self.assertEqual(json.loads(buf.getvalue())["errorCode"],
                             "BSA303_KEY_ERROR_REDACTED")
            self.assertNotIn("student private text",buf.getvalue())

    @skipUnless(os.name=="nt" and
                os.environ.get("COMPUTERNAME","").upper()=="YOGA6",
                "Private original textbook only on owner Yoga6")
    def test_real_signed_original_serway_a21_reopened_no_new_receipt(self):
        private=Path(os.environ["LOCALAPPDATA"])/"Microvid"/"BoslaV3ReviewYoga6"
        from app_generator.runtime.v3_long_horizon_development import (
            read_long_horizon_development,
        )
        original=read_long_horizon_development(private)
        head=original["gitHead"]
        state={"scienceAcceptance":{"acceptedCount":15,
               "lastIncreaseAt":"2026-11-27T09:17:23+00:00"}}
        result=progress.reconcile_independent_science(
            private=private,state=state,head=head,now=self.NOW,cycle=75)
        self.assertGreaterEqual(result["acceptedCount"],21)
        self.assertEqual(state["scienceAcceptance"]["lastVerifiedHead"],head)
        self.assertFalse(result["publicationAuthorized"])


class LongHorizonFailureEscalation(TestCase):
    def test_second_same_exact_failure_changes_diagnostic_strategy(self):
        from tempfile import TemporaryDirectory
        from scripts import bosla_persistent_development as owner
        event=json.dumps({
            "status":"BSA276_ELIGIBLE_ACADEMIC_STEP_UNVERIFIED",
            "errorClass":"KeyError",
            "errorCode":"BSA303_KEY_ERROR_MISSINGFIELD",
            "academicAcceptanceAdvanced":False,
            "publicationAuthorized":False})
        with TemporaryDirectory() as td:
            private=Path(td)
            logs=private/"logs"
            logs.mkdir()
            path=logs/"OWNER_REAL_SOURCE_ADMISSION.log"
            path.write_text(event+"\n",encoding="utf8")
            state={"schemaVersion":1,"cycle":74,
                   "currentLog":str(path)}
            with (patch.object(owner,"PRIVATE",private),
                  patch.object(owner,"STATE",private/"state.json"),
                  patch.object(owner,"JOURNAL",private/"events.jsonl")):
                first=owner._failed_owner_decision(
                    state,head="a"*40,exit_code=2)
                second=owner._failed_owner_decision(
                    state,head="b"*40,exit_code=2)
            self.assertEqual(first["rootCauseAttempts"],1)
            self.assertEqual(second["rootCauseAttempts"],2)
            self.assertEqual(second["repairStrategy"],
                             "DIFFERENTIAL_REAL_SOURCE_ROOT_CAUSE_DIAGNOSIS")
            self.assertFalse(second["academicPASS"])
            self.assertEqual(state["recoveryProgress"]["attempts"],2)
            self.assertEqual(state["recoveryProgress"]["safeFailureCode"],
                             "BSA303_KEY_ERROR_MISSINGFIELD")


class EqualEnergyReceiptInterfaceRegression(TestCase):
    @skipUnless(os.name=="nt" and
                os.environ.get("COMPUTERNAME","").upper()=="YOGA6",
                "Exact source-bound A21 readback only on owner Yoga6")
    def test_true_A21_signed_receipt_is_exported_under_A22_required_key(self):
        from app_generator.runtime.v3_isolated_pair_academic_batch_admission import (
            _prior_twenty_one,
        )
        private=Path(os.environ["LOCALAPPDATA"])/"Microvid"/"BoslaV3ReviewYoga6"
        verified=_prior_twenty_one(private)
        new_hash=verified["equalEnergyBatchReceiptSha256"]
        self.assertEqual(len(new_hash),64)
        self.assertTrue(all(c in "0123456789abcdef" for c in new_hash))
        self.assertEqual(new_hash,verified["equalSpeedBatchReceiptSha256"])
        self.assertEqual(verified["independentlyAcceptedAcademicTasks"],21)
        self.assertEqual(verified["fullAcademicTasksStillOpen"],408)

"""BSA279 fault-injection/restart/persistence tests for Bosla Yoga6 daemon.

CI tests do NOT create Windows scheduled tasks or fake original Serway
academic PASS. The actual owner runner and scheduler must be acceptance-
tested independently on Yoga6. All default test state is private temp.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
from unittest import TestCase,skipUnless
from unittest.mock import patch

from scripts import bosla_persistent_development as worker


class PersistentBoslaTests(TestCase):
    def test_scheduler_is_new_name_and_never_retired_legacy(self):
        installer=(worker.ROOT/"scripts"/
                   "install_bosla_persistent_development.ps1").read_text(
                       encoding="utf8")
        self.assertIn("BoslaPersistentDevelopment-Yoga6",installer)
        self.assertIn("New-ScheduledTaskTrigger -AtLogOn",installer)
        self.assertIn("New-ScheduledTaskTrigger -Once",installer)
        self.assertIn("-RepetitionInterval (New-TimeSpan -Minutes 15)",installer)
        self.assertIn("New-TimeSpan -Minutes 15",installer)
        self.assertIn("MultipleInstances IgnoreNew",installer)
        self.assertIn("BoslaYoga6V3Recovery",installer)
        self.assertIn("RETIRED_LEGACY_TASK_PRESENT",installer)
        self.assertNotIn("Register-ScheduledTask -TaskName $legacy",installer)

    def test_approved_code_scope_excludes_secrets_and_ci_bypass(self):
        with patch.object(worker,"_ok",return_value=(
            "tests/test_example.py\n"
            "app_generator/validation/new_source_proof.py\n"
            "docs/recurrence_registry.json")):
            self.assertTrue(worker._approved_diff("a"*40,"b"*40))
        for forbidden in (
            ".github/workflows/ci.yml",
            "scripts/.env",
            "data/source.pdf",
            "docs/secret_credentials.md",
            "README.txt",
            "C:/Users/User/source.pdf",
        ):
            with self.subTest(forbidden=forbidden):
                with patch.object(worker,"_ok",return_value=forbidden):
                    self.assertFalse(worker._approved_diff("a"*40,"b"*40))

    def test_hosted_ci_requires_exact_sha_and_every_success(self):
        wanted="a"*40
        other="b"*40
        results=[
            {"headSha":other,"status":"completed","conclusion":"success",
             "databaseId":1},
            {"headSha":wanted,"status":"completed","conclusion":"success",
             "databaseId":2},
            {"headSha":wanted,"status":"completed","conclusion":"success",
             "databaseId":3},
        ]
        p=subprocess.CompletedProcess(["gh"],0,json.dumps(results),"")
        with patch.object(worker,"_run",return_value=p):
            self.assertEqual(worker._hosted_ci(wanted,"feature",min_runs=2),
                             "CI_SUCCESS")
            self.assertEqual(worker._hosted_ci(other,"feature",min_runs=2),
                             "CI_AWAITING")
        results[2]["conclusion"]="failure"
        p=subprocess.CompletedProcess(["gh"],0,json.dumps(results),"")
        with patch.object(worker,"_run",return_value=p):
            self.assertEqual(worker._hosted_ci(wanted,"feature",min_runs=2),
                             "CI_FAILED")

    def test_unreadable_or_offline_hosted_ci_fails_closed(self):
        for rc,out in ((2,""),(0,"not-json")):
            with patch.object(worker,"_run",return_value=
                              subprocess.CompletedProcess(["gh"],rc,out,"")):
                self.assertNotEqual(worker._hosted_ci("a"*40,"f",min_runs=1),
                                    "CI_SUCCESS")

    def test_atomic_restart_state_is_durable_not_memory_only(self):
        with TemporaryDirectory() as t:
            private=Path(t)
            with (patch.object(worker,"PRIVATE",private),
                  patch.object(worker,"STATE",private/"state.json"),
                  patch.object(worker,"JOURNAL",private/"events.jsonl")):
                s=worker._read_state()
                worker._update(s,"BSA279_GENUINE_TEST_RECORD",
                               pendingBranch="feature/recover")
                reread=worker._read_state()
                self.assertEqual(reread["pendingBranch"],"feature/recover")
                self.assertEqual(reread["status"],
                                 "BSA279_GENUINE_TEST_RECORD")
                self.assertFalse((private/"state.json.new").exists())

    def test_tampered_state_schema_fails_without_silent_reset(self):
        with TemporaryDirectory() as t:
            file=Path(t)/"state.json"
            file.write_text('{"schemaVersion":100}',encoding="utf8")
            with patch.object(worker,"STATE",file):
                with self.assertRaisesRegex(ValueError,"SCHEMA_UNTRUSTED"):
                    worker._read_state()

    @skipUnless(sys.platform=="win32","Windows OS byte-lock only")
    def test_singleflight_denies_overlap_and_releases_after_exit(self):
        with TemporaryDirectory() as t:
            private=Path(t)
            with (patch.object(worker,"PRIVATE",private),
                  patch.object(worker,"LOCK",private/"active.lock")):
                with worker.SingleFlight():
                    with self.assertRaisesRegex(ValueError,
                                                "ANOTHER_PERSISTENT_WORKER"):
                        with worker.SingleFlight():
                            pass
                with worker.SingleFlight():
                    pass

    def test_cycle_automatically_runs_next_eligible_developer_stage(self):
        with TemporaryDirectory() as t:
            private=Path(t)
            with (patch.object(worker,"PRIVATE",private),
                  patch.object(worker,"STATE",private/"state.json"),
                  patch.object(worker,"JOURNAL",private/"events.jsonl"),
                  patch.dict(os.environ,{"COMPUTERNAME":"YOGA6"}),
                  patch.object(worker,"SingleFlight"),
                  patch.object(worker,"_head",return_value="a"*40),
                  patch.object(worker,"_branch",return_value=
                               worker.MAIN_BRANCH),
                  patch.object(worker,"_promote_known",return_value=False)
                  as promotion,
                  patch.object(worker,"_owner_stage",return_value=True)
                  as owner,
                  patch.object(worker,"_codex_stage",return_value=True)
                  as codegen):
                    result=worker.cycle()
                    self.assertEqual(result["cycle"],1)
                    promotion.assert_called_once()
                    owner.assert_called_once()
                    codegen.assert_called_once()

    def test_no_model_call_after_unverified_owner_or_new_ci_promotion(self):
        for promoted,owner_ok in ((True,True),(False,False)):
            with self.subTest(promoted=promoted,owner=owner_ok):
                with TemporaryDirectory() as t:
                    private=Path(t)
                    with (patch.object(worker,"PRIVATE",private),
                          patch.object(worker,"STATE",private/"state.json"),
                          patch.object(worker,"JOURNAL",private/"events.jsonl"),
                          patch.dict(os.environ,{"COMPUTERNAME":"YOGA6"}),
                          patch.object(worker,"SingleFlight"),
                          patch.object(worker,"_head",return_value="b"*40),
                          patch.object(worker,"_branch",
                                       return_value=worker.MAIN_BRANCH),
                          patch.object(worker,"_promote_known",
                                       return_value=promoted),
                          patch.object(worker,"_owner_stage",
                                       return_value=owner_ok),
                          patch.object(worker,"_codex_stage") as codex):
                        worker.cycle()
                        codex.assert_not_called()

    def test_daily_model_invocations_are_bounded_without_bypass(self):
        state={"codexDay":"","codexCount":0}
        self.assertTrue(worker._daily_budget(state))
        state["codexCount"]=worker.MAX_CODEX_PER_DAY
        self.assertFalse(worker._daily_budget(state))

    def test_real_bounded_child_writes_local_private_log(self):
        with TemporaryDirectory() as t:
            private=Path(t)
            state={"schemaVersion":1,"cycle":2}
            with (patch.object(worker,"PRIVATE",private),
                  patch.object(worker,"STATE",private/"state.json"),
                  patch.object(worker,"JOURNAL",private/"events.jsonl")):
                rc=worker._log_process(
                    state,"SMOKE_REAL_CHILD",
                    [sys.executable,"-c","print('BSA279_PROCESSED')"],
                    cwd=Path(t),timeout=15)
                self.assertEqual(rc,0)
                self.assertTrue(list((private/"logs").glob("SMOKE_REAL_CHILD*")))
                self.assertIn("BSA279_PROCESSED",
                              list((private/"logs").glob(
                                  "SMOKE_REAL_CHILD*"))[0].read_text())

    def test_codex_task_must_create_science_code_not_merely_report(self):
        prompt=worker._codex_prompt()
        for required in (
            "SUBSTANTIVE CODE DEVELOPMENT",
            "actual source-bound test",
            "fault-injection",
            "executable recovery-registry integration",
            "No public PR merge",
            "Do not initiate paid Gemini",
            "no-op scheduler",
        ):
            self.assertIn(required,prompt)

    def test_bad_machine_prevents_any_singleflight_academic_work(self):
        with patch.dict(os.environ,{"COMPUTERNAME":"DELL115"}):
            with self.assertRaisesRegex(ValueError,"YOGA6_ONLY"):
                worker.cycle()

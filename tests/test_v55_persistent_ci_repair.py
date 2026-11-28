"""BSA279: failure-injection for same-branch automatic CI repair and checkpoint resume."""
from __future__ import annotations

import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch

from scripts import bosla_persistent_development as worker


class ScheduledModelRepairTests(TestCase):
    def _pending_cycle(self,ci:str,codegen:bool=True):
        with TemporaryDirectory() as t:
            private=Path(t)
            dev=private/"dev"
            dev.mkdir()
            (private/"state.json").write_text(json.dumps({
                "schemaVersion":1,"cycle":1,"pendingBranch":"feature/example",
                "devBranch":"feature/example","devWorktree":str(dev),
                "integratedBranches":[],"codexCount":1,
                "codexDay":"2026-11-27",
            }),encoding="utf8")
            with (patch.object(worker,"PRIVATE",private),
                  patch.object(worker,"STATE",private/"state.json"),
                  patch.object(worker,"JOURNAL",private/"events.jsonl"),
                  patch.dict(os.environ,{"COMPUTERNAME":"YOGA6"}),
                  patch.object(worker,"SingleFlight"),
                  patch.object(worker,"_head",return_value="a"*40),
                  patch.object(worker,"_branch",
                               return_value=worker.MAIN_BRANCH),
                  patch.object(worker,"_promote_known",return_value=False),
                  patch.object(worker,"_hosted_ci",return_value=ci),
                  patch.object(worker,"_owner_stage") as owner,
                  patch.object(worker,"_codex_stage") as codex):
                state=worker.cycle(codegen=codegen)
                owner.assert_not_called()
                return state,codex.call_args

    def test_failed_hosted_ci_dispatches_same_worktree_repair(self):
        state,called=self._pending_cycle("CI_FAILED")
        self.assertEqual(state["status"],
                         "BSA279_FAILED_CI_TARGETED_REPAIR_DISPATCHED")
        self.assertIsNotNone(called)
        self.assertEqual(called.kwargs,{"repair":True})

    def test_pending_ci_does_not_replay_or_fake_academic_acceptance(self):
        for ci in ("CI_AWAITING","GH_UNAVAILABLE","CI_UNREADABLE"):
            with self.subTest(ci=ci):
                state,called=self._pending_cycle(ci)
                self.assertIsNone(called)
                self.assertIn(ci,state["status"])
                self.assertNotIn("lastOwnerHead",state)

    def test_ci_failure_does_not_start_codex_when_disabled(self):
        state,called=self._pending_cycle("CI_FAILED",codegen=False)
        self.assertIsNone(called)

    def test_local_test_failure_reuses_its_actual_worktree(self):
        with TemporaryDirectory() as t:
            private=Path(t)
            dev=private/"dev"
            dev.mkdir()
            state={"schemaVersion":1,"cycle":3,
                   "devBranch":"feature/resume-me",
                   "devWorktree":str(dev),
                   "codexRepairRequired":True,
                   "codexCount":0}
            def branch(where=worker.ROOT):
                return ("feature/resume-me" if Path(where)==dev
                        else worker.MAIN_BRANCH)
            with (patch.object(worker,"PRIVATE",private),
                  patch.object(worker,"STATE",private/"state.json"),
                  patch.object(worker,"JOURNAL",private/"events.jsonl"),
                  patch.object(worker,"_branch",side_effect=branch),
                  patch.object(worker,"_head",return_value="a"*40),
                  patch.object(worker,"_clean",return_value=True),
                  patch.object(worker.shutil,"which",return_value="codex.cmd"),
                  patch.object(worker,"_dev_worktree") as new_branch,
                  patch.object(worker,"_log_process",return_value=0) as call,
                  patch.object(worker,"build_isolated_coding_snapshot",
                               return_value={"AGENTS.md":"hash"}),
                  patch.object(worker,"apply_isolated_patch",return_value=[]),
                  patch.object(worker,"_ok",return_value="")):
                self.assertFalse(worker._codex_stage(state))
                new_branch.assert_not_called()
                self.assertIn("CODEX_TARGETED_REPAIR",call.call_args.args[1])
                self.assertEqual(state["devWorktree"],str(dev))

    def test_missing_repair_worktree_cannot_generate_fake_success(self):
        with TemporaryDirectory() as t:
            private=Path(t)
            state={"schemaVersion":1,"cycle":4,
                   "pendingBranch":"feature/absent",
                   "devBranch":"feature/absent",
                   "devWorktree":str(private/"not-present")}
            with (patch.object(worker,"PRIVATE",private),
                  patch.object(worker,"STATE",private/"state.json"),
                  patch.object(worker,"JOURNAL",private/"events.jsonl"),
                  patch.object(worker,"_clean",return_value=True),
                  patch.object(worker,"_branch",
                               return_value=worker.MAIN_BRANCH),
                  patch.object(worker.shutil,"which",
                               return_value="codex.cmd"),
                  patch.object(worker,"_dev_worktree") as new_branch):
                self.assertFalse(worker._codex_stage(state,repair=True))
                self.assertEqual(state["status"],
                                 "BSA279_REPAIR_WORKTREE_NOT_AUTHENTIC")
                new_branch.assert_not_called()

"""BSA311 durable CI -> owner -> science continuation, no fabricated PASS."""
from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
from tempfile import TemporaryDirectory
import os
from unittest import TestCase,skipUnless
from unittest.mock import patch

from scripts import bosla_persistent_development as owner
from app_generator.runtime.v3_long_horizon_ci_continuation import (
    ci_gate,decide_next,
)

HEAD="a"*40
PATCH="b"*40
NEW_OWNER="c"*40

@contextmanager
def _flight():
    yield

class BoslaLongHorizonCIContinuation(TestCase):
    def test_explicit_dispatch_policy_never_mistakes_ci_for_science_pass(self):
        self.assertEqual(decide_next(
            "BSA279_NEW_SOURCE_CODE_COMMITTED_CI_DISPATCHED",
            pending_branch="feature/bosla-auto-valid",
            recovery_attempts=0),
            "BSA311_WAIT_EXACT_GIT_COMMIT_CI")
        self.assertEqual(decide_next(
            "BSA279_CODEX_TESTS_FAIL_KEEP_PATCH",
            pending_branch=None,recovery_attempts=1),
            "BSA311_DISPATCH_EXISTING_TARGETED_RECOVERY")
        self.assertEqual(decide_next(
            "BSA279_CODEX_TESTS_FAIL_KEEP_PATCH",
            pending_branch=None,recovery_attempts=2),
            "BSA311_STOP_REPEATED_UNVERIFIED_REPAIR")
        self.assertEqual(decide_next(
            "BSA280_ORIGINAL_SOURCE_TRUST_FAILURE",
            pending_branch=None,recovery_attempts=0),
            "BSA311_STOP_UNRESOLVED_OR_SAFETY_BOUNDARY")

    def test_pending_gate_must_reference_existing_worktree_and_exact_head(self):
        with TemporaryDirectory() as td:
            data={"pendingBranch":"feature/bosla-auto-20261128-135555",
                  "devWorktree":td}
            self.assertEqual(ci_gate(data,main_branch=owner.MAIN_BRANCH),
                             (td,data["pendingBranch"],1))
        with self.assertRaisesRegex(ValueError,"UNTRUSTED_CANDIDATE"):
            ci_gate({"pendingBranch":"feature/bosla-auto-safe",
                     "devWorktree":"C:/missing-do-not-fabricate"},
                    main_branch=owner.MAIN_BRANCH)
        self.assertEqual(ci_gate({
            "status":"BSA279_NEW_CODE_PROMOTED_WAIT_HOSTED_CI",
            "currentHead":HEAD},main_branch=owner.MAIN_BRANCH),
                         (HEAD,owner.MAIN_BRANCH,2))

    def test_continues_code_ci_owner_ci_without_second_scheduler_tick(self):
        with TemporaryDirectory() as td:
            state={"schemaVersion":1,"cycle":84,
                   "currentHead":HEAD,
                   "pendingBranch":"feature/bosla-auto-20261128-135555",
                   "devWorktree":td,
                   "status":"BSA279_NEW_SOURCE_CODE_COMMITTED_CI_DISPATCHED",
                   "scienceAcceptance":{"acceptedCount":27}}
            elapsed=[0.]
            def pause(seconds):
                elapsed[0]+=seconds
            def head(repo=owner.ROOT):
                return PATCH if Path(repo)==Path(td) else state["currentHead"]
            def branch(repo=owner.ROOT):
                return (state["pendingBranch"] if Path(repo)==Path(td)
                        else owner.MAIN_BRANCH)
            answers=iter(["CI_AWAITING","CI_SUCCESS",
                          "CI_AWAITING","CI_SUCCESS"])
            seen=[]
            def ci(head,branch,*,min_runs):
                seen.append((head,branch,min_runs))
                return next(answers)
            called=[]
            def step(*,codegen):
                called.append(codegen)
                if len(called)==1:
                    state.update(status="BSA279_NEW_CODE_PROMOTED_WAIT_HOSTED_CI",
                                 pendingBranch=None,currentHead=NEW_OWNER)
                else:
                    state["status"]="BSA280_NEXT_REAL_SOURCE_BLOCKER"
                return dict(state)
            saved=[]
            with (patch.dict(os.environ,{"COMPUTERNAME":"YOGA6"}),
                  patch.object(owner,"LongHorizonFlight",side_effect=_flight),
                  patch.object(owner,"_read_state",return_value=state),
                  patch.object(owner,"_head",side_effect=head),
                  patch.object(owner,"_branch",side_effect=branch),
                  patch.object(owner,"_clean",return_value=True),
                  patch.object(owner,"_atomic_json",
                               side_effect=lambda p,v:saved.append(dict(v)))):
                result=owner.run_long_horizon(
                    clock=lambda:elapsed[0],pause=pause,step=step,
                    probe=ci,max_seconds=1200,max_actions=6,poll_seconds=30)
            self.assertEqual(called,[True,True])
            self.assertEqual(seen,[
                (PATCH,"feature/bosla-auto-20261128-135555",1),
                (PATCH,"feature/bosla-auto-20261128-135555",1),
                (NEW_OWNER,owner.MAIN_BRANCH,2),
                (NEW_OWNER,owner.MAIN_BRANCH,2),
            ])
            self.assertEqual(result["developmentActionsAttempted"],2)
            self.assertEqual(result["ciReadinessPolls"],4)
            self.assertEqual(result["independentlyAcceptedAcademicTasks"],27)
            self.assertFalse(result["academicAcceptanceGranted"])
            self.assertEqual(saved[0]["status"],
                             "BSA311_WAIT_EXACT_GIT_COMMIT_CI")
            self.assertEqual(result["status"],
                             "BSA311_STOP_UNRESOLVED_OR_SAFETY_BOUNDARY")

    def test_no_model_or_new_owner_action_during_unconfirmed_ci(self):
        with TemporaryDirectory() as td:
            state={"schemaVersion":1,"cycle":84,"currentHead":HEAD,
                   "pendingBranch":"feature/bosla-auto-20261128-135555",
                   "devWorktree":td,
                   "status":"BSA279_NEW_SOURCE_CODE_COMMITTED_CI_DISPATCHED",
                   "scienceAcceptance":{"acceptedCount":27}}
            elapsed=[0.]
            calls=[]
            with (patch.dict(os.environ,{"COMPUTERNAME":"YOGA6"}),
                  patch.object(owner,"LongHorizonFlight",side_effect=_flight),
                  patch.object(owner,"_read_state",return_value=state),
                  patch.object(owner,"_head",return_value=PATCH),
                  patch.object(owner,"_branch",return_value=state[
                      "pendingBranch"]),
                  patch.object(owner,"_clean",return_value=True),
                  patch.object(owner,"_atomic_json")):
                result=owner.run_long_horizon(
                    clock=lambda:elapsed[0],
                    pause=lambda n:elapsed.__setitem__(0,elapsed[0]+n),
                    step=lambda **k:calls.append(k),
                    probe=lambda *a,**k:"CI_AWAITING",
                    max_seconds=95,max_actions=4,poll_seconds=30)
            self.assertEqual(calls,[])
            self.assertEqual(result["status"],
              "BSA311_BOUNDED_HORIZON_CHECKPOINTED_FOR_NEXT_TRIGGER")
            self.assertEqual(result["independentlyAcceptedAcademicTasks"],27)
            self.assertGreaterEqual(result["ciReadinessPolls"],3)

    def test_failing_github_service_has_bounded_backoff_no_unverified_promotion(self):
        with TemporaryDirectory() as td:
            state={"schemaVersion":1,"cycle":84,"currentHead":HEAD,
                   "pendingBranch":"feature/bosla-auto-20261128-135555",
                   "devWorktree":td,
                   "status":"BSA279_NEW_SOURCE_CODE_COMMITTED_CI_DISPATCHED",
                   "scienceAcceptance":{"acceptedCount":27}}
            elapsed=[0.]
            with (patch.dict(os.environ,{"COMPUTERNAME":"YOGA6"}),
                  patch.object(owner,"LongHorizonFlight",side_effect=_flight),
                  patch.object(owner,"_read_state",return_value=state),
                  patch.object(owner,"_head",return_value=PATCH),
                  patch.object(owner,"_branch",
                               return_value=state["pendingBranch"]),
                  patch.object(owner,"_clean",return_value=True),
                  patch.object(owner,"_atomic_json")):
                result=owner.run_long_horizon(
                    clock=lambda:elapsed[0],
                    pause=lambda n:elapsed.__setitem__(0,elapsed[0]+n),
                    step=lambda **k:self.fail("unverified CI dispatched owner"),
                    probe=lambda *a,**k:"GH_UNAVAILABLE",
                    max_seconds=600,max_actions=4,poll_seconds=30)
            self.assertEqual(result["status"],
                             "BSA311_CI_UNAVAILABLE_SAFETY_BACKOFF")
            self.assertEqual(result["developmentActionsAttempted"],0)

    def test_real_scheduled_entry_uses_long_horizon_and_keeps_backup_triggers(self):
        installer=(owner.ROOT/"scripts"/
                   "install_bosla_persistent_development.ps1").read_text(
                       encoding="utf8")
        self.assertIn(
            "-Argument '-B -m scripts.bosla_persistent_development --long-horizon'",
            installer)
        self.assertIn("New-ScheduledTaskTrigger -AtLogOn",installer)
        self.assertIn("-RepetitionInterval (New-TimeSpan -Minutes 15)",installer)
        self.assertIn("-MultipleInstances IgnoreNew",installer)
        self.assertIn("RETIRED_LEGACY_TASK_PRESENT",installer)
        self.assertNotIn("Register-ScheduledTask -TaskName $legacy",installer)

    @skipUnless(os.name=="nt","Win32 byte-range lock on Yoga6 only")
    def test_horizon_flight_and_per_cycle_locks_are_distinct_and_restart_safe(self):
        with TemporaryDirectory() as td:
            h=Path(td)/"long.lock"
            c=Path(td)/"cycle.lock"
            with (patch.object(owner,"PRIVATE",Path(td)),
                  patch.object(owner,"HORIZON_LOCK",h),
                  patch.object(owner,"LOCK",c)):
                with owner.LongHorizonFlight():
                    with owner.SingleFlight():
                        self.assertTrue(h.is_file())
                        self.assertTrue(c.is_file())
                        with self.assertRaisesRegex(ValueError,
                                    "ANOTHER_PERSISTENT_WORKER"):
                            with owner.LongHorizonFlight():
                                pass
                with owner.LongHorizonFlight():
                    pass

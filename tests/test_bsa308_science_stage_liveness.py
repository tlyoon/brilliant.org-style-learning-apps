"""BSA308: stage-level evidence telemetry, CPU/stall fault injections.

No CPU reading, phase marker or synthetic log is academic acceptance.
The one real Windows test exercises OS process-tree CPU without touching
the live Yoga6 textbook worker.
"""
from __future__ import annotations

from contextlib import redirect_stderr
from io import StringIO
import os
from pathlib import Path
import re
import subprocess
import sys
import time
from tempfile import TemporaryDirectory
from unittest import TestCase,skipUnless
from unittest.mock import MagicMock,patch

from app_generator.runtime.v3_owner_science_stage_liveness import (
    cpu_time_gain,liveness_decision,stage_log_observation,
    windows_owner_tree_cpu,
)
from app_generator.runtime.v3_autonomous_academic_advancement import (
    _SignedStageTelemetry,
)
from scripts import bosla_persistent_development as owner

HEAD="a"*40

def update(state,label,**kw):
    state.update(kw)
    state["status"]=label


class BSA308SignedStageAndProcessLiveness(TestCase):
    def test_well_formed_same_head_stage_markers_are_progress_only(self):
        with TemporaryDirectory() as td:
            log=Path(td)/"source.log"
            log.write_text(
                "BSA283_VERIFIABLE_ACADEMIC_STEP_ENTER 3/14 head="+HEAD[:12]+"\n"
                "BSA308_SIGNED_STAGE_STEP_COMPLETED 3/14 head="+HEAD[:12]+
                " action=SIGNED_AND_INDEPENDENTLY_READ_A25_A27_SCIENCE_TASKS\n"
                "BSA283_VERIFIABLE_ACADEMIC_STEP_ENTER 4/14 head="+HEAD[:12]+"\n",
                encoding="ascii")
            result=stage_log_observation(log,head=HEAD)
            self.assertEqual(result["stageEntered"],4)
            self.assertEqual(result["stageCompleted"],3)
            self.assertEqual(result["lastCompletedAction"],
                             "SIGNED_AND_INDEPENDENTLY_READ_A25_A27_SCIENCE_TASKS")
            self.assertNotIn("academicPASS",result)
            self.assertNotIn("acceptedCount",result)
            fake=stage_log_observation(log,head="b"*40)
            self.assertEqual(fake["stageEntered"],0)
            self.assertEqual(fake["stageCompleted"],0)

    def test_stage_journal_emits_evidence_separate_from_academic_acceptance(self):
        log=StringIO()
        journal=_SignedStageTelemetry(HEAD,14)
        journal.current_step=4
        with redirect_stderr(log):
            journal.append("SIGNED_AND_INDEPENDENTLY_READ_A25_A27_SCIENCE_TASKS")
        self.assertEqual(len(journal),1)
        self.assertIn("BSA308_SIGNED_STAGE_STEP_COMPLETED 4/14",log.getvalue())
        self.assertNotIn("academicPASS",log.getvalue())
        self.assertNotIn("publicationAuthorized",log.getvalue())

    def test_owner_cpu_time_must_match_pid_and_creation_time(self):
        before={"100:90":10., "200:21":3.}
        after={"100:90":11.3,"200:22":0.5}
        self.assertAlmostEqual(cpu_time_gain(before,after),1.8,places=5)
        self.assertEqual(cpu_time_gain(after,before),3.)
        self.assertEqual(cpu_time_gain(None,after),0.)

    def test_quiet_cpu_active_is_not_treated_as_deadlock(self):
        self.assertEqual(liveness_decision(
            elapsed=1500,idle_log=1400,idle_cpu=10,hard_cap=3600,
            idle_cap=1200,cpu_available=True,stage_started=3,
            last_completed=2),"BSA308_COMPUTATION_ACTIVE_NO_NEW_SIGNED_PROOF")
        self.assertEqual(liveness_decision(
            elapsed=1500,idle_log=1400,idle_cpu=1400,hard_cap=3600,
            idle_cap=1200,cpu_available=True,stage_started=3,
            last_completed=2),"BSA308_QUIET_SOURCE_WORKER_STALL")
        self.assertEqual(liveness_decision(
            elapsed=1500,idle_log=1400,idle_cpu=10,hard_cap=3600,
            idle_cap=1200,cpu_available=False,stage_started=3,
            last_completed=2),"BSA308_QUIET_SOURCE_WORKER_STALL")

    def test_cpu_loop_never_bypasses_total_execution_deadline(self):
        self.assertEqual(liveness_decision(
            elapsed=3601,idle_log=1400,idle_cpu=0,hard_cap=3600,
            idle_cap=1200,cpu_available=True,stage_started=7,
            last_completed=6),"BSA308_HARD_OWNER_RUNTIME_CAP")

    def test_log_silent_cpu_busy_process_continues_without_science_pass(self):
        with TemporaryDirectory() as td:
            process=MagicMock()
            process.pid=9137
            process.poll.side_effect=[None,0]
            process.wait.return_value=0
            process.returncode=0
            st={"currentHead":HEAD,"scienceAcceptance":{"acceptedCount":24}}
            with (patch.object(owner,"PRIVATE",Path(td)),
                  patch.object(owner.subprocess,"Popen",return_value=process),
                  patch.object(owner,"_update",side_effect=update),
                  patch.object(owner,"windows_owner_tree_cpu",
                               side_effect=[{"9137:1":0.},
                                            {"9137:1":7.}]),
                  patch.object(owner,"windows_kill_tree") as kill,
                  patch.object(owner.time,"monotonic",side_effect=[0.,20.,21.]),
                  patch.object(owner.time,"sleep")):
                result=owner._log_process(st,"OWNER_REAL_SOURCE_ADMISSION",
                    ["python","-u","-m","safe"],cwd=Path(td),
                    timeout=3600,idle_timeout=15)
            self.assertEqual(result,0)
            kill.assert_not_called()
            self.assertEqual(st["scienceAcceptance"]["acceptedCount"],24)
            self.assertEqual(st["scienceExecution"]["lastStageCompleted"],0)
            self.assertGreater(st["scienceExecution"][
                "ownedProcessTreeCpuSecondsObserved"],0)
            self.assertFalse(st["scienceExecution"]["cpuUsageIsAcademicProof"])

    def test_hard_cap_still_kills_cpu_busy_owned_tree(self):
        with TemporaryDirectory() as td:
            process=MagicMock()
            process.pid=9138
            process.poll.return_value=None
            process.wait.return_value=0
            st={"currentHead":HEAD}
            with (patch.object(owner,"PRIVATE",Path(td)),
                  patch.object(owner.subprocess,"Popen",return_value=process),
                  patch.object(owner,"_update",side_effect=update),
                  patch.object(owner,"windows_owner_tree_cpu",
                               side_effect=[{"9138:1":0.},
                                            {"9138:1":7.}]),
                  patch.object(owner,"windows_kill_tree") as kill,
                  patch.object(owner.time,"monotonic",side_effect=[0.,20.]),
                  patch.object(owner.time,"sleep")):
                result=owner._log_process(st,"OWNER_REAL_SOURCE_ADMISSION",
                    ["python","-u","-m","safe"],cwd=Path(td),
                    timeout=15,idle_timeout=5)
            self.assertEqual(result,124)
            kill.assert_called_once_with(9138)
            self.assertEqual(st["ownerScienceLivenessDecision"],
                             "BSA308_HARD_OWNER_RUNTIME_CAP")
            self.assertNotIn("academicPASS",st)

    @skipUnless(os.name=="nt","Only Windows has the authorized process API")
    def test_real_windows_process_tree_cpu_snapshot_tracks_child_work(self):
        proc=subprocess.Popen([sys.executable,"-c",
            "import time;x=0;t=time.monotonic();\n"
            "while time.monotonic()-t<2.5: x+=1"],
            stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        try:
            before=windows_owner_tree_cpu(os.getpid())
            time.sleep(0.55)
            after=windows_owner_tree_cpu(os.getpid())
            self.assertIsNotNone(before)
            self.assertIsNotNone(after)
            self.assertGreaterEqual(cpu_time_gain(before,after),0.)
            self.assertTrue(any(s.startswith(str(proc.pid)+":")
                                for s in after))
        finally:
            if proc.poll() is None:
                proc.terminate()
            proc.wait(timeout=5)

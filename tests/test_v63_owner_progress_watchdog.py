"""BSA283: parent heartbeat cannot mask a silent original-source child."""
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import MagicMock, patch
import subprocess

from scripts import bosla_persistent_development as worker
from app_generator.runtime.v3_persistent_academic_failure_recovery import (
    classify_owner_failure,
)


def fake_update(st,label,**changes):
    st.update(changes)
    st["status"]=label


class RealChildProgressWatchdogTests(TestCase):
    def test_child_no_output_fails_closed_and_kills_only_its_tree(self):
        with TemporaryDirectory() as t:
            child=MagicMock()
            child.pid=9137
            child.poll.return_value=None
            child.wait.return_value=0
            state={}
            with (patch.object(worker,"PRIVATE",Path(t)),
                  patch.object(worker.subprocess,"Popen",return_value=child),
                  patch.object(worker.subprocess,"run",
                               return_value=subprocess.CompletedProcess([],0)) as kill,
                  patch.object(worker,"_update",side_effect=fake_update),
                  patch.object(worker.time,"monotonic",side_effect=[0.,20.]),
                  patch.object(worker.time,"sleep")):
                result=worker._log_process(
                    state,"OWNER_REAL_SOURCE_ADMISSION",
                    ["python","-u","-m","safe"],cwd=Path(t),
                    timeout=3600,idle_timeout=15)
            self.assertEqual(result,125)
            self.assertEqual(state["status"],
                             "BSA283_OWNER_REAL_SOURCE_ADMISSION_NO_VERIFIABLE_PROGRESS")
            self.assertEqual(state["failedPid"],9137)
            self.assertEqual(state["lastLogBytes"],0)
            args=kill.call_args.args[0]
            self.assertEqual(args,["taskkill","/T","/F","/PID","9137"])
            self.assertNotIn("academicPASS",state)
            self.assertNotIn("publicationAuthorized",state)

    def test_real_output_resets_idle_clock_and_saves_progress_bytes(self):
        with TemporaryDirectory() as t:
            child=MagicMock()
            child.pid=9138
            attempts=[0]
            def poll():
                attempts[0]+=1
                if attempts[0]==1:
                    # A real source-bound phase marker, not a parent heartbeat.
                    child_output.write(b"BSA283_OWNER_STEP_COMPLETE\n")
                    child_output.flush()
                    return None
                return 0
            child.poll.side_effect=poll
            child.wait.return_value=0
            child.returncode=0
            state={}
            def mkchild(*args,**kwargs):
                nonlocal child_output
                child_output=kwargs["stdout"]
                return child
            child_output=None
            with (patch.object(worker,"PRIVATE",Path(t)),
                  patch.object(worker.subprocess,"Popen",side_effect=mkchild),
                  patch.object(worker.subprocess,"run") as kill,
                  patch.object(worker,"_update",side_effect=fake_update),
                  patch.object(worker.time,"monotonic",
                               side_effect=[0.,20.,21.]),
                  patch.object(worker.time,"sleep")):
                result=worker._log_process(
                    state,"OWNER_REAL_SOURCE_ADMISSION",
                    ["python","-u","-m","safe"],cwd=Path(t),
                    timeout=3600,idle_timeout=15)
            self.assertEqual(result,0)
            self.assertEqual(state["status"],
                             "BSA279_OWNER_REAL_SOURCE_ADMISSION_ENDED")
            self.assertGreater(state["lastLogBytes"],0)
            kill.assert_not_called()

    def test_silent_exit_125_classified_as_local_owner_fault(self):
        failure=classify_owner_failure(
            exit_code=125,
            log_excerpt="SOURCE_BOUND_PER_GATE_PROOF still incomplete")
        self.assertEqual(failure,"LOCAL_OWNER_IMPLEMENTATION_DEFECT")
        self.assertEqual(classify_owner_failure(
            exit_code=125,log_excerpt="HMAC_MISMATCH"),
            "SOURCE_OR_SIGNATURE_UNTRUSTED")

    def test_no_mistaking_hard_timeout_for_success(self):
        self.assertNotEqual(classify_owner_failure(
            exit_code=124,log_excerpt="timeout"),"OWNER_SUCCESS_VERIFY_SEPARATELY")

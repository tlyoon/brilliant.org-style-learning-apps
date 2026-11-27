"""BSA286 fault injection: owner exception must not leak its process tree."""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import MagicMock,patch
import subprocess

from scripts import bosla_persistent_development as owner
from app_generator.runtime.v3_owner_child_tree_recovery import (
    exact_owner_identity,recover_previous_owner_tree,
)

STAMP="2026-11-27T08:45:33+00:00"
START="2026-11-27T08:45:31+00:00"
LATEST="2026-11-27T08:46:13+00:00"
PID=65432
PYTHON=Path("G:/My Drive/Projects/yoga 6/brilliant-project-continuity/bosla-v3-native-yoga6-20261115/.venv/Scripts/python.exe")


def state():
    return {
        "childPid":PID,
        "ownerChildStartedAt":STAMP,
        "ownerChildLabel":"OWNER_REAL_SOURCE_ADMISSION",
        "cycleStartedAt":START,
        "heartbeatAt":LATEST,
        "currentLog":r"C:\Users\User\AppData\Local\Microvid\BoslaPersistentDevelopment\logs\OWNER_REAL_SOURCE_ADMISSION_20261127_164533.log",
    }


def info():
    return {
        "pid":PID,"created":STAMP,"exe":str(PYTHON),
        "command":'"'+str(PYTHON)+'" -u -m scripts.auto_advance_bosla_academic_frontier --max-steps 8',
    }


class OwnerTreeSupervision(TestCase):
    def test_old_process_is_exactly_identified_before_kill(self):
        self.assertTrue(exact_owner_identity(info(),state(),expected_python=PYTHON))
        changed=info();changed["command"]="python -m unrelated_project"
        self.assertFalse(exact_owner_identity(changed,state(),expected_python=PYTHON))
        changed=info();changed["exe"]="C:/Other/Projects/other/.venv/Scripts/python.exe"
        self.assertFalse(exact_owner_identity(changed,state(),expected_python=PYTHON))
        changed=info();changed["created"]="2026-11-27T09:30:33+00:00"
        self.assertFalse(exact_owner_identity(changed,state(),expected_python=PYTHON))
        changed=info();changed["pid"]=PID+2
        self.assertFalse(exact_owner_identity(changed,state(),expected_python=PYTHON))

    def test_untrusted_pid_is_quarantined_not_killed(self):
        seen=[]
        fake=info();fake["created"]="2026-11-27T09:30:33+00:00"
        result=recover_previous_owner_tree(
            state(),expected_python=PYTHON,probe=lambda p:fake,
            kill=lambda p:seen.append(p))
        self.assertFalse(result["safe"])
        self.assertEqual(result["status"],"BSA286_REFUSED_UNTRUSTED_OLD_PID_IDENTITY")
        self.assertEqual(seen,[])

    def test_exact_saved_tree_reaped_then_same_restart_idempotent(self):
        st=state()
        alive=[info()]
        kills=[]
        def probe(pid):
            self.assertEqual(pid,PID)
            return alive[0] if alive else None
        def kill(pid):
            kills.append(pid)
            alive.clear()
            return 0
        result=recover_previous_owner_tree(st,expected_python=PYTHON,
                                           probe=probe,kill=kill)
        self.assertEqual(result["status"],"BSA286_STALE_OWNER_TREE_REAPED")
        self.assertTrue(result["safe"])
        self.assertEqual(kills,[PID])
        second=recover_previous_owner_tree(st,expected_python=PYTHON,
                                           probe=probe,kill=kill)
        self.assertTrue(second["safe"])
        self.assertEqual(kills,[PID])

    def test_refuse_failed_tree_kill_or_remaining_child(self):
        for code,expected in ((9,"BSA286_OWNER_TREE_TERMINATION_NOT_CONFIRMED"),
                              (0,"BSA286_OWNER_TREE_STILL_ALIVE_AFTER_KILL")):
            with self.subTest(code=code):
                result=recover_previous_owner_tree(
                    state(),expected_python=PYTHON,
                    probe=lambda pid:info(),kill=lambda pid:code)
                self.assertEqual(result["status"],expected)
                self.assertFalse(result["safe"])

    def test_missing_old_child_is_not_synthetic_science_progress(self):
        st=state()
        result=recover_previous_owner_tree(
            st,expected_python=PYTHON,
            probe=lambda pid:None,kill=lambda pid:self.fail("kill"))
        self.assertTrue(result["safe"])
        self.assertEqual(st["ownerChildLifecycle"],"EXITED_OR_ALREADY_CLEANED")
        self.assertNotIn("academicProofTasksAccepted",st)

    def test_exception_during_20_second_heartbeat_kills_owned_tree(self):
        with TemporaryDirectory() as td:
            child=MagicMock()
            child.pid=PID
            child.poll.return_value=None
            child.wait.return_value=0
            st={}
            seen=[]
            def update(st,label,**kw):
                st.update(kw)
                if label=="BSA279_OWNER_REAL_SOURCE_ADMISSION_RUNNING" and "elapsedSeconds" in kw:
                    raise OSError("transient owner state write failure")
                st["status"]=label
            with (patch.object(owner,"PRIVATE",Path(td)),
                  patch.object(owner.subprocess,"Popen",return_value=child),
                  patch.object(owner,"windows_kill_tree",side_effect=seen.append),
                  patch.object(owner,"_update",side_effect=update),
                  patch.object(owner.time,"monotonic",side_effect=[0.,20.]),
                  patch.object(owner.time,"sleep")):
                with self.assertRaisesRegex(OSError,"transient owner state"):
                    owner._log_process(st,"OWNER_REAL_SOURCE_ADMISSION",
                        ["python","-u","-m","safe"],cwd=Path(td),
                        timeout=3600,idle_timeout=1200)
            self.assertEqual(seen,[PID])
            child.wait.assert_called_once()
            self.assertNotIn("academicPASS",st)

    def test_secondary_wait_timeout_cannot_hide_cleanup_or_mark_pass(self):
        with TemporaryDirectory() as td:
            child=MagicMock()
            child.pid=PID
            child.poll.return_value=None
            child.wait.side_effect=[
                subprocess.TimeoutExpired("real-child",5),
                subprocess.TimeoutExpired("real-child",4),
            ]
            st={}
            with (patch.object(owner,"PRIVATE",Path(td)),
                  patch.object(owner.subprocess,"Popen",return_value=child),
                  patch.object(owner,"windows_kill_tree",return_value=0) as kill,
                  patch.object(owner,"_update",side_effect=lambda s,label,**kw:s.update(kw)),
                  patch.object(owner.time,"monotonic",side_effect=[0.,20.]),
                  patch.object(owner.time,"sleep")):
                with self.assertRaisesRegex(ValueError,"TERMINATION_UNVERIFIED"):
                    owner._log_process(st,"OWNER_REAL_SOURCE_ADMISSION",
                        ["python","-u","-m","safe"],cwd=Path(td),
                        timeout=3600,idle_timeout=1200)
            self.assertEqual(kill.call_count,2)
            self.assertEqual(st["ownerChildLifecycle"],"CLEANUP_UNVERIFIED")

"""BSA286 real Windows fault injection: kill owned nested worker, not siblings."""
from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import os
import re
import subprocess
import sys
import time
from unittest import TestCase,skipUnless
from unittest.mock import patch

from scripts import bosla_persistent_development as owner
from app_generator.runtime.v3_owner_child_tree_recovery import windows_process_probe,windows_kill_tree


@skipUnless(os.name=="nt","Requires real Windows taskkill and Win32_Process")
class WindowsNestedTreeRecovery(TestCase):
    def test_real_nested_child_idle_kills_all_descendants_without_touching_sibling(self):
        with TemporaryDirectory() as td:
            private=Path(td)
            sibling=subprocess.Popen([sys.executable,"-c","import time;time.sleep(40)"],
                                      stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
            grandchild=None
            try:
                # This child really creates a second Python process in Windows.
                code=("import subprocess,sys,time;"
                      "p=subprocess.Popen([sys.executable,'-c','import time;time.sleep(40)']);"
                      "print('BSA286_GRANDCHILD_PID='+str(p.pid),flush=True);"
                      "time.sleep(40)")
                def state_update(st,status,**fields):
                    st.update(fields)
                    st["status"]=status
                st={}
                with patch.object(owner,"PRIVATE",private),patch.object(
                        owner,"_update",side_effect=state_update):
                    result=owner._log_process(
                        st,"OWNER_REAL_SOURCE_ADMISSION",
                        [sys.executable,"-u","-c",code],cwd=private,
                        timeout=40,idle_timeout=3)
                self.assertEqual(result,125)
                self.assertTrue(sibling.poll() is None,
                    "BSA286 must not kill unrelated Windows processes")
                logs=list((private/"logs").glob("*.log"))
                self.assertEqual(len(logs),1)
                m=re.search(r"BSA286_GRANDCHILD_PID=(\d+)",
                            logs[0].read_text(encoding="utf8"))
                self.assertIsNotNone(m,"Test subprocess must actually launch its descendant")
                grandchild=int(m.group(1))
                # OS snapshots take longer than process reaping on some hosts.
                for _ in range(10):
                    if windows_process_probe(grandchild) is None:
                        break
                    time.sleep(.2)
                self.assertIsNone(windows_process_probe(grandchild))
                self.assertIsNone(windows_process_probe(st["childPid"]))
                self.assertNotIn("academicPASS",st)
            finally:
                if grandchild is not None and windows_process_probe(grandchild):
                    windows_kill_tree(grandchild)
                sibling.kill()
                sibling.wait(timeout=10)

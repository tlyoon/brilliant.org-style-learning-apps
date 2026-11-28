"""BSA307 Windows scheduler launcher survives nested scripts imports.

Both historical file entry and module invocation are source-read-only --status.
No scheduled task is created/removed by hosted tests.
"""
from __future__ import annotations
from pathlib import Path
import json
import os
import subprocess
import sys
from tempfile import TemporaryDirectory
from unittest import TestCase

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/"scripts"/"bosla_persistent_development.py"
INSTALLER=ROOT/"scripts"/"install_bosla_persistent_development.ps1"

class PersistentBoslaTaskEntrypoint(TestCase):
    def _probe(self,entry:list[str]):
        with TemporaryDirectory() as temp:
            env={**os.environ,"LOCALAPPDATA":temp}
            env.pop("PYTHONPATH",None)
            out=subprocess.run([sys.executable,"-B",*entry,"--status"],
                cwd=ROOT,env=env,text=True,capture_output=True,timeout=35)
        self.assertEqual(out.returncode,0,
            "BSA307_STATUS_ENTRY_FAILED:"+out.stderr[-280:])
        value=json.loads(out.stdout)
        self.assertIsInstance(value.get("state"),dict)
        self.assertNotIn("Traceback",out.stderr)
        return value

    def test_old_task_file_invocation_imports_nested_scripts_successfully(self):
        self._probe([str(SCRIPT)])

    def test_new_module_task_invocation_is_source_read_only(self):
        self._probe(["-m","scripts.bosla_persistent_development"])

    def test_future_installation_preserves_two_triggers_and_exact_module_action(self):
        script=INSTALLER.read_text(encoding="utf8")
        self.assertIn(
            "-Argument '-B -m scripts.bosla_persistent_development --long-horizon'",
            script)
        self.assertIn("-WorkingDirectory $repo",script)
        self.assertIn("New-ScheduledTaskTrigger -AtLogOn",script)
        self.assertIn("New-ScheduledTaskTrigger -Once",script)
        self.assertIn("-MultipleInstances IgnoreNew",script)
        self.assertIn("BSA279_RETIRED_LEGACY_TASK_PRESENT_DO_NOT_REINSTALL",
                      script)
        self.assertNotIn("('-B \"'+$worker+'\" --once')",script)

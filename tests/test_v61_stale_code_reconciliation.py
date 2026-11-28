"""BSA282: stale developer branch cannot overwrite newer original science.

Owner main may advance original academic acceptance A13-A15 while an earlier
uncommitted Codex patch was constructed from a previous Git head. The normal
scheduler must preserve prior work, stop replay of old context, and try
current-head code development without manual user intervention. Never merge
stale unreviewed bytes or sign academic PASS.
"""
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch
import subprocess

from scripts import bosla_persistent_development as worker

MAIN="a"*40
OLD="b"*40
BRANCH="feature/old-repair"

class StaleDevelopmentTests(TestCase):
    def test_old_branch_changes_quarantined_and_new_head_is_next(self):
        with TemporaryDirectory() as t:
            repo=Path(t)
            path=repo/"preserved-old-dev"
            path.mkdir()
            untouched=path/"valuable-old-patch.py"
            untouched.write_text("KEEP_PRESERVED=1\n",encoding="utf8")
            state={
                "codexRepairRequired":True,
                "devBranch":BRANCH,"devWorktree":str(path),
                "codexCount":7,
                "status":"BSA279_CODEX_PATCH_WHITESPACE_FAILURE",
            }
            def githead(at=worker.ROOT):
                return OLD if Path(at)==path else MAIN
            def branch(at=worker.ROOT):
                return BRANCH if Path(at)==path else worker.MAIN_BRANCH
            def fake_update(s,label,**fields):
                s.update(fields)
                s["status"]=label
            with (patch.object(worker,"_head",side_effect=githead),
                  patch.object(worker,"_branch",side_effect=branch),
                  patch.object(worker,"_run",return_value=
                    subprocess.CompletedProcess([],0,"","")),
                  patch.object(worker,"_ok",return_value="tests/preserved.py"),
                  patch.object(worker,"_update",side_effect=fake_update),
                  patch.object(worker,"_adaptive_model_admission",
                               side_effect=lambda st:(
                                   fake_update(st,"BSA288_OBSERVED_PROVIDER_BACKOFF")
                                   or False)),
                  patch.object(worker,"_log_process") as model):
                self.assertFalse(worker._codex_stage(state))
                model.assert_not_called()
            self.assertEqual(state["status"],
                "BSA288_OBSERVED_PROVIDER_BACKOFF")
            self.assertEqual(len(state["quarantinedStalePatches"]),1)
            self.assertEqual(state["quarantinedStalePatches"][0]["head"],OLD)
            self.assertEqual(state["quarantinedStalePatches"][0]["branch"],BRANCH)
            self.assertEqual(state["quarantinedStalePatches"][0]["worktree"],str(path))
            self.assertFalse(state["codexRepairRequired"])
            self.assertNotIn("devBranch",state)
            self.assertTrue(untouched.is_file())
            self.assertEqual(untouched.read_text(),"KEEP_PRESERVED=1\n")
            self.assertEqual(state["codexCount"],7)
            self.assertNotIn("academicPASS",state)

    def test_previous_same_head_whitespace_repaired_without_model(self):
        with TemporaryDirectory() as t:
            path=Path(t)
            state={
                "codexRepairRequired":True,
                "devBranch":BRANCH,"devWorktree":str(path),
                "codexCount":7,
                "status":"BSA279_CODEX_PATCH_WHITESPACE_FAILURE",
            }
            with (patch.object(worker,"_head",return_value=MAIN),
                  patch.object(worker,"_branch",return_value=BRANCH),
                  patch.object(worker,"_update",side_effect=lambda s,v,**kw:
                               s.update({"status":v,**kw})),
                  patch.object(worker,"repair_staged_blank_eof",
                    return_value={
                        "status":"REPAIRED_EXACT_BLANK_LINES_AT_EOF",
                        "fixedFiles":["tests/test_science.py"],
                        "beforeAfterSha256":{"tests/test_science.py":
                           {"before":"a"*64,"after":"b"*64}}}) as cleanup,
                  patch.object(worker,"_finalize_staged_patch",
                               return_value=True) as finalize,
                  patch.object(worker,"_log_process") as model):
                self.assertTrue(worker._codex_stage(state))
                cleanup.assert_called_once()
                finalize.assert_called_once()
                model.assert_not_called()
            self.assertEqual(state["codexCount"],7)
            self.assertEqual(state["status"],
                             "BSA282_RESUMED_SAVED_PATCH_NO_MODEL_CALL")
            self.assertNotIn("academicPASS",state)

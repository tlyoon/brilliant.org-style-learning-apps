"""BSA280 safe Git-less Codex snapshot and no-evidence-forgery tests."""
from __future__ import annotations
from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory
from unittest import TestCase,skipUnless
from app_generator.runtime.v3_isolated_codegen_workspace import (
    _safe_name,_safe_patch_path,build_isolated_coding_snapshot,
    collect_isolated_patch,apply_isolated_patch,
)

def git(repo:Path,*args:str)->None:
    result=subprocess.run(["git",*args],cwd=repo,capture_output=True,
                          text=True,timeout=20)
    if result.returncode:
        raise AssertionError(result.stderr)

class IsolatedCodegenWorkspaceTests(TestCase):
    def fixture(self,base:Path)->Path:
        repo=base/"repo"
        repo.mkdir()
        git(repo,"init","-q")
        (repo/"AGENTS.md").write_text("Bosla original source only\n")
        (repo/"docs").mkdir()
        (repo/"docs/recurrence_registry.json").write_text('{"incidents":[]}')
        (repo/"app_generator").mkdir()
        (repo/"app_generator/original.py").write_text("VALUE=10\n")
        (repo/"content").mkdir()
        (repo/"content/source.pdf").write_bytes(b"private-not-for-model")
        git(repo,"add","AGENTS.md","docs/recurrence_registry.json",
            "app_generator/original.py")
        return repo

    def test_snapshot_is_standalone_gitless_and_no_private_pdf(self):
        with TemporaryDirectory() as t:
            base=Path(t)
            repo=self.fixture(base)
            snap=base/"safe-snapshot"
            digest=build_isolated_coding_snapshot(repo=repo,snapshot=snap)
            self.assertIn("AGENTS.md",digest)
            self.assertTrue((snap/"app_generator/original.py").exists())
            self.assertFalse((snap/"content/source.pdf").exists())
            self.assertFalse((snap/".git").exists())
            self.assertFalse((snap/"source.pdf").exists())

    def test_untracked_private_source_not_sent_to_model(self):
        with TemporaryDirectory() as t:
            base=Path(t)
            repo=self.fixture(base)
            # Untracked code may be a pending repair; unrelated local
            # private source cannot enter the disposable model snapshot.
            (repo/"content"/"original_transcript.txt").write_text(
                "NEVER SEND PRIVATE ORIGINAL SOURCE")
            (repo/"app_generator"/"pending_proof.py").write_text(
                "def source_safe_rule(): return True\n")
            snap=base/"safe"
            baseline=build_isolated_coding_snapshot(
                repo=repo,snapshot=snap)
            self.assertFalse(
                (snap/"content/original_transcript.txt").exists())
            self.assertTrue(
                (snap/"app_generator/pending_proof.py").exists())
            self.assertNotIn("content/original_transcript.txt",baseline)

    def test_patch_import_verified_without_git_or_academic_pass(self):
        with TemporaryDirectory() as t:
            base=Path(t)
            repo=self.fixture(base)
            snap=base/"safe-snapshot"
            baseline=build_isolated_coding_snapshot(repo=repo,snapshot=snap)
            new=snap/"app_generator/validation/safe_countermodel.py"
            new.parent.mkdir(parents=True)
            new.write_text(
                "from fractions import Fraction\n"
                "def force(m, a): return Fraction(m)*Fraction(a)\n")
            (snap/"tests").mkdir()
            (snap/"tests/test_safe.py").write_text("assert 2+2==4\n")
            patch=collect_isolated_patch(snapshot=snap,baseline=baseline)
            self.assertEqual(set(patch),{
                "app_generator/validation/safe_countermodel.py",
                "tests/test_safe.py"})
            adopted=apply_isolated_patch(
                repo=repo,snapshot=snap,baseline=baseline)
            self.assertEqual(set(adopted),set(patch))
            self.assertEqual(
                (repo/"app_generator/validation/safe_countermodel.py").read_text(),
                new.read_text())
            self.assertNotIn("academicPASS",str(patch))

    def test_no_docs_only_or_synthetic_academic_pass(self):
        with TemporaryDirectory() as t:
            base=Path(t)
            repo=self.fixture(base)
            snap=base/"safe"
            baseline=build_isolated_coding_snapshot(repo=repo,snapshot=snap)
            (snap/"AGENTS.md").write_text("I declare 429 tasks PASS\n")
            with self.assertRaisesRegex(ValueError,"DOCS_ONLY"):
                collect_isolated_patch(snapshot=snap,baseline=baseline)

    def test_fails_closed_on_deleting_existing_source(self):
        with TemporaryDirectory() as t:
            base=Path(t)
            repo=self.fixture(base)
            snap=base/"safe"
            baseline=build_isolated_coding_snapshot(repo=repo,snapshot=snap)
            (snap/"app_generator/original.py").unlink()
            with self.assertRaisesRegex(ValueError,"DELETED_SOURCE"):
                collect_isolated_patch(snapshot=snap,baseline=baseline)

    def test_unapproved_paths_and_secrets_quarantined(self):
        with TemporaryDirectory() as t:
            base=Path(t)
            repo=self.fixture(base)
            snap=base/"safe"
            baseline=build_isolated_coding_snapshot(repo=repo,snapshot=snap)
            (snap/".github/workflows").mkdir(parents=True)
            (snap/".github/workflows/ci.yml").write_text("disable ci")
            with self.assertRaisesRegex(ValueError,
                                        "UNSAFE_NEW_PATH|UNAPPROVED_SCOPE"):
                collect_isolated_patch(snapshot=snap,baseline=baseline)
            (snap/".github/workflows/ci.yml").unlink()
            (snap/"scripts").mkdir()
            (snap/"scripts/.env").write_text("SECRET")
            with self.assertRaisesRegex(ValueError,"UNSAFE_NEW_PATH"):
                collect_isolated_patch(snapshot=snap,baseline=baseline)

    def test_preexisting_file_mutation_between_snapshot_and_import(self):
        with TemporaryDirectory() as t:
            base=Path(t)
            repo=self.fixture(base)
            snap=base/"safe"
            baseline=build_isolated_coding_snapshot(repo=repo,snapshot=snap)
            (snap/"app_generator/original.py").write_text("VALUE=21\n")
            (repo/"app_generator/original.py").write_text("VALUE=999\n")
            with self.assertRaisesRegex(ValueError,"SOURCE_CHANGED"):
                apply_isolated_patch(repo=repo,snapshot=snap,baseline=baseline)
            self.assertEqual((repo/"app_generator/original.py").read_text(),
                             "VALUE=999\n")

    def test_rejects_nontarget_traversal_and_nonpublic_release_paths(self):
        for path in ("../secrets.py","/tmp/bad.py","docs/.env",
                     "scripts/source.pdf",".github/workflows/main.yml",
                     "docs/private_source.md","C:/evil.py"):
            with self.subTest(path=path):
                self.assertFalse(_safe_patch_path(path))

    def test_snapshot_cannot_include_symlink_to_private_source(self):
        with TemporaryDirectory() as t:
            base=Path(t)
            repo=self.fixture(base)
            snap=base/"safe"
            baseline=build_isolated_coding_snapshot(repo=repo,snapshot=snap)
            private=base/"private.txt"
            private.write_text("not allowed")
            link=snap/"app_generator/exfil.py"
            try:
                link.symlink_to(private)
            except (OSError,NotImplementedError):
                self.skipTest("symlinks not supported in this environment")
            with self.assertRaisesRegex(ValueError,"SYMLINK"):
                collect_isolated_patch(snapshot=snap,baseline=baseline)

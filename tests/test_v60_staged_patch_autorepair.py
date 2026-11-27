"""BSA282: executable fault injection against real Git staged changes."""
from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory
from unittest import TestCase

from app_generator.runtime.v3_staged_patch_autorepair import (
    repair_staged_blank_eof,
)


def git(repo:Path,*args:str)->subprocess.CompletedProcess[bytes]:
    return subprocess.run(["git",*args],cwd=repo,capture_output=True)


class AutoRepairGitWhitespaceTests(TestCase):
    def repo(self,base:Path)->Path:
        repo=base/"repo"
        repo.mkdir()
        result=git(repo,"init","-q")
        if result.returncode:
            raise RuntimeError(result.stderr.decode())
        (repo/"tests").mkdir()
        (repo/"app_generator").mkdir()
        (repo/"docs").mkdir()
        (repo/"tests/a.py").write_bytes(b"def f():\n    return 1\n")
        (repo/"app_generator/physics.py").write_bytes(b"VALUE=10\n")
        (repo/"docs/report.md").write_bytes(b"hello\n")
        git(repo,"add","--all")
        return repo

    def test_repair_real_git_extra_blank_line_then_exact_gate(self):
        with TemporaryDirectory() as t:
            repo=self.repo(Path(t))
            orig=b"def f():\n    return 1\n"
            bad=orig+b"\n"
            (repo/"tests/a.py").write_bytes(bad)
            git(repo,"add","--all")
            self.assertNotEqual(git(repo,"diff","--cached","--check").returncode,0)
            status=repair_staged_blank_eof(repo)
            self.assertEqual(status["status"],"REPAIRED_EXACT_BLANK_LINES_AT_EOF")
            self.assertEqual(status["fixedFiles"],["tests/a.py"])
            self.assertEqual((repo/"tests/a.py").read_bytes(),orig)
            self.assertEqual(git(repo,"diff","--cached","--check").returncode,0)
            self.assertFalse(status["academicPASS"])
            self.assertFalse(status["publicationAuthorized"])

    def test_crlf_multiple_blank_lines_retains_science_content(self):
        with TemporaryDirectory() as t:
            repo=self.repo(Path(t))
            # Git's default CRLF policy differs by host OS. Pin the
            # actual Git core.whitespace interpretation for this fixture;
            # production still requires Git's exact real-time report.
            self.assertEqual(
                git(repo,"config","core.whitespace","cr-at-eol").returncode,0)
            correct=b"from fractions import Fraction\r\nx = Fraction(1, 3)\r\n"
            (repo/"app_generator/physics.py").write_bytes(correct+b"\r\n\r\n")
            git(repo,"add","--all")
            fixed=repair_staged_blank_eof(repo)
            self.assertEqual(fixed["status"],"REPAIRED_EXACT_BLANK_LINES_AT_EOF")
            self.assertEqual((repo/"app_generator/physics.py").read_bytes(),correct)

    def test_unrelated_trailing_whitespace_not_autofixed(self):
        with TemporaryDirectory() as t:
            repo=self.repo(Path(t))
            bad=b"def f(): \n    return 1\n"
            (repo/"tests/a.py").write_bytes(bad)
            git(repo,"add","--all")
            status=repair_staged_blank_eof(repo)
            self.assertEqual(status["status"],"UNCLASSIFIED_WHITESPACE_NOT_AUTO_REPAIRED")
            self.assertEqual((repo/"tests/a.py").read_bytes(),bad)

    def test_mixed_critical_error_and_eof_blank_not_autofixed(self):
        with TemporaryDirectory() as t:
            repo=self.repo(Path(t))
            bad=b"def f(): \n    return 1\n\n"
            (repo/"tests/a.py").write_bytes(bad)
            git(repo,"add","--all")
            status=repair_staged_blank_eof(repo)
            self.assertEqual(status["status"],"UNCLASSIFIED_WHITESPACE_NOT_AUTO_REPAIRED")
            self.assertEqual((repo/"tests/a.py").read_bytes(),bad)

    def test_clean_patch_is_left_untouched(self):
        with TemporaryDirectory() as t:
            repo=self.repo(Path(t))
            status=repair_staged_blank_eof(repo)
            self.assertEqual(status["status"],"ALREADY_CLEAN")
            self.assertEqual(status["fixedFiles"],[])

    def test_refuse_invalid_dir_even_with_matching_error(self):
        with TemporaryDirectory() as t:
            repo=self.repo(Path(t))
            (repo/"docs").mkdir(exist_ok=True)
            bad=repo/"docs/source.pdf"
            bad.write_bytes(b"science\n\n")
            git(repo,"add","--all")
            with self.assertRaisesRegex(ValueError,"UNSAFE_PATCH_PATH"):
                repair_staged_blank_eof(repo)

    def test_never_edit_secret_credentials(self):
        with TemporaryDirectory() as t:
            repo=self.repo(Path(t))
            bad=repo/"tests/something_secret.py"
            bad.write_bytes(b"secret=2\n\n")
            git(repo,"add","--all")
            with self.assertRaisesRegex(ValueError,"UNSAFE_PATCH_PATH"):
                repair_staged_blank_eof(repo)
            self.assertEqual(bad.read_bytes(),b"secret=2\n\n")

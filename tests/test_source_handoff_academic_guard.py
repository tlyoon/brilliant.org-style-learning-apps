import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from app_generator.errors import GitPublishError, ValidationFailure
from app_generator.publishing.git import GitPublisher


class SourceHandoffAcademicGuardTests(unittest.TestCase):
    def _fixture(self, root):
        def git(*args):
            result = subprocess.run(
                ["git", *args], cwd=root, capture_output=True, text=True,
                check=False, encoding="utf-8"
            )
            if result.returncode:
                raise AssertionError((args, result.stdout, result.stderr))
            return result.stdout.strip()
        git("init", "-q")
        git("config", "user.email", "fixture@example.invalid")
        git("config", "user.name", "Test Fixture")
        git("switch", "-c", "auto/section-9-4-test")
        package = root / "content/chapter-9/section-9-4/package.json"
        package.parent.mkdir(parents=True)
        package.write_text(
            json.dumps({"packageId": "test", "sourceManifest": "content/source-manifests/source.json"}),
            encoding="utf-8"
        )
        manifest = root / "content/source-manifests/source.json"
        manifest.parent.mkdir(parents=True)
        manifest.write_text(json.dumps({"sha256": "a"*64, "sources": []}), encoding="utf-8")
        git("add", ".")
        git("commit", "-qm", "fixture handoff")
        config = SimpleNamespace(
            repo_root=root, package_path=package, state_dir=root / "state",
            git_remote="origin", git_auto_merge=True,
        )
        return GitPublisher(config), package, manifest

    def test_missing_or_changed_local_package_blocks_before_github_pr_mutation(self):
        with tempfile.TemporaryDirectory() as d:
            p, package, _ = self._fixture(Path(d))
            p._ensure_pr = MagicMock(side_effect=AssertionError("no GH operation should occur"))
            package.unlink()
            with self.assertRaisesRegex(GitPublishError, "local package/state evidence unavailable"):
                p._finalize_pr("auto/section-9-4-test", subchapter="9.4", package_id="test")
            package.write_text('{"sourceManifest":"other.json"}', encoding="utf-8")
            with self.assertRaisesRegex(GitPublishError, "exact source manifest"):
                p._finalize_pr("auto/section-9-4-test", subchapter="9.4", package_id="test")
            p._ensure_pr.assert_not_called()

    def test_dirty_manifest_or_branch_mismatch_fails_closed(self):
        with tempfile.TemporaryDirectory() as d:
            p, package, manifest = self._fixture(Path(d))
            manifest.write_text('{"tampered":true}', encoding="utf-8")
            p._ensure_pr = MagicMock(side_effect=AssertionError("no GitHub PR operation"))
            with self.assertRaisesRegex(GitPublishError, "mismatched"):
                p._finalize_pr("auto/section-9-4-test", subchapter="9.4", package_id="test")
            p._ensure_pr.assert_not_called()

    def test_valid_exact_handoff_requires_academic_evidence_before_github_mutation(self):
        with tempfile.TemporaryDirectory() as d:
            p, package, _ = self._fixture(Path(d))
            p._ensure_pr = MagicMock(side_effect=AssertionError("no GitHub PR operation"))
            with patch("app_generator.publishing.git.enforce_academic_release_gate",
                       side_effect=ValidationFailure("QA unresolved", ["REVIEW_REQUIRED"])):
                with self.assertRaisesRegex(ValidationFailure, "QA unresolved"):
                    p._finalize_pr("auto/section-9-4-test", subchapter="9.4", package_id="test")
            p._ensure_pr.assert_not_called()
            with patch("app_generator.publishing.git.enforce_academic_release_gate",
                       return_value={"academicQA": "PASS"}) as check:
                p._ensure_pr = MagicMock(return_value={
                    "state": "MERGED", "mergedAt": "2026-10-24T00:00:00Z",
                    "url": "https://github.com/example/repo/pull/1"
                })
                _, merged = p._finalize_pr("auto/section-9-4-test", subchapter="9.4", package_id="test")
                self.assertTrue(merged)
                check.assert_called_once()
                p._ensure_pr.assert_called_once()

    def test_draft_handoff_keeps_legacy_review_without_claiming_academic_pass(self):
        with tempfile.TemporaryDirectory() as d:
            p, _, _ = self._fixture(Path(d))
            p.config.git_auto_merge = False
            p._ensure_pr = MagicMock(return_value={
                "state": "OPEN", "url": "https://github.com/example/repo/pull/2"
            })
            with patch("app_generator.publishing.git.enforce_academic_release_gate") as gate:
                url, merged = p._finalize_pr("auto/section-9-4-test", subchapter="9.4", package_id="test")
            self.assertFalse(merged)
            self.assertIn("/pull/2", url)
            gate.assert_not_called()


if __name__ == "__main__":
    unittest.main()

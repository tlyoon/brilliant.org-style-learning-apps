import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from app_generator.errors import ValidationFailure
from app_generator.runtime.academic_release import (
    enforce_academic_release_gate, public_release_requested,
)

ROOT=Path(__file__).resolve().parents[1]

class AcademicPublicationGateTests(unittest.TestCase):
    def test_draft_review_allowed_but_merge_and_deploy_require_academic_gate(self):
        self.assertFalse(public_release_requested(SimpleNamespace(
            git_publish=True, git_create_draft_pr=True, git_auto_merge=False, public_deploy=False,
        )))
        self.assertTrue(public_release_requested(SimpleNamespace(git_auto_merge=True, public_deploy=False)))
        self.assertTrue(public_release_requested(SimpleNamespace(git_auto_merge=False, public_deploy=True)))
        self.assertTrue(public_release_requested(SimpleNamespace(git_auto_merge=True, public_deploy=True)))

    def test_real_section94_blocks_unreviewed_public_release_and_saves_report(self):
        package=ROOT/"content/chapter-9/section-9-4/package.json"
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ValidationFailure, "unresolved academic QA"):
                enforce_academic_release_gate(ROOT,package,Path(tmp))
            report=json.loads((Path(tmp)/"academic-release-gate.json").read_text(encoding="utf-8"))
            self.assertEqual("REVIEW_REQUIRED",report["academicQA"])
            self.assertEqual(hashlib.sha256(package.read_bytes()).hexdigest(),report["artifactSha256"])
            self.assertFalse(report["publicationAuthorized"])

    def test_approved_verifier_result_requires_matching_artifact_bytes(self):
        with tempfile.TemporaryDirectory() as tmp:
            package=Path(tmp)/"package.json"
            package.write_text('{"activities":[]}',encoding="utf-8")
            digest=hashlib.sha256(package.read_bytes()).hexdigest()
            with patch("app_generator.runtime.academic_release.academic_triage",return_value={
                "academicQA":"PASS", "gates":{"answer_correctness":"PASS"}, "artifactSha256":digest
            }):
                result=enforce_academic_release_gate(ROOT,package,Path(tmp))
            self.assertEqual(result["academicQA"],"PASS")
            with patch("app_generator.runtime.academic_release.academic_triage",return_value={
                "academicQA":"PASS", "gates":{}, "artifactSha256":"0"*64
            }):
                with self.assertRaisesRegex(ValidationFailure,"another package version"):
                    enforce_academic_release_gate(ROOT,package,Path(tmp))

    def test_verifier_failure_is_fail_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            package=Path(tmp)/"package.json"
            package.write_text("{}",encoding="utf-8")
            with patch("app_generator.runtime.academic_release.academic_triage",side_effect=ValueError("invalid")):
                with self.assertRaisesRegex(ValidationFailure,"could not be completed"):
                    enforce_academic_release_gate(ROOT,package,Path(tmp))

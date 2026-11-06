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
            self.assertIn(report["academicQA"],("FAIL","REVIEW_REQUIRED"))
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
                with self.assertRaisesRegex(ValidationFailure,"visual-value assessment"):
                    enforce_academic_release_gate(ROOT,package,Path(tmp))
            receipt=json.loads((Path(tmp)/"visual-release-gate.json").read_text(encoding="utf-8"))
            self.assertEqual(receipt["status"],"BLOCKED_VISUAL_VALUE_ASSESSMENT")
            self.assertFalse(receipt["publicationAuthorized"])
            with patch("app_generator.runtime.academic_release.academic_triage",return_value={
                "academicQA":"PASS", "gates":{}, "artifactSha256":"0"*64
            }):
                with self.assertRaisesRegex(ValidationFailure,"another package version"):
                    enforce_academic_release_gate(ROOT,package,Path(tmp))

    def test_mocked_academic_pass_still_refuses_legacy_no_visual_plan(self):
        source=ROOT/"content/chapter-1/section-1-1/package.json"
        with tempfile.TemporaryDirectory() as tmp:
            package=Path(tmp)/"package.json"
            package.write_bytes(source.read_bytes())
            digest=hashlib.sha256(package.read_bytes()).hexdigest()
            with patch("app_generator.runtime.academic_release.academic_triage",return_value={
                "academicQA":"PASS", "gates":{"answer_correctness":"PASS"},
                "artifactSha256":digest,
            }):
                with self.assertRaisesRegex(ValidationFailure,"visual-value assessment"):
                    enforce_academic_release_gate(ROOT,package,Path(tmp))
            receipt=json.loads((Path(tmp)/"visual-release-gate.json").read_text())
            self.assertEqual("BLOCKED_VISUAL_VALUE_ASSESSMENT",receipt["status"])
            self.assertEqual(digest,receipt["packageSha256"])

    def test_valid_text_first_plans_require_no_decorative_visual_quota(self):
        # Only an artificial academic PASS stub: no actual physics approval.
        from tests.test_visual_contracts import plan
        source=ROOT/"content/chapter-1/section-1-1/package.json"
        package_data=json.loads(source.read_text(encoding="utf-8"))
        for activity in package_data["activities"]:
            value=plan("none",None)
            value["fallbackMode"]="none"
            value["renderStrategy"]="none"
            value["representationAssessment"].update(
                visualValue=0,simulationValue=0,visualRequired=False,
                rationale="The text-based reasoning task needs no drawing.")
            value["generatedAssetPolicy"]["answerCriticalLayer"]="none"
            value["activityIntent"].update(
                learningObjective=activity["objective"],difficulty=activity["difficulty"],
                misconceptionTargets=activity["misconceptions"])
            value["groundedFactsUsed"]=[]
            activity["visualPlan"]=value
        with tempfile.TemporaryDirectory() as tmp:
            package=Path(tmp)/"package.json"
            package.write_text(json.dumps(package_data),encoding="utf-8")
            digest=hashlib.sha256(package.read_bytes()).hexdigest()
            with patch("app_generator.runtime.academic_release.academic_triage",return_value={
                "academicQA":"PASS", "gates":{"answer_correctness":"PASS"},
                "artifactSha256":digest,
            }):
                result=enforce_academic_release_gate(ROOT,package,Path(tmp))
            self.assertEqual(result["academicQA"],"PASS")
            receipt=json.loads((Path(tmp)/"visual-release-gate.json").read_text())
            self.assertEqual(receipt["declaredVisualPlans"],18)
            self.assertEqual(receipt["declaredVisualSpecs"],0)
            self.assertFalse(receipt["visualSemanticsIndependentlyVerified"])
            self.assertFalse(receipt["publicationAuthorized"])

    def test_invalid_declared_visual_plan_cannot_bypass_release_gate(self):
        from tests.test_visual_contracts import plan
        source=ROOT/"content/chapter-1/section-1-1/package.json"
        data=json.loads(source.read_text(encoding="utf-8"))
        for activity in data["activities"]:
            value=plan("none",None)
            value["fallbackMode"]="none"
            value["renderStrategy"]="none"
            value["representationAssessment"].update(
                visualValue=0,simulationValue=0,visualRequired=False,
                rationale="No graphic is necessary.")
            value["generatedAssetPolicy"]["answerCriticalLayer"]="none"
            value["activityIntent"].update(
                learningObjective=activity["objective"],difficulty=activity["difficulty"],
                misconceptionTargets=activity["misconceptions"])
            value["groundedFactsUsed"]=[]
            activity["visualPlan"]=value
        data["activities"][0]["visualPlan"]["representationAssessment"]["visualRequired"]=True
        with tempfile.TemporaryDirectory() as tmp:
            package=Path(tmp)/"package.json"
            package.write_text(json.dumps(data),encoding="utf-8")
            digest=hashlib.sha256(package.read_bytes()).hexdigest()
            with patch("app_generator.runtime.academic_release.academic_triage",return_value={
                "academicQA":"PASS", "gates":{"answer_correctness":"PASS"},
                "artifactSha256":digest,
            }):
                with self.assertRaisesRegex(ValidationFailure,"visual-value assessment"):
                    enforce_academic_release_gate(ROOT,package,Path(tmp))
            receipt=json.loads((Path(tmp)/"visual-release-gate.json").read_text())
            self.assertEqual(receipt["status"],"BLOCKED_VISUAL_VALUE_ASSESSMENT")

    def test_direct_public_publisher_refuses_real_unverified_section94_without_git_calls(self):
        from app_generator.publishing.public import PublicPagesPublisher
        with tempfile.TemporaryDirectory() as tmp:
            package=ROOT/"content/chapter-9/section-9-4/package.json"
            config=SimpleNamespace(repo_root=ROOT, state_dir=Path(tmp))
            class NeverRemote(PublicPagesPublisher):
                def _run(self, arguments, *, cwd=None, check=True):
                    raise AssertionError("no remote publication commands permitted")
            publisher=NeverRemote(config)
            with self.assertRaisesRegex(ValidationFailure, "unresolved academic QA"):
                publisher.publish(
                    package_path=package, subchapter_id="9.4",
                    ensure_lease=lambda: None,
                )
            digest=hashlib.sha256(package.read_bytes()).hexdigest()
            record=Path(tmp)/"academic-publication-gates"/digest/"academic-release-gate.json"
            report=json.loads(record.read_text(encoding="utf-8"))
            self.assertIn(report["academicQA"],("FAIL","REVIEW_REQUIRED"))
            self.assertEqual(digest,report["artifactSha256"])

    def test_public_publisher_missing_state_receipt_directory_fails_before_remote(self):
        from app_generator.publishing.public import PublicPagesPublisher
        with tempfile.TemporaryDirectory() as tmp:
            package=Path(tmp)/"package.json"
            package.write_text("{}",encoding="utf-8")
            class NeverRemote(PublicPagesPublisher):
                def _run(self, arguments, *, cwd=None, check=True):
                    raise AssertionError("no remote publication commands permitted")
            config=SimpleNamespace(repo_root=ROOT)
            with self.assertRaisesRegex(Exception, "state_dir"):
                NeverRemote(config).publish(
                    package_path=package,subchapter_id="9.4",ensure_lease=lambda: None,
                )

    def test_verifier_failure_is_fail_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            package=Path(tmp)/"package.json"
            package.write_text("{}",encoding="utf-8")
            with patch("app_generator.runtime.academic_release.academic_triage",side_effect=ValueError("invalid")):
                with self.assertRaisesRegex(ValidationFailure,"could not be completed"):
                    enforce_academic_release_gate(ROOT,package,Path(tmp))

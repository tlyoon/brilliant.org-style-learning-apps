"""Current V3 public-release gates: autonomous AI, never manual signoff.

Historical V2 frozen acceptance regressions live in the separate V2 tests;
these tests enforce the NEW current release route and fail-closed behavior.
"""
from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import hashlib
import json
import unittest

from app_generator.errors import ValidationFailure
from app_generator.runtime.academic_release import (
    enforce_academic_release_gate, public_release_requested,
)
from app_generator.validation.autonomous_completion import (
    assess_with_models, seal_private_release_receipt,
)
from tests.test_autonomous_completion_v3 import _raw, sessions, checks

ROOT=Path(__file__).resolve().parents[1]


class AcademicPublicationGateTests(unittest.TestCase):
    def test_merge_and_deploy_are_automatic_actions_but_no_unverified_release(self):
        self.assertFalse(public_release_requested(SimpleNamespace(
            git_publish=True,git_create_draft_pr=True,git_auto_merge=False,
            public_deploy=False,
        )))
        self.assertTrue(public_release_requested(SimpleNamespace(
            git_auto_merge=True,public_deploy=False)))
        self.assertTrue(public_release_requested(SimpleNamespace(
            git_auto_merge=False,public_deploy=True)))

    def test_frozen_original_requires_v3_model_evidence_not_independent_review(self):
        package=ROOT/"content/chapter-9/section-9-4/package.json"
        with TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ValidationFailure,
                                        "pending complete V3 AI"):
                enforce_academic_release_gate(ROOT,package,Path(tmp))
            self.assertEqual([],list(Path(tmp).iterdir()))

    def test_no_manual_review_or_visualplan_quota_after_valid_v3_auto_pass(self):
        raw=_raw()
        self.assertNotIn(b"visualPlan",raw)
        assessment=assess_with_models(raw,sessions(),
            generated_content_transfer_allowed=True)
        with TemporaryDirectory() as tmp:
            private=Path(tmp)
            package=private/"package.json"
            package.write_bytes(raw)
            seal_private_release_receipt(raw,assessment,checks(raw),private)
            result=enforce_academic_release_gate(ROOT,package,private)
            self.assertTrue(result["publicationAuthorized"])
            self.assertEqual("AI_ASSESSED_PASS",result["academicQA"])
            self.assertFalse(result["manualAcademicSignoffRequired"])
            self.assertFalse(result["realLearnerPilotRequired"])
            self.assertFalse(result["explicitReleaseAuthorizationRequired"])

    def test_wrong_package_digest_cannot_reuse_valid_ai_attestation(self):
        raw=_raw()
        assessment=assess_with_models(raw,sessions(),
            generated_content_transfer_allowed=True)
        with TemporaryDirectory() as tmp:
            private=Path(tmp)
            package=private/"package.json"
            package.write_bytes(raw+b" ")
            seal_private_release_receipt(raw,assessment,checks(raw),private)
            with self.assertRaisesRegex(ValidationFailure,
                                        "pending complete V3 AI"):
                enforce_academic_release_gate(ROOT,package,private)

    def test_direct_publisher_never_reaches_remote_without_v3_receipt(self):
        from app_generator.publishing.public import PublicPagesPublisher
        with TemporaryDirectory() as tmp:
            package=ROOT/"content/chapter-9/section-9-4/package.json"
            config=SimpleNamespace(repo_root=ROOT,state_dir=Path(tmp))
            class NeverRemote(PublicPagesPublisher):
                def _run(self,arguments,*,cwd=None,check=True):
                    raise AssertionError("no Git or public deployment until V3 PASS")
            with self.assertRaisesRegex(ValidationFailure,
                                        "pending complete V3 AI"):
                NeverRemote(config).publish(
                    package_path=package,subchapter_id="9.4",
                    ensure_lease=lambda:None)
            self.assertTrue(Path(tmp).is_dir())

    def test_public_publisher_missing_receipt_state_fails_before_remote(self):
        from app_generator.publishing.public import PublicPagesPublisher
        with TemporaryDirectory() as tmp:
            package=Path(tmp)/"package.json"
            package.write_bytes(_raw())
            class NeverRemote(PublicPagesPublisher):
                def _run(self,arguments,*,cwd=None,check=True):
                    raise AssertionError("no remote operation")
            with self.assertRaisesRegex(Exception,"state_dir"):
                NeverRemote(SimpleNamespace(repo_root=ROOT)).publish(
                    package_path=package,subchapter_id="9.4",
                    ensure_lease=lambda:None)

    # Historical recurrence IDs still point to these names. Their formerly
    # mandatory independent/visual contract is superseded by owner V3.
    # Keep executable checks while testing the new real automatic gate.
    def test_real_section94_blocks_unreviewed_public_release_and_saves_report(self):
        self.test_frozen_original_requires_v3_model_evidence_not_independent_review()

    def test_mocked_academic_pass_still_refuses_legacy_no_visual_plan(self):
        self.test_untrusted_handwritten_one_line_pass_receipt_is_rejected()

    def test_valid_text_first_plans_require_no_decorative_visual_quota(self):
        self.test_no_manual_review_or_visualplan_quota_after_valid_v3_auto_pass()

    def test_invalid_declared_visual_plan_cannot_bypass_release_gate(self):
        self.test_untrusted_handwritten_one_line_pass_receipt_is_rejected()

    def test_direct_public_publisher_refuses_real_unverified_section94_without_git_calls(self):
        self.test_direct_publisher_never_reaches_remote_without_v3_receipt()

    def test_untrusted_handwritten_one_line_pass_receipt_is_rejected(self):
        with TemporaryDirectory() as tmp:
            private=Path(tmp)
            package=private/"package.json"
            package.write_bytes(_raw())
            (private/"autonomous-v3-release-receipt.json").write_text(
                json.dumps({"status":"PASS","publicationAuthorized":True}),
                encoding="utf-8")
            with self.assertRaisesRegex(ValidationFailure,
                                        "pending complete V3 AI"):
                enforce_academic_release_gate(ROOT,package,private)

"""Offline-only negative controls for C3 reconciliation and C4 release readiness."""
from __future__ import annotations

from contextlib import redirect_stdout
from copy import deepcopy
import io
import json
from pathlib import Path
import tempfile
import unittest

from app_generator.validation.reconciliation_readiness import inspect_reconciliation_readiness
from scripts.audit_reconciliation_readiness import main as audit_cli


def safe_config():
    return {
        "git": {"git_publish": False, "git_auto_merge": False},
        "automation": {"public_deploy": False, "public_deploy_auto_merge": False},
    }


def synthetic_round_two():
    return {
        "schemaVersion": 1,
        "campaignId": "synthetic-reconciliation-20261104",
        "round": 2,
        "baselineGitSha": "a" * 40,
        "profileId": "university-level-physics",
        "selectionWitnessSha256": "e" * 64,
        "priorCampaign": {
            "receiptSha256": "b" * 64,
            "genericFixRegressionSha256": "c" * 64,
            "sourceSha256s": ["1" * 64, "2" * 64, "3" * 64],
        },
        "sources": [
            {"caseId": "source-mechanics", "sourceSha256": "4" * 64,
             "topicFamily": "mechanics", "declaredUnseen": True, "rightsCleared": True},
            {"caseId": "source-electricity", "sourceSha256": "5" * 64,
             "topicFamily": "electromagnetism", "declaredUnseen": True, "rightsCleared": True},
            {"caseId": "source-optics", "sourceSha256": "6" * 64,
             "topicFamily": "waves-optics", "declaredUnseen": True, "rightsCleared": True},
        ],
    }


class ReconciliationReadinessTests(unittest.TestCase):
    def audit(self, *, config=None, baseline=None, candidate=None, manifest=None, witness=None):
        return inspect_reconciliation_readiness(
            safe_config() if config is None else config,
            frozen_engine_sha=baseline or "a" * 40,
            candidate_engine_sha=candidate or "a" * 40,
            manifest=synthetic_round_two() if manifest is None else manifest,
            selection_witness_sha256="e" * 64 if witness is None else witness,
        )

    def test_matching_private_metadata_is_not_execution_approval(self):
        report = self.audit()
        self.assertEqual("OFFLINE_READY_FOR_EXTERNAL_REVIEW", report["status"])
        self.assertTrue(report["metadataReadyOnly"])
        for field in ("executionAuthorized", "publicationAuthorized",
                      "campaignReopened", "geminiAccessVerifiedHere",
                      "sourceAndBrowserEvidenceVerifiedHere",
                      "independentAcademicAcceptanceGranted"):
            self.assertFalse(report[field])

    def test_newer_code_cannot_impersonate_frozen_engine(self):
        report = self.audit(candidate="f" * 40)
        self.assertEqual("BLOCKED_OFFLINE", report["status"])
        self.assertIn("FROZEN_ENGINE_MISMATCH", report["blockers"])
        self.assertFalse(report["metadataReadyOnly"])

    def test_all_publication_controls_require_explicit_false(self):
        for section, key in (("git", "git_publish"), ("git", "git_auto_merge"),
                             ("automation", "public_deploy"),
                             ("automation", "public_deploy_auto_merge")):
            for bad in (True, "false", None):
                with self.subTest(flag=key, bad=bad):
                    cfg = safe_config()
                    cfg[section][key] = bad
                    outcome = self.audit(config=cfg)
                    self.assertIn("PUBLICATION_FLAGS_NOT_EXPLICITLY_DISABLED",
                                  outcome["blockers"])
                    self.assertFalse(outcome["executionAuthorized"])
                    self.assertIn(section + "." + key, outcome["unsafeReleaseFlags"])

    def test_missing_config_sections_are_not_safe_defaults(self):
        outcome = self.audit(config={"git": {"git_publish": False}})
        self.assertEqual("BLOCKED_OFFLINE", outcome["status"])
        self.assertEqual(3, len(outcome["unsafeReleaseFlags"]))

    def test_no_manifest_or_unpinned_witness_remains_blocked(self):
        missing = inspect_reconciliation_readiness(
            safe_config(), frozen_engine_sha="a" * 40, candidate_engine_sha="a" * 40)
        self.assertIn("PRIVATE_ROUND_TWO_MANIFEST_NOT_SUPPLIED", missing["blockers"])
        unpinned = self.audit(witness="")
        self.assertIn("SELECTION_WITNESS_NOT_PINNED", unpinned["blockers"])

    def test_wrong_round_source_or_witness_is_rejected(self):
        for change in ("round", "baselineGitSha", "selectionWitnessSha256", "sourceSha256"):
            with self.subTest(change=change):
                manifest = synthetic_round_two()
                if change == "sourceSha256":
                    manifest["sources"][0]["sourceSha256"] = "1" * 64
                elif change == "round":
                    manifest["round"] = 1
                else:
                    manifest[change] = "f" * (40 if change == "baselineGitSha" else 64)
                report = self.audit(manifest=manifest)
                self.assertIn("FROZEN_ROUND_TWO_MANIFEST_MISMATCH", report["blockers"])
                self.assertFalse(report["executionAuthorized"])

    def test_invalid_commit_identifiers_fail_before_any_external_call(self):
        for value in ("", "abc", "z" * 40, "a" * 41):
            with self.subTest(value=value), self.assertRaises(ValueError):
                inspect_reconciliation_readiness(
                    safe_config(), frozen_engine_sha=value, candidate_engine_sha="a" * 40)

    def test_tracked_publication_enabled_template_fails_closed(self):
        repo = Path(__file__).resolve().parents[1]
        stdout = io.StringIO()
        with redirect_stdout(stdout):
            status = audit_cli([
                "--config", str(repo / "config" / "configure_project.toml"),
                "--frozen-engine", "7a7b146e16d719576ef7bceea6719fa4153b4a1c",
                "--candidate-engine", "ff1e9afa12f5c94a3bad9a35ac9725043e60d680",
            ])
        self.assertEqual(2, status)
        report = json.loads(stdout.getvalue())
        self.assertEqual("BLOCKED_OFFLINE", report["status"])
        self.assertIn("FROZEN_ENGINE_MISMATCH", report["blockers"])
        self.assertIn("PUBLICATION_FLAGS_NOT_EXPLICITLY_DISABLED", report["blockers"])
        self.assertFalse(report["executionAuthorized"])
        self.assertFalse(report["publicationAuthorized"])

    def test_cli_rejects_private_metadata_inside_public_git(self):
        repo = Path(__file__).resolve().parents[1]
        stdout = io.StringIO()
        with redirect_stdout(stdout):
            status = audit_cli([
                "--config", str(repo / "config" / "configure_project.toml"),
                "--manifest", str(repo / "docs" / "recurrence_registry.json"),
                "--frozen-engine", "a" * 40,
                "--candidate-engine", "a" * 40,
            ])
        self.assertEqual(2, status)
        report = json.loads(stdout.getvalue())
        self.assertEqual("BLOCKED_INPUT", report["status"])
        self.assertFalse(report["publicationAuthorized"])


if __name__ == "__main__":
    unittest.main()

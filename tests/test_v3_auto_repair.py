"""Synthetic receipt + authentic frozen-bytes V3 automatic repair regressions.

Every response mock in this module is SYNTHETIC; only original parent package
bytes are reused. Never represent fake reviewer receipts as genuine model PASS.
"""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import tempfile
import unittest

from app_generator.runtime.v3_auto_repair import (
    _PARENT, _CANDIDATE, _approved_parent_bytes,
    _confirmed_failure, stage_known_language_repair,
)
from app_generator.validation.autonomous_completion import package_identity


REPO = Path(__file__).resolve().parents[1]
FROZEN = REPO / "content" / "chapter-9" / "section-9-2" / "package.json"
PASS = ("physicsAnswer", "visualValue", "accessibleLearnerExperience")


def synthetic_assessment(raw: bytes, *, real_fail: bool = True) -> dict:
    digest, activities = package_identity(raw)
    dimensions = {dimension: "PASS" for dimension in PASS}
    dimensions["trilingualMeaning"] = "FAIL" if real_fail else "PASS"
    return {
        "packageSha256": digest,
        "activityIds": [a["id"] for a in activities],
        "reviews": ([{"synthetic": True}] * 13) + [{
            "activityId": "act-int-iso-05",
            "status": "AI_REPAIR_REQUIRED" if real_fail else "AI_CONSENSUS_PASS",
            "reviewers": [{
                "reviewerId": f"v3-gemini-api-{role}",
                "sessionId": f"synthetic-{role}",
                "providerId": "gemini_api",
                "decision": {
                    "activityId": "act-int-iso-05",
                    "dimensions": dimensions,
                },
            } for role in ("physics", "semantics")],
        }],
    }


class AutoRepairTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.course = self.root / "content" / "chapter-9"
        section = self.course / "section-9-2"
        section.mkdir(parents=True)
        self.original = FROZEN.read_bytes()
        self.file = section / "package.json"
        self.file.write_bytes(self.original)
        self.private = self.root / "private"
        self.plan = {"publicationAuthorized": False,
                     "scriptQuarantinedSections": {"section-9-2": 2}}
        digest = sha256(self.original).hexdigest()
        self.record = (self.private / ("v3-generated-" + digest) /
                       "batches" / ("v3-assessment-" + digest + ".json"))
        self.record.parent.mkdir(parents=True)
        self.record.write_text(
            json.dumps(synthetic_assessment(self.original)), encoding="utf8")

    def test_genuine_frozen_text_and_exact_known_repair_identity(self):
        self.assertTrue(_approved_parent_bytes(self.original))
        result = stage_known_language_repair(self.course, self.private, self.plan)
        self.assertTrue(result["repairStaged"])
        self.assertEqual(result["parentSha256"], sha256(self.original).hexdigest())
        self.assertEqual(result["archivalParentSha256"], _PARENT)
        self.assertEqual(result["candidateSha256"], _CANDIDATE)
        self.assertFalse(result["publicationAuthorized"])
        self.assertEqual(self.file.read_bytes(), self.original)
        destination = (self.private / "repair-proposals" / "section-9-2" /
                       _CANDIDATE)
        self.assertTrue((destination / "package.json").is_file())
        receipt = json.loads((destination / "review-required.json").read_text())
        self.assertFalse(receipt["newModelConsensusPassClaimed"])
        self.assertFalse(receipt["parentModelVerdictModified"])
        self.assertEqual(receipt["status"], "PENDING_FRESH_GEMINI_TWO_REVIEWER_QA")

    def test_restart_stages_idempotently_without_overwriting(self):
        first = stage_known_language_repair(self.course, self.private, self.plan)
        path = (self.private / "repair-proposals" / "section-9-2" /
                first["candidateSha256"] / "package.json")
        old = path.read_bytes()
        again = stage_known_language_repair(self.course, self.private, self.plan)
        self.assertEqual(first, again)
        self.assertEqual(path.read_bytes(), old)

    def test_missing_two_reviewers_never_stages_candidate(self):
        report = json.loads(self.record.read_text())
        report["reviews"][13]["reviewers"] = report["reviews"][13]["reviewers"][:1]
        self.record.write_text(json.dumps(report), encoding="utf8")
        result = stage_known_language_repair(self.course, self.private, self.plan)
        self.assertEqual(result["repairStatus"], "STOP_NO_GENUINE_REVIEW_EVIDENCE")
        self.assertFalse(result["repairStaged"])
        self.assertFalse((self.private / "repair-proposals").exists())

    def test_model_pass_cannot_trigger_language_repair(self):
        self.record.write_text(
            json.dumps(synthetic_assessment(self.original, real_fail=False)),
            encoding="utf8")
        result = stage_known_language_repair(self.course, self.private, self.plan)
        self.assertEqual(result["repairStatus"], "STOP_NO_GENUINE_REVIEW_EVIDENCE")
        self.assertFalse(result["repairStaged"])

    def test_missing_source_defect_or_parent_hash_changed_stops(self):
        self.file.write_bytes(self.original + b" ")
        result = stage_known_language_repair(self.course, self.private, self.plan)
        self.assertEqual(result["repairStatus"], "STOP_UNRECOGNIZED_PARENT")
        self.assertFalse(result["repairStaged"])
        self.assertFalse((self.private / "repair-proposals").exists())

    def test_different_or_unregistered_failure_does_not_guess_a_repair(self):
        self.plan["scriptQuarantinedSections"] = {"section-9-2": 3}
        result = stage_known_language_repair(self.course, self.private, self.plan)
        self.assertEqual(result["repairStatus"], "STOP_UNKNOWN_SCRIPT_DEFECT")
        self.assertFalse(result["repairStaged"])
        self.plan["scriptQuarantinedSections"] = {"section-9-6": 2}
        result = stage_known_language_repair(self.course, self.private, self.plan)
        self.assertEqual(result["repairStatus"], "NO_MATCHING_SCRIPT_REPAIR")

    def test_corrupt_private_candidate_does_not_silently_replace(self):
        result = stage_known_language_repair(self.course, self.private, self.plan)
        path = (self.private / "repair-proposals" / "section-9-2" /
                result["candidateSha256"] / "review-required.json")
        path.write_text("{}")
        with self.assertRaisesRegex(ValueError, "IDENTITY_CONFLICT"):
            stage_known_language_repair(self.course, self.private, self.plan)

    def test_forged_review_decision_is_rejected(self):
        report = json.loads(self.record.read_text())
        report["reviews"][13]["reviewers"][0]["decision"]["dimensions"][
            "trilingualMeaning"] = "PASS"
        self.record.write_text(json.dumps(report), encoding="utf8")
        self.assertFalse(_confirmed_failure(self.private, self.original))
        self.assertFalse(stage_known_language_repair(
            self.course, self.private, self.plan)["repairStaged"])


    def test_foreign_reviewer_provider_cannot_authorize_auto_repair(self):
        report = json.loads(self.record.read_text())
        report["reviews"][13]["reviewers"][1]["providerId"] = "chatgpt_browser"
        self.record.write_text(json.dumps(report), encoding="utf8")
        self.assertFalse(_confirmed_failure(self.private, self.original))
        self.assertFalse(stage_known_language_repair(
            self.course, self.private, self.plan)["repairStaged"])
        self.assertFalse((self.private / "repair-proposals").exists())

    def test_only_whole_file_lf_crlf_archival_equivalence(self):
        normalized = self.original.replace(b"\r\n", b"\n")
        other = (normalized if normalized != self.original else
                 normalized.replace(b"\n", b"\r\n"))
        self.assertNotEqual(other, self.original)
        self.assertTrue(_approved_parent_bytes(other))
        self.file.write_bytes(other)
        digest = sha256(other).hexdigest()
        record = (self.private / ("v3-generated-" + digest) /
                  "batches" / ("v3-assessment-" + digest + ".json"))
        record.parent.mkdir(parents=True, exist_ok=True)
        record.write_text(json.dumps(synthetic_assessment(other)), encoding="utf8")
        result = stage_known_language_repair(self.course, self.private, self.plan)
        self.assertTrue(result["repairStaged"])
        self.assertEqual(result["parentSha256"], digest)
        self.assertEqual(result["archivalParentSha256"], _PARENT)
        self.assertEqual(result["candidateSha256"], _CANDIDATE)

    def test_mixed_line_endings_are_not_a_valid_frozen_candidate(self):
        raw = self.original
        edited = (raw.replace(b"\r\n", b"\n", 1)
                  if b"\r\n" in raw else raw.replace(b"\n", b"\r\n", 1))
        self.file.write_bytes(edited)
        self.assertFalse(_approved_parent_bytes(edited))
        result = stage_known_language_repair(self.course, self.private, self.plan)
        self.assertEqual(result["repairStatus"], "STOP_UNRECOGNIZED_PARENT")
        self.assertFalse(result["repairStaged"])

if __name__ == "__main__":
    unittest.main()

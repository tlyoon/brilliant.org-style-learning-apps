"""Source-free, independent two-Gemini QA preparation for a revised V3 activity.

These are NOT Gemini reviewers and do not assert an accepted course.
"""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from app_generator.runtime.v3_auto_repair import (
    _ACTIVITY, _CANDIDATE, _CHANGES,
)
from app_generator.runtime.v3_repair_review_handoff import (
    stage_changed_activity_review_handoff,
)
from app_generator.validation.v3_versioned_text_repair import (
    make_locale_repair, store_private_repair,
)

SOURCE = (Path(__file__).resolve().parents[1] / "content" / "chapter-9" /
          "section-9-2" / "package.json")


class VersionedHandoffTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.course = self.root / "content" / "chapter-9"
        sec = self.course / "section-9-2"
        sec.mkdir(parents=True)
        self.parent_raw = SOURCE.read_bytes()
        self.source = sec / "package.json"
        self.source.write_bytes(self.parent_raw)
        self.private = self.root / "private"
        self.candidate = None
        self.prepare()

    def prepare(self):
        output, receipt = make_locale_repair(
            self.source.read_bytes(), _ACTIVITY, "ms", _CHANGES)
        self.candidate = store_private_repair(
            self.private / "repair-proposals" / "section-9-2",
            output, receipt)
        self.assertEqual(self.candidate.name, _CANDIDATE)

    def run_handoff(self):
        return stage_changed_activity_review_handoff(
            self.course, self.private, _CANDIDATE)

    def test_real_archived_parent_prepares_two_independent_roles_not_pass(self):
        result = self.run_handoff()
        self.assertTrue(result["handoffStaged"])
        self.assertEqual(result["requiredReviewerRoles"], 2)
        self.assertEqual(result["actualGeminiResponses"], 0)
        self.assertIs(result["wholeCourseScopeAccepted"], False)
        self.assertIs(result["publicationAuthorized"], False)
        self.assertEqual(self.source.read_bytes(), self.parent_raw)
        manifest = json.loads((
            self.private / "review-handovers" / _CANDIDATE /
            "review-handoff.json").read_text(encoding="utf8"))
        self.assertEqual([row["reviewerRole"] for row in manifest["rows"]],
                         ["physics", "semantics"])
        self.assertEqual({row["activityId"] for row in manifest["rows"]},
                         {_ACTIVITY})
        self.assertEqual(len({row["rowSha256"] for row in manifest["rows"]}), 2)
        self.assertEqual(len(manifest["requiredDimensions"]), 4)
        self.assertFalse(manifest["wholeCourseScopeAccepted"])
        self.assertFalse(manifest["publicationAuthorized"])
        self.assertNotIn("kereta luncur", json.dumps(manifest))
        self.assertNotIn("api_key", json.dumps(manifest))

    def test_restart_idempotent_final_handoff(self):
        first = self.run_handoff()
        raw = (self.private / "review-handovers" / _CANDIDATE /
               "review-handoff.json").read_bytes()
        second = self.run_handoff()
        self.assertEqual(first, second)
        self.assertEqual(raw, (
            self.private / "review-handovers" / _CANDIDATE /
            "review-handoff.json").read_bytes())

    def test_tampered_final_handoff_is_not_overwritten(self):
        self.run_handoff()
        target = self.private / "review-handovers" / _CANDIDATE / "review-handoff.json"
        target.write_text("{}")
        with self.assertRaisesRegex(ValueError, "EXISTING_MANIFEST_CONFLICT"):
            self.run_handoff()

    def test_crash_before_atomic_promotion_then_restart(self):
        final = self.private / "review-handovers" / _CANDIDATE
        with patch(
                "app_generator.runtime.v3_repair_review_handoff.Path.rename",
                side_effect=OSError("synthetic power loss during promotion")):
            with self.assertRaisesRegex(OSError, "synthetic power loss"):
                self.run_handoff()
        self.assertFalse(final.exists())
        self.assertEqual(self.run_handoff()["actualGeminiResponses"], 0)
        self.assertTrue((final / "review-handoff.json").is_file())

    def test_unexpected_changed_candidate_rejected(self):
        (self.candidate / "package.json").write_bytes(
            (self.candidate / "package.json").read_bytes() + b"\n")
        with self.assertRaisesRegex(ValueError, "CANDIDATE_CHANGED"):
            self.run_handoff()

    def test_modified_parent_rejected_without_new_scope(self):
        self.source.write_bytes(self.parent_raw + b"\n")
        with self.assertRaisesRegex(ValueError, "PARENT_NOT_FROZEN"):
            self.run_handoff()

    def test_tampered_private_repair_receipt_rejected(self):
        target = self.candidate / "review-required.json"
        data = json.loads(target.read_text(encoding="utf8"))
        data["newModelConsensusPassClaimed"] = True
        target.write_text(json.dumps(data), encoding="utf8")
        with self.assertRaisesRegex(ValueError, "UNTRUSTED_REPAIR_RECEIPT"):
            self.run_handoff()

    def test_other_whole_file_line_endings_same_content_same_handoff(self):
        original = self.parent_raw
        alternate = (original.replace(b"\r\n", b"\n")
                     if b"\r\n" in original else
                     original.replace(b"\n", b"\r\n"))
        self.assertNotEqual(sha256(alternate).hexdigest(),
                            sha256(original).hexdigest())
        self.source.write_bytes(alternate)
        # A receipt tied to the previous local byte representation may not
        # be silently relabeled. The new host must stage a matching receipt.
        with self.assertRaisesRegex(ValueError, "UNTRUSTED_REPAIR_RECEIPT"):
            self.run_handoff()
        self.private = self.root / "other-os-private"
        self.prepare()
        self.assertEqual(self.run_handoff()["candidateSha256"], _CANDIDATE)

    def test_mixed_line_endings_do_not_pass_frozen_identity(self):
        original = self.parent_raw
        altered = (original.replace(b"\r\n", b"\n", 1)
                   if b"\r\n" in original else
                   original.replace(b"\n", b"\r\n", 1))
        self.source.write_bytes(altered)
        with self.assertRaisesRegex(ValueError, "PARENT_NOT_FROZEN"):
            self.run_handoff()

    def test_unknown_candidate_sha_never_staged(self):
        with self.assertRaisesRegex(ValueError, "UNAUTHORIZED_SCOPE"):
            stage_changed_activity_review_handoff(
                self.course, self.private, "0"*64)
        self.assertFalse((self.private / "review-handovers").exists())


if __name__ == "__main__":
    unittest.main()

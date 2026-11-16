"""Regression tests for exact-scope V3 revised-activity review isolation.

The two generated replies below are SYNTHETIC test fixtures, not Gemini data.
The existing V3 assessor/checkpoint engine must process only one changed
activity and must not repeat completed role claims after restart.
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
from app_generator.runtime.v3_isolated_repair_review import (
    stage_isolated_review_slice, verify_isolated_review_slice,
)
from app_generator.validation.autonomous_completion import (
    package_identity, make_prompt,
)
from app_generator.validation.autonomous_ai_review import ReviewerSession
from app_generator.validation.v3_versioned_text_repair import (
    make_locale_repair, store_private_repair,
)
from app_generator.runtime.v3_authorized_review import advance_v3_generated_text

SOURCE = (Path(__file__).resolve().parents[1] / "content" / "chapter-9" /
          "section-9-2" / "package.json")
FIELDS = ("physicsAnswer", "trilingualMeaning", "visualValue",
          "accessibleLearnerExperience")


class FakeGeminiConversation:
    def __init__(self):
        self.calls = 0

    def ask(self, prompt, *, stage):
        self.calls += 1
        return json.dumps({
            "activityId": _ACTIVITY,
            "dimensions": {field: "PASS" for field in FIELDS},
            "rationales": {field: "SYNTHETIC test pass showing the validation "
                           "and role-checkpoint pipeline only." for field in FIELDS},
            "counterexample": "SYNTHETIC carefully considered counterexample",
            "concern": "",
        })


class IsolatedReviewSliceTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.course = self.root / "content" / "chapter-9"
        section = self.course / "section-9-2"
        section.mkdir(parents=True)
        self.source = section / "package.json"
        self.parent = SOURCE.read_bytes()
        self.source.write_bytes(self.parent)
        self.private = self.root / "private"
        corrected, receipt = make_locale_repair(
            self.parent, _ACTIVITY, "ms", _CHANGES)
        self.corrected = corrected
        self.candidate = store_private_repair(
            self.private / "repair-proposals" / "section-9-2",
            corrected, receipt)

    def stage(self):
        return stage_isolated_review_slice(self.course, self.private, _CANDIDATE)

    def test_one_changed_activity_without_parent_replay(self):
        result = self.stage()
        self.assertEqual(result["activityCount"], 1)
        self.assertEqual(result["reviewerCountRequired"], 2)
        self.assertEqual(result["actualGeminiResponses"], 0)
        self.assertEqual(result["sourcePackageSha256"], _CANDIDATE)
        self.assertFalse(result["wholeCourseScopeAccepted"])
        self.assertFalse(result["publicationAuthorized"])
        raw = verify_isolated_review_slice(
            self.course, self.private, _CANDIDATE, result["reviewSliceSha256"])
        sha, activities = package_identity(raw)
        self.assertEqual(sha, result["reviewSliceSha256"])
        self.assertEqual([a["id"] for a in activities], [_ACTIVITY])
        self.assertNotEqual(sha, _CANDIDATE)
        self.assertEqual(self.source.read_bytes(), self.parent)
        manifest = json.loads((
            self.private / "single-activity-review-slices" / sha /
            "review-slice.json").read_text(encoding="utf8"))
        self.assertEqual(
            [row["role"] for row in manifest["reviewRows"]],
            ["physics", "semantics"])
        self.assertEqual([
            row["promptSha256"] for row in manifest["reviewRows"]],
            [sha256(make_prompt(activities[0], perspective).encode("utf8")).hexdigest()
             for perspective in ("physics-adversary",
                                 "language-and-learner-adversary")])
        self.assertEqual(manifest["modelRequestsSubmitted"], 0)

    def test_idempotent_staging_and_wrong_identity_stops(self):
        first = self.stage()
        second = self.stage()
        self.assertEqual(first, second)
        with self.assertRaisesRegex(ValueError, "WRONG_REVIEW_IDENTITY"):
            verify_isolated_review_slice(
                self.course, self.private, _CANDIDATE, "0"*64)

    def test_changed_source_fails_closed(self):
        self.source.write_bytes(self.parent+b"\n")
        with self.assertRaisesRegex(ValueError, "PARENT_NOT_FROZEN"):
            self.stage()

    def test_corrupt_slice_private_package_conflict(self):
        result = self.stage()
        f = (self.private / "single-activity-review-slices" /
             result["reviewSliceSha256"] / "package.json")
        f.write_bytes(f.read_bytes() + b"\n")
        with self.assertRaisesRegex(ValueError, "EXISTING_IDENTITY_CONFLICT"):
            self.stage()

    def test_partial_write_crash_does_not_publish_candidate(self):
        with patch("app_generator.runtime.v3_isolated_repair_review.Path.rename",
                   side_effect=OSError("synthetic crash before promotion")):
            with self.assertRaisesRegex(OSError, "synthetic crash"):
                self.stage()
        self.assertEqual(len(list((self.private /
            "single-activity-review-slices").glob("[a-f0-9]"*64))), 0)
        result = self.stage()
        self.assertTrue((self.private / "single-activity-review-slices" /
                         result["reviewSliceSha256"] / "package.json").is_file())

    def test_existing_gemini_engine_reviews_only_one_synthetic_activity(self):
        staged = self.stage()
        raw = verify_isolated_review_slice(
            self.course, self.private, _CANDIDATE,
            staged["reviewSliceSha256"])
        first, second = FakeGeminiConversation(), FakeGeminiConversation()
        sessions = (
            ReviewerSession("v3-gemini-api-physics", "SYNTHETIC-physics", first,
                            provider_id="gemini_api"),
            ReviewerSession("v3-gemini-api-semantics", "SYNTHETIC-semantics",
                            second, provider_id="gemini_api"),
        )
        result = advance_v3_generated_text(
            raw, sessions, private_root=self.private,
            generated_content_transfer_allowed=True, max_activities=1)
        self.assertEqual((first.calls, second.calls), (1, 1))
        self.assertEqual(result["activitiesTotal"], 1)
        self.assertEqual(result["activitiesAssessed"], 1)
        self.assertEqual(result["modelConsensusPassActivities"], 1)
        self.assertIs(result["publicationAuthorized"], False)
        # A restart against the immutable private role claims cannot resend
        # those already completed synthetic replies to a new pair of sessions.
        third, fourth = FakeGeminiConversation(), FakeGeminiConversation()
        resumed = (
            ReviewerSession("v3-gemini-api-physics", "SYNTHETIC-restarted-physics",
                            third, provider_id="gemini_api"),
            ReviewerSession("v3-gemini-api-semantics", "SYNTHETIC-restarted-semantics",
                            fourth, provider_id="gemini_api"),
        )
        again = advance_v3_generated_text(
            raw, resumed, private_root=self.private,
            generated_content_transfer_allowed=True, max_activities=1)
        self.assertEqual((third.calls, fourth.calls), (0, 0))
        self.assertEqual(again["modelConsensusPassActivities"], 1)
        self.assertEqual(self.source.read_bytes(), self.parent)

    def test_provider_authorization_gate_preserved(self):
        data = self.stage()
        raw = verify_isolated_review_slice(
            self.course, self.private, _CANDIDATE,
            data["reviewSliceSha256"])
        a, b = FakeGeminiConversation(), FakeGeminiConversation()
        pair = (
            ReviewerSession("v3-gemini-api-physics", "safe-a", a, provider_id="gemini_api"),
            ReviewerSession("v3-gemini-api-semantics", "safe-b", b, provider_id="gemini_api"),
        )
        with self.assertRaisesRegex(ValueError, "TRANSFER_NOT_ALLOWED"):
            advance_v3_generated_text(raw, pair, private_root=self.private,
                                      max_activities=1)
        self.assertEqual((a.calls, b.calls), (0, 0))


if __name__ == "__main__":
    unittest.main()

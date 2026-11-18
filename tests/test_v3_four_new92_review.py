"""BSA209: synthetic-only exact new-4 Gemini scope and adversarial recovery tests."""
from contextlib import ExitStack
from pathlib import Path
import json
import tempfile
import unittest
from unittest.mock import patch

from app_generator.runtime.v3_frozen_original_tail import _slice
from app_generator.validation.autonomous_completion import package_identity
from app_generator.runtime import v3_four_new92_review as target


class FourNew92Tests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        self.repo = root / "repo"
        self.course = self.repo / "content" / "chapter-9"
        self.source = self.course / target.SECTION / "package.json"
        self.source.parent.mkdir(parents=True)
        self.private = root / "private"
        self.private.mkdir()
        items = [
            {"id": f"mock-{i}", "type": "mcq",
             "answerKey": {"correct": "A"},
             "prompt": {"en": f"Question {i}", "ms": f"Soalan {i}",
                        "zh": f"问题{i}"}}
            for i in range(18)
        ]
        for index, name, _ in target.PINNED:
            items[index]["id"] = name
        self.original = {"activities": items}
        raw = json.dumps(self.original, sort_keys=True,
                         ensure_ascii=False).encode("utf8")
        self.source.write_bytes(raw)
        self.sha, activities = package_identity(raw)
        self.pins = tuple(
            (idx, name, _slice(self.sha, target.SECTION, idx, items[idx])[1])
            for idx, name, _ in target.PINNED
        )
        self.progress = {
            "scopeSource": "FROZEN_CANDIDATE_MANIFEST",
            "sectionsTotal": 6, "publicationAuthorized": False,
            "sectionProgress": [{
                "section": target.SECTION, "packageSha256": self.sha,
                "activitiesTotal": 18, "activitiesAssessedRows": 14,
                "modelConsensusPassActivities": 13,
                "modelRepairRequiredActivities": 1,
                "modelUncertainActivities": 0, "unreconciledRoleClaims": 0,
            }]
        }
        old = self.private / ("v3-generated-" + self.sha) / "batches"
        old.mkdir(parents=True)
        (old / ("v3-assessment-" + self.sha + ".json")).write_text(json.dumps({
            "reviews": [{"status": "AI_CONSENSUS_PASS"}] * 13 +
                       [{"status": "AI_REPAIR_REQUIRED"}]
        }), encoding="utf8")
        self.mocksummary = {
            "activitiesAssessed": 14, "modelConsensusPassActivities": 13,
            "modelRepairRequiredActivities": 1
        }

    def fixtures(self):
        s = "app_generator.runtime.v3_four_new92_review."
        return [
            patch(s + "PARENT", self.sha),
            patch(s + "PINNED", self.pins),
            patch(s + "course_readiness", return_value=self.progress),
            patch(s + "assessment_progress", return_value=self.mocksummary),
        ]

    def with_fixture(self):
        stack = ExitStack()
        self.addCleanup(stack.close)
        for fx in self.fixtures():
            stack.enter_context(fx)
        return stack

    def test_owner_authorizes_exact_eight_not_more_and_frozen_prior(self):
        approved = target.authorize_four_new(
            execute=True, transfer=True, activities=4, seconds=900)
        self.assertEqual(approved["maximumGeminiCalls"], 8)
        self.assertFalse(approved["publicationAuthorized"])
        for n, seconds in ((5, 900), (4, 901), (0, 900), (4, 5)):
            with self.subTest(n=n, seconds=seconds):
                with self.assertRaisesRegex(ValueError, "BUDGET_EXCEEDED"):
                    target.authorize_four_new(
                        execute=True, transfer=True, activities=n, seconds=seconds)
        for execute, transfer in ((False, True), (True, False)):
            with self.assertRaisesRegex(ValueError, "BOTH_FLAGS_REQUIRED"):
                target.authorize_four_new(
                    execute=execute, transfer=transfer, activities=4)
        bad = dict(target.EXPECTED)
        bad["publicationAuthorized"] = True
        fake = self.private / "tampered_authority.json"
        fake.write_text(json.dumps(bad), encoding="utf8")
        with self.assertRaisesRegex(ValueError, "OWNER_SCOPE_CHANGED"):
            target.authorize_four_new(
                execute=True, transfer=True, activities=4, file=fake)

    def test_frozen_parent_with_prior_failure_isolated_and_four_untouched(self):
        self.with_fixture()
        entries = target.exact_four_unreviewed(self.course, self.repo, self.private)
        self.assertEqual([x["index"] for x in entries], [14, 15, 16, 17])
        self.assertTrue(all(x["originalReviewState"] ==
                            "UNREVIEWED_ELIGIBLE" for x in entries))
        self.assertEqual(self.source.read_bytes(),
                         json.dumps(self.original, sort_keys=True,
                                    ensure_ascii=False).encode("utf8"))

    def test_historical_original_role_is_never_replayed(self):
        self.with_fixture()
        role = (self.private / ("v3-generated-" + self.sha) / "batches" /
                f"v3-review-{self.sha[:12]}-014-0.json")
        role.write_text("{}", encoding="utf8")
        with self.assertRaisesRegex(ValueError, "NO_REPLAY"):
            target.exact_four_unreviewed(self.course, self.repo, self.private)

    def test_modified_source_or_saved_failed_verdict_is_rejected(self):
        self.with_fixture()
        self.source.write_bytes(self.source.read_bytes() + b" ")
        with self.assertRaisesRegex(ValueError, "INVENTORY_CHANGED"):
            target.exact_four_unreviewed(self.course, self.repo, self.private)
        self.source.write_bytes(self.source.read_bytes()[:-1])
        saved = (self.private / ("v3-generated-" + self.sha) / "batches" /
                 ("v3-assessment-" + self.sha + ".json"))
        old = json.loads(saved.read_text(encoding="utf8"))
        old["reviews"][-1]["status"] = "AI_CONSENSUS_PASS"
        saved.write_text(json.dumps(old), encoding="utf8")
        with self.assertRaisesRegex(ValueError, "OLD_SCIENTIFIC_FAILURE_CHANGED"):
            target.exact_four_unreviewed(self.course, self.repo, self.private)

    def test_immutable_source_slice_stage_idempotent_and_tamper_stop(self):
        self.with_fixture()
        entry = target.exact_four_unreviewed(self.course, self.repo, self.private)[0]
        target.stage_exact_one(self.private, entry)
        target.stage_exact_one(self.private, entry)
        staging = self.private / "four-new-original92-slices" / entry["sha"]
        (staging / "package.json").write_text("forged", encoding="utf8")
        with self.assertRaisesRegex(ValueError, "IDENTITY_CHANGED"):
            target.stage_exact_one(self.private, entry)

    def test_fake_callback_cannot_become_saved_genuine_gemini_pass(self):
        self.with_fixture()
        calls = []
        with patch.object(target, "verified_new_provider_capability", return_value=True):
            with self.assertRaisesRegex(ValueError, "MISSING_DURABLE_ASSESSMENT"):
                target.advance_four_new(
                    self.course, self.repo, self.private, execute=True,
                    transfer=True, max_activities=4,
                    capability={"sourceFree": True},
                    review_one=lambda raw, activity, private: (
                        calls.append(activity) or {"activitiesAssessed": 1,
                            "modelConsensusPassActivities": 1,
                            "modelRepairRequiredActivities": 0,
                            "modelUncertainActivities": 0}))
        self.assertEqual(len(calls), 1)

    def test_batch_has_at_most_four_isolated_reviews_and_eight_roles(self):
        self.with_fixture()
        calls = []
        positive = {"pass": True, "repair": False, "uncertain": False}
        with patch.object(target, "verified_new_provider_capability", return_value=True):
            with patch.object(target, "verify_persisted_two_role_science",
                              return_value=positive):
                result = target.advance_four_new(
                    self.course, self.repo, self.private, execute=True,
                    transfer=True, max_activities=4, max_seconds=900,
                    capability={"sourceFree": True},
                    review_one=lambda raw, activity, private: (
                        calls.append(activity) or {"activitiesAssessed": 1}))
        self.assertEqual(result["status"], "NEW4_AUTHORIZED_BATCH_COMPLETED")
        self.assertEqual(result["maximumGeminiCalls"], 8)
        self.assertEqual(len(calls), 4)
        self.assertTrue(result["allNewScientificPass"])

    def test_one_uncertain_saves_old_claim_and_stops_further_new_work(self):
        self.with_fixture()
        calls = []
        uncertain = {"pass": False, "repair": False, "uncertain": True}
        with patch.object(target, "verified_new_provider_capability", return_value=True):
            with patch.object(target, "verify_persisted_two_role_science",
                              return_value=uncertain):
                result = target.advance_four_new(
                    self.course, self.repo, self.private, execute=True,
                    transfer=True, max_activities=4,
                    capability={"sourceFree": True},
                    review_one=lambda raw, activity, private: (
                        calls.append(activity) or {"activitiesAssessed": 1}))
        self.assertEqual(len(calls), 1)
        self.assertEqual(result["status"], "NEW4_STOPPED_AT_REVIEW_BOUNDARY")
        self.assertFalse(result["allNewScientificPass"])

    def test_restart_reconciles_previous_completed_slice_without_another_call(self):
        self.with_fixture()
        first_sha = self.pins[0][2]
        (self.private / ("v3-generated-" + first_sha)).mkdir()
        calls = []
        positive = {"pass": True, "repair": False, "uncertain": False}
        with patch.object(target, "verified_new_provider_capability", return_value=True):
            with patch.object(target, "verify_persisted_two_role_science",
                              return_value=positive):
                with patch.object(target, "read_prior_two_role_science",
                                  return_value=positive):
                    result = target.advance_four_new(
                        self.course, self.repo, self.private, execute=True,
                        transfer=True, max_activities=4,
                        capability={"sourceFree": True},
                        review_one=lambda raw, activity, private: (
                            calls.append(activity) or {"activitiesAssessed": 1}))
        self.assertEqual(len(calls), 3)
        self.assertTrue(result["outcomes"][0]["reusedPreviouslyVerifiedRoles"])

    def test_scientific_failure_never_triggers_browser_as_all_pass(self):
        data = {"status": "NEW4_AUTHORIZED_BATCH_COMPLETED",
                "outcomes": [{"index": i, "reviewSliceSha256": sha,
                              "newConsensusPass": True, "newUncertain": False,
                              "newScientificRepairRequired": False}
                             for i, _, sha in target.PINNED],
                "allNewScientificPass": True, "publicationAuthorized": False,
                "versionedScopeAdmitted": False}
        data["outcomes"][2]["newConsensusPass"] = False
        data["outcomes"][2]["newScientificRepairRequired"] = True
        output = target.continue_four_to_browser(
            data, lambda: self.fail("science failure must stop local promotion"))
        self.assertEqual(output["status"], "NEW4_STOP_CHANGED_SCIENCE_EVIDENCE")

    def test_verified_four_science_passes_trigger_bounded_local_browser(self):
        data = {"status": "NEW4_AUTHORIZED_BATCH_COMPLETED",
                "outcomes": [{"index": i, "reviewSliceSha256": sha,
                              "newConsensusPass": True, "newUncertain": False,
                              "newScientificRepairRequired": False}
                             for i, _, sha in target.PINNED],
                "allNewScientificPass": True, "publicationAuthorized": False,
                "versionedScopeAdmitted": False}
        calls = []
        good = {"section96ScienceIntegrated": True,
                "paidGeminiCalls": 0, "publicationAuthorized": False,
                "versionedScopeAdmitted": False,
                "proposalSha256": "a" * 64,
                "realCandidateBrowserAcceptance": {
                    "status": "ACTUAL_UNADMITTED_CHAPTER9_BROWSER_QA_PASS",
                    "proposalSha256": "a" * 64,
                    "activitiesInCandidate": 108, "all108ActivitiesVisited": True,
                    "renderedChecks": 698, "allLocaleViewportPromptChecks": 648,
                    "publicationAuthorized": False,
                    "integritySha256": "b" * 64,
                }}
        result = target.continue_four_to_browser(
            data, lambda: calls.append("browser") or good)
        self.assertEqual(calls, ["browser"])
        self.assertEqual(result["status"], "NEW4_AUTOMATICALLY_ADVANCED_108_BROWSER_PASS")
        self.assertEqual(result["paidGeminiCalls"], 0)
        bad = json.loads(json.dumps(good))
        bad["realCandidateBrowserAcceptance"]["renderedChecks"] = 697
        output = target.continue_four_to_browser(data, lambda: bad)
        self.assertEqual(output["status"], "NEW4_STOP_UNVERIFIED_BROWSER")


if __name__ == "__main__":
    unittest.main()

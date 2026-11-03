"""Adversarial, source-free tests for exact-version academic receipt reconciliation."""
from __future__ import annotations
from copy import deepcopy
from hashlib import sha256
import json
import unittest

from app_generator.validation.academic_evidence_inventory import reconcile_evidence, GATES


class EvidenceInventoryTests(unittest.TestCase):
    SOURCE = "0" * 64
    PACKAGE = "1" * 64

    def setUp(self):
        self.package = {"activities": []}
        self.matrix = {"sourceSha256": self.SOURCE, "packageSha256": self.PACKAGE,
                       "activityCount": 18, "academicQA": "REVIEW_REQUIRED",
                       "publicationAuthorized": False,
                       "counts": {"PASS": 0, "FAIL": 0, "REVIEW_REQUIRED": 18},
                       "activities": []}
        for n in range(18):
            aid = f"activity-{n:02d}"
            act = {"id": aid, "type": "mcq" if n < 9 else "ordering",
                   "question": {"en": f"Original {n}"}}
            if n < 9:
                act["answerKey"] = {
                    "correct": "option-0",
                    "options": [
                        {"id": f"option-{m}",
                         "label": {"en": f"Question {n} answer {m}",
                                   "ms": f"Soalan {n} jawapan {m}",
                                   "zh": f"题目{n}答案{m}"}}
                        for m in range(4)]}
            elif n < 14:
                act["visualSpec"] = {"kind": "synthetic-test-only"}
            self.package["activities"].append(act)
            digest = sha256(json.dumps(act, sort_keys=True, ensure_ascii=False,
                                       separators=(",", ":")).encode()).hexdigest()
            self.matrix["activities"].append({
                "activityId": aid, "activitySha256": digest, "type": act["type"],
                "sourceLocationVerified": True,
                "academicQA": "REVIEW_REQUIRED",
                "gates": {g: "REVIEW_REQUIRED" for g in GATES},
                "publicationAuthorized": False})

    def run_inventory(self, reports=None):
        return reconcile_evidence(self.matrix, reports=reports or {},
                                  expected_source_sha256=self.SOURCE,
                                  expected_package_sha256=self.PACKAGE,
                                  exact_package=self.package)

    def make_mcq(self):
        opts = []
        for n in range(9):
            for m in range(4):
                opts.append({
                    "activityId": f"activity-{n:02d}", "optionId": f"option-{m}",
                    "status": ("BOUNDED_PHYSICS_SUPPORT" if m == 0
                               else "BOUNDED_PHYSICS_COUNTEREXAMPLE"),
                    "exactMultilingualLabelSha256": sha256(json.dumps(
                        self.package["activities"][n]["answerKey"]["options"][m]["label"],
                        sort_keys=True, ensure_ascii=False,
                        separators=(",", ":")).encode("utf-8")).hexdigest(),
                    "scientificMeaningFullyVerified": False,
                    "translationMeaningVerified": False,
                    "sourceFigureInterpretationVerified": False})
        return {"status": "SOURCE_BOUND_MC_Q_BOUNDED_STATEMENT_AUDIT",
                "sourceSha256": self.SOURCE, "packageSha256": self.PACKAGE,
                "academicQA": "REVIEW_REQUIRED", "publicationAuthorized": False,
                "originalSourceActivityPassagesReverified": 18,
                "mcqActivitiesChecked": 9,
                "threeLanguageOptionLabelsBoundBySha256": 36,
                "boundedAnswerOptionsSupported": 9,
                "boundedDistractorsCounterexampled": 27,
                "sourceFigureContactSemanticsPending": 0,
                "allOptionMeaningsFullyVerified": False,
                "translationMeaningVerified": False,
                "originalFigureScientificMeaningAutomaticallyApproved": False,
                "independentAcademicReviewerAccepted": False,
                "formalAcademicPASS": 0, "optionChecks": opts}

    def make_collision(self):
        return {"status": "SOURCE_BOUND_EXACT_COLLISION_PROPERTY_GRID_ONLY",
                "sourceSha256": self.SOURCE, "packageSha256": self.PACKAGE,
                "academicQA": "REVIEW_REQUIRED", "publicationAuthorized": False,
                "originalSourceActivitiesReverified": 18,
                "mcqAnswerIdRostersChecked": 9, "mcqOptionIdentifiersChecked": 36,
                "interactionAnswerModelsCompared": 9, "formalAcademicPASS": 0}

    def make_visual(self):
        rows = []
        for n in range(18):
            yes = n < 5
            rows.append({"activityId": f"activity-{n:02d}",
                         "academicQA": "REVIEW_REQUIRED", "publicationAuthorized": False,
                         "visualSpecPresent": yes,
                         "technicalPixelIntegrityVerified": yes,
                         "technicalVisualCapturesVerified": 6 if yes else 0,
                         "scientificVisualSemanticsVerified": False,
                         "trilingualVisualMeaningVerified": False})
        return {"status": "EXACT_SOURCE_TECHNICAL_VISUAL_COVERAGE_ONLY",
                "sourceSha256": self.SOURCE, "packageSha256": self.PACKAGE,
                "academicQA": "REVIEW_REQUIRED", "publicationAuthorized": False,
                "activityCount": 18, "screenshotCapturesVerified": 30,
                "visualActivities": 5, "scientificVisualSemanticsVerified": False,
                "formalAcademicPASSCount": 0, "activities": rows}

    def make_claims(self, pending=False):
        rows = []
        for n in range(18):
            states = {"NOT_SUBMITTED": 10}
            action = "FRESH_INDEPENDENT_REVIEW_NOT_YET_SUBMITTED"
            if pending and n == 0:
                states = {"AMBIGUOUS": 1, "NOT_SUBMITTED": 9}
                action = "RECONCILE_EXISTING_NONREPLAYABLE_CLAIMS"
            rows.append({"activityId": f"activity-{n:02d}",
                         "academicQA": "REVIEW_REQUIRED", "publicationAuthorized": False,
                         "originalSourcePassageReverified": True,
                         "reviewRunLocated": pending and n == 0,
                         "claimStates": states, "nextAction": action})
        total = {"NOT_SUBMITTED": 179, "AMBIGUOUS": 1} if pending else {"NOT_SUBMITTED": 180}
        return {"status": "EXACT_ORIGINAL_SOURCE_ACADEMIC_CLAIM_COVERAGE",
                "sourceSha256": self.SOURCE, "packageSha256": self.PACKAGE,
                "academicQA": "REVIEW_REQUIRED", "publicationAuthorized": False,
                "activityCount": 18, "sourceActivitiesReverified": 18,
                "claimRoleSlots": 180, "claimStates": total,
                "modelReviewIsFormalPass": False, "formalAcademicPASSCount": 0,
                "activities": rows}

    def test_missing_reports_remain_pending(self):
        result = self.run_inventory()
        self.assertEqual(0, result["formalAcademicPASSCount"])
        self.assertEqual(18, result["academicCounts"]["REVIEW_REQUIRED"])
        self.assertFalse(result["publicationAuthorized"])
        self.assertEqual(9, result["nextActionCounts"]["AUTO_REVERIFY_MCQ_STATEMENT_MODELS"])

    def test_all_bounded_reports_cannot_grant_pass(self):
        result = self.run_inventory({
            "mcq": self.make_mcq(), "collision": self.make_collision(),
            "visual": self.make_visual(), "claims": self.make_claims()})
        self.assertEqual([], result["missingReceiptCategories"])
        self.assertEqual(0, result["formalAcademicPASSCount"])
        self.assertEqual(18, result["nextActionCounts"][
            "AUTO_ADMIT_FRESH_INDEPENDENT_REVIEW_AFTER_READINESS_PREFLIGHT"])

    def test_different_package_or_source_rejected(self):
        for field in ("sourceSha256", "packageSha256"):
            with self.subTest(field=field):
                mutated = deepcopy(self.matrix)
                mutated[field] = "a" * 64
                with self.assertRaises(ValueError):
                    reconcile_evidence(mutated, expected_source_sha256=self.SOURCE,
                                       expected_package_sha256=self.PACKAGE,
                                       exact_package=self.package)

    def test_modified_activity_or_type_rejected(self):
        for field in ("question", "type"):
            with self.subTest(field=field):
                actual = deepcopy(self.package)
                actual["activities"][0][field] = "changed"
                with self.assertRaises(ValueError):
                    reconcile_evidence(self.matrix, exact_package=actual,
                                       expected_source_sha256=self.SOURCE,
                                       expected_package_sha256=self.PACKAGE)

    def test_duplicate_or_missing_activity_rejected(self):
        self.matrix["activities"][0] = deepcopy(self.matrix["activities"][1])
        with self.assertRaises(ValueError):
            self.run_inventory()

    def test_forged_academic_pass_rejected(self):
        self.matrix["activities"][0]["gates"]["physics_consistency"] = "PASS"
        with self.assertRaises(ValueError):
            self.run_inventory()

    def test_stale_mcq_report_rejected(self):
        report = self.make_mcq()
        report["packageSha256"] = "a" * 64
        with self.assertRaises(ValueError):
            self.run_inventory({"mcq": report})

    def test_duplicate_mcq_option_rejected(self):
        report = self.make_mcq()
        report["optionChecks"][0]["optionId"] = report["optionChecks"][1]["optionId"]
        with self.assertRaises(ValueError):
            self.run_inventory({"mcq": report})

    def test_missing_visual_capture_rejected(self):
        report = self.make_visual()
        report["activities"][0]["technicalVisualCapturesVerified"] = 5
        with self.assertRaises(ValueError):
            self.run_inventory({"visual": report})

    def test_inconsistent_reviewer_claim_count_rejected(self):
        report = self.make_claims()
        report["activities"][2]["claimStates"] = {"NOT_SUBMITTED": 9}
        with self.assertRaises(ValueError):
            self.run_inventory({"claims": report})

    def test_no_replay_takes_priority(self):
        result = self.run_inventory({"mcq": self.make_mcq(),
                                     "collision": self.make_collision(),
                                     "claims": self.make_claims(pending=True)})
        self.assertEqual("AUTO_RECONCILE_EXISTING_NONREPLAYABLE_CLAIMS_NO_RETRY",
                         result["nextActions"][0]["nextAutomaticAction"])
        self.assertTrue(result["nextActions"][0]["immutableNonReplayableReviewClaimPresent"])

    def test_four_unique_but_forged_mcq_option_id_rejected(self):
        report = self.make_mcq()
        report["optionChecks"][0]["optionId"] = "forged-option"
        with self.assertRaisesRegex(ValueError, "identity, wording"):
            self.run_inventory({"mcq": report})

    def test_valid_looking_but_wrong_multilingual_hash_rejected(self):
        report = self.make_mcq()
        report["optionChecks"][0]["exactMultilingualLabelSha256"] = "2" * 64
        with self.assertRaisesRegex(ValueError, "identity, wording"):
            self.run_inventory({"mcq": report})

    def test_swapped_answer_status_preserving_totals_rejected(self):
        report = self.make_mcq()
        report["optionChecks"][0]["status"] = "BOUNDED_PHYSICS_COUNTEREXAMPLE"
        report["optionChecks"][1]["status"] = "BOUNDED_PHYSICS_SUPPORT"
        with self.assertRaisesRegex(ValueError, "identity, wording"):
            self.run_inventory({"mcq": report})

    def test_visual_counts_cannot_be_assigned_to_wrong_activity(self):
        report = self.make_visual()
        report["activities"][0]["visualSpecPresent"] = False
        report["activities"][0]["technicalPixelIntegrityVerified"] = False
        report["activities"][0]["technicalVisualCapturesVerified"] = 0
        report["activities"][5]["visualSpecPresent"] = True
        report["activities"][5]["technicalPixelIntegrityVerified"] = True
        report["activities"][5]["technicalVisualCapturesVerified"] = 6
        with self.assertRaisesRegex(ValueError, "visualSpec"):
            self.run_inventory({"visual": report})

    def test_ambiguous_reviewer_claim_cannot_be_scheduled_as_fresh(self):
        report = self.make_claims(pending=True)
        report["activities"][0]["nextAction"] = "FRESH_INDEPENDENT_REVIEW_NOT_YET_SUBMITTED"
        with self.assertRaisesRegex(ValueError, "next action"):
            self.run_inventory({"claims": report})

    def test_boolean_count_not_accepted(self):
        report = self.make_mcq()
        report["mcqActivitiesChecked"] = True
        with self.assertRaises(ValueError):
            self.run_inventory({"mcq": report})


if __name__ == "__main__":
    unittest.main()

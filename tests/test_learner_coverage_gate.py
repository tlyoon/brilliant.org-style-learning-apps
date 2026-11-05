"""Negative controls for zero-check and metadata-only browser acceptance."""
from __future__ import annotations

import unittest
import json
from contextlib import redirect_stdout
from hashlib import sha256
import io
import tempfile
from pathlib import Path
from unittest.mock import patch
from scripts.audit_browser_visual import audit_browser
from scripts.audit_learner_coverage import main as learner_cli
from app_generator.validation.learner_coverage_gate import (
    audit_visual_browser_scope, audit_full_learner_coverage,
)


def visual(ids, mcqs, responsive, keyboard, frames, *, captured=True, errors=0):
    return audit_visual_browser_scope(
        visual_ids=ids, mcq_ids=mcqs,
        responsive_checks=responsive, keyboard_checks=keyboard,
        screenshots_captured=frames, capture_requested=captured,
        issue_count=errors,
    )


class LearnerCoverageGateTests(unittest.TestCase):
    def test_actual_browser_audit_rejects_zero_visual_scope_before_chrome(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            package=root/"empty.json"
            package.write_text(json.dumps({"activities": []}),encoding="utf-8")
            with patch("selenium.webdriver.Chrome",
                       side_effect=AssertionError("no Chrome must be launched")):
                result=audit_browser(root,package)
        self.assertEqual("fail",result["outcome"])
        self.assertEqual(0,result["visualActivities"])
        self.assertFalse(result["fullLearnerAcceptanceVerified"])

    def test_zero_visual_activities_cannot_pass_with_zero_checks(self):
        result = visual([], set(), 0, 0, 0)
        self.assertEqual("INSUFFICIENT_VISUAL_BROWSER_COVERAGE", result["status"])
        self.assertIn("NO_VISUAL_ACTIVITIES_EXERCISED", result["missing"])
        self.assertFalse(result["fullLearnerAcceptanceVerified"])

    def test_valid_visual_counters_do_not_prove_visual_quality_or_academic_pass(self):
        result = visual(["mcq-a"], {"mcq-a"}, 6, 6, 6)
        self.assertEqual("VISUAL_BROWSER_SCOPE_COMPLETE_UNREVIEWED", result["status"])
        self.assertEqual(6, result["expectedResponsiveChecks"])
        self.assertFalse(result["independentBrowserEvidenceVerified"])
        self.assertFalse(result["scientificVisualSemanticsVerified"])
        self.assertEqual("REVIEW_REQUIRED", result["academicQA"])
        self.assertFalse(result["publicationAuthorized"])

    def test_missing_responsive_keyboard_or_screenshots_fails_closed(self):
        for params,missing in (
            ((5,6,6),"RESPONSIVE_LOCALE_COVERAGE_MISSING"),
            ((6,0,6),"KEYBOARD_COVERAGE_MISSING"),
            ((6,6,0),"VISUAL_SCREENSHOTS_MISSING"),
        ):
            with self.subTest(missing=missing):
                r=visual(["mcq-a"],{"mcq-a"},*params)
                self.assertIn(missing,r["missing"])
                self.assertEqual("INSUFFICIENT_VISUAL_BROWSER_COVERAGE",r["status"])

    def test_dom_only_smoke_not_full_learner_acceptance(self):
        result=visual(["mcq-a"],{"mcq-a"},6,6,0,captured=False)
        self.assertIn("SCREENSHOT_EVIDENCE_NOT_REQUESTED", result["missing"])
        self.assertFalse(result["fullLearnerAcceptanceVerified"])

    def test_interactive_only_visual_smoke_lacks_keyboard_check(self):
        result=visual(["interactive-a"],set(),6,0,6)
        self.assertIn("KEYBOARD_COVERAGE_MISSING", result["missing"])

    def test_invalid_boolean_as_counter_or_duplicate_ids_rejected(self):
        with self.assertRaises(ValueError):
            visual(["same","same"],{"same"},12,12,12)
        with self.assertRaises(ValueError):
            visual(["mcq-a"],{"mcq-a"},True,6,6)

    def test_full_learner_coverage_rejects_empty_aggregates(self):
        package={"activities":[{"id":"mcq-a","type":"mcq"},
                               {"id":"interactive-b","type":"interactive"}]}
        result=audit_full_learner_coverage(package,{"checks":[]})
        self.assertEqual("INCOMPLETE_LEARNER_COVERAGE",result["status"])
        self.assertEqual(12,result["expectedCheckCount"])
        self.assertEqual(12,result["missingCheckCount"])
        self.assertFalse(result["interactiveLearnerAcceptanceVerified"])

    def test_full_learner_coverage_requires_every_localized_interaction(self):
        package={"activities":[{"id":"mcq-a","type":"mcq"},
                               {"id":"interactive-b","type":"interactive"}]}
        rows=[{"activityId":aid,"locale":lang,"viewportWidth":width,
               "rendered":True,"responsive":True,
               "keyboardOperable":True,"answerInteractionExercised":True}
              for aid in ("mcq-a","interactive-b")
              for lang in ("en","ms","zh") for width in (390,1280)]
        receipt=audit_full_learner_coverage(package,{"checks":rows})
        self.assertEqual("COMPLETE_COVERAGE_METADATA_UNVERIFIED",receipt["status"])
        self.assertFalse(receipt["browserObservationsIndependentlyVerified"])
        self.assertFalse(receipt["interactiveLearnerAcceptanceVerified"])
        self.assertFalse(receipt["publicationAuthorized"])
        broken=[dict(row) for row in rows]
        broken[-1]["answerInteractionExercised"]=False
        result=audit_full_learner_coverage(package,{"checks":broken})
        self.assertEqual("INCOMPLETE_LEARNER_COVERAGE",result["status"])
        self.assertEqual(1,result["failedCheckCount"])

    def test_full_learner_coverage_rejects_duplicate_or_unknown_rows(self):
        package={"activities":[{"id":"a","type":"mcq"}]}
        one={"activityId":"a","locale":"en","viewportWidth":390,
             "rendered":True,"responsive":True,"keyboardOperable":True,
             "answerInteractionExercised":True}
        with self.assertRaises(ValueError):
            audit_full_learner_coverage(package,{"checks":[one,one]})
        with self.assertRaises(ValueError):
            audit_full_learner_coverage(package,{"checks":[dict(one,activityId="evil")]})

    def test_learner_cli_rejects_aggregate_only_receipt(self):
        package={"activities":[{"id":"a","type":"mcq"}]}
        raw=json.dumps(package).encode("utf-8")
        receipt={"packageSha256":sha256(raw).hexdigest(),
                 "publicationAuthorized":False,
                 "outcome":"browser_dom_smoke_pass",
                 "checks":0,"keyboardSelectionChecks":0}
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            (root/"package.json").write_bytes(raw)
            (root/"receipt.json").write_text(json.dumps(receipt),encoding="utf-8")
            stream=io.StringIO()
            with redirect_stdout(stream):
                code=learner_cli(["--package",str(root/"package.json"),
                                  "--receipt",str(root/"receipt.json")])
        self.assertEqual(2,code)
        self.assertFalse(json.loads(stream.getvalue())["publicationAuthorized"])

    def test_nonactual_receipts_never_claim_approval(self):
        package={"activities":[{"id":"a","type":"mcq"}]}
        r=audit_full_learner_coverage(package,{"checks":[]})
        self.assertEqual("REVIEW_REQUIRED",r["academicQA"])
        self.assertTrue(r["coverageOnly"])
        self.assertFalse(r["publicationAuthorized"])


if __name__=="__main__":
    unittest.main()

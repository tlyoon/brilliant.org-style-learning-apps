"""BSA255 V27: finite formula tokenization repair and fail-closed evidence."""
from __future__ import annotations
from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from app_generator.validation import typed_scientific_semantic_alignment as core
from app_generator.validation.bounded_symbolic_qa import (
    equation_fragments,audit_bounded_symbolic_recovery,
)
from app_generator.runtime import v3_post_v26_bounded_symbolic_recovery as runtime
from app_generator.runtime.v3_native_release_adapter import _v6_checkpoint

ROOT=Path(__file__).resolve().parents[1]


class V27BoundedSymbolicTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.package=json.loads((
            ROOT/"content/chapter-9/section-9-1/package.json"
        ).read_text(encoding="utf8"))

    def test_contextual_prose_not_swallowed_as_equation_variable(self):
        self.assertEqual(equation_fragments("F=ma for all times"),["f=ma"])
        self.assertEqual(equation_fragments("p=m*v is a vector"),["p=m*v"])
        self.assertEqual(equation_fragments("K=0.5mv^2 and p=mv")[0],
                         "k=0.5mv^2")
        self.assertEqual(equation_fragments("F = dp/dt. Thus force changes"),
                         ["f=dp/dt"])

    def test_physics_variable_and_wrong_formula_stay_distinct(self):
        self.assertEqual(equation_fragments("F=ma"),["f=ma"])
        self.assertNotEqual(equation_fragments("p=m*v"),
                            equation_fragments("p=m*v^2"))
        self.assertNotEqual(equation_fragments("F=dp/dt"),
                            equation_fragments("F=p"))

    def test_actual_eighteen_explanation_surface_symbolic_inventory(self):
        result=audit_bounded_symbolic_recovery(self.package["activities"])
        self.assertEqual(result["activityCount"],18)
        original=core.audit_reusable_scientific_alignment(
            self.package["activities"])
        self.assertEqual(
            result["priorAmbiguousSymbolicFields"],
            result["boundedParserFalsePositivesResolved"]+
            result["remainingAmbiguousSymbolicFields"])
        self.assertEqual(
            result["independentRemainingPriorReviewFlags"]+
            result["boundedParserFalsePositivesResolved"],original["issues"])
        self.assertGreaterEqual(result["remainingAmbiguousSymbolicFields"],0)
        self.assertEqual(result["formalAcademicPASS"],0)
        self.assertTrue(all(row["remainingSemanticStatus"]=="REVIEW_REQUIRED"
                            for row in result["rows"]))
        self.assertTrue(all(not row["fullScientificOrTrilingualMeaningProven"]
                            for row in result["rows"]))
        self.assertEqual(result["formalAcademicPASS"],0)
        self.assertFalse(result["publicationAuthorized"])

    def test_academic_truth_must_not_be_promoted_from_literal_equivalence(self):
        result=audit_bounded_symbolic_recovery(self.package["activities"])
        result["rows"][0]["fullScientificOrTrilingualMeaningProven"]=True
        with self.assertRaisesRegex(ValueError,"FALSE_SYMBOLIC_DIAGNOSTIC"):
            runtime._compact(result)

    def test_dropped_or_forged_symbolic_row_rejected(self):
        result=audit_bounded_symbolic_recovery(self.package["activities"])
        result["rows"].pop()
        with self.assertRaisesRegex(ValueError,"FALSE_SYMBOLIC_DIAGNOSTIC"):
            runtime._compact(result)

    def test_actual_old_package_unchanged_reproducible_metadata(self):
        one=audit_bounded_symbolic_recovery(self.package["activities"])
        two=audit_bounded_symbolic_recovery(deepcopy(self.package["activities"]))
        self.assertEqual(runtime._compact(one),runtime._compact(two))
        self.assertEqual(runtime._compact(one)["rowsSha256"],
                         runtime._compact(two)["rowsSha256"])

    def test_changing_localized_content_changes_evidence_identity(self):
        one=audit_bounded_symbolic_recovery(self.package["activities"])
        changed=deepcopy(self.package["activities"])
        affected=one["rows"][0]["activityId"]
        activity=next(a for a in changed if a["id"]==affected)
        activity["prompt"]["en"]+=" injected changed source"
        new=audit_bounded_symbolic_recovery(changed)
        # Exact-source runtime rejects wrong source/candidate SHA; the generic
        # parser never promotes a changed content version by itself.
        self.assertNotEqual(one["rows"][0]["activitySha256"],
                            new["rows"][0]["activitySha256"])

    def test_no_external_api_or_original_pdf_dependency_in_generic_parser(self):
        from inspect import getsource
        src=getsource(audit_bounded_symbolic_recovery)
        self.assertNotIn("generate_content(",src)
        self.assertNotIn("models.get(",src)
        self.assertNotIn("pdf.open(",src)

    def test_unverified_v26_source_or_queue_cannot_reach_pdf(self):
        with tempfile.TemporaryDirectory() as temp:
            folder=Path(temp)
            ready={"gitHead":"a"*40,"proposalSha256":"b"*64}
            v26={"status":"FORGED","integritySha256":"z"*64}
            with (patch.object(runtime,"_preflight",
                               return_value=(folder,None,None,None,None)),
                  patch.object(runtime,"_signed",return_value=v26),
                  patch.object(runtime,"_trusted_json",
                               side_effect=AssertionError("source must not open"))):
                with self.assertRaisesRegex(ValueError,"SIGNED_V26"):
                    runtime.run_post_v26_bounded_symbolic_recovery(
                        ROOT,folder,ready,{}, {},{},v26,v26)

    def test_small_signed_restart_receipt_and_tamper(self):
        report=audit_bounded_symbolic_recovery(self.package["activities"])
        compact=runtime._compact(report)
        with tempfile.TemporaryDirectory() as root:
            file=Path(root)/runtime._V27_RESULT
            data={"gitHead":"a"*40,"proposalSha256":"b"*64,
                  **compact,"status":"BOUNDED_MATH_NO_ACADEMIC_PASS"}
            prior=_v6_checkpoint(file,data)
            self.assertLess(file.stat().st_size,12000)
            self.assertEqual(prior,_v6_checkpoint(file,data))
            wrong=dict(data);wrong["strictLiteralFormulaMatches"]=8
            with self.assertRaisesRegex(ValueError,"CHECKPOINT_CHANGED"):
                _v6_checkpoint(file,wrong)

    def test_real_worker_must_dispatch_exact_v27_and_preserve_stop(self):
        src=(ROOT/"scripts/run_v3_yoga6_recovery_worker.py").read_text(
            encoding="utf8")
        self.assertIn("run_post_v26_bounded_symbolic_recovery(",src)
        self.assertIn('result["boundedSymbolicRecovery"]',src)
        self.assertIn("V27_FIVE_FALSE_POSITIVE_SYMBOLIC_FLAGS_BOUNDED",src)


if __name__=="__main__":
    unittest.main()

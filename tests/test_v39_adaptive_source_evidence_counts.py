"""BSA267: source-signed V26/V27/V28 evidence adapts to parser counts.

A correction to the lexer must not strand downstream stages just because
historic count literals changed. A forged academic PASS or inconsistent
task arithmetic remains forbidden.
"""
from __future__ import annotations
from copy import deepcopy
import json
from pathlib import Path
from unittest import TestCase

from app_generator.validation.typed_scientific_semantic_alignment import (
    audit_reusable_scientific_alignment,
)
from app_generator.validation.bounded_symbolic_qa import audit_bounded_symbolic_recovery
from app_generator.runtime.v3_post_v26_bounded_symbolic_recovery import _compact
from app_generator.runtime.v3_post_v27_five_proof_producers import _assert_bounded_receipt

ROOT=Path(__file__).resolve().parents[1]
PKG=ROOT/"content"/"chapter-9"/"section-9-1"/"package.json"

class AdaptiveSignedProofCascade(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.activities=json.loads(PKG.read_text(encoding="utf8"))["activities"]

    def test_counts_derive_from_same_source_roster_not_prior_fixed_numbers(self):
        science=audit_reusable_scientific_alignment(self.activities)
        source=audit_bounded_symbolic_recovery(self.activities)
        result=_compact(source)
        self.assertEqual(
            result["remainingTechnicalReviewFlags"]+
            result["strictLiteralFormulaMatches"],science["issues"])
        self.assertEqual(
            result["symbolicReviewFields"],
            result["unresolvedSymbolicReviewFields"]+
            result["strictLiteralFormulaMatches"])
        self.assertFalse(result["trilingualSemanticMeaningProven"])
        self.assertEqual(result["formalAcademicPASS"],0)
        self.assertFalse(result["publicationAuthorized"])

    def test_future_internally_consistent_counts_not_bound_to_old_constants(self):
        source=deepcopy(audit_bounded_symbolic_recovery(self.activities))
        # This synthetic report is NOT signed or accepted as science. It only
        # verifies the generic arithmetic validator has no old count trap.
        extra=deepcopy(source["rows"][0])
        extra["field"]="different_synthetic_formula_field"
        extra["boundedIdenticalExplicitMath"]=True
        source["rows"].append(extra)
        source["priorAmbiguousSymbolicFields"]+=1
        source["boundedParserFalsePositivesResolved"]+=1
        compact=_compact(source)
        self.assertEqual(compact["symbolicReviewFields"],3)
        self.assertEqual(compact["strictLiteralFormulaMatches"],1)
        self.assertEqual(compact["unresolvedSymbolicReviewFields"],2)
        self.assertEqual(compact["remainingTechnicalReviewFlags"],20)
        self.assertEqual(compact["formalAcademicPASS"],0)

    def test_forged_mismatch_remains_denied(self):
        source=audit_bounded_symbolic_recovery(self.activities)
        tampered=deepcopy(source)
        tampered["boundedParserFalsePositivesResolved"]+=1
        with self.assertRaisesRegex(ValueError,"FALSE_SYMBOLIC_DIAGNOSTIC"):
            _compact(tampered)

    def test_forged_complete_science_remains_denied(self):
        source=audit_bounded_symbolic_recovery(self.activities)
        tampered=deepcopy(source)
        tampered["trilingualSemanticMeaningProven"]=True
        with self.assertRaisesRegex(ValueError,"FALSE_SYMBOLIC_DIAGNOSTIC"):
            _compact(tampered)

    def test_signed_v27_v28_math_crosscheck_is_executable(self):
        stage=(ROOT/"app_generator"/"runtime"/
               "v3_post_v27_five_proof_producers.py").read_text(encoding="utf8")
        worker=(ROOT/"scripts"/"run_v3_yoga6_recovery_worker.py").read_text(
            encoding="utf8")
        self.assertIn("_V27_RESULT",stage)
        self.assertIn(
            "BSA267_SIGNED_V27_AND_INDEPENDENT_V28_MATH_COUNTS_DISAGREE",stage)
        self.assertIn('"unresolvedTriLocaleSemanticReviewItems")',worker)
        self.assertIn('"boundedParserFalsePositivesResolved"]+',worker)
        self.assertIn('"remainingTechnicalReviewFlags"]==',worker)

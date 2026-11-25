"""BSA266: parser evidence changes must reconcile V26/V27/V28/worker.

All checks use the same immutable Serway 9.1 candidate. Missing proofs remain
REVIEW_REQUIRED; no false academic approval or auto-publication.
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
from app_generator.validation.section91_formal_physics import _SOURCE_SHA,_CANDIDATE_SHA

ROOT=Path(__file__).resolve().parents[1]
PKG=ROOT/"content"/"chapter-9"/"section-9-1"/"package.json"

class ParserRecoveryCascade(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.activities=json.loads(PKG.read_text(encoding="utf8"))["activities"]

    def test_exact_source_roster_and_counts_reconcile_across_v26_v27(self):
        language=audit_reusable_scientific_alignment(self.activities)
        result=audit_bounded_symbolic_recovery(self.activities)
        compact=_compact(result)
        self.assertEqual(language["issues"],20)
        self.assertEqual(result["priorAmbiguousSymbolicFields"],2)
        self.assertEqual(result["boundedParserFalsePositivesResolved"],0)
        self.assertEqual(result["remainingAmbiguousSymbolicFields"],2)
        self.assertEqual(result["independentRemainingPriorReviewFlags"],20)
        self.assertEqual(compact["remainingTechnicalReviewFlags"],language["issues"])
        self.assertEqual(compact["symbolicReviewFields"],2)
        self.assertEqual(compact["strictLiteralFormulaMatches"],0)
        self.assertEqual(compact["unresolvedSymbolicReviewFields"],2)
        self.assertFalse(compact["trilingualSemanticMeaningProven"])
        self.assertEqual(compact["formalAcademicPASS"],0)

    def test_forged_resolved_symbolic_issue_is_rejected(self):
        result=audit_bounded_symbolic_recovery(self.activities)
        forged=deepcopy(result)
        forged["boundedParserFalsePositivesResolved"]=1
        with self.assertRaisesRegex(ValueError,"FALSE_SYMBOLIC_DIAGNOSTIC"):
            _compact(forged)

    def test_old_26_issue_count_is_rejected(self):
        result=audit_bounded_symbolic_recovery(self.activities)
        forged=deepcopy(result)
        forged["independentRemainingPriorReviewFlags"]=21
        with self.assertRaisesRegex(ValueError,"FALSE_SYMBOLIC_DIAGNOSTIC"):
            _compact(forged)

    def test_real_source_adapter_has_no_promoted_science_pass(self):
        p=json.loads(PKG.read_text(encoding="utf8"))
        self.assertEqual(len(p["activities"]),18)
        self.assertTrue(all(a.get("visualSpec") is None for a in p["activities"]))
        self.assertEqual(len(_SOURCE_SHA),64)
        self.assertEqual(len(_CANDIDATE_SHA),64)

    def test_worker_rechecks_v27_and_v28_exact_reconciled_counts(self):
        text=(ROOT/"scripts"/"run_v3_yoga6_recovery_worker.py").read_text(encoding="utf8")
        for marker in (
            '"boundedParserFalsePositivesResolved")==0',
            '"remainingAmbiguousSymbolicFields")==2',
            '"remainingTechnicalReviewFlags")==20',
            '"privateSemanticTaskDispatch"',
        ):
            self.assertIn(marker,text)

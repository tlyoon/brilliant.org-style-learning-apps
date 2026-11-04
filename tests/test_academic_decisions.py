import unittest
from app_generator.validation.academic_qa import Finding, REQUIRED, decide

class AcademicDecisionTests(unittest.TestCase):
    def test_absent_evidence_is_review_required(self):
        result = decide([])
        self.assertEqual(result["academicQA"], "REVIEW_REQUIRED")
        self.assertEqual(set(result["gates"]), set(REQUIRED))
        self.assertFalse(result["publicationAuthorized"])

    def test_pass_requires_independent_receipt(self):
        with self.assertRaises(ValueError):
            Finding("source_fidelity", "PASS", "model_claim", "llm", "looks correct", True)
        with self.assertRaises(ValueError):
            Finding("source_fidelity", "PASS", "deterministic", "", "passed", True)
        good = [Finding(x, "PASS", "deterministic", "sha256:test", "tested", True) for x in REQUIRED]
        self.assertEqual("PASS", decide(good)["academicQA"])
        self.assertFalse(decide(good)["humanReviewed"])

    def test_failure_outweighs_missing_and_model_opinion(self):
        failure = Finding("physics_consistency", "FAIL", "deterministic", "run123", "energy mismatch")
        self.assertEqual("FAIL", decide([failure])["academicQA"])
        model = Finding("source_fidelity", "REVIEW_REQUIRED", "model_claim", "run123", "not checked")
        self.assertEqual("REVIEW_REQUIRED", decide([model])["academicQA"])
        self.assertEqual("FAIL", decide([failure, model])["academicQA"])

    def test_ambiguous_or_duplicate_requirements_fail_closed(self):
        with self.assertRaises(ValueError): decide([], ["source_fidelity", "source_fidelity"])
        with self.assertRaises(ValueError): decide([Finding("unexpected", "FAIL", "", "", "not allowed")])

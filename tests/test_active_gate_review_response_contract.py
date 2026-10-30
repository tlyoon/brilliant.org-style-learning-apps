"""Source-free academic gate response contract hardening tests."""
from __future__ import annotations

import json
import unittest

from app_generator.validation.autonomous_ai_review import (
    _evaluate_response, independent_review_prompt, RESPONSE_VALIDATION_CODES,
)

BASE = {
    "gate": "answer_correctness",
    "verdict": "SUPPORTED",
    "rationale": "The option follows conservation of momentum as described.",
    "sourcePage": 2,
    "issue": "",
}


def framed(data: dict) -> str:
    return "BEGIN_JSON\n" + json.dumps(data) + "\nEND_JSON"


class ActiveGateResponseContractTests(unittest.TestCase):
    def test_prompt_repeats_exact_current_gate_after_data_without_fake_template(self):
        activity = {"id": "case", "type": "mcq", "prompt": {"en": "Question"}}
        source = {"sourceSha256": "b"*64, "sourceEvidence": "x"*50, "verifiedPages": [2]}
        for gate in ("source_fidelity", "answer_correctness", "physics_consistency",
                     "visual_semantics", "multilingual_meaning"):
            with self.subTest(gate=gate):
                prompt = independent_review_prompt(activity, gate, source,
                                                   perspective="independent reviewer")
                self.assertIn("The current gate identifier is: "+gate, prompt)
                self.assertIn("not a gate from any previous conversation turn", prompt)
                self.assertIn("return verdict UNCERTAIN", prompt)
                self.assertNotIn("{...}", prompt)
                self.assertNotIn("publication approved", prompt)

    def test_wrong_gate_is_separate_fail_closed_reason(self):
        response = {**BASE, "gate": "source_fidelity"}
        with self.assertRaisesRegex(ValueError, "another gate") as context:
            _evaluate_response(framed(response), "answer_correctness", {2})
        self.assertEqual("MISMATCHED_GATE",
                         RESPONSE_VALIDATION_CODES[str(context.exception)])

    def test_unknown_verdict_is_separate_fail_closed_reason(self):
        response = {**BASE, "verdict": "LIKELY_CORRECT"}
        with self.assertRaisesRegex(ValueError, "invalid verdict") as context:
            _evaluate_response(framed(response), "answer_correctness", {2})
        self.assertEqual("INVALID_VERDICT",
                         RESPONSE_VALIDATION_CODES[str(context.exception)])

    def test_correct_bound_response_still_allowed_but_not_academic_pass(self):
        parsed = _evaluate_response(framed(BASE), "answer_correctness", {2})
        self.assertEqual("SUPPORTED", parsed["verdict"])
        self.assertEqual("answer_correctness", parsed["gate"])
        self.assertNotIn("academicQA", parsed)
        self.assertNotIn("publicationAuthorized", parsed)

    def test_ambiguous_verdict_remains_uncertain_not_supported(self):
        parsed = _evaluate_response(framed({**BASE, "verdict": "UNCERTAIN"}),
                                    "answer_correctness", {2})
        self.assertEqual("UNCERTAIN", parsed["verdict"])


if __name__ == "__main__":
    unittest.main()

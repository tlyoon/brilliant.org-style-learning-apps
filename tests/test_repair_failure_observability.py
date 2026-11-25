"""Source-free, generic repair diagnostics and bounded retry regressions."""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app_generator.errors import ResponseContractError
from app_generator.generation.protocol import GenerationProtocol
from app_generator.generation.repair_diagnostics import (
    StableRepairContractError, InteractionSolutionError,
    classify_repair_failure,
)
from app_generator.runtime.run_context import RunContext


class FakeConversation:
    def __init__(self, responses):
        self.responses = iter(responses)
        self.calls = 0

    def ask(self, prompt, *, stage=None):
        self.calls += 1
        return next(self.responses)


def reply(document):
    return "BEGIN_JSON\n" + json.dumps(document) + "\nEND_JSON"


def original():
    return {
        "id": "general-ordering-a", "type": "interactive", "difficulty": "easy",
        "objective": "Generic ordering", "misconceptions": ["some-misconception"],
        "interactionMode": "ordering",
        "prerequisiteRecovery": {"prerequisiteId": "prerequisite-1"},
        "interaction": {
            "items": [{"id": "first"}, {"id": "second"}],
            "correctOrder": ["first", "second"],
        },
    }


class RepairFailureObservabilityTests(unittest.TestCase):
    def test_typed_stable_violation_keeps_legacy_value_error_contract(self):
        before = original()
        after = dict(before, id="renamed")
        with self.assertRaises(StableRepairContractError) as err:
            GenerationProtocol._assert_stable_activity_contract(before, after)
        self.assertEqual("STABLE_FIELD", classify_repair_failure(err.exception)["category"])
        self.assertIsInstance(err.exception, ValueError)

    def test_distinct_interaction_completion_and_schema_categories(self):
        invalid = original()
        invalid["interaction"] = {**invalid["interaction"], "correctOrder": ["first"]}
        with self.assertRaises(InteractionSolutionError) as err:
            GenerationProtocol._assert_complete_interaction_solution(invalid)
        self.assertEqual("INTERACTION_SOLUTION",
                         classify_repair_failure(err.exception)["category"])
        self.assertEqual(
            "SCHEMA_VALIDATION",
            classify_repair_failure(ResponseContractError(
                "Activity x violates schema-1.1: unexpected field"))["category"])

    def test_exhausted_repairs_preserve_per_attempt_categories_without_raw_errors(self):
        before = original()
        bad_identity = dict(before, id="renamed")
        bad_solution = original()
        bad_solution["interaction"] = {**before["interaction"], "correctOrder": ["first"]}
        valid_but_rejected = original()
        responses = [reply(bad_identity), reply(bad_solution), reply(valid_but_rejected)]
        with tempfile.TemporaryDirectory() as tmp:
            ctx = RunContext.create(Path(tmp))
            conversation = FakeConversation(responses)
            protocol = GenerationProtocol(conversation, ctx)
            def validator(batch, plan):
                if batch["activities"][0]["id"] == before["id"] and conversation.calls == 3:
                    raise ResponseContractError(
                        "Activity general-ordering-a violates schema-1.1: SECRET_SENSITIVE_RESPONSE")
                return batch["activities"]
            with patch("app_generator.generation.protocol.validate_activity_batch",
                       side_effect=validator):
                with self.assertRaisesRegex(ResponseContractError, "categories=") as error:
                    protocol._repair_stage("repair-a", before, lambda: "source-free fixture")
            self.assertEqual(3, conversation.calls)
            self.assertNotIn("SECRET_SENSITIVE_RESPONSE", str(error.exception))
            path = ctx.diagnostics / "repair-a-repair-attempts.json"
            self.assertTrue(path.is_file())
            data = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(["STABLE_FIELD", "INTERACTION_SOLUTION", "SCHEMA_VALIDATION"],
                             [x["category"] for x in data["attempts"]])
            self.assertEqual([1, 2, 3], [x["attempt"] for x in data["attempts"]])
            self.assertEqual("general-ordering-a", data["activityId"])
            self.assertFalse(data["sourceTextStored"])
            self.assertNotIn("SECRET_SENSITIVE_RESPONSE", path.read_text(encoding="utf-8"))
            self.assertIsNone(ctx.load_stage("repair-a"))

    def test_good_repair_preserves_correction_and_failed_attempt_receipt(self):
        before = original()
        wrong = dict(before, difficulty="challenging")
        conversation = FakeConversation([reply(wrong), reply(before)])
        with tempfile.TemporaryDirectory() as tmp:
            ctx = RunContext.create(Path(tmp))
            protocol = GenerationProtocol(conversation, ctx)
            with patch("app_generator.generation.protocol.validate_activity_batch",
                       return_value=[before]):
                result = protocol._repair_stage("repair-good", before, lambda: "fixture")
            self.assertEqual(before, result)
            receipt = json.loads((ctx.diagnostics / "repair-good-repair-attempts.json").read_text())
            self.assertEqual("STABLE_FIELD", receipt["attempts"][0]["category"])
            self.assertEqual(2, conversation.calls)

    def test_classifier_never_returns_arbitrary_error_text(self):
        secret = "do-not-log-secret-account-value"
        self.assertEqual(
            {"category": "UNKNOWN_CONTRACT", "field": "unspecified"},
            classify_repair_failure(ValueError(secret)))


if __name__ == "__main__":
    unittest.main()

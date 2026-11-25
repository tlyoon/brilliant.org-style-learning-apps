"""No-network negative controls for upstream Gemini execution denials."""
from __future__ import annotations

from contextlib import redirect_stdout
import io
import json
import unittest

from app_generator.errors import ExternalExecutionDenied
from app_generator.llm.gemini_key_failover import (
    ApiKeyCandidate, select_healthy_key,
)
from app_generator.validation.gemini_execution_boundary import (
    classify_gemini_attempt,
)
from scripts.triage_gemini_execution_boundary import main as triage_cli


def event(origin, *, stage="SOURCE_FREE_PREFLIGHT", dispatch=None,
          code=None, evidence="HISTORICAL_REPORT"):
    if dispatch is None:
        dispatch = {
            "HOST_OR_CONNECTOR": "DENIED_BEFORE_EXECUTION",
            "GEMINI_PROVIDER": "STARTED",
            "LOCAL_RUNTIME": "STARTED",
            "UNKNOWN": "UNKNOWN",
        }[origin]
    return {
        "origin": origin,
        "stage": stage,
        "dispatch": dispatch,
        "providerHttpStatus": code,
        "evidence": evidence,
    }


class GeminiExecutionBoundaryTests(unittest.TestCase):
    def test_upstream_denial_is_not_gemini_http_403(self):
        output = classify_gemini_attempt(event("HOST_OR_CONNECTOR"))
        self.assertEqual("BLOCKED_EXTERNAL", output["status"])
        self.assertIsNone(output["providerHttpStatus"])
        self.assertFalse(output["keyRotationEligibleWithinExistingAuthorizedPreflight"])
        self.assertFalse(output["providerRequestMayHaveBeenSent"])
        for key in ("authorizesNewExecution", "authorizesToolRerouting",
                    "allowsSourceReplay", "unblocksExistingDeniedOperation",
                    "publicationAuthorized", "dispatchIndependentlyVerified"):
            self.assertFalse(output[key])

    def test_explicit_upstream_exception_with_403_never_rotates_key(self):
        attempts = []
        keys = (ApiKeyCandidate(label="KEY_1", secret="secret-one"),
                ApiKeyCandidate(label="KEY_2", secret="secret-two"))
        denied = ExternalExecutionDenied("tool refused dispatch")
        denied.status_code = 403  # An upstream wrapper may have set this.
        def probe(candidate):
            attempts.append(candidate.label)
            raise denied
        with self.assertRaises(ExternalExecutionDenied):
            select_healthy_key(keys, probe)
        self.assertEqual(["KEY_1"], attempts)

    def test_real_provider_http_403_is_distinct_and_rotation_eligible(self):
        result = classify_gemini_attempt(event("GEMINI_PROVIDER", code=403))
        self.assertEqual("PROVIDER_SOURCE_FREE_KEY_ROTATION_ELIGIBLE", result["status"])
        self.assertTrue(result["keyRotationEligibleWithinExistingAuthorizedPreflight"])
        self.assertFalse(result["authorizesNewExecution"])
        self.assertFalse(result["dispatchIndependentlyVerified"])

    def test_source_bearing_503_must_not_rotate(self):
        result = classify_gemini_attempt(event(
            "GEMINI_PROVIDER", stage="SOURCE_BEARING_GENERATION", code=503))
        self.assertFalse(result["keyRotationEligibleWithinExistingAuthorizedPreflight"])
        self.assertEqual("RECONCILE_ORIGINAL_REQUEST", result["safeNextAction"])
        self.assertTrue(result["providerRequestMayHaveBeenSent"])
        self.assertFalse(result["allowsSourceReplay"])

    def test_429_and_noneligible_codes_stop(self):
        quota = classify_gemini_attempt(event("GEMINI_PROVIDER", code=429))
        self.assertEqual("PROVIDER_QUOTA_STOP", quota["status"])
        self.assertFalse(quota["keyRotationEligibleWithinExistingAuthorizedPreflight"])
        error = classify_gemini_attempt(event("GEMINI_PROVIDER", code=400))
        self.assertFalse(error["keyRotationEligibleWithinExistingAuthorizedPreflight"])

    def test_unknown_execution_is_never_assumed_unsent(self):
        result = classify_gemini_attempt(event("UNKNOWN"))
        self.assertTrue(result["providerRequestMayHaveBeenSent"])
        self.assertFalse(result["authorizesNewExecution"])
        self.assertEqual("PRESERVE_EVIDENCE_AND_STOP", result["safeNextAction"])

    def test_local_runtime_error_cannot_prove_no_submission(self):
        result = classify_gemini_attempt(event("LOCAL_RUNTIME"))
        self.assertEqual("LOCAL_EXECUTION_FAILURE", result["status"])
        self.assertTrue(result["providerRequestMayHaveBeenSent"])
        self.assertFalse(result["keyRotationEligibleWithinExistingAuthorizedPreflight"])

    def test_self_described_tool_result_is_not_independent_proof(self):
        result = classify_gemini_attempt(event(
            "GEMINI_PROVIDER", code=402, evidence="TOOL_RESULT_METADATA"))
        self.assertFalse(result["dispatchIndependentlyVerified"])
        self.assertFalse(result["providerResponseIndependentlyVerified"])

    def test_bad_observation_fields_and_secret_payload_rejected(self):
        invalid = event("HOST_OR_CONNECTOR")
        invalid["apiKey"] = "secret-data"
        with self.assertRaises(ValueError):
            classify_gemini_attempt(invalid)
        for bad in (
            event("HOST_OR_CONNECTOR", code=403),
            event("GEMINI_PROVIDER", dispatch="DENIED_BEFORE_EXECUTION", code=403),
            event("GEMINI_PROVIDER"),
            event("UNKNOWN", dispatch="STARTED"),
            event("GEMINI_PROVIDER", code=True),
            event("GEMINI_PROVIDER", code=200),
        ):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                classify_gemini_attempt(bad)

    def test_metadata_only_cli_reports_without_executing(self):
        stdout = io.StringIO()
        with redirect_stdout(stdout):
            rc = triage_cli([
                "--origin", "HOST_OR_CONNECTOR",
                "--stage", "SOURCE_FREE_PREFLIGHT",
                "--dispatch", "DENIED_BEFORE_EXECUTION",
            ])
        self.assertEqual(0, rc)
        parsed = json.loads(stdout.getvalue())
        self.assertEqual("BLOCKED_EXTERNAL", parsed["status"])
        self.assertFalse(parsed["unblocksExistingDeniedOperation"])
        self.assertFalse(parsed["providerResponseIndependentlyVerified"])

    def test_metadata_only_cli_rejects_forged_http_on_denial(self):
        stdout = io.StringIO()
        with redirect_stdout(stdout):
            rc = triage_cli([
                "--origin", "HOST_OR_CONNECTOR",
                "--stage", "SOURCE_FREE_PREFLIGHT",
                "--dispatch", "DENIED_BEFORE_EXECUTION",
                "--provider-http-status", "403",
            ])
        self.assertEqual(2, rc)
        parsed = json.loads(stdout.getvalue())
        self.assertEqual("INVALID_OBSERVATION", parsed["status"])
        self.assertFalse(parsed["authorizesNewExecution"])


if __name__ == "__main__":
    unittest.main()

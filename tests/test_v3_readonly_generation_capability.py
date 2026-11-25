"""Read-only Gemini model action diagnosis: no paid generation or credentials.

Uses real SDK Model and ClientError types with a local instrumented
models.get transport. Project quota and generation eligibility are always
reported as unverified, including when both metadata requests return HTTP200.
"""
from __future__ import annotations

from types import SimpleNamespace
import unittest

from google.genai import types
from google.genai.errors import ClientError

from app_generator.runtime.v3_gemini_diagnostics import (
    diagnose_declared_generation_support,
)


class Models:
    def __init__(self, actions=None, *, code=None):
        self.actions=actions
        self.code=code
        self.get_calls=0
        self.generate_calls=0

    def get(self, *, model):
        self.get_calls+=1
        if self.code is not None:
            raise ClientError(self.code,{
                "error":{"code":self.code,
                         "message":"PRIVATE_DIAGNOSTIC_TOKEN_MUST_NOT_LOG"}})
        return types.Model(name="models/"+model,
                           supported_actions=self.actions)

    def generate_content(self, *args, **kwargs):
        self.generate_calls+=1
        raise AssertionError("NO_PAID_GENERATION_ALLOWED")


class Client:
    def __init__(self, models):
        self.models=models
        self.closed=False
    def close(self):
        self.closed=True


class ReadonlyGenerationCapabilityTests(unittest.TestCase):
    def setUp(self):
        self.config=SimpleNamespace(gemini_api_model="gemini-3.8-flash",
                                    gemini_api_timeout_seconds=1200)

    def check(self, models):
        clients=[]
        def factory(config, *, candidate_offset):
            self.assertEqual(config.gemini_api_timeout_seconds,15)
            def create(role):
                self.assertEqual(role,"physics")
                c=Client(models[candidate_offset])
                clients.append(c)
                return c
            return create,types
        result=diagnose_declared_generation_support(
            self.config,
            make_sdk_components=factory,
            count_credentials=lambda:("DUMMY_KEY_0","DUMMY_KEY_1"),
        )
        self.assertTrue(all(c.closed for c in clients))
        self.assertTrue(all(m.generate_calls==0 for m in models))
        self.assertTrue(result["sourceFree"])
        self.assertEqual(result["paidModelCalls"],0)
        self.assertFalse(result["generationPermissionVerified"])
        self.assertFalse(result["projectQuotaVerified"])
        self.assertNotIn("DUMMY_KEY",str(result))
        self.assertNotIn("PRIVATE_DIAGNOSTIC_TOKEN",str(result))
        return result,models

    def test_two_actual_sdk_metadata_models_do_not_prove_generation_access(self):
        result,models=self.check([
            Models(["generateContent","countTokens"]),
            Models(["generateContent","countTokens"]),
        ])
        self.assertEqual(result["status"],
                         "MODEL_GENERATION_ACTION_DECLARED_QUOTA_UNVERIFIED")
        self.assertEqual([m.get_calls for m in models],[1,1])
        self.assertEqual(len(result["attempts"]),2)
        self.assertEqual([item["httpStatus"] for item in result["attempts"]],
                         [200,200])
        self.assertTrue(all(item["classification"]==
                            "MODEL_DECLARES_GENERATE_CONTENT"
                            for item in result["attempts"]))

    def test_legacy_format_on_two_keys_is_warning_not_quota_proof(self):
        clients=[]
        models=[Models(["generateContent"]),Models(["generateContent"])]
        def sdk(config, *, candidate_offset):
            def open_client(role):
                result=Client(models[candidate_offset])
                clients.append(result)
                return result
            return open_client,types
        result=diagnose_declared_generation_support(
            self.config,
            make_sdk_components=sdk,
            count_credentials=lambda:(
                SimpleNamespace(secret="AIza_DO_NOT_LEAK_SYNTHETIC_A"),
                SimpleNamespace(secret="AIza_DO_NOT_LEAK_SYNTHETIC_B"),
            ))
        self.assertEqual(
            result["status"],
            "MODEL_ACTION_DECLARED_LEGACY_KEY_FORMAT_REVIEW_REQUIRED")
        self.assertEqual([m.get_calls for m in models],[1,1])
        self.assertEqual([m.generate_calls for m in models],[0,0])
        self.assertTrue(all(c.closed for c in clients))
        self.assertTrue(all(row["keyFormatHint"] ==
                            "LEGACY_STANDARD_FORMAT_HINT"
                            for row in result["attempts"]))
        self.assertFalse(result["generationPermissionVerified"])
        self.assertFalse(result["projectQuotaVerified"])
        self.assertNotIn("AIza_",str(result))

    def test_metadata_200_without_generation_action_is_not_approved(self):
        result,models=self.check([
            Models(["countTokens"]),Models(["generateContent"]),
        ])
        self.assertEqual(result["status"],"STOP_MODEL_NO_GENERATION_ACTION")
        self.assertEqual([m.get_calls for m in models],[1,0])

    def test_explicit_denial_not_bypassed_by_another_key(self):
        result,models=self.check([
            Models(code=403),Models(["generateContent"]),
        ])
        self.assertEqual(result["status"],
                         "STOP_READONLY_MODEL_METADATA_AUTH_OR_PROJECT_DENIED")
        self.assertEqual([m.get_calls for m in models],[1,0])
        self.assertEqual(result["attempts"][0]["httpStatus"],403)

    def test_quota_denial_not_bypassed_by_alternate_key(self):
        result,models=self.check([
            Models(code=429),Models(["generateContent"]),
        ])
        self.assertEqual(result["status"],
                         "STOP_READONLY_MODEL_METADATA_QUOTA_OR_RATE_LIMIT")
        self.assertEqual([m.get_calls for m in models],[1,0])

    def test_metadata_incomplete_does_not_count_as_generation_proof(self):
        result,models=self.check([Models(None),Models(["generateContent"])])
        self.assertEqual(result["status"],"STOP_MODEL_ACTIONS_NOT_REPORTED")
        self.assertEqual([m.get_calls for m in models],[1,0])

    def test_normal_worker_private_diagnostic_checkpoint_is_strict(self):
        import json
        from pathlib import Path
        import tempfile
        from app_generator.runtime.v3_yoga6_recovery import persist_status
        result, _ = self.check([
            Models(["generateContent"]), Models(["generateContent"]),
        ])
        status={
            "status":"DIAGNOSTIC_READY_SOURCE_FREE_ONLY",
            "publicationAuthorized":False,
            "generationCapabilityMetadata":result,
            "generationPermissionVerified":False,
            "projectQuotaVerified":False,
        }
        with tempfile.TemporaryDirectory() as path:
            target=persist_status(Path(path),status)
            self.assertEqual(json.loads(target.read_text(encoding="utf8")),
                             status)
            with self.assertRaisesRegex(ValueError,"CANNOT_PROVE_PERMISSION"):
                persist_status(Path(path),{
                    **status,"generationPermissionVerified":True})
            with self.assertRaisesRegex(ValueError,"UNSAFE_GENERATION_DIAGNOSTIC"):
                persist_status(Path(path),{
                    **status,"generationCapabilityMetadata":{
                        **result,"apiKey":"PRIVATE_DO_NOT_PERSIST"}})
            with self.assertRaisesRegex(ValueError,"UNSAFE_GENERATION_DIAGNOSTIC"):
                persist_status(Path(path),{
                    **status,"generationCapabilityMetadata":{
                        **result,
                        "attempts":[{"candidateIndex":0,
                                     "classification":"MODEL_DECLARES_GENERATE_CONTENT",
                                     "httpStatus":200,
                                     "rawGoogleMessage":"SECRET"}]}})
            self.assertEqual(json.loads(target.read_text(encoding="utf8")),
                             status)

    def test_budget_is_strict_and_no_keys_is_safe(self):
        with self.assertRaisesRegex(ValueError,"INVALID_READONLY_CAPABILITY_BUDGET"):
            diagnose_declared_generation_support(self.config,max_candidates=3,
                                                 count_credentials=lambda:())
        result=diagnose_declared_generation_support(
            self.config,count_credentials=lambda:())
        self.assertEqual(result["status"],"STOP_NO_GEMINI_CREDENTIAL")
        self.assertEqual(result["paidModelCalls"],0)


if __name__=="__main__":
    unittest.main()

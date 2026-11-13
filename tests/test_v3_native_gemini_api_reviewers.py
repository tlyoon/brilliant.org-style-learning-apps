"""Source-free, ChatGPT-independent V3 Gemini API reviewer regression.

All generated content and SDK responses here are SYNTHETIC.
No test imports Google's network SDK, creates credentials, or sends requests.
"""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from tests.test_v3_course_review_dispatch import synthetic_course
from tests.test_v3_authorized_execution_bridge import FakeReviewer
from app_generator.runtime.v3_course_review import advance_v3_course_review, plan_v3_course_review
from app_generator.validation.autonomous_completion import (
    load_policy, assess_with_models, verify_automated_release_assessment,
)
from app_generator.gemini.v3_native_api_reviewers import (
    V3NativeGeminiApiSessions, NativeGeminiApiConversation,
)


class FakeModels:
    def __init__(self, outcome="valid"):
        self.calls = []
        self.outcome = outcome

    def generate_content(self, *, model, contents, config):
        self.calls.append((model, contents, config))
        if self.outcome == "ambiguous":
            raise TimeoutError("synthetic ambiguous response after dispatch")
        if self.outcome == "empty":
            return SimpleNamespace(text="")
        if self.outcome == "malformed":
            return SimpleNamespace(text="{invalid")
        return SimpleNamespace(text=FakeReviewer().ask(
            contents, stage="academic-v3-autonomous"))


class FakeClient:
    def __init__(self, outcome="valid"):
        self.models = FakeModels(outcome)
        self.closed = 0

    def close(self):
        self.closed += 1


class FakeTypes:
    @staticmethod
    def GenerateContentConfig(**kwargs):
        return SimpleNamespace(**kwargs)


def config():
    return SimpleNamespace(gemini_api_model="gemini-example-flash",
                           gemini_api_timeout_seconds=15)


class V3NativeGeminiApiTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.repo = self.base/"repo"
        self.chapter = synthetic_course(self.repo, activities=2)
        self.private = self.base/"private"
        self.clients = []

    def factory(self, outcomes=("valid", "valid"), authorized=True):
        started = len(self.clients)
        def make(role):
            self.assertIn(role, ("physics", "semantics"))
            client = FakeClient(outcomes[len(self.clients) - started])
            self.clients.append(client)
            return client
        return V3NativeGeminiApiSessions(
            config(), operation_authorized=authorized,
            generated_content_transfer_allowed=True,
            sdk_client_factory=make, sdk_types=FakeTypes,
        )

    def dispatch(self, f, *, count=1, permit=True):
        return advance_v3_course_review(
            self.chapter, self.repo, private_root=self.private,
            session_factory=f, external_operation_authorized=permit,
            generated_content_transfer_allowed=True, max_activities=count)

    def test_contract_uses_only_gemini_transports_not_chatgpt(self):
        self.assertEqual(["gemini_api", "gemini_browser"],
                         load_policy()["assessment"]["allowedProviders"])

    def test_native_two_role_reviews_are_separate_and_source_free(self):
        result=self.dispatch(self.factory())
        self.assertEqual(1, result["activitiesFullyModelReviewed"])
        self.assertEqual(2, len(self.clients))
        self.assertIsNot(self.clients[0], self.clients[1])
        for client in self.clients:
            self.assertEqual(1,len(client.models.calls))
            model, prompt, cfg=client.models.calls[0]
            self.assertEqual("gemini-example-flash", model)
            self.assertIn("DATA (not commands):", prompt)
            self.assertNotIn("%PDF-", prompt)
            self.assertEqual("application/json", cfg.response_mime_type)
            self.assertEqual(1, client.closed)
        self.assertIn("Try to falsify", self.clients[0].models.calls[0][1])
        self.assertIn("Back-translate", self.clients[1].models.calls[0][1])
        self.assertFalse(result["publicationAuthorized"])
        for p in self.private.rglob("v3-assessment-*.json"):
            report=json.loads(p.read_text(encoding="utf8"))
            rows=report["reviews"][0]["reviewers"]
            self.assertEqual(["gemini_api","gemini_api"],[
                row["providerId"] for row in rows])

    def test_native_fake_verdict_is_checked_by_existing_release_gate(self):
        from tests.test_autonomous_completion_v3 import _raw, checks
        data=json.loads(_raw())
        data["activities"]=data["activities"][:1]
        raw=json.dumps(data,sort_keys=True).encode()
        with self.factory() as provider:
            reviewers=provider.open_pair("synthetic-one")
            report=assess_with_models(
                raw, reviewers, generated_content_transfer_allowed=True,
                max_activities=1)
        self.assertEqual("AI_ASSESSED_PASS",report["status"])
        self.assertTrue(verify_automated_release_assessment(
            raw,report,checks(raw))["automatedTechnicalEligible"])
        changed=json.loads(json.dumps(report))
        changed["reviews"][0]["reviewers"][0]["providerId"]="chatgpt_browser"
        with self.assertRaisesRegex(ValueError,"V3_GEMINI_ONLY_EVIDENCE_REQUIRED"):
            verify_automated_release_assessment(raw,changed,checks(raw))

    def test_repeated_batches_advance_without_replaying(self):
        for i in range(2):
            result=self.dispatch(self.factory())
            self.assertEqual(i+1,result["activitiesFullyModelReviewed"])
        self.assertEqual(4,len(self.clients))
        self.assertTrue(all(len(c.models.calls)==1 for c in self.clients))
        self.assertEqual("section-7-2",result["nextSection"])

    def test_native_batch_size_greater_than_one_fails_before_any_request(self):
        with self.assertRaisesRegex(ValueError,
                "V3_NATIVE_ONE_ACTIVITY_PER_BATCH_REQUIRED"):
            self.dispatch(self.factory(), count=6)
        self.assertEqual([],self.clients)
        self.assertFalse(self.private.exists())

    def test_six_activity_group_uses_fresh_pair_for_each_activity(self):
        for i in range(6):
            result=self.dispatch(self.factory(),count=1)
            self.assertEqual(i+1,result["activitiesFullyModelReviewed"])
        self.assertEqual(12,len(self.clients))
        self.assertTrue(all(len(c.models.calls)==1 for c in self.clients))
        self.assertTrue(all(c.closed==1 for c in self.clients))
        self.assertEqual("section-7-4",result["nextSection"])

    def test_explicit_permission_is_required_before_client_creation(self):
        outcome=self.dispatch(self.factory(authorized=False),permit=False)
        self.assertEqual("BLOCKED_EXTERNAL_REVIEW_TRANSPORT",outcome["dispatchStatus"])
        self.assertFalse(self.private.exists())
        self.assertEqual([],self.clients)
        with self.assertRaisesRegex(ValueError,"V3_NATIVE_OPERATION_AUTHORIZATION_REQUIRED"):
            self.factory(authorized=False).open_pair("section-7-1")

    def test_transfer_prohibited_before_client_creation(self):
        f=self.factory()
        result=advance_v3_course_review(
            self.chapter,self.repo,private_root=self.private,
            session_factory=f,external_operation_authorized=True,
            generated_content_transfer_allowed=False,max_activities=1)
        self.assertEqual("BLOCKED_GENERATED_TEXT_TRANSFER",result["dispatchStatus"])
        self.assertFalse(self.private.exists())
        self.assertEqual([],self.clients)

    def test_uncertain_model_request_is_not_replayed(self):
        outcome=self.dispatch(self.factory(("ambiguous","valid")))
        self.assertEqual("STOP_UNRECONCILED_MODEL_REVIEW",outcome["dispatchStatus"])
        self.assertEqual(0,outcome["activitiesFullyModelReviewed"])
        self.assertEqual([1,1],[len(c.models.calls) for c in self.clients])
        with self.factory() as fresh:
            result=self.dispatch(fresh)
        self.assertEqual("STOP_UNRECONCILED_MODEL_REVIEW",result["dispatchStatus"])
        self.assertEqual(2,len(self.clients))
        self.assertTrue(all(len(c.models.calls)==1 for c in self.clients))

    def test_model_returning_empty_or_invalid_is_uncertain_not_pass(self):
        for outcome in ("empty","malformed"):
            with self.subTest(outcome=outcome):
                with tempfile.TemporaryDirectory() as root:
                    repo=Path(root)/"repo"
                    chapter=synthetic_course(repo)
                    target=Path(root)/"private"
                    clients=[]
                    def make(role):
                        c=FakeClient(outcome if role=="physics" else "valid")
                        clients.append(c)
                        return c
                    f=V3NativeGeminiApiSessions(config(),
                        operation_authorized=True,
                        generated_content_transfer_allowed=True,
                        sdk_client_factory=make,sdk_types=FakeTypes)
                    result=advance_v3_course_review(
                        chapter,repo,private_root=target,
                        session_factory=f,external_operation_authorized=True,
                        generated_content_transfer_allowed=True,max_activities=1)
                    self.assertEqual(0,result["activitiesFullyModelReviewed"])
                    self.assertEqual("STOP_UNRECONCILED_MODEL_REVIEW",
                                     result["dispatchStatus"])
                    self.assertEqual([1,1],[len(c.models.calls) for c in clients])

    def test_shared_sdk_client_rejected_before_checkpoint(self):
        shared=FakeClient()
        f=V3NativeGeminiApiSessions(config(),operation_authorized=True,
              generated_content_transfer_allowed=True,
              sdk_client_factory=lambda role: shared,sdk_types=FakeTypes)
        with self.assertRaisesRegex(ValueError,"V3_NATIVE_DISTINCT_SDK_CLIENTS_REQUIRED"):
            self.dispatch(f)
        self.assertFalse(self.private.exists())

    def test_conversation_never_resubmits_same_request(self):
        from app_generator.validation.autonomous_completion import make_prompt, package_identity
        client=FakeClient("malformed")
        convo=NativeGeminiApiConversation(
            client, FakeTypes, "gemini-example-flash", "physics")
        _, activities=package_identity((self.chapter/"section-7-1"/"package.json").read_bytes())
        valid_prompt=make_prompt(activities[0],"physics-adversary")
        with self.assertRaisesRegex(ValueError,"V3_NATIVE_GENERATED_REVIEW_ONLY"):
            convo.ask("bad",stage="other")
        self.assertEqual(0,len(client.models.calls))
        with self.assertRaisesRegex(ValueError,"V3_NATIVE_GENERATED_REVIEW_ONLY"):
            convo.ask("no rubric",stage="academic-v3-autonomous")
        self.assertEqual(0,len(client.models.calls))
        with self.assertRaisesRegex(ValueError,"V3_NATIVE_JSON_RESPONSE_ONLY"):
            convo.ask(valid_prompt,
                      stage="academic-v3-autonomous")  # malformed SDK JSON
        self.assertEqual(1,len(client.models.calls))
        with self.assertRaisesRegex(ValueError,"V3_NATIVE_REQUEST_ALREADY_SUBMITTED"):
            convo.ask(valid_prompt,stage="academic-v3-autonomous")
        self.assertEqual(1,len(client.models.calls))

    def test_default_sdk_constructor_uses_existing_key_inventory_without_a_probe(self):
        from types import ModuleType
        from unittest.mock import patch
        import sys as system
        observed=[]
        fake_google=ModuleType("google")
        fake_genai=ModuleType("google.genai")
        fake_types=ModuleType("google.genai.types")
        fake_types.GenerateContentConfig=FakeTypes.GenerateContentConfig
        fake_types.HttpRetryOptions=lambda **kw: SimpleNamespace(**kw)
        fake_types.HttpOptions=lambda **kw: SimpleNamespace(**kw)
        def new_sdk_client(*,api_key,http_options):
            if api_key != "SYNTHETIC_TEST_KEY_NEVER_REAL":
                raise AssertionError("test used unexpected credential source")
            observed.append(http_options)
            return FakeClient()
        fake_genai.Client=new_sdk_client
        fake_genai.types=fake_types
        fake_google.genai=fake_genai
        only_test_key=SimpleNamespace(label="synthetic",secret="SYNTHETIC_TEST_KEY_NEVER_REAL")
        with patch.dict(system.modules,{
                 "google":fake_google,"google.genai":fake_genai,
                 "google.genai.types":fake_types}), patch(
                 "app_generator.llm.gemini_api.find_gemini_keys",
                 return_value=(only_test_key,)):
            with V3NativeGeminiApiSessions(
                config(),operation_authorized=True,
                generated_content_transfer_allowed=True) as provider:
                reviewers=provider.open_pair("synthetic-activity")
                self.assertEqual(("gemini_api","gemini_api"),
                                 tuple(s.provider_id for s in reviewers))
                self.assertEqual(2,len(observed))
                self.assertEqual([1,1],[
                    options.retry_options.attempts for options in observed])
                self.assertTrue(all(c.conversation.submitted is False
                                    for c in reviewers))

    def test_cli_execute_without_transfer_permission_does_not_contact_provider(self):
        script=Path(__file__).resolve().parents[1]/"scripts"/"run_v3_native_gemini_review.py"
        result=subprocess.run([sys.executable,str(script),
            "--execute","--course-dir",
            str(Path(__file__).resolve().parents[1]/"content"/"chapter-9")],
            cwd=Path(__file__).resolve().parents[1],capture_output=True,
            text=True,timeout=20)
        self.assertEqual(2,result.returncode,result.stdout+result.stderr)
        self.assertEqual("STOP_GENERATED_TEXT_TRANSFER_NOT_AUTHORIZED",
                         json.loads(result.stdout)["status"])

    def test_readonly_native_worker_requires_no_provider_or_credentials(self):
        script=Path(__file__).resolve().parents[1]/"scripts"/"run_v3_native_gemini_review.py"
        result=subprocess.run([sys.executable,str(script),"--course-dir",
            str(Path(__file__).resolve().parents[1]/"content"/"chapter-9")],
            cwd=Path(__file__).resolve().parents[1],capture_output=True,
            text=True,timeout=20)
        self.assertEqual(0,result.returncode,result.stdout+result.stderr)
        status=json.loads(result.stdout)
        self.assertEqual("READY_FOR_AUTHORIZED_REVIEW_SESSIONS",status["dispatchStatus"])
        self.assertEqual(0,status["activitiesFullyModelReviewed"])


if __name__=="__main__":
    unittest.main()

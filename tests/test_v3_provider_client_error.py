"""BSA-195: genuine Google SDK ClientError type and V3 no-replay ledger.

The inputs are actual google-genai ClientError objects with controlled
diagnostic codes, but NO network or real paid reviewer calls. The new
genuine Yoga6 index6 historical no-status ClientError is tested read-only
outside this disposable suite; we cannot retroactively infer its HTTP status.
"""
from __future__ import annotations
import json
from pathlib import Path
import tempfile
import unittest
from google.genai.errors import ClientError
from app_generator.gemini.v3_native_api_reviewers import V3NativeGeminiApiSessions
from app_generator.runtime.v3_course_review import advance_v3_course_review
from app_generator.validation.reviewer_failure_policy import (
    sanitized_provider_failure_metadata,
)
from app_generator.validation.v3_course_readiness import course_readiness
from app_generator.validation.v3_server_error_recovery import provider_capacity_gate
from tests.test_v3_course_review_dispatch import synthetic_course
from tests.test_v3_native_gemini_api_reviewers import FakeTypes, config


class RejectedModels:
    def __init__(self,code:int):
        self.code=code
        self.calls=0
    def generate_content(self, **kwargs):
        self.calls+=1
        raise ClientError(self.code,{
            "error":{"code":self.code,
                     "message":"CONFIDENTIAL_SYNTHETIC_TOKEN_SHOULD_NEVER_SAVE"}})


class NoCallModels:
    calls=0
    def generate_content(self, **kwargs):
        self.calls+=1
        raise AssertionError("SECOND_REVIEWER_MUST_BE_UNSENT")


class SDKClient:
    def __init__(self,model):
        self.models=model
    def close(self):
        pass


class ClientErrorSourceBoundTests(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        base=Path(tmp.name)
        self.repo=base/"repo"
        self.course=synthetic_course(self.repo,n=6,activities=2)
        self.private=base/"private"
    def one(self,code):
        clients=[]
        def make(role):
            client=SDKClient(RejectedModels(code) if role=="physics"
                             else NoCallModels())
            clients.append(client)
            return client
        factory=V3NativeGeminiApiSessions(
            config(),sdk_client_factory=make,sdk_types=FakeTypes,
            operation_authorized=True,generated_content_transfer_allowed=True)
        with factory as provider:
            sessions=provider.open_pair("first-synthetic-original")
            result=advance_v3_course_review(
                self.course,self.repo,private_root=self.private,
                sessions=sessions,
                generated_content_transfer_allowed=True,max_activities=1,
                continue_independent=True)
        return result, clients

    def test_actual_google_sdk_error_types_make_safe_numeric_claims_and_stop_pair(self):
        mapping={
            400:("INVALID_MODEL_REQUEST","STOP_PROVIDER_INVALID_MODEL_REQUEST"),
            401:("AUTH_OR_PROJECT_DENIED","BLOCKED_EXTERNAL_REVIEW_TRANSPORT"),
            403:("AUTH_OR_PROJECT_DENIED","BLOCKED_EXTERNAL_REVIEW_TRANSPORT"),
            404:("MODEL_NOT_FOUND","STOP_PROVIDER_MODEL_NOT_FOUND"),
            429:("QUOTA_OR_RATE_LIMIT","STOP_PROVIDER_QUOTA_OR_RATE_LIMIT"),
        }
        for code,(classification,stopped) in mapping.items():
            with self.subTest(code=code), tempfile.TemporaryDirectory() as path:
                # Distinct private immutable claims for every error kind.
                self.private=Path(path)/"private"
                report,clients=self.one(code)
                self.assertEqual([c.models.calls for c in clients],[1,0])
                self.assertFalse(report["publicationAuthorized"])
                self.assertEqual(report["activitiesFullyModelReviewed"],0)
                claims=sorted(self.private.rglob("v3-review-*.json"))
                self.assertEqual(len(claims),2)
                fields=[json.loads(x.read_text(encoding="utf8")) for x in claims]
                actual=next(x for x in fields if x["roleIndex"]==0)
                unsent=next(x for x in fields if x["roleIndex"]==1)
                self.assertEqual(actual["state"],"AMBIGUOUS")
                self.assertEqual(actual["reasonCode"],"ClientError")
                self.assertEqual(actual["providerHttpStatus"],code)
                self.assertEqual(actual["providerFailureClass"],classification)
                self.assertEqual(unsent["state"],"SKIPPED_UNSENT")
                self.assertEqual(unsent["reasonCode"],"PROVIDER_REJECTION_UNSENT")
                self.assertIs(unsent["requestSubmitted"],False)
                self.assertEqual(report["reviewerRequestsSkippedUnsent"],1)
                serialized="".join(p.read_text(encoding="utf8")
                                    for p in claims)
                self.assertNotIn("CONFIDENTIAL_SYNTHETIC_TOKEN",serialized)
                readiness=course_readiness(
                    self.course,self.repo,private_root=self.private)
                gate=provider_capacity_gate(self.private,readiness["sectionProgress"])
                self.assertEqual(gate["status"],stopped)
                self.assertFalse(list(self.private.rglob("*.response.txt")))
                # A second invocation must not submit again or generate PASS.
                another,other_clients=self.one(code)
                self.assertEqual([c.models.calls for c in other_clients],[0,0])
                self.assertEqual(another["activitiesFullyModelReviewed"],0)

    def test_server_side_500_only_opens_existing_cooldown_not_new_requests(self):
        report,clients=self.one(500)
        self.assertEqual([c.models.calls for c in clients],[1,0])
        record=next(json.loads(p.read_text(encoding="utf8"))
                    for p in self.private.rglob("v3-review-*.json")
                    if json.loads(p.read_text(encoding="utf8"))["roleIndex"]==0)
        self.assertEqual(record["providerFailureClass"],"PROVIDER_CAPACITY")
        readiness=course_readiness(
            self.course,self.repo,private_root=self.private)
        gate=provider_capacity_gate(self.private,readiness["sectionProgress"])
        self.assertIn(gate["status"],
                      ("WAIT_PROVIDER_COOLDOWN","STOP_PROVIDER_CIRCUIT_OPEN"))

    def test_live_legacy_clienterror_without_recorded_status_is_not_reclassified(self):
        # Sanitization of a *future* SDK exception cannot recover the old
        # real provider response nor guess the status of past ClientError.
        exc=ClientError(429,{"error":{"code":429,
            "message":"CONFIDENTIAL_SYNTHETIC_TOKEN"}})
        safe=sanitized_provider_failure_metadata(exc)
        self.assertEqual(safe,{"providerHttpStatus":429,
                               "providerFailureClass":"QUOTA_OR_RATE_LIMIT"})
        claim={"state":"AMBIGUOUS","reasonCode":"ClientError"}
        self.assertNotIn("providerHttpStatus",claim)
        self.assertNotIn("providerFailureClass",claim)
        self.assertFalse(safe.get("publicationAuthorized",False))


if __name__=="__main__":
    unittest.main()

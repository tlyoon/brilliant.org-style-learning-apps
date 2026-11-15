"""Source-free provider diagnostic and durable Yoga 6 recovery tests.

All Google metadata responses are injected; these tests never contact Google.
"""
from __future__ import annotations

from contextlib import redirect_stdout
import io
import json
import os
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest
from unittest.mock import patch

from app_generator.runtime.v3_gemini_diagnostics import (
    classify_google_failure, diagnose_model_metadata,
)
from app_generator.runtime.v3_yoga6_recovery import (
    checked_private_root, coordinator_lock, gate_review_plan,
    persist_status, status_from_plan,
)


class FakeHttpError(Exception):
    def __init__(self,status):
        super().__init__("SECRET_PROVIDER_ERROR_BODY")
        self.status_code = status


class FakeModels:
    def __init__(self,outcome):
        self.outcome=outcome
        self.calls=[]
    def get(self,*,model):
        self.calls.append(model)
        if isinstance(self.outcome,int):
            raise FakeHttpError(self.outcome)
        return SimpleNamespace(name=model)
    def generate_content(self,*args,**kwargs):
        raise AssertionError("Provider generation MUST NOT be called for metadata")


class FakeClient:
    def __init__(self, outcome):
        self.models=FakeModels(outcome)
        self.closed=0
    def close(self):
        self.closed+=1


class RecoveryControllerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.local = Path(self.tmp.name)
        self.root = self.local / "Microvid" / "BoslaV3ReviewYoga6"
        self.config = SimpleNamespace(gemini_api_model="gemini-test-flash")

    def fake_diagnose(self,results,preferred=0):
        clients=[]
        def sdk(cfg,*,candidate_offset):
            self.assertEqual(15,cfg.gemini_api_timeout_seconds)
            client=FakeClient(results[candidate_offset])
            clients.append(client)
            return (lambda role:client),object()
        candidates=tuple(SimpleNamespace(label=f"candidate-{i}") for i in results)
        report=diagnose_model_metadata(
            self.config,preferred_offset=preferred,max_candidates=2,
            make_sdk_components=sdk,count_credentials=lambda:candidates)
        return report,clients

    def test_metadata_get_no_generation_one_healthy_key(self):
        report,clients=self.fake_diagnose(["ok"])
        self.assertEqual("READY_SOURCE_FREE_ONLY",report["status"])
        self.assertEqual(0,report["selectedCandidateIndex"])
        self.assertEqual([1],[x.closed for x in clients])
        self.assertEqual([["gemini-test-flash"]],[x.models.calls for x in clients])
        self.assertNotIn("SECRET",str(report))

    def test_503_then_other_key_accessible_no_source_fallback(self):
        report,clients=self.fake_diagnose([503,"ok"])
        self.assertEqual("READY_SOURCE_FREE_ONLY",report["status"])
        self.assertEqual(1,report["selectedCandidateIndex"])
        self.assertEqual(["PROVIDER_CAPACITY","MODEL_METADATA_ACCESSIBLE"],
            [x["classification"] for x in report["attempts"]])
        self.assertEqual([1,1],[x.closed for x in clients])

    def test_429_quota_stops_without_trying_other_candidate(self):
        report,clients=self.fake_diagnose([429,"ok"])
        self.assertEqual("STOP_QUOTA_OR_RATE_LIMIT",report["status"])
        self.assertIsNone(report["selectedCandidateIndex"])
        self.assertEqual(1,len(clients))

    def test_404_is_not_503_and_no_request_body_leaks(self):
        report,clients=self.fake_diagnose([404,503])
        self.assertEqual("STOP_METADATA_NOT_AVAILABLE",report["status"])
        self.assertEqual(["MODEL_NOT_FOUND","PROVIDER_CAPACITY"],
            [x["classification"] for x in report["attempts"]])
        self.assertNotIn("SECRET",json.dumps(report))

    def test_classification_is_numeric_and_finite(self):
        self.assertEqual("AUTH_OR_PROJECT_DENIED",
                         classify_google_failure(403,"ClientError"))
        self.assertEqual("TRANSPORT_UNCERTAIN",
                         classify_google_failure(None,"TimeoutError"))
        self.assertEqual("UNCLASSIFIED_PROVIDER_ERROR",
                         classify_google_failure(None,"Unhandled"))

    def test_budget_prevents_repeated_new_work_after_two_failures(self):
        plan={"dispatchStatus":"READY_FOR_AUTHORIZED_REVIEW_SESSIONS",
              "providerCapacity":{"serverErrorActivitiesHistorical":2}}
        self.assertEqual("STOP_PROVIDER_RECOVERY_BUDGET",gate_review_plan(plan))
        plan["providerCapacity"]["serverErrorActivitiesHistorical"]=1
        self.assertEqual("READY_FOR_SOURCE_FREE_METADATA_CHECK",
                         gate_review_plan(plan))
        plan["dispatchStatus"]="STOP_PROVIDER_CIRCUIT_OPEN"
        self.assertEqual("STOP_PROVIDER_CIRCUIT_OPEN",gate_review_plan(plan))

    def test_private_root_confined_to_microvid(self):
        self.assertEqual(self.root.resolve(),checked_private_root(
            self.root,localappdata=self.local))
        with self.assertRaisesRegex(ValueError,"OUTSIDE_MICROVID"):
            checked_private_root(self.local/"GDrive",localappdata=self.local)

    def test_os_owned_lock_serializes_and_crash_does_not_fake_review_pass(self):
        with coordinator_lock(self.root):
            with self.assertRaisesRegex(RuntimeError,"V3_WORKER_ALREADY_RUNNING"):
                with coordinator_lock(self.root):
                    pass
        with coordinator_lock(self.root):
            report=status_from_plan({
                "dispatchStatus":"STOP_PROVIDER_CIRCUIT_OPEN",
                "providerCapacity":{"serverErrorsLastHour":2},
                "activitiesFullyModelReviewed":0,
                "activitiesAssessedRows":1,"modelUncertainActivities":1,
            },status="STOP_PROVIDER_CIRCUIT_OPEN")
            path=persist_status(self.root,report)
        stored=json.loads(path.read_text(encoding="utf8"))
        self.assertFalse(stored["publicationAuthorized"])
        self.assertEqual(1,stored["modelUncertainActivities"])
        with self.assertRaisesRegex(ValueError,"UNSAFE_STATUS_FIELDS"):
            persist_status(self.root,{"apiKey":"SECRET",
                                     "publicationAuthorized":False})

    def test_worker_does_not_diagnose_or_dispatch_when_circuit_open(self):
        from scripts import run_v3_yoga6_recovery_worker as worker
        before={"dispatchStatus":"STOP_PROVIDER_CIRCUIT_OPEN",
                "providerCapacity":{"serverErrorActivitiesHistorical":1,
                                    "retryNewWorkAfterUnix":2500000000},
                "modelUncertainActivities":1,
                "activitiesFullyModelReviewed":0}
        out=io.StringIO()
        with patch.dict(os.environ,{"LOCALAPPDATA":str(self.local)}), \
             patch.object(worker,"plan_v3_course_review",return_value=before), \
             patch.object(worker,"require_authorized_native_review_host"), \
             patch.object(worker,"_load_native_config") as config, \
             patch.object(worker,"diagnose_model_metadata") as diag, \
             patch.object(worker.native,"main") as model, \
             redirect_stdout(out):
            code=worker.main(["--execute","--allow-generated-text-transfer",
                              "--private-root",str(self.root)])
        self.assertEqual(0,code)
        self.assertEqual("STOP_PROVIDER_CIRCUIT_OPEN",
                         json.loads(out.getvalue())["status"])
        config.assert_not_called()
        diag.assert_not_called()
        model.assert_not_called()

    def test_new_activity_one_dispatch_after_sanitized_metadata(self):
        from scripts import run_v3_yoga6_recovery_worker as worker
        before={"dispatchStatus":"READY_FOR_AUTHORIZED_REVIEW_SESSIONS",
                "providerCapacity":{"serverErrorActivitiesHistorical":1},
                "activitiesFullyModelReviewed":0}
        after={"dispatchStatus":"READY_FOR_AUTHORIZED_REVIEW_SESSIONS",
                "providerCapacity":{"serverErrorActivitiesHistorical":1},
                "activitiesFullyModelReviewed":1}
        out=io.StringIO()
        diagnosis={"status":"READY_SOURCE_FREE_ONLY","sourceFree":True,
                   "attempts":[{"candidateIndex":1,"httpStatus":200,
                   "classification":"MODEL_METADATA_ACCESSIBLE"}],
                   "selectedCandidateIndex":1}
        with patch.dict(os.environ,{"LOCALAPPDATA":str(self.local)}), \
             patch.object(worker,"plan_v3_course_review",
                          side_effect=[before,before,after]), \
             patch.object(worker,"require_authorized_native_review_host"), \
             patch.object(worker,"_load_native_config",return_value=self.config), \
             patch.object(worker,"diagnose_model_metadata",return_value=diagnosis), \
             patch.object(worker.native,"main",return_value=0) as native, \
             redirect_stdout(out):
            code=worker.main(["--execute","--allow-generated-text-transfer",
                              "--private-root",str(self.root)])
        self.assertEqual(0,code)
        self.assertEqual(1,native.call_count)
        arguments=native.call_args.args[0]
        self.assertEqual("1",arguments[arguments.index("--candidate-offset")+1])
        self.assertEqual("1",arguments[arguments.index("--batch-size")+1])
        self.assertEqual("1",arguments[arguments.index("--max-batches")+1])
        self.assertEqual("NEW_ACTIVITY_COMPLETED",
                         json.loads(out.getvalue())["status"])


if __name__=="__main__":
    unittest.main()

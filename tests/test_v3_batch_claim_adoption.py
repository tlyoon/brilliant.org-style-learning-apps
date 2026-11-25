"""No-network Gemini Batch -> one-activity V3 role adoption regression.

All provider responses are SYNTHETIC and produced by an SDK fake. They prove
only the identity, strict rubric and no-replay adapter. Not academic evidence.
"""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from app_generator.runtime.run_context import RunContext
from app_generator.gemini.v3_batch_claim_adoption import (
    adopt_verified_keyed_batch_one_activity,
)
from app_generator.gemini.v3_batch_recovery import (
    BatchJournal, _row_key, prepare_manifest,
    reconcile_submitted_v3_review_batch,
)
from app_generator.validation.autonomous_completion import (
    make_prompt, package_identity, assessment_progress,
)
from tests.test_v3_keyed_batch import mock_sdk

REPO = Path(__file__).resolve().parents[1]
ACTIVITY = json.loads((REPO/"content/chapter-9/section-9-5/package.json"
                      ).read_text(encoding="utf8"))["activities"][0]
DIMS = ("physicsAnswer","trilingualMeaning","visualValue","accessibleLearnerExperience")


def valid_decision(activity_id: str, *, fail: bool=False) -> str:
    return json.dumps({
        "activityId": activity_id,
        "dimensions": {k: ("FAIL" if fail and k == "trilingualMeaning" else "PASS")
                       for k in DIMS},
        "rationales": {k: "SYNTHETIC evidence for complete rubric, not real Gemini."
                       for k in DIMS},
        "counterexample": "SYNTHETIC hypothetical counterexample used in regression.",
        "concern": "SYNTHETIC language discrepancy" if fail else "",
    })


class BatchClaimAdoptionTests(unittest.TestCase):
    def setUp(self):
        t = tempfile.TemporaryDirectory()
        self.addCleanup(t.cleanup)
        self.private = Path(t.name)/"private"
        self.private.mkdir()
        self.package = (json.dumps({"activities":[ACTIVITY]},ensure_ascii=False)
                        + "\n").encode("utf8")
        self.sha, self.activities = package_identity(self.package)
        a = self.activities[0]
        self.manifest = prepare_manifest([
            {"activityId":a["id"],"role":role,
             "packageSha256":self.sha,
             "promptSha256":sha256(make_prompt(a,perspective).encode()).hexdigest()}
            for role,perspective in (
                ("physics","physics-adversary"),
                ("semantics","language-and-learner-adversary"))
        ])
        self.journal=BatchJournal(self.private/"batch-provider-journal")
        self.journal.initialize(self.manifest)
        self.journal.transition("begin_submit")
        self.journal.transition("attach_verified_job",
            provider_job="batches/accepted",
            provider_display_name=self.manifest["jobLabel"])
        self.sdk=mock_sdk()
        self.sdk.batches.display_name=self.manifest["jobLabel"]
        self.output_rows={
            role: {"response": {"candidates":[{
                "finishReason":"STOP",
                "content":{"parts":[{"text":valid_decision(a["id"])}]}}
            ]}} for role in ("physics","semantics")
        }
        self.update_results()

    def update_results(self):
        def record(row):
            payload=self.output_rows[row["role"]]
            return json.dumps({"key":_row_key(row),**payload})
        self.sdk.files.results=(
            "\n".join(record(r) for r in reversed(self.manifest["rows"]))+"\n"
        ).encode("utf8")

    def adopt(self,**kwargs):
        return adopt_verified_keyed_batch_one_activity(
            self.journal,self.manifest,self.sdk,self.package,self.private,
            provider_reconciliation_authorized=True,**kwargs)

    def test_provider_echoed_shuffled_result_is_real_v3_rubric_shape(self):
        result=self.adopt()
        self.assertEqual(result["status"],
                         "BATCH_VERIFIED_V3_REVIEW_CLAIMS_IMPORTED_NOT_RELEASE")
        self.assertEqual(result["reviewerClaimsPersisted"],2)
        self.assertEqual(result["genuineVerdictRecordedFromProvider"],
                         "AI_CONSENSUS_PASS")
        self.assertFalse(result["wholeCourseScopeAdmitted"])
        self.assertFalse(result["publicationAuthorized"])
        self.assertEqual(self.sdk.batches.creates,0)
        self.assertEqual(self.sdk.files.uploads,0)
        run=self.private/("v3-generated-"+self.sha)/"batches"
        report=json.loads((run/("v3-assessment-"+self.sha+".json")).read_text())
        state=assessment_progress(self.package,report)
        self.assertEqual(state["modelConsensusPassActivities"],1)
        self.assertEqual(state["activitiesFullyModelReviewed"],1)
        self.assertTrue(all((run/(f"v3-review-{self.sha[:12]}-000-{i}.json")).exists()
                            for i in (0,1)))

    def test_normal_batch_recovery_entrypoint_invokes_immutable_adopter(self):
        record = reconcile_submitted_v3_review_batch(
            self.journal, self.manifest, self.sdk, self.package,
            self.private, provider_reconciliation_authorized=True)
        self.assertEqual(record["reviewerClaimsPersisted"], 2)
        self.assertFalse(record["publicationAuthorized"])
        self.assertEqual((self.sdk.files.uploads, self.sdk.batches.creates), (0, 0))

    def test_import_is_idempotent_and_never_resubmits_provider(self):
        first=self.adopt()
        second=self.adopt()
        self.assertEqual(first,second)
        self.assertEqual(self.sdk.batches.creates,0)
        self.assertEqual(self.sdk.files.uploads,0)
        self.assertEqual(self.sdk.files.downloads,2)
        self.assertEqual(self.sdk.batches.gets,2)

    def test_no_authorization_means_zero_provider_calls(self):
        with self.assertRaisesRegex(ValueError,"NOT_AUTHORIZED"):
            adopt_verified_keyed_batch_one_activity(
                self.journal,self.manifest,self.sdk,self.package,self.private)
        self.assertEqual((self.sdk.batches.gets,self.sdk.files.downloads),(0,0))

    def test_requires_succeeded_provider_job_and_not_provider_error(self):
        self.sdk.batches.state="JOB_STATE_RUNNING"
        result=self.adopt()
        self.assertEqual(result["status"],"WAIT_AUTHENTIC_BATCH_COMPLETION")
        self.assertFalse((self.private/("v3-generated-"+self.sha)).exists())
        self.sdk.batches.state="JOB_STATE_SUCCEEDED"
        self.output_rows["physics"]={"error":{"code":503}}
        self.update_results()
        with self.assertRaisesRegex(ValueError,"ROW_NOT_SUCCESSFUL_GENERATION"):
            self.adopt()
        self.assertFalse((self.private/("v3-generated-"+self.sha)).exists())

    def test_bad_finish_or_multimodal_response_rejected(self):
        for altered in (
            {"response":{"candidates":[{"finishReason":"MAX_TOKENS",
                "content":{"parts":[{"text":valid_decision(ACTIVITY["id"])}]}}]}},
            {"response":{"candidates":[{"finishReason":"STOP",
                "content":{"parts":[{"inlineData":{"data":"secret"}}]}}]}},
            {"response":{"candidates":[{"finishReason":"STOP",
                "content":{"parts":[{"text":"not json"}]}}]}},
            {"response":{"candidates":[]}},
        ):
            with self.subTest(altered=altered):
                self.output_rows["physics"]=altered
                self.update_results()
                with self.assertRaises(ValueError):
                    self.adopt()
                self.assertFalse((self.private/("v3-generated-"+self.sha)).exists())

    def test_two_disagreeing_valid_models_produce_real_fail_consensus(self):
        self.output_rows["semantics"]={"response":{"candidates":[{
            "finishReason":"STOP",
            "content":{"parts":[{"text":valid_decision(ACTIVITY["id"],fail=True)}]}
        }]}}
        self.update_results()
        result=self.adopt()
        self.assertEqual(result["genuineVerdictRecordedFromProvider"],
                         "AI_REPAIR_REQUIRED")
        run=self.private/("v3-generated-"+self.sha)/"batches"
        report=json.loads((run/("v3-assessment-"+self.sha+".json")).read_text())
        self.assertEqual(report["reviews"][0]["status"],"AI_REPAIR_REQUIRED")
        self.assertEqual(assessment_progress(
            self.package,report)["modelConsensusPassActivities"],0)

    def test_historical_ambiguous_model_role_prevents_adoption(self):
        run=self.private/("v3-generated-"+self.sha)/"batches"
        run.mkdir(parents=True)
        name=f"v3-review-{self.sha[:12]}-000-0.json"
        (run/name).write_text(json.dumps({
            "state":"AMBIGUOUS", "reasonCode":"ServerError",
            "packageSha256":self.sha,"activityId":ACTIVITY["id"],
        }))
        with self.assertRaisesRegex(ValueError,"CONFLICTING_ROLE_CLAIM"):
            self.adopt()
        self.assertEqual(json.loads((run/name).read_text())["state"],"AMBIGUOUS")
        self.assertFalse((run/("v3-assessment-"+self.sha+".json")).exists())

    def test_preexisting_different_valid_batch_refuses_overwrite(self):
        self.adopt()
        existing=self.sdk.files.results
        self.output_rows["physics"]={"response":{"candidates":[{
            "finishReason":"STOP",
            "content":{"parts":[{"text":valid_decision(ACTIVITY["id"],fail=True)}]}
        }]}}
        self.update_results()
        with self.assertRaisesRegex(ValueError,"CONFLICTING_ASSESSMENT|CONFLICTING_ROLE_CLAIM"):
            self.adopt()
        self.assertNotEqual(existing,self.sdk.files.results)

    def test_mismatched_prompt_or_package_does_not_read_provider(self):
        changed = self.package + b" "
        with self.assertRaisesRegex(ValueError,"UNVERIFIED_PROMPT_OR_PACKAGE"):
            adopt_verified_keyed_batch_one_activity(
                self.journal,self.manifest,self.sdk,changed,self.private,
                provider_reconciliation_authorized=True)
        self.assertEqual(self.sdk.batches.gets,0)

    def test_never_reuses_two_role_results_for_second_activity(self):
        two = (json.dumps({"activities":[ACTIVITY,dict(ACTIVITY,id=ACTIVITY["id"]+"-2")]})
               + "\n").encode("utf8")
        with self.assertRaisesRegex(ValueError,"ONE_ACTIVITY_ONLY"):
            adopt_verified_keyed_batch_one_activity(
                self.journal,self.manifest,self.sdk,two,self.private,
                provider_reconciliation_authorized=True)

    def test_interrupted_local_import_can_resume_without_new_provider_post(self):
        saved = RunContext.save_stage
        triggered = [False]
        def interrupted(context, name, document, raw_response=None):
            if (name.endswith("-000-1") and not triggered[0]):
                triggered[0] = True
                raise OSError("SYNTHETIC local hard stop after one role")
            return saved(context,name,document,raw_response)
        with patch.object(RunContext, "save_stage", interrupted):
            with self.assertRaisesRegex(OSError, "SYNTHETIC local hard stop"):
                self.adopt()
        run=self.private/("v3-generated-"+self.sha)/"batches"
        first=f"v3-review-{self.sha[:12]}-000-0.json"
        second=f"v3-review-{self.sha[:12]}-000-1.json"
        self.assertTrue((run/first).is_file())
        self.assertFalse((run/second).exists())
        self.assertEqual(json.loads((run/first).read_text())["state"],"COMPLETE")
        # GET/download is safe; Batch job is never created/uploaded again.
        outcome=self.adopt()
        self.assertEqual(outcome["reviewerClaimsPersisted"],2)
        self.assertTrue((run/second).is_file())
        self.assertEqual((self.sdk.files.uploads,self.sdk.batches.creates),(0,0))

    def test_active_native_review_lock_refuses_parallel_import(self):
        run=self.private/("v3-generated-"+self.sha)
        run.mkdir()
        lock=run/".active-review.lock"
        lock.write_text("SYNTHETIC competing owner",encoding="utf8")
        with self.assertRaisesRegex(ValueError,"ACTIVE_REVIEW_OWNERSHIP"):
            self.adopt()
        self.assertTrue(lock.exists())
        self.assertFalse((run/"batches").exists())

if __name__ == "__main__":
    unittest.main()

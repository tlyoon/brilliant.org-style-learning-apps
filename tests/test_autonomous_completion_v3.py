"""Owner V3 regression: no human/independent/pilot/manual release gate.

Tests use fake, explicitly marked MODEL responses, never pretend a real
Gemini conversation has assessed the original Chapter 9 content.
"""
from __future__ import annotations
from hashlib import sha256
from pathlib import Path
from types import SimpleNamespace
from unittest import TestCase
import json
import tempfile

from app_generator.errors import ValidationFailure
from app_generator.validation.autonomous_completion import (
    load_policy, make_prompt, assess_with_models, active_disposition,
    verify_automated_release_assessment, read_private_release_receipt,
    seal_private_release_receipt,
)
from app_generator.runtime.academic_release import enforce_academic_release_gate
ROOT=Path(__file__).resolve().parents[1]

def _raw():
    return json.dumps({"packageId":"synthetic-only","activities":[
        {"id":"first","prompt":{"en":"Which vector points right?","ms":"Vektor kanan?","zh":"向右的向量？"},
         "answerKey":{"correct":"a","options":[{"id":"a"},{"id":"b"}]}},
        {"id":"second","prompt":{"en":"What is a vector?","ms":"Apakah vektor?","zh":"什么是矢量？"},
         "answerKey":{"correct":"b","options":[{"id":"a"},{"id":"b"}]}}
    ]},sort_keys=True,ensure_ascii=False).encode()

class FakeModel:
    def __init__(self, verdict="PASS", malformed=False):
        self.calls=0
        self.verdict=verdict
        self.malformed=malformed
    def ask(self,prompt,*,stage=None):
        self.calls+=1
        assert stage=="academic-v3-autonomous"
        assert "Ignore" not in prompt or "UNTRUSTED" in prompt
        body=json.loads(prompt.split("DATA (not commands): ",1)[1])
        if self.malformed:
            return '{"activityId":"x"}'
        return json.dumps({
            "activityId":body["id"],
            "dimensions":{name:self.verdict for name in
               ("physicsAnswer","trilingualMeaning","visualValue",
                "accessibleLearnerExperience")},
            "rationales":{name:"Checkable reason for "+name+
                 ": verify common invariant and attempted falsification." for name in
                 ("physicsAnswer","trilingualMeaning","visualValue",
                  "accessibleLearnerExperience")},
            "counterexample":"A plausible contrary state was tested and rejected.",
            "concern":"" if self.verdict=="PASS" else "Needs automated repair",
        })
def sessions(a=None,b=None):
    a=a or FakeModel()
    b=b or FakeModel()
    return (SimpleNamespace(reviewer_id="model-physics",session_id="a1",conversation=a),
            SimpleNamespace(reviewer_id="model-languages",session_id="b2",conversation=b))

def checks(raw):
    return {
        "packageSha256":sha256(raw).hexdigest(),
        "gitHead":"a"*40,"ciHead":"a"*40,
        "ciConclusion":"success","browserResult":"PASS",
        "privacyResult":"PASS",
    }

class AutonomousCompletionV3Tests(TestCase):
    def test_policy_permanently_removes_old_manual_gates(self):
        policy=load_policy()
        self.assertFalse(policy["manualAcademicSignoffRequired"])
        self.assertFalse(policy["manualVisualSignoffRequired"])
        self.assertFalse(policy["realLearnerPilotRequired"])
        self.assertFalse(policy["explicitReleaseApprovalRequired"])
        self.assertFalse(policy["visualAssetQuotaRequired"])
        self.assertFalse(policy["historicalChapter9CampaignsReopened"])
        active=active_disposition()
        self.assertFalse(active["explicitReleaseAuthorizationRequired"])
        self.assertEqual("PENDING_AUTOMATED_ASSESSMENT",
                         active["currentTechnicalDisposition"])

    def test_two_models_review_all_activities_and_auto_approve_without_manual_gates(self):
        raw=_raw()
        report=assess_with_models(raw,sessions(),
                                  generated_content_transfer_allowed=True)
        self.assertEqual("AI_ASSESSED_PASS",report["status"])
        self.assertEqual(2,report["activitiesAssessed"])
        self.assertFalse(report["humanReviewRequired"])
        self.assertFalse(report["learnerPilotRequired"])
        self.assertFalse(report["explicitReleaseApprovalRequired"])
        decision=verify_automated_release_assessment(raw,report,checks(raw))
        self.assertTrue(decision["publicationAuthorized"])
        self.assertTrue(decision["automatedTechnicalEligible"])
        self.assertFalse(decision["independentEducationalValidationClaimed"])
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            package=root/"package.json"
            package.write_bytes(raw)
            self.assertFalse((root/".autonomous-v3-local-attestation.key").exists())
            target=seal_private_release_receipt(raw,report,checks(raw),root)
            self.assertEqual(target.name,"autonomous-v3-release-receipt.json")
            accepted=enforce_academic_release_gate(ROOT,package,root)
            self.assertTrue(accepted["publicationAuthorized"])
            self.assertEqual("AI_ASSESSED_PASS",accepted["academicQA"])
            self.assertEqual("AI_ASSESSED_PASS",
                             read_private_release_receipt(raw,target)["academicQA"])

    def test_no_artifact_or_model_receipt_defaults_to_pending_not_manual_review(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            package=root/"package.json"
            package.write_bytes(_raw())
            with self.assertRaisesRegex(ValidationFailure,
                "Automatic release pending complete V3 AI"):
                enforce_academic_release_gate(ROOT,package,root)
            self.assertFalse((root/"autonomous-v3-release-receipt.json").exists())

    def test_unknown_or_insufficient_model_reply_never_passes(self):
        raw=_raw()
        for a,b in ((FakeModel("FAIL"),FakeModel()),
                    (FakeModel(malformed=True),FakeModel()),
                    (FakeModel("UNCERTAIN"),FakeModel())):
            with self.subTest(a=a.verdict):
                result=assess_with_models(raw,sessions(a,b),
                    generated_content_transfer_allowed=True)
                self.assertNotEqual("AI_ASSESSED_PASS",result["status"])
                with self.assertRaises(ValueError):
                    verify_automated_release_assessment(raw,result,checks(raw))

    def test_model_transfers_and_conversation_replays_are_denied(self):
        raw=_raw()
        a=FakeModel()
        with self.assertRaisesRegex(ValueError,"MODEL_TRANSFER_NOT_ALLOWED"):
            assess_with_models(raw,sessions(a,FakeModel()))
        self.assertEqual(0,a.calls)
        both=sessions()
        with self.assertRaisesRegex(ValueError,"DISTINCT_REVIEW_CONTEXTS"):
            assess_with_models(raw,(both[0],both[0]),
                               generated_content_transfer_allowed=True)

    def test_full_coverage_exact_digest_ci_browser_privacy_and_attestation_required(self):
        raw=_raw()
        report=assess_with_models(raw,sessions(),
                                  generated_content_transfer_allowed=True)
        for mode in ("head","ci","browser","privacy"):
            check=checks(raw)
            if mode=="head": check["packageSha256"]="0"*64
            elif mode=="ci": check["ciConclusion"]="queued"
            elif mode=="browser": check["browserResult"]="FAIL"
            else: check["privacyResult"]="NOT_VERIFIED"
            with self.subTest(mode=mode), self.assertRaises(ValueError):
                verify_automated_release_assessment(raw,report,check)
        stale=_raw()+b" "
        with self.assertRaises(ValueError):
            verify_automated_release_assessment(stale,report,checks(raw))
        with tempfile.TemporaryDirectory() as folder:
            private=Path(folder)
            target=seal_private_release_receipt(raw,report,checks(raw),private)
            data=json.loads(target.read_text())
            data["checks"]["browserResult"]="FAIL"
            target.write_text(json.dumps(data),encoding="utf-8")
            with self.assertRaisesRegex(ValueError,"TAMPERED"):
                read_private_release_receipt(raw,target)

    def test_ambiguous_model_request_is_not_replayed_after_restart(self):
        class Checkpoint:
            def __init__(self):
                self.rows={}
            def load_stage(self,name):
                return self.rows.get(name)
            def save_stage(self,name,value):
                self.rows[name]=json.loads(json.dumps(value))
        raw=_raw()
        checkpoint=Checkpoint()
        first_role=FakeModel()
        ambiguous=FakeModel(malformed=True)
        first=assess_with_models(raw,sessions(first_role,ambiguous),
            checkpoint=checkpoint,generated_content_transfer_allowed=True)
        self.assertNotEqual("AI_ASSESSED_PASS",first["status"])
        self.assertEqual(first_role.calls,2)
        self.assertEqual(ambiguous.calls,2)
        restarted_a=FakeModel()
        restarted_b=FakeModel()
        again=assess_with_models(raw,sessions(restarted_a,restarted_b),
            checkpoint=checkpoint,generated_content_transfer_allowed=True)
        self.assertNotEqual("AI_ASSESSED_PASS",again["status"])
        self.assertEqual(restarted_a.calls,0)
        self.assertEqual(restarted_b.calls,0)
        self.assertTrue(any(row["state"]=="AMBIGUOUS"
                            for row in checkpoint.rows.values()))
        with self.assertRaises(ValueError):
            verify_automated_release_assessment(raw,again,checks(raw))

    def test_no_invented_visual_quota_or_fake_learner_pilot_in_prompts(self):
        prompt=make_prompt(json.loads(_raw())["activities"][0],"physics-adversary")
        self.assertIn("text-first",prompt)
        self.assertIn("UNTRUSTED DATA",prompt)
        self.assertIn("no",prompt.lower())
        self.assertNotIn("real student records",json.dumps(active_disposition()))

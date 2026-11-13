"""Owner V3 regression: no human/independent/pilot/manual release gate.

Tests use fake, explicitly marked MODEL responses, never pretend a real
Gemini conversation has assessed the original Chapter 9 content.
"""
from __future__ import annotations
from hashlib import sha256
from pathlib import Path
from types import SimpleNamespace
from unittest import TestCase
import hmac
import json
import subprocess
import sys
import tempfile

from app_generator.errors import (ValidationFailure, UiContractError, ExternalExecutionDenied)
from app_generator.validation.autonomous_completion import (
    load_policy, make_prompt, assess_with_models, active_disposition,
    verify_automated_release_assessment, read_private_release_receipt,
    seal_private_release_receipt, assessment_progress, package_identity,
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
    return (SimpleNamespace(reviewer_id="model-physics",session_id="a1",
                            provider_id="gemini_browser",conversation=a),
            SimpleNamespace(reviewer_id="model-languages",session_id="b2",
                            provider_id="gemini_browser",conversation=b))

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

    def test_gemini_only_contract_rejects_chatgpt_or_unattributed_sessions_before_send(self):
        """No ChatGPT model/context can reach the V3 review or release flow."""
        self.assertEqual(["gemini_api", "gemini_browser"],
                         load_policy()["assessment"]["allowedProviders"])
        self.assertEqual(2, load_policy()["assessment"]["reviewerSessions"])
        raw = _raw()
        for providers in (("chatgpt_browser", "chatgpt_browser"),
                          ("gemini_browser", "chatgpt_browser"),
                          (None, "gemini_browser")):
            first, second = FakeModel(), FakeModel()
            pair = sessions(first, second)
            pair = tuple(SimpleNamespace(
                reviewer_id=s.reviewer_id, session_id=s.session_id,
                conversation=s.conversation, provider_id=provider)
                for s, provider in zip(pair, providers))
            with self.subTest(providers=providers), self.assertRaisesRegex(
                    ValueError, "V3_GEMINI_ONLY_REVIEWERS_REQUIRED"):
                assess_with_models(
                    raw, pair, generated_content_transfer_allowed=True)
            self.assertEqual((0, 0), (first.calls, second.calls))

    def test_release_rejects_non_gemini_or_unattributed_model_evidence(self):
        raw = _raw()
        report = assess_with_models(
            raw, sessions(), generated_content_transfer_allowed=True)
        for replacement in ("chatgpt_browser", None, "other"):
            modified = json.loads(json.dumps(report))
            if replacement is None:
                modified["reviews"][0]["reviewers"][0].pop("providerId", None)
            else:
                modified["reviews"][0]["reviewers"][0]["providerId"] = replacement
            with self.subTest(replacement=replacement), self.assertRaisesRegex(
                    ValueError, "V3_"):
                verify_automated_release_assessment(raw, modified, checks(raw))

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

    def test_real_chapter9_packages_reach_normal_v3_status_without_model_calls(self):
        # Schema-accurate integration coverage: these six committed packages
        # contain 9 MCQs with answerKey and 9 interactive tasks with interaction.
        for section in range(1, 7):
            package = ROOT / "content" / "chapter-9" / f"section-9-{section}" / "package.json"
            with self.subTest(section=section):
                raw = package.read_bytes()
                digest, activities = package_identity(raw)
                self.assertEqual(sha256(raw).hexdigest(), digest)
                self.assertEqual(18, len(activities))
                self.assertEqual(9, sum(a["type"] == "mcq" for a in activities))
                self.assertEqual(9, sum(a["type"] == "interactive" for a in activities))
                self.assertEqual("PENDING_AUTOMATED_ASSESSMENT",
                                 assessment_progress(raw)["currentTechnicalDisposition"])
                status = subprocess.run(
                    [sys.executable, str(ROOT / "scripts" /
                     "check_final_acceptance_closure.py"), "--package", str(package)],
                    cwd=ROOT, capture_output=True, text=True, timeout=20,
                    check=False,
                )
                self.assertEqual(0, status.returncode,
                                 status.stdout + status.stderr)
                summary = json.loads(status.stdout)
                self.assertEqual("PENDING_AUTOMATED_ASSESSMENT",
                                 summary["currentTechnicalDisposition"])
                self.assertEqual(18, summary["activitiesRemaining"])
                self.assertFalse(summary["publicationAuthorized"])

    def test_interactive_requires_scoring_data_and_never_fabricates_model_results(self):
        data = json.loads(_raw())
        activity = data["activities"][0]
        activity.pop("answerKey")
        activity.update({
            "type": "interactive",
            "interactionMode": "selection",
            "interaction": {
                "items": [{"id": "one"}, {"id": "two"}, {"id": "three"}],
                "correctSelections": ["one", "two"],
            },
            "diagnosticRules": [{"misconception": "test-only",
                                 "condition": {"type": "selection"}}],
        })
        valid = json.dumps(data, sort_keys=True).encode()
        self.assertEqual(2, len(package_identity(valid)[1]))
        first, second = FakeModel(), FakeModel()
        report = assess_with_models(
            valid, sessions(first, second),
            generated_content_transfer_allowed=True,
        )
        self.assertEqual("AI_ASSESSED_PASS", report["status"])
        self.assertEqual((2, 2), (first.calls, second.calls))
        for mode in ("missing-interaction", "empty-logic", "missing-rules",
                     "unknown-mode", "mixed-scoring"):
            altered = json.loads(valid)
            item = altered["activities"][0]
            if mode == "missing-interaction":
                item.pop("interaction")
            elif mode == "empty-logic":
                item["interaction"].pop("correctSelections")
            elif mode == "missing-rules":
                item.pop("diagnosticRules")
            elif mode == "unknown-mode":
                item["interactionMode"] = "freeform"
            else:
                item["answerKey"] = {"correct": "one"}
            invalid = json.dumps(altered).encode()
            with self.subTest(mode=mode), self.assertRaisesRegex(
                ValueError, "V3_INVALID_ACTIVITIES"
            ):
                package_identity(invalid)
            no_call_a, no_call_b = FakeModel(), FakeModel()
            with self.subTest(mode=mode), self.assertRaisesRegex(
                ValueError, "V3_INVALID_ACTIVITIES"
            ):
                assess_with_models(
                    invalid, sessions(no_call_a, no_call_b),
                    generated_content_transfer_allowed=True,
                )
            self.assertEqual((0, 0), (no_call_a.calls, no_call_b.calls))

    def test_release_verifier_reuses_exact_prompt_and_aggregate_provenance(self):
        # Source-free synthetic controls: a valid-looking two-role PASS
        # must never become a release receipt after its reviewer prompt or
        # aggregate was changed, even if a caller can seal its own key.
        raw=_raw()
        original=assess_with_models(
            raw,sessions(),generated_content_transfer_allowed=True)
        for mode in ("stale-prompt","swapped-role","forged-aggregate"):
            changed=json.loads(json.dumps(original))
            if mode=="stale-prompt":
                changed["reviews"][0]["reviewers"][0]["promptSha256"]="0"*64
            elif mode=="swapped-role":
                changed["reviews"][0]["reviewers"].reverse()
            else:
                changed["independentAcademicValidationClaimed"]=True
            with self.subTest(mode=mode), self.assertRaisesRegex(
                ValueError, "V3_"
            ):
                verify_automated_release_assessment(raw,changed,checks(raw))
            with tempfile.TemporaryDirectory() as tmp:
                root=Path(tmp)
                with self.subTest(mode=mode), self.assertRaisesRegex(
                    ValueError, "V3_"
                ):
                    seal_private_release_receipt(
                        raw,changed,checks(raw),root)
                self.assertFalse((root/"autonomous-v3-release-receipt.json").exists())

    def test_even_locally_reattested_stale_model_prompt_blocks_normal_publisher(self):
        # The HMAC is only a LOCAL attestation, not source-model evidence.
        # Regenerating a valid local signature cannot rehabilitate a prompt
        # bound to another activity, review role, or package revision.
        raw=_raw()
        valid=assess_with_models(
            raw,sessions(),generated_content_transfer_allowed=True)
        with tempfile.TemporaryDirectory() as tmp:
            private=Path(tmp)
            package=private/"package.json"
            package.write_bytes(raw)
            receipt=seal_private_release_receipt(
                raw,valid,checks(raw),private)
            payload=json.loads(receipt.read_text(encoding="utf-8"))
            payload["assessment"]["reviews"][0]["reviewers"][0][
                "promptSha256"]="0"*64
            key=(private/".autonomous-v3-local-attestation.key").read_bytes()
            canonical=json.dumps({
                "assessment":payload["assessment"],"checks":payload["checks"]
            },sort_keys=True,ensure_ascii=False,separators=(",",":")).encode("utf-8")
            payload["localAttestation"]=hmac.new(key,canonical,"sha256").hexdigest()
            receipt.write_text(json.dumps(payload),encoding="utf-8")
            with self.assertRaisesRegex(ValueError,"V3_STALE_OR_FORGED_REVIEW_PROMPT"):
                read_private_release_receipt(raw,receipt)
            with self.assertRaises(ValidationFailure):
                enforce_academic_release_gate(ROOT,package,private)

    def test_release_only_status_uses_signed_review_coverage_not_zero(self):
        raw=_raw()
        original=assess_with_models(
            raw,sessions(),generated_content_transfer_allowed=True)
        with tempfile.TemporaryDirectory() as tmp:
            receipt=seal_private_release_receipt(
                raw,original,checks(raw),Path(tmp))
            status=assessment_progress(raw,release_receipt=receipt)
            self.assertEqual("AUTOMATED_TECHNICAL_ELIGIBLE",
                             status["currentTechnicalDisposition"])
            self.assertEqual(2,status["activitiesAssessed"])
            self.assertEqual(2,status["activitiesFullyModelReviewed"])
            self.assertEqual(2,status["modelConsensusPassActivities"])
            self.assertEqual(0,status["activitiesRemaining"])
            # An externally supplied but different report cannot borrow the
            # valid receipt's PASS status, even when itself schema-complete.
            different=json.loads(json.dumps(original))
            different["reviews"][0]["reviewers"][0]["decision"]["rationales"][
                "physicsAnswer"]="A different synthetic model rationale of sufficient length."
            with self.assertRaisesRegex(ValueError,"V3_"):
                assessment_progress(raw,different,release_receipt=receipt)

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

    def test_three_automatic_bounded_invocations_cover_all_eighteen(self):
        # Reproduces the earlier repeat-first-six bug: no caller-supplied
        # 'existing' object, no resets or copied model verdicts.
        source=json.loads(_raw())
        template=source["activities"][0]
        source["activities"]=[
            {**template, "id":f"concept-{i}"} for i in range(1,19)
        ]
        raw=json.dumps(source,sort_keys=True,ensure_ascii=False).encode()
        class Checkpoint:
            def __init__(self):
                self.rows={}
            def load_stage(self,name):
                return self.rows.get(name)
            def save_stage(self,name,record):
                self.rows[name]=json.loads(json.dumps(record))
        cp=Checkpoint()
        for n in (6,12,18):
            first,second=FakeModel(),FakeModel()
            report=assess_with_models(raw,sessions(first,second),
                checkpoint=cp,generated_content_transfer_allowed=True)
            self.assertEqual(n,report["activitiesAssessed"])
            self.assertEqual(6,first.calls)
            self.assertEqual(6,second.calls)
        self.assertEqual("AI_ASSESSED_PASS",report["status"])
        self.assertEqual(18,len(report["reviews"]))
        self.assertEqual(
            verify_automated_release_assessment(raw,report,checks(raw))
            ["academicQA"],"AI_ASSESSED_PASS"
        )
        repeat_a,repeat_b=FakeModel(),FakeModel()
        resumed=assess_with_models(raw,sessions(repeat_a,repeat_b),
            checkpoint=cp,generated_content_transfer_allowed=True)
        self.assertEqual("AI_ASSESSED_PASS",resumed["status"])
        self.assertEqual(0,repeat_a.calls)
        self.assertEqual(0,repeat_b.calls)

    def test_tampered_cached_consensus_and_prompt_hash_refuse_replay(self):
        class Checkpoint:
            def __init__(self):
                self.rows={}
            def load_stage(self,name):
                return self.rows.get(name)
            def save_stage(self,name,record):
                self.rows[name]=json.loads(json.dumps(record))
        raw=_raw()
        for mode in ("prompt", "status", "missing-reviewer"):
            cp=Checkpoint()
            assess_with_models(raw,sessions(),checkpoint=cp,
                generated_content_transfer_allowed=True)
            stage="v3-assessment-"+sha256(raw).hexdigest()
            row=cp.rows[stage]["reviews"][0]
            if mode=="prompt":
                row["reviewers"][0]["promptSha256"]="0"*64
            elif mode=="status":
                row["status"]="AI_REPAIR_REQUIRED"
            else:
                row["reviewers"].pop()
            first,second=FakeModel(),FakeModel()
            with self.subTest(mode=mode),self.assertRaisesRegex(
                ValueError, "V3_"
            ):
                assess_with_models(raw,sessions(first,second),
                    checkpoint=cp,generated_content_transfer_allowed=True)
            self.assertEqual(0,first.calls)
            self.assertEqual(0,second.calls)

    def test_private_progress_reports_true_partial_coverage_not_fabricated_pass(self):
        raw=_raw()
        no_evidence=assessment_progress(raw)
        self.assertEqual("PENDING_AUTOMATED_ASSESSMENT",
                         no_evidence["currentTechnicalDisposition"])
        self.assertEqual(2,no_evidence["activitiesRemaining"])
        self.assertFalse(no_evidence["publicationAuthorized"])
        first,second=FakeModel(),FakeModel()
        report=assess_with_models(raw,sessions(first,second),
            generated_content_transfer_allowed=True)
        summary=assessment_progress(raw,report)
        self.assertEqual(2,summary["activitiesAssessed"])
        self.assertEqual(0,summary["activitiesRemaining"])
        self.assertEqual(2,summary["modelConsensusPassActivities"])
        self.assertEqual("PENDING_DETERMINISTIC_RELEASE_EVIDENCE",
                         summary["currentTechnicalDisposition"])
        self.assertFalse(summary["publicationAuthorized"])
        with tempfile.TemporaryDirectory() as folder:
            target=seal_private_release_receipt(raw,report,checks(raw),Path(folder))
            accepted=assessment_progress(raw,report,release_receipt=target)
            self.assertEqual("AUTOMATED_TECHNICAL_ELIGIBLE",
                             accepted["currentTechnicalDisposition"])
            self.assertTrue(accepted["publicationAuthorized"])
            raw_changed=raw+b" "
            with self.assertRaises(ValueError):
                assessment_progress(raw_changed,report,release_receipt=target)
        spoof=json.loads(json.dumps(report))
        spoof["reviews"][0]["status"]="AI_CONSENSUS_PASS"
        spoof["reviews"][0]["reviewers"][0]["promptSha256"]="0"*64
        with self.assertRaisesRegex(ValueError,"V3_"):
            assessment_progress(raw,spoof)

    def test_v3_uncaptured_role_circuit_matches_legacy_and_preserves_healthy_role(self):
        source=json.loads(_raw())
        template=source["activities"][0]
        source["activities"]=[{**template,"id":f"concept-{i}"} for i in range(1,7)]
        raw=json.dumps(source,sort_keys=True).encode()
        class Checkpoint:
            def __init__(self):
                self.rows={}
            def load_stage(self,name):
                return self.rows.get(name)
            def save_stage(self,name,record):
                self.rows[name]=json.loads(json.dumps(record))
        class Uncaptured:
            def __init__(self):
                self.calls=0
            def ask(self,prompt,*,stage=None):
                self.calls+=1
                raise UiContractError("synthetic uncaptured Gemini UI response")
        cp=Checkpoint()
        broken,healthy=Uncaptured(),FakeModel()
        report=assess_with_models(raw,sessions(broken,healthy),
            checkpoint=cp,generated_content_transfer_allowed=True)
        self.assertEqual(2,broken.calls)
        self.assertEqual(6,healthy.calls)
        self.assertEqual(6,report["activitiesAssessed"])
        self.assertEqual("PENDING_AUTOMATED_ASSESSMENT",report["status"])
        skipped=[v for v in cp.rows.values() if isinstance(v,dict)
                 and v.get("state")=="SKIPPED_UNSENT"]
        self.assertEqual(4,len(skipped))
        self.assertTrue(all(v["requestSubmitted"] is False for v in skipped))
        progress=assessment_progress(raw,report)
        self.assertEqual(4,progress["reviewerRequestsSkippedUnsent"])
        self.assertEqual(0,progress["activitiesFullyModelReviewed"])
        again_a,again_b=FakeModel(),FakeModel()
        resumed=assess_with_models(raw,sessions(again_a,again_b),
            checkpoint=cp,generated_content_transfer_allowed=True)
        self.assertEqual(report,resumed)
        self.assertEqual((0,0),(again_a.calls,again_b.calls))

    def test_v3_prior_external_execution_denial_stops_before_other_model_calls(self):
        class Checkpoint:
            def __init__(self):
                self.rows={}
            def load_stage(self,name):
                return self.rows.get(name)
            def save_stage(self,name,record):
                self.rows[name]=json.loads(json.dumps(record))
        class Denied:
            def __init__(self):
                self.calls=0
            def ask(self,prompt,*,stage=None):
                self.calls+=1
                raise ExternalExecutionDenied("synthetic client rejection")
        cp=Checkpoint()
        denied,healthy=Denied(),FakeModel()
        with self.assertRaises(ExternalExecutionDenied):
            assess_with_models(_raw(),sessions(denied,healthy),
                checkpoint=cp,generated_content_transfer_allowed=True)
        self.assertEqual((1,0),(denied.calls,healthy.calls))
        blocked=[v for v in cp.rows.values() if isinstance(v,dict)
                 and v.get("state")=="BLOCKED_EXTERNAL"]
        self.assertEqual(1,len(blocked))
        self.assertFalse(blocked[0]["requestSubmitted"])
        retry_a,retry_b=FakeModel(),FakeModel()
        with self.assertRaisesRegex(ExternalExecutionDenied,"PREVIOUS"):
            assess_with_models(_raw(),sessions(retry_a,retry_b),
                checkpoint=cp,generated_content_transfer_allowed=True)
        self.assertEqual((0,0),(retry_a.calls,retry_b.calls))

    def test_v3_circuit_survives_all_three_bounded_invocations(self):
        source=json.loads(_raw())
        template=source["activities"][0]
        source["activities"]=[{**template,"id":f"concept-{i}"} for i in range(1,19)]
        raw=json.dumps(source,sort_keys=True).encode()
        class Checkpoint:
            def __init__(self):
                self.rows={}
            def load_stage(self,name):
                return self.rows.get(name)
            def save_stage(self,name,record):
                self.rows[name]=json.loads(json.dumps(record))
        class Uncaptured:
            def __init__(self):
                self.calls=0
            def ask(self,prompt,*,stage=None):
                self.calls+=1
                raise UiContractError("synthetic uncaptured UI response")
        cp=Checkpoint()
        for n in (6,12,18):
            unresponsive,healthy=Uncaptured(),FakeModel()
            report=assess_with_models(raw,sessions(unresponsive,healthy),
                checkpoint=cp,generated_content_transfer_allowed=True)
            self.assertEqual(n,report["activitiesAssessed"])
            self.assertEqual(2 if n==6 else 0,unresponsive.calls)
            self.assertEqual(6,healthy.calls)
        progress=assessment_progress(raw,report)
        self.assertEqual(16,progress["reviewerRequestsSkippedUnsent"])
        self.assertEqual(0,progress["activitiesFullyModelReviewed"])
        self.assertFalse(progress["publicationAuthorized"])
        self.assertEqual("RECONCILE_AMBIGUOUS_REVIEW",
                         progress["currentTechnicalDisposition"])

    def test_v3_malformed_captured_json_does_not_trip_ui_circuit(self):
        source=json.loads(_raw())
        template=source["activities"][0]
        source["activities"]=[{**template,"id":f"concept-{i}"} for i in range(1,7)]
        raw=json.dumps(source,sort_keys=True).encode()
        malformed,healthy=FakeModel(malformed=True),FakeModel()
        report=assess_with_models(raw,sessions(malformed,healthy),
            generated_content_transfer_allowed=True)
        self.assertEqual((6,6),(malformed.calls,healthy.calls))
        self.assertEqual("PENDING_AUTOMATED_ASSESSMENT",report["status"])

    def test_no_invented_visual_quota_or_fake_learner_pilot_in_prompts(self):
        prompt=make_prompt(json.loads(_raw())["activities"][0],"physics-adversary")
        self.assertIn("text-first",prompt)
        self.assertIn("UNTRUSTED DATA",prompt)
        self.assertIn("no",prompt.lower())
        self.assertNotIn("real student records",json.dumps(active_disposition()))

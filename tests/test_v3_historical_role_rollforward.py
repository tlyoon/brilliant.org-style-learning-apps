"""Real frozen BOSLA 9.6 source + real Google SDK types; NO live API calls.

The historical private owner evidence is verified separately by the native
Yoga6 source-free worker; these portable cases exercise the same real content,
immutable local checkpoint and native Gemini response adapter without credentials.
Synthetic reviewer verdicts here NEVER constitute authentic scientific QA.
"""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
from types import SimpleNamespace
import shutil
import tempfile
import unittest
from unittest.mock import patch

from app_generator.runtime.run_context import RunContext
from app_generator.runtime.v3_historical_role_rollforward import (
    stage_known_unrecoverable_section96,
)
from app_generator.runtime.v3_source_free_forward import (
    advance_source_free_until_boundary,
)
from app_generator.validation.autonomous_completion import (
    assess_with_models, package_identity, make_prompt,
)
from app_generator.gemini.v3_native_api_reviewers import (
    NativeGeminiApiConversation,
)
from tests.test_v3_authorized_execution_bridge import FakeReviewer
from tests.test_v3_native_gemini_api_reviewers import FakeTypes, config

ROOT=Path(__file__).resolve().parents[1]
COURSE=ROOT/"content"/"chapter-9"
SECTION="section-9-6"
INDEX=5


class SixthLocalUncapturedFailure(FakeReviewer):
    def ask(self, prompt: str, *, stage=None):
        self.calls += 1
        if self.calls == 6:
            raise ValueError("SYNTHETIC_NO_PROVIDER_TEXT_TO_CAPTURE")
        self.calls -= 1
        return super().ask(prompt,stage=stage)


class RealSourceRollforwardTests(unittest.TestCase):
    def setUp(self):
        temp=tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        base=Path(temp.name)
        self.private=base/"PRIVATE_NOT_REAL_OWNER"
        self.repo=ROOT
        self.course=COURSE
        self.raw=(COURSE/SECTION/"package.json").read_bytes()
        self.digest,self.items=package_identity(self.raw)
        archival="1620d15e1d645c81301997f0e42d0efbad0a7b2d123eb6b11cba9ec8c04b027f"
        if self.digest!=archival:
            # Reuse BSA-127/176's exact Git-blob EOL equivalence. The
            # real frozen original was reviewed as CRLF on Yoga6, while
            # hosted Linux CI obtains the identical Git file as LF.
            normalized=self.raw.replace(b"\r\n",b"\n")
            self.assertNotIn(b"\r",normalized)
            self.assertEqual(self.raw,normalized)
            windows=normalized.replace(b"\n",b"\r\n")
            self.assertEqual(sha256(windows).hexdigest(),archival)
            self.repo=base/"repo"
            self.course=self.repo/"content"/"chapter-9"
            shutil.copytree(COURSE,self.course)
            (self.repo/"docs").mkdir(parents=True,exist_ok=True)
            shutil.copy2(ROOT/"docs"/"acceptance_closure_chapter9.json",
                         self.repo/"docs"/"acceptance_closure_chapter9.json")
            (self.course/SECTION/"package.json").write_bytes(windows)
            self.raw=windows
            self.digest,self.items=package_identity(self.raw)
        self.assertEqual(self.digest,archival)
        cp=RunContext.create(self.private,"v3-generated-"+self.digest)
        self.sessions=(
            SimpleNamespace(
                reviewer_id="v3-gemini-api-physics",
                session_id="fixture-physics",provider_id="gemini_api",
                conversation=SixthLocalUncapturedFailure()),
            SimpleNamespace(
                reviewer_id="v3-gemini-api-semantics",
                session_id="fixture-semantics",provider_id="gemini_api",
                conversation=FakeReviewer()),
        )
        self.assessment=assess_with_models(
            self.raw,self.sessions,checkpoint=cp,
            generated_content_transfer_allowed=True,max_activities=6)
        self.assertEqual(len(self.assessment["reviews"]),6)
        self.assertEqual(self.assessment["reviews"][INDEX]["status"],"AI_UNCERTAIN")
        self.old_claim=(self.private/("v3-generated-"+self.digest)/"batches"
                        /f"v3-review-{self.digest[:12]}-005-0.json")
        self.old_bytes=self.old_claim.read_bytes()

    def stage(self):
        return stage_known_unrecoverable_section96(self.course,self.repo,self.private)

    def test_exact_authentic_section96_fork_and_restart(self):
        first=self.stage()
        self.assertEqual(first["status"],
                         "NEW_VERSIONED_SECTION96_REPAIR_STAGED_QA_NOT_AUTHORIZED")
        self.assertEqual(first["paidGeminiCalls"],0)
        self.assertFalse(first["newModelConsensusPassClaimed"])
        self.assertFalse(first["publicationAuthorized"])
        self.assertFalse(first["versionedScopeAdmitted"])
        self.assertTrue(first["oldAmbiguousProviderRolePreserved"])
        self.assertFalse(first["oldRequestReplayed"])
        new_sha=first["candidatePackageSha256"]
        revised=self.private/"historical-role-rollforward"/SECTION/new_sha
        raw=(revised/"package.json").read_bytes()
        digest,updated=package_identity(raw)
        self.assertEqual(digest,new_sha)
        self.assertNotEqual(digest,self.digest)
        self.assertEqual([a["id"] for a in updated],
                         [a["id"] for a in self.items])
        self.assertEqual([i for i,(a,b) in enumerate(zip(self.items,updated))
                          if a!=b],[INDEX])
        self.assertEqual(
            [k for k in updated[INDEX] if updated[INDEX][k]!=self.items[INDEX][k]],
            ["prompt"])
        for locale in ("en","ms","zh"):
            self.assertIn("2 cm" if locale!="zh" else "2 厘米",
                          updated[INDEX]["prompt"][locale])
            self.assertIn("8 cm" if locale!="zh" else "8 厘米",
                          updated[INDEX]["prompt"][locale])
        receipt=json.loads((revised/"review-required.json").read_text(encoding="utf8"))
        self.assertEqual(receipt["historicalRoleClaimSha256"],
                         sha256(self.old_bytes).hexdigest())
        self.assertEqual(receipt["balanceProof"]["thickToSlenderMassRatio"],4)
        review=self.private/"historical-role-review-inputs"/SECTION/first["isolatedReviewInputSha256"]
        review_sha,one=package_identity((review/"package.json").read_bytes())
        self.assertEqual(review_sha,first["isolatedReviewInputSha256"])
        self.assertEqual(len(one),1)
        self.assertEqual(one[0],updated[INDEX])
        self.assertEqual(first,self.stage())
        self.assertEqual(self.old_claim.read_bytes(),self.old_bytes)
        self.assertEqual((self.course/SECTION/"package.json").read_bytes(),self.raw)
        self.assertFalse((self.private/"frozen-original-review-attempts").exists())

    def test_exact_real_source_108_activity_combined_proposal(self):
        from app_generator.runtime.v3_auto_repair import (
            _ACTIVITY, _CHANGES,
        )
        from app_generator.runtime.v3_versioned_acceptance_scope import (
            prepare_versioned_course_proposal,
        )
        from app_generator.validation.v3_versioned_text_repair import (
            make_locale_repair, store_private_repair,
        )
        section92=(self.course/"section-9-2"/"package.json").read_bytes()
        correction,receipt=make_locale_repair(
            section92,_ACTIVITY,"ms",_CHANGES)
        store_private_repair(self.private/"repair-proposals"/"section-9-2",
                             correction,receipt)
        staged=self.stage()
        result=prepare_versioned_course_proposal(
            self.course,self.repo,self.private)
        self.assertEqual(result["status"],
                         "VERSIONED_COURSE_PROPOSAL_STAGED_NOT_ADMITTED")
        self.assertEqual(result["section96NewContentCandidateSha256"],
                         staged["candidatePackageSha256"])
        self.assertEqual(result["section96NewGeminiScientificStatus"],
                         "NEW_SECTION96_TWO_GEMINI_REVIEWS_NOT_YET_AUTHORIZED")
        self.assertFalse(result["versionedScopeAdmitted"])
        self.assertFalse(result["publicationAuthorized"])
        proposal=(self.private/"versioned-course-proposals"/
                  result["proposalSha256"]/"scope-proposal.json")
        manifest=json.loads(proposal.read_text(encoding="utf8"))
        changed=[row["section"] for row in manifest["sections"]
                 if row["originalPackageSha256"]!=row["proposedPackageSha256"]]
        self.assertEqual(changed,["section-9-2","section-9-6"])
        self.assertEqual(manifest["counts"]["revisedSection96NewGeminiConsensusPass"],0)
        self.assertTrue(manifest["section96UnrecoverableRoleReplacement"]
                        ["oldAmbiguousProviderRolePreserved"])
        self.assertIn("NEW_SECTION96_REVISED_ACTIVITY_TWO_GEMINI_REVIEW_PENDING",
                      manifest["unresolved"])
        self.assertEqual(result,prepare_versioned_course_proposal(
            self.course,self.repo,self.private))
        self.assertEqual(self.old_claim.read_bytes(),self.old_bytes)
        self.assertEqual(self.raw,(self.course/SECTION/"package.json").read_bytes())

    def test_real_sdk_valueerror_is_captured_before_rubric_on_real_96_content(self):
        from google.genai import types
        original=self.items[INDEX]
        single_raw=(json.dumps({"schema":"BOSLA_SINGLE_ORIGINAL_QA_FIXTURE",
                                "activities":[original]},ensure_ascii=False)
                    +"\n").encode("utf8")
        single_sha,_=package_identity(single_raw)
        provider_response=types.GenerateContentResponse(candidates=[
            types.Candidate(content=types.Content(parts=[
                types.Part(text="{invalid-received-json")]))])
        class ReturnedButBrokenTextAccessor:
            candidates=provider_response.candidates
            @property
            def text(self):
                raise ValueError("GOOGLE_SDK_LOCAL_TEXT_ACCESSOR_ERROR")
        class SDKModels:
            calls=0
            def generate_content(self,**kwargs):
                self.calls+=1
                return ReturnedButBrokenTextAccessor()
        models=SDKModels()
        native=NativeGeminiApiConversation(
            SimpleNamespace(models=models),FakeTypes,
            "gemini-example-flash","physics")
        sessions=(
            SimpleNamespace(reviewer_id="v3-gemini-api-physics",
                            session_id="real-source-physics",
                            provider_id="gemini_api",conversation=native),
            SimpleNamespace(reviewer_id="v3-gemini-api-semantics",
                            session_id="real-source-semantics",
                            provider_id="gemini_api",conversation=FakeReviewer()),
        )
        # An authentic original question + actual Google SDK envelope,
        # but deliberately synthetic model text. Not real scientific QA.
        private=self.private/"SDK_RECOVERY_FIXTURE"
        checkpoint=RunContext.create(private,"v3-generated-"+single_sha)
        result=assess_with_models(
            single_raw,sessions,checkpoint=checkpoint,
            generated_content_transfer_allowed=True,max_activities=1)
        self.assertEqual(result["reviews"][0]["status"],"AI_UNCERTAIN")
        self.assertEqual(models.calls,1)
        files=list(checkpoint.batches.glob("*.response.txt"))
        self.assertEqual(len(files),2)
        physics=checkpoint.batches/f"v3-review-{single_sha[:12]}-000-0"
        self.assertEqual((physics.with_suffix(".response.txt")).read_text(
            encoding="utf8"),"{invalid-received-json")
        claim=json.loads((physics.with_suffix(".json")).read_text(
            encoding="utf8"))
        self.assertEqual(claim["state"],"PARSE_FAILED")
        self.assertEqual(claim["reasonCode"],"V3_CAPTURED_PARSE_FAILED")
        self.assertEqual(claim["responseSha256"],
                         sha256(b"{invalid-received-json").hexdigest())
        self.assertEqual(models.calls,1)
        self.assertFalse(result.get("publicationAuthorized",False))

    def test_new_section96_paid_review_is_not_implicitly_authorized(self):
        from app_generator.runtime.v3_paid_review_authorization import (
            authorize_paid_v3_action,
        )
        staged=self.stage()
        with self.assertRaisesRegex(ValueError,"UNKNOWN_WORKFLOW"):
            authorize_paid_v3_action(
                "ISOLATED_CORRECTED_SECTION_9_6_ACTIVITY",
                execute=True,transfer=True,next_section=None,
                max_activities=1,
                corrected_candidate_sha256=staged["candidatePackageSha256"])
        self.assertEqual(self.old_claim.read_bytes(),self.old_bytes)

    def test_future_genuine_shaped_new_version_review_does_not_admit_course(self):
        # This is a SYNTHETIC two-reviewer test on the authentic revised
        # content. The actual owner record still has ZERO new 9.6 reviews.
        from app_generator.runtime.v3_auto_repair import _ACTIVITY,_CHANGES
        from app_generator.runtime.v3_versioned_acceptance_scope import (
            prepare_versioned_course_proposal,
        )
        from app_generator.validation.v3_versioned_text_repair import (
            make_locale_repair,store_private_repair,
        )
        old_92=(self.course/"section-9-2"/"package.json").read_bytes()
        repair_92,receipt=make_locale_repair(old_92,_ACTIVITY,"ms",_CHANGES)
        store_private_repair(self.private/"repair-proposals"/"section-9-2",
                             repair_92,receipt)
        recovered=self.stage()
        slice_sha=recovered["isolatedReviewInputSha256"]
        single=(self.private/"historical-role-review-inputs"/SECTION/slice_sha/
                "package.json").read_bytes()
        pair=(
            SimpleNamespace(reviewer_id="v3-gemini-api-physics",
                            session_id="new-version-test-p",
                            provider_id="gemini_api",
                            conversation=FakeReviewer()),
            SimpleNamespace(reviewer_id="v3-gemini-api-semantics",
                            session_id="new-version-test-s",
                            provider_id="gemini_api",
                            conversation=FakeReviewer()),
        )
        cp=RunContext.create(self.private,"v3-generated-"+slice_sha)
        assessed=assess_with_models(
            single,pair,checkpoint=cp,
            generated_content_transfer_allowed=True,max_activities=1)
        self.assertEqual(assessed["reviews"][0]["status"],"AI_CONSENSUS_PASS")
        # The proposal reads only exact-new-source, independently reviewed
        # evidence and may label it proposed, not admitted or published.
        proposal=prepare_versioned_course_proposal(
            self.course,self.repo,self.private)
        self.assertEqual(
            proposal["section96NewGeminiScientificStatus"],
            "GENUINE_REVISED_SECTION96_GEMINI_PASS_NOT_ADMITTED")
        self.assertFalse(proposal["versionedScopeAdmitted"])
        self.assertFalse(proposal["publicationAuthorized"])
        self.assertEqual(self.old_claim.read_bytes(),self.old_bytes)

    def test_changed_old_claim_fails_closed_without_new_candidate(self):
        damaged=json.loads(self.old_bytes)
        damaged["reasonCode"]="ServerError"
        self.old_claim.write_text(json.dumps(damaged),encoding="utf8")
        blocked=self.stage()
        self.assertEqual(blocked["status"],
                         "STOP_UNTRUSTED_UNRECOVERABLE_ROLE_SIGNATURE")
        self.assertFalse((self.private/"historical-role-rollforward").exists())

    def test_found_original_raw_response_must_be_reconciled_first(self):
        path=self.old_claim.with_suffix(".response.txt")
        path.write_text("{raw-but-not-attributed}",encoding="utf8")
        result=self.stage()
        self.assertEqual(result["status"],
                         "STOP_ORIGINAL_RESPONSE_EVIDENCE_MUST_RECONCILE")
        self.assertFalse((self.private/"historical-role-rollforward").exists())

    def test_crash_after_candidate_before_review_input_resumes(self):
        from app_generator.runtime import v3_historical_role_rollforward as impl
        real=impl.store_private_repair
        counter=[0]
        def interrupted(*args,**kwargs):
            counter[0]+=1
            if counter[0]==2:
                raise OSError("SYNTHETIC_POWER_LOSS_BEFORE_REVIEW_INPUT")
            return real(*args,**kwargs)
        with patch.object(impl,"store_private_repair",side_effect=interrupted):
            with self.assertRaisesRegex(OSError,"SYNTHETIC_POWER_LOSS"):
                self.stage()
        self.assertTrue((self.private/"historical-role-rollforward").exists())
        success=self.stage()
        self.assertEqual(success["status"],
                         "NEW_VERSIONED_SECTION96_REPAIR_STAGED_QA_NOT_AUTHORIZED")
        self.assertEqual(self.old_claim.read_bytes(),self.old_bytes)

    def test_real_source_normal_source_free_pipeline_dispatch(self):
        before=self.old_claim.read_bytes()
        # The portable private fixture intentionally has NO genuine 9.2
        # reviewer FAIL; unrelated BSA-174's legitimate evidence-bound
        # repair is stubbed while the real Section 9.6 recovery executes.
        no_92=lambda *args: {
            "repairStatus":"NO_SCRIPT_BLOCKER", "repairStaged":False,
            "publicationAuthorized":False}
        result=advance_source_free_until_boundary(
            self.course,self.repo,self.private,repair=no_92)
        recovery=result["historicalUnrecoverableRoleRecovery"]
        self.assertEqual(recovery["status"],
                         "NEW_VERSIONED_SECTION96_REPAIR_STAGED_QA_NOT_AUTHORIZED")
        self.assertEqual(result["providerCapacity"],
                         "STOP_UNCLASSIFIED_PROVIDER_REVIEW")
        self.assertEqual(result["stagedImmutableOriginalTailSlices"],12)
        self.assertEqual(result["paidGeminiCalls"],0)
        self.assertFalse(result["publicationAuthorized"])
        self.assertFalse(recovery["newModelConsensusPassClaimed"])
        self.assertEqual(before,self.old_claim.read_bytes())
        again=advance_source_free_until_boundary(
            self.course,self.repo,self.private,repair=no_92)
        self.assertEqual(again["historicalUnrecoverableRoleRecovery"],recovery)
        self.assertEqual(again["checkpointIntegritySha256"],
                         result["checkpointIntegritySha256"])


class RealSdkResponseEnvelopeTests(unittest.TestCase):
    def test_real_google_genai_candidate_after_text_accessor_valueerror(self):
        from google.genai import types
        from app_generator.validation.autonomous_completion import package_identity
        item=package_identity(
            (COURSE/SECTION/"package.json").read_bytes())[1][INDEX]
        prompt=make_prompt(item,"physics-adversary")
        actual=types.GenerateContentResponse(candidates=[
            types.Candidate(content=types.Content(parts=[
                types.Part(text='{"provider":"returned-text", "status":"capturable"}')
            ]))
        ])
        class BrokenAccessor:
            candidates=actual.candidates
            @property
            def text(self):
                raise ValueError("SDK .text property raised after response return")
        class Models:
            calls=0
            def generate_content(self,**kwargs):
                self.calls+=1
                return BrokenAccessor()
        model=Models()
        conversation=NativeGeminiApiConversation(
            SimpleNamespace(models=model),FakeTypes,
            "gemini-example-flash","physics")
        answer=conversation.ask(prompt,stage="academic-v3-autonomous")
        self.assertEqual(answer,
                         '{"provider":"returned-text", "status":"capturable"}')
        self.assertEqual(model.calls,1)
        with self.assertRaisesRegex(ValueError,"ALREADY_SUBMITTED"):
            conversation.ask(prompt,stage="academic-v3-autonomous")
        self.assertEqual(model.calls,1)

    def test_mixed_or_multiple_candidates_still_fail_closed(self):
        from google.genai import types
        item=package_identity(
            (COURSE/SECTION/"package.json").read_bytes())[1][INDEX]
        prompt=make_prompt(item,"physics-adversary")
        class BrokenAccessor:
            def __init__(self,candidates):
                self.candidates=candidates
            @property
            def text(self):
                raise ValueError("synthetic accessor fault")
        one=types.Candidate(content=types.Content(parts=[
            types.Part(text='{"x":"only"}')]))
        cases=[
            [one,one],
            [types.Candidate(content=types.Content(parts=[
                types.Part(function_call=types.FunctionCall(name="unsafe",
                                                            args={"x":1}))]))],
            [types.Candidate(content=types.Content(parts=[]))],
        ]
        for parts in cases:
            with self.subTest(mode=len(parts)):
                model=SimpleNamespace(
                    generate_content=lambda **_: BrokenAccessor(parts))
                convo=NativeGeminiApiConversation(
                    SimpleNamespace(models=model),FakeTypes,
                    "gemini-example-flash","physics")
                with self.assertRaisesRegex(ValueError,"JSON_RESPONSE_ONLY"):
                    convo.ask(prompt,stage="academic-v3-autonomous")

if __name__=="__main__":
    unittest.main()

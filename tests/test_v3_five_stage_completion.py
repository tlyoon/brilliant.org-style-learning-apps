"""BSA221 owner five-stage contract: fake-only functional and fault controls.

No mock results here are real Chapter9 science, institutional permission,
Genuine CI, Chrome release acceptance or production publication authority.
"""
from contextlib import ExitStack
from copy import deepcopy
from pathlib import Path
import json
import os
from subprocess import CompletedProcess
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from app_generator.runtime import v3_five_stage_completion as v
from app_generator.runtime import v3_versioned_readiness as readiness_mod
from app_generator.runtime import v3_public_bundle_handoff as bundle_handoff
from app_generator.runtime import v3_public_deployment_scope as scope
from app_generator.runtime import v3_pinned_public_release_proposal as proposal
from app_generator.runtime import v3_public_release_browser_acceptance as browser_stage
from app_generator.runtime import v3_private_public_patch_rehearsal as v11_stage
from app_generator.runtime import v3_private_nonmerging_pr_readiness as v12_stage
from app_generator.runtime import v3_public_nonmerging_draft_pr as v13_stage
from scripts import run_v3_yoga6_recovery_worker as worker


class FiveStageSyntheticTests(unittest.TestCase):
    def setUp(self):
        folder=TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.root=Path(folder.name)
        self.repo=self.root/"repo"
        self.repo.mkdir()
        # Mocked child process contract still requires a real mock script
        # entrypoint on disk: don't relax the production safety guard.
        child=self.repo/"scripts"/"run_v3_yoga6_five_stage.py"
        child.parent.mkdir()
        child.write_text("synthetic only")
        # Fake-only reference summaries with the later C3 status taking
        # precedence over obsolete HTTP402. Never copy real private PDFs.
        docs=self.repo/"docs"
        docs.mkdir()
        (docs/"FINITE_GLOBAL_CODEBASE_DISPOSITION_20261104.md").write_text(
            "CURRENT-STATUS CORRECTION: FAILED_LIMITED_CAMPAIGN")
        (docs/"C3_POST_BILLING_RECONCILIATION_20261104.md").write_text(
            "PROVIDER_ACCESS_RECOVERED, FAILED_LIMITED_CAMPAIGN, "
            "RESPONSE_CONTRACT_ERROR, No third campaign, "
            "zero responsive checks")
        gate=self.repo/"app_generator"/"runtime"
        gate.mkdir(parents=True)
        (gate/"academic_release.py").write_text(
            "def enforce_academic_release_gate(x): "
            "return read_private_release_receipt(x)")
        self.local=self.root/"local"
        self.private=self.local/"Microvid"/"owner"
        self.private.mkdir(parents=True)
        self.head="a"*40
        self.source="b"*64
        self.readiness={
            "status":"VERSIONED_SCIENCE_BROWSER_AND_CI_VERIFIED_UNADMITTED",
            "sourceVersionOnly":True,
            "publicationAuthorized":False,
            "exactHeadHostedCiSuccess":True,
            "codeWorkingTreeClean":True,
            "proposedContentScientificCoverage":108,
            "realChromeChecks":698,"realChromeActivities":108,
            "gitHead":self.head,"proposalSha256":self.source,
            "integritySha256":"c"*64,"browserReceiptSha256":"d"*64,
        }
        self.packages=[(n,json.dumps({"activities":[{"id":f"i{i}"} for i in range(18)]}).encode("utf8"),
                       [{"id":str(i)} for i in range(18)]) for n in range(1,7)]
        self.browser={"renderedChecks":698,"all108ActivitiesVisited":True,
                      "allLocaleViewportPromptChecks":648}
        self.calls={"stage":0,"browser":0}

    def _stage(self,path,packages):
        self.calls["stage"]+=1
        app=path/"app"
        app.mkdir()
        (app/"rc1-chapter9-draft.html").write_text("trusted test-only")
        for i in range(16):
            (app/f"module-{i}.js").write_text(f"fixture source {i}")
        for number,raw,_ in packages:
            dest=(path/"content"/"chapter-9"/f"section-9-{number}"/"package.json")
            dest.parent.mkdir(parents=True)
            dest.write_bytes(raw)
        roster=path/"local-pilot"
        roster.mkdir()
        (roster/"roster.json").write_text("{}")

    def _exercise(self,path,packages):
        self.calls["browser"]+=1
        # Real browser is tested separately in live Yoga6 normal path.
        return self.browser

    def invoke(self,*,exercise=True):
        with ExitStack() as stack:
            stack.enter_context(patch.dict(os.environ,
                {"LOCALAPPDATA":str(self.local)}))
            stack.enter_context(patch.object(v,"_read_previous",
                return_value=self.readiness))
            stack.enter_context(patch.object(v,"_source_bound_packages",
                return_value=(self.source,self.packages)))
            stack.enter_context(patch.object(v,"_static_privacy",
                return_value={
                    "sourceContentSensitiveFieldCount":0,
                    "checkedRuntimeSourceFiles":6,
                    "personalStudentRecordsUsed":False,
                    "institutionalPrivacyCertificationClaimed":False,
                    "technicalPrivacyChecksPassed":True,
                }))
            stack.enter_context(patch.object(v,"_stage_site",
                side_effect=self._stage))
            stack.enter_context(patch.object(v,"_exercise",
                side_effect=self._exercise))
            stack.enter_context(patch.object(readiness_mod,
                "_git_info",return_value=(self.head,"feature/test")))
            stack.enter_context(patch.object(readiness_mod,
                "_git_clean",return_value=True))
            return v.run_five_stage_completion(
                self.repo,self.private,self.readiness,
                exercise_candidate=exercise,native_release_adapter=False)

    def test_owner_five_stages_advance_without_publication(self):
        answer=self.invoke()
        self.assertEqual(answer["completedStageCount"],5)
        self.assertEqual(answer["realPrivateCandidateBrowserChecks"],698)
        self.assertTrue(answer["versionedCourseInternalAdmission"])
        self.assertFalse(answer["publicV3ReleaseReceiptMinted"])
        self.assertFalse(answer["publicationAuthorized"])
        self.assertEqual(self.calls["browser"],1)
        self.assertTrue(answer["sourceFreeDownstreamAdapterVerified"])
        self.assertEqual(
            answer["historicalFiniteC3Result"],
            "C3_FAILED_LIMITED_CAMPAIGN_RECONCILED_READ_ONLY")
        self.assertTrue(all(x["status"] in (
            "PASS_PRIVATE_ONLY","READY_FOR_NEXT_AUTHORIZED_STAGE")
            for x in answer["stages"]))

    def test_saved_checkpoints_resume_idempotently_without_second_browser(self):
        first=self.invoke()
        later=self.invoke(exercise=False)
        self.assertEqual(first,later)
        self.assertEqual(self.calls["browser"],1)

    def test_corrupt_source_content_in_staged_private_candidate_rejected(self):
        self.invoke()
        staged=v._candidate_dir(self.private,self.head,self.source)
        target=staged/"content"/"chapter-9"/"section-9-1"/"package.json"
        target.write_bytes(b"corruption")
        with self.assertRaisesRegex(ValueError,
                "STALE_EXISTING_CANDIDATE"):
            self.invoke(exercise=False)

    def test_corrupt_staged_javascript_rejected_on_restart(self):
        self.invoke()
        staged=v._candidate_dir(self.private,self.head,self.source)
        (staged/"app"/"module-6.js").write_text("malicious")
        with self.assertRaisesRegex(ValueError,
                "STALE_EXISTING_CANDIDATE"):
            self.invoke(exercise=False)

    def test_unauthorized_publication_rejected_before_checkpoint_write(self):
        with TemporaryDirectory() as root:
            folder=Path(root)
            payload={"gitHead":self.head,"proposalSha256":self.source,
                     "status":"PASS_PRIVATE_ONLY",
                     "publicationAuthorized":True,
                     "publicDeployExecuted":False}
            with self.assertRaisesRegex(ValueError,"UNSAFE_RELEASE_CLAIM"):
                v._save_stage(folder,v._STAGE_NAMES[0],payload)

    def test_tampered_signed_checkpoint_fails_closed(self):
        self.invoke()
        file=(self.private/v._BASE/self.head/self.source/
              (v._STAGE_NAMES[0]+".json"))
        saved=json.loads(file.read_text())
        saved["publicationAuthorized"]=True
        file.write_text(json.dumps(saved))
        with self.assertRaisesRegex(ValueError,"CHECKPOINT_INTEGRITY_ERROR"):
            self.invoke(exercise=False)

    def test_future_stage_executes_real_sourcefree_historical_c3_precedence(self):
        answer=self.invoke()
        self.assertTrue(answer["sourceFreeDownstreamAdapterVerified"])
        stage=(self.private/v._BASE/self.head/self.source/
               (v._STAGE_NAMES[4]+".json"))
        doc=json.loads(stage.read_text(encoding="utf8"))
        history=doc["historicalFiniteC3Reconciliation"]
        self.assertTrue(doc["sourceFreeDownstreamWorkExecuted"])
        self.assertEqual(history["completedDraftsInRecordedReconciliation"],2)
        self.assertTrue(history["historicalProvider402SupersededByAuthenticatedSourceFreeRecovery"])
        self.assertFalse(history["historicalThirdCampaignAllowed"])
        self.assertEqual(history["newSourceBearingPDFCalls"],0)
        self.assertFalse(doc["publicationAuthorized"])

    def test_older_http402_without_later_reconciliation_must_fail_closed(self):
        self.repo.joinpath(
            "docs","C3_POST_BILLING_RECONCILIATION_20261104.md"
        ).write_text("BLOCKED_EXTERNAL only")
        with self.assertRaisesRegex(ValueError,
                "C3_STALE_OR_CONTRADICTORY_HISTORY"):
            self.invoke()
        self.assertFalse((self.private/v._BASE/self.head/self.source/
                  (v._STAGE_NAMES[4]+".json")).exists())

    def test_existing_public_release_gate_must_remain_attested(self):
        gate=self.repo/"app_generator"/"runtime"/"academic_release.py"
        gate.write_text("def unsafe_release(): return True")
        with self.assertRaisesRegex(ValueError,
                "PUBLIC_V3_GATE_WEAKENED"):
            self.invoke()

    def test_broken_private_qa_does_not_become_real_acceptance(self):
        self.browser["renderedChecks"]=697
        with self.assertRaisesRegex(ValueError,
                "REAL_PREVIEW_BROWSER_DID_NOT_PASS"):
            self.invoke()
        self.assertFalse((self.private/v._BASE/self.head/self.source/
                (v._STAGE_NAMES[3]+".json")).exists())

    def test_missing_real_chrome_never_mock_accepted(self):
        with self.assertRaisesRegex(ValueError,
                "REAL_PREVIEW_BROWSER_REQUIRED"):
            self.invoke(exercise=False)

    def test_missing_model_source_readiness_fails_without_any_stage(self):
        self.readiness["proposedContentScientificCoverage"]=107
        with self.assertRaisesRegex(ValueError,
                "GENUINE_READINESS_REQUIRED"):
            self.invoke()
        self.assertEqual(self.calls["stage"],0)

    def test_stale_git_ci_fails_without_any_stage(self):
        self.readiness["exactHeadHostedCiSuccess"]=False
        with self.assertRaisesRegex(ValueError,
                "GENUINE_READINESS_REQUIRED"):
            self.invoke()
        self.assertEqual(self.calls["stage"],0)

    def test_source_repo_changed_during_run_fails_closed(self):
        with patch.dict(os.environ,{"LOCALAPPDATA":str(self.local)}):
            with patch.object(readiness_mod,"_git_clean",return_value=False):
                with self.assertRaisesRegex(ValueError,"GENUINE_READINESS_REQUIRED"):
                    v.run_five_stage_completion(
                        self.repo,self.private,
                        {**self.readiness,"codeWorkingTreeClean":False})

    def test_strict_private_root_refuses_repository_location(self):
        with patch.dict(os.environ,{"LOCALAPPDATA":str(self.local)}):
            with self.assertRaisesRegex(ValueError,
                    "UNSAFE_WORKSTATION_ROOT"):
                v.run_five_stage_completion(
                    self.repo,self.repo,self.readiness)

    def test_unauthorized_source_asset_extension_rejected(self):
        self.invoke()
        site=v._candidate_dir(self.private,self.head,self.source)
        (site/"copied-textbook.pdf").write_bytes(b"fake PDF")
        with self.assertRaisesRegex(ValueError,
                "UNAUTHORIZED_CANDIDATE_ASSET"):
            self.invoke(exercise=False)

    def test_private_student_field_detected(self):
        fake=self.packages
        fake[0][2][0]["studentEmail"]="secret"
        source=self.repo/"app"
        source.mkdir()
        for key in ("app.js","course-preview.js","rc1-chapter9-bridge.js",
                    "rc1-course-routing.js","rc1-course-diagnostic.js",
                    "visual-renderers.js"):
            (source/key).write_text("safe")
        with self.assertRaisesRegex(ValueError,
                "PRIVATE_STUDENT_FIELD_IN_CONTENT"):
            v._static_privacy(self.repo,fake)

    def test_nonlocal_exfiltration_api_detected(self):
        source=self.repo/"app"
        source.mkdir()
        for key in ("app.js","course-preview.js","rc1-chapter9-bridge.js",
                    "rc1-course-routing.js","rc1-course-diagnostic.js",
                    "visual-renderers.js"):
            (source/key).write_text("safe")
        (source/"app.js").write_text("navigator.sendBeacon('/outside', 'raw')")
        with self.assertRaisesRegex(ValueError,
                "UNAPPROVED_EXTERNAL_PRIVACY_API"):
            v._static_privacy(self.repo,self.packages)

    def test_existing_fake_status_cannot_claim_human_privacy_certification(self):
        self.invoke()
        receipt=(self.private/v._BASE/self.head/self.source/
                 (v._STAGE_NAMES[1]+".json"))
        doc=json.loads(receipt.read_text())
        self.assertFalse(doc["institutionalPrivacyCertificationClaimed"])
        self.assertFalse(doc["publicationAuthorized"])

    def test_normal_dispatcher_real_child_reused_without_api(self):
        outcome={"status":"FIVE_STAGE_PRIVATE_TECHNICAL_PATH_COMPLETE_NO_PUBLICATION",
            "completedStageCount":5,"proposalSha256":self.source,
            "gitHead":self.head,"publicationAuthorized":False,
            "paidGeminiCalls":0,"realPrivateCandidateBrowserChecks":698,
            "technicalV3ReleaseAttestationsVerified":True,
            "privateNativeV3Attestations":6}
        with ExitStack() as stack:
            from scripts import run_v3_yoga6_acceptance
            stack.enter_context(patch.object(
                run_v3_yoga6_acceptance,"_browser_python",
                return_value=Path("pinned-python")))
            stack.enter_context(patch.object(v.subprocess,"run",
                return_value=CompletedProcess(["pinned"],0,
                    json.dumps(outcome),"")))
            got=v.advance_five_stage_on_pinned_browser(
                self.repo,self.private,self.readiness)
        self.assertEqual(got["browserChildAttempts"],1)
        self.assertFalse(got["publicationAuthorized"])

    def test_transient_child_retry_at_most_once(self):
        denied={"status":"STOP_FIVE_STAGE_AUTONOMOUS_COMPLETION",
                "errorClass":"TimeoutException"}
        pass_result={
            "status":"FIVE_STAGE_PRIVATE_TECHNICAL_PATH_COMPLETE_NO_PUBLICATION",
            "completedStageCount":5,"proposalSha256":self.source,
            "gitHead":self.head,"publicationAuthorized":False,
            "paidGeminiCalls":0,"realPrivateCandidateBrowserChecks":698,
            "technicalV3ReleaseAttestationsVerified":True,
            "privateNativeV3Attestations":6}
        with ExitStack() as stack:
            from scripts import run_v3_yoga6_acceptance
            stack.enter_context(patch.object(
                run_v3_yoga6_acceptance,"_browser_python",
                return_value=Path("pinned-python")))
            trial=stack.enter_context(patch.object(v.subprocess,"run",
                side_effect=[
                    CompletedProcess([],3,json.dumps(denied),""),
                    CompletedProcess([],0,json.dumps(pass_result),""),
                ]))
            got=v.advance_five_stage_on_pinned_browser(
                self.repo,self.private,self.readiness)
        self.assertEqual(got["browserChildAttempts"],2)
        self.assertEqual(trial.call_count,2)

    def test_real_normal_sourcefree_worker_dispatches_all_five_without_model(self):
        with ExitStack() as stack:
            stack.enter_context(patch.dict(os.environ,
                {"LOCALAPPDATA":str(self.local)}))
            stack.enter_context(patch.object(
                worker,"checked_private_root",return_value=self.private))
            stack.enter_context(patch.object(
                worker,"require_authorized_native_review_host"))
            stack.enter_context(patch.object(
                worker,"advance_source_free_until_boundary",
                return_value={"publicationAuthorized":False}))
            browser={
                "status":"ACTUAL_UNADMITTED_CHAPTER9_BROWSER_QA_PASS",
                "proposalSha256":self.source,
                "renderedChecks":698,
                "all108ActivitiesVisited":True,
                "allLocaleViewportPromptChecks":648,
            }
            stack.enter_context(patch.object(
                worker,"_complete_source_free_with_browser",
                return_value={
                    "proposalSha256":self.source,
                    "finalTwoScienceIntegrated":True,
                    "paidGeminiCalls":0,
                    "publicationAuthorized":False,
                    "realCandidateBrowserAcceptance":browser,
                }))
            stack.enter_context(patch.object(
                readiness_mod,"evaluate_current_versioned_evidence",
                return_value=self.readiness))
            expected={
                "status":"FIVE_STAGE_PRIVATE_TECHNICAL_PATH_COMPLETE_NO_PUBLICATION",
                "completedStageCount":5,
                "publicationAuthorized":False,
                "paidGeminiCalls":0,
            }
            five=stack.enter_context(patch.object(
                v,"advance_five_stage_on_pinned_browser",
                return_value=expected))
            release=stack.enter_context(patch.object(
                bundle_handoff,"dispatch_private_public_bundle_build",
                return_value={
                    "status":"SIX_REAL_PUBLIC_BUNDLE_BUILDS_VERIFIED_PRIVATE_NO_DEPLOY",
                    "realOriginalPublicBuilderInvocations":6,
                    "publicationAuthorized":False,"publicDeployExecuted":False,
                }))
            audit=stack.enter_context(patch.object(
                scope,"verify_public_deployment_scope",
                return_value={
                    "status":"EXISTING_PUBLIC_SIX_SECTION_SCOPE_AND_PERMISSION_VERIFIED_NO_DEPLOY",
                    "packagesRequiringUpdates":3,
                    "individualChangedActivities":5,
                    "publicDeployExecuted":False,
                }))
            proposal_mock=stack.enter_context(patch.object(
                proposal,"stage_pinned_private_public_proposal",
                return_value={
                    "status":"THREE_ROUTE_PRIVATE_PINNED_RELEASE_PROPOSAL_READY_NO_PUBLIC_WRITE",
                    "productionReleaseBuilderInvocations":3,
                    "publicDeployExecuted":False,
                }))
            browser_mock=stack.enter_context(patch.object(
                browser_stage,"run_private_release_browser_acceptance",
                return_value={
                    "status":"THREE_PRIVATE_PRODUCTION_BUNDLES_REAL_CHROME_RENDERED_NO_PUBLIC_WRITE",
                    "realHeadlessChromeRoutesPassed":3,
                    "publicDeployExecuted":False,
                }))
            v11_mock=stack.enter_context(patch.object(
                v11_stage,"stage_exact_private_public_patch",
                return_value={
                    "status":"PINNED_THREE_SECTION_PRIVATE_PUBLIC_PATCH_REHEARSED_NO_PUBLIC_WRITE",
                    "changedFileCount":21,"publicDeployExecuted":False,
                }))
            v12_mock=stack.enter_context(patch.object(
                v12_stage,"stage_private_nonmerging_pr_draft",
                return_value={
                    "status":"PRIVATE_SCOPED_NONMERGING_PR_DRAFT_VERIFIED_NO_REMOTE_WRITE",
                    "changedFileCount":21,
                    "publicPRCreated":False,"publicDeployExecuted":False,
                }))
            v13_mock=stack.enter_context(patch.object(
                v13_stage,"dispatch_scoped_nonmerging_public_pr",
                return_value={
                    "status":"SCOPED_PUBLIC_DRAFT_PR_OPEN_UNMERGED_MAIN_UNCHANGED",
                    "publicPullRequestDraft":True,
                    "publicMergeExecuted":False,
                    "publicDeployExecuted":False,
                    "publicBaseMainPinnedSha":"eb86fe8eb94ec33f8c0c055d2423b245e5898241",
                }))
            observed=[]
            stack.enter_context(patch.object(worker,"_print",
                                              side_effect=observed.append))
            status=worker.main(["--source-free-advance"])
        self.assertEqual(status,0)
        self.assertEqual(five.call_count,1)
        self.assertEqual(release.call_count,1)
        self.assertEqual(audit.call_count,1)
        self.assertEqual(proposal_mock.call_count,1)
        self.assertEqual(browser_mock.call_count,1)
        self.assertEqual(v11_mock.call_count,1)
        self.assertEqual(v12_mock.call_count,1)
        self.assertEqual(v13_mock.call_count,1)
        self.assertEqual(observed[-1]["fiveStageAutonomousCompletion"],expected)
        self.assertEqual(observed[-1]["paidGeminiCalls"],0)
        self.assertFalse(observed[-1]["publicationAuthorized"])

    def test_real_normal_worker_refuses_fake_five_stage_success(self):
        with ExitStack() as stack:
            stack.enter_context(patch.dict(os.environ,
                {"LOCALAPPDATA":str(self.local)}))
            stack.enter_context(patch.object(
                worker,"checked_private_root",return_value=self.private))
            stack.enter_context(patch.object(
                worker,"require_authorized_native_review_host"))
            stack.enter_context(patch.object(
                worker,"advance_source_free_until_boundary",
                return_value={"publicationAuthorized":False}))
            stack.enter_context(patch.object(
                worker,"_complete_source_free_with_browser",
                return_value={
                    "proposalSha256":self.source,
                    "finalTwoScienceIntegrated":True,
                    "paidGeminiCalls":0,
                    "publicationAuthorized":False,
                    "realCandidateBrowserAcceptance":{
                        "status":"ACTUAL_UNADMITTED_CHAPTER9_BROWSER_QA_PASS",
                        "proposalSha256":self.source,"renderedChecks":698,
                        "all108ActivitiesVisited":True,
                        "allLocaleViewportPromptChecks":648,
                    },
                }))
            stack.enter_context(patch.object(
                readiness_mod,"evaluate_current_versioned_evidence",
                return_value=self.readiness))
            stack.enter_context(patch.object(
                v,"advance_five_stage_on_pinned_browser",
                return_value={
                    "status":"STOP_FIVE_STAGE_NORMAL_PIPELINE",
                    "publicationAuthorized":False,
                }))
            stack.enter_context(patch.object(worker,"_print"))
            status=worker.main(["--source-free-advance"])
        self.assertEqual(status,3)

    def test_semantic_privacy_source_error_never_retried(self):
        denied={"status":"STOP_FIVE_STAGE_AUTONOMOUS_COMPLETION",
                "errorClass":"ValueError",
                "errorCode":"V3_FIVE_STAGE_PRIVATE_STUDENT_FIELD_IN_CONTENT"}
        with ExitStack() as stack:
            from scripts import run_v3_yoga6_acceptance
            stack.enter_context(patch.object(
                run_v3_yoga6_acceptance,"_browser_python",
                return_value=Path("pinned-python")))
            trial=stack.enter_context(patch.object(v.subprocess,"run",
                return_value=CompletedProcess([],3,json.dumps(denied),"")))
            got=v.advance_five_stage_on_pinned_browser(
                self.repo,self.private,self.readiness)
        self.assertEqual(trial.call_count,1)
        self.assertEqual(got["status"],"STOP_FIVE_STAGE_NORMAL_PIPELINE")
        self.assertFalse(got["publicationAuthorized"])


if __name__=="__main__":
    unittest.main()

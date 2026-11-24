"""BSA224 exact-head hosted CI race: no future manual repeat of sourcefree.

All records, GH statuses and model/browser outputs here are synthetically
injected. Never contact GitHub, Gemini, PDFs or student services in tests.
"""
from contextlib import ExitStack
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from app_generator.runtime import v3_ci_resume as ci
from app_generator.runtime import v3_versioned_readiness as actual
from app_generator.runtime import v3_five_stage_completion as five
from app_generator.runtime import v3_public_bundle_handoff as bundle
from app_generator.runtime import v3_public_deployment_scope as scope
from app_generator.runtime import v3_pinned_public_release_proposal as proposal
from app_generator.runtime import v3_public_release_browser_acceptance as browser_stage
from app_generator.runtime import v3_private_public_patch_rehearsal as v11_stage
from app_generator.runtime import v3_private_nonmerging_pr_readiness as v12_stage
from app_generator.runtime import v3_public_nonmerging_draft_pr as v13_stage
from app_generator.runtime import v3_public_pr_independent_browser_acceptance as v14_stage
from app_generator.runtime import v3_global_post_pr_readonly_roadmap as v15_stage
from app_generator.runtime import v3_public_pr_security_accessibility as v16_stage
from scripts import run_v3_yoga6_recovery_worker as worker


class ExactCommitHostedCiQueryTests(unittest.TestCase):
    """BSA238: CI on a differently named GitHub branch remains discoverable."""

    def setUp(self):
        self.head="a"*40
        self.local="feature/local-audit-alias"
        self.green={"headSha":self.head,"status":"completed",
                    "conclusion":"success","databaseId":71}

    def test_alias_branch_queries_exact_commit_required_workflow(self):
        from subprocess import CompletedProcess
        import json
        with patch.object(actual,"_git_info",return_value=(
                 self.head,self.local)),patch.object(
                 actual.subprocess,"run",return_value=CompletedProcess(
                 [],0,stdout=json.dumps([self.green]))) as gh:
            runs=actual._hosted_runs(Path("."),self.local)
        argv=gh.call_args.args[0]
        self.assertIn("-c",argv)
        self.assertEqual(argv[argv.index("-c")+1],self.head)
        self.assertEqual(argv[argv.index("-w")+1],"validate.yml")
        self.assertNotIn("-b",argv)
        self.assertTrue(actual._exact_ci_success(runs,self.head))

    def test_branch_identity_mismatch_prevents_remote_read(self):
        with patch.object(actual,"_git_info",return_value=(
             self.head,self.local)),patch.object(
             actual.subprocess,"run") as gh:
            self.assertEqual(actual._hosted_runs(
                Path("."),"feature/unknown-other"),[])
        gh.assert_not_called()

    def test_wrong_sha_success_cannot_admit_CI(self):
        from subprocess import CompletedProcess
        import json
        fake={**self.green,"headSha":"f"*40}
        with patch.object(actual,"_git_info",return_value=(
             self.head,self.local)),patch.object(
             actual.subprocess,"run",return_value=CompletedProcess(
             [],0,stdout=json.dumps([fake]))):
            runs=actual._hosted_runs(Path("."),self.local)
        self.assertFalse(actual._exact_ci_success(runs,self.head))

    def test_failed_GitHub_query_fails_closed(self):
        from subprocess import CompletedProcess
        with patch.object(actual,"_git_info",return_value=(
             self.head,self.local)),patch.object(
             actual.subprocess,"run",return_value=CompletedProcess(
             [],1,stdout="")):
            self.assertEqual(actual._hosted_runs(Path("."),self.local),[])


class ExactHeadCIBoundedRecoveryTests(unittest.TestCase):
    def setUp(self):
        folder=TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.root=Path(folder.name)
        self.head="a"*40
        self.proposal="b"*64
        self.pending={
            "status":ci._WAIT,"gitHead":self.head,
            "proposalSha256":self.proposal,
            "codeWorkingTreeClean":True,
            "exactHeadHostedCiSuccess":False,
            "publicationAuthorized":False,
            "sourceVersionOnly":True,
            "realChromeChecks":698,
            "proposedContentScientificCoverage":108,
        }
        self.success={
            **self.pending,"status":ci._GREEN,
            "exactHeadHostedCiSuccess":True,
            "publicationAuthorized":False,
        }
        self.finished={"headSha":self.head,"status":"completed",
                       "conclusion":"success","databaseId":123}
        self.inflight={"headSha":self.head,"status":"in_progress",
                       "conclusion":"","databaseId":123}

    def run_fake(self,sequence,max_wait=2):
        with ExitStack() as stack:
            stack.enter_context(patch.object(
                actual,"_git_info",return_value=(self.head,"feature/test")))
            stack.enter_context(patch.object(
                actual,"_git_clean",return_value=True))
            gh=stack.enter_context(patch.object(
                actual,"_hosted_runs",side_effect=sequence))
            validate=stack.enter_context(patch.object(
                actual,"evaluate_current_versioned_evidence",
                return_value=self.success))
            rest=stack.enter_context(patch.object(ci.time,"sleep"))
            output=ci.await_exact_ci_and_resume(
                self.root,self.root,self.pending,
                max_wait_seconds=max_wait,poll_interval_seconds=1)
            return output,gh.call_count,validate.call_count,rest.call_count

    def test_running_ci_auto_resumes_to_genuine_revalidation(self):
        output,queries,revalidated,slept=self.run_fake(
            [[self.inflight],[self.finished]])
        self.assertEqual(output["status"],ci._GREEN)
        self.assertEqual(output["ciRecoveryPolls"],2)
        self.assertTrue(output["ciRecoveredInSameInvocation"])
        self.assertEqual(queries,2)
        self.assertEqual(revalidated,1)
        self.assertEqual(slept,1)
        self.assertFalse(output["publicationAuthorized"])

    def test_terminal_failed_hosted_ci_stops_without_retry(self):
        failed={**self.finished,"conclusion":"failure"}
        out,queries,verified,slept=self.run_fake([[failed]])
        self.assertEqual(out["status"],"STOP_HOSTED_CI_COMPLETED_NOT_SUCCESS")
        self.assertEqual(queries,1)
        self.assertEqual(verified,0)
        self.assertEqual(slept,0)
        self.assertFalse(out["publicationAuthorized"])

    def test_wrong_head_green_ci_not_reused(self):
        wrong={**self.finished,"headSha":"f"*40}
        out,queries,verified,slept=self.run_fake(
            [[wrong],[wrong],[wrong]],max_wait=2)
        self.assertEqual(out["status"],"STOP_HOSTED_CI_BOUNDED_WAIT_EXHAUSTED")
        self.assertGreaterEqual(queries,2)
        self.assertEqual(verified,0)
        self.assertFalse(out["publicationAuthorized"])

    def test_missing_hosted_ci_always_finite(self):
        out,queries,verified,slept=self.run_fake(
            [[],[],[]],max_wait=2)
        self.assertEqual(out["status"],"STOP_HOSTED_CI_BOUNDED_WAIT_EXHAUSTED")
        self.assertLessEqual(queries,3)
        self.assertEqual(verified,0)
        self.assertFalse(out["publicationAuthorized"])

    def test_dirty_source_never_touches_hosted_ci(self):
        with patch.object(actual,"_git_info",return_value=(
             self.head,"feature/test")),patch.object(
             actual,"_git_clean",return_value=False),patch.object(
             actual,"_hosted_runs") as gh:
            with self.assertRaisesRegex(ValueError,
                    "GIT_DIRTY_OR_HEAD_MOVED"):
                ci.await_exact_ci_and_resume(
                    self.root,self.root,self.pending)
        gh.assert_not_called()

    def test_exact_head_changes_during_ci_wait_fails_closed(self):
        with patch.object(
                actual,"_git_info",
                side_effect=[(self.head,"feature/test"),("f"*40,"feature/test")]
        ),patch.object(actual,"_git_clean",return_value=True),patch.object(
                actual,"_hosted_runs") as gh:
            with self.assertRaisesRegex(ValueError,
                    "GIT_CHANGED_DURING_WAIT"):
                ci.await_exact_ci_and_resume(
                    self.root,self.root,self.pending)
        gh.assert_not_called()

    def test_bad_wait_window_rejected(self):
        with self.assertRaisesRegex(ValueError,"INVALID_FINITE_BOUNDS"):
            ci.await_exact_ci_and_resume(
                self.root,self.root,self.pending,max_wait_seconds=100000)

    def test_dirty_repo_proof_cannot_wait(self):
        invalid={**self.pending,
                 "status":"VERSIONED_SCIENCE_BROWSER_WAIT_COMMITTED_HEAD",
                 "codeWorkingTreeClean":False}
        with self.assertRaisesRegex(ValueError,"UNSAFE_PENDING_STATUS"):
            ci.await_exact_ci_and_resume(self.root,self.root,invalid)

    def test_green_with_false_ci_flag_refused(self):
        forged={**self.pending,"status":ci._GREEN,
                "exactHeadHostedCiSuccess":False}
        with self.assertRaisesRegex(ValueError,"FORGED_GREEN_STATUS"):
            ci.await_exact_ci_and_resume(self.root,self.root,forged)

    def test_normal_worker_immediately_continues_after_bounded_ci_green(self):
        self._run_worker(when_green=True)

    def test_normal_worker_stops_on_exhausted_ci_without_false_pass(self):
        self._run_worker(when_green=False)

    def test_invalid_green_poll_count_cannot_trigger_v6_or_v7(self):
        self._run_worker(when_green=True,bad_poll=True)

    def _run_worker(self,*,when_green:bool,bad_poll:bool=False):
        with ExitStack() as stack:
            stack.enter_context(patch.dict(os.environ,{
                "LOCALAPPDATA":str(self.root)}))
            stack.enter_context(patch.object(
                worker,"checked_private_root",return_value=self.root))
            stack.enter_context(patch.object(
                worker,"require_authorized_native_review_host"))
            stack.enter_context(patch.object(
                worker,"advance_source_free_until_boundary",
                return_value={"publicationAuthorized":False}))
            qa={
                "status":"ACTUAL_UNADMITTED_CHAPTER9_BROWSER_QA_PASS",
                "proposalSha256":self.proposal,"renderedChecks":698,
                "all108ActivitiesVisited":True,
                "allLocaleViewportPromptChecks":648,
            }
            stack.enter_context(patch.object(
                worker,"_complete_source_free_with_browser",
                return_value={
                    "proposalSha256":self.proposal,
                    "finalTwoScienceIntegrated":True,
                    "paidGeminiCalls":0,
                    "publicationAuthorized":False,
                    "realCandidateBrowserAcceptance":qa,
                }))
            original=stack.enter_context(patch.object(
                actual,"evaluate_current_versioned_evidence",
                return_value=self.pending))
            # BSA226: real hosted CI initially pending, then succeeded.
            # The coordinator's transient poll annotations MUST NOT enter
            # the separately signed, immutable source-readiness object.
            recovered=({**self.success,
                        "ciRecoveryPolls":("invalid" if bad_poll else 4),
                        "ciRecoveredInSameInvocation":True}
                       if when_green else {
                "status":"STOP_HOSTED_CI_BOUNDED_WAIT_EXHAUSTED",
                "publicationAuthorized":False,"paidGeminiCalls":0,
            })
            resumecall=stack.enter_context(patch.object(
                ci,"await_exact_ci_and_resume",return_value=recovered))
            advance=stack.enter_context(patch.object(
                five,"advance_five_stage_on_pinned_browser",
                return_value={
                    "status":"FIVE_STAGE_PRIVATE_TECHNICAL_PATH_COMPLETE_NO_PUBLICATION",
                    "publicationAuthorized":False,
                    "paidGeminiCalls":0,
                    "technicalV3ReleaseAttestationsVerified":True,
                    "privateNativeV3Attestations":6,
                }))
            def strict_genuine_v7(repo, private, exact, completed):
                if ("ciRecoveryPolls" in exact or
                        "ciRecoveredInSameInvocation" in exact):
                    raise ValueError("V3_PUBLIC_BUILD_READINESS_NOT_SAVED")
                return {
                    "status":"SIX_REAL_PUBLIC_BUNDLE_BUILDS_VERIFIED_PRIVATE_NO_DEPLOY",
                    "realOriginalPublicBuilderInvocations":6,
                    "publicationAuthorized":False,"publicDeployExecuted":False,
                }
            release=stack.enter_context(patch.object(
                bundle,"dispatch_private_public_bundle_build",
                side_effect=strict_genuine_v7))
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
            v14_mock=stack.enter_context(patch.object(
                v14_stage,"independent_public_pr_browser_acceptance",
                return_value={
                    "status":"PR_EXACT_PUBLIC_GIT_BRANCH_NINE_ROUTES_ACTUAL_CHROME_PASS",
                    "realChromeRoutesPassed":9,
                    "changedFileCount":21,
                    "publicPrDraft":True,
                    "publicMergeExecuted":False,
                    "publicDeployExecuted":False,
                }))
            v15_mock=stack.enter_context(patch.object(
                v15_stage,"run_global_readonly_roadmap",
                return_value={
                    "status":"POST_PR_GLOBAL_READONLY_TASKS_EXECUTED_NO_RELEASE",
                    "taskDispatchCount":3,
                    "nextTaskDispatchActuallyExecuted":True,
                    "quarantinedTaskIds":[],
                    "publicMergeExecuted":False,
                    "publicDeployExecuted":False,
                }))
            v16_mock=stack.enter_context(patch.object(
                v16_stage,"run_public_pr_security_accessibility",
                return_value={
                    "status":"SOURCE_PINNED_PR_SECURITY_A11Y_TECHNICAL_PREFLIGHT_NO_RELEASE",
                    "technicalEvidence":{"changedFileCount":21,"totalActivities":54},
                    "publicationAuthorized":False,
                    "publicMergeExecuted":False,
                    "publicDeployExecuted":False,
                }))
            from app_generator.runtime import (
                v3_science_c3_independent_dispatch as v17_stage,
            )
            v17_mock=stack.enter_context(patch.object(
                v17_stage,"run_post_v16_science_c3",
                return_value={
                    "status":"V17_REAL_SCIENCE_C3_GAP_AUDITS_EXECUTED_NO_RELEASE",
                    "taskDispatchActuallyExecuted":True,
                    "quarantinedTaskIds":[],
                    "historicalC3":"FAILED_LIMITED_CAMPAIGN",
                    "publicationAuthorized":False,
                }))
            from app_generator.runtime import (
                v3_selected_textbook_scientific_provenance as v18_stage,
            )
            v18_mock=stack.enter_context(patch.object(
                v18_stage,"run_post_v17_selected_textbook",
                return_value={
                    "status":"V18_SINGLE_TEXTBOOK_REAL_PDF_EVIDENCE_VERIFIED_SCIENCE_STILL_PARTIAL",
                    "realSingleTextbookPdfOpened":True,
                    "nextTaskDispatchActuallyExecuted":True,
                    "academicGapAuditReceiptSha256":"a"*64,
                    "additionalExternalPdfsRequired":False,
                    "newModelCalls":0,
                    "publicationAuthorized":False,
                }))
            from app_generator.runtime import (
                v3_original_reviewer_evidence_reuse as v19_stage,
            )
            v19_mock=stack.enter_context(patch.object(
                v19_stage,"run_post_v18_original_review_reuse",
                return_value={
                    "status":"V19_17_EXISTING_REVIEW_PAIRS_RECONCILED_ACADEMIC_PROOFS_STILL_OPEN",
                    "nextTaskDispatchActuallyExecuted":True,
                    "reusedIndependentTwoRolePairs":17,
                    "oldUncertainRoleReplayed":False,
                    "independentAcademicProofsStillOpen":90,
                    "independentScientificAcceptanceComplete":False,
                    "newModelCalls":0,
                    "publicationAuthorized":False,
                }))
            from app_generator.runtime import (
                v3_historical_academic_audit as v20_stage,
            )
            v20_mock=stack.enter_context(patch.object(
                v20_stage,"run_post_v19_historical_academic_audit",
                return_value={
                    "status":"V20_REAL_ORIGINAL_FIVE_GATE_ACADEMIC_AUDIT_EXECUTED_NO_RELEASE",
                    "historicFiveGateVerifierActuallyExecuted":True,
                    "verifiedOriginalSourceLocations":18,
                    "verifiedActivityGateEvaluations":90,
                    "formalAcademicPASS":0,
                    "historicalUncertainReviewerReplayed":False,
                    "newModelCalls":0,
                    "publicationAuthorized":False,
                }))
            from app_generator.runtime import (
                v3_revised_source_proof_rebinding as v21_stage,
            )
            v21_mock=stack.enter_context(patch.object(
                v21_stage,"run_post_v20_revised_source_rebind",
                return_value={
                    "status":"V21_REVISED_18_SOURCE_LOCATIONS_REVERIFIED_SEMANTIC_PROOFS_OPEN",
                    "candidateSourceLocationsActuallyReverified":18,
                    "changedActivitiesReverified":4,
                    "priorModelReviewerClaimsTransferred":0,
                    "candidateFormalAcademicPASS":0,
                    "candidateDeterministicFAIL":0,
                    "newGeminiCalls":0,
                    "publicationAuthorized":False,
                }))
            from app_generator.runtime import (
                v3_exact_revised_review_reconciliation as v22_stage,
            )
            v22_mock=stack.enter_context(patch.object(
                v22_stage,"run_post_v21_exact_revised_history_reconciliation",
                return_value={
                    "status":"V22_13_UNCHANGED_REVIEW_PAIRS_VERIFIED_4_NEW_SCOPED_NOT_SUBMITTED",
                    "unchangedReviewerPairsReusedAsAdvisoryEvidence":13,
                    "revisedReviewerPairsThatRequireFreshAssessment":4,
                    "oldUncertainRoleReplayed":False,
                    "fourPrivateReviewInputsStaged":True,
                    "remainingIndependentAcademicProofSlots":90,
                    "formalAcademicPASS":0,
                    "newGeminiCalls":0,
                    "publicationAuthorized":False,
                }))
            from app_generator.runtime import (
                v3_autonomous_academic_recovery as v24_stage,
            )
            v24_mock=stack.enter_context(patch.object(
                v24_stage,"run_post_v22_autonomous_academic_recovery",
                return_value={
                    "status":"V24_BOUNDED_HISTORY_FIRST_ACADEMIC_DISPATCH_EXECUTED_PROOFS_OPEN",
                    "historicalRemedyHandlersActuallyExecuted":6,
                    "genuineTextbookPageRechecks":18,
                    "completeAcademicProofGapsStillOpen":90,
                    "autoRecoveryRounds":2,
                    "academicFixedPointReached":True,
                    "externalGeminiCalls":0,
                    "academicPASS":0,
                    "publicationAuthorized":False,
                }))
            from app_generator.runtime import (
                v3_section91_formal_academic_dispatch as v25_stage,
            )
            v25_mock=stack.enter_context(patch.object(
                v25_stage,"run_post_v24_formal_science",
                return_value={
                    "status":"V25_ALL_18_REAL_SOURCE_BOUND_FORMAL_ANSWER_MODELS_VERIFIED_PARTIAL_ACADEMIC",
                    "independentlyReextractedTextbookPhysicsPremises":9,
                    "boundedFormalAnswerItemWitnesses":68,
                    "formalModelledActivities":18,
                    "academicProofGatesStillOpen":90,
                    "formalAcademicPASS":0,
                    "newGeminiCalls":0,
                    "externalPdfAcquisition":False,
                    "publicationAuthorized":False,
                }))
            from app_generator.runtime import (
                v3_source_semantic_triage as v26_stage,
            )
            v26_mock=stack.enter_context(patch.object(
                v26_stage,"run_post_v25_source_scientific_semantic_triage",
                return_value={
                    "status":"V26_SOURCE_BOUND_EXPLANATION_AND_TRILINGUAL_CUE_TRIAGE_COMPLETE_NO_RELEASE",
                    "activitiesChecked":18,
                    "scientificLocalizedFieldsChecked":222,
                    "unresolvedTriLocaleSemanticReviewItems":26,
                    "deterministicScienceDefects":0,
                    "renderedDiagramSemanticsVerified":False,
                    "academicProofGatesStillOpen":90,
                    "formalAcademicPASS":0,
                    "newGeminiCalls":0,
                    "publicationAuthorized":False,
                }))
            from app_generator.runtime import (
                v3_full_semantic_proof_dispatch as v26_queue_stage,
            )
            v26_queue_mock=stack.enter_context(patch.object(
                v26_queue_stage,"run_post_v25_full_semantic_queue",
                return_value={
                    "status":"V26_FULL_EXPLANATION_DISTRACTOR_DIAGRAM_TRILINGUAL_TASKS_QUEUED",
                    "activityCount":18,
                    "completeAcademicGateSlotsStillOpen":90,
                    "independentSemanticPASS":0,
                    "newProviderCalls":0,
                    "externalPdfAcquisition":False,
                    "publicationAuthorized":False,
                }))
            from app_generator.runtime import (
                v3_post_v26_bounded_symbolic_recovery as v27_stage,
            )
            v27_mock=stack.enter_context(patch.object(
                v27_stage,"run_post_v26_bounded_symbolic_recovery",
                return_value={
                    "status":"V27_FIVE_FALSE_POSITIVE_SYMBOLIC_FLAGS_BOUNDED_NO_ACADEMIC_PASS",
                    "boundedParserFalsePositivesResolved":5,
                    "remainingAmbiguousSymbolicFields":3,
                    "remainingTechnicalReviewFlags":21,
                    "completeIndependentAcademicProofSlotsStillOpen":90,
                    "fullAcademicPASS":0,
                    "newGeminiCalls":0,
                    "outsideSourcePdfsRequired":False,
                    "publicationAuthorized":False,
                }))
            from app_generator.runtime import (
                v3_post_v27_five_proof_producers as v28_stage,
            )
            v28_mock=stack.enter_context(patch.object(
                v28_stage,"run_post_v27_five_proof_producers",
                return_value={
                    "status":"V28_FIVE_BOUNDED_PROOF_PRODUCERS_REAL_EXECUTION_NOT_FULL_ACADEMIC_PASS",
                    "realSourcePageAnchors":18,
                    "boundedScientificAnswerWitnesses":68,
                    "falseMcqOptionsProvenAgainstFormalModels":27,
                    "trilingualSurfacesNumericLiteralChecked":222,
                    "actualDiagramsAbsent":18,
                    "independentMeaningMicroproofsPending":429,
                    "completeAcademicProofGatesStillOpen":90,
                    "formalAcademicPASS":0,
                    "newProviderCalls":0,
                    "publicationAuthorized":False,
                }))
            from app_generator.runtime import (
                v3_auto_development_handoff as v29_auto,
            )
            v29_mock=stack.enter_context(patch.object(
                v29_auto,"advance_eligible_verified_development_stages",
                return_value={
                    "status":"AUTONOMOUSLY_ADVANCED_ALL_REGISTERED_SAFE_STAGES_TO_CURRENT_BOUNDARY",
                    "stagesExecutedThisRun":1,
                    "academicPASS":0,
                    "publicationAuthorized":False,
                    "newModelCalls":0,
                    "privateSourceVisualPilot":{
                        "status":"V29_ACTUAL_SOURCE_BOUND_PRIVATE_VECTOR_RENDERER_RECHECKED_NO_PUBLICATION",
                        "actualSourceGroundedDraftCount":1,
                        "actualRenderedSvgArrowsVerified":6,
                        "fullAcademicPASS":0,
                        "publicationAuthorized":False,
                    },
                }))
            output=[]
            stack.enter_context(patch.object(
                worker,"_print",side_effect=output.append))
            rc=worker.main(["--source-free-advance"])
        succeeded=when_green and not bad_poll
        self.assertEqual(rc,0 if succeeded else 3)
        self.assertEqual(original.call_count,1)
        self.assertEqual(resumecall.call_count,1)
        self.assertEqual(advance.call_count,1 if succeeded else 0)
        self.assertEqual(release.call_count,1 if succeeded else 0)
        self.assertEqual(audit.call_count,1 if succeeded else 0)
        self.assertEqual(proposal_mock.call_count,1 if succeeded else 0)
        self.assertEqual(browser_mock.call_count,1 if succeeded else 0)
        self.assertEqual(v11_mock.call_count,1 if succeeded else 0)
        self.assertEqual(v12_mock.call_count,1 if succeeded else 0)
        self.assertEqual(v13_mock.call_count,1 if succeeded else 0)
        self.assertEqual(v14_mock.call_count,1 if succeeded else 0)
        self.assertEqual(v15_mock.call_count,1 if succeeded else 0)
        self.assertEqual(v16_mock.call_count,1 if succeeded else 0)
        self.assertEqual(v17_mock.call_count,1 if succeeded else 0)
        self.assertEqual(v18_mock.call_count,1 if succeeded else 0)
        self.assertEqual(v27_mock.call_count,1 if succeeded else 0)
        self.assertEqual(v28_mock.call_count,1 if succeeded else 0)
        self.assertEqual(v29_mock.call_count,1 if succeeded else 0)
        # The generic worker exception boundary deliberately does not
        # invent a paid-call count; the source-free path makes no API calls.
        if not bad_poll:
            self.assertEqual(output[-1]["paidGeminiCalls"],0)
        self.assertFalse(output[-1]["publicationAuthorized"])
        if succeeded:
            self.assertEqual(output[-1]["exactHostedCiRecovery"]["polls"],4)
            self.assertNotIn("ciRecoveryPolls",
                             output[-1]["versionedEvidenceReadiness"])
            self.assertNotIn("ciRecoveredInSameInvocation",
                             output[-1]["versionedEvidenceReadiness"])
        elif bad_poll:
            self.assertEqual(output[-1]["status"],"STOP_YOGA6_RECOVERY_WORKER")
            self.assertNotIn("realPublicBundleBuildHandoff",output[-1])
        else:
            self.assertEqual(output[-1]["automaticCiRecoveryBoundary"]["status"],
                "STOP_HOSTED_CI_BOUNDED_WAIT_EXHAUSTED")


if __name__=="__main__":
    unittest.main()

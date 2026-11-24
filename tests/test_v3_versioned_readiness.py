"""BSA220: negative controls for source-bound versioned technical evidence.

All fixtures are SYNTHETIC, with mocked source/Git/CI/browser. They never
provide academic approval for actual BOSLA content and make no provider call.
"""
from contextlib import ExitStack
from copy import deepcopy
from hashlib import sha256
import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from app_generator.runtime import v3_versioned_readiness as v
from scripts import run_v3_yoga6_recovery_worker as worker
from scripts import check_final_acceptance_closure as checker


class VersionedReadinessTests(unittest.TestCase):
    def setUp(self):
        tmp=TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        base=Path(tmp.name)
        self.repo=base/"repo"
        self.repo.mkdir()
        self.private=base/"owner-private"
        self.private.mkdir()
        self.head="a"*40
        self.digest="b"*64
        self.browser="c"*64
        self.runtime="d"*64
        self.ci=[{"headSha":self.head,"status":"completed",
                  "conclusion":"success","databaseId":123}]
        self.manifest={
            "schema":"BOSLA_V3_VERSIONED_COURSE_PROPOSAL_V1",
            "scope":"PROPOSAL_NOT_ADMITTED",
            "sections":[{"section":f"section-9-{n}","activities":18}
                        for n in range(1,7)],
            "counts":{
                "originalAssessed":75,
                "originalGenuineConsensusPasses":72,
                "scientificallyReviewedProposedContent":108,
                "proposedContentWithoutScience":0,
                "potentiallyReusablePasses":103,
                "finalTwoNewVersionConsensusPasses":2,
            },
            "unresolved":[
                "ORIGINAL_SECTION_9_1_AMBIGUOUS_DO_NOT_REPLAY",
                "HISTORICAL_SECTION96_PROVIDER_RESPONSE_UNRECOVERABLE_DO_NOT_REPLAY"],
            "finalTwoNewVersionGenuineScience":{
                "proofs":[{"section":"section-9-1"},{"section":"section-9-6"}]},
            "publicationAuthorized":False,"versionedScopeAdmitted":False,
        }
        self.proposal={
            "proposalSha256":self.digest,
            "finalTwoScienceIntegrated":True,
            "remainingContentUnreviewedAfterSupplemental":0,
        }
        self.receipt={
            "status":"ACTUAL_UNADMITTED_CHAPTER9_BROWSER_QA_PASS",
            "proposalSha256":self.digest,"revisionSha":self.head,
            "rendererRuntimeSha256":self.runtime,
            "activitiesInCandidate":108,"renderedChecks":698,
            "allLocaleViewportPromptChecks":648,
            "all108ActivitiesVisited":True,"publicationAuthorized":False,
            "versionedScopeAdmitted":False,
            "integritySha256":self.browser,
        }

    def fixture(self):
        # Explicitly synthetic evidence; no actual model/API calls.
        path=(self.private/"versioned-course-proposals"/self.digest)
        path.mkdir(parents=True,exist_ok=True)
        unsigned={**self.manifest}
        path.joinpath("scope-proposal.json").write_text(json.dumps({
            **unsigned,
            "integritySha256":sha256(v._encoded(unsigned)).hexdigest(),
        }),encoding="utf8")
        return path/"scope-proposal.json"

    def fake_hash(self):
        # Fixture digest must be the *actual* source-manifest digest.
        self.digest=sha256(v._encoded(self.manifest)).hexdigest()
        self.proposal["proposalSha256"]=self.digest
        self.receipt["proposalSha256"]=self.digest
        return self.fixture()

    def invoke(self,*,clean=True,rows=None,persist=False):
        with ExitStack() as stack:
            stack.enter_context(patch.object(
                v,"prepare_versioned_course_proposal",
                return_value=self.proposal))
            stack.enter_context(patch.object(
                v,"_read_saved",return_value=self.receipt))
            stack.enter_context(patch.object(v,"_runtime_sha",
                return_value=self.runtime))
            stack.enter_context(patch.object(v,"_git_info",
                return_value=(self.head,"feature/test")))
            stack.enter_context(patch.object(v,"_git_clean",return_value=clean))
            return v.evaluate_current_versioned_evidence(
                self.repo,self.private,
                hosted_runs=self.ci if rows is None else rows,
                persist=persist)

    def test_real_source_chain_shape_ci_browser_yes_but_never_release(self):
        self.fake_hash()
        report=self.invoke()
        self.assertEqual(report["status"],
                         "VERSIONED_SCIENCE_BROWSER_AND_CI_VERIFIED_UNADMITTED")
        self.assertEqual(report["proposedContentScientificCoverage"],108)
        self.assertTrue(report["exactHeadHostedCiSuccess"])
        self.assertFalse(report["publicationAuthorized"])
        self.assertFalse(report["automaticReleaseEligibilityGranted"])
        self.assertFalse(report["versionedScopeAdmitted"])
        self.assertEqual(report["nextEligibleMilestone"],
                         "INDEPENDENT_VERSION_ADMISSION_PRIVACY_AND_RELEASE_PROOFS")
        self.assertFalse((self.private/v._READINESS_FILE).exists())

    def test_missing_ci_does_not_become_release_or_true_exact_head(self):
        self.fake_hash()
        report=self.invoke(rows=[])
        self.assertFalse(report["exactHeadHostedCiSuccess"])
        self.assertEqual(report["nextEligibleMilestone"],
                         "VERIFY_EXACT_GIT_HEAD_HOSTED_CI")
        self.assertFalse(report["publicationAuthorized"])

    def test_uncommitted_development_never_reuses_old_ci_success(self):
        self.fake_hash()
        report=self.invoke(clean=False)
        self.assertFalse(report["codeWorkingTreeClean"])
        self.assertFalse(report["exactHeadHostedCiSuccess"])
        self.assertEqual(report["status"],
                         "VERSIONED_SCIENCE_BROWSER_WAIT_COMMITTED_HEAD")

    def test_old_wrong_source_browser_pass_fails_not_recounted(self):
        self.fake_hash()
        self.receipt["proposalSha256"]="f"*64
        with self.assertRaisesRegex(ValueError,"EXACT_HEAD_BROWSER_MISSING"):
            self.invoke()

    def test_old_wrong_git_head_browser_receipt_fails(self):
        self.fake_hash()
        self.receipt["revisionSha"]="f"*40
        with self.assertRaisesRegex(ValueError,"EXACT_HEAD_BROWSER_MISSING"):
            self.invoke()

    def test_fake_sci_count_108_without_true_source_coverage_fails(self):
        self.manifest["counts"]["potentiallyReusablePasses"]=104
        self.fake_hash()
        with self.assertRaisesRegex(ValueError,"HISTORY_PROOF_INCOMPLETE"):
            self.invoke()

    def test_missing_original_unknown_history_protection_fails(self):
        self.manifest["unresolved"]=[]
        self.fake_hash()
        with self.assertRaisesRegex(ValueError,"HISTORY_PROOF_INCOMPLETE"):
            self.invoke()

    def test_source_manifest_tamper_fails_before_ci(self):
        file=self.fake_hash()
        content=json.loads(file.read_text(encoding="utf8"))
        content["counts"]["scientificallyReviewedProposedContent"]=0
        file.write_text(json.dumps(content),encoding="utf8")
        with self.assertRaisesRegex(ValueError,"HISTORY_PROOF_INCOMPLETE"):
            self.invoke()

    def test_private_receipt_idempotent_and_tamper_is_rejected(self):
        self.fake_hash()
        a=self.invoke(persist=True)
        b=self.invoke(persist=True)
        self.assertEqual(a,b)
        file=self.private/v._READINESS_FILE
        tampered=json.loads(file.read_text(encoding="utf8"))
        tampered["publicationAuthorized"]=True
        file.write_text(json.dumps(tampered),encoding="utf8")
        with self.assertRaisesRegex(ValueError,"RECEIPT_TAMPERED"):
            self.invoke(persist=True)

    def test_wrong_ci_head_is_insufficient_even_when_green(self):
        self.fake_hash()
        report=self.invoke(rows=[{"headSha":"e"*40,
            "status":"completed","conclusion":"success","databaseId":123}])
        self.assertFalse(report["exactHeadHostedCiSuccess"])


class NormalReadinessDispatchTests(unittest.TestCase):
    def _run_worker(self,*,failing=False):
        with TemporaryDirectory() as folder,ExitStack() as stack:
            stack.enter_context(patch.dict(os.environ,{"LOCALAPPDATA":folder}))
            stack.enter_context(patch.object(
                worker,"checked_private_root",return_value=Path(folder)))
            stack.enter_context(patch.object(
                worker,"require_authorized_native_review_host"))
            stack.enter_context(patch.object(
                worker,"advance_source_free_until_boundary",return_value={}))
            qa={"status":"ACTUAL_UNADMITTED_CHAPTER9_BROWSER_QA_PASS",
                "proposalSha256":"a"*64,"renderedChecks":698,
                "all108ActivitiesVisited":True,
                "allLocaleViewportPromptChecks":648}
            sourcefree={"proposalSha256":"a"*64,
                "finalTwoScienceIntegrated":True,
                "paidGeminiCalls":0,"publicationAuthorized":False,
                "realCandidateBrowserAcceptance":qa}
            stack.enter_context(patch.object(
                worker,"_complete_source_free_with_browser",
                return_value=sourcefree))
            verified=stack.enter_context(patch.object(
                v,"evaluate_current_versioned_evidence",
                side_effect=(ValueError("INCOMPLETE_PROOF") if failing
                else None),
                return_value={
                    "status":"VERSIONED_SCIENCE_BROWSER_AND_CI_VERIFIED_UNADMITTED",
                    "exactHeadHostedCiSuccess":True,
                    "publicationAuthorized":False}))
            from app_generator.runtime import v3_five_stage_completion
            from app_generator.runtime import v3_public_bundle_handoff
            from app_generator.runtime import v3_public_deployment_scope as scope
            from app_generator.runtime import v3_pinned_public_release_proposal as proposal
            from app_generator.runtime import v3_public_release_browser_acceptance as browser_stage
            from app_generator.runtime import v3_private_public_patch_rehearsal as v11_stage
            from app_generator.runtime import v3_private_nonmerging_pr_readiness as v12_stage
            from app_generator.runtime import v3_public_nonmerging_draft_pr as v13_stage
            from app_generator.runtime import v3_public_pr_independent_browser_acceptance as v14_stage
            from app_generator.runtime import v3_global_post_pr_readonly_roadmap as v15_stage
            from app_generator.runtime import v3_public_pr_security_accessibility as v16_stage
            stack.enter_context(patch.object(
                v3_five_stage_completion,
                "advance_five_stage_on_pinned_browser",
                return_value={
                    "status":"FIVE_STAGE_PRIVATE_TECHNICAL_PATH_COMPLETE_NO_PUBLICATION",
                    "publicationAuthorized":False,
                    "paidGeminiCalls":0,
                    "technicalV3ReleaseAttestationsVerified":True,
                    "privateNativeV3Attestations":6,
                }))
            bundle=stack.enter_context(patch.object(
                v3_public_bundle_handoff,
                "dispatch_private_public_bundle_build",
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
            out=[]
            stack.enter_context(patch.object(worker,"_print",
                                             side_effect=out.append))
            status=worker.main(["--source-free-advance"])
            self.assertEqual(verified.call_count,1)
            self.assertEqual(bundle.call_count,0 if failing else 1)
            self.assertEqual(audit.call_count,0 if failing else 1)
            self.assertEqual(proposal_mock.call_count,0 if failing else 1)
            self.assertEqual(browser_mock.call_count,0 if failing else 1)
            self.assertEqual(v11_mock.call_count,0 if failing else 1)
            self.assertEqual(v12_mock.call_count,0 if failing else 1)
            self.assertEqual(v13_mock.call_count,0 if failing else 1)
            self.assertEqual(v14_mock.call_count,0 if failing else 1)
            self.assertEqual(v15_mock.call_count,0 if failing else 1)
            self.assertEqual(v16_mock.call_count,0 if failing else 1)
            self.assertEqual(v17_mock.call_count,0 if failing else 1)
            self.assertEqual(v18_mock.call_count,0 if failing else 1)
            self.assertEqual(v27_mock.call_count,0 if failing else 1)
            if failing:
                self.assertEqual(status,3)
            else:
                self.assertEqual(status,0)
                self.assertIn("versionedEvidenceReadiness",out[-1])
                self.assertFalse(out[-1]["versionedEvidenceReadiness"]
                                 ["publicationAuthorized"])

    def test_authenticated_browser_completion_auto_dispatches_next_stage(self):
        self._run_worker()

    def test_incomplete_new_readiness_stops_normal_worker(self):
        self._run_worker(failing=True)

    def test_no_flag_preserves_legacy_pending_policy(self):
        self.assertEqual(checker.active_disposition()[
            "currentTechnicalDisposition"],"PENDING_AUTOMATED_ASSESSMENT")


if __name__=="__main__":
    unittest.main()

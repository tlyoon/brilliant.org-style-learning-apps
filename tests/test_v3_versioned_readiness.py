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
            out=[]
            stack.enter_context(patch.object(worker,"_print",
                                             side_effect=out.append))
            status=worker.main(["--source-free-advance"])
            self.assertEqual(verified.call_count,1)
            self.assertEqual(bundle.call_count,0 if failing else 1)
            self.assertEqual(audit.call_count,0 if failing else 1)
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

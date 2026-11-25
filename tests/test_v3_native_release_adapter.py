"""BSA223: FAKE-ONLY V3 native release integration and adversarial controls.

Every model-shaped response and release receipt produced here is synthetic
and confined to TemporaryDirectory; no real model provider, student record,
PDF, PR merge, or live publication is ever reached.
"""
from copy import deepcopy
from hashlib import sha256
import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from app_generator.runtime import v3_native_release_adapter as a
from app_generator.runtime import v3_five_stage_completion as v
from app_generator.runtime.v3_versioned_acceptance_scope import _encoded
from app_generator.runtime.v3_standing_paid_science import _bytes
from app_generator.validation import autonomous_completion as native


class NativeV3ReleaseAdapterSyntheticTests(unittest.TestCase):
    def setUp(self):
        tmp=TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.work=Path(tmp.name)
        self.repo=self.work/"repo"
        self.repo.mkdir()
        self.private=self.work/"private"
        self.private.mkdir()
        self.head="a"*40
        self.packages=[]
        self.rows={}
        for section in range(1,7):
            items=[]
            for index in range(18):
                item={
                    "id":f"fake-section{section}-activity{index}",
                    "type":"mcq",
                    "prompt":{"en":f"Synthetic fake physics {section} {index}",
                              "ms":f"Fake Malay {section} {index}",
                              "zh":f"Fake Chinese {section} {index}"},
                    "answerKey":{"correct":"a","options":[
                        {"id":"a","label":{"en":"Fake a"}},
                        {"id":"b","label":{"en":"Fake b"}}]},
                }
                items.append(item)
                self.rows[(f"section-9-{section}",item["id"])]=self._model_row(item,section,index)
            raw=json.dumps({"activities":items},ensure_ascii=True,sort_keys=True).encode("utf8")
            self.packages.append((section,raw,items))
        self.manifest={
            "potentiallyReusableOriginalPasses":[],
            "isolatedReviewSliceSha256":"b"*64,
            "section96ScientificFailureReplacement":{
                "changedActivityIndices":[5,9],
                "independentNewVersionGeminiEvidence":[],
                "originalIndex9ScientificFailurePreserved":True,
                "originalIndex6ProviderUnknownPreserved":True,
            },
            "finalTwoNewVersionGenuineScience":{
                "originalSection91Index0UnknownPreserved":True,
                "originalSection96Index6UnknownPreserved":True,
                "reviewedNewSourceOnly":True,
                "proofs":[],
            },
            "publicationAuthorized":False,
        }
        changed={
            ("section-9-1",0):"e"*64,
            ("section-9-2",13):"b"*64,
            ("section-9-6",5):"c"*64,
            ("section-9-6",6):"f"*64,
            ("section-9-6",9):"d"*64,
        }
        for section,raw,items in self.packages:
            for index,item in enumerate(items):
                key=(f"section-9-{section}",index)
                row=self.rows[(key[0],item["id"])]
                if key not in changed:
                    self.manifest["potentiallyReusableOriginalPasses"].append({
                        "section":key[0],"activityId":item["id"],
                        "sourceReviewSha256":sha256(_bytes(row)).hexdigest(),
                        "status":"POTENTIALLY_REUSABLE_NOT_RELEASE_ACCEPTED",
                    })
                else:
                    digest=changed[key]
                    if key[0]=="section-9-6" and index in (5,9):
                        self.manifest[
                            "section96ScientificFailureReplacement"
                        ]["independentNewVersionGeminiEvidence"].append({
                            "index":index,"reviewSliceSha256":digest,
                            "genuineConsensusPass":True})
                    if key in (("section-9-1",0),("section-9-6",6)):
                        self.manifest["finalTwoNewVersionGenuineScience"]["proofs"].append({
                            "section":key[0],"index":index,
                            "reviewSliceSha256":digest,"genuineConsensusPass":True})
                    report=native._build_review_report(digest,[item],[row])
                    dir=self.private/("v3-generated-"+digest)/"batches"
                    dir.mkdir(parents=True)
                    (dir/("v3-assessment-"+digest+".json")).write_text(
                        json.dumps(report,sort_keys=True),encoding="utf8")
        # Store real-shaped historic fake reports so the native row search
        # checks the actual sourceReviewSha256 witness and Gemini prompt hash.
        for section,raw,items in self.packages:
            rows=[self.rows[(f"section-9-{section}",i["id"])] for i in items]
            digest=sha256(raw).hexdigest()
            dir=self.private/("v3-generated-"+digest)/"batches"
            dir.mkdir(parents=True)
            (dir/("v3-assessment-"+digest+".json")).write_text(
                json.dumps(native._build_review_report(digest,items,rows),
                           sort_keys=True),encoding="utf8")
        self.proposal=sha256(_encoded(self.manifest)).hexdigest()
        manifest={**self.manifest,"integritySha256":self.proposal}
        source=self.private/"versioned-course-proposals"/self.proposal
        source.mkdir(parents=True)
        (source/"scope-proposal.json").write_text(
            json.dumps(manifest,sort_keys=True),encoding="utf8")
        self.ready={
            "status":"VERSIONED_SCIENCE_BROWSER_AND_CI_VERIFIED_UNADMITTED",
            "gitHead":self.head,"proposalSha256":self.proposal,
            "exactHeadHostedCiSuccess":True,"codeWorkingTreeClean":True,
            "publicationAuthorized":False,
            "proposedContentScientificCoverage":108,
            "realChromeChecks":698,
            "integritySha256":"8"*64,"browserReceiptSha256":"9"*64,
        }
        self.location=self.private/v._BASE/self.head/self.proposal
        self.location.mkdir(parents=True)
        self.preview=a._candidate_dir(self.private,self.head,self.proposal)
        self.preview.mkdir(parents=True)
        app=self.preview/"app"
        app.mkdir()
        for index in range(14):
            (app/f"fake-module-{index}.js").write_text(f"synthetic {index}")
        for number,raw,_ in self.packages:
            file=self.preview/"content"/"chapter-9"/f"section-9-{number}"/"package.json"
            file.parent.mkdir(parents=True)
            file.write_bytes(raw)
        roster=self.preview/"local-pilot"
        roster.mkdir()
        (roster/"roster.json").write_text("{}")
        self._stage_records()

    @staticmethod
    def _model_row(item,section,index):
        dimensions={key:"PASS" for key in native.DIMENSIONS}
        verdict={
            "activityId":item["id"],"dimensions":dimensions,
            "rationales":{key:"Fake-only detailed test rationale: no scientific claim."
                          for key in native.DIMENSIONS},
            "counterexample":"Fake-only possible error used as a test counterexample.",
            "concern":"",
        }
        reviewers=[]
        for slot,perspective in enumerate((
            "physics-adversary","language-and-learner-adversary"
        )):
            reviewers.append({
                "reviewerId":f"synthetic-{perspective}",
                "sessionId":f"synthetic-session-{section}-{index}-{slot}",
                "providerId":next(iter(native.GEMINI_PROVIDERS)),
                "promptSha256":sha256(
                    native.make_prompt(item,perspective).encode("utf8")
                ).hexdigest(),
                "responseSha256":sha256(json.dumps(verdict).encode()).hexdigest(),
                "decision":deepcopy(verdict),
            })
        return {
            "activityId":item["id"],
            "status":"AI_CONSENSUS_PASS",
            "dimensions":dimensions,"reviewers":reviewers,
        }

    def _stage_records(self):
        common={
            "contract":"BOSLA_OWNER_FIVE_STAGE_AUTONOMOUS_COMPLETION_V1",
            "gitHead":self.head,"proposalSha256":self.proposal,
            "publicationAuthorized":False,"publicDeployExecuted":False,
        }
        cases=[
            {
                "status":"PASS_PRIVATE_ONLY",
                "versionedCourseInternalAdmission":True,
            },
            {
                "status":"PASS_PRIVATE_ONLY",
                "technicalPrivacyChecksPassed":True,
                "institutionalPrivacyCertificationClaimed":False,
            },
            {
                "status":"PASS_PRIVATE_ONLY",
                "originalScientificReadinessSha256":self.ready["integritySha256"],
                "realBrowserReceiptSha256":self.ready["browserReceiptSha256"],
                "exactHeadHostedCiSuccess":True,
                "existingPublicV3PerPackageAttestationMinted":False,
            },
            {
                "status":"PASS_PRIVATE_ONLY",
                "stagedFilesSha256":v._hash({"files":a._files_snapshot(self.preview)}),
                "stagedRealBrowserChecks":698,
                "faultInjectedRollbackRestoredAndVerified":True,
            },
            {
                "status":"READY_FOR_NEXT_AUTHORIZED_STAGE",
                "sourceFreeDownstreamWorkExecuted":True,
                "sourceFreePublicAdapter":{
                    "status":"PRIVATE_RELEASE_ADAPTER_EVIDENCE_VERIFIED",
                },
            },
        ]
        for name,fields in zip(v._STAGE_NAMES,cases):
            v._save_stage(self.location,name,{**common,**fields})

    def execute_adapter(self):
        with patch.object(a,"_read_previous",return_value=self.ready,
                          create=True):
            # Direct V3 adapter uses imported readiness verifier.
            from app_generator.runtime import v3_versioned_readiness
            with patch.object(v3_versioned_readiness,"_read_previous",
                              return_value=self.ready), patch.object(
                    v3_versioned_readiness,"_git_info",
                    return_value=(self.head,"synthetic")), patch.object(
                    v3_versioned_readiness,"_git_clean",return_value=True), patch.object(
                    v3_versioned_readiness,"_hosted_runs",
                    return_value=[{"headSha":self.head,"status":"completed",
                                   "conclusion":"success","databaseId":123}]):
                return a.run_exact_native_release_adapter(
                    self.repo,self.private,self.ready,self.packages)

    def test_native_gate_six_real_shaped_fake_receipts_only_in_private(self):
        output=self.execute_adapter()
        self.assertEqual(output["status"],a._RESULT)
        self.assertEqual(output["nativeV3TechnicalReleaseChecksPassed"],6)
        self.assertEqual(output["sourceGenuineTwoReviewerPositions"],108)
        self.assertFalse(output["publicationAuthorized"])
        self.assertFalse(output["publicDeployExecuted"])
        for n,raw,_ in self.packages:
            folder=self.location/"native-v3-exact-attestations"/f"section-9-{n}"
            outcome=a.enforce_academic_release_gate(
                self.repo,self.preview/"content"/"chapter-9"/f"section-9-{n}"/"package.json",folder)
            self.assertTrue(outcome["automatedTechnicalEligible"])
            self.assertEqual(outcome["artifactSha256"],sha256(raw).hexdigest())
        self.assertTrue((self.location/(a._V6+".json")).is_file())

    def test_source_provenance_fake_reports_both_canonical_encodings(self):
        rows=a._candidate_rows(self.private,self.manifest,self.packages)
        self.assertEqual(rows,self.rows)

    def test_restart_readonly_reuses_identical_attestations(self):
        prior=self.execute_adapter()
        paths=list(self.location.glob("native-v3-exact-attestations/*/autonomous-v3-release-receipt.json"))
        before={str(p):p.read_bytes() for p in paths}
        subsequent=self.execute_adapter()
        self.assertEqual(prior,subsequent)
        self.assertEqual(before,{str(p):p.read_bytes() for p in paths})

    def test_missing_one_model_aggregate_fails_before_receipt(self):
        (self.private/("v3-generated-"+"b"*64)/"batches"/
         ("v3-assessment-"+"b"*64+".json")).unlink()
        with self.assertRaisesRegex(ValueError,"UNSAFE_PRIVATE_PROOF|UNTRUSTED|MISSING_GENUINE"):
            self.execute_adapter()
        self.assertFalse((self.location/"native-v3-exact-attestations").exists())

    def test_revised_model_prompt_mismatch_rejected_before_write(self):
        revised=self.private/("v3-generated-"+"e"*64)/"batches"/(
            "v3-assessment-"+"e"*64+".json")
        doc=json.loads(revised.read_text())
        doc["reviews"][0]["reviewers"][0]["promptSha256"]="f"*64
        revised.write_text(json.dumps(doc))
        with self.assertRaisesRegex(ValueError,"STALE_OR_FORGED_REVIEW_PROMPT"):
            self.execute_adapter()
        self.assertFalse((self.location/"native-v3-exact-attestations").exists())

    def test_missing_ci_never_attested(self):
        self.ready["exactHeadHostedCiSuccess"]=False
        with self.assertRaisesRegex(ValueError,"EXACT_HOSTED_READINESS_MISSING"):
            self.execute_adapter()
        self.assertFalse((self.location/"native-v3-exact-attestations").exists())

    def test_direct_adapter_refuses_uncommitted_repository(self):
        from app_generator.runtime import v3_versioned_readiness as readiness
        with patch.object(readiness,"_git_clean",return_value=False):
            # The normal test helper forcibly patches source clean; directly
            # exercise the real adapter with other trusted inputs mocked.
            with patch.object(readiness,"_read_previous",
                              return_value=self.ready), patch.object(
                    readiness,"_git_info",
                    return_value=(self.head,"synthetic")),patch.object(
                    readiness,"_hosted_runs",
                    return_value=[{"headSha":self.head,"status":"completed",
                                   "conclusion":"success","databaseId":123}]):
                with self.assertRaisesRegex(ValueError,
                        "NOT_CURRENT_CLEAN_HOSTED_CI"):
                    a.run_exact_native_release_adapter(
                        self.repo,self.private,self.ready,self.packages)
        self.assertFalse((self.location/"native-v3-exact-attestations").exists())

    def test_direct_adapter_refuses_wrong_hosted_head(self):
        from app_generator.runtime import v3_versioned_readiness as readiness
        with patch.object(readiness,"_read_previous",
                          return_value=self.ready),patch.object(
                readiness,"_git_info",
                return_value=(self.head,"synthetic")),patch.object(
                readiness,"_git_clean",return_value=True),patch.object(
                readiness,"_hosted_runs",
                return_value=[{"headSha":"f"*40,"status":"completed",
                               "conclusion":"success","databaseId":123}]):
            with self.assertRaisesRegex(ValueError,
                    "NOT_CURRENT_CLEAN_HOSTED_CI"):
                a.run_exact_native_release_adapter(
                    self.repo,self.private,self.ready,self.packages)
        self.assertFalse((self.location/"native-v3-exact-attestations").exists())

    def test_wrong_browser_and_privacy_receipt_hash_blocks(self):
        stage=self.location/(v._STAGE_NAMES[2]+".json")
        doc=json.loads(stage.read_text())
        doc["originalScientificReadinessSha256"]="f"*64
        # File checksum is intentionally not recomputed.
        stage.write_text(json.dumps(doc))
        with self.assertRaisesRegex(ValueError,"CHECKPOINT_INTEGRITY_ERROR"):
            self.execute_adapter()

    def test_modified_staged_course_blocks_all_attestations(self):
        package=(self.preview/"content"/"chapter-9"/"section-9-3"/"package.json")
        package.write_bytes(b"{}")
        with self.assertRaisesRegex(ValueError,"PREVIEW_HASH_NOT_VERIFIED"):
            self.execute_adapter()

    def test_missing_private_rollback_proof_rejected(self):
        receipt=self.location/(v._STAGE_NAMES[3]+".json")
        data=json.loads(receipt.read_text())
        data["faultInjectedRollbackRestoredAndVerified"]=False
        data["integritySha256"]=v._hash({
            k:value for k,value in data.items() if k!="integritySha256"})
        receipt.write_text(json.dumps(data))
        with self.assertRaisesRegex(ValueError,"FIVE_STAGE_REAL_QA_MISSING"):
            self.execute_adapter()

    def test_corrupted_signed_v3_receipt_never_autorepaired(self):
        self.execute_adapter()
        path=self.location/"native-v3-exact-attestations"/"section-9-1"/(
            "autonomous-v3-release-receipt.json")
        doc=json.loads(path.read_text())
        doc["localAttestation"]="0"*64
        path.write_text(json.dumps(doc))
        with self.assertRaisesRegex(ValueError,"TAMPERED"):
            self.execute_adapter()

    def test_modified_synthetic_role_witness_rejected(self):
        source=self.private/("v3-generated-"+sha256(self.packages[2][1]).hexdigest())/(
            "batches")/("v3-assessment-"+sha256(self.packages[2][1]).hexdigest()+".json")
        doc=json.loads(source.read_text())
        doc["reviews"][3]["reviewers"][0]["decision"]["dimensions"]["physicsAnswer"]="FAIL"
        source.write_text(json.dumps(doc))
        with self.assertRaisesRegex(ValueError,"REVIEW"):
            self.execute_adapter()

    def test_stale_v6_checkpoint_must_fail(self):
        self.execute_adapter()
        p=self.location/(a._V6+".json")
        doc=json.loads(p.read_text())
        doc["publicDeployExecuted"]=True
        p.write_text(json.dumps(doc))
        with self.assertRaisesRegex(ValueError,"V6_CHECKPOINT_CHANGED"):
            self.execute_adapter()

    def test_native_gate_never_opens_model_or_publishes(self):
        with patch("app_generator.validation.autonomous_completion."
                   "seal_private_release_receipt",side_effect=RuntimeError(
                       "unavailable provider")):
            # The adapter binds the imported function; test that native V3
            # sealing is required rather than silently skipping it.
            with patch.object(a,"seal_private_release_receipt",
                              side_effect=RuntimeError("provider not needed")):
                with self.assertRaisesRegex(RuntimeError,"provider not needed"):
                    self.execute_adapter()


if __name__=="__main__":
    unittest.main()

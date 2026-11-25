"""BSA-207 synthetic private revised-roster fault injection, zero Gemini.

Actual Yoga6 source-bound two-real-Gemini PASS and real 108-Chrome checks
must be independently executed; these fixtures DO NOT produce approval.
"""
from hashlib import sha256
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from app_generator.runtime.v3_science_validated_roster import (
    validated_section96_two_science_revision,
)
from app_generator.runtime.v3_section96_authorized_revised_qa import (
    _EXPECTED_SLICES,
)


class BothCorrectedRosterTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        base=Path(self.temp.name)
        self.repo=base/"repo"
        self.repo.mkdir()
        self.course=self.repo/"content"/"chapter-9"
        (self.course/"section-9-6").mkdir(parents=True)
        self.private=base/"private"
        self.private.mkdir()
        self.original=[{"id":f"task-{i}","prompt":{"en":f"prompt-{i}"}}
                       for i in range(18)]
        for index,activity,_,_,_ in _EXPECTED_SLICES:
            self.original[index]["id"]=activity
        self.old_raw=self._save(self.course/"section-9-6"/"package.json",
                                self.original)
        self.old_sha=sha256(self.old_raw).hexdigest()
        self.previous=json.loads(json.dumps(self.original))
        self.previous[5]["prompt"]["en"]="SYNTHETIC revised mass"
        self.previous_sha=sha256(self._raw(self.previous)).hexdigest()
        self.new=json.loads(json.dumps(self.previous))
        self.new[9]["prompt"]["en"]="SYNTHETIC gravity-free physics"
        self.final_raw=self._raw(self.new)
        self.final_sha=sha256(self.final_raw).hexdigest()
        self.final_dir=self.private/"scientific-failure-rollforward"/"section-9-6"/self.final_sha
        self.final_dir.mkdir(parents=True)
        (self.final_dir/"package.json").write_bytes(self.final_raw)
        for index,activity,parent,sha,folder in _EXPECTED_SLICES:
            f=self.private/folder/"section-9-6"/sha
            f.mkdir(parents=True)
            (f/"package.json").write_text(json.dumps({
                "schema":"SYNTHETIC_SINGLE_ACTIVITY_REVIEW",
                "sourceActivityIndex":index,
                "activities":[self.new[index]],
            }),encoding="utf8")
        self.state={
            "status":"NEW_SECTION96_SCIENCE_REPAIR_STAGED_REVIEW_NOT_AUTHORIZED",
            "previousRevisedPackageSha256":self.previous_sha,
            "originalPackageSha256":self.old_sha,
            "candidatePackageSha256":self.final_sha,
            "isolatedReviewInputSha256":_EXPECTED_SLICES[1][3],
            "oldScientificFailurePreserved":True,
            "oldProviderUncertaintyPreserved":True,
            "publicationAuthorized":False,
            "newModelConsensusPassClaimed":False,
        }

    def _raw(self,items):
        return (json.dumps({"activities":items},sort_keys=True)+"\n").encode("utf8")

    def _save(self,path,items):
        raw=self._raw(items)
        path.write_bytes(raw)
        return raw

    def raw_identity(self,raw):
        doc=json.loads(raw)
        if doc.get("schema")=="SYNTHETIC_SINGLE_ACTIVITY_REVIEW":
            index=doc["sourceActivityIndex"]
            return _EXPECTED_SLICES[0 if index==5 else 1][3],doc["activities"]
        return sha256(raw).hexdigest(),doc["activities"]

    def call(self,state=None,progress=None,role_proof=None):
        def prior(role_raw,saved):
            return progress or {"activitiesAssessed":1,
                                "modelConsensusPassActivities":1,
                                "activitiesFullyModelReviewed":1}
        synthetic_slices=tuple(
            (i,activity,self.previous_sha if i==5 else self.final_sha,
             sha,folder)
            for i,activity,parent,sha,folder in _EXPECTED_SLICES)
        with patch(
            "app_generator.runtime.v3_science_validated_roster."
            "stage_known_section96_scientific_failure",
            return_value=self.state if state is None else state
        ),patch(
            "app_generator.runtime.v3_science_validated_roster."
            "_EXPECTED_SLICES",synthetic_slices
        ),patch(
            "app_generator.runtime.v3_science_validated_roster."
            "package_identity",side_effect=self.raw_identity
        ),patch(
            "app_generator.runtime.v3_science_validated_roster."
            "assessment_progress",side_effect=prior
        ),patch(
            "app_generator.runtime.v3_science_validated_roster."
            "verify_persisted_two_role_science",
            return_value=role_proof or {"pass":True,"repair":False,"uncertain":False}
        ):
            return validated_section96_two_science_revision(
                self.course,self.repo,self.private,
                previous_sha=self.previous_sha,previous_items=self.previous)

    def fake_both_saved(self):
        for _,_,_,sha,_ in _EXPECTED_SLICES:
            f=self.private/("v3-generated-"+sha)/"batches"
            f.mkdir(parents=True)
            (f/("v3-assessment-"+sha+".json")).write_text(
                '{"schema":"SYNTHETIC_ASSESSMENT_ONLY"}',encoding="utf8")

    def test_both_fake_model_approvals_only_in_fixture_return_exact_new_parent(self):
        self.fake_both_saved()
        result=self.call()
        self.assertEqual(result["candidatePackageSha256"],self.final_sha)
        self.assertEqual([x["index"] for x in result["proofs"]],[5,9])
        self.assertFalse(result["publicationAuthorized"])
        self.assertFalse(result["newContentVersionAdmitted"])
        self.assertEqual(
            (self.course/"section-9-6"/"package.json").read_bytes(),
            self.old_raw)

    def test_missing_either_new_independent_review_is_not_a_scientific_pass(self):
        self.assertIsNone(self.call())
        first=_EXPECTED_SLICES[0][3]
        folder=self.private/("v3-generated-"+first)/"batches"
        folder.mkdir(parents=True)
        (folder/("v3-assessment-"+first+".json")).write_text("{}")
        self.assertIsNone(self.call())

    def test_reviewer_scientific_failure_never_inherits_original_pass(self):
        self.fake_both_saved()
        self.assertIsNone(self.call(progress={
            "activitiesAssessed":1,"modelConsensusPassActivities":0,
            "activitiesFullyModelReviewed":1,"modelRepairRequiredActivities":1}))
        with self.assertRaisesRegex(ValueError,"TWO_ROLE_PASS_NOT_PROVEN"):
            self.call(role_proof={"pass":False,"repair":True,"uncertain":False})

    def test_extra_changed_index_or_changed_old_source_fails_closed(self):
        self.fake_both_saved()
        previous=self.final_raw
        try:
            changed=json.loads(previous)
            changed["activities"][11]["prompt"]["en"]="TAMPERED EXTRA"
            (self.final_dir/"package.json").write_text(json.dumps(
                changed,sort_keys=True)+"\n")
            with self.assertRaisesRegex(ValueError,"BOTH_CHANGED_INDICES"):
                self.call()
        finally:
            (self.final_dir/"package.json").write_bytes(previous)

    def test_forged_original_fail_status_cannot_promote_new_version(self):
        self.fake_both_saved()
        state={**self.state,"oldScientificFailurePreserved":False}
        with self.assertRaisesRegex(ValueError,"SOURCE_PROVENANCE_CHANGED"):
            self.call(state=state)

    def test_normal_worker_only_uses_main_browser_for_integrated_exact_revision(self):
        from scripts.run_v3_yoga6_recovery_worker import (
            _complete_source_free_with_browser,
        )
        with patch(
            "scripts.run_v3_yoga6_recovery_worker."
            "advance_real_candidate_browser_qa",
            return_value={"status":"ACTUAL_UNADMITTED_CHAPTER9_BROWSER_QA_PASS",
                          "renderedChecks":698,"publicationAuthorized":False}
        ),patch(
            "app_generator.runtime.v3_science_candidate_browser."
            "advance_science_revision_browser_qa",
            side_effect=AssertionError("old parent browser must not be re-used"),
        ):
            result=_complete_source_free_with_browser(self.private,{
                "section96ScienceIntegrated":True,
                "scientificFailureRepair":{
                    "status":"NEW_SECTION96_SCIENCE_REPAIR_STAGED_REVIEW_NOT_AUTHORIZED"},
            })
        self.assertEqual(result["scienceRevisionBrowserAcceptance"]["status"],
            "SCIENCE_INDEX9_INCLUDED_IN_FULL_CANDIDATE_BROWSER")
        self.assertEqual(result["realCandidateBrowserAcceptance"]["renderedChecks"],698)
        self.assertFalse(result["scienceRevisionBrowserAcceptance"]["publicationAuthorized"])


if __name__=="__main__":
    unittest.main()

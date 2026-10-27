"""Normal stage opt-in is safe when absent, repeated, stale or malformed."""
from __future__ import annotations
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from types import SimpleNamespace

from app_generator.runtime.run_context import RunContext
from app_generator.runtime.bounded_recovery_stage import maybe_run_bounded_recovery, REQUEST_NAME
from app_generator.validation.bounded_physics_transfer import digest
from app_generator.validation.impulse_qualifier_repair import ACTIVITY_ID
from app_generator.validation.impulse_v3 import V3_LABEL
from app_generator.validation.impulse_v3_audit import ITEM_ID

class StageRecoveryTests(unittest.TestCase):
    def setUp(self):
        temp=tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root=Path(temp.name)
        self.repo=self.root/"repo"; self.repo.mkdir()
        self.run=RunContext.create(self.root/"runs")
        self.pdf=self.root/"source.pdf"
        self.pdf.write_bytes(b"%PDF-1.4 synthetic")
        self.sha=sha256(self.pdf.read_bytes()).hexdigest()
        self.base=self.root/"base.json"
        self.candidate=self.root/"candidate.json"
        self.dossier=self.root/"dossier.json"
        activity={"id":ACTIVITY_ID,"type":"interactive","interactionMode":"selection",
                  "interaction":{"items":[{"id":ITEM_ID,"label":deepcopy(V3_LABEL)},
                    {"id":"other","label":{"en":"wrong","ms":"wrong","zh":"wrong"}}],
                    "correctSelections":[ITEM_ID]}}
        self.baseline={"activities":[activity]}
        self.base.write_text(json.dumps(self.baseline,ensure_ascii=False),encoding="utf-8")
        self.baseline_sha=sha256(self.base.read_bytes()).hexdigest()
        changed=deepcopy(self.baseline)
        changed["activities"][0]["interaction"]["items"][0]["label"]["en"]+=(
          " Nevertheless, each external force must be small.")
        self.candidate.write_text(json.dumps(changed,ensure_ascii=False),encoding="utf-8")
        self.dossier.write_text(json.dumps({
          "sourceSha256":self.sha,"packageSha256":self.baseline_sha,
          "activityId":ACTIVITY_ID,"activitySha256":digest(activity),
          "boundedPhysicsReceiptMatched":True,"sourceLocationVerifiedInMatrix":True,
          "publicationAuthorized":False,"fullAcademicPass":False,
          "academicQA":"REVIEW_REQUIRED",
        }),encoding="utf-8")
        self.manifest={
          "version":1,"baselineFile":str(self.base),"dossierFile":str(self.dossier),
          "baselineSha256":self.baseline_sha,"sourceSha256":self.sha,
        }

    def save_request(self):
        (self.run.validation/REQUEST_NAME).write_text(json.dumps(self.manifest),encoding="utf-8")

    def dispatch(self):
        return maybe_run_bounded_recovery(run=self.run,repository=self.repo,
                                         package_file=self.candidate,source_pdf=self.pdf)

    def test_no_request_preserves_ordinary_pipeline(self):
        self.assertIsNone(self.dispatch())
        self.assertIsNone(self.run.load_stage("bounded-academic-recovery"))

    def test_opt_in_restores_without_installing_and_reuses_checkpoint(self):
        self.save_request()
        result=self.dispatch()
        self.assertEqual("COMPLETE",result["state"])
        self.assertEqual(self.baseline_sha,result["restoredPackageSha256"])
        self.assertEqual(self.baseline_sha,sha256(
            (self.run.validation/"bounded-academic-restored"/"restored-package.json").read_bytes()).hexdigest())
        self.assertNotEqual(self.candidate.read_bytes(),self.base.read_bytes())
        self.assertFalse(result["publicationAuthorized"])
        repeat=self.dispatch()
        self.assertEqual("COMPLETE",repeat["state"])
        self.assertEqual("AUTO_INDEPENDENT_SEMANTIC_VISUAL_REVIEW",repeat["nextAction"])

    def test_blocked_unknown_change_does_not_retry_provider(self):
        self.candidate.write_bytes(b'{"activities":[]}')
        self.save_request()
        result=self.dispatch()
        self.assertEqual("BLOCKED",result["state"])
        self.assertEqual("AUTO_SOURCE_CHECK",result["nextAction"])
        self.assertFalse((self.run.validation/"bounded-academic-restored").exists())
        self.assertEqual("RECONCILE_PREVIOUS_ATTEMPT",self.dispatch()["nextAction"])

    def test_stale_request_checkpoint_mismatch_is_rejected(self):
        self.save_request()
        self.dispatch()
        self.manifest["baselineSha256"]="f"*64
        self.save_request()
        with self.assertRaisesRegex(ValueError,"checkpoint"):
            self.dispatch()

    def test_normal_academic_stage_consumes_only_explicit_private_request(self):
        from app_generator.runtime.academic_generation_stage import run_academic_stage
        config=SimpleNamespace(repo_root=self.repo,
            chrome_profile_dir=self.root/"unowned-browser",
            browser_mode="controlled",llm_backend="gemini_browser")
        self.save_request()
        output=run_academic_stage(config,self.run,self.candidate,self.pdf)
        self.assertEqual("COMPLETE",output["boundedRecovery"]["state"])
        self.assertEqual("AUTO_INDEPENDENT_SEMANTIC_VISUAL_REVIEW",
                         output["queue"][-1]["nextAction"])
        self.assertFalse(output["publicationAuthorized"])
        again=run_academic_stage(config,self.run,self.candidate,self.pdf)
        self.assertEqual("COMPLETE",again["boundedRecovery"]["state"])

    def test_private_references_cannot_live_in_public_checkout(self):
        self.manifest["dossierFile"]=str(self.repo/"report.json")
        (self.repo/"report.json").write_text("{}")
        self.save_request()
        with self.assertRaisesRegex(ValueError,"Git"):
            self.dispatch()


if __name__=="__main__":
    unittest.main()
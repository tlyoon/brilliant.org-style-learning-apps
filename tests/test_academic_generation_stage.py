import hashlib
import json
import tempfile
import unittest
from dataclasses import dataclass
from pathlib import Path
from unittest.mock import patch

from app_generator.runtime.run_context import RunContext
from app_generator.runtime.academic_generation_stage import run_academic_stage


@dataclass
class Config:
    repo_root:Path
    chrome_profile_dir:Path
    browser_mode:str="controlled"
    llm_backend:str="gemini_browser"
    gem_url:str="https://gemini.google.com/gem/custom"
    gem_edit_url:str="https://gemini.google.com/gem/custom/edit"


class StageTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        self.config=Config(self.root/"source-repo",self.root/"chrome-profile")
        self.config.repo_root.mkdir()
        self.context=RunContext.create(self.root/"run")
        self.pdf=self.root/"source.pdf"
        self.pdf.write_bytes(b"%PDF-1.4 synthetic")
        self.source_sha=hashlib.sha256(self.pdf.read_bytes()).hexdigest()
        self.package=self.root/"package.json"
        self.package.write_bytes(json.dumps({"activities":[{"id":"one","type":"mcq"}]}).encode("utf-8"))
        self.pkg_sha=hashlib.sha256(self.package.read_bytes()).hexdigest()
        self.anchor={"activityId":"one","pageIndex":1,"quotedText":"A lengthier controlled physical source quotation that should be checked."}
        self.trusted={"activityId":"one","sourceSha256":self.source_sha,
           "verifiedPages":[1],"sourceEvidence":"A private source citation that is long enough for independent review and confirmed against PDF.",
           "sourceAnchors":[self.anchor],"passageSha256":["a"*64]}
        self.packet_path=self.context.validation/"academic-review-source-packets.json"

    def save_packet(self,package_sha=None):
        self.packet_path.write_text(json.dumps({
            "packageSha256":package_sha or self.pkg_sha,
            "sourceSha256":self.source_sha,
            "packets":{"one":self.trusted},
        }),encoding="utf-8")

    def test_empty_packets_create_machine_source_queue_without_human(self):
        result=run_academic_stage(self.config,self.context,self.package,self.pdf)
        self.assertEqual(0,result["sourceReady"])
        self.assertEqual("AUTO_SOURCE_CHECK",result["queue"][0]["nextAction"])
        self.assertFalse(result["humanAcademicApprovalRequired"])
        self.assertFalse(result["publicationAuthorized"])
        self.assertTrue((self.context.validation/"autonomous-academic-queue.json").is_file())

    def test_stale_package_source_receipt_is_rejected(self):
        self.save_packet("f"*64)
        r=run_academic_stage(self.config,self.context,self.package,self.pdf)
        self.assertEqual("AUTO_SOURCE_CHECK",r["queue"][0]["nextAction"])

    def test_validated_packet_but_missing_independent_browser_profiles_queues_retry(self):
        self.save_packet()
        with patch("app_generator.runtime.academic_generation_stage.extract_pages",
                   return_value=("Private synthetic scientific passage.",)), patch(
                   "app_generator.runtime.academic_generation_stage.verified_source_packet",
                   return_value=self.trusted):
            result=run_academic_stage(self.config,self.context,self.package,self.pdf)
        self.assertEqual(1,result["sourceReady"])
        self.assertEqual("AUTO_RETRY",result["queue"][0]["nextAction"])
        self.assertIn("profiles",result["queue"][0]["reason"])

    def test_forged_source_packet_is_not_passed_to_model(self):
        self.save_packet()
        with patch("app_generator.runtime.academic_generation_stage.extract_pages",
                   return_value=("Private synthetic scientific passage.",)), patch(
                   "app_generator.runtime.academic_generation_stage.verified_source_packet",
                   side_effect=ValueError("wrong original textbook passage")):
            result=run_academic_stage(self.config,self.context,self.package,self.pdf)
        self.assertEqual("AUTO_SOURCE_CHECK",result["queue"][0]["nextAction"])

    def test_wrong_local_pdf_never_triggers_ai(self):
        self.save_packet()
        self.pdf.write_bytes(b"%PDF-1.4 modified")
        r=run_academic_stage(self.config,self.context,self.package,self.pdf)
        self.assertEqual("AUTO_SOURCE_CHECK",r["queue"][0]["nextAction"])

    def test_busy_chrome_profiles_defer_model_without_browser_factory(self):
        self.save_packet()
        for role in ("physics","semantics"):
            (self.config.chrome_profile_dir/"academic-reviewers"/role/"gemini-browser").mkdir(parents=True)
        def forbidden_factory(*args,**kwargs):
            raise AssertionError("occupied profile must never open a browser")
        with patch("app_generator.runtime.academic_generation_stage.extract_pages",
                   return_value=("Private synthetic scientific passage.",)), patch(
                   "app_generator.runtime.academic_generation_stage.verified_source_packet",
                   return_value=self.trusted), patch(
                   "app_generator.runtime.academic_generation_stage.reviewer_ownership_preflight",
                   return_value={"canAttemptIndependentBrowserReview":False}):
            output=run_academic_stage(self.config,self.context,self.package,self.pdf,
                                      reviewer_factory_type=forbidden_factory)
        self.assertEqual(1,output["sourceReady"])
        self.assertEqual("AUTO_RETRY",output["queue"][0]["nextAction"])
        self.assertIn("occupied",output["queue"][0]["reason"])
        self.assertFalse(output["publicationAuthorized"])

    def test_protected_repo_cannot_receive_qa_receipts(self):
        self.config.repo_root=self.root
        with self.assertRaisesRegex(ValueError,"public repository"):
            run_academic_stage(self.config,self.context,self.package,self.pdf)

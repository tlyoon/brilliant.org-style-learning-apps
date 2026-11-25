import hashlib
import json
import tempfile
import unittest
from dataclasses import dataclass
from pathlib import Path
from app_generator.runtime.private_gemini_pilot import (
    readiness,run_private_pilot,ACTIVITY_ID,NEUTRAL_GEM_URL,
)
from app_generator.validation.autonomous_ai_review import ReviewerSession

@dataclass
class Config:
    browser_mode:str
    llm_backend:str
    chrome_profile_dir:Path
    repo_root:Path
    gem_url:str="https://gemini.google.com/gem/custom"
    gem_edit_url:str="https://gemini.google.com/gem/custom/edit"

class Model:
    def ask(self,prompt,*,stage=None):
        return "BEGIN_JSON\n"+json.dumps({
            "gate":stage.removeprefix("academic-"),
            "verdict":"UNCERTAIN",
            "rationale":"The test intentionally leaves this claim unresolved.",
            "sourcePage":None,
            "issue":"no independent domain proof",
        })+"\nEND_JSON"

class MockReviewers:
    received=[]
    def __init__(self,config,pdf):
        self.received.append(config)
    def __enter__(self):return self
    def __exit__(self,*args):pass
    def open_pair(self,activity_id):
        return (
            ReviewerSession("physics","pilot-1",Model()),
            ReviewerSession("language","pilot-2",Model()),
        )

class PilotTests(unittest.TestCase):
    def setUp(self):
        self.t=tempfile.TemporaryDirectory()
        self.addCleanup(self.t.cleanup)
        root=Path(self.t.name)
        self.root=root
        self.config=Config("controlled","gemini_browser",root/"profile",root/"repo")
        self.pdf=root/"source.pdf";self.pdf.write_bytes(b"%PDF-1.4 fixture")
        self.sha=hashlib.sha256(self.pdf.read_bytes()).hexdigest()
        self.pkg=root/"package.json"
        self.pkg.write_text(json.dumps({"activities":[{"id":ACTIVITY_ID,"prompt":{"en":"Collision"}}]}),encoding="utf-8")
        self.source={
            "activityId":ACTIVITY_ID,"sourceSha256":self.sha,
            "verifiedPages":[2],"sourceEvidence":"Private textbook source passage containing sufficient words and a force theorem.",
        }

    def test_unprovisioned_profiles_block_without_model_send(self):
        report=run_private_pilot(self.config,self.pkg,self.pdf,self.source,
                                 run_directory=self.root/"no-output",
                                 reviewer_factory_type=MockReviewers)
        self.assertEqual("BLOCKED_NO_INDEPENDENT_BROWSER_PROFILE",report["status"])
        self.assertFalse((self.root/"no-output").exists())
        self.assertFalse(report["publicationAuthorized"])

    def test_two_provisioned_profiles_use_neutral_not_author_gem(self):
        for role in ("physics","semantics"):
            (self.config.chrome_profile_dir/"academic-reviewers"/role/"gemini-browser").mkdir(parents=True)
        report=run_private_pilot(self.config,self.pkg,self.pdf,self.source,
                                 run_directory=self.root/"trial",
                                 reviewer_factory_type=MockReviewers)
        self.assertEqual("AI_REVIEW_ATTEMPTED",report["status"])
        self.assertEqual(NEUTRAL_GEM_URL,MockReviewers.received[-1].gem_url)
        self.assertEqual(NEUTRAL_GEM_URL,MockReviewers.received[-1].gem_edit_url)
        # A simulated UNCERTAIN review was attempted but never completed.
        self.assertEqual(0,report["aiReviewedActivities"])
        self.assertEqual(1,report["nextActions"]["AUTO_SOURCE_CHECK"])
        self.assertEqual("REVIEW_REQUIRED",report["academicQA"])
        self.assertFalse(report["publicationAuthorized"])

    def test_wrong_source_and_backend_rejected(self):
        self.source["sourceSha256"]="a"*64
        with self.assertRaisesRegex(ValueError,"hash"):
            readiness(self.config,self.pkg,self.pdf,self.source)
        self.source["sourceSha256"]=self.sha
        self.config.llm_backend="gemini_api"
        with self.assertRaisesRegex(ValueError,"non-API"):
            readiness(self.config,self.pkg,self.pdf,self.source)

    def test_refuse_public_pilot_directory(self):
        for role in ("physics","semantics"):
            (self.config.chrome_profile_dir/"academic-reviewers"/role/"gemini-browser").mkdir(parents=True)
        self.config.repo_root.mkdir()
        with self.assertRaisesRegex(ValueError,"outside repository"):
            run_private_pilot(self.config,self.pkg,self.pdf,self.source,
                              run_directory=self.config.repo_root/"unsafe",
                              reviewer_factory_type=MockReviewers)

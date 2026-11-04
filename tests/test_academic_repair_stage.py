"""Independent objection-to-repair dispatch, no browser/account required."""
import tempfile
import unittest
from dataclasses import dataclass
from pathlib import Path

from app_generator.runtime.run_context import RunContext
from app_generator.runtime.academic_repair_stage import dispatch_repair_queue
from tests.test_autonomous_repair import ACT,SOURCE,response,label_patches

@dataclass
class Config:
    chrome_profile_dir:Path
    gem_url:str="https://gemini.google.com/gem/custom"
    gem_edit_url:str="https://gemini.google.com/gem/custom/edit"

class FakeModel:
    def __init__(self):
        self.conversation=self
        self.calls=0
    def ask(self,prompt):
        self.calls+=1
        return response(label_patches())

class FakeBrowser:
    models=[]
    def __init__(self,role,config,pdf):
        assert role=="repair"
        assert config.gem_url=="https://gemini.google.com/app"
        self.client=FakeModel()
        self.models.append(self.client)
        self.closed=False
    def open(self):return self.client
    def close(self):self.closed=True

class DispatchTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        self.ctx=RunContext.create(self.root/"run")
        self.config=Config(self.root/"chrome")
        self.pdf=self.root/"source.pdf"
        self.pdf.write_bytes(b"%PDF-1.4 private source fixture")
        self.report={
            "packageSha256":"a"*64,"sourceSha256":SOURCE["sourceSha256"],
            "receipts":[{
                "activityId":ACT["id"],"originalActivity":ACT,
                "nextAction":"AUTO_REPAIR",
                "gates":{"physics_consistency":{
                    "reports":[{"verdict":"CONTRADICTED",
                        "issue":"External forces can cancel in the whole isolated system."}]
                }},
            }],
        }
    def dispatch(self):
        return dispatch_repair_queue(
            self.config,self.ctx,self.report,{ACT["id"]:SOURCE},self.pdf,
            repair_browser_factory=FakeBrowser,
        )
    def test_missing_profile_does_not_request_human_or_model(self):
        FakeBrowser.models=[]
        a=self.dispatch()
        self.assertEqual("AUTO_RETRY",a[0]["nextAction"])
        self.assertFalse(FakeBrowser.models)
    def test_tight_private_repair_and_fresh_review_required(self):
        (self.config.chrome_profile_dir/"academic-reviewers"/"repair"/"gemini-browser").mkdir(parents=True)
        FakeBrowser.models=[]
        out=self.dispatch()
        self.assertEqual("RECHECK_WITH_FRESH_REVIEWERS",out[0]["nextAction"])
        self.assertTrue(out[0]["independentReverificationRequired"])
        self.assertEqual(1,FakeBrowser.models[0].calls)
        self.assertEqual(64,len(out[0]["candidateSha256"]))
        self.assertTrue(any((self.ctx.validation/"academic-repair-candidates").iterdir()))
        again=self.dispatch()
        self.assertEqual("RECONCILE_PREVIOUS_ATTEMPT",again[0]["nextAction"])
        self.assertEqual(0,FakeBrowser.models[1].calls)
    def test_source_and_evidence_protection(self):
        with self.assertRaisesRegex(ValueError,"wrong original"):
            dispatch_repair_queue(
                self.config,self.ctx,self.report,
                {ACT["id"]:{**SOURCE,"sourceSha256":"f"*64}},self.pdf,
                repair_browser_factory=FakeBrowser)
        self.report["receipts"][0]["gates"]["physics_consistency"]["reports"][0]["issue"]="x"
        self.assertEqual("AUTO_SOURCE_CHECK",self.dispatch()[0]["nextAction"])

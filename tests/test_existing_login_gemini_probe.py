"""Safe no-source Gemini probe and source-bound login readiness tests."""
from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from app_generator.runtime.private_gemini_pilot import readiness, ACTIVITY_ID
from scripts.probe_existing_gemini import probe, NEUTRAL


@dataclass(frozen=True)
class Config:
    repo_root:Path
    chrome_profile_dir:Path
    login_name:str="teacher@example.com"
    browser_mode:str="controlled"
    llm_backend:str="gemini_browser"
    gem_url:str=NEUTRAL
    gem_edit_url:str=NEUTRAL
    response_timeout_seconds:int=90
    ui_timeout_seconds:int=24


class Switch:
    def __init__(self,driver):self.driver=driver
    def new_window(self,kind):
        assert kind=="tab"
        h=f"role-{len(self.driver.handles)}"
        self.driver.handles.append(h)
        self.driver.active=h
        self.driver.urls[h]="about:blank"
    def window(self,handle):self.driver.active=handle


class Driver:
    def __init__(self):
        self.handles=["original"]
        self.active="original"
        self.urls={"original":NEUTRAL}
        self.switch_to=Switch(self)
        self.closed=[]
    @property
    def current_url(self):return self.urls[self.active]
    @property
    def current_window_handle(self):return self.active
    @property
    def window_handles(self):return list(self.handles)
    def get(self,url):self.urls[self.active]=url
    def close(self):
        self.closed.append(self.active)
        self.handles.remove(self.active)
        self.active=self.handles[0]


class Chrome:
    made=[]
    def __init__(self,cfg):
        self.cfg=cfg
        self.driver=Driver()
        self.was_closed=False
        self.made.append(self)
    def start(self):return self.driver
    def close(self):self.was_closed=True


class Verifier:
    def __init__(self,driver,email,timeout):pass
    def verify(self):pass


class Page:
    prompts=[]
    failure=False
    def __init__(self,driver,url,ui,response):
        self.driver=driver
        self.url=url
    def open_new(self):
        self.driver.get(self.url)
    def ask(self,prompt):
        self.prompts.append((self.driver.current_window_handle,prompt))
        if self.failure:
            raise ValueError("simulated possibly submitted response lost")
        if 'arithmetic' in prompt:
            return 'BEGIN_JSON\n{"role":"physics","sum":4}\nEND_JSON'
        return 'BEGIN_JSON\n{"role":"semantics","ms":"momentum","zh":"??"}\nEND_JSON'


class ExistingLoginProbeTests(unittest.TestCase):
    def setUp(self):
        root=tempfile.TemporaryDirectory()
        self.addCleanup(root.cleanup)
        self.root=Path(root.name)
        self.repo=self.root/"repo"
        self.repo.mkdir()
        self.profile=self.root/"profile"
        (self.profile/"gemini-browser").mkdir(parents=True)
        (self.profile/"gemini-browser"/"Default").mkdir()
        (self.profile/"gemini-browser"/"Default"/"Preferences").write_text("initialized")
        self.config=Config(self.repo,self.profile)
        self.output=self.root/"private-receipt"
        self.pdf=self.root/"source.pdf"
        self.pdf.write_bytes(b"%PDF-1.4 test only")
        self.pkg=self.root/"package.json"
        self.pkg.write_text(json.dumps({"activities":[{"id":ACTIVITY_ID}]}))
        Page.prompts.clear()
        Page.failure=False
        Chrome.made.clear()

    def test_existing_login_ready_is_attempt_only_not_authenticated(self):
        import hashlib
        from app_generator.runtime.private_gemini_pilot import readiness
        evidence={"activityId":ACTIVITY_ID,
                  "sourceSha256":hashlib.sha256(self.pdf.read_bytes()).hexdigest(),
                  "sourceEvidence":"a private source passage of adequate length" }
        r=readiness(self.config,self.pkg,self.pdf,evidence,existing_login=True)
        self.assertEqual([True,True],r["existingAuthorizedProfileEvidence"])
        self.assertFalse(r["authenticated"])
        self.assertFalse(r["independentGoogleAccounts"])
        self.assertEqual([False,False],r["distinctReviewerProfilesProvisioned"])
        self.assertTrue(r["readyToAttemptBrowserReview"])
        self.assertFalse(r["publicationAuthorized"])

    def test_two_new_tabs_one_existing_login_without_source(self):
        with patch("scripts.probe_existing_gemini.load_config",return_value=self.config):
            report=probe(self.root/"cfg",self.output,
                         chrome_factory=Chrome,verifier_factory=Verifier,
                         page_factory=Page,profile_busy=lambda _:False)
        self.assertEqual("NEUTRAL_TWO_CONTEXTS_CONFIRMED",report["status"])
        self.assertEqual(2,len(Page.prompts))
        self.assertNotEqual(Page.prompts[0][0],Page.prompts[1][0])
        self.assertTrue(all("No source documents" in p for _,p in Page.prompts))
        self.assertTrue(all(x["responseCaptured"] for x in report["roleResults"].values()))
        self.assertTrue(Chrome.made[-1].was_closed)
        self.assertNotIn("original",Chrome.made[-1].driver.closed)
        with self.assertRaisesRegex(ValueError,"already exists"):
            with patch("scripts.probe_existing_gemini.load_config",return_value=self.config):
                probe(self.root/"cfg",self.output,
                      chrome_factory=Chrome,verifier_factory=Verifier,page_factory=Page,profile_busy=lambda _:False)

    def test_restored_non_gemini_tab_gets_new_owned_neutral_verification_tab(self):
        class RestoredChrome(Chrome):
            def __init__(self,cfg):
                super().__init__(cfg)
                self.driver.urls["original"]="https://example.net/previous-page"
                self.navigation=[]
                old_get=self.driver.get
                def get(url):
                    self.navigation.append((self.driver.active,url))
                    old_get(url)
                self.driver.get=get
        with patch("scripts.probe_existing_gemini.load_config",return_value=self.config):
            result=probe(self.root/"cfg",self.output,
                         chrome_factory=RestoredChrome,verifier_factory=Verifier,
                         page_factory=Page,profile_busy=lambda _:False)
        self.assertEqual("NEUTRAL_TWO_CONTEXTS_CONFIRMED",result["status"])
        driver=Chrome.made[-1].driver
        self.assertEqual("https://example.net/previous-page",driver.urls["original"])
        self.assertTrue(all(handle!="original" for handle,url in Chrome.made[-1].navigation))
        self.assertEqual(3,len(driver.closed))
        self.assertNotIn("original",driver.closed)
        self.assertTrue(Chrome.made[-1].was_closed)
        self.assertEqual(2,len(Page.prompts))
        self.assertNotEqual(Page.prompts[0][0],Page.prompts[1][0])

    def test_redirected_fresh_neutral_tab_fails_before_prompt_and_preserves_original(self):
        class RedirectChrome(Chrome):
            def __init__(self,cfg):
                super().__init__(cfg)
                self.driver.urls["original"]="https://example.net/previous-page"
                self.navigation=[]
                def get(url):
                    self.navigation.append((self.driver.active,url))
                    self.driver.urls[self.driver.active]="https://www.google.com/"
                self.driver.get=get
        with patch("scripts.probe_existing_gemini.load_config",return_value=self.config):
            result=probe(self.root/"cfg",self.output,
                         chrome_factory=RedirectChrome,verifier_factory=Verifier,
                         page_factory=Page,profile_busy=lambda _:False)
        self.assertEqual("BLOCKED_BEFORE_OR_DURING_PROBE",result["status"])
        driver=Chrome.made[-1].driver
        self.assertEqual("https://example.net/previous-page",driver.urls["original"])
        self.assertNotIn("original",driver.closed)
        self.assertTrue(all(handle!="original" for handle,url in Chrome.made[-1].navigation))
        self.assertEqual([],Page.prompts)
        receipt=json.loads((self.output/"state.json").read_text(encoding="utf-8"))
        self.assertEqual("BLOCKED_BEFORE_OR_DURING_PROBE",receipt["status"])
        self.assertFalse(receipt["sourcePdfUploaded"])
        self.assertFalse(receipt["publicationAuthorized"])
        self.assertEqual({},receipt["roles"])

    def test_ambiguous_request_has_durable_claim_and_never_retries(self):
        Page.failure=True
        with patch("scripts.probe_existing_gemini.load_config",return_value=self.config):
            report=probe(self.root/"cfg",self.output,
                         chrome_factory=Chrome,verifier_factory=Verifier,page_factory=Page,profile_busy=lambda _:False)
        self.assertEqual("REQUIRES_RECONCILIATION",report["status"])
        self.assertEqual(1,len(Page.prompts))
        r=json.loads((self.output/"state.json").read_text())
        self.assertEqual("AMBIGUOUS",r["roles"]["physics"]["state"])
        self.assertNotIn("semantics",r["roles"])
        self.assertFalse(r["sourcePdfUploaded"])
        self.assertFalse(r["publicationAuthorized"])

    def test_busy_authoring_profile_blocks_before_claim_or_browser(self):
        with patch("scripts.probe_existing_gemini.load_config",return_value=self.config):
            with self.assertRaisesRegex(ValueError,"busy"):
                probe(self.root/"cfg",self.output,
                      chrome_factory=Chrome,verifier_factory=Verifier,
                      page_factory=Page,profile_busy=lambda _:True)
        self.assertFalse(self.output.exists())
        self.assertEqual(0,len(Chrome.made))
        self.assertEqual(0,len(Page.prompts))

    def test_ambiguous_diagnostics_never_store_model_text(self):
        from scripts.probe_existing_gemini import privacy_safe_response_diagnostics
        from unittest.mock import patch
        seen='PRIVATE MODEL TEXT THAT MUST NOT BE PERSISTED'
        with patch("scripts.probe_existing_gemini.find_all",return_value=[object()]), \
             patch("scripts.probe_existing_gemini._response_text",return_value=seen), \
             patch("scripts.probe_existing_gemini._generation_signals",return_value=(False,True)):
            out=privacy_safe_response_diagnostics(Driver())
        self.assertEqual("OBSERVED_COUNTS_ONLY",out["status"])
        self.assertEqual(1,out["visibleResponseCount"])
        self.assertEqual(len(seen),out["longestResponseCharacters"])
        self.assertFalse(out["generationActive"])
        self.assertTrue(out["responseCompleteSignal"])
        self.assertNotIn(seen,json.dumps(out))

    def test_ambiguous_claim_persists_safe_ui_diagnostics_without_resend(self):
        Page.failure=True
        simulated={"status":"OBSERVED_COUNTS_ONLY",
                   "visibleResponseCount":1,"nonemptyResponseCount":1,
                   "longestResponseCharacters":52,"parseableJsonFrameCount":0,
                   "generationActive":False,"responseCompleteSignal":True}
        with patch("scripts.probe_existing_gemini.load_config",return_value=self.config), \
             patch("scripts.probe_existing_gemini.privacy_safe_response_diagnostics",
                   return_value=simulated):
            report=probe(self.root/"cfg",self.output,chrome_factory=Chrome,
                         verifier_factory=Verifier,page_factory=Page,
                         profile_busy=lambda _:False)
        self.assertEqual("REQUIRES_RECONCILIATION",report["status"])
        self.assertEqual(1,len(Page.prompts))
        state=json.loads((self.output/"state.json").read_text(encoding="utf-8"))
        self.assertEqual(simulated,state["roles"]["physics"]["privacySafeUiDiagnostics"])
        self.assertEqual("AMBIGUOUS",state["roles"]["physics"]["state"])
        self.assertNotIn("semantics",state["roles"])

    def test_repo_receipts_rejected_before_browser_start(self):
        with patch("scripts.probe_existing_gemini.load_config",return_value=self.config):
            with self.assertRaisesRegex(ValueError,"inside Git"):
                probe(self.root/"cfg",self.repo/"bad",
                      chrome_factory=Chrome,verifier_factory=Verifier,page_factory=Page,profile_busy=lambda _:False)
        self.assertEqual(0,len(Chrome.made))
        self.assertFalse((self.repo/"bad").exists())

if __name__=="__main__":
    unittest.main()

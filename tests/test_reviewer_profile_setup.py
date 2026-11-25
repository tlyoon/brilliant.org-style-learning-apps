import json
import subprocess
import sys
import tempfile
import unittest
from dataclasses import dataclass
from pathlib import Path
from unittest.mock import patch

from app_generator.gemini.reviewer_profile_setup import (
    NEUTRAL_GEMINI,inspect_reviewer_profiles,open_missing_signin_windows,
    role_browser_config,
)

ROOT=Path(__file__).resolve().parents[1]

@dataclass(frozen=True)
class FakeConfig:
    repo_root:Path
    chrome_profile_dir:Path
    browser_mode:str="controlled"
    gem_url:str="https://gemini.google.com/gem/author"
    gem_edit_url:str="https://gemini.google.com/gem/author/edit"
    llm_backend:str="gemini_api"

class FakeWindow:
    requests=[]
    def __init__(self,config):
        self.config=config
        self.requests.append(config)
    def open_window(self):
        dest=self.config.chrome_profile_dir/"gemini-browser"/"Default"
        dest.mkdir(parents=True)
        (dest/"Preferences").write_text("fake-local-profile",encoding="utf-8")

class ProfilesTests(unittest.TestCase):
    def setUp(self):
        temp=tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        root=Path(temp.name)
        self.repo=root/"repo"
        self.repo.mkdir()
        self.base=root/"local-preserved-profile"
        self.base.mkdir()
        (self.base/"do-not-touch.txt").write_text("author",encoding="utf-8")
        self.config=FakeConfig(self.repo,self.base)

    def test_readiness_never_infers_authentication(self):
        record=inspect_reviewer_profiles(self.config)
        self.assertEqual("PREFLIGHT_ONLY",record["status"])
        self.assertFalse(record["usingPaidApi"])
        self.assertTrue(all(not t["profileExists"] for t in record["profiles"]))
        self.assertTrue(all(not t["authenticated"] for t in record["profiles"]))
        self.assertFalse(record["browserResponseCaptured"])
        self.assertFalse(record["publicationAuthorized"])

    def test_provision_two_neutral_distinct_browser_profiles(self):
        FakeWindow.requests.clear()
        result=open_missing_signin_windows(self.config,launcher=FakeWindow)
        self.assertEqual(["physics","semantics"],result["launchedRoles"])
        self.assertTrue(all(x["chromeInitialized"] for x in result["profiles"]))
        self.assertEqual(2,len(FakeWindow.requests))
        self.assertNotEqual(FakeWindow.requests[0].chrome_profile_dir,
                            FakeWindow.requests[1].chrome_profile_dir)
        for cfg in FakeWindow.requests:
            self.assertEqual(NEUTRAL_GEMINI,cfg.gem_url)
            self.assertEqual(NEUTRAL_GEMINI,cfg.gem_edit_url)
            self.assertEqual("gemini_browser",cfg.llm_backend)
            self.assertNotEqual(cfg.chrome_profile_dir,self.base)
        self.assertEqual("author",(self.base/"do-not-touch.txt").read_text())
        self.assertTrue(all(not x["authenticated"] for x in result["profiles"]))
        self.assertFalse(result["publicationAuthorized"])

    def test_repeat_is_idempotent_and_does_not_open_existing_profile(self):
        FakeWindow.requests.clear()
        open_missing_signin_windows(self.config,launcher=FakeWindow)
        again=open_missing_signin_windows(self.config,launcher=FakeWindow)
        self.assertEqual([] ,again["launchedRoles"])
        self.assertEqual(["physics","semantics"],again["skippedExistingRoles"])
        self.assertEqual(2,len(FakeWindow.requests))

    def test_missing_only_provisions_one_role(self):
        FakeWindow.requests.clear()
        status=role_browser_config(self.config,"physics")
        (status.chrome_profile_dir/"gemini-browser").mkdir(parents=True)
        result=open_missing_signin_windows(self.config,launcher=FakeWindow)
        self.assertEqual(["semantics"],result["launchedRoles"])
        self.assertEqual(["physics"],result["skippedExistingRoles"])
        self.assertEqual(1,len(FakeWindow.requests))

    def test_no_untrusted_locations_or_attach_mode(self):
        bad=FakeConfig(self.repo,self.repo/"profile")
        with self.assertRaisesRegex(ValueError,"Git"):
            inspect_reviewer_profiles(bad)
        bad=FakeConfig(self.repo,self.base,browser_mode="attach")
        with self.assertRaisesRegex(ValueError,"controlled"):
            open_missing_signin_windows(bad,launcher=FakeWindow)
        with self.assertRaisesRegex(ValueError,"roles"):
            role_browser_config(self.config,"authoring")
        self.assertFalse((self.repo/"profile").exists())

    def test_refuse_partial_provisioning_root(self):
        cfg=role_browser_config(self.config,"physics")
        cfg.chrome_profile_dir.mkdir(parents=True)
        (cfg.chrome_profile_dir/"mystery.lock").write_text("reserved")
        with self.assertRaisesRegex(ValueError,"unexpected"):
            open_missing_signin_windows(self.config,launcher=FakeWindow)

    def test_cli_readonly_status_works_in_isolated_python(self):
        r=subprocess.run(
            [sys.executable,"-I",
             str(ROOT/"scripts"/"prepare_academic_reviewers.py"),"--help"],
             capture_output=True,text=True,timeout=20)
        self.assertEqual(0,r.returncode,r.stderr)
        self.assertIn("--open-missing-windows",r.stdout)

    def test_private_pilot_cli_overrides_only_review_backend(self):
        from scripts import private_section94_gemini_pilot as pilot
        with tempfile.TemporaryDirectory() as d:
            dest=Path(d)/"pilot"
            args=[
                "private_section94_gemini_pilot.py",
                "--config",str(Path(d)/"dummy.toml"),
                "--v3",str(Path(d)/"v3"),
                "--v2",str(Path(d)/"v2"),
                "--pdf",str(Path(d)/"source.pdf"),
                "--proofs",str(Path(d)/"proof.json"),
                "--out",str(dest),
            ]
            seen=[]
            def preflight(cfg,pkg,pdf,source,*,existing_login=False):
                seen.append(cfg.llm_backend)
                self.assertFalse(existing_login)
                return {"readyToAttemptBrowserReview":False,
                        "authenticated":False,
                        "academicQA":"REVIEW_REQUIRED",
                        "publicationAuthorized":False}
            with patch.object(pilot,"load_config",return_value=self.config), \
                patch.object(pilot,"prepare_context",return_value={"verified":True}), \
                patch.object(pilot,"readiness",side_effect=preflight), \
                patch.object(sys,"argv",args):
                ret=pilot.main()
            self.assertEqual(2,ret)
            self.assertEqual(["gemini_browser"],seen)
            self.assertEqual("gemini_api",self.config.llm_backend)
            self.assertTrue((dest/"private-pilot-evidence.json").is_file())

if __name__=="__main__":
    unittest.main()

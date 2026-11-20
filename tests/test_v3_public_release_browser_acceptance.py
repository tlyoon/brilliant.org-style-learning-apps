"""BSA230 browser acceptance and exact favicon404 regression controls.

These synthetic tests are separate from the real Yoga6 Chrome acceptance.
"""
from hashlib import sha256
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from app_generator.runtime import v3_public_release_browser_acceptance as m
from app_generator.runtime.v3_five_stage_completion import _BASE, _hash
from app_generator.runtime.v3_pinned_public_release_proposal import _manifest


class ActualChromeConsoleClassification(unittest.TestCase):
    def test_exact_historical_favicon404_is_benign_only(self):
        text=("http://127.0.0.1:65248/favicon.ico - Failed to load resource: "
              "the server responded with a status of 404 (File not found)")
        result=m._console_health([{"level":"SEVERE","message":text}])
        self.assertEqual(result["favicon404Ignored"],1)
        self.assertEqual(result["severeRuntimeErrors"],[])

    def test_actual_runtime_js_not_found_remains_failure(self):
        text=("http://127.0.0.1:65248/section-9-1/app/app.js "
              "- Failed to load resource: the server responded with a "
              "status of 404 (File not found)")
        got=m._console_health([{"level":"SEVERE","message":text}])
        self.assertEqual(len(got["severeRuntimeErrors"]),1)

    def test_favicon_five_hundred_is_not_ignored(self):
        text=("http://127.0.0.1:65248/favicon.ico - Failed to load resource: "
              "the server responded with a status of 500 (Server Error)")
        got=m._console_health([{"level":"SEVERE","message":text}])
        self.assertEqual(len(got["severeRuntimeErrors"]),1)

    def test_remote_unrelated_favicon_not_ignored(self):
        text=("https://example.com/favicon.ico - Failed to load resource: "
              "the server responded with a status of 404 (File not found)")
        got=m._console_health([{"level":"SEVERE","message":text}])
        self.assertEqual(len(got["severeRuntimeErrors"]),1)

    def test_javascript_exceptions_remain_blocking(self):
        got=m._console_health([{"level":"SEVERE",
            "message":"Uncaught TypeError: Cannot read properties of null"}])
        self.assertEqual(len(got["severeRuntimeErrors"]),1)

    def test_nonsevere_console_info_not_blocking(self):
        got=m._console_health([{"level":"WARNING","message":"some warning"},
                               {"level":"INFO","message":"startup"}])
        self.assertEqual(got["severeRuntimeErrors"],[])

    def test_real_browser_route_and_button_state_required(self):
        result=m._check_page_state({
            "path":"/section-9-1/","appTextChars":940,"buttons":7,
            "initialPlaceholder":False,"failedLoading":False})
        self.assertEqual(result["route"],"section-9-1")
        self.assertTrue(result["realChromeRendered"])

    def test_empty_or_stalled_or_wrong_route_fails(self):
        sample={"path":"/section-9-2/","appTextChars":630,"buttons":7,
                "initialPlaceholder":False,"failedLoading":False}
        for key,bad in (("path","/section-8-2/"),
                        ("appTextChars",0),("buttons",0),
                        ("initialPlaceholder",True),("failedLoading",True)):
            with self.subTest(key=key):
                candidate={**sample,key:bad}
                with self.assertRaisesRegex(ValueError,"NOT_RENDERED"):
                    m._check_page_state(candidate)
        for field in ("initialPlaceholder","failedLoading"):
            candidate=sample.copy();del candidate[field]
            with self.assertRaises(ValueError):
                m._check_page_state(candidate)


class V10SourceBoundBrowserPreflight(unittest.TestCase):
    def setUp(self):
        t=TemporaryDirectory()
        self.addCleanup(t.cleanup)
        self.base=Path(t.name)
        self.repo=self.base/"repo";self.repo.mkdir()
        self.private=self.base/"private";self.private.mkdir()
        self.head="a"*40;self.proposal="b"*64
        self.folder=self.private/_BASE/self.head/self.proposal
        self.folder.mkdir(parents=True)
        self.stage=self.folder/"v9-private-pinned-public-proposal"
        self.stage.mkdir()
        self.diffs=[]
        for section in m._SECTIONS:
            dir=self.stage/section
            (dir/"app").mkdir(parents=True)
            (dir/"content").mkdir()
            package=dir/"content"/"package.json"
            package.write_text(json.dumps({"fake":section}))
            (dir/".nojekyll").write_bytes(b"")
            (dir/"index.html").write_text("<html>valid fake</html>")
            for i in range(5):
                (dir/"app"/f"fake{i}.js").write_text("fake")
            self.diffs.append({
                "section":section,"packageSha256":sha256(package.read_bytes()).hexdigest()})
        self.ready={"status":"VERSIONED_SCIENCE_BROWSER_AND_CI_VERIFIED_UNADMITTED",
                    "exactHeadHostedCiSuccess":True,
                    "codeWorkingTreeClean":True,
                    "publicationAuthorized":False,
                    "gitHead":self.head,"proposalSha256":self.proposal}
        self.v9={
            "status":m.V9_STATUS,
            "gitHead":self.head,"proposalSha256":self.proposal,
            "productionReleaseBuilderInvocations":3,
            "privateFullRouteBundles":3,"releaseFileCount":24,
            "changedPublicRoutes":list(m._SECTIONS),
            "routeDiffs":self.diffs,
            "publicMainPinnedSha":"f"*40,
            "publicPushExecuted":False,
            "publicMergeExecuted":False,
            "publicDeployExecuted":False,
            "publicationAuthorized":False,
            "fileManifestSha256":_hash({"files":_manifest(self.stage)}),
        }
        self.v9["integritySha256"]=_hash(self.v9)
        (self.folder/m._V9).write_text(json.dumps(self.v9))

    def go(self):
        with patch.object(m,"_read_previous",return_value=self.ready),patch.object(
                m,"_git_info",return_value=(self.head,"feature/fake")),patch.object(
                m,"_git_clean",return_value=True),patch.object(
                m,"_hosted_runs",return_value=[]),patch.object(
                m,"_exact_ci_success",return_value=True):
            return m._preflight(self.repo,self.private,self.ready,self.v9)

    def test_private_manifest_and_v9_signed_exact_proof_accepted(self):
        folder,stage,saved=self.go()
        self.assertEqual(stage,self.stage)
        self.assertEqual(folder,self.folder)
        self.assertEqual(saved,self.v9)

    def test_tampered_bundle_refused_before_chrome_launch(self):
        package=self.stage/"section-9-6"/"content"/"package.json"
        package.write_bytes(b"wrong")
        with self.assertRaisesRegex(ValueError,"BUNDLE_CONTENT_CHANGED"):
            self.go()

    def test_forged_v9_acceptance_refused(self):
        bad=json.loads((self.folder/m._V9).read_text())
        bad["releaseFileCount"]=23
        (self.folder/m._V9).write_text(json.dumps(bad))
        with self.assertRaisesRegex(ValueError,"V9_SIGNED_RECEIPT_CHANGED"):
            self.go()

    def test_missing_source_ci_refused_before_chrome(self):
        self.ready["exactHeadHostedCiSuccess"]=False
        with self.assertRaisesRegex(ValueError,"PREREQUISITE_MISSING"):
            self.go()

if __name__=="__main__":
    unittest.main()

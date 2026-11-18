"""BSA-204: REAL Chrome in production, synthetic browser ONLY in temp tests.

No model call; scientific approval and publication stay false. Test authentic
normal-worker invocation wiring and source/git/renderer/receipt reuse.
"""
from __future__ import annotations
from hashlib import sha256
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from app_generator.runtime.v3_science_candidate_browser import (
    _canonical, _assert_result, advance_science_revision_browser_qa,
    _STATUS, _SCHEMA,
)

_EXPECTED={
    "schema":_SCHEMA,"baseUnadmittedProposalSha256":"a"*64,
    "correctedSection96Sha256":"b"*64,
    "correctedIndex9ReviewInputSha256":"c"*64,
    "originalFrozenSection96Sha256":"d"*64,
    "gitRevisionSha256":"e"*40,
    "rendererRuntimeSha256":"f"*64,
    "activitiesInCandidate":108,
}
_BROWSING={
    "renderedChecks":698,"viewports":2,"locales":3,
    "all108ActivitiesVisited":True,
    "allLocaleViewportPromptChecks":648,
    "sourceFree":True,"publicationAuthorized":False,
    "originalModelVerdictsChanged":False,
}


class ScienceCandidateBrowserTests(unittest.TestCase):
    def setUp(self):
        ctx=tempfile.TemporaryDirectory()
        self.addCleanup(ctx.cleanup)
        base=Path(ctx.name)
        self.repo=base/"repo"
        self.repo.mkdir()
        self.course=self.repo/"content"/"chapter-9"
        self.private=base/"private"
        self.private.mkdir()
        self.identity=sha256(_canonical(_EXPECTED)).hexdigest()

    def plan(self, expected=None):
        return (dict(_EXPECTED if expected is None else expected),
                self.identity,[("synthetic-trilingual",b"not-real-browser",[])])

    def exercise(self,site,packages):
        self.assertTrue(site.is_dir())
        self.assertEqual(packages[0][0],"synthetic-trilingual")
        return dict(_BROWSING)

    def check_browser(self,exercise=None,expected=None):
        with (
            patch("app_generator.runtime.v3_science_candidate_browser._identity",
                  return_value=self.plan(expected)),
            patch("scripts.check_v3_real_chapter9_browser._stage_site"),
        ):
            return advance_science_revision_browser_qa(
                self.repo,self.course,self.private,
                exercise=self.exercise if exercise is None else exercise)

    def test_first_run_and_restart_reuse_same_immutable_real_contract(self):
        result=self.check_browser()
        self.assertEqual(result["status"],_STATUS)
        self.assertFalse(result["publicationAuthorized"])
        self.assertFalse(result["versionedScopeAdmitted"])
        self.assertEqual(result["genuineGeminiReviewsAdded"],0)
        self.assertEqual(result["renderedChecks"],698)
        with patch(
            "app_generator.runtime.v3_science_candidate_browser._identity",
            return_value=self.plan(),
        ):
            cached=advance_science_revision_browser_qa(
                self.repo,self.course,self.private,
                exercise=lambda *_:self.fail("should reuse verified receipt"))
        self.assertEqual(result,cached)

    def test_bad_or_partial_chrome_result_cannot_create_pass_receipt(self):
        for changes in ({"renderedChecks":697},
                        {"sourceFree":False},
                        {"allLocaleViewportPromptChecks":647},
                        {"all108ActivitiesVisited":False},
                        {"publicationAuthorized":True}):
            with self.subTest(changes=changes):
                with self.assertRaisesRegex(
                    ValueError,"GENUINE_COVERAGE_INCOMPLETE"):
                    self.check_browser(exercise=lambda *_:{**_BROWSING,**changes})
                self.assertFalse((self.private/"scientific-failure-browser-acceptance"
                                  /self.identity).exists())

    def test_tampered_prior_receipt_stops_before_browser(self):
        self.check_browser()
        file=(self.private/"scientific-failure-browser-acceptance"/
              self.identity/"receipt.json")
        previous=file.read_bytes()
        try:
            file.write_bytes(previous+b" ")
            with self.assertRaisesRegex(ValueError,"TAMPERED_RECEIPT_BYTES"):
                self.check_browser(exercise=lambda *_:self.fail("tampered receipt"))
            file.write_text(json.dumps(
                {"status":_STATUS,"publicationAuthorized":True}))
            with self.assertRaisesRegex(ValueError,"UNTRUSTED_PASS_RECEIPT"):
                self.check_browser(exercise=lambda *_:self.fail("tampered receipt"))
        finally:
            file.write_bytes(previous)

    def test_change_of_revision_source_or_renderer_never_reuses_receipt(self):
        self.check_browser()
        for field in ("gitRevisionSha256","correctedSection96Sha256",
                      "baseUnadmittedProposalSha256","rendererRuntimeSha256"):
            with self.subTest(field=field):
                updated=dict(_EXPECTED)
                updated[field]=("0"*len(updated[field]))
                digest=sha256(_canonical(updated)).hexdigest()
                with patch(
                    "app_generator.runtime.v3_science_candidate_browser._identity",
                    return_value=(updated,digest,[("fake",b"",[])]),
                ),patch("scripts.check_v3_real_chapter9_browser._stage_site"):
                    called=[]
                    def record(*_):
                        called.append(1)
                        return dict(_BROWSING)
                    newer=advance_science_revision_browser_qa(
                        self.repo,self.course,self.private,exercise=record)
                self.assertEqual(called,[1])
                self.assertEqual(newer[field],updated[field])
                self.assertNotEqual(newer["integritySha256"],
                                    self.check_browser()["integritySha256"])

    def test_worker_invokes_separate_browser_only_when_science_staged(self):
        from scripts.run_v3_yoga6_recovery_worker import (
            _complete_source_free_with_browser,
        )
        with patch("scripts.run_v3_yoga6_recovery_worker."
                   "advance_real_candidate_browser_qa",
                   return_value={"status":"NORMAL_SOURCEBOUND_PASS"}),patch(
            "app_generator.runtime.v3_science_candidate_browser."
            "advance_science_revision_browser_qa",
            return_value={"status":_STATUS,"publicationAuthorized":False},
        ) as science:
            result=_complete_source_free_with_browser(
                self.private,{
                    "scientificFailureRepair":{
                        "status":"NEW_SECTION96_SCIENCE_REPAIR_STAGED_REVIEW_NOT_AUTHORIZED"}})
            self.assertEqual(result["scienceRevisionBrowserAcceptance"]
                             ["status"],_STATUS)
            science.assert_called_once()
            no_change=_complete_source_free_with_browser(
                self.private,{"scientificFailureRepair":{"status":"NOT_APPLICABLE"}})
            self.assertNotIn("scienceRevisionBrowserAcceptance",no_change)
            science.assert_called_once()

    def test_linked_browser_receipt_parent_never_reused(self):
        from app_generator.runtime.v3_science_candidate_browser import (
            _RECEIPT_DIR,
        )
        actual=Path.is_symlink
        suspect=self.private/_RECEIPT_DIR
        def fake_link(path):
            if path==suspect:
                return True
            return actual(path)
        with patch(
            "app_generator.runtime.v3_science_candidate_browser._identity",
            return_value=self.plan()
        ),patch("pathlib.Path.is_symlink",autospec=True,
                side_effect=fake_link):
            with self.assertRaisesRegex(
                ValueError,"INVALID_PRIVATE_ROOT"):
                advance_science_revision_browser_qa(
                    self.repo,self.course,self.private,exercise=self.exercise)

    def test_private_root_cannot_be_repo_or_relative_path(self):
        with self.assertRaisesRegex(ValueError,"UNSAFE_PRIVATE"):
            advance_science_revision_browser_qa(
                self.repo,self.course,self.repo,exercise=self.exercise)
        with self.assertRaisesRegex(ValueError,"UNSAFE_PRIVATE"):
            advance_science_revision_browser_qa(
                self.repo,self.course,Path("relative-private"),
                exercise=self.exercise)


if __name__=="__main__":
    unittest.main()

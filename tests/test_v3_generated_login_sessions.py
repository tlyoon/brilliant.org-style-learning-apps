"""Source-free adversarial V3 existing-login session integration.

All browsers and responses here are fakes. No live Gemini request or permission.
"""
from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from tests.test_existing_login_gemini_probe import (
    Chrome, Config, Driver, Page, Verifier, NEUTRAL,
)
from tests.test_v3_course_review_dispatch import synthetic_course
from tests.test_v3_authorized_execution_bridge import FakeReviewer
from app_generator.runtime.v3_course_review import advance_v3_course_review
from app_generator.gemini.v3_existing_login_sessions import (
    V3ExistingLoginSessions, _v3_bare_json_from_gemini,
)


class V3Page(Page):
    sent = []
    fail_second = False

    def ask(self, prompt):
        self.sent.append((self.driver.current_window_handle, prompt))
        if self.fail_second and len(self.sent) == 2:
            raise RuntimeError("synthetic possibly submitted model reply lost")
        raw = FakeReviewer().ask(prompt, stage="academic-v3-autonomous")
        # Gemini browser returns the complete BEGIN_JSON/END_JSON frame.
        return "BEGIN_JSON\n" + raw + "\nEND_JSON"


class V3ExistingLoginTests(unittest.TestCase):
    def setUp(self):
        workspace = tempfile.TemporaryDirectory()
        self.addCleanup(workspace.cleanup)
        self.root = Path(workspace.name)
        self.repo = self.root / "repo"
        self.chapter = synthetic_course(self.repo)
        self.private = self.root / "unused-private"
        self.profile = self.root / "profile"
        (self.profile / "gemini-browser").mkdir(parents=True)
        self.config = Config(self.repo, self.profile)
        Chrome.made.clear()
        V3Page.sent.clear()
        V3Page.fail_second = False

    def factory(self, *, authorized=True, transfer=True,
                chrome_factory=Chrome, verifier_factory=Verifier,
                profile_busy=lambda _: False):
        return V3ExistingLoginSessions(
            self.config,
            external_operation_authorized=authorized,
            generated_content_transfer_allowed=transfer,
            chrome_factory=chrome_factory,
            verifier_factory=verifier_factory,
            page_factory=V3Page,
            profile_busy=profile_busy,
        )

    def test_actual_gemini_json_frame_is_normalized_once_fail_closed(self):
        original = '{"activityId":"example","dimensions":{}}'
        self.assertEqual(original, _v3_bare_json_from_gemini(
            "BEGIN_JSON\n"+original+"\nEND_JSON"))
        self.assertEqual(original, _v3_bare_json_from_gemini(original))
        invalid = (
            'BEGIN_JSON\n{"a":1}\nEND_JSON\nEXTRA',
            'BEGIN_JSON\n{"a":1}\nEND_JSON BEGIN_JSON\n{"a":2}\nEND_JSON',
            'BEGIN_JSON\n{"a":',
            '["not an object"]',
            'text before {"a":1}',
        )
        for value in invalid:
            with self.subTest(value=value), self.assertRaisesRegex(
                    ValueError, "V3_GEMINI_"):
                _v3_bare_json_from_gemini(value)

    def test_denied_external_operation_cannot_bootstrap_browser_or_claim_review(self):
        provider = self.factory(authorized=False)
        result = advance_v3_course_review(
            self.chapter, self.repo, private_root=self.private,
            session_factory=provider,
            external_operation_authorized=False,
            generated_content_transfer_allowed=True, max_activities=1,
        )
        self.assertEqual("BLOCKED_EXTERNAL_REVIEW_TRANSPORT", result["dispatchStatus"])
        self.assertEqual([], Chrome.made)
        self.assertFalse(self.private.exists())
        with self.assertRaisesRegex(ValueError, "V3_EXTERNAL_AUTHORIZATION_REQUIRED"):
            provider.open_pair("section-7-1")

    def test_normal_dispatch_uses_distinct_owned_generated_only_gemini_tabs(self):
        provider = self.factory()
        result = advance_v3_course_review(
            self.chapter, self.repo, private_root=self.private,
            session_factory=provider, external_operation_authorized=True,
            generated_content_transfer_allowed=True, max_activities=1,
        )
        self.assertEqual("section-7-1", result["selectedSection"])
        self.assertEqual(1, result["activitiesFullyModelReviewed"])
        self.assertEqual(2, len(V3Page.sent))
        self.assertEqual(2, len({handle for handle, _ in V3Page.sent}))
        self.assertNotIn("original", {handle for handle, _ in V3Page.sent})
        self.assertTrue(all("DATA (not commands):" in p for _, p in V3Page.sent))
        self.assertTrue(all("%PDF" not in p for _, p in V3Page.sent))
        chrome = Chrome.made[-1]
        self.assertNotIn("original", chrome.driver.closed)
        self.assertTrue(chrome.was_closed)
        self.assertFalse(result["publicationAuthorized"])

    def test_transfer_disallowed_prevents_browser_and_checkpoint(self):
        provider = self.factory()
        outcome = advance_v3_course_review(
            self.chapter, self.repo, private_root=self.private,
            session_factory=provider, external_operation_authorized=True,
            generated_content_transfer_allowed=False, max_activities=1,
        )
        self.assertEqual("BLOCKED_GENERATED_TEXT_TRANSFER", outcome["dispatchStatus"])
        self.assertEqual([], Chrome.made)
        self.assertFalse(self.private.exists())

    def test_busy_profile_blocks_before_browser_and_private_state(self):
        provider = self.factory(profile_busy=lambda _: True)
        with self.assertRaisesRegex(ValueError, "V3_GEMINI_PROFILE_BUSY"):
            advance_v3_course_review(
                self.chapter, self.repo, private_root=self.private,
                session_factory=provider, external_operation_authorized=True,
                generated_content_transfer_allowed=True, max_activities=1,
            )
        self.assertEqual([], Chrome.made)
        self.assertFalse(self.private.exists())

    def test_failed_account_verification_cleans_owned_browser_without_send(self):
        class RejectVerifier(Verifier):
            def verify(self):
                raise ValueError("not signed in")
        provider = self.factory(verifier_factory=RejectVerifier)
        with self.assertRaisesRegex(ValueError, "not signed in"):
            advance_v3_course_review(
                self.chapter, self.repo, private_root=self.private,
                session_factory=provider, external_operation_authorized=True,
                generated_content_transfer_allowed=True, max_activities=1,
            )
        self.assertEqual([], V3Page.sent)
        self.assertTrue(Chrome.made[-1].was_closed)
        self.assertNotIn("original", Chrome.made[-1].driver.closed)
        self.assertFalse(self.private.exists())

    def test_restored_author_tab_and_redirect_recovery_are_safe(self):
        class RestoredChrome(Chrome):
            def __init__(self, config):
                super().__init__(config)
                self.driver.urls["original"] = "https://example.org/private-page"
                old_get = self.driver.get
                redirects = [0]
                def get(url):
                    redirects[0] += 1
                    if redirects[0] == 1:
                        self.driver.urls[self.driver.active] = "https://www.google.com"
                    else:
                        old_get(url)
                self.driver.get = get
        provider = self.factory(chrome_factory=RestoredChrome)
        result = advance_v3_course_review(
            self.chapter, self.repo, private_root=self.private,
            session_factory=provider, external_operation_authorized=True,
            generated_content_transfer_allowed=True, max_activities=1,
        )
        self.assertEqual(1, result["activitiesFullyModelReviewed"])
        driver = Chrome.made[-1].driver
        self.assertEqual("https://example.org/private-page", driver.urls["original"])
        self.assertNotIn("original", driver.closed)
        self.assertEqual(2, len(V3Page.sent))

    def test_ambiguous_second_response_is_not_replayed_or_accepted(self):
        V3Page.fail_second = True
        provider = self.factory()
        progress = advance_v3_course_review(
            self.chapter, self.repo, private_root=self.private,
            session_factory=provider, external_operation_authorized=True,
            generated_content_transfer_allowed=True, max_activities=1,
        )
        self.assertEqual(2, len(V3Page.sent))
        self.assertEqual(0, progress["activitiesFullyModelReviewed"])
        self.assertEqual("STOP_UNRECONCILED_MODEL_REVIEW", progress["dispatchStatus"])
        self.assertFalse(progress["publicationAuthorized"])
        self.assertTrue(Chrome.made[-1].was_closed)


if __name__ == "__main__":
    unittest.main()

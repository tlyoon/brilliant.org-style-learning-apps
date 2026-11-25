"""Run independent conversation tabs, not separate Google logins."""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from app_generator.gemini.existing_login_reviewers import (
    BoundFreshConversation, ExistingLoginReviewerFactory, NEUTRAL_URL
)


@dataclass(frozen=True)
class FakeConfig:
    chrome_profile_dir: Path
    repo_root: Path
    login_name: str = "teacher@example.com"
    browser_mode: str = "controlled"
    llm_backend: str = "gemini_browser"
    gem_url: str = "https://gemini.google.com/gem/author"
    gem_edit_url: str = "https://gemini.google.com/gem/author/edit"


class Switch:
    def __init__(self, driver):
        self.driver=driver
    def new_window(self, kind):
        assert kind=="tab"
        h="fresh-"+str(len(self.driver.handles))
        self.driver.handles.append(h)
        self.driver.active=h
        self.driver.urls[h]="about:blank"
    def window(self, handle):
        if handle not in self.driver.handles:
            raise ValueError("missing tab")
        self.driver.active=handle


class FakeDriver:
    def __init__(self):
        self.handles=["original-author"]
        self.urls={"original-author":"https://gemini.google.com/gem/author"}
        self.active="original-author"
        self.switch_to=Switch(self)
        self.visited=[]
        self.closed=[]
    @property
    def window_handles(self):return self.handles[:]
    @property
    def current_window_handle(self):return self.active
    @property
    def current_url(self):return self.urls[self.active]
    def get(self,url):
        self.visited.append((self.active,url))
        self.urls[self.active]=url
    def close(self):
        self.closed.append(self.active)
        self.handles.remove(self.active)
        self.active=self.handles[0] if self.handles else ""


class FakeChrome:
    made=[]
    def __init__(self,config):
        self.config=config
        self.driver=FakeDriver()
        self.is_closed=False
        FakeChrome.made.append(self)
    def start(self):return self.driver
    def close(self):self.is_closed=True


class FakeAccountVerifier:
    calls=[]
    def __init__(self,driver,expected,timeout):
        self.driver=driver
        self.expected=expected
        self.timeout=timeout
    def verify(self):
        self.calls.append(self.expected)


class FakeClient:
    made=[]
    def __init__(self,driver,config):
        self.driver=driver
        self.config=config
        self.conversation=self
        self.handle=driver.current_window_handle
        self.made.append(self)
    def open_conversation_select_model_and_attach(self,pdf):
        self.driver.get(NEUTRAL_URL)
        self.pdf=pdf
    def ask(self,prompt):
        if self.driver.current_window_handle!=self.handle:
            raise AssertionError("cross-contaminated review context")
        return "BEGIN_JSON\n{}\nEND_JSON"


class ExistingLoginTests(unittest.TestCase):
    def setUp(self):
        temp=tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root=Path(temp.name)
        self.profile=self.root/"existing"
        self.profile.mkdir()
        self.repo=self.root/"git"
        self.repo.mkdir()
        self.pdf=self.root/"source.pdf"
        self.pdf.write_bytes(b"%PDF-1.4 fixture")
        self.config=FakeConfig(self.profile,self.repo)
        FakeChrome.made.clear()
        FakeClient.made.clear()
        FakeAccountVerifier.calls.clear()

    def factory(self):
        return ExistingLoginReviewerFactory(
            self.config,self.pdf,
            chrome_factory=FakeChrome,
            client_factory=FakeClient,
            account_verifier=FakeAccountVerifier,
            profile_busy=lambda path: False,
        )

    def test_one_authenticated_context_two_fresh_gemini_chats(self):
        f=self.factory()
        with f:
            a,b=f.open_pair("int-select-isolated-conditions")
            self.assertNotEqual(a.session_id,b.session_id)
            self.assertNotEqual(a.reviewer_id,b.reviewer_id)
            self.assertIsNot(a.conversation,b.conversation)
            self.assertNotEqual(a.conversation.handle,b.conversation.handle)
            self.assertEqual("BEGIN_JSON\n{}\nEND_JSON",a.conversation.ask("physics",stage="academic-physics_consistency"))
            self.assertEqual("BEGIN_JSON\n{}\nEND_JSON",b.conversation.ask("translation",stage="academic-multilingual_meaning"))
            self.assertEqual(["teacher@example.com"],FakeAccountVerifier.calls)
            self.assertEqual(1,len(FakeChrome.made))
            self.assertEqual(2,len(FakeClient.made))
            self.assertEqual("original-author",FakeChrome.made[0].driver.window_handles[0])
            self.assertEqual("https://gemini.google.com/gem/author",
                             FakeChrome.made[0].driver.urls["original-author"])
        self.assertTrue(FakeChrome.made[0].is_closed)
        self.assertEqual(2,len(FakeChrome.made[0].driver.closed))
        self.assertNotIn("original-author",FakeChrome.made[0].driver.closed)

    def test_refuses_cross_role_nonacademic_and_wrong_origin(self):
        with self.factory() as f:
            a,b=f.open_pair("collision")
            with self.assertRaisesRegex(ValueError,"academic"):
                a.conversation.ask("write slides",stage="generation")
            d=FakeChrome.made[-1].driver
            d.urls[b.conversation.handle]="https://not-gemini.example.com"
            with self.assertRaisesRegex(ValueError,"outside Gemini"):
                b.conversation.ask("x",stage="academic-physics_consistency")
            d.urls[b.conversation.handle]=NEUTRAL_URL
            d.handles.remove(b.conversation.handle)
            with self.assertRaisesRegex(ValueError,"no longer exists"):
                b.conversation.ask("x",stage="academic-physics_consistency")

    def test_existing_author_chat_not_navigated_or_closed(self):
        with self.factory() as f:
            f.open_pair("collision")
            d=FakeChrome.made[-1].driver
            self.assertFalse(any(h=="original-author" and url==NEUTRAL_URL for h,url in d.visited[1:]))
            self.assertNotIn("original-author",d.closed)

    def test_restored_unrelated_starting_tab_is_preserved_and_new_neutral_tab_verified(self):
        class RestoredChrome(FakeChrome):
            def __init__(self, config):
                super().__init__(config)
                self.driver.urls["original-author"] = "https://example.net/unrelated"
        f=ExistingLoginReviewerFactory(
            self.config,self.pdf,
            chrome_factory=RestoredChrome,client_factory=FakeClient,
            account_verifier=FakeAccountVerifier,profile_busy=lambda path:False)
        with f:
            a,b=f.open_pair("collision")
            d=FakeChrome.made[-1].driver
            self.assertEqual("https://example.net/unrelated",
                             d.urls["original-author"])
            self.assertFalse(any(h=="original-author" for h,url in d.visited))
            self.assertTrue(any(
                h not in {"original-author",a.conversation.handle,b.conversation.handle}
                and url==NEUTRAL_URL for h,url in d.visited
            ))
            self.assertNotEqual(a.conversation.handle,b.conversation.handle)
            self.assertEqual(["teacher@example.com"],FakeAccountVerifier.calls)
            self.assertEqual(2,len(FakeClient.made))
        self.assertEqual(3,len(d.closed))
        self.assertNotIn("original-author",d.closed)

    def test_one_redirected_fresh_tab_recovers_on_second_owned_tab(self):
        class OneRedirectChrome(FakeChrome):
            def __init__(self,config):
                super().__init__(config)
                self.driver.urls["original-author"]="https://example.net/unrelated"
                real_get=self.driver.get
                attempts=[0]
                def get(url):
                    if url==NEUTRAL_URL and attempts[0]==0:
                        attempts[0]+=1
                        real_get("https://www.google.com/")
                    else:
                        real_get(url)
                self.driver.get=get
        f=ExistingLoginReviewerFactory(
            self.config,self.pdf,chrome_factory=OneRedirectChrome,
            client_factory=FakeClient,account_verifier=FakeAccountVerifier,
            profile_busy=lambda _:False)
        with f:
            a,b=f.open_pair("collision")
            d=FakeChrome.made[-1].driver
            self.assertEqual("https://example.net/unrelated",
                             d.urls["original-author"])
            self.assertNotIn("original-author",d.closed)
            self.assertEqual(1,len(d.closed))
            self.assertNotEqual(a.conversation.handle,b.conversation.handle)
            self.assertEqual(["teacher@example.com"],FakeAccountVerifier.calls)
            self.assertEqual(2,len(FakeClient.made))
            self.assertTrue(all(h!="original-author" for h,url in d.visited))
        self.assertEqual(4,len(d.closed))
        self.assertNotIn("original-author",d.closed)

    def test_both_owned_neutral_tabs_redirect_and_never_verify_or_upload(self):
        class RedirectChrome(FakeChrome):
            def __init__(self,config):
                super().__init__(config)
                self.driver.urls["original-author"]="https://example.net/unrelated"
                real_get=self.driver.get
                def redirect(url):
                    real_get("https://www.google.com/")
                self.driver.get=redirect
        f=ExistingLoginReviewerFactory(
            self.config,self.pdf,chrome_factory=RedirectChrome,
            client_factory=FakeClient,account_verifier=FakeAccountVerifier,
            profile_busy=lambda _:False)
        with self.assertRaisesRegex(ValueError,"fresh account-verification"):
            f.open_pair("collision")
        d=FakeChrome.made[-1].driver
        self.assertEqual("https://example.net/unrelated",
                         d.urls["original-author"])
        self.assertEqual(2,len(d.closed))
        self.assertNotIn("original-author",d.closed)
        self.assertEqual([],FakeAccountVerifier.calls)
        self.assertEqual([],FakeClient.made)
        self.assertTrue(FakeChrome.made[-1].is_closed)

    def test_restored_page_recovery_fails_closed_if_new_tab_redirects_away(self):
        class RedirectChrome(FakeChrome):
            def __init__(self, config):
                super().__init__(config)
                self.driver.urls["original-author"]="https://example.net/unrelated"
                def redirect_elsewhere(url):
                    self.driver.visited.append((self.driver.active,url))
                    self.driver.urls[self.driver.active]="https://example.net/redirected"
                self.driver.get=redirect_elsewhere
        f=ExistingLoginReviewerFactory(
            self.config,self.pdf,
            chrome_factory=RedirectChrome,client_factory=FakeClient,
            account_verifier=FakeAccountVerifier,profile_busy=lambda path:False)
        with self.assertRaisesRegex(ValueError,"fresh account-verification"):
            f.open_pair("collision")
        d=FakeChrome.made[-1].driver
        self.assertEqual("https://example.net/unrelated",d.urls["original-author"])
        self.assertFalse(any(h=="original-author" for h,url in d.visited))
        self.assertNotIn("original-author",d.closed)
        self.assertEqual([],FakeClient.made)
        self.assertEqual([],FakeAccountVerifier.calls)
        self.assertTrue(FakeChrome.made[-1].is_closed)

    def test_busy_existing_author_profile_cannot_be_taken_over(self):
        f=ExistingLoginReviewerFactory(
            self.config,self.pdf,
            chrome_factory=FakeChrome,client_factory=FakeClient,
            account_verifier=FakeAccountVerifier,
            profile_busy=lambda path: True,
        )
        with self.assertRaisesRegex(ValueError,"currently in use"):
            f.open_pair("collision")
        self.assertEqual([],FakeChrome.made)

    def test_fail_closed_unverified_authentication(self):
        class Denied(FakeAccountVerifier):
            def verify(self):raise ValueError("not signed in")
        f=ExistingLoginReviewerFactory(self.config,self.pdf,
            chrome_factory=FakeChrome,client_factory=FakeClient,
            account_verifier=Denied,profile_busy=lambda path: False)
        with self.assertRaisesRegex(ValueError,"not signed in"):
            f.open_pair("collision")
        self.assertTrue(FakeChrome.made[-1].is_closed)
        self.assertEqual([],FakeClient.made)

    def test_invalid_profile_source_backend(self):
        bad=FakeConfig(self.profile,self.repo,llm_backend="gemini_api")
        with self.assertRaisesRegex(ValueError,"non-API"):
            ExistingLoginReviewerFactory(bad,self.pdf)
        bad=FakeConfig(self.repo/"unsafe",self.repo)
        bad.chrome_profile_dir.mkdir()
        with self.assertRaisesRegex(ValueError,"inside Git"):
            ExistingLoginReviewerFactory(bad,self.pdf)
        bad=FakeConfig(self.profile,self.repo,browser_mode="attach")
        with self.assertRaisesRegex(ValueError,"controlled"):
            ExistingLoginReviewerFactory(bad,self.pdf)

    def test_each_new_activity_requires_fresh_browser_claim(self):
        with self.factory() as f:
            first=f.open_pair("one")
            with self.assertRaisesRegex(ValueError,"previous review"):
                f.open_pair("two")
            f.close()
            second=f.open_pair("two")
            self.assertNotEqual(first[0].session_id,second[0].session_id)
            self.assertEqual(2,len(FakeChrome.made))

if __name__=="__main__":
    unittest.main()

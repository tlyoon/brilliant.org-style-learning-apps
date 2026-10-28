import tempfile
import unittest
from dataclasses import dataclass
from pathlib import Path
from app_generator.gemini.academic_reviewers import ReviewerBrowser, IndependentReviewerFactory
from app_generator.errors import AuthenticationRequired

@dataclass
class Config:
    browser_mode: str
    chrome_profile_dir: Path
    login_name: str = "teacher@example.com"
    ui_timeout_seconds: int = 8

class FakeAuth:
    def __init__(self, driver, expected, timeout):
        self.expected = expected
    def verify_noninteractive(self):
        return None

class FakeChrome:
    made=[]
    def __init__(self,config):
        self.config=config
        self.closed=False
        FakeChrome.made.append(self)
    def start(self):return object()
    def close(self):self.closed=True

class FakeClient:
    def __init__(self,driver,config):
        self.driver=driver
        self.config=config
        self.conversation=self
        self.attached=None
    def open_conversation_select_model_and_attach(self,pdf):self.attached=pdf
    def ask(self,prompt):return "BEGIN_JSON\n{}\nEND_JSON"

class TestReviewers(unittest.TestCase):
    def test_separate_author_and_review_browser_profiles(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            pdf=root/"source.pdf"
            pdf.write_bytes(b"%PDF-1.4 fixture")
            base=Config("controlled",root/"generator")
            def make(role,config,pdf):
                return ReviewerBrowser(role,config,pdf,
                                       chrome_factory=FakeChrome,
                                       client_factory=FakeClient,
                                       account_verifier=FakeAuth)
            f=IndependentReviewerFactory(base,pdf,browser_factory=make)
            a,b=f.open_pair("collision")
            self.assertNotEqual(a.session_id,b.session_id)
            self.assertNotEqual(a.reviewer_id,b.reviewer_id)
            self.assertNotEqual(FakeChrome.made[0].config.chrome_profile_dir,
                                FakeChrome.made[1].config.chrome_profile_dir)
            self.assertEqual(a.conversation.ask("test",stage="academic-source_fidelity"),
                             "BEGIN_JSON\n{}\nEND_JSON")
            with self.assertRaisesRegex(ValueError,"generation"):
                a.conversation.ask("test",stage="generation")
            f.close()
            self.assertTrue(all(x.closed for x in FakeChrome.made))
            self.assertNotEqual(a.session_id,f.open_pair("new")[0].session_id)
            f.close()

    def test_unauthenticated_reviewer_cannot_attach_source_or_prompt(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            pdf=root/"source.pdf"
            pdf.write_bytes(b"%PDF-1.4 fixture")
            called=[]
            class Denied(FakeAuth):
                def verify_noninteractive(self):
                    raise AuthenticationRequired("no previous authorization")
            class RecordingClient(FakeClient):
                def __init__(self,*args):
                    called.append("client-created")
                    super().__init__(*args)
            reviewer=ReviewerBrowser(
                "physics",Config("controlled",root/"generator"),pdf,
                chrome_factory=FakeChrome,
                client_factory=RecordingClient,
                account_verifier=Denied,
            )
            with self.assertRaises(AuthenticationRequired):
                reviewer.open()
            self.assertEqual([],called, "source-capable client must not be constructed")
            self.assertTrue(FakeChrome.made[-1].closed)
            self.assertIsNone(reviewer.client)

    def test_reject_attach_mode_and_unverified_source(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            cfg=Config("attach",root/"profile")
            with self.assertRaisesRegex(ValueError,"controlled"):
                ReviewerBrowser("physics",cfg,root/"source.pdf")
            cfg.browser_mode="controlled"
            with self.assertRaisesRegex(ValueError,"PDF"):
                ReviewerBrowser("physics",cfg,root/"missing.pdf")

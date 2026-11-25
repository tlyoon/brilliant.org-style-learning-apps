"""Regression coverage for bounded source-free Gemini key failover."""
import os
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from app_generator.errors import AuthenticationRequired, GeminiApiError, TransientGeminiError
from app_generator.llm.gemini_key_failover import (
    build_keyed_gemini_client, find_gemini_keys, select_healthy_key,
)


class HttpError(Exception):
    def __init__(self, status_code):
        super().__init__("provider error")
        self.status_code=status_code


class FakeTypes:
    class HttpRetryOptions:
        def __init__(self, **kwargs):
            self.attempts=kwargs["attempts"]

    class HttpOptions:
        def __init__(self, **kwargs):
            self.timeout=kwargs["timeout"]
            self.retry_options=kwargs["retry_options"]

    class GenerateContentConfig:
        def __init__(self, **kwargs):
            self.options=kwargs


class FakeSdk:
    def __init__(self, result_by_key):
        self.answers=result_by_key
        self.created=[]
        outer=self

        class _Client:
            def __init__(self, *, api_key, http_options):
                self.label=api_key
                self.closed=False
                self.models=self
                self.options=http_options
                self.calls=[]
                outer.created.append(self)

            def generate_content(self, **kwargs):
                self.calls.append(kwargs)
                answer=outer.answers[self.label]
                if isinstance(answer, BaseException):
                    raise answer
                return SimpleNamespace(text=answer)

            def close(self):
                self.closed=True

        self.Client=_Client


class KeyDiscoveryTests(unittest.TestCase):
    def make_dotenv(self, directory, text):
        home=Path(directory)
        file=home/"Microvid"/".env"
        file.parent.mkdir()
        file.write_text(text,encoding="utf-8")
        return file

    def test_default_folder_key_order_and_secret_is_not_repr_visible(self):
        with tempfile.TemporaryDirectory() as d:
            self.make_dotenv(d,
                "GEMINI_API_KEY='private-default'\n"
                "GEMINI_API_KEY_2='private-second'\n"
                "GEMINI_API_KEY_1=private-first # comment\n"
                "MALICIOUS=$(test-command)\n")
            candidates=find_gemini_keys(environ={"LOCALAPPDATA":d})
            self.assertEqual(["GEMINI_API_KEY_1","GEMINI_API_KEY_2","GEMINI_API_KEY"],
                             [x.label for x in candidates])
            self.assertNotIn("private-",repr(candidates))
            self.assertEqual("private-first",candidates[0].secret)

    def test_explicit_environment_precedence_and_duplicate_dedup(self):
        with tempfile.TemporaryDirectory() as d:
            self.make_dotenv(d,"GEMINI_API_KEY_1=abc\nGEMINI_API_KEY_2=def\nGEMINI_API_KEY=abc\n")
            candidates=find_gemini_keys(environ={
                "LOCALAPPDATA":d,"GOOGLE_API_KEY":"abc","GEMINI_API_KEY":"def"})
            self.assertEqual(2,len(candidates))
            self.assertEqual(["GOOGLE_API_KEY (environment)","GEMINI_API_KEY (environment)"],
                             [x.label for x in candidates])

    def test_missing_file_and_no_localappdata_do_not_scan_filesystem(self):
        self.assertEqual((),find_gemini_keys(environ={}))
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual((),find_gemini_keys(environ={"LOCALAPPDATA":d}))

    def test_never_executes_shell_expansions(self):
        with tempfile.TemporaryDirectory() as d:
            self.make_dotenv(d,"GEMINI_API_KEY_1='$(rm -rf anything)'\n")
            self.assertEqual("$(rm -rf anything)",
                             find_gemini_keys(environ={"LOCALAPPDATA":d})[0].secret)

    def test_numbered_names_are_numeric_sorted_and_bounded(self):
        with tempfile.TemporaryDirectory() as d:
            values="".join(f"GEMINI_API_KEY_{i}=unique-key-{i}\n" for i in range(12,0,-1))
            self.make_dotenv(d,values)
            result=find_gemini_keys(environ={"LOCALAPPDATA":d})
            self.assertEqual(8,len(result))
            self.assertEqual(["GEMINI_API_KEY_"+str(i) for i in range(1,9)],
                             [r.label for r in result])


class KeyFailoverTests(unittest.TestCase):
    def setUp(self):
        self.keys=find_gemini_keys(environ={},dotenv_path=None)
        from app_generator.llm.gemini_key_failover import ApiKeyCandidate
        self.keys=tuple(ApiKeyCandidate(label=f"KEY_{i}",secret=f"token-{i}") for i in range(1,4))

    def test_503_then_504_then_success(self):
        called=[]
        def probe(key):
            called.append(key.label)
            if len(called)==1: raise HttpError(503)
            if len(called)==2: raise HttpError(504)
            return "ready"
        selected,outcome=select_healthy_key(self.keys,probe)
        self.assertEqual("KEY_3",selected.label)
        self.assertEqual("ready",outcome)
        self.assertEqual(["KEY_1","KEY_2","KEY_3"],called)

    def test_exhausted_capacity_fails_closed(self):
        with self.assertRaisesRegex(TransientGeminiError,"source-free preflight"):
            select_healthy_key(self.keys,lambda _: (_ for _ in ()).throw(HttpError(503)))

    def test_access_and_billing_failures_try_next_distinct_key(self):
        for code in (401, 402, 403, 503, 504):
            with self.subTest(code=code):
                visited=[]
                def probe(candidate):
                    visited.append(candidate.label)
                    if len(visited) == 1:
                        raise HttpError(code)
                    return "READY"
                chosen,result=select_healthy_key(self.keys,probe)
                self.assertEqual("KEY_2",chosen.label)
                self.assertEqual("READY",result)
                self.assertEqual(["KEY_1","KEY_2"],visited)

    def test_failed_key_statuses_are_logged_without_secret_values(self):
        called=[]
        def probe(candidate):
            called.append(candidate.label)
            if len(called) == 1:
                raise HttpError(402)
            return "READY"
        with self.assertLogs(
            "app_generator.llm.gemini_key_failover", level="INFO"
        ) as recorded:
            chosen,result=select_healthy_key(self.keys,probe)
        self.assertEqual("KEY_2",chosen.label)
        self.assertEqual("READY",result)
        log="\n".join(recorded.output)
        self.assertIn("KEY_1",log)
        self.assertIn("HTTP 402",log)
        for candidate in self.keys:
            self.assertNotIn(candidate.secret,log)

    def test_all_keys_billing_blocked_does_not_send_source(self):
        visited=[]
        def probe(candidate):
            visited.append(candidate.label)
            raise HttpError(402)
        with self.assertRaisesRegex(GeminiApiError,"HTTP 402 billing"):
            select_healthy_key(self.keys,probe)
        self.assertEqual(["KEY_1","KEY_2","KEY_3"],visited)

    def test_all_keys_denied_reports_auth_failure(self):
        with self.assertRaises(AuthenticationRequired):
            select_healthy_key(self.keys,lambda _: (_ for _ in ()).throw(HttpError(403)))

    def test_quota_and_bad_request_stop_without_trying_other_keys(self):
        for code,expected in ((429,TransientGeminiError),(400,GeminiApiError)):
            with self.subTest(code=code):
                visited=[]
                def probe(candidate):
                    visited.append(candidate.label)
                    raise HttpError(code)
                with self.assertRaises(expected):
                    select_healthy_key(self.keys,probe)
                self.assertEqual(["KEY_1"],visited)

    def test_transport_error_does_not_rotate(self):
        attempts=[]
        def probe(c):
            attempts.append(c.label)
            raise TimeoutError("unknown completion")
        with self.assertRaises(GeminiApiError):
            select_healthy_key(self.keys,probe)
        self.assertEqual(["KEY_1"],attempts)


class ClientSelectionTests(unittest.TestCase):
    def test_preflight_uses_no_pdf_and_selects_second_key(self):
        with tempfile.TemporaryDirectory() as d:
            envpath=Path(d)/"Microvid"/".env"
            envpath.parent.mkdir()
            envpath.write_text("GEMINI_API_KEY_1=first\nGEMINI_API_KEY_2=second\n",encoding="utf-8")
            sdk=FakeSdk({"first":HttpError(503),"second":"READY"})
            config=SimpleNamespace(gemini_api_model="gemini-3.8-flash",
                gemini_api_timeout_seconds=1200)
            with patch.dict(os.environ,{"LOCALAPPDATA":d},clear=True):
                selected=build_keyed_gemini_client(sdk,FakeTypes,config,probe_keys=True)
            self.assertEqual("second",selected.label)
            self.assertEqual(2,len(sdk.created))
            self.assertTrue(sdk.created[0].closed)
            self.assertFalse(sdk.created[1].closed)
            self.assertEqual(1,selected.options.retry_options.attempts)
            self.assertEqual("Reply with exactly the word READY.",
                             selected.calls[0]["contents"])
            self.assertNotIn("application/pdf",str(selected.calls))

    def test_source_free_probe_omits_deprecated_sampling_for_gemini_3_8(self):
        # Google Gemini 3.8 Flash migration explicitly removes temperature,
        # top_p and top_k. This is separate from an HTTP 402 billing error.
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)/"Microvid"
            root.mkdir()
            (root/".env").write_text("GEMINI_API_KEY_1=test-only-key\n",encoding="utf-8")
            sdk=FakeSdk({"test-only-key":"READY"})
            config=SimpleNamespace(gemini_api_model="gemini-3.8-flash",
                gemini_api_timeout_seconds=1200)
            with patch.dict(os.environ,{"LOCALAPPDATA":d},clear=True):
                selected=build_keyed_gemini_client(sdk,FakeTypes,config)
            self.assertEqual("test-only-key",selected.label)
            self.assertEqual(1,len(sdk.created))
            call=sdk.created[0].calls[0]
            self.assertEqual("gemini-3.8-flash",call["model"])
            self.assertEqual(512,call["config"].options["max_output_tokens"])
            for obsolete in ("temperature","top_p","top_k","candidate_count"):
                self.assertNotIn(obsolete,call["config"].options)
            self.assertEqual("Reply with exactly the word READY.",call["contents"])
            self.assertNotIn("application/pdf",str(sdk.created[0].calls))

    def test_billing_failure_is_recovered_before_source_upload(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)/"Microvid"
            root.mkdir()
            (root/".env").write_text(
                "GEMINI_API_KEY_1=unfunded\nGEMINI_API_KEY_2=funded\n",
                encoding="utf-8",
            )
            sdk=FakeSdk({"unfunded":HttpError(402),"funded":"READY"})
            config=SimpleNamespace(gemini_api_model="gemini-3.8-flash",
                gemini_api_timeout_seconds=1200)
            with patch.dict(os.environ,{"LOCALAPPDATA":d},clear=True):
                selected=build_keyed_gemini_client(sdk,FakeTypes,config,probe_keys=True)
            self.assertEqual("funded",selected.label)
            self.assertTrue(sdk.created[0].closed)
            self.assertEqual(["Reply with exactly the word READY."],
                             [call["contents"] for call in sdk.created[0].calls])
            self.assertNotIn("application/pdf",str(sdk.created[0].calls))

    def test_single_key_is_preflighted_before_source(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)/"Microvid"
            root.mkdir()
            (root/".env").write_text("GEMINI_API_KEY_1=only-key\n")
            sdk=FakeSdk({"only-key":HttpError(402)})
            config=SimpleNamespace(gemini_api_model="gemini-3.8-flash",
                gemini_api_timeout_seconds=1200)
            with patch.dict(os.environ,{"LOCALAPPDATA":d},clear=True):
                with self.assertRaisesRegex(GeminiApiError,"HTTP 402"):
                    build_keyed_gemini_client(sdk,FakeTypes,config,probe_keys=True)
            self.assertEqual(1,len(sdk.created))
            self.assertTrue(sdk.created[0].closed)
            self.assertNotIn("application/pdf",str(sdk.created[0].calls))

    def test_ordinary_client_creation_inherently_tries_next_key(self):
        # Calling the factory without an opt-in flag must safely select
        # the second key before any source-bearing API request.
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)/"Microvid"
            root.mkdir()
            (root/".env").write_text(
                "GEMINI_API_KEY_1=blocked\nGEMINI_API_KEY_2=working\n",
                encoding="utf-8",
            )
            sdk=FakeSdk({"blocked":HttpError(402),"working":"READY"})
            config=SimpleNamespace(gemini_api_model="gemini-3.8-flash",
                gemini_api_timeout_seconds=1200)
            with patch.dict(os.environ,{"LOCALAPPDATA":d},clear=True):
                chosen=build_keyed_gemini_client(sdk,FakeTypes,config)
            self.assertEqual("working",chosen.label)
            self.assertEqual(2,len(sdk.created))
            self.assertTrue(sdk.created[0].closed)
            self.assertEqual(1,len(sdk.created[0].calls))
            self.assertEqual("Reply with exactly the word READY.",
                             sdk.created[0].calls[0]["contents"])
            self.assertEqual("Reply with exactly the word READY.",
                             sdk.created[1].calls[0]["contents"])
            self.assertNotIn("application/pdf",str(sdk.created[0].calls))
            self.assertNotIn("application/pdf",str(sdk.created[1].calls))

    def test_doctor_does_not_generate(self):
        with tempfile.TemporaryDirectory() as d:
            envpath=Path(d)/"Microvid"/".env"
            envpath.parent.mkdir()
            envpath.write_text("GEMINI_API_KEY_1=first\nGEMINI_API_KEY_2=second\n")
            sdk=FakeSdk({"first":"READY","second":"READY"})
            with patch.dict(os.environ,{"LOCALAPPDATA":d},clear=True):
                selected=build_keyed_gemini_client(
                    sdk,FakeTypes,SimpleNamespace(
                        gemini_api_model="gemini-3.8-flash",
                        gemini_api_timeout_seconds=1200),
                    probe_keys=False)
            self.assertEqual("first",selected.label)
            self.assertEqual([],selected.calls)
            self.assertEqual(1,len(sdk.created))

if __name__=="__main__":
    unittest.main()

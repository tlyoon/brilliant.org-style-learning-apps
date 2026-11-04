import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from app_generator.errors import AuthenticationRequired, GeminiApiError, TransientGeminiError
from app_generator.llm.gemini_api import GeminiApiClient, build_gemini_sdk_client, response_schema_for_stage


class FakeModels:
    def __init__(self, outputs):
        self.outputs = iter(outputs)
        self.calls = []

    def generate_content(self, **kwargs):
        self.calls.append(kwargs)
        value = next(self.outputs)
        if isinstance(value, BaseException):
            raise value
        return SimpleNamespace(text=value)


class FakeSdk:
    def __init__(self, outputs):
        self.models = FakeModels(outputs)



class FakeTypes:
    """Only the SDK data-shape methods required by this unit-level test."""

    class Part:
        @staticmethod
        def from_bytes(*, data, mime_type):
            return SimpleNamespace(
                inline_data=SimpleNamespace(data=data, mime_type=mime_type)
            )

    class ThinkingConfig:
        def __init__(self, *, thinking_level):
            self.thinking_level = thinking_level

    class GenerateContentConfig:
        def __init__(self, **kwargs):
            self.__dict__.update(kwargs)
            self.response_json_schema = kwargs.get("response_json_schema")
            self.response_mime_type = kwargs.get("response_mime_type")



class GeminiApiClientTests(unittest.TestCase):
    def config(self, root: Path, **overrides):
        values = dict(
            repo_root=root,
            gemini_api_model="gemini-3.8-flash",
            gemini_api_location="global",
            gemini_api_thinking_level="high",
            gemini_api_timeout_seconds=1200,
            gemini_api_upload_timeout_seconds=30,
            gemini_api_max_attempts=3,
            gemini_api_retry_backoff_seconds=1,
        )
        values.update(overrides)
        return SimpleNamespace(**values)

    def test_shared_gemini_factory_auto_preflights_by_default(self):
        from inspect import signature

        self.assertIs(True, signature(build_gemini_sdk_client).parameters["probe_keys"].default)
        from app_generator.llm.gemini_key_failover import build_keyed_gemini_client
        self.assertIs(True, signature(build_keyed_gemini_client).parameters["probe_keys"].default)

    def test_production_pdf_client_uses_shared_factory_without_opt_in(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "config").mkdir()
            (root / "config" / "gem_instructions.md").write_text("MASTER", encoding="utf-8")
            pdf = root / "source.pdf"
            pdf.write_bytes(b"%PDF-test")
            sdk = FakeSdk(['{"ok":true}'])
            config = self.config(root)
            client = GeminiApiClient(config, (pdf,), sdk_types=FakeTypes)
            with patch(
                "app_generator.llm.gemini_api.build_gemini_sdk_client",
                return_value=sdk,
            ) as factory:
                client.prepare()
                self.assertEqual("BEGIN_JSON", client.ask("Return object", stage="custom").splitlines()[0])
            factory.assert_called_once_with(config)
            self.assertEqual(1, len(sdk.models.calls))

    def test_no_other_production_module_bypasses_shared_gemini_gateway(self):
        import re

        repo_root = Path(__file__).resolve().parents[1]
        authorized = {
            "app_generator/llm/gemini_api.py",
            "app_generator/llm/gemini_key_failover.py",
        }
        direct_calls = []
        for folder in ("app_generator", "scripts"):
            for source_file in (repo_root / folder).rglob("*.py"):
                relative = source_file.relative_to(repo_root).as_posix()
                if relative in authorized:
                    continue
                source = source_file.read_text(encoding="utf-8")
                if re.search(r"\bgenai\.Client\s*\(", source) or re.search(
                    r"\.models\.generate_content\s*\(", source
                ):
                    direct_calls.append(relative)
        self.assertEqual([], sorted(direct_calls), "Unprotected direct Gemini SDK entrypoints")

    def test_source_analysis_uses_inline_pdf_master_prompt_and_structured_output(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "config").mkdir()
            (root / "config" / "gem_instructions.md").write_text("MASTER POLICY", encoding="utf-8")
            pdf = root / "source.pdf"
            pdf.write_bytes(b"%PDF-test")
            sdk = FakeSdk(['{"sectionTitle":"Energy"}'])
            client = GeminiApiClient(self.config(root), (pdf,), sdk_client=sdk, sdk_types=FakeTypes, sleep=lambda _: None)
            client.prepare()
            response = client.ask("Analyze source", stage="source-analysis")
            self.assertEqual("BEGIN_JSON\n{\"sectionTitle\": \"Energy\"}\nEND_JSON", response)
            call = sdk.models.calls[0]
            self.assertEqual("gemini-3.8-flash", call["model"])
            self.assertGreaterEqual(len(call["contents"]), 2)
            self.assertEqual("application/pdf", call["contents"][0].inline_data.mime_type)
            self.assertEqual(b"%PDF-test", call["contents"][0].inline_data.data)
            self.assertIn("Analyze source", call["contents"][-1])
            self.assertEqual("MASTER POLICY", call["config"].system_instruction)
            self.assertEqual("HIGH", str(call["config"].thinking_config.thinking_level).split(".")[-1])
            self.assertEqual("application/json", call["config"].response_mime_type)
            self.assertIsNotNone(call["config"].response_json_schema)

    def test_transient_api_error_retries_then_succeeds(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "config").mkdir()
            (root / "config" / "gem_instructions.md").write_text("MASTER", encoding="utf-8")
            pdf = root / "source.pdf"
            pdf.write_bytes(b"%PDF-test")
            sdk = FakeSdk([TimeoutError("temporary timeout"), '{"ok":true}'])
            sleeps = []
            client = GeminiApiClient(self.config(root), (pdf,), sdk_client=sdk, sdk_types=FakeTypes, sleep=sleeps.append)
            client.prepare()
            response = client.ask("Return object", stage="custom")
            self.assertEqual("BEGIN_JSON\n{\"ok\": true}\nEND_JSON", response)
            self.assertEqual(2, len(sdk.models.calls))
            self.assertEqual([1], sleeps)

    def test_explicit_503_504_and_429_never_replay_controlled_pdf(self):
        class ProviderFailure(RuntimeError):
            def __init__(self, status_code):
                super().__init__("Simulated provider response")
                self.status_code = status_code

        for status in (503, 504, 429):
            with self.subTest(status=status), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                (root / "config").mkdir()
                (root / "config" / "gem_instructions.md").write_text("MASTER", encoding="utf-8")
                pdf = root / "source.pdf"
                pdf.write_bytes(b"%PDF-test")
                # The second entry would succeed if the code incorrectly replayed.
                sdk = FakeSdk([ProviderFailure(status), '{"ok":true}'])
                client = GeminiApiClient(
                    self.config(root, gemini_api_max_attempts=5),
                    (pdf,), sdk_client=sdk, sdk_types=FakeTypes,
                    sleep=lambda _: self.fail("no automatic source replay"),
                )
                client.prepare()
                with self.assertRaises(TransientGeminiError):
                    client.ask("Return object", stage="custom")
                self.assertEqual(1, len(sdk.models.calls))

    def test_http_402_after_pdf_submission_is_not_replayed(self):
        class BillingError(RuntimeError):
            status_code = 402

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "config").mkdir()
            (root / "config" / "gem_instructions.md").write_text("MASTER", encoding="utf-8")
            pdf = root / "source.pdf"
            pdf.write_bytes(b"%PDF-test")
            sdk = FakeSdk([BillingError("prepay exhausted"), '{"ok":true}'])
            client = GeminiApiClient(
                self.config(root, gemini_api_max_attempts=5),
                (pdf,), sdk_client=sdk, sdk_types=FakeTypes,
                sleep=lambda _: self.fail("source-bearing request must not replay"),
            )
            client.prepare()
            with self.assertRaisesRegex(GeminiApiError, "HTTP 402"):
                client.ask("Return object", stage="custom")
            self.assertEqual(1, len(sdk.models.calls))

    def test_keyboard_interrupt_propagates_without_being_wrapped(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "config").mkdir()
            (root / "config" / "gem_instructions.md").write_text("MASTER", encoding="utf-8")
            pdf = root / "source.pdf"
            pdf.write_bytes(b"%PDF-test")
            sdk = FakeSdk([KeyboardInterrupt()])
            client = GeminiApiClient(self.config(root), (pdf,), sdk_client=sdk, sdk_types=FakeTypes, sleep=lambda _: None)
            client.prepare()
            with self.assertRaises(KeyboardInterrupt):
                client.ask("Return object", stage="custom")
            self.assertEqual(1, len(sdk.models.calls))

    def test_permanent_api_error_is_not_mislabeled_transient(self):
        class BadRequest(RuntimeError):
            status_code = 400

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "config").mkdir()
            (root / "config" / "gem_instructions.md").write_text("MASTER", encoding="utf-8")
            pdf = root / "source.pdf"
            pdf.write_bytes(b"%PDF-test")
            sdk = FakeSdk([BadRequest("invalid request")])
            client = GeminiApiClient(self.config(root), (pdf,), sdk_client=sdk, sdk_types=FakeTypes, sleep=lambda _: None)
            client.prepare()
            with self.assertRaisesRegex(GeminiApiError, "HTTP 400"):
                client.ask("Return object", stage="custom")
            self.assertEqual(1, len(sdk.models.calls))

    def test_auth_api_error_maps_to_authentication_required(self):
        class Forbidden(RuntimeError):
            status_code = 403

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "config").mkdir()
            (root / "config" / "gem_instructions.md").write_text("MASTER", encoding="utf-8")
            pdf = root / "source.pdf"
            pdf.write_bytes(b"%PDF-test")
            sdk = FakeSdk([Forbidden("permission denied")])
            client = GeminiApiClient(self.config(root), (pdf,), sdk_client=sdk, sdk_types=FakeTypes, sleep=lambda _: None)
            client.prepare()
            with self.assertRaisesRegex(AuthenticationRequired, "403"):
                client.ask("Return object", stage="custom")
            self.assertEqual(1, len(sdk.models.calls))

    def test_fake_sdk_never_imports_real_google_genai(self):
        """A fake API response must never start the heavyweight real SDK."""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "config").mkdir()
            (root / "config" / "gem_instructions.md").write_text("MASTER", encoding="utf-8")
            pdf = root / "source.pdf"
            pdf.write_bytes(b"%PDF-test")
            sdk = FakeSdk(['{"ok":true}'])
            client = GeminiApiClient(
                self.config(root), (pdf,), sdk_client=sdk,
                sdk_types=FakeTypes, sleep=lambda _: None,
            )
            client.prepare()
            original_import = __import__

            def no_sdk_import(name, *args, **kwargs):
                if name == "google.genai" or name.startswith("google.genai."):
                    raise AssertionError("real SDK imported by fake unit test")
                return original_import(name, *args, **kwargs)

            with patch("builtins.__import__", side_effect=no_sdk_import):
                answer = client.ask("Return object", stage="custom")
            self.assertIn('"ok": true', answer)
            self.assertEqual(1, len(sdk.models.calls))

    def test_high_value_stage_schemas_are_explicit(self):
        domain = response_schema_for_stage("domain-discovery")
        self.assertEqual("object", domain["type"])
        self.assertIn("sampleAssessments", domain["required"])
        self.assertEqual(["consistent", "mixed", "ambiguous"], domain["properties"]["consistency"]["enum"])
        source = response_schema_for_stage("source-analysis")
        self.assertEqual("object", source["type"])
        self.assertIn("scopeNotes", source["required"])
        plan = response_schema_for_stage("activity-plan")
        self.assertEqual(18, plan["properties"]["activities"]["minItems"])
        self.assertIsNone(response_schema_for_stage("activity-batch-00"))

    def test_prepare_rejects_non_pdf_signature(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "config").mkdir()
            (root / "config" / "gem_instructions.md").write_text("MASTER", encoding="utf-8")
            pdf = root / "source.pdf"
            pdf.write_bytes(b"not a pdf")
            client = GeminiApiClient(self.config(root), (pdf,), sdk_client=FakeSdk([]), sdk_types=FakeTypes)
            with self.assertRaisesRegex(Exception, "PDF signature"):
                client.prepare()


if __name__ == "__main__":
    unittest.main()

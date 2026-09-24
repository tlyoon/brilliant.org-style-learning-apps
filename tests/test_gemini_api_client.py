import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from app_generator.llm.gemini_api import GeminiApiClient, response_schema_for_stage


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

    def test_source_analysis_uses_inline_pdf_master_prompt_and_structured_output(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "config").mkdir()
            (root / "config" / "gem_instructions.md").write_text("MASTER POLICY", encoding="utf-8")
            pdf = root / "source.pdf"
            pdf.write_bytes(b"%PDF-test")
            sdk = FakeSdk(['{"sectionTitle":"Energy"}'])
            client = GeminiApiClient(self.config(root), (pdf,), sdk_client=sdk, sleep=lambda _: None)
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
            client = GeminiApiClient(self.config(root), (pdf,), sdk_client=sdk, sleep=sleeps.append)
            client.prepare()
            response = client.ask("Return object", stage="custom")
            self.assertEqual("BEGIN_JSON\n{\"ok\": true}\nEND_JSON", response)
            self.assertEqual(2, len(sdk.models.calls))
            self.assertEqual([1], sleeps)

    def test_high_value_stage_schemas_are_explicit(self):
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
            client = GeminiApiClient(self.config(root), (pdf,), sdk_client=FakeSdk([]))
            with self.assertRaisesRegex(Exception, "PDF signature"):
                client.prepare()


if __name__ == "__main__":
    unittest.main()

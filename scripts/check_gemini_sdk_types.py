"""Read-only Google GenAI SDK shape smoke check (never creates a client/request).

Run in hosted CI where dependencies are on non-synchronized local disk.
Developer unit tests use an injected fake types adapter to avoid slow imports
from a cloud-synced workstation virtual environment.
"""
from __future__ import annotations


def main() -> int:
    from google.genai import types

    pdf = types.Part.from_bytes(data=b"%PDF-test", mime_type="application/pdf")
    if pdf.inline_data is None or pdf.inline_data.data != b"%PDF-test":
        raise AssertionError("SDK cannot create inline PDF parts")
    if pdf.inline_data.mime_type != "application/pdf":
        raise AssertionError("SDK PDF MIME type has changed")

    config = types.GenerateContentConfig(
        system_instruction="Offline SDK schema compatibility probe",
        thinking_config=types.ThinkingConfig(thinking_level="HIGH"),
        response_mime_type="application/json",
        response_json_schema={"type": "object"},
    )
    if config.response_mime_type != "application/json":
        raise AssertionError("SDK structured JSON configuration has changed")
    if config.thinking_config is None:
        raise AssertionError("SDK thinking configuration has changed")
    if config.response_json_schema is None:
        raise AssertionError("SDK schema field is no longer available")
    print("Real Gemini SDK type shapes passed (offline, no client or API request).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

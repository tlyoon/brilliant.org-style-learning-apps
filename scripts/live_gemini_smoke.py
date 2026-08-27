#!/usr/bin/env python3
"""Bounded live Gemini transport check without generating repository content."""

from __future__ import annotations

import argparse
import sys
import tempfile
from pathlib import Path

from app_generator.browser.chrome import ChromeSession
from app_generator.config import load_config
from app_generator.errors import GeneratorError, ResponseContractError
from app_generator.gemini.client import GeminiClient
from app_generator.generation.extraction import parse_json_response
from app_generator.locking import WorkerLock
from app_generator.sources.google_drive import DriveRestClient, resolve_drive_source
from app_generator.sources.google_drive_auth import authorize_google_drive


EXPECTED = {
    "status": "ok",
    "attachmentAccessible": True,
    "contract": "gemini-live-smoke-v1",
}

PROMPT = """Run a bounded transport smoke check. Do not quote, paraphrase, summarize, or otherwise reproduce the attached source. Confirm only whether the attachment is accessible. Return exactly three keys: status as the string ok, attachmentAccessible as boolean true, and contract as the string gemini-live-smoke-v1. Put the object between BEGIN_JSON and END_JSON sentinel lines, with no other keys or prose."""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    args = parser.parse_args()
    browser = None
    downloaded_source: Path | None = None
    try:
        config = load_config(args.config)
        if config.selection_mode != "specific":
            raise ResponseContractError("Live smoke testing requires selection_mode='specific'")
        with tempfile.TemporaryDirectory(prefix="content-generator-gemini-smoke-") as directory:
            if config.uses_google_drive:
                authorization = authorize_google_drive(config)
                drive = DriveRestClient(authorization.session, config.drive_api_timeout_seconds)
                source = resolve_drive_source(
                    drive,
                    sourcepath=config.sourcepath,
                    pdf_subchapter_path=config.pdf_subchapter_path,
                    target_filename=config.target_filename,
                    max_folders=config.max_drive_folders,
                )
                source_path = drive.download_file(source, Path(directory) / source.filename)
                downloaded_source = source_path
            else:
                if len(config.source_files) != 1:
                    raise ResponseContractError("Live smoke testing requires exactly one controlled source")
                source_path = config.source_files[0]

            with WorkerLock(config.state_dir, config.gem_url):
                browser = ChromeSession(config)
                driver = browser.start()
                client = GeminiClient(driver, config)
                client.open_editor_and_verify_account()
                client.configure_gem()
                model = client.open_conversation_select_model_and_attach(source_path)
                if downloaded_source is not None:
                    downloaded_source.unlink()
                    downloaded_source = None
                result = parse_json_response(client.ask(PROMPT))
                if result != EXPECTED:
                    raise ResponseContractError("Gemini returned the wrong live-smoke contract")
                print(f"Live Gemini smoke check passed using {model}.")
        return 0
    except GeneratorError as exc:
        print(f"{exc.code}: {exc}", file=sys.stderr)
        return 2
    except Exception as exc:
        print(f"UNEXPECTED_ERROR: {exc}", file=sys.stderr)
        return 3
    finally:
        if downloaded_source is not None:
            try:
                downloaded_source.unlink()
            except FileNotFoundError:
                pass
        if browser is not None:
            browser.close()


if __name__ == "__main__":
    raise SystemExit(main())

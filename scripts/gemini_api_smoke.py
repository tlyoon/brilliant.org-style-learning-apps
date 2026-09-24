"""Live Gemini API smoke test for one controlled Google Drive PDF."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from app_generator.config import load_config
from app_generator.generation.extraction import parse_json_response
from app_generator.llm.gemini_api import GeminiApiClient
from app_generator.prompts import source_analysis_prompt
from app_generator.sources.google_drive import DriveRestClient, ResolvedDriveSource, resolve_drive_source
from app_generator.sources.google_drive_auth import authorize_google_drive


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--subchapter", default="8.4")
    parser.add_argument("--sourcepath", default=None)
    parser.add_argument("--drive-file-id", default=None)
    args = parser.parse_args()

    overrides = {"pdf_subchapter_path": args.subchapter, "llm_backend": "gemini_api"}
    if args.sourcepath:
        overrides["sourcepath"] = args.sourcepath
    config = load_config(args.config, cli_overrides=overrides).for_subchapter(args.subchapter)
    authorization = authorize_google_drive(config)
    drive = DriveRestClient(authorization.session, config.drive_api_timeout_seconds)
    if args.drive_file_id:
        item = drive.get_item(args.drive_file_id)
        source = ResolvedDriveSource(
            file_id=item.file_id,
            filename=item.name,
            relative_path=f"{args.subchapter}/source.pdf",
            mime_type=item.mime_type,
            size_bytes=item.size_bytes,
            md5_checksum=item.md5_checksum,
            subchapter_id=args.subchapter,
            modified_time=item.modified_time,
            version=item.version,
        )
    else:
        source = resolve_drive_source(
            drive,
            sourcepath=config.sourcepath,
            pdf_subchapter_path=args.subchapter,
            target_filename=config.target_filename,
            max_folders=config.max_drive_folders,
        )

    smoke_root = config.state_dir.parent / "gemini-api-smoke" / args.subchapter
    smoke_root.mkdir(parents=True, exist_ok=True)
    pdf_path = drive.download_file(source, smoke_root / source.filename)
    try:
        api = GeminiApiClient(config, (pdf_path,))
        api.prepare()
        run_metadata = {
            "packageId": config.package_id,
            "chapter": config.chapter,
            "subchapterId": config.pdf_subchapter_path,
            "learningBoundary": config.learning_boundary,
            "sourceFilenames": [source.filename],
            "pageRange": config.page_range,
            "attachmentMode": "gemini-api-files",
        }
        response = api.ask(source_analysis_prompt(run_metadata), stage="source-analysis")
        parsed = parse_json_response(response)
        result_path = smoke_root / "source-analysis.json"
        result_path.write_text(json.dumps(parsed, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"GEMINI_API_SMOKE=PASS model={api.actual_model}")
        print(f"SECTION_TITLE={parsed.get('sectionTitle', '')}")
        print(f"OBJECTIVES={len(parsed.get('learningObjectives', []))}")
        print(f"PROMPT_SHA256={api.prompt_sha256}")
        print(f"RESULT_FILE={result_path}")
        return 0
    finally:
        try:
            pdf_path.unlink()
        except FileNotFoundError:
            pass


if __name__ == "__main__":
    raise SystemExit(main())

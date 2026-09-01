"""PowerShell-friendly command-line interface."""

from __future__ import annotations

import argparse
import shutil
import sys
import tempfile
from pathlib import Path

from app_generator.config import GeneratorConfig, load_config
from app_generator.coordinator.client import CoordinatorClient
from app_generator.coordinator.managed import (
    bootstrap_managed_coordinator,
    ensure_managed_coordinator,
    managed_status,
)
from app_generator.errors import GeneratorError, NoAvailableJob
from app_generator.prompts import gem_description, gem_instructions
from app_generator.runtime.orchestrator import run_generation
from app_generator.runtime.auto import inspect_auto_queue, run_continuous_auto
from app_generator.sources.google_drive import (
    DriveRestClient,
    discover_drive_sources,
    resolve_drive_source,
)
from app_generator.sources.google_drive_auth import authorize_google_drive
from app_generator.sources.local_sources import inspect_sources
from app_generator.sources.manifest import build_manifest, load_existing_manifest
from app_generator.validation.schema_validation import validate_manifest


DEFAULT_CONFIG = Path("project.local.toml")


def _add_config_arguments(command: argparse.ArgumentParser) -> None:
    command.add_argument(
        "--config",
        type=Path,
        default=DEFAULT_CONFIG,
        help="configuration file (default: .\\project.local.toml)",
    )
    command.add_argument("--repo-root", type=Path)
    command.add_argument("--gem-url")
    command.add_argument("--gem-edit-url")
    command.add_argument("--login-name")
    command.add_argument("--chrome-profile-dir", type=Path)
    command.add_argument("--sourcepath")
    command.add_argument("--pdf-subchapter-path")
    command.add_argument("--drive-oauth-client-file", type=Path)
    command.add_argument("--selection-mode", choices=("specific", "auto", "distributed"))


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="learning-app-content-generator")
    subparsers = parser.add_subparsers(dest="command", required=True)
    for name in ("doctor", "run"):
        command = subparsers.add_parser(name)
        _add_config_arguments(command)
        if name == "run":
            command.add_argument("--resume", metavar="RUN_ID")
    complete = subparsers.add_parser("coordinator-complete")
    _add_config_arguments(complete)
    complete.add_argument("--job-key", required=True)
    complete.add_argument("--pr-url", default="")
    for name in ("coordinator-bootstrap", "coordinator-ensure", "coordinator-status"):
        command = subparsers.add_parser(name)
        _add_config_arguments(command)
    subparsers.add_parser("show-gem-config")
    return parser


def _load(args: argparse.Namespace) -> GeneratorConfig:
    overrides = {
        "repo_root": getattr(args, "repo_root", None),
        "gem_url": getattr(args, "gem_url", None),
        "gem_edit_url": getattr(args, "gem_edit_url", None),
        "login_name": getattr(args, "login_name", None),
        "chrome_profile_dir": getattr(args, "chrome_profile_dir", None),
        "sourcepath": getattr(args, "sourcepath", None),
        "pdf_subchapter_path": getattr(args, "pdf_subchapter_path", None),
        "drive_oauth_client_file": getattr(args, "drive_oauth_client_file", None),
        "selection_mode": getattr(args, "selection_mode", None),
    }
    return load_config(args.config, cli_overrides=overrides)


def doctor(config: GeneratorConfig) -> int:
    if config.selection_mode == "auto":
        snapshot = inspect_auto_queue(config)
        print(
            "Auto queue: "
            f"total={snapshot.total}, generated={snapshot.generated}, review_pending={snapshot.review_pending}, "
            f"completed={snapshot.completed}, interrupted={snapshot.interrupted}, fresh={snapshot.queued}, "
            f"leased={snapshot.leased}, failed={snapshot.failed}"
        )
        if snapshot.next_subchapter_id:
            print(f"Next non-claiming candidate preview: {snapshot.next_subchapter_id}")
        elif snapshot.leased:
            print("No job is currently claimable; remaining work is leased by another worker.")
        elif snapshot.failed:
            print("No job is currently claimable; terminal failures require intervention.")
        else:
            print("No job is currently claimable; all discovered sources are globally successful.")
        print("Auto doctor does not claim a generation job or exercise the Gemini UI.")
        return 0

    drive_source = None
    effective_config = config
    with tempfile.TemporaryDirectory(prefix="content-generator-doctor-") as directory:
        if config.uses_google_drive:
            authorization = authorize_google_drive(config)
            drive_client = DriveRestClient(authorization.session, config.drive_api_timeout_seconds)
            if config.selection_mode == "distributed":
                config = ensure_managed_coordinator(config)
                CoordinatorClient(config).health()
                inventory = discover_drive_sources(
                    drive_client,
                    sourcepath=config.sourcepath,
                    target_filename=config.target_filename,
                    max_folders=config.max_drive_folders,
                )
                eligible = tuple(
                    source for source in inventory
                    if not config.for_subchapter(source.subchapter_id).package_path.exists()
                )
                if not eligible:
                    raise NoAvailableJob("No unprocessed Drive source remains in the local main-branch view")
                drive_source = eligible[0]
                print(f"Discovered source jobs: {len(inventory)} total, {len(eligible)} absent from this checkout")
            else:
                drive_source = resolve_drive_source(
                    drive_client,
                    sourcepath=config.sourcepath,
                    pdf_subchapter_path=config.pdf_subchapter_path,
                    target_filename=config.target_filename,
                    max_folders=config.max_drive_folders,
                )
            effective_config = config.for_subchapter(drive_source.subchapter_id)
            local_path = drive_client.download_file(drive_source, Path(directory) / drive_source.filename)
            sources = inspect_sources((local_path,))
            print(f"Google Drive account: {authorization.email}")
            print(f"Source root: {config.sourcepath}")
            print(f"Target locator: {config.target_locator}")
            print(f"Examined target: {drive_source.relative_path}")
            print(f"Drive file ID: {drive_source.file_id}")
        else:
            effective_config = config.for_subchapter(config.pdf_subchapter_path.split("/")[-1])
            sources = inspect_sources(config.source_files)
        manifest = (
            load_existing_manifest(effective_config.existing_source_manifest, sources[0], effective_config)
            if effective_config.existing_source_manifest
            else build_manifest(
                effective_config,
                sources,
                drive_file_id=drive_source.file_id if drive_source else None,
            )
        )
        manifest_errors = validate_manifest(effective_config.repo_root, manifest)
        if manifest_errors:
            print("Manifest validation failed:")
            for error in manifest_errors:
                print(f"- {error}")
            return 1
        source_summary = f"{sources[0].controlled_filename} sha256={sources[0].sha256}"
    chrome = shutil.which("chrome") or shutil.which("chrome.exe") or shutil.which("google-chrome")
    print(f"Repository: {effective_config.repo_root}")
    print(f"Output: {effective_config.package_path}")
    print(f"Source: {source_summary}")
    print(f"Chrome on PATH: {chrome or 'not found (Selenium Manager may still locate installed Chrome)'}")
    scope = "Drive, coordinator, and deterministic provenance" if config.selection_mode == "distributed" else "Drive and deterministic provenance"
    print(f"Configuration, {scope} checks passed. Gemini UI was not exercised.")
    return 0


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.command == "show-gem-config":
        print("Gem Description\n===============\n" + gem_description())
        print("\nGem Instructions\n================\n" + gem_instructions())
        return 0
    try:
        config = _load(args)
        if args.command == "coordinator-status":
            print(f"Managed coordinator: {managed_status(config)}")
            return 0
        if args.command == "coordinator-bootstrap":
            ready = bootstrap_managed_coordinator(config)
            print(f"Managed coordinator bootstrap completed: {ready.coordinator_url}")
            return 0
        if args.command == "coordinator-ensure":
            ready = ensure_managed_coordinator(config)
            print(f"Managed coordinator ready: {ready.coordinator_url}")
            return 0
        if args.command == "doctor":
            return doctor(config)
        if args.command == "coordinator-complete":
            config = ensure_managed_coordinator(config)
            CoordinatorClient(config).mark_completed(args.job_key, pr_url=args.pr_url)
            print(f"Coordinator job {args.job_key} marked completed.")
            return 0
        def report_context(context):
            print(f"Run {context.run_id} completed.")
            for path in context.store.state.installed_paths:
                print(f"Generated: {path}")
            if context.store.state.pr_url:
                print(f"Draft pull request: {context.store.state.pr_url}")
            print("Status: structurally validated draft awaiting qualified content review; not approved for publication.")

        if config.selection_mode == "auto":
            if args.resume:
                raise GeneratorError("--resume is not supported with continuous auto mode")
            return run_continuous_auto(config, on_completed=report_context)
        if config.selection_mode == "distributed":
            config = ensure_managed_coordinator(config)

        context = run_generation(config, resume_run_id=args.resume)
        report_context(context)
        return 0
    except KeyboardInterrupt:
        print("AUTO_INTERRUPTED: worker stopped by user; any active auto lease was returned to the coordinator.", file=sys.stderr)
        return 130
    except GeneratorError as exc:
        print(f"{exc.code}: {exc}", file=sys.stderr)
        if exc.detail:
            print(exc.detail, file=sys.stderr)
        return 2
    except Exception as exc:
        print(f"UNEXPECTED_ERROR: {exc}", file=sys.stderr)
        return 3


if __name__ == "__main__":
    raise SystemExit(main())

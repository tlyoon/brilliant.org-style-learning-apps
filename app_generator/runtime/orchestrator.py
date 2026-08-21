"""End-to-end one-PDF generation with optional distributed job leasing."""

from __future__ import annotations

import hashlib
import json
import logging
from contextlib import nullcontext
from copy import deepcopy
from pathlib import Path
from typing import Callable

from app_generator.browser.chrome import ChromeSession
from app_generator.config import GeneratorConfig
from app_generator.coordinator.client import CoordinatorClient, JobLease
from app_generator.coordinator.heartbeat import LeaseGuard
from app_generator.errors import NoAvailableJob, RepairLimitExceeded, SourceSetMismatch, ValidationFailure
from app_generator.filesystem.outputs import Artifact, install_new_artifacts, stage_artifacts, write_json_atomic
from app_generator.gemini.client import GeminiClient
from app_generator.generation.documents import render_learning_design, render_review_record, render_section_readme
from app_generator.generation.protocol import GenerationProtocol
from app_generator.locking import WorkerLock
from app_generator.logging_setup import configure_logging
from app_generator.publishing.git import GitPublisher
from app_generator.runtime.run_context import RunContext
from app_generator.runtime.state import RunPhase
from app_generator.sources.google_drive import (
    DriveRestClient,
    ResolvedDriveSource,
    discover_drive_sources,
    resolve_drive_source,
)
from app_generator.sources.google_drive_auth import DriveAuthorization, authorize_google_drive
from app_generator.sources.local_sources import inspect_sources
from app_generator.sources.manifest import build_manifest, load_existing_manifest
from app_generator.validation.repository_checks import run_repository_validator, validate_candidate
from app_generator.validation.schema_validation import validate_manifest, validate_schemas

LOGGER = logging.getLogger("app_generator.orchestrator")


def _remove_temporary_source(path: Path | None, source_root: Path) -> None:
    if path is None:
        return
    try:
        path.resolve().relative_to(source_root.resolve())
    except ValueError as exc:
        raise RuntimeError(f"Refusing to remove a source outside the controlled run directory: {path}") from exc
    try:
        path.unlink()
    except FileNotFoundError:
        pass


def _relative_paths(config: GeneratorConfig) -> tuple[Path, ...]:
    section = Path("content") / config.chapter_dir / config.section_dir
    return (
        section / "README.md",
        section / "learning-design.md",
        section / "package.json",
        section / "review-record.md",
        config.manifest_relative_path,
    )


def _stage_complete_artifacts(
    context: RunContext,
    config: GeneratorConfig,
    package: dict,
    manifest: dict,
) -> Path:
    package_relative = Path("content") / config.chapter_dir / config.section_dir / "package.json"
    artifacts = (
        Artifact(package_relative.parent / "README.md", render_section_readme(config)),
        Artifact(package_relative.parent / "learning-design.md", render_learning_design(config, package)),
        Artifact(package_relative, json.dumps(package, indent=2, ensure_ascii=False) + "\n"),
        Artifact(package_relative.parent / "review-record.md", render_review_record(config)),
        Artifact(config.manifest_relative_path, json.dumps(manifest, indent=2, ensure_ascii=False) + "\n"),
    )
    stage_artifacts(context.candidate, artifacts)
    return package_relative


def _candidate_errors(
    config: GeneratorConfig,
    context: RunContext,
    package: dict,
    manifest: dict,
    package_relative: Path,
) -> list[str]:
    errors = validate_schemas(config.repo_root, package, manifest)
    if errors:
        return errors
    write_json_atomic(context.candidate / package_relative, package)
    errors.extend(validate_candidate(config.repo_root, context.candidate, package_relative))
    review_candidate = deepcopy(package)
    review_candidate["status"] = "review"
    write_json_atomic(context.candidate / package_relative, review_candidate)
    errors.extend(validate_candidate(config.repo_root, context.candidate, package_relative))
    write_json_atomic(context.candidate / package_relative, package)
    return errors


def _unprocessed_sources(
    config: GeneratorConfig,
    sources: tuple[ResolvedDriveSource, ...],
) -> tuple[ResolvedDriveSource, ...]:
    eligible: list[ResolvedDriveSource] = []
    for source in sources:
        materialized = config.for_subchapter(source.subchapter_id)
        if not materialized.package_path.exists():
            eligible.append(source)
    return tuple(eligible)


def _local_job_key(config: GeneratorConfig, source_path: Path) -> str:
    material = f"{config.package_id}:{source_path.resolve()}".encode("utf-8")
    return hashlib.sha256(material).hexdigest()


def run_generation(
    config: GeneratorConfig,
    *,
    resume_run_id: str | None = None,
    chrome_factory: Callable[[GeneratorConfig], ChromeSession] = ChromeSession,
    client_factory: Callable[[object, GeneratorConfig], GeminiClient] = GeminiClient,
    drive_authorizer: Callable[[GeneratorConfig], DriveAuthorization] = authorize_google_drive,
    drive_client_factory: Callable[[object, int], DriveRestClient] = DriveRestClient,
    coordinator_factory: Callable[[GeneratorConfig], CoordinatorClient] = CoordinatorClient,
    publisher_factory: Callable[[GeneratorConfig], GitPublisher] = GitPublisher,
) -> RunContext:
    if resume_run_id and (config.selection_mode == "distributed" or config.git_publish):
        raise ValidationFailure(
            "Automatic resume is disabled for leased or Git-published runs",
            ["Inspect the recorded job branch and coordinator row, then retry or release it deliberately."],
        )
    context = RunContext.create(config.state_dir, resume_run_id)
    configure_logging(context.logs / "run.jsonl", config.log_level)
    store = context.store
    original_source_metadata = list(store.state.source_metadata)
    if resume_run_id:
        store.resume()
    else:
        store.transition(RunPhase.CONFIG_LOADED)

    with WorkerLock(config.state_dir, config.gem_url):
        store.transition(RunPhase.WORKER_LOCK_ACQUIRED)
        temporary_source: Path | None = None
        browser: ChromeSession | None = None
        coordinator: CoordinatorClient | None = None
        lease: JobLease | None = None
        lease_guard: LeaseGuard | None = None
        active_config = config
        branch = ""
        try:
            if config.git_publish:
                publisher_factory(config).sync_base()
            drive_source: ResolvedDriveSource | None = None
            drive_client: DriveRestClient | None = None
            if config.uses_google_drive:
                authorization = drive_authorizer(config)
                store.transition(RunPhase.DRIVE_AUTHENTICATED)
                drive_client = drive_client_factory(authorization.session, config.drive_api_timeout_seconds)
                if config.selection_mode == "distributed":
                    inventory = discover_drive_sources(
                        drive_client,
                        sourcepath=config.sourcepath,
                        target_filename=config.target_filename,
                        max_folders=config.max_drive_folders,
                    )
                    inventory = _unprocessed_sources(config, inventory)
                    store.transition(RunPhase.DRIVE_INVENTORIED)
                    coordinator = coordinator_factory(config)
                    lease = coordinator.claim(inventory)
                    drive_source = next(
                        (source for source in inventory if source.file_id == lease.drive_file_id),
                        None,
                    )
                    if drive_source is None or drive_source.job_key != lease.job_key:
                        raise SourceSetMismatch("Coordinator returned a source outside the current Drive inventory")
                    active_config = config.for_subchapter(drive_source.subchapter_id)
                    store.transition(
                        RunPhase.JOB_LEASED,
                        job_key=lease.job_key,
                        worker_id=lease.worker_id,
                        lease_expires_at=lease.lease_expires_at,
                    )
                    lease_guard = LeaseGuard(
                        coordinator,
                        lease,
                        config.heartbeat_seconds,
                        config.lease_seconds,
                    )
                else:
                    drive_source = resolve_drive_source(
                        drive_client,
                        sourcepath=config.sourcepath,
                        pdf_subchapter_path=config.pdf_subchapter_path,
                        target_filename=config.target_filename,
                        max_folders=config.max_drive_folders,
                    )
                    active_config = config.for_subchapter(drive_source.subchapter_id)
                store.transition(RunPhase.SOURCE_RESOLVED, source_locator=drive_source.metadata())
            else:
                subchapter_id = config.pdf_subchapter_path.replace("\\", "/").split("/")[-1]
                active_config = config.for_subchapter(subchapter_id)

            guard_context = lease_guard if lease_guard is not None else nullcontext()
            with guard_context:
                if drive_source is not None:
                    assert drive_client is not None
                    temporary_source = drive_client.download_file(
                        drive_source,
                        context.sources / drive_source.filename,
                    )
                    store.transition(RunPhase.SOURCE_DOWNLOADED)
                    sources = inspect_sources((temporary_source,))
                    job_key = drive_source.job_key
                else:
                    sources = inspect_sources(active_config.source_files)
                    job_key = _local_job_key(active_config, sources[0].path)

                current_source_metadata = [source.metadata() for source in sources]
                if resume_run_id and original_source_metadata and current_source_metadata != original_source_metadata:
                    raise SourceSetMismatch("The source bytes or metadata changed since the failed run; resume stopped safely")
                store.update(source_metadata=current_source_metadata)

                publisher = publisher_factory(active_config) if active_config.git_publish else None
                if publisher is not None:
                    if lease_guard is not None:
                        lease_guard.ensure_owned()
                    branch = publisher.prepare_branch(
                        subchapter_id=active_config.pdf_subchapter_path,
                        job_key=job_key,
                    )
                    store.transition(RunPhase.GIT_BRANCH_PREPARED, branch=branch)

                manifest = (
                    load_existing_manifest(active_config.existing_source_manifest, sources[0], active_config)
                    if active_config.existing_source_manifest
                    else build_manifest(
                        active_config,
                        sources,
                        drive_file_id=drive_source.file_id if drive_source else None,
                    )
                )
                manifest_errors = validate_manifest(active_config.repo_root, manifest)
                if manifest_errors:
                    raise ValidationFailure(
                        "Source manifest is incompatible with the current repository schema",
                        manifest_errors,
                    )
                store.transition(RunPhase.SOURCE_MANIFEST_READY)

                browser = chrome_factory(active_config)
                driver = browser.start()
                store.transition(RunPhase.CHROME_STARTED)
                client = client_factory(driver, active_config)
                client.open_editor_and_verify_account()
                store.transition(RunPhase.GOOGLE_ACCOUNT_VERIFIED)
                client.configure_gem()
                store.transition(RunPhase.GEM_CONFIG_CHECKED)
                client.open_conversation_select_model_and_attach(sources[0].path)
                store.transition(RunPhase.MODEL_SELECTED, actual_model=client.actual_model)
                store.transition(RunPhase.SOURCE_ATTACHED)
                if temporary_source is not None:
                    _remove_temporary_source(temporary_source, context.sources)
                    temporary_source = None
                    store.transition(RunPhase.TEMPORARY_SOURCE_REMOVED)

                protocol = GenerationProtocol(client, context)
                store.transition(RunPhase.GENERATING)
                run_metadata = {
                    "packageId": active_config.package_id,
                    "chapter": active_config.chapter,
                    "subchapter": active_config.subchapter,
                    "learningBoundary": active_config.learning_boundary,
                    "sourceFilenames": [source.controlled_filename for source in sources],
                    "heading": active_config.heading,
                    "pageRange": active_config.page_range,
                    "attachmentMode": "fresh-conversation",
                }
                source_location = f"{active_config.heading}; {active_config.page_range}"
                package, _, _ = protocol.generate(
                    config=active_config,
                    run_metadata=run_metadata,
                    source_location=source_location,
                )
                store.transition(RunPhase.PACKAGE_ASSEMBLED, actual_model=client.actual_model)
                package_relative = _stage_complete_artifacts(context, active_config, package, manifest)

                for attempt in range(active_config.max_repair_attempts + 1):
                    if lease_guard is not None:
                        lease_guard.ensure_owned()
                    store.transition(RunPhase.VALIDATING)
                    errors = _candidate_errors(active_config, context, package, manifest, package_relative)
                    write_json_atomic(context.validation / f"validation-{attempt:02d}.json", {"errors": errors})
                    if not errors:
                        break
                    if attempt >= active_config.max_repair_attempts:
                        raise RepairLimitExceeded("The package did not converge within the configured repair limit")
                    repairable = any("activity[" in error for error in errors)
                    if not repairable:
                        raise ValidationFailure("Non-activity validation errors require deterministic correction", errors)
                    store.transition(RunPhase.REPAIRING)
                    package = protocol.repair_validation_errors(package, errors, attempt + 1)
                    _stage_complete_artifacts(context, active_config, package, manifest)
                store.transition(RunPhase.CONTENT_VALIDATED)

                package, findings = protocol.audit_and_repair(package)
                write_json_atomic(context.validation / "semantic-findings.json", {"findings": findings})
                _stage_complete_artifacts(context, active_config, package, manifest)
                final_errors = _candidate_errors(active_config, context, package, manifest, package_relative)
                if final_errors:
                    raise ValidationFailure("Semantic repair introduced deterministic validation failures", final_errors)
                store.transition(RunPhase.SEMANTIC_REVIEW_COMPLETED, actual_model=client.actual_model)

                installed = install_new_artifacts(
                    active_config.repo_root,
                    context.candidate,
                    _relative_paths(active_config),
                    verify=lambda: run_repository_validator(active_config.repo_root),
                )
                store.transition(RunPhase.FINAL_PACKAGE_WRITTEN, installed_paths=[str(path) for path in installed])
                json.loads(active_config.package_path.read_text(encoding="utf-8"))
                run_repository_validator(active_config.repo_root)
                store.transition(RunPhase.FINAL_PACKAGE_REVERIFIED)

                if publisher is not None:
                    ensure_lease = lease_guard.ensure_owned if lease_guard is not None else (lambda: None)
                    published = publisher.publish(
                        branch=branch,
                        installed_paths=installed,
                        subchapter=active_config.subchapter,
                        package_id=active_config.package_id,
                        ensure_lease=ensure_lease,
                    )
                    store.transition(
                        RunPhase.GIT_PUBLISHED,
                        branch=published.branch,
                        commit=published.commit,
                        pr_url=published.pr_url,
                    )
                if coordinator is not None and lease is not None:
                    assert lease_guard is not None
                    lease_guard.ensure_owned()
                    coordinator.mark_review_pending(
                        lease_guard.lease,
                        branch=store.state.branch or "",
                        pr_url=store.state.pr_url or "",
                    )
                    store.transition(RunPhase.REVIEW_PENDING)
                store.transition(RunPhase.COMPLETE)
                return context
        except BaseException as exc:
            LOGGER.exception(
                "Generation run failed",
                extra={"run_id": context.run_id, "error_code": getattr(exc, "code", exc.__class__.__name__)},
            )
            if coordinator is not None and lease is not None:
                try:
                    coordinator.mark_failed(
                        lease_guard.lease if lease_guard is not None else lease,
                        error_code=str(getattr(exc, "code", exc.__class__.__name__)),
                        error_message=str(exc),
                    )
                except BaseException:
                    LOGGER.exception("Could not return the failed job to the coordinator")
            store.fail(exc)
            raise
        finally:
            _remove_temporary_source(temporary_source, context.sources)
            if browser is not None:
                browser.close()

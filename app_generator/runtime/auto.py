"""Continuous multi-PC automatic job selection and recovery."""

from __future__ import annotations

import time
from collections.abc import Callable
from pathlib import Path

from app_generator.config import GeneratorConfig
from app_generator.coordinator.client import CoordinatorClient, JobLease, QueueSnapshot
from app_generator.coordinator.verified import ensure_coordinator_ready
from app_generator.errors import AutoJobExecutionError, AutoModeBlockedError, NoAvailableJob
from app_generator.publishing.git import GitPublisher
from app_generator.runtime.orchestrator import run_generation
from app_generator.runtime.run_context import RunContext
from app_generator.sources.google_drive import DriveRestClient, ResolvedDriveSource, discover_drive_sources
from app_generator.sources.google_drive_auth import authorize_google_drive


def _require_durable_publication(config: GeneratorConfig) -> None:
    """Require every successful auto job to have a shared Git handoff."""

    if not config.git_publish:
        raise AutoModeBlockedError(
            "Continuous auto mode requires git_publish=true so every successful job is "
            "durably handed off through Git before the coordinator marks it generated."
        )


def _expected_paths(config: GeneratorConfig) -> tuple[Path, ...]:
    section = Path("content") / config.chapter_dir / config.section_dir
    return (
        section / "README.md",
        section / "learning-design.md",
        section / "package.json",
        section / "review-record.md",
        config.manifest_relative_path,
    )


def _drive_inventory(config: GeneratorConfig) -> tuple[ResolvedDriveSource, ...]:
    authorization = authorize_google_drive(config)
    drive_client = DriveRestClient(authorization.session, config.drive_api_timeout_seconds)
    return discover_drive_sources(
        drive_client,
        sourcepath=config.sourcepath,
        target_filename=config.target_filename,
        max_folders=config.max_drive_folders,
    )


def _base_completed(config: GeneratorConfig, inventory: tuple[ResolvedDriveSource, ...]) -> set[str]:
    """Identify content present in the freshly synchronized durable Git base."""

    return {
        source.job_key
        for source in inventory
        if config.for_subchapter(source.subchapter_id).package_path.exists()
    }


def inspect_auto_queue(config: GeneratorConfig) -> QueueSnapshot:
    """Inspect auto state without claiming a generation or recovery lease."""

    _require_durable_publication(config)
    config = ensure_coordinator_ready(config)
    publisher = GitPublisher(config)
    publisher.sync_base()
    inventory = _drive_inventory(config)
    local_completed = _base_completed(config, inventory)
    coordinator = CoordinatorClient(config)
    return coordinator.snapshot_auto(inventory, local_completed_job_keys=local_completed)


def reconcile_auto_publications(config: GeneratorConfig) -> int:
    """Recover exact deterministic Git handoffs left by an interrupted worker.

    Reconciliation claims the exact source job before changing coordinator state. This
    preserves the same lease boundary as normal generation: two PCs may discover the
    same recoverable branch, but only one can finalize it. No Gemini session is opened.
    """

    _require_durable_publication(config)
    config = ensure_coordinator_ready(config)
    publisher = GitPublisher(config)
    publisher.sync_base()
    inventory = _drive_inventory(config)
    local_completed = _base_completed(config, inventory)
    coordinator = CoordinatorClient(config)
    # Seed rows, reconcile expired leases, and mark only content visible in the freshly
    # synchronized Git base as already generated.
    coordinator.snapshot_auto(inventory, local_completed_job_keys=local_completed)

    recovered = 0
    for source in inventory:
        if source.job_key in local_completed:
            continue
        if not publisher.has_recoverable_handoff(
            subchapter_id=source.subchapter_id,
            job_key=source.job_key,
        ):
            continue
        try:
            lease = coordinator.claim_auto((source,), local_completed_job_keys=set())
        except NoAvailableJob:
            # Already successful or currently leased to another worker.
            continue

        current_lease: list[JobLease] = [lease]

        def ensure_lease() -> None:
            current_lease[0] = coordinator.heartbeat(current_lease[0])

        active_config = config.for_subchapter(source.subchapter_id)
        try:
            result = publisher.recover_handoff(
                subchapter_id=source.subchapter_id,
                job_key=source.job_key,
                expected_paths=_expected_paths(active_config),
                subchapter=active_config.subchapter,
                package_id=active_config.package_id,
                ensure_lease=ensure_lease,
            )
            if result is None:
                coordinator.mark_failed(
                    current_lease[0],
                    error_code="GIT_HANDOFF_DISAPPEARED",
                    error_message="A recoverable Git handoff disappeared before it could be finalized",
                )
                continue
            ensure_lease()
            coordinator.checkpoint_clear(current_lease[0])
            coordinator.mark_generated(
                current_lease[0],
                branch=result.branch,
                pr_url=result.pr_url,
            )
            recovered += 1
            print(
                f"AUTO_RECOVERED: section {source.subchapter_id} reused durable Git handoff "
                f"{result.branch}; Gemini generation was skipped."
            )
        except BaseException as exc:
            try:
                coordinator.mark_failed(
                    current_lease[0],
                    error_code=str(getattr(exc, "code", exc.__class__.__name__)),
                    error_message=str(exc),
                )
            except BaseException:
                pass
            raise

    # A local committed recovery may have switched to its job branch, and auto-merge may
    # have advanced the remote base. Leave the worker on a clean current base.
    publisher.sync_base()
    return recovered


def run_continuous_auto(
    config: GeneratorConfig,
    *,
    on_completed: Callable[[RunContext], None] | None = None,
    run_once: Callable[[GeneratorConfig], RunContext] = run_generation,
    snapshotter: Callable[[GeneratorConfig], QueueSnapshot] = inspect_auto_queue,
    reconciler: Callable[[GeneratorConfig], int] = reconcile_auto_publications,
    sleeper: Callable[[float], None] = time.sleep,
) -> int:
    """Run coordinated jobs until every discovered source has a successful global state."""

    _require_durable_publication(config)
    config = ensure_coordinator_ready(config)
    poll_seconds = max(5, min(60, config.heartbeat_seconds // 10 or 5))
    print(
        f"AUTO_START: worker={config.worker_id}; persistent continuous mode is active. "
        "Press Ctrl+C for a coordinated stop."
    )
    reconciler(config)
    while True:
        try:
            context = run_once(config)
            if on_completed is not None:
                on_completed(context)
            continue
        except AutoJobExecutionError as exc:
            print(
                f"AUTO_JOB_{exc.status.upper()}: {exc}. "
                "The worker will reconcile durable Git handoffs and re-inspect the shared queue."
            )
            reconciler(config)
            continue
        except NoAvailableJob:
            snapshot = snapshotter(config)
            if snapshot.failed and snapshot.unfinished == 0:
                raise AutoModeBlockedError(
                    f"Auto mode is blocked by {snapshot.failed} terminally failed job(s); "
                    "all remaining discovered jobs require intervention."
                )
            if snapshot.unfinished == 0:
                print(
                    f"AUTO_COMPLETE: all {snapshot.total} discovered source job(s) are globally successful."
                )
                return 0
            if snapshot.leased and snapshot.queued + snapshot.interrupted == 0:
                print(
                    f"AUTO_IDLE: {snapshot.leased} remaining job(s) are leased by other workers; "
                    f"checking again in {poll_seconds}s."
                )
                sleeper(float(poll_seconds))
                continue
            # A queue snapshot can race with another worker's claim/release. Re-enter
            # claim immediately whenever globally runnable work exists.
            continue

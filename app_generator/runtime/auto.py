"""Continuous multi-PC automatic job selection and recovery."""

from __future__ import annotations

import time
from collections.abc import Callable

from app_generator.config import GeneratorConfig
from app_generator.coordinator.client import CoordinatorClient, QueueSnapshot
from app_generator.errors import AutoJobExecutionError, AutoModeBlockedError, NoAvailableJob
from app_generator.runtime.orchestrator import run_generation
from app_generator.runtime.run_context import RunContext
from app_generator.sources.google_drive import DriveRestClient, discover_drive_sources
from app_generator.sources.google_drive_auth import authorize_google_drive


def _require_durable_publication(config: GeneratorConfig) -> None:
    """Require every successful auto job to have a shared Git handoff.

    Auto workers coordinate globally. Marking a job generated when its artifacts exist
    only in one worker's checkout would make that local filesystem an accidental source
    of truth and could cause every other worker to skip content it cannot retrieve.
    Requiring Git publication keeps the coordinator's generated state aligned with a
    durable remote branch/PR (or merged result).
    """

    if not config.git_publish:
        raise AutoModeBlockedError(
            "Continuous auto mode requires git_publish=true so every successful job is "
            "durably handed off through Git before the coordinator marks it generated."
        )


def inspect_auto_queue(config: GeneratorConfig) -> QueueSnapshot:
    _require_durable_publication(config)
    authorization = authorize_google_drive(config)
    drive_client = DriveRestClient(authorization.session, config.drive_api_timeout_seconds)
    inventory = discover_drive_sources(
        drive_client,
        sourcepath=config.sourcepath,
        target_filename=config.target_filename,
        max_folders=config.max_drive_folders,
    )
    local_completed = {
        source.job_key
        for source in inventory
        if config.for_subchapter(source.subchapter_id).package_path.exists()
    }
    coordinator = CoordinatorClient(config)
    coordinator.health(require_checkpoints=True)
    return coordinator.snapshot_auto(inventory, local_completed_job_keys=local_completed)


def run_continuous_auto(
    config: GeneratorConfig,
    *,
    on_completed: Callable[[RunContext], None] | None = None,
    run_once: Callable[[GeneratorConfig], RunContext] = run_generation,
    snapshotter: Callable[[GeneratorConfig], QueueSnapshot] = inspect_auto_queue,
    sleeper: Callable[[float], None] = time.sleep,
) -> int:
    """Run coordinated jobs until every discovered source has a successful global state.

    Every successful job must first be published through Git so the coordinator's
    generated state never depends on one worker's local checkout. Recoverable/terminal
    per-job failures do not stop the worker immediately: the coordinator priority rules
    allow another interrupted job or a fresh job to run. The worker exits non-zero only
    when no runnable work remains and terminal failures still block global completion.
    """

    _require_durable_publication(config)
    poll_seconds = max(5, min(60, config.heartbeat_seconds // 10 or 5))
    while True:
        try:
            context = run_once(config)
            if on_completed is not None:
                on_completed(context)
            continue
        except AutoJobExecutionError as exc:
            print(
                f"AUTO_JOB_{exc.status.upper()}: {exc}. "
                "The worker will re-inspect the shared queue."
            )
            continue
        except NoAvailableJob:
            snapshot = snapshotter(config)
            if snapshot.failed and snapshot.unfinished == 0:
                raise AutoModeBlockedError(
                    f"Auto mode is blocked by {snapshot.failed} terminally failed job(s); "
                    "all remaining discovered jobs require intervention."
                )
            if snapshot.unfinished == 0:
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

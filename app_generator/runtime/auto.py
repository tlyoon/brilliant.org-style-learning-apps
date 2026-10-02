"""Continuous multi-PC automatic job selection and recovery."""

from __future__ import annotations

import time
from collections.abc import Callable
from pathlib import Path

from app_generator.config import GeneratorConfig
from app_generator.coordinator.client import JobLease, QueueSnapshot
from app_generator.coordinator.drive import DriveCoordinatorClient
from app_generator.errors import AutoJobExecutionError, AutoModeBlockedError, NoAvailableJob
from app_generator.publishing.git import GitPublisher
from app_generator.publishing.public import PublicPagesPublisher
from app_generator.deployments import has_current_public_deployment
from app_generator.runtime.orchestrator import run_generation
from app_generator.runtime.run_context import RunContext
from app_generator.runtime.watchdog import AutoAttemptSupervisor
from app_generator.runtime.targeting import restrict_auto_inventory
from app_generator.sources.google_drive import (
    DriveRestClient,
    ResolvedDriveSource,
    discover_drive_sources_with_corpus_keys,
    discover_drive_sources,
)
from app_generator.sources.google_drive_auth import authorize_google_drive


def _require_durable_publication(config: GeneratorConfig) -> None:
    """Require every successful auto job to have a shared Git handoff."""

    if not config.git_publish:
        raise AutoModeBlockedError(
            "Continuous auto mode requires git_publish=true so every successful job is "
            "durably handed off through Git before Drive coordination marks it generated."
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


def _drive_inventory(
    config: GeneratorConfig,
    *,
    target_subchapter_id: str | None = None,
    target_chapter: str | int | None = None,
) -> tuple[ResolvedDriveSource, ...]:
    authorization = authorize_google_drive(config)
    drive_client = DriveRestClient(authorization.session, config.drive_api_timeout_seconds)
    inventory = discover_drive_sources_with_corpus_keys(
        drive_client,
        sourcepath=config.sourcepath,
        target_filename=config.target_filename,
        max_folders=config.max_drive_folders,
    )
    return restrict_auto_inventory(
        inventory,
        target_subchapter_id=target_subchapter_id,
        target_chapter=target_chapter,
    )


def _base_completed(config: GeneratorConfig, inventory: tuple[ResolvedDriveSource, ...]) -> set[str]:
    """Identify content present in the freshly synchronized durable Git base."""

    return {
        source.job_key
        for source in inventory
        if config.for_subchapter(source.subchapter_id).package_path.exists()
        and (
            not getattr(config, "public_deploy", False)
            or has_current_public_deployment(
                config.repo_root, config.for_subchapter(source.subchapter_id)
            )
        )
    }


def inspect_auto_queue(
    config: GeneratorConfig,
    *,
    target_subchapter_id: str | None = None,
    target_chapter: str | int | None = None,
) -> QueueSnapshot:
    """Inspect auto state without claiming a generation or recovery lease."""

    _require_durable_publication(config)
    publisher = GitPublisher(config)
    publisher.sync_base()
    inventory = _drive_inventory(
        config,
        target_subchapter_id=target_subchapter_id,
        target_chapter=target_chapter,
    )
    local_completed = _base_completed(config, inventory)
    coordinator = DriveCoordinatorClient(config)
    return coordinator.snapshot_auto(inventory, local_completed_job_keys=local_completed)


def retry_failed_auto_job(config: GeneratorConfig, *, target_subchapter_id: str) -> tuple[str, int, str]:
    """Explicitly requeue one exact terminal target after operator intervention."""

    _require_durable_publication(config)
    publisher = GitPublisher(config)
    publisher.sync_base()
    inventory = _drive_inventory(
        config,
        target_subchapter_id=target_subchapter_id,
    )
    if len(inventory) != 1:
        raise AutoModeBlockedError(
            f"Target section {target_subchapter_id} did not resolve to exactly one Drive source job"
        )
    source = inventory[0]
    local_completed = _base_completed(config, inventory)
    coordinator = DriveCoordinatorClient(config)
    snapshot = coordinator.snapshot_auto(inventory, local_completed_job_keys=local_completed)
    if snapshot.failed != 1 or snapshot.total != 1:
        raise AutoModeBlockedError(
            f"Target section {target_subchapter_id} is not one terminally failed coordinator job"
        )
    result = coordinator.retry_failed(source)
    if result.status != "interrupted":
        raise AutoModeBlockedError(
            f"Drive coordination did not return target section {target_subchapter_id} to interrupted state"
        )
    return source.subchapter_id, result.previous_attempt_count, result.previous_error_code


def reconcile_auto_publications(
    config: GeneratorConfig,
    *,
    target_subchapter_id: str | None = None,
    target_chapter: str | int | None = None,
) -> int:
    """Recover exact deterministic Git handoffs left by an interrupted worker.

    Reconciliation claims the exact source job before changing coordinator state. This
    preserves the same lease boundary as normal generation: two PCs may discover the
    same recoverable branch, but only one can finalize it. No Gemini session is opened.
    """

    _require_durable_publication(config)
    publisher = GitPublisher(config)
    publisher.sync_base()
    inventory = _drive_inventory(
        config,
        target_subchapter_id=target_subchapter_id,
        target_chapter=target_chapter,
    )
    local_completed = _base_completed(config, inventory)
    coordinator = DriveCoordinatorClient(config)
    # Seed rows, reconcile expired leases, and mark only content visible in the freshly
    # synchronized Git base as already generated.
    coordinator.snapshot_auto(inventory, local_completed_job_keys=local_completed)

    recovered = 0
    for source in inventory:
        if source.job_key in local_completed:
            continue
        active_config = config.for_subchapter(source.subchapter_id)
        source_in_base = active_config.package_path.exists()
        if not source_in_base and not publisher.has_recoverable_handoff(
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

        try:
            result = None
            if not source_in_base:
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
                # Auto-merge may have advanced source main while this worker was
                # finishing the source PR; build the public release from durable main.
                publisher.sync_base()
            ensure_lease()
            if getattr(active_config, "public_deploy", False):
                public = PublicPagesPublisher(active_config).publish(
                    package_path=active_config.package_path,
                    subchapter_id=active_config.pdf_subchapter_path,
                    ensure_lease=ensure_lease,
                )
                if not public.merged:
                    raise AutoJobExecutionError(
                        "Public release PR did not merge",
                        status="interrupted",
                        original_code="PUBLIC_DEPLOY_NOT_MERGED",
                    )
                print(f"AUTO_PUBLIC_DEPLOYED: section {source.subchapter_id} {public.public_url}")
            ensure_lease()
            coordinator.checkpoint_clear(current_lease[0])
            coordinator.mark_generated(
                current_lease[0],
                branch=result.branch if result is not None else "source-main",
                pr_url=result.pr_url if result is not None else "",
                public_branch=public.branch if getattr(active_config, "public_deploy", False) else "",
                public_pr_url=public.pr_url if getattr(active_config, "public_deploy", False) else "",
                public_url=public.public_url if getattr(active_config, "public_deploy", False) else "",
                public_package_sha256=public.package_sha256 if getattr(active_config, "public_deploy", False) else "",
            )
            recovered += 1
            print(
                f"AUTO_RECOVERED: section {source.subchapter_id} reused durable Git handoff "
                f"{result.branch if result is not None else 'source-main'}; Gemini generation was skipped."
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
    target_subchapter_id: str | None = None,
    target_chapter: str | int | None = None,
    on_completed: Callable[[RunContext], None] | None = None,
    run_once: Callable[..., RunContext] = run_generation,
    snapshotter: Callable[..., QueueSnapshot] = inspect_auto_queue,
    reconciler: Callable[..., int] = reconcile_auto_publications,
    sleeper: Callable[[float], None] = time.sleep,
    supervisor_factory: Callable[[GeneratorConfig], AutoAttemptSupervisor] = AutoAttemptSupervisor,
) -> int:
    """Run coordinated jobs globally, or only one explicitly targeted subchapter."""

    _require_durable_publication(config)
    poll_seconds = max(5, min(60, config.heartbeat_seconds // 10 or 5))
    if target_subchapter_id and target_chapter is not None:
        raise AutoModeBlockedError("Auto mode cannot combine an exact subchapter target with a chapter scope")
    if target_subchapter_id:
        print(
            f"AUTO_TARGET_START: worker={config.worker_id}; target={target_subchapter_id}. "
            "Drive lease fencing remains active; this worker will not fall through to another section."
        )
    elif target_chapter is not None:
        print(
            f"AUTO_CHAPTER_START: worker={config.worker_id}; chapter={target_chapter}. "
            "Only sections in this chapter may be claimed; multi-PC lease fencing remains active."
        )
    else:
        print(
            f"AUTO_START: worker={config.worker_id}; persistent continuous mode is active. "
            "Press Ctrl+C for a coordinated stop."
        )
    if target_subchapter_id:
        reconciler(config, target_subchapter_id=target_subchapter_id)
    elif target_chapter is not None:
        reconciler(config, target_chapter=target_chapter)
    else:
        reconciler(config)
    while True:
        try:
            if run_once is run_generation:
                context = supervisor_factory(config).run(
                    target_subchapter_id,
                    target_chapter=target_chapter,
                )
            else:
                if target_subchapter_id:
                    context = run_once(
                        config, auto_target_subchapter_id=target_subchapter_id
                    )
                elif target_chapter is not None:
                    context = run_once(
                        config, auto_target_chapter=target_chapter
                    )
                else:
                    context = run_once(config)
            if on_completed is not None:
                on_completed(context)
            if target_subchapter_id:
                print(
                    f"AUTO_TARGET_COMPLETE: section {target_subchapter_id} is globally successful; "
                    "targeted auto mode is exiting."
                )
                return 0
            continue
        except AutoJobExecutionError as exc:
            print(
                f"AUTO_JOB_{exc.status.upper()}: {exc}. "
                "The worker will reconcile durable Git handoffs and re-inspect the shared queue."
            )
            if target_subchapter_id:
                reconciler(config, target_subchapter_id=target_subchapter_id)
            elif target_chapter is not None:
                reconciler(config, target_chapter=target_chapter)
            else:
                reconciler(config)
            continue
        except NoAvailableJob:
            if target_subchapter_id:
                snapshot = snapshotter(
                    config, target_subchapter_id=target_subchapter_id
                )
            elif target_chapter is not None:
                snapshot = snapshotter(config, target_chapter=target_chapter)
            else:
                snapshot = snapshotter(config)
            if snapshot.failed and snapshot.unfinished == 0:
                scope = (
                    f"Target section {target_subchapter_id}"
                    if target_subchapter_id
                    else (
                        f"Chapter {target_chapter} auto mode"
                        if target_chapter is not None
                        else "Auto mode"
                    )
                )
                raise AutoModeBlockedError(
                    f"{scope} is blocked by {snapshot.failed} terminally failed job(s); "
                    "intervention is required."
                )
            if snapshot.unfinished == 0:
                if target_subchapter_id:
                    print(
                        f"AUTO_TARGET_COMPLETE: section {target_subchapter_id} is already globally successful."
                    )
                elif target_chapter is not None:
                    print(
                        f"AUTO_CHAPTER_COMPLETE: all {snapshot.total} Chapter {target_chapter} source job(s) "
                        "are globally successful."
                    )
                else:
                    print(
                        f"AUTO_COMPLETE: all {snapshot.total} discovered source job(s) are globally successful."
                    )
                return 0
            if snapshot.leased and snapshot.queued + snapshot.interrupted == 0:
                if target_subchapter_id:
                    print(
                        f"AUTO_TARGET_WAIT: section {target_subchapter_id} is leased by another worker; "
                        f"checking again in {poll_seconds}s."
                    )
                elif target_chapter is not None:
                    print(
                        f"AUTO_CHAPTER_IDLE: {snapshot.leased} Chapter {target_chapter} job(s) are leased "
                        f"by other workers; checking again in {poll_seconds}s."
                    )
                else:
                    print(
                        f"AUTO_IDLE: {snapshot.leased} remaining job(s) are leased by other workers; "
                        f"checking again in {poll_seconds}s."
                    )
                sleeper(float(poll_seconds))
                continue
            # A queue snapshot can race with another worker's claim/release. Re-enter
            # claim immediately whenever globally runnable work exists.
            continue

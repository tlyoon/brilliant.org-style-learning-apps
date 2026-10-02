"""Supervision of one auto-generation child without killing the coordinator loop."""

from __future__ import annotations

import multiprocessing
import queue
import time
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app_generator.errors import AutoJobExecutionError, NoAvailableJob
from app_generator.runtime.orchestrator import run_generation


@dataclass(frozen=True)
class SupervisedRunResult:
    """Pickle-safe subset consumed by the CLI completion reporter."""

    run_id: str
    installed_paths: tuple[str, ...]
    pr_url: str | None

    @property
    def store(self) -> object:
        from types import SimpleNamespace
        return SimpleNamespace(state=SimpleNamespace(installed_paths=self.installed_paths, pr_url=self.pr_url))


def _child(config: object, target: str | None, target_chapter: str | int | None, result_queue: object) -> None:
    try:
        context = run_generation(
            config,
            auto_target_subchapter_id=target,
            auto_target_chapter=target_chapter,
        )
        state = context.store.state
        result_queue.put(("ok", SupervisedRunResult(
            context.run_id, tuple(state.installed_paths), state.pr_url,
        )))
    except NoAvailableJob as exc:
        result_queue.put(("no-job", str(exc)))
    except AutoJobExecutionError as exc:
        result_queue.put(("auto-error", str(exc), exc.status, exc.original_code))
    except BaseException as exc:
        result_queue.put(("error", str(exc), str(getattr(exc, "code", exc.__class__.__name__))))


class AutoAttemptSupervisor:
    """Watch meaningful run-state changes, not lease-heartbeat traffic."""

    def __init__(
        self,
        config: object,
        *,
        process_factory: Callable[..., Any] | None = None,
        monotonic: Callable[[], float] = time.monotonic,
        sleeper: Callable[[float], None] = time.sleep,
    ) -> None:
        self.config = config
        self.process_factory = process_factory
        self.monotonic = monotonic
        self.sleeper = sleeper

    def _activity(self) -> tuple[tuple[str, int], ...]:
        """State-file writes are phase/progress writes; heartbeats do not touch them."""
        root = Path(self.config.state_dir)
        return tuple(sorted(
            (str(path), path.stat().st_mtime_ns)
            for path in root.glob("*/state/run-state.json")
            if path.is_file()
        ))

    def run(
        self,
        target_subchapter_id: str | None = None,
        *,
        target_chapter: str | int | None = None,
    ) -> object:
        context = multiprocessing.get_context("spawn")
        results = context.Queue()
        process = (
            self.process_factory(_child, (self.config, target_subchapter_id, target_chapter, results))
            if self.process_factory is not None
            else context.Process(
                target=_child,
                args=(self.config, target_subchapter_id, target_chapter, results),
            )
        )
        # Every run_generation() call creates a fresh run-state path. Snapshot
        # pre-existing paths before the child starts, then pin progress tracking
        # to the first new run-state created by this supervised attempt. This
        # prevents unrelated historical/manual run-state writes from masking a
        # stalled child. WorkerLock further fences concurrent use of the same Gem.
        baseline_paths = {path for path, _ in self._activity()}
        process.start()
        tracked_state_path: str | None = None
        previous: tuple[tuple[str, int], ...] = ()
        last_activity = self.monotonic()
        stale_checks = 0
        terminated = False
        while process.is_alive():
            self.sleeper(float(self.config.stall_check_seconds))
            all_activity = self._activity()
            if tracked_state_path is None:
                new_states = [item for item in all_activity if item[0] not in baseline_paths]
                if new_states:
                    # A single worker normally creates exactly one new run-state.
                    # Pin deterministically so later writes elsewhere cannot reset
                    # this attempt's watchdog.
                    tracked_state_path = sorted(new_states)[0][0]
            activity = tuple(
                item for item in all_activity
                if tracked_state_path is not None and item[0] == tracked_state_path
            )
            now = self.monotonic()
            if activity != previous:
                previous = activity
                last_activity = now
                stale_checks = 0
                continue
            if now - last_activity < self.config.stall_after_seconds:
                continue
            stale_checks += 1
            if stale_checks < self.config.stall_max_consecutive_checks:
                continue
            terminated = True
            # Newer Python runtimes can request KeyboardInterrupt first. Windows
            # lacks a reliably deliverable equivalent for spawned children, so it
            # falls back to terminate(); either path deliberately leaves Drive
            # checkpoints untouched for lease-expiry recovery.
            interrupter = getattr(process, "interrupt", None)
            if callable(interrupter):
                interrupter()
            else:
                process.terminate()
            process.join(float(self.config.stall_terminate_grace_seconds))
            if process.is_alive():
                if callable(interrupter):
                    process.terminate()
                    process.join(float(self.config.stall_terminate_grace_seconds))
                if process.is_alive() and hasattr(process, "kill"):
                    process.kill()
            break
        process.join()
        if terminated:
            raise AutoJobExecutionError(
                "Generation worker was terminated after three consecutive stale checks; "
                "durable parsed-stage checkpoints were preserved for recovery.",
                status="interrupted",
                original_code="AUTO_STALL_TERMINATED",
            )
        try:
            # The spawned child's queue feeder can complete just after join(),
            # especially on Windows; allow a short bounded handoff.
            result = results.get(timeout=1)
        except queue.Empty as exc:
            raise AutoJobExecutionError(
                "Generation child exited without a result",
                status="interrupted",
                original_code="AUTO_CHILD_NO_RESULT",
            ) from exc
        status = result[0]
        if status == "ok":
            return result[1]
        if status == "no-job":
            raise NoAvailableJob(result[1])
        if status == "auto-error":
            _, message, error_status, original_code = result
            raise AutoJobExecutionError(message, status=error_status, original_code=original_code)
        _, message, code = result
        raise AutoJobExecutionError(message, status="interrupted", original_code=code)

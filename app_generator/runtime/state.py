"""Durable explicit run-state machine."""

from __future__ import annotations

import json
import os
import tempfile
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Any

from app_generator.errors import GeneratorError


class RunPhase(StrEnum):
    START = "START"
    CONFIG_LOADED = "CONFIG_LOADED"
    WORKER_LOCK_ACQUIRED = "WORKER_LOCK_ACQUIRED"
    DRIVE_AUTHENTICATED = "DRIVE_AUTHENTICATED"
    DRIVE_INVENTORIED = "DRIVE_INVENTORIED"
    JOB_LEASED = "JOB_LEASED"
    GIT_BRANCH_PREPARED = "GIT_BRANCH_PREPARED"
    SOURCE_RESOLVED = "SOURCE_RESOLVED"
    SOURCE_DOWNLOADED = "SOURCE_DOWNLOADED"
    CHROME_STARTED = "CHROME_STARTED"
    GOOGLE_ACCOUNT_VERIFIED = "GOOGLE_ACCOUNT_VERIFIED"
    GEM_CONFIG_CHECKED = "GEM_CONFIG_CHECKED"
    SOURCE_ATTACHED = "SOURCE_ATTACHED"
    TEMPORARY_SOURCE_REMOVED = "TEMPORARY_SOURCE_REMOVED"
    SOURCE_MANIFEST_READY = "SOURCE_MANIFEST_READY"
    MODEL_SELECTED = "MODEL_SELECTED"
    GENERATING = "GENERATING"
    PACKAGE_ASSEMBLED = "PACKAGE_ASSEMBLED"
    VALIDATING = "VALIDATING"
    REPAIRING = "REPAIRING"
    CONTENT_VALIDATED = "CONTENT_VALIDATED"
    SEMANTIC_REVIEW_COMPLETED = "SEMANTIC_REVIEW_COMPLETED"
    FINAL_PACKAGE_WRITTEN = "FINAL_PACKAGE_WRITTEN"
    FINAL_PACKAGE_REVERIFIED = "FINAL_PACKAGE_REVERIFIED"
    GIT_PUBLISHED = "GIT_PUBLISHED"
    REVIEW_PENDING = "REVIEW_PENDING"
    COMPLETE = "COMPLETE"
    FAILED = "FAILED"


@dataclass
class RunState:
    run_id: str
    phase: RunPhase = RunPhase.START
    created_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    actual_model: str | None = None
    job_key: str | None = None
    worker_id: str | None = None
    lease_expires_at: str | None = None
    source_locator: dict[str, str | int] = field(default_factory=dict)
    source_metadata: list[dict[str, str | int]] = field(default_factory=list)
    installed_paths: list[str] = field(default_factory=list)
    branch: str | None = None
    commit: str | None = None
    pr_url: str | None = None
    error_code: str | None = None
    error_message: str | None = None
    history: list[dict[str, str]] = field(default_factory=list)


class StateStore:
    def __init__(self, path: Path, run_id: str) -> None:
        self.path = path
        if path.exists():
            payload = json.loads(path.read_text(encoding="utf-8"))
            payload["phase"] = RunPhase(payload["phase"])
            self.state = RunState(**payload)
        else:
            self.state = RunState(run_id=run_id)
            self._save()

    def transition(self, phase: RunPhase, **updates: Any) -> None:
        terminal = {RunPhase.COMPLETE, RunPhase.FAILED}
        if self.state.phase in terminal:
            raise GeneratorError(f"Cannot transition a terminal run from {self.state.phase}")
        previous = self.state.phase
        self.state.phase = phase
        self.state.updated_at = datetime.now(UTC).isoformat()
        for key, value in updates.items():
            if not hasattr(self.state, key):
                raise GeneratorError(f"Unknown run-state field: {key}")
            setattr(self.state, key, value)
        self.state.history.append({"from": previous.value, "to": phase.value, "at": self.state.updated_at})
        self._save()

    def update(self, **updates: Any) -> None:
        """Persist diagnostic/recovery fields without inventing a phase transition."""

        for key, value in updates.items():
            if not hasattr(self.state, key):
                raise GeneratorError(f"Unknown run-state field: {key}")
            setattr(self.state, key, value)
        self.state.updated_at = datetime.now(UTC).isoformat()
        self._save()

    def resume(self) -> None:
        if (
            self.state.phase == RunPhase.CONFIG_LOADED
            and self.state.history
            and self.state.history[-1].get("to") == "RESUMED"
        ):
            # A prior resume may have reached CONFIG_LOADED before an older
            # runtime discovered that the worker lock was unavailable. Treat
            # that narrowly identified pre-work state as an idempotent resume.
            return
        if self.state.phase == RunPhase.COMPLETE:
            raise GeneratorError(
                "Completed runs cannot resume generation"
            )
        previous = self.state.phase
        self.state.phase = RunPhase.CONFIG_LOADED
        self.state.error_code = None
        self.state.error_message = None
        self.state.updated_at = datetime.now(UTC).isoformat()
        self.state.history.append({"from": previous.value, "to": "RESUMED", "at": self.state.updated_at})
        self._save()

    def fail(self, error: BaseException) -> None:
        code = getattr(error, "code", error.__class__.__name__)
        if self.state.phase not in {RunPhase.COMPLETE, RunPhase.FAILED}:
            self.transition(RunPhase.FAILED, error_code=code, error_message=str(error))

    def _save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = asdict(self.state)
        payload["phase"] = self.state.phase.value
        descriptor, temporary = tempfile.mkstemp(prefix=f".{self.path.name}.", suffix=".tmp", dir=self.path.parent)
        try:
            with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
                json.dump(payload, handle, indent=2, ensure_ascii=False)
                handle.write("\n")
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, self.path)
        except BaseException:
            try:
                os.unlink(temporary)
            except FileNotFoundError:
                pass
            raise

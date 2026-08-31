"""HTTPS client for the Google Apps Script lease coordinator."""

from __future__ import annotations

import os
import warnings
from dataclasses import dataclass
from typing import Any, Iterable

from app_generator.config import GeneratorConfig
from app_generator.errors import CoordinatorError, LeaseLostError, NoAvailableJob
from app_generator.sources.google_drive import ResolvedDriveSource


@dataclass(frozen=True)
class JobLease:
    job_key: str
    drive_file_id: str
    subchapter_id: str
    relative_path: str
    source_version: str
    worker_id: str
    lease_expires_at: str
    attempt_count: int


@dataclass(frozen=True)
class QueueSnapshot:
    total: int
    queued: int
    interrupted: int
    leased: int
    generated: int
    review_pending: int
    completed: int
    failed: int
    next_job_key: str
    next_subchapter_id: str

    @property
    def unfinished(self) -> int:
        return self.queued + self.interrupted + self.leased

    @property
    def blocked(self) -> bool:
        return self.failed > 0 and self.unfinished == 0

    @property
    def all_successful(self) -> bool:
        return self.total > 0 and self.unfinished == 0 and self.failed == 0


class CoordinatorClient:
    def __init__(self, config: GeneratorConfig, *, session: Any | None = None) -> None:
        token = os.environ.get(config.coordinator_token_env, "").strip()
        if not token and config.project_name == "BrilliantContentGenerator":
            token = os.environ.get("BRILLIANT_COORDINATOR_TOKEN", "").strip()
            if token:
                warnings.warn(
                    "BRILLIANT_COORDINATOR_TOKEN is deprecated; use "
                    f"{config.coordinator_token_env}",
                    DeprecationWarning,
                    stacklevel=2,
                )
        if not token:
            raise CoordinatorError(
                f"Coordinated selection requires the {config.coordinator_token_env} environment variable"
            )
        if session is None:
            try:
                import requests
            except ImportError as exc:
                raise CoordinatorError("The requests package is required for coordinated generation") from exc
            session = requests.Session()
        self.url = config.coordinator_url
        self.project_name = config.project_name
        self.token = token
        self.timeout = config.coordinator_timeout_seconds
        self.worker_id = config.worker_id
        self.lease_seconds = config.lease_seconds
        self.max_job_attempts = config.max_job_attempts
        self.session = session

    def _post(self, action: str, **payload: Any) -> dict[str, Any]:
        request = {
            "action": action,
            "token": self.token,
            "project_name": self.project_name,
            **payload,
        }
        try:
            response = self.session.post(self.url, json=request, timeout=self.timeout)
            response.raise_for_status()
            body = response.json()
        except Exception as exc:
            raise CoordinatorError(f"Coordinator request {action!r} failed: {exc}") from exc
        if not isinstance(body, dict):
            raise CoordinatorError("Coordinator returned a non-object response")
        if not body.get("ok"):
            code = str(body.get("code", "COORDINATOR_ERROR"))
            message = str(body.get("error", "Coordinator rejected the request"))
            if code == "NO_AVAILABLE_JOB":
                raise NoAvailableJob(message)
            if code == "LEASE_LOST":
                raise LeaseLostError(message)
            raise CoordinatorError(message)
        return body

    @staticmethod
    def _candidate(source: ResolvedDriveSource, *, local_completed: bool = False) -> dict[str, Any]:
        return {
            "job_key": source.job_key,
            "drive_file_id": source.file_id,
            "subchapter_id": source.subchapter_id,
            "relative_path": source.relative_path,
            "source_version": source.source_version,
            "local_completed": bool(local_completed),
        }

    @staticmethod
    def _lease(payload: dict[str, Any]) -> JobLease:
        lease = payload.get("lease")
        if not isinstance(lease, dict):
            raise CoordinatorError("Coordinator response omitted the lease object")
        try:
            return JobLease(
                job_key=str(lease["job_key"]),
                drive_file_id=str(lease["drive_file_id"]),
                subchapter_id=str(lease["subchapter_id"]),
                relative_path=str(lease["relative_path"]),
                source_version=str(lease["source_version"]),
                worker_id=str(lease["worker_id"]),
                lease_expires_at=str(lease["lease_expires_at"]),
                attempt_count=int(lease["attempt_count"]),
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise CoordinatorError(f"Coordinator returned an invalid lease: {exc}") from exc

    @staticmethod
    def _snapshot(payload: dict[str, Any]) -> QueueSnapshot:
        raw = payload.get("snapshot")
        if not isinstance(raw, dict):
            raise CoordinatorError("Coordinator response omitted the queue snapshot")
        counts = raw.get("counts")
        if not isinstance(counts, dict):
            raise CoordinatorError("Coordinator queue snapshot omitted counts")
        next_candidate = raw.get("next_candidate") or {}
        if not isinstance(next_candidate, dict):
            next_candidate = {}
        try:
            return QueueSnapshot(
                total=int(raw.get("total", 0)),
                queued=int(counts.get("queued", 0)),
                interrupted=int(counts.get("interrupted", 0)),
                leased=int(counts.get("leased", 0)),
                generated=int(counts.get("generated", 0)),
                review_pending=int(counts.get("review_pending", 0)),
                completed=int(counts.get("completed", 0)),
                failed=int(counts.get("failed", 0)),
                next_job_key=str(next_candidate.get("job_key", "")),
                next_subchapter_id=str(next_candidate.get("subchapter_id", "")),
            )
        except (TypeError, ValueError) as exc:
            raise CoordinatorError(f"Coordinator returned an invalid queue snapshot: {exc}") from exc

    @staticmethod
    def _candidate_list(
        sources: Iterable[ResolvedDriveSource],
        local_completed_job_keys: set[str] | frozenset[str] | None = None,
    ) -> list[dict[str, Any]]:
        completed = local_completed_job_keys or set()
        return [
            CoordinatorClient._candidate(source, local_completed=source.job_key in completed)
            for source in sources
        ]

    def claim(self, sources: Iterable[ResolvedDriveSource]) -> JobLease:
        candidates = self._candidate_list(sources)
        if not candidates:
            raise NoAvailableJob("Google Drive contains no eligible source.pdf jobs")
        body = self._post(
            "claim",
            worker_id=self.worker_id,
            lease_seconds=self.lease_seconds,
            max_job_attempts=self.max_job_attempts,
            candidates=candidates,
        )
        return self._lease(body)

    def claim_auto(
        self,
        sources: Iterable[ResolvedDriveSource],
        *,
        local_completed_job_keys: set[str] | frozenset[str],
    ) -> JobLease:
        candidates = self._candidate_list(sources, local_completed_job_keys)
        if not candidates:
            raise NoAvailableJob("Google Drive contains no source.pdf jobs")
        body = self._post(
            "claim",
            worker_id=self.worker_id,
            lease_seconds=self.lease_seconds,
            max_job_attempts=self.max_job_attempts,
            candidates=candidates,
        )
        return self._lease(body)

    def snapshot_auto(
        self,
        sources: Iterable[ResolvedDriveSource],
        *,
        local_completed_job_keys: set[str] | frozenset[str],
    ) -> QueueSnapshot:
        candidates = self._candidate_list(sources, local_completed_job_keys)
        body = self._post(
            "snapshot",
            worker_id=self.worker_id,
            max_job_attempts=self.max_job_attempts,
            candidates=candidates,
        )
        return self._snapshot(body)

    def health(self, *, require_checkpoints: bool = False) -> None:
        body = self._post("health", worker_id=self.worker_id)
        if require_checkpoints and not bool(body.get("checkpoint_configured")):
            raise CoordinatorError(
                "Auto mode requires CHECKPOINT_FOLDER_ID in the coordinator Apps Script properties"
            )

    def heartbeat(self, lease: JobLease) -> JobLease:
        body = self._post(
            "heartbeat",
            worker_id=self.worker_id,
            job_key=lease.job_key,
            lease_seconds=self.lease_seconds,
        )
        return self._lease(body)

    def mark_review_pending(self, lease: JobLease, *, branch: str, pr_url: str) -> None:
        self._post(
            "review_pending",
            worker_id=self.worker_id,
            job_key=lease.job_key,
            branch=branch,
            pr_url=pr_url,
        )

    def mark_generated(self, lease: JobLease) -> None:
        self._post("generated", worker_id=self.worker_id, job_key=lease.job_key)

    def mark_failed(self, lease: JobLease, *, error_code: str, error_message: str) -> str:
        body = self._post(
            "failed",
            worker_id=self.worker_id,
            job_key=lease.job_key,
            max_job_attempts=self.max_job_attempts,
            error_code=error_code,
            error_message=error_message[:2000],
        )
        return str(body.get("status", "failed"))

    def mark_completed(self, job_key: str, *, pr_url: str = "") -> None:
        self._post("completed", worker_id=self.worker_id, job_key=job_key, pr_url=pr_url)

    def checkpoint_save(self, lease: JobLease, name: str, document: object) -> None:
        self._post(
            "checkpoint_save",
            worker_id=self.worker_id,
            job_key=lease.job_key,
            source_version=lease.source_version,
            stage=name,
            document=document,
        )

    def checkpoint_load(self, lease: JobLease) -> dict[str, object]:
        body = self._post(
            "checkpoint_load",
            worker_id=self.worker_id,
            job_key=lease.job_key,
            source_version=lease.source_version,
        )
        stages = body.get("stages", {})
        if not isinstance(stages, dict):
            raise CoordinatorError("Coordinator returned an invalid checkpoint stage map")
        return {str(name): document for name, document in stages.items()}

    def checkpoint_delete(self, lease: JobLease, name: str) -> None:
        self._post(
            "checkpoint_delete",
            worker_id=self.worker_id,
            job_key=lease.job_key,
            source_version=lease.source_version,
            stage=name,
        )

    def checkpoint_clear(self, lease: JobLease) -> None:
        self._post(
            "checkpoint_clear",
            worker_id=self.worker_id,
            job_key=lease.job_key,
            source_version=lease.source_version,
        )

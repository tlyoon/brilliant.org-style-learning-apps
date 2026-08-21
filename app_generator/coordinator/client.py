"""HTTPS client for the Google Apps Script lease coordinator."""

from __future__ import annotations

import os
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


class CoordinatorClient:
    def __init__(self, config: GeneratorConfig, *, session: Any | None = None) -> None:
        token = os.environ.get(config.coordinator_token_env, "").strip()
        if not token:
            raise CoordinatorError(
                f"Distributed mode requires the {config.coordinator_token_env} environment variable"
            )
        if session is None:
            try:
                import requests
            except ImportError as exc:
                raise CoordinatorError("The requests package is required for distributed coordination") from exc
            session = requests.Session()
        self.url = config.coordinator_url
        self.token = token
        self.timeout = config.coordinator_timeout_seconds
        self.worker_id = config.worker_id
        self.lease_seconds = config.lease_seconds
        self.max_job_attempts = config.max_job_attempts
        self.session = session

    def _post(self, action: str, **payload: Any) -> dict[str, Any]:
        request = {"action": action, "token": self.token, **payload}
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
    def _candidate(source: ResolvedDriveSource) -> dict[str, Any]:
        return {
            "job_key": source.job_key,
            "drive_file_id": source.file_id,
            "subchapter_id": source.subchapter_id,
            "relative_path": source.relative_path,
            "source_version": source.source_version,
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

    def claim(self, sources: Iterable[ResolvedDriveSource]) -> JobLease:
        candidates = [self._candidate(source) for source in sources]
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

    def health(self) -> None:
        self._post("health", worker_id=self.worker_id)

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

    def mark_failed(self, lease: JobLease, *, error_code: str, error_message: str) -> None:
        self._post(
            "failed",
            worker_id=self.worker_id,
            job_key=lease.job_key,
            max_job_attempts=self.max_job_attempts,
            error_code=error_code,
            error_message=error_message[:2000],
        )

    def mark_completed(self, job_key: str, *, pr_url: str = "") -> None:
        self._post("completed", worker_id=self.worker_id, job_key=job_key, pr_url=pr_url)

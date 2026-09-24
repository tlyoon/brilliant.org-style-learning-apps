"""Google-Drive-native lease, queue, and checkpoint coordination for auto mode."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, replace
from datetime import UTC, datetime, timedelta
from email.utils import parsedate_to_datetime
from typing import Any, Iterable
from uuid import uuid4

from app_generator.config import GeneratorConfig
from app_generator.coordinator.client import FailedJobRetry, JobLease, QueueSnapshot
from app_generator.errors import CoordinatorError, LeaseLostError, NoAvailableJob
from app_generator.sources.google_drive import DRIVE_FILES_URL, ResolvedDriveSource
from app_generator.sources.google_drive_auth import authorize_google_drive

DRIVE_UPLOAD_URL = "https://www.googleapis.com/upload/drive/v3/files"
STATE_SCHEMA = 1


@dataclass(frozen=True)
class _Marker:
    file_id: str
    kind: str
    job_key: str
    attempt_id: str
    created_at: datetime
    modified_at: datetime
    attempt_no: int = 0


@dataclass(frozen=True)
class _JobState:
    status: str
    attempt_count: int
    last_error_code: str = ""
    winner: _Marker | None = None


def _utc(value: str) -> datetime:
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(UTC)
    except ValueError as exc:
        raise CoordinatorError(f"Google Drive returned an invalid timestamp: {value!r}") from exc


def _server_now(response: Any) -> datetime:
    raw = str(getattr(response, "headers", {}).get("Date", "")).strip()
    if not raw:
        raise CoordinatorError("Google Drive response omitted its Date header; refusing local-clock lease decisions")
    try:
        return parsedate_to_datetime(raw).astimezone(UTC)
    except (TypeError, ValueError) as exc:
        raise CoordinatorError(f"Google Drive returned an invalid Date header: {raw!r}") from exc


def _q(value: str) -> str:
    return value.replace("\\", "\\\\").replace("'", "\\'")


class DriveCoordinatorClient:
    """Drive-backed coordinator used only by continuous/targeted auto mode."""

    def __init__(self, config: GeneratorConfig, *, session: Any | None = None, sleeper=time.sleep) -> None:
        self.config = config
        self.project_name = config.project_name
        self.worker_id = config.worker_id
        self.lease_seconds = config.lease_seconds
        self.max_job_attempts = config.max_job_attempts
        self.timeout = config.drive_api_timeout_seconds
        self.sleeper = sleeper
        self.session = session or authorize_google_drive(config).session

    def _request(self, method: str, url: str, **kwargs: Any) -> Any:
        last: BaseException | None = None
        for attempt in range(3):
            try:
                response = self.session.request(method, url, timeout=self.timeout, **kwargs)
                response.raise_for_status()
                return response
            except BaseException as exc:
                last = exc
                if attempt == 2:
                    break
                self.sleeper(float(2 ** attempt))
        raise CoordinatorError(f"Google Drive coordination request failed: {last}") from last

    def _list(self, query: str) -> tuple[list[dict[str, Any]], datetime]:
        files: list[dict[str, Any]] = []
        token = ""
        server_now: datetime | None = None
        while True:
            params: dict[str, Any] = {
                "q": query,
                "spaces": "drive",
                "pageSize": "1000",
                "supportsAllDrives": "true",
                "includeItemsFromAllDrives": "true",
                "fields": "nextPageToken,files(id,name,createdTime,modifiedTime,appProperties)",
            }
            if token:
                params["pageToken"] = token
            response = self._request("GET", DRIVE_FILES_URL, params=params)
            server_now = _server_now(response)
            payload = response.json()
            rows = payload.get("files", [])
            if not isinstance(rows, list):
                raise CoordinatorError("Google Drive returned an invalid marker list")
            files.extend(row for row in rows if isinstance(row, dict))
            token = str(payload.get("nextPageToken", ""))
            if not token:
                break
        assert server_now is not None
        return files, server_now

    def _properties(self, kind: str, job_key: str, attempt_id: str = "", attempt_no: int = 0) -> dict[str, str]:
        result = {
            "appgen_project": self.project_name,
            "appgen_kind": kind,
            "appgen_job": job_key,
        }
        if attempt_id:
            result["appgen_attempt"] = attempt_id
        if attempt_no:
            result["appgen_attempt_no"] = str(attempt_no)
        return result

    def _create_json(
        self,
        kind: str,
        job_key: str,
        payload: dict[str, Any],
        *,
        parent_id: str,
        attempt_id: str = "",
        attempt_no: int = 0,
    ) -> dict[str, Any]:
        if not parent_id:
            raise CoordinatorError("Drive coordination event omitted its topic parent folder ID")
        nonce = uuid4().hex
        metadata = {
            "name": f"{kind}.{job_key[:16]}.{attempt_id or nonce}.{nonce[:10]}.json",
            "parents": [parent_id],
            "mimeType": "application/json",
            "appProperties": self._properties(kind, job_key, attempt_id, attempt_no),
        }
        boundary = f"appgen-{uuid4().hex}"
        metadata_bytes = json.dumps(metadata, ensure_ascii=False).encode("utf-8")
        payload_bytes = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        body = b"".join((
            f"--{boundary}\r\nContent-Type: application/json; charset=UTF-8\r\n\r\n".encode("ascii"),
            metadata_bytes,
            f"\r\n--{boundary}\r\nContent-Type: application/json\r\n\r\n".encode("ascii"),
            payload_bytes,
            f"\r\n--{boundary}--\r\n".encode("ascii"),
        ))
        response = self._request(
            "POST",
            DRIVE_UPLOAD_URL,
            params={"uploadType": "multipart", "supportsAllDrives": "true", "fields": "id,name,createdTime,modifiedTime,appProperties"},
            headers={"Content-Type": f'multipart/related; boundary="{boundary}"'},
            data=body,
        )
        return response.json()

    def _read_json(self, file_id: str) -> dict[str, Any]:
        response = self._request(
            "GET",
            f"{DRIVE_FILES_URL}/{file_id}",
            params={"alt": "media", "supportsAllDrives": "true"},
        )
        payload = response.json()
        if not isinstance(payload, dict):
            raise CoordinatorError(f"Drive marker {file_id} is not a JSON object")
        return payload

    def _update_json(self, file_id: str, payload: dict[str, Any]) -> tuple[dict[str, Any], datetime]:
        response = self._request(
            "PATCH",
            f"{DRIVE_UPLOAD_URL}/{file_id}",
            params={"uploadType": "media", "supportsAllDrives": "true", "fields": "id,modifiedTime"},
            headers={"Content-Type": "application/json"},
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        )
        return response.json(), _server_now(response)

    def _delete(self, file_id: str) -> None:
        try:
            self._request(
                "DELETE",
                f"{DRIVE_FILES_URL}/{file_id}",
                params={"supportsAllDrives": "true"},
            )
        except CoordinatorError as exc:
            if "404" not in str(exc):
                raise

    def _marker_rows(self, job_key: str, *, kind: str | None = None) -> tuple[list[_Marker], datetime]:
        query = (
            "trashed = false and "
            f"appProperties has {{ key='appgen_project' and value='{_q(self.project_name)}' }} and "
            f"appProperties has {{ key='appgen_job' and value='{_q(job_key)}' }}"
        )
        if kind:
            query += f" and appProperties has {{ key='appgen_kind' and value='{_q(kind)}' }}"
        rows, server_now = self._list(query)
        markers: list[_Marker] = []
        for row in rows:
            props = row.get("appProperties", {}) or {}
            try:
                markers.append(
                    _Marker(
                        file_id=str(row["id"]),
                        kind=str(props.get("appgen_kind", "")),
                        job_key=str(props.get("appgen_job", "")),
                        attempt_id=str(props.get("appgen_attempt", "")),
                        created_at=_utc(str(row["createdTime"])),
                        modified_at=_utc(str(row["modifiedTime"])),
                        attempt_no=int(props.get("appgen_attempt_no", "0") or 0),
                    )
                )
            except (KeyError, TypeError, ValueError) as exc:
                raise CoordinatorError(f"Invalid Drive coordination marker metadata: {row}") from exc
        markers.sort(key=lambda item: (item.created_at, item.file_id))
        return markers, server_now

    def _active_claims(self, job_key: str) -> tuple[list[_Marker], datetime]:
        claims, server_now = self._marker_rows(job_key, kind="claim")
        active = [
            claim
            for claim in claims
            if (server_now - claim.modified_at).total_seconds() < self.lease_seconds
        ]
        active.sort(key=lambda item: (item.created_at, item.file_id))
        return active, server_now

    def _latest_retry_time(self, job_key: str) -> datetime | None:
        retries, _ = self._marker_rows(job_key, kind="retry")
        return retries[-1].created_at if retries else None

    def _attempt_markers(self, job_key: str) -> list[_Marker]:
        claims, _ = self._marker_rows(job_key, kind="claim")
        failures, _ = self._marker_rows(job_key, kind="failure")
        cutoff = self._latest_retry_time(job_key)
        events = claims + failures
        if cutoff is not None:
            events = [item for item in events if item.created_at > cutoff]
        # A normal failed attempt has both a claim and a failure event. Count it once.
        by_attempt: dict[str, _Marker] = {}
        for item in events:
            key = item.attempt_id or item.file_id
            previous = by_attempt.get(key)
            if previous is None or item.attempt_no > previous.attempt_no:
                by_attempt[key] = item
        return sorted(by_attempt.values(), key=lambda item: (item.created_at, item.file_id))

    def _last_failure_code(self, job_key: str) -> str:
        failures, _ = self._marker_rows(job_key, kind="failure")
        cutoff = self._latest_retry_time(job_key)
        if cutoff is not None:
            failures = [item for item in failures if item.created_at > cutoff]
        if not failures:
            return ""
        try:
            return str(self._read_json(failures[-1].file_id).get("error_code", ""))
        except CoordinatorError:
            return "DRIVE_FAILURE_MARKER_UNREADABLE"

    def _job_state(self, source: ResolvedDriveSource, *, local_completed: bool = False) -> _JobState:
        if local_completed:
            return _JobState("generated", 0)
        success, _ = self._marker_rows(source.job_key, kind="success")
        if success:
            return _JobState("generated", 0)
        active, _ = self._active_claims(source.job_key)
        attempts = self._attempt_markers(source.job_key)
        attempt_count = max((item.attempt_no for item in attempts), default=len(attempts))
        if active:
            return _JobState("leased", attempt_count, winner=active[0])
        error_code = self._last_failure_code(source.job_key)
        if attempt_count >= self.max_job_attempts:
            return _JobState("failed", attempt_count, error_code)
        if attempt_count:
            return _JobState("interrupted", attempt_count, error_code)
        if self._latest_retry_time(source.job_key) is not None:
            return _JobState("interrupted", 0)
        return _JobState("queued", 0)

    def snapshot_auto(
        self,
        candidates: Iterable[ResolvedDriveSource],
        *,
        local_completed_job_keys: set[str] | None = None,
    ) -> QueueSnapshot:
        sources = tuple(candidates)
        completed = local_completed_job_keys or set()
        counts = {"queued": 0, "interrupted": 0, "leased": 0, "generated": 0, "failed": 0}
        states: list[tuple[ResolvedDriveSource, _JobState]] = []
        for source in sources:
            state = self._job_state(source, local_completed=source.job_key in completed)
            counts[state.status] += 1
            states.append((source, state))
        runnable = [item for item in states if item[1].status == "interrupted"]
        if not runnable:
            runnable = [item for item in states if item[1].status == "queued"]
        next_source = runnable[0][0] if runnable else None
        target_state = states[0][1] if len(states) == 1 else None
        return QueueSnapshot(
            total=len(sources),
            queued=counts["queued"],
            interrupted=counts["interrupted"],
            leased=counts["leased"],
            generated=counts["generated"],
            review_pending=0,
            completed=0,
            failed=counts["failed"],
            next_job_key=next_source.job_key if next_source else "",
            next_subchapter_id=next_source.subchapter_id if next_source else "",
            target_status=target_state.status if target_state else "",
            target_attempt_count=target_state.attempt_count if target_state else 0,
            target_error_code=target_state.last_error_code if target_state else "",
        )

    def _lease_from_claim(self, source: ResolvedDriveSource, marker: _Marker, attempt_no: int) -> JobLease:
        expires = marker.modified_at + timedelta(seconds=self.lease_seconds)
        return JobLease(
            job_key=source.job_key,
            drive_file_id=source.file_id,
            subchapter_id=source.subchapter_id,
            relative_path=source.relative_path,
            source_version=source.source_version,
            worker_id=self.worker_id,
            lease_expires_at=expires.isoformat().replace("+00:00", "Z"),
            attempt_count=attempt_no,
            lease_token=marker.file_id,
            attempt_id=marker.attempt_id,
            coordination_parent_id=source.parent_folder_id or "",
        )

    def claim_auto(
        self,
        candidates: Iterable[ResolvedDriveSource],
        *,
        local_completed_job_keys: set[str] | None = None,
    ) -> JobLease:
        completed = local_completed_job_keys or set()
        for source in candidates:
            state = self._job_state(source, local_completed=source.job_key in completed)
            if state.status not in {"queued", "interrupted"}:
                continue
            if not source.parent_folder_id:
                raise CoordinatorError(f"Drive source {source.relative_path} omitted its parent folder ID")
            attempt_no = state.attempt_count + 1
            attempt_id = uuid4().hex
            payload = {
                "schema": STATE_SCHEMA,
                "kind": "claim",
                "project": self.project_name,
                "job_key": source.job_key,
                "drive_file_id": source.file_id,
                "subchapter_id": source.subchapter_id,
                "relative_path": source.relative_path,
                "source_version": source.source_version,
                "worker_id": self.worker_id,
                "attempt_id": attempt_id,
                "attempt_count": attempt_no,
            }
            row = self._create_json(
                "claim", source.job_key, payload, parent_id=source.parent_folder_id,
                attempt_id=attempt_id, attempt_no=attempt_no,
            )
            own_id = str(row.get("id", ""))
            won = True
            winner: _Marker | None = None
            for _ in range(2):
                self.sleeper(1.0)
                active, _ = self._active_claims(source.job_key)
                winner = active[0] if active else None
                if winner is None or winner.file_id != own_id:
                    won = False
                    break
            if won and winner is not None:
                return self._lease_from_claim(source, winner, attempt_no)
            if own_id:
                self._delete(own_id)
        raise NoAvailableJob("No Drive auto source job is currently claimable")

    def heartbeat(self, lease: JobLease) -> JobLease:
        if not lease.lease_token:
            raise LeaseLostError("Drive lease omitted its fencing token")
        active, _ = self._active_claims(lease.job_key)
        if not active or active[0].file_id != lease.lease_token:
            raise LeaseLostError("Drive lease expired or another claim won the deterministic election")
        payload = self._read_json(lease.lease_token)
        payload["heartbeat_nonce"] = uuid4().hex
        metadata, server_now = self._update_json(lease.lease_token, payload)
        modified = _utc(str(metadata.get("modifiedTime", "")))
        if modified > server_now + timedelta(seconds=5):
            raise LeaseLostError("Drive heartbeat returned an implausible future modifiedTime")
        expires = modified + timedelta(seconds=self.lease_seconds)
        return replace(lease, lease_expires_at=expires.isoformat().replace("+00:00", "Z"))

    def _checkpoint_event(self, lease: JobLease, operation: str, *, name: str = "", document: object = None) -> None:
        self.heartbeat(lease)
        payload: dict[str, Any] = {
            "schema": STATE_SCHEMA,
            "kind": "checkpoint",
            "job_key": lease.job_key,
            "attempt_id": lease.attempt_id,
            "operation": operation,
        }
        if name:
            payload["stage"] = name
        if operation == "save":
            payload["document"] = document
        self._create_json(
            "checkpoint",
            lease.job_key,
            payload,
            parent_id=lease.coordination_parent_id,
            attempt_id=lease.attempt_id,
            attempt_no=lease.attempt_count,
        )

    def checkpoint_save(self, lease: JobLease, name: str, document: object) -> None:
        self._checkpoint_event(lease, "save", name=name, document=document)

    def checkpoint_delete(self, lease: JobLease, name: str) -> None:
        self._checkpoint_event(lease, "delete", name=name)

    def checkpoint_clear(self, lease: JobLease) -> None:
        self._checkpoint_event(lease, "clear")

    def checkpoint_load(self, lease: JobLease) -> dict[str, object]:
        markers, _ = self._marker_rows(lease.job_key, kind="checkpoint")
        stages: dict[str, object] = {}
        for marker in markers:
            payload = self._read_json(marker.file_id)
            operation = str(payload.get("operation", ""))
            if operation == "clear":
                stages.clear()
                continue
            name = str(payload.get("stage", ""))
            if operation == "delete":
                stages.pop(name, None)
            elif operation == "save" and name:
                stages[name] = payload.get("document")
        return stages

    def _release_claim(self, lease: JobLease) -> None:
        if lease.lease_token:
            self._delete(lease.lease_token)

    def mark_failed(self, lease: JobLease, *, error_code: str, error_message: str) -> str:
        payload = {
            "schema": STATE_SCHEMA,
            "kind": "failure",
            "job_key": lease.job_key,
            "attempt_id": lease.attempt_id,
            "attempt_count": lease.attempt_count,
            "worker_id": lease.worker_id,
            "error_code": error_code,
            "error_message": error_message[:4000],
        }
        self._create_json(
            "failure",
            lease.job_key,
            payload,
            parent_id=lease.coordination_parent_id,
            attempt_id=lease.attempt_id,
            attempt_no=lease.attempt_count,
        )
        self._release_claim(lease)
        return "failed" if lease.attempt_count >= self.max_job_attempts else "interrupted"

    def mark_generated(self, lease: JobLease, *, branch: str = "", pr_url: str = "") -> str:
        current = self.heartbeat(lease)
        payload = {
            "schema": STATE_SCHEMA,
            "kind": "success",
            "job_key": current.job_key,
            "attempt_id": current.attempt_id,
            "attempt_count": current.attempt_count,
            "worker_id": current.worker_id,
            "branch": branch,
            "pr_url": pr_url,
        }
        self._create_json(
            "success",
            current.job_key,
            payload,
            parent_id=current.coordination_parent_id,
            attempt_id=current.attempt_id,
            attempt_no=current.attempt_count,
        )
        self.checkpoint_clear(current)
        self._release_claim(current)
        return "generated"

    def retry_failed(self, source: ResolvedDriveSource) -> FailedJobRetry:
        state = self._job_state(source)
        if state.status != "failed":
            raise CoordinatorError(f"Drive auto job {source.subchapter_id} is not terminally failed")
        payload = {
            "schema": STATE_SCHEMA,
            "kind": "retry",
            "job_key": source.job_key,
            "previous_attempt_count": state.attempt_count,
            "previous_error_code": state.last_error_code,
        }
        if not source.parent_folder_id:
            raise CoordinatorError(f"Drive source {source.relative_path} omitted its parent folder ID")
        self._create_json("retry", source.job_key, payload, parent_id=source.parent_folder_id)
        return FailedJobRetry(
            status="interrupted",
            previous_attempt_count=state.attempt_count,
            previous_error_code=state.last_error_code,
        )

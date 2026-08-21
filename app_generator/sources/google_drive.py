"""Deterministic Google Drive discovery and controlled PDF download."""

from __future__ import annotations

import logging
import os
import re
import hashlib
from collections import deque
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import parse_qs, urlparse

from app_generator.errors import DriveAccessError, SourceAmbiguous, SourceDownloadError, SourceNotFound

LOGGER = logging.getLogger("app_generator.sources.google_drive")
DRIVE_FILES_URL = "https://www.googleapis.com/drive/v3/files"
FOLDER_MIME = "application/vnd.google-apps.folder"
PDF_MIME = "application/pdf"
DRIVE_ID = re.compile(r"^[A-Za-z0-9_-]{10,}$")
SUBCHAPTER_ID = re.compile(r"^(?P<chapter>[1-9][0-9]*)\.(?P<section>[1-9][0-9]*)$")


@dataclass(frozen=True)
class DriveItem:
    file_id: str
    name: str
    mime_type: str
    size_bytes: int | None = None
    can_download: bool | None = None
    md5_checksum: str | None = None
    modified_time: str | None = None
    version: str | None = None


@dataclass(frozen=True)
class ResolvedDriveSource:
    file_id: str
    filename: str
    relative_path: str
    mime_type: str
    size_bytes: int | None
    md5_checksum: str | None
    subchapter_id: str
    modified_time: str | None = None
    version: str | None = None

    @property
    def source_version(self) -> str:
        return self.md5_checksum or self.version or self.modified_time or "unknown"

    @property
    def job_key(self) -> str:
        material = f"{self.file_id}:{self.source_version}".encode("utf-8")
        return hashlib.sha256(material).hexdigest()

    def metadata(self) -> dict[str, str | int]:
        result: dict[str, str | int] = {
            "drive_file_id": self.file_id,
            "filename": self.filename,
            "relative_path": self.relative_path,
            "mime_type": self.mime_type,
            "subchapter_id": self.subchapter_id,
            "source_version": self.source_version,
            "job_key": self.job_key,
        }
        if self.size_bytes is not None:
            result["size_bytes"] = self.size_bytes
        if self.md5_checksum:
            result["md5_checksum"] = self.md5_checksum
        if self.modified_time:
            result["modified_time"] = self.modified_time
        if self.version:
            result["version"] = self.version
        return result


def extract_drive_folder_id(value: str) -> str:
    """Extract a folder ID from supported Drive links or a raw ID."""

    candidate = value.strip()
    if DRIVE_ID.fullmatch(candidate):
        return candidate
    parsed = urlparse(candidate)
    if parsed.scheme != "https" or parsed.hostname != "drive.google.com":
        raise DriveAccessError("sourcepath is not a supported Google Drive folder URL")
    query_id = parse_qs(parsed.query).get("id", [""])[0]
    if DRIVE_ID.fullmatch(query_id):
        return query_id
    parts = [part for part in parsed.path.split("/") if part]
    if "folders" in parts:
        index = parts.index("folders") + 1
        if index < len(parts) and DRIVE_ID.fullmatch(parts[index]):
            return parts[index]
    raise DriveAccessError("sourcepath does not contain a recognizable Google Drive folder ID")


def _item(payload: dict[str, Any]) -> DriveItem:
    raw_size = payload.get("size")
    return DriveItem(
        file_id=str(payload.get("id", "")),
        name=str(payload.get("name", "")),
        mime_type=str(payload.get("mimeType", "")),
        size_bytes=int(raw_size) if raw_size not in {None, ""} else None,
        can_download=payload.get("capabilities", {}).get("canDownload"),
        md5_checksum=str(payload["md5Checksum"]) if payload.get("md5Checksum") else None,
        modified_time=str(payload["modifiedTime"]) if payload.get("modifiedTime") else None,
        version=str(payload["version"]) if payload.get("version") else None,
    )


class DriveRestClient:
    """Small Drive v3 REST adapter using an authorized requests session."""

    def __init__(self, session: Any, timeout: int) -> None:
        self.session = session
        self.timeout = timeout

    def _json(self, url: str, *, params: dict[str, str | bool]) -> dict[str, Any]:
        try:
            response = self.session.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            payload = response.json()
        except Exception as exc:
            raise DriveAccessError(f"Google Drive request failed: {exc}") from exc
        if not isinstance(payload, dict):
            raise DriveAccessError("Google Drive returned an unexpected response")
        return payload

    def get_item(self, file_id: str) -> DriveItem:
        payload = self._json(
            f"{DRIVE_FILES_URL}/{file_id}",
            params={
                "fields": "id,name,mimeType,size,md5Checksum,modifiedTime,version,capabilities(canDownload)",
                "supportsAllDrives": "true",
            },
        )
        return _item(payload)

    def list_children(self, folder_id: str) -> tuple[DriveItem, ...]:
        page_token = ""
        children: list[DriveItem] = []
        while True:
            params: dict[str, str | bool] = {
                "q": f"'{folder_id}' in parents and trashed = false",
                "spaces": "drive",
                "pageSize": "1000",
                "fields": "nextPageToken,files(id,name,mimeType,size,md5Checksum,modifiedTime,version,capabilities(canDownload))",
                "supportsAllDrives": "true",
                "includeItemsFromAllDrives": "true",
            }
            if page_token:
                params["pageToken"] = page_token
            payload = self._json(DRIVE_FILES_URL, params=params)
            raw_files = payload.get("files", [])
            if not isinstance(raw_files, list):
                raise DriveAccessError("Google Drive returned an invalid child-file list")
            children.extend(_item(entry) for entry in raw_files if isinstance(entry, dict))
            page_token = str(payload.get("nextPageToken", ""))
            if not page_token:
                break
        return tuple(sorted(children, key=lambda child: (child.name.casefold(), child.file_id)))

    def download_file(self, source: ResolvedDriveSource, destination: Path) -> Path:
        if source.mime_type != PDF_MIME:
            raise SourceDownloadError(f"Drive item is not a PDF: {source.relative_path}")
        destination.parent.mkdir(parents=True, exist_ok=True)
        partial = destination.with_name(destination.name + ".part")
        try:
            response = self.session.get(
                f"{DRIVE_FILES_URL}/{source.file_id}",
                params={"alt": "media", "supportsAllDrives": "true"},
                timeout=self.timeout,
                stream=True,
            )
            response.raise_for_status()
            written = 0
            with partial.open("wb") as handle:
                for chunk in response.iter_content(chunk_size=1024 * 1024):
                    if chunk:
                        handle.write(chunk)
                        written += len(chunk)
                handle.flush()
                os.fsync(handle.fileno())
            if source.size_bytes is not None and written != source.size_bytes:
                raise SourceDownloadError(
                    f"Downloaded byte count {written} does not match Drive metadata {source.size_bytes}"
                )
            with partial.open("rb") as handle:
                if handle.read(5) != b"%PDF-":
                    raise SourceDownloadError("Downloaded source does not have a valid PDF signature")
            os.replace(partial, destination)
            return destination
        except SourceDownloadError:
            raise
        except Exception as exc:
            raise SourceDownloadError(f"Could not download {source.relative_path}: {exc}") from exc
        finally:
            try:
                partial.unlink()
            except FileNotFoundError:
                pass


def _selector_components(value: str) -> tuple[str, ...]:
    return tuple(part.casefold() for part in value.replace("\\", "/").split("/") if part)


def _path_matches(parent_path: Iterable[str], selector: tuple[str, ...]) -> bool:
    folded = tuple(part.casefold() for part in parent_path)
    return len(folded) >= len(selector) and folded[-len(selector) :] == selector


def _source_sort_key(source: ResolvedDriveSource) -> tuple[int, int, str, str]:
    match = SUBCHAPTER_ID.fullmatch(source.subchapter_id)
    if not match:
        return (10**9, 10**9, source.relative_path.casefold(), source.file_id)
    return (
        int(match.group("chapter")),
        int(match.group("section")),
        source.relative_path.casefold(),
        source.file_id,
    )


def discover_drive_sources(
    client: DriveRestClient,
    *,
    sourcepath: str,
    target_filename: str,
    max_folders: int,
) -> tuple[ResolvedDriveSource, ...]:
    """Discover every subchapter PDF below the configured Drive root."""

    root_id = extract_drive_folder_id(sourcepath)
    root = client.get_item(root_id)
    if root.mime_type != FOLDER_MIME:
        raise DriveAccessError(f"sourcepath resolves to {root.name!r}, which is not a folder")

    queue: deque[tuple[str, tuple[str, ...]]] = deque([(root_id, ())])
    visited: set[str] = set()
    candidates: list[ResolvedDriveSource] = []
    while queue:
        folder_id, relative_folder = queue.popleft()
        if folder_id in visited:
            continue
        visited.add(folder_id)
        if len(visited) > max_folders:
            raise DriveAccessError(
                f"Drive traversal exceeded the configured max_drive_folders limit ({max_folders})"
            )
        for child in client.list_children(folder_id):
            if child.mime_type == FOLDER_MIME:
                queue.append((child.file_id, relative_folder + (child.name,)))
                continue
            if child.name.casefold() != target_filename.casefold() or child.mime_type != PDF_MIME:
                continue
            if not relative_folder or not SUBCHAPTER_ID.fullmatch(relative_folder[-1]):
                continue
            if child.can_download is False:
                raise SourceDownloadError(
                    f"Google Drive reports that downloading is disabled for "
                    f"{'/'.join(relative_folder + (child.name,))}"
                )
            candidates.append(
                ResolvedDriveSource(
                    file_id=child.file_id,
                    filename=child.name,
                    relative_path="/".join(relative_folder + (child.name,)),
                    mime_type=child.mime_type,
                    size_bytes=child.size_bytes,
                    md5_checksum=child.md5_checksum,
                    subchapter_id=relative_folder[-1],
                    modified_time=child.modified_time,
                    version=child.version,
                )
            )
    return tuple(sorted(candidates, key=_source_sort_key))


def resolve_drive_source(
    client: DriveRestClient,
    *,
    sourcepath: str,
    pdf_subchapter_path: str,
    target_filename: str,
    max_folders: int,
) -> ResolvedDriveSource:
    """Find exactly one target PDF beneath the configured Drive root."""

    selector = _selector_components(pdf_subchapter_path)
    candidates = [
        source
        for source in discover_drive_sources(
            client,
            sourcepath=sourcepath,
            target_filename=target_filename,
            max_folders=max_folders,
        )
        if _path_matches(source.relative_path.split("/")[:-1], selector)
    ]

    if not candidates:
        message = (
            f"No {target_filename} was found below a folder path ending in {pdf_subchapter_path!r} "
            f"under {sourcepath}"
        )
        LOGGER.warning(message)
        raise SourceNotFound(message)
    if len(candidates) > 1:
        paths = sorted(source.relative_path for source in candidates)
        raise SourceAmbiguous(
            "More than one Google Drive PDF matches the configured target; refine pdf_subchapter_path. "
            "Candidates: " + "; ".join(paths)
        )
    return candidates[0]

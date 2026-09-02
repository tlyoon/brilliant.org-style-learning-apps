"""Idempotently provision/update the Apps Script coordinator from GitHub Actions.

This module is intentionally action-oriented: privileged Google OAuth credentials live in
GitHub Actions secrets, while worker PCs only receive a private runtime record through
Google Drive. Repeated invocations converge on one project-scoped deployment.
"""

from __future__ import annotations

import argparse
import json
import os
import secrets
import sys
import tomllib
from pathlib import Path
from typing import Any

import requests
from google.auth.transport.requests import AuthorizedSession, Request
from google.oauth2.credentials import Credentials

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from app_generator.coordinator.managed import ADMIN_SCOPES  # noqa: E402
from app_generator.coordinator.protocol import (  # noqa: E402
    ADMIN_SECRET_NAME,
    MANAGED_BY,
    MANAGED_COORDINATOR_FILE_NAME,
    REQUIRED_COORDINATOR_VERSION,
)

DRIVE_FILES = "https://www.googleapis.com/drive/v3/files"
DRIVE_UPLOAD = "https://www.googleapis.com/upload/drive/v3/files"
SCRIPT_API = "https://script.googleapis.com/v1/projects"
SHEET_MIME = "application/vnd.google-apps.spreadsheet"
FOLDER_MIME = "application/vnd.google-apps.folder"
SCRIPT_DESCRIPTION = "learning-app-content-generator managed coordinator"


def _json_response(response: Any, action: str) -> dict[str, Any]:
    try:
        response.raise_for_status()
    except Exception as exc:
        text = getattr(response, "text", "")
        raise RuntimeError(f"{action} failed: {text or exc}") from exc
    payload = response.json()
    if not isinstance(payload, dict):
        raise RuntimeError(f"{action} returned a non-object response")
    return payload


def _escape_query(value: str) -> str:
    return value.replace("\\", "\\\\").replace("'", "\\'")


def _credentials() -> Credentials:
    raw = os.environ.get(ADMIN_SECRET_NAME, "").strip()
    if not raw:
        raise RuntimeError(
            f"Missing GitHub Actions secret {ADMIN_SECRET_NAME}. Run `python -m app_generator coordinator-bootstrap` once."
        )
    try:
        info = json.loads(raw)
        credentials = Credentials.from_authorized_user_info(info, scopes=ADMIN_SCOPES)
    except Exception as exc:
        raise RuntimeError(f"{ADMIN_SECRET_NAME} is not a valid Google authorized-user token JSON") from exc
    if credentials.expired and credentials.refresh_token:
        credentials.refresh(Request())
    if not credentials.valid:
        raise RuntimeError("Coordinator administrator OAuth token is not valid or refreshable")
    return credentials


def _tracked_project_name(repo_root: Path) -> str:
    path = repo_root / "config" / "configure_project.toml"
    with path.open("rb") as handle:
        document = tomllib.load(handle)
    project = document.get("project", {})
    value = str(project.get("project_name", "")).strip()
    if not value:
        raise RuntimeError("Tracked project configuration does not contain project.project_name")
    return value


def _app_properties(project_name: str, kind: str) -> dict[str, str]:
    return {
        "managed_by": MANAGED_BY,
        "project_name": project_name,
        "resource_kind": kind,
    }


def _find_drive_resource(session: AuthorizedSession, project_name: str, kind: str) -> dict[str, Any] | None:
    query = (
        "trashed = false and "
        f"appProperties has {{ key='managed_by' and value='{_escape_query(MANAGED_BY)}' }} and "
        f"appProperties has {{ key='project_name' and value='{_escape_query(project_name)}' }} and "
        f"appProperties has {{ key='resource_kind' and value='{_escape_query(kind)}' }}"
    )
    payload = _json_response(
        session.get(
            DRIVE_FILES,
            params={
                "q": query,
                "spaces": "drive",
                "pageSize": "10",
                "fields": "files(id,name,mimeType,modifiedTime)",
            },
            timeout=60,
        ),
        f"discover Drive {kind}",
    )
    files = payload.get("files", [])
    if not isinstance(files, list):
        raise RuntimeError(f"Drive returned an invalid {kind} resource list")
    if len(files) > 1:
        raise RuntimeError(f"Multiple managed Drive resources exist for {project_name}/{kind}; refusing ambiguity")
    return files[0] if files else None


def _create_drive_resource(
    session: AuthorizedSession,
    project_name: str,
    *,
    kind: str,
    name: str,
    mime_type: str,
) -> str:
    payload = _json_response(
        session.post(
            DRIVE_FILES,
            params={"fields": "id"},
            json={
                "name": name,
                "mimeType": mime_type,
                "appProperties": _app_properties(project_name, kind),
            },
            timeout=60,
        ),
        f"create Drive {kind}",
    )
    file_id = str(payload.get("id", ""))
    if not file_id:
        raise RuntimeError(f"Drive did not return an ID for created {kind}")
    return file_id


def _ensure_drive_id(
    session: AuthorizedSession,
    project_name: str,
    *,
    kind: str,
    name: str,
    mime_type: str,
    preferred_id: str = "",
) -> str:
    if preferred_id:
        response = session.get(
            f"{DRIVE_FILES}/{preferred_id}",
            params={"fields": "id,trashed,mimeType"},
            timeout=60,
        )
        if response.status_code < 400:
            payload = response.json()
            if not payload.get("trashed") and str(payload.get("mimeType")) == mime_type:
                return preferred_id
    found = _find_drive_resource(session, project_name, kind)
    if found:
        return str(found["id"])
    return _create_drive_resource(
        session,
        project_name,
        kind=kind,
        name=name,
        mime_type=mime_type,
    )


def _read_runtime(session: AuthorizedSession, project_name: str) -> tuple[str, dict[str, Any]] | tuple[None, None]:
    found = _find_drive_resource(session, project_name, "runtime_metadata")
    if not found:
        return None, None
    file_id = str(found["id"])
    payload = _json_response(
        session.get(f"{DRIVE_FILES}/{file_id}", params={"alt": "media"}, timeout=60),
        "read managed runtime metadata",
    )
    return file_id, payload


def _write_runtime(
    session: AuthorizedSession,
    project_name: str,
    payload: dict[str, Any],
    *,
    file_id: str | None,
) -> str:
    if not file_id:
        file_id = _create_drive_resource(
            session,
            project_name,
            kind="runtime_metadata",
            name=MANAGED_COORDINATOR_FILE_NAME,
            mime_type="application/json",
        )
    response = session.patch(
        f"{DRIVE_UPLOAD}/{file_id}",
        params={"uploadType": "media"},
        headers={"Content-Type": "application/json; charset=utf-8"},
        data=(json.dumps(payload, indent=2, sort_keys=True) + "\n").encode("utf-8"),
        timeout=60,
    )
    try:
        response.raise_for_status()
    except Exception as exc:
        raise RuntimeError(f"write managed runtime metadata failed: {response.text or exc}") from exc
    return file_id


def _script_exists(session: AuthorizedSession, script_id: str) -> bool:
    if not script_id:
        return False
    response = session.get(f"{SCRIPT_API}/{script_id}", timeout=60)
    return response.status_code < 400


def _ensure_script(session: AuthorizedSession, project_name: str, preferred_id: str = "") -> str:
    if _script_exists(session, preferred_id):
        return preferred_id
    payload = _json_response(
        session.post(
            SCRIPT_API,
            json={"title": f"{project_name} Managed Coordinator"},
            timeout=60,
        ),
        "create Apps Script project",
    )
    script_id = str(payload.get("scriptId", ""))
    if not script_id:
        raise RuntimeError("Apps Script API did not return scriptId")
    return script_id


def _managed_config_source(
    *,
    project_name: str,
    spreadsheet_id: str,
    checkpoint_folder_id: str,
    worker_token: str,
) -> str:
    # Global initialization runs before doPost. The IIFE keeps the existing Script
    # Properties-based implementation compatible while making properties fully managed.
    config = {
        "PROJECT_NAME": project_name,
        "JOB_SPREADSHEET_ID": spreadsheet_id,
        "CHECKPOINT_FOLDER_ID": checkpoint_folder_id,
        "WORKER_TOKEN": worker_token,
    }
    encoded = json.dumps(config, sort_keys=True)
    return (
        "// Generated by coordinator/deployment/manage.py; do not edit in Apps Script.\n"
        f"const MANAGED_COORDINATOR_CONFIG = Object.freeze({encoded});\n"
        "const MANAGED_COORDINATOR_PROPERTIES_APPLIED = (() => {\n"
        "  PropertiesService.getScriptProperties().setProperties(MANAGED_COORDINATOR_CONFIG, false);\n"
        "  return true;\n"
        "})();\n"
    )


def _update_script_content(
    session: AuthorizedSession,
    repo_root: Path,
    *,
    script_id: str,
    project_name: str,
    spreadsheet_id: str,
    checkpoint_folder_id: str,
    worker_token: str,
) -> None:
    code = (repo_root / "coordinator" / "apps-script" / "Code.gs").read_text(encoding="utf-8")
    manifest = (repo_root / "coordinator" / "apps-script" / "appsscript.json").read_text(encoding="utf-8")
    managed = _managed_config_source(
        project_name=project_name,
        spreadsheet_id=spreadsheet_id,
        checkpoint_folder_id=checkpoint_folder_id,
        worker_token=worker_token,
    )
    _json_response(
        session.put(
            f"{SCRIPT_API}/{script_id}/content",
            json={
                "files": [
                    {"name": "Code", "type": "SERVER_JS", "source": code},
                    {"name": "ManagedConfig", "type": "SERVER_JS", "source": managed},
                    {"name": "appsscript", "type": "JSON", "source": manifest},
                ]
            },
            timeout=60,
        ),
        "update Apps Script content",
    )


def _create_version(session: AuthorizedSession, script_id: str) -> int:
    payload = _json_response(
        session.post(
            f"{SCRIPT_API}/{script_id}/versions",
            json={"description": f"managed coordinator protocol v{REQUIRED_COORDINATOR_VERSION}"},
            timeout=60,
        ),
        "create Apps Script version",
    )
    try:
        return int(payload["versionNumber"])
    except (KeyError, TypeError, ValueError) as exc:
        raise RuntimeError("Apps Script version response omitted versionNumber") from exc


def _deployment_config(script_id: str, version_number: int, project_name: str) -> dict[str, Any]:
    return {
        "scriptId": script_id,
        "versionNumber": version_number,
        "manifestFileName": "appsscript",
        "description": f"{SCRIPT_DESCRIPTION}: {project_name}",
    }


def _web_app_url(deployment: dict[str, Any]) -> str:
    for entry in deployment.get("entryPoints", []) or []:
        if isinstance(entry, dict) and str(entry.get("entryPointType", "")) == "WEB_APP":
            url = str(entry.get("webApp", {}).get("url", ""))
            if url:
                return url
    return ""


def _web_app_is_reachable(deployment: dict[str, Any]) -> bool:
    url = _web_app_url(deployment)
    if not url.startswith("https://script.google.com/macros/s/"):
        return False
    try:
        response = requests.post(url, json={}, timeout=60)
        response.raise_for_status()
        payload = response.json()
    except Exception:
        return False
    return (
        isinstance(payload, dict)
        and payload.get("ok") is False
        and payload.get("code") == "UNAUTHORIZED"
    )


def _ensure_deployment(
    session: AuthorizedSession,
    *,
    script_id: str,
    version_number: int,
    project_name: str,
    preferred_id: str = "",
) -> tuple[str, str]:
    config = _deployment_config(script_id, version_number, project_name)
    deployment: dict[str, Any] | None = None
    if preferred_id:
        response = session.put(
            f"{SCRIPT_API}/{script_id}/deployments/{preferred_id}",
            json={"deploymentConfig": config},
            timeout=60,
        )
        if response.status_code < 400:
            candidate = response.json()
            if isinstance(candidate, dict) and _web_app_is_reachable(candidate):
                deployment = candidate
    if deployment is None:
        payload = _json_response(
            session.get(f"{SCRIPT_API}/{script_id}/deployments", timeout=60),
            "list Apps Script deployments",
        )
        deployments = payload.get("deployments", [])
        if isinstance(deployments, list):
            reachable_web_apps = [
                item
                for item in deployments
                if isinstance(item, dict) and _web_app_is_reachable(item)
            ]
            matching = [
                item
                for item in reachable_web_apps
                if str(item.get("deploymentConfig", {}).get("description", "")) == config["description"]
            ]
            candidates = matching or reachable_web_apps
            if len(candidates) > 1:
                raise RuntimeError("Multiple Apps Script web-app deployments match this project")
            if candidates:
                deployment_id = str(candidates[0].get("deploymentId", ""))
                deployment = _json_response(
                    session.put(
                        f"{SCRIPT_API}/{script_id}/deployments/{deployment_id}",
                        json={"deploymentConfig": config},
                        timeout=60,
                    ),
                    "update Apps Script deployment",
                )
        if deployment is None:
            deployment = _json_response(
                session.post(
                    f"{SCRIPT_API}/{script_id}/deployments",
                    json=config,
                    timeout=60,
                ),
                "create Apps Script deployment",
            )
    deployment_id = str(deployment.get("deploymentId", ""))
    if not deployment_id:
        raise RuntimeError("Apps Script deployment response omitted deploymentId")
    url = _web_app_url(deployment)
    if not url:
        raise RuntimeError(
            "Apps Script deployment has no WEB_APP entry point; authorize the script and create one web-app "
            "deployment in the Apps Script editor, then retry"
        )
    return deployment_id, url


def ensure(repo_root: Path, project_name: str) -> dict[str, Any]:
    tracked = _tracked_project_name(repo_root)
    if project_name != tracked:
        raise RuntimeError(
            f"Workflow project_name {project_name!r} does not match tracked project.project_name {tracked!r}"
        )
    credentials = _credentials()
    session = AuthorizedSession(credentials)
    metadata_file_id, existing = _read_runtime(session, project_name)
    existing = existing or {}

    worker_token = str(existing.get("worker_token", "")) or secrets.token_urlsafe(40)
    spreadsheet_id = _ensure_drive_id(
        session,
        project_name,
        kind="job_ledger",
        name=f"{project_name} Coordinator Ledger",
        mime_type=SHEET_MIME,
        preferred_id=str(existing.get("spreadsheet_id", "")),
    )
    checkpoint_folder_id = _ensure_drive_id(
        session,
        project_name,
        kind="checkpoint_folder",
        name=f"{project_name} Auto Checkpoints",
        mime_type=FOLDER_MIME,
        preferred_id=str(existing.get("checkpoint_folder_id", "")),
    )
    script_id = _ensure_script(session, project_name, str(existing.get("script_id", "")))
    _update_script_content(
        session,
        repo_root,
        script_id=script_id,
        project_name=project_name,
        spreadsheet_id=spreadsheet_id,
        checkpoint_folder_id=checkpoint_folder_id,
        worker_token=worker_token,
    )
    version_number = _create_version(session, script_id)
    deployment_id, coordinator_url = _ensure_deployment(
        session,
        script_id=script_id,
        version_number=version_number,
        project_name=project_name,
        preferred_id=str(existing.get("deployment_id", "")),
    )
    runtime = {
        "managed_by": MANAGED_BY,
        "project_name": project_name,
        "coordinator_version": REQUIRED_COORDINATOR_VERSION,
        "coordinator_url": coordinator_url,
        "worker_token": worker_token,
        "script_id": script_id,
        "deployment_id": deployment_id,
        "script_version_number": version_number,
        "spreadsheet_id": spreadsheet_id,
        "checkpoint_folder_id": checkpoint_folder_id,
    }
    metadata_file_id = _write_runtime(
        session,
        project_name,
        runtime,
        file_id=metadata_file_id,
    )
    runtime["metadata_file_id"] = metadata_file_id
    return runtime


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("ensure",))
    parser.add_argument("--repo-root", type=Path, default=REPO_ROOT)
    parser.add_argument("--project-name", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    runtime = ensure(args.repo_root.resolve(), args.project_name)
    # Deliberately omit the worker token from logs.
    print(
        "Managed coordinator ready: "
        f"project={runtime['project_name']} version={runtime['coordinator_version']} "
        f"script_id={runtime['script_id']} deployment_id={runtime['deployment_id']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

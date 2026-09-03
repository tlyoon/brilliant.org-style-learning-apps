"""Repository-managed coordinator discovery, bootstrap, and serialized deployment."""

from __future__ import annotations

import json
import os
import re
import subprocess
import time
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, Callable

from google.auth.transport.requests import AuthorizedSession, Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

from app_generator.config import GeneratorConfig
from app_generator.coordinator.protocol import (
    ADMIN_SECRET_NAME,
    MANAGED_BY,
    MANAGED_COORDINATOR_FILE_NAME,
    MANAGED_WORKFLOW,
    REQUIRED_COORDINATOR_VERSION,
)
from app_generator.errors import CoordinatorError, DriveAuthenticationError, WrongAccountError
from app_generator.sources.google_drive import DRIVE_FILES_URL
from app_generator.sources.google_drive_auth import authorize_google_drive

ADMIN_SCOPES = (
    "openid",
    "https://www.googleapis.com/auth/script.projects",
    "https://www.googleapis.com/auth/script.deployments",
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/userinfo.email",
)


@dataclass(frozen=True)
class ManagedCoordinatorRuntime:
    project_name: str
    coordinator_version: int
    coordinator_url: str
    worker_token: str
    script_id: str
    deployment_id: str
    spreadsheet_id: str
    checkpoint_folder_id: str
    metadata_file_id: str = ""

    @classmethod
    def from_payload(cls, payload: dict[str, Any], *, file_id: str = "") -> "ManagedCoordinatorRuntime":
        try:
            return cls(
                project_name=str(payload["project_name"]),
                coordinator_version=int(payload["coordinator_version"]),
                coordinator_url=str(payload["coordinator_url"]),
                worker_token=str(payload["worker_token"]),
                script_id=str(payload["script_id"]),
                deployment_id=str(payload["deployment_id"]),
                spreadsheet_id=str(payload["spreadsheet_id"]),
                checkpoint_folder_id=str(payload["checkpoint_folder_id"]),
                metadata_file_id=file_id,
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise CoordinatorError(f"Managed coordinator metadata is incomplete: {exc}") from exc


def _management_mode(config: GeneratorConfig) -> str:
    return str(getattr(config, "coordinator_management", "external")).strip().casefold()


def _drive_query_value(value: str) -> str:
    return value.replace("\\", "\\\\").replace("'", "\\'")


def discover_managed_runtime(
    config: GeneratorConfig,
    *,
    session: Any | None = None,
) -> ManagedCoordinatorRuntime | None:
    """Read the private managed-runtime record using the worker's Drive-readonly OAuth."""

    if session is None:
        session = authorize_google_drive(config).session
    query = (
        f"name = '{_drive_query_value(MANAGED_COORDINATOR_FILE_NAME)}' and trashed = false and "
        f"appProperties has {{ key='managed_by' and value='{_drive_query_value(MANAGED_BY)}' }} and "
        f"appProperties has {{ key='project_name' and value='{_drive_query_value(config.project_name)}' }}"
    )
    try:
        response = session.get(
            DRIVE_FILES_URL,
            params={
                "q": query,
                "spaces": "drive",
                "pageSize": "10",
                "fields": "files(id,name,modifiedTime)",
            },
            timeout=config.drive_api_timeout_seconds,
        )
        response.raise_for_status()
        files = response.json().get("files", [])
    except Exception as exc:
        raise CoordinatorError(f"Could not discover managed coordinator metadata in Drive: {exc}") from exc
    if not isinstance(files, list):
        raise CoordinatorError("Google Drive returned an invalid managed coordinator file list")
    if not files:
        return None
    if len(files) > 1:
        raise CoordinatorError(
            "More than one managed coordinator metadata file exists for this project; "
            "refusing to choose an arbitrary deployment."
        )
    file_id = str(files[0].get("id", ""))
    try:
        response = session.get(
            f"{DRIVE_FILES_URL}/{file_id}",
            params={"alt": "media"},
            timeout=config.drive_api_timeout_seconds,
        )
        response.raise_for_status()
        payload = response.json()
    except Exception as exc:
        raise CoordinatorError(f"Could not read managed coordinator metadata: {exc}") from exc
    if not isinstance(payload, dict):
        raise CoordinatorError("Managed coordinator metadata is not a JSON object")
    runtime = ManagedCoordinatorRuntime.from_payload(payload, file_id=file_id)
    if runtime.project_name != config.project_name:
        raise CoordinatorError("Managed coordinator metadata belongs to another project")
    return runtime


def _apply_runtime(config: GeneratorConfig, runtime: ManagedCoordinatorRuntime) -> GeneratorConfig:
    if not runtime.coordinator_url.startswith("https://script.google.com/macros/s/"):
        raise CoordinatorError("Managed coordinator metadata contains an invalid web-app URL")
    if not runtime.worker_token:
        raise CoordinatorError("Managed coordinator metadata omitted the worker token")
    os.environ[config.coordinator_token_env] = runtime.worker_token
    return replace(config, coordinator_url=runtime.coordinator_url)


def _run_gh(config: GeneratorConfig, arguments: list[str], *, stdin_text: str | None = None) -> str:
    try:
        completed = subprocess.run(
            ["gh", *arguments],
            cwd=config.repo_root,
            input=stdin_text,
            text=True,
            encoding="utf-8",
            capture_output=True,
            check=False,
        )
    except OSError as exc:
        raise CoordinatorError(f"GitHub CLI is required for managed coordinator deployment: {exc}") from exc
    output = (completed.stdout + "\n" + completed.stderr).strip()
    if completed.returncode:
        raise CoordinatorError(f"GitHub CLI command failed: {output}")
    return output


def trigger_managed_deployment(config: GeneratorConfig) -> None:
    workflow = str(getattr(config, "coordinator_workflow", MANAGED_WORKFLOW)).strip() or MANAGED_WORKFLOW
    _run_gh(
        config,
        [
            "workflow",
            "run",
            workflow,
            "--ref",
            config.git_base_branch,
            "-f",
            f"project_name={config.project_name}",
        ],
    )


def ensure_managed_coordinator(
    config: GeneratorConfig,
    *,
    deploy_if_needed: bool = True,
    sleeper: Callable[[float], None] = time.sleep,
) -> GeneratorConfig:
    """Resolve a current managed coordinator, deploying it once through GitHub Actions if required."""

    if _management_mode(config) != "github_actions":
        return config
    runtime = discover_managed_runtime(config)
    if runtime is not None and runtime.coordinator_version >= REQUIRED_COORDINATOR_VERSION:
        return _apply_runtime(config, runtime)
    if not deploy_if_needed:
        found = runtime.coordinator_version if runtime is not None else "missing"
        raise CoordinatorError(
            f"Managed coordinator is not current (found={found}, required={REQUIRED_COORDINATOR_VERSION})"
        )

    print(
        f"COORDINATOR_ENSURE: requesting serialized GitHub Actions deployment for "
        f"{config.project_name} protocol v{REQUIRED_COORDINATOR_VERSION}."
    )
    trigger_managed_deployment(config)
    timeout = int(getattr(config, "coordinator_ensure_timeout_seconds", 600))
    deadline = time.monotonic() + timeout
    last_version: int | str = "missing"
    while time.monotonic() < deadline:
        sleeper(5.0)
        runtime = discover_managed_runtime(config)
        if runtime is None:
            last_version = "missing"
            continue
        last_version = runtime.coordinator_version
        if runtime.coordinator_version >= REQUIRED_COORDINATOR_VERSION:
            print(
                f"COORDINATOR_READY: managed deployment protocol v{runtime.coordinator_version} is available."
            )
            return _apply_runtime(config, runtime)
    raise CoordinatorError(
        "Managed coordinator deployment did not become ready before the configured timeout. "
        f"Last discovered version={last_version}. Inspect the Ensure managed coordinator workflow."
    )


def _admin_token_path(config: GeneratorConfig) -> Path:
    return config.drive_oauth_client_file.with_name("coordinator-admin-oauth-token.json")


def _load_or_authorize_admin(config: GeneratorConfig) -> Credentials:
    token_path = _admin_token_path(config)
    credentials: Credentials | None = None
    if token_path.is_file():
        try:
            credentials = Credentials.from_authorized_user_file(str(token_path), scopes=ADMIN_SCOPES)
        except Exception:
            credentials = None
    if credentials and credentials.expired and credentials.refresh_token:
        try:
            credentials.refresh(Request())
        except Exception:
            credentials = None
    if not credentials or not credentials.valid or not set(ADMIN_SCOPES).issubset(set(credentials.scopes or ())):
        if not config.drive_oauth_client_file.is_file():
            raise DriveAuthenticationError(
                f"Coordinator bootstrap requires the Google Desktop OAuth client file: {config.drive_oauth_client_file}"
            )
        flow = InstalledAppFlow.from_client_secrets_file(str(config.drive_oauth_client_file), scopes=list(ADMIN_SCOPES))
        credentials = flow.run_local_server(port=0, open_browser=True, prompt="consent")
        token_path.parent.mkdir(parents=True, exist_ok=True)
        token_path.write_text(credentials.to_json() + "\n", encoding="utf-8")
    return credentials


def _verify_admin_account(config: GeneratorConfig, credentials: Credentials) -> None:
    session = AuthorizedSession(credentials)
    try:
        response = session.get(
            "https://www.googleapis.com/drive/v3/about",
            params={"fields": "user(emailAddress)"},
            timeout=config.drive_api_timeout_seconds,
        )
        response.raise_for_status()
        email = str(response.json().get("user", {}).get("emailAddress", "")).strip().casefold()
    except Exception as exc:
        raise DriveAuthenticationError(f"Could not verify coordinator administrator account: {exc}") from exc
    if email != config.login_name.strip().casefold():
        raise WrongAccountError(
            f"Coordinator administrator account {email or '<unknown>'} does not match configured login_name {config.login_name}"
        )


def bootstrap_managed_coordinator(config: GeneratorConfig) -> GeneratorConfig:
    """One-time privileged bootstrap: authorize Google admin scopes, store them as a GitHub secret, and deploy."""

    if _management_mode(config) != "github_actions":
        raise CoordinatorError("coordinator-bootstrap requires coordinator_management='github_actions'")
    credentials = _load_or_authorize_admin(config)
    _verify_admin_account(config, credentials)
    token_json = credentials.to_json()
    _run_gh(config, ["secret", "set", ADMIN_SECRET_NAME], stdin_text=token_json)
    print(f"COORDINATOR_BOOTSTRAP: stored {ADMIN_SECRET_NAME} in GitHub Actions secrets.")
    # The deployment workflow is serialized, so concurrent workstations can safely request the same ensure operation.
    return ensure_managed_coordinator(config, deploy_if_needed=True)


def managed_status(config: GeneratorConfig) -> str:
    if _management_mode(config) != "github_actions":
        return "external"
    runtime = discover_managed_runtime(config)
    if runtime is None:
        return f"missing (required v{REQUIRED_COORDINATOR_VERSION})"
    return f"v{runtime.coordinator_version} at {runtime.coordinator_url}"

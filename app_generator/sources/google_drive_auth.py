"""Read-only installed-app OAuth for the Google Drive source resolver."""

from __future__ import annotations

import os
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app_generator.config import GeneratorConfig
from app_generator.errors import DriveAccessError, DriveAuthenticationError, WrongAccountError

DRIVE_READONLY_SCOPE = "https://www.googleapis.com/auth/drive.readonly"
DRIVE_ABOUT_URL = "https://www.googleapis.com/drive/v3/about"


@dataclass(frozen=True)
class DriveAuthorization:
    session: Any
    email: str


def _write_token_atomic(path: Path, payload: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(payload)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        try:
            os.chmod(temporary, 0o600)
        except OSError:
            pass
        os.replace(temporary, path)
    except BaseException:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
        raise


def authorize_google_drive(config: GeneratorConfig) -> DriveAuthorization:
    """Authorize Drive read-only access and verify the configured account."""

    if not config.drive_oauth_client_file.is_file():
        raise DriveAuthenticationError(
            "Google Drive OAuth client file was not found: "
            f"{config.drive_oauth_client_file}. Create a Desktop app OAuth client, download its JSON file, "
            "and set drive_oauth_client_file in generator.local.toml."
        )
    try:
        from google.auth.transport.requests import AuthorizedSession, Request
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
    except ImportError as exc:
        raise DriveAuthenticationError(
            "Google Drive authentication dependencies are missing. Run: python -m pip install -e ."
        ) from exc

    credentials = None
    try:
        if config.drive_token_file.is_file():
            credentials = Credentials.from_authorized_user_file(
                str(config.drive_token_file),
                scopes=[DRIVE_READONLY_SCOPE],
            )
        if credentials and credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())
        if not credentials or not credentials.valid:
            flow = InstalledAppFlow.from_client_secrets_file(
                str(config.drive_oauth_client_file),
                scopes=[DRIVE_READONLY_SCOPE],
            )
            print(
                "Authorize read-only Google Drive access in the browser window. "
                f"Use {config.login_name}."
            )
            credentials = flow.run_local_server(
                host="127.0.0.1",
                port=0,
                open_browser=True,
                authorization_prompt_message="Open this URL if the browser did not open:\n{url}",
                success_message="Google Drive authorization completed. You may close this tab.",
            )
        _write_token_atomic(config.drive_token_file, credentials.to_json())
        session = AuthorizedSession(credentials)
        response = session.get(
            DRIVE_ABOUT_URL,
            params={"fields": "user(emailAddress,displayName)"},
            timeout=config.drive_api_timeout_seconds,
        )
        response.raise_for_status()
        email = str(response.json().get("user", {}).get("emailAddress", "")).strip()
    except DriveAuthenticationError:
        raise
    except Exception as exc:
        raise DriveAuthenticationError(f"Google Drive OAuth authorization failed: {exc}") from exc

    if not email:
        raise DriveAccessError("Google Drive did not return the authorized account email")
    if email.casefold() != config.login_name.casefold():
        raise WrongAccountError(
            f"Google Drive is authorized as {email}, but generator.local.toml expects {config.login_name}. "
            f"Delete {config.drive_token_file} and authorize the expected account."
        )
    return DriveAuthorization(session=session, email=email)

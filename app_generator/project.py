"""Project identity and project-derived machine-local paths."""

from __future__ import annotations

import os
import re
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping


PROJECT_NAME_PATTERN = re.compile(r"^[A-Za-z][A-Za-z0-9._-]{0,63}$")
_CAMEL_BOUNDARY = re.compile(r"(?<=[a-z0-9])(?=[A-Z])")
_NON_ALPHANUMERIC = re.compile(r"[^A-Za-z0-9]+")


class ProjectIdentityError(ValueError):
    """The repository project identity is missing or unsafe."""


@dataclass(frozen=True)
class ProjectIdentity:
    """Canonical project name plus values deterministically derived from it."""

    name: str
    env_prefix: str
    state_root: Path

    @property
    def slug(self) -> str:
        return project_slug(self.name)

    @property
    def settings_path(self) -> Path:
        return self.state_root / "workstation-sync.toml"

    @property
    def oauth_client_file(self) -> Path:
        return self.state_root / "credentials" / "drive-oauth-client.json"

    @property
    def oauth_token_file(self) -> Path:
        return self.state_root / "credentials" / "drive-oauth-token.json"

    @property
    def chrome_profile_dir(self) -> Path:
        return self.state_root / "chrome-profile"

    @property
    def runs_dir(self) -> Path:
        return self.state_root / "runs"

    def tokens(self, *, repo_root: Path) -> dict[str, str]:
        return {
            "${PROJECT_NAME}": self.name,
            "${PROJECT_SLUG}": self.slug,
            "${PROJECT_ENV_PREFIX}": self.env_prefix,
            "${STATE_ROOT}": self.state_root.resolve().as_posix(),
            "${REPO_ROOT}": repo_root.resolve().as_posix(),
        }


def validate_project_name(value: object) -> str:
    name = str(value).strip()
    if not PROJECT_NAME_PATTERN.fullmatch(name):
        raise ProjectIdentityError(
            "project.project_name must start with a letter and contain only letters, "
            "digits, '.', '_' or '-'"
        )
    return name


def environment_prefix(project_name: str) -> str:
    """Convert a project name to an uppercase environment-variable namespace."""

    name = validate_project_name(project_name)
    separated = _CAMEL_BOUNDARY.sub("_", name)
    prefix = _NON_ALPHANUMERIC.sub("_", separated).strip("_").upper()
    if not prefix or not prefix[0].isalpha():
        raise ProjectIdentityError("project.project_name cannot produce a safe environment prefix")
    return prefix


def project_slug(project_name: str) -> str:
    """Convert a project name to a lowercase kebab-case identifier prefix."""

    name = validate_project_name(project_name)
    separated = _CAMEL_BOUNDARY.sub("-", name)
    slug = _NON_ALPHANUMERIC.sub("-", separated).strip("-").casefold()
    if not slug:
        raise ProjectIdentityError("project.project_name cannot produce a safe project slug")
    return slug


def state_root_for(
    project_name: str,
    *,
    environ: Mapping[str, str] | None = None,
    home: Path | None = None,
) -> Path:
    env = os.environ if environ is None else environ
    local_app_data = str(env.get("LOCALAPPDATA", "")).strip()
    if local_app_data:
        return Path(local_app_data).expanduser() / validate_project_name(project_name)
    base = Path.home() if home is None else home
    return base.expanduser() / ".local" / "state" / validate_project_name(project_name)


def identity_from_payload(
    payload: Mapping[str, Any],
    *,
    environ: Mapping[str, str] | None = None,
    home: Path | None = None,
) -> ProjectIdentity:
    project = payload.get("project")
    if not isinstance(project, Mapping):
        raise ProjectIdentityError("Project configuration must contain a [project] table")
    name = validate_project_name(project.get("project_name", ""))
    return ProjectIdentity(
        name=name,
        env_prefix=environment_prefix(name),
        state_root=state_root_for(name, environ=environ, home=home),
    )


def load_project_identity(
    path: Path,
    *,
    environ: Mapping[str, str] | None = None,
    home: Path | None = None,
) -> ProjectIdentity:
    try:
        with path.open("rb") as handle:
            payload = tomllib.load(handle)
    except (OSError, tomllib.TOMLDecodeError) as exc:
        raise ProjectIdentityError(f"Could not read project configuration {path}: {exc}") from exc
    return identity_from_payload(payload, environ=environ, home=home)

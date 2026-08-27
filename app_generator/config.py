"""Configuration loading with CLI > environment > TOML > defaults precedence."""

from __future__ import annotations

import os
import re
import socket
import tomllib
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, Mapping
from urllib.parse import urlparse

from app_generator.errors import ConfigurationError, RepositoryCompatibilityError
from app_generator.project import ProjectIdentityError, environment_prefix, validate_project_name

PACKAGE_ID = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
CONTENT_DIR = re.compile(r"^(?:chapter|section)-[a-z0-9-]+$")
SUBCHAPTER_ID = re.compile(r"^(?P<chapter>[1-9][0-9]*)\.(?P<section>[1-9][0-9]*)$")
BRANCH_PREFIX = re.compile(r"^[a-z0-9][a-z0-9._/-]*$")


DEFAULTS: dict[str, Any] = {
    "gem_edit_url": "",
    "browser_mode": "controlled",
    "debugger_address": "",
    "max_repair_attempts": 4,
    "ui_timeout_seconds": 30,
    "login_timeout_seconds": 300,
    "response_timeout_seconds": 600,
    "max_gemini_session_restarts": 2,
    "drive_api_timeout_seconds": 60,
    "max_drive_folders": 10000,
    "log_level": "INFO",
    "selection_mode": "specific",
    "worker_id": socket.gethostname().casefold(),
    "coordinator_url": "",
    "coordinator_timeout_seconds": 30,
    "lease_seconds": 3600,
    "heartbeat_seconds": 300,
    "max_job_attempts": 3,
    "git_publish": False,
    "git_remote": "origin",
    "git_base_branch": "main",
    "git_branch_prefix": "automation",
    "git_create_draft_pr": True,
    "git_run_full_tests": True,
    "model_preference_patterns": [
        r"\bpro\b|most capable|highest capability|advanced reasoning",
        r"advanced|reasoning|high capability",
        r"\bflash\b|fast",
    ],
    "allow_unknown_model_fallback": True,
}

ALIASES = {
    "gemini-gem": "gem_url",
    "loginname": "login_name",
}


@dataclass(frozen=True)
class GeneratorConfig:
    project_name: str
    env_prefix: str
    gem_url: str
    gem_edit_url: str
    gem_name: str
    login_name: str
    browser_mode: str
    debugger_address: str
    chrome_profile_dir: Path
    state_dir: Path
    repo_root: Path
    source_files: tuple[Path, ...]
    sourcepath: str
    pdf_subchapter_path: str
    target_filename: str
    target_file: str
    drive_oauth_client_file: Path
    drive_token_file: Path
    drive_api_timeout_seconds: int
    max_drive_folders: int
    package_id: str
    chapter: str
    subchapter: str
    chapter_dir: str
    section_dir: str
    learning_boundary: str
    source_id: str
    edition: str
    heading: str
    page_range: str
    reviewer: str
    rights_note: str
    drive_file_id: str | None
    existing_source_manifest: Path | None
    max_repair_attempts: int
    ui_timeout_seconds: int
    login_timeout_seconds: int
    response_timeout_seconds: int
    max_gemini_session_restarts: int
    log_level: str
    model_preference_patterns: tuple[str, ...]
    allow_unknown_model_fallback: bool
    selection_mode: str
    worker_id: str
    coordinator_url: str
    coordinator_token_env: str
    coordinator_timeout_seconds: int
    lease_seconds: int
    heartbeat_seconds: int
    max_job_attempts: int
    git_publish: bool
    git_remote: str
    git_base_branch: str
    git_branch_prefix: str
    git_create_draft_pr: bool
    git_run_full_tests: bool

    @property
    def output_dir(self) -> Path:
        return self.repo_root / "content" / self.chapter_dir / self.section_dir

    @property
    def package_path(self) -> Path:
        return self.output_dir / "package.json"

    @property
    def manifest_relative_path(self) -> Path:
        return Path("content") / "source-manifests" / f"{self.package_id}.json"

    @property
    def review_relative_path(self) -> Path:
        return Path("content") / self.chapter_dir / self.section_dir / "review-record.md"

    @property
    def learning_design_relative_path(self) -> Path:
        return Path("content") / self.chapter_dir / self.section_dir / "learning-design.md"

    @property
    def uses_google_drive(self) -> bool:
        return not self.source_files

    @property
    def target_locator(self) -> str:
        return self.target_file.format(
            sourcepath=self.sourcepath.rstrip("/"),
            pdf_subchapter_path=self.pdf_subchapter_path.strip("/\\"),
            target_filename=self.target_filename,
        )

    def for_subchapter(self, subchapter_id: str) -> "GeneratorConfig":
        """Materialize run-metadata templates for a claimed Drive subchapter."""

        values = _run_template_values(self.__dict__, subchapter_id)
        package_id = values["package_id"]
        chapter_dir = values["chapter_dir"]
        section_dir = values["section_dir"]
        _validate_output_identifiers(package_id, chapter_dir, section_dir)
        return replace(
            self,
            pdf_subchapter_path=subchapter_id,
            package_id=package_id,
            chapter=values["chapter"],
            subchapter=values["subchapter"],
            chapter_dir=chapter_dir,
            section_dir=section_dir,
            learning_boundary=values["learning_boundary"],
            source_id=values["source_id"],
            heading=values["heading"],
            page_range=values["page_range"],
        )


def _flatten(document: Mapping[str, Any]) -> dict[str, Any]:
    flat: dict[str, Any] = {}
    for key, value in document.items():
        if isinstance(value, Mapping):
            for child_key, child_value in value.items():
                if child_key in flat:
                    raise ConfigurationError(f"Duplicate configuration key: {child_key}")
                flat[child_key] = child_value
        else:
            flat[key] = value
    return flat


def _coerce_env(key: str, value: str) -> Any:
    if key in {
        "max_repair_attempts",
        "ui_timeout_seconds",
        "login_timeout_seconds",
        "response_timeout_seconds",
        "max_gemini_session_restarts",
        "drive_api_timeout_seconds",
        "max_drive_folders",
        "coordinator_timeout_seconds",
        "lease_seconds",
        "heartbeat_seconds",
        "max_job_attempts",
    }:
        return int(value)
    if key in {"allow_unknown_model_fallback", "git_publish", "git_create_draft_pr", "git_run_full_tests"}:
        return value.strip().casefold() in {"1", "true", "yes", "on"}
    if key in {"source_files", "model_preference_patterns"}:
        return [item for item in value.split(os.pathsep) if item]
    return value


def _required(values: Mapping[str, Any], key: str) -> Any:
    value = values.get(key)
    if value is None or (isinstance(value, str) and not value.strip()):
        raise ConfigurationError(f"Missing required configuration value: {key}")
    return value


def _validate_gemini_url(value: str, key: str) -> str:
    parsed = urlparse(value)
    if parsed.scheme != "https" or parsed.hostname != "gemini.google.com":
        raise ConfigurationError(f"{key} must be an https://gemini.google.com URL")
    return value


def _normalize_aliases(values: Mapping[str, Any]) -> dict[str, Any]:
    normalized = dict(values)
    for alias, canonical in ALIASES.items():
        if alias not in normalized:
            continue
        if canonical in normalized and normalized[canonical] != normalized[alias]:
            raise ConfigurationError(f"Conflicting configuration values: {alias} and {canonical}")
        normalized[canonical] = normalized.pop(alias)
    return normalized


def _is_within(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def _run_template_values(values: Mapping[str, Any], subchapter_id: str) -> dict[str, str]:
    match = SUBCHAPTER_ID.fullmatch(subchapter_id.strip())
    if not match:
        raise ConfigurationError("A source subchapter folder must look like 8.1")
    context = {
        "chapter_number": match.group("chapter"),
        "section_number": match.group("section"),
        "subchapter_id": subchapter_id.strip(),
        "section_slug": subchapter_id.strip().replace(".", "-"),
    }
    fields = (
        "package_id", "chapter", "subchapter", "chapter_dir", "section_dir",
        "learning_boundary", "source_id", "heading", "page_range",
    )
    rendered: dict[str, str] = {}
    for field in fields:
        raw = str(_required(values, field))
        try:
            rendered[field] = raw.format_map(context).strip()
        except (KeyError, ValueError) as exc:
            raise ConfigurationError(f"{field} contains an invalid template placeholder: {exc}") from exc
        if not rendered[field]:
            raise ConfigurationError(f"{field} resolves to an empty value")
    return rendered


def _validate_output_identifiers(package_id: str, chapter_dir: str, section_dir: str) -> None:
    if not PACKAGE_ID.fullmatch(package_id):
        raise ConfigurationError("package_id must resolve to lowercase kebab-case")
    if not CONTENT_DIR.fullmatch(chapter_dir) or not chapter_dir.startswith("chapter-"):
        raise ConfigurationError("chapter_dir must resolve to a value such as chapter-8")
    if not CONTENT_DIR.fullmatch(section_dir) or not section_dir.startswith("section-"):
        raise ConfigurationError("section_dir must resolve to a value such as section-8-1")


def load_config(
    config_path: Path,
    *,
    cli_overrides: Mapping[str, Any] | None = None,
    environ: Mapping[str, str] | None = None,
) -> GeneratorConfig:
    if not config_path.is_file():
        raise ConfigurationError(f"Configuration file does not exist: {config_path}")
    with config_path.open("rb") as handle:
        file_values = _normalize_aliases(_flatten(tomllib.load(handle)))
    try:
        project_name = validate_project_name(_required(file_values, "project_name"))
        env_prefix = f"{environment_prefix(project_name)}_GENERATOR_"
    except ProjectIdentityError as exc:
        raise ConfigurationError(str(exc)) from exc
    values = {**DEFAULTS, **file_values}
    env = environ if environ is not None else os.environ
    for name, raw in env.items():
        if name.startswith(env_prefix):
            key = name.removeprefix(env_prefix).lower()
            values[key] = _coerce_env(key, raw)
    values.update({key: value for key, value in (cli_overrides or {}).items() if value is not None})

    for required_key in (
        "gem_url", "gem_name", "login_name", "chrome_profile_dir", "state_dir",
        "sourcepath", "pdf_subchapter_path", "target_filename", "target_file",
        "drive_oauth_client_file", "drive_token_file", "coordinator_token_env",
    ):
        _required(values, required_key)

    repo_root = Path(_required(values, "repo_root")).expanduser().resolve()
    raw_sources = values.get("source_files", [])
    if not isinstance(raw_sources, (list, tuple)):
        raise ConfigurationError("source_files must be a TOML array or path-separated environment value")
    source_files = tuple(Path(item).expanduser().resolve() for item in raw_sources)
    if len(source_files) > 1:
        raise RepositoryCompatibilityError(
            "The current source-manifest schema supports exactly one PDF per generated package. "
            "Use one source file or approve a versioned schema change before using multiple PDFs."
        )
    for source in source_files:
        if source.suffix.casefold() != ".pdf" or not source.is_file():
            raise ConfigurationError(f"Configured source is not an existing PDF: {source}")
    if not (repo_root / "AGENTS.md").is_file() or not (repo_root / "content" / "schema").is_dir():
        raise ConfigurationError(f"repo_root is not a compatible repository checkout: {repo_root}")

    sourcepath = str(_required(values, "sourcepath")).strip()
    parsed_source = urlparse(sourcepath)
    if parsed_source.scheme != "https" or parsed_source.hostname != "drive.google.com":
        raise ConfigurationError("sourcepath must be an https://drive.google.com folder URL")
    pdf_subchapter_path = str(_required(values, "pdf_subchapter_path")).strip().replace("\\", "/")
    components = [part for part in pdf_subchapter_path.split("/") if part]
    if not components or any(part in {".", ".."} for part in components):
        raise ConfigurationError("pdf_subchapter_path must contain one or more safe folder names")
    target_filename = str(_required(values, "target_filename")).strip()
    if Path(target_filename).name != target_filename or not target_filename.casefold().endswith(".pdf"):
        raise ConfigurationError("target_filename must be a PDF basename such as source.pdf")
    target_file = str(_required(values, "target_file")).strip()
    try:
        target_file.format(
            sourcepath=sourcepath.rstrip("/"),
            pdf_subchapter_path=pdf_subchapter_path,
            target_filename=target_filename,
        )
    except (KeyError, ValueError) as exc:
        raise ConfigurationError(f"target_file contains an invalid placeholder: {exc}") from exc

    rendered = _run_template_values(values, pdf_subchapter_path.split("/")[-1])
    _validate_output_identifiers(rendered["package_id"], rendered["chapter_dir"], rendered["section_dir"])

    browser_mode = str(values["browser_mode"]).casefold()
    if browser_mode not in {"controlled", "attach"}:
        raise ConfigurationError("browser_mode must be controlled or attach")
    debugger_address = str(values.get("debugger_address", ""))
    if browser_mode == "attach" and not debugger_address:
        raise ConfigurationError("debugger_address is required in attach mode")
    chrome_profile_dir = Path(values["chrome_profile_dir"]).expanduser().resolve()
    if chrome_profile_dir.name.casefold() == "user data":
        raise ConfigurationError("Use a dedicated non-default Chrome profile directory")

    existing = values.get("existing_source_manifest")
    existing_path = Path(existing).expanduser().resolve() if existing else None
    if existing_path and not existing_path.is_file():
        raise ConfigurationError(f"Existing source manifest does not exist: {existing_path}")

    max_repair_attempts = int(values["max_repair_attempts"])
    if max_repair_attempts < 0:
        raise ConfigurationError("max_repair_attempts must be zero or greater")
    max_gemini_session_restarts = int(values["max_gemini_session_restarts"])
    if max_gemini_session_restarts < 0:
        raise ConfigurationError("max_gemini_session_restarts must be zero or greater")
    for pattern in values["model_preference_patterns"]:
        try:
            re.compile(str(pattern), re.I)
        except re.error as exc:
            raise ConfigurationError(f"Invalid model preference pattern {pattern!r}: {exc}") from exc

    state_dir = Path(values["state_dir"]).expanduser().resolve()
    drive_oauth_client_file = Path(values["drive_oauth_client_file"]).expanduser().resolve()
    drive_token_file = Path(values["drive_token_file"]).expanduser().resolve()
    if _is_within(state_dir, repo_root):
        raise ConfigurationError("state_dir must be outside the repository so run data and PDFs cannot enter Git")
    if _is_within(drive_oauth_client_file, repo_root) or _is_within(drive_token_file, repo_root):
        raise ConfigurationError("Google OAuth client and token files must be stored outside the repository")
    drive_api_timeout_seconds = int(values["drive_api_timeout_seconds"])
    max_drive_folders = int(values["max_drive_folders"])
    if drive_api_timeout_seconds < 1 or max_drive_folders < 1:
        raise ConfigurationError("Drive timeout and folder limit must be positive integers")

    selection_mode = str(values["selection_mode"]).strip().casefold()
    if selection_mode not in {"specific", "distributed"}:
        raise ConfigurationError("selection_mode must be specific or distributed")
    coordinator_url = str(values.get("coordinator_url", "")).strip()
    if selection_mode == "distributed":
        parsed_coordinator = urlparse(coordinator_url)
        if parsed_coordinator.scheme != "https" or parsed_coordinator.hostname not in {
            "script.google.com", "script.googleusercontent.com",
        }:
            raise ConfigurationError(
                "Distributed mode requires an HTTPS Google Apps Script coordinator_url"
            )
        if source_files:
            raise ConfigurationError("Distributed mode discovers its source jobs from Google Drive")
        if not bool(values["git_publish"]):
            raise ConfigurationError("Distributed mode requires git_publish=true so a claimed job is durably handed off")
    coordinator_timeout_seconds = int(values["coordinator_timeout_seconds"])
    lease_seconds = int(values["lease_seconds"])
    heartbeat_seconds = int(values["heartbeat_seconds"])
    max_job_attempts = int(values["max_job_attempts"])
    if min(coordinator_timeout_seconds, lease_seconds, heartbeat_seconds, max_job_attempts) < 1:
        raise ConfigurationError("Coordinator timeout, lease, heartbeat, and attempt values must be positive")
    if heartbeat_seconds * 2 >= lease_seconds:
        raise ConfigurationError("heartbeat_seconds must be less than half of lease_seconds")
    worker_id = re.sub(r"[^a-z0-9._-]+", "-", str(values["worker_id"]).strip().casefold()).strip("-")
    if not worker_id:
        raise ConfigurationError("worker_id must contain at least one safe character")
    coordinator_token_env = str(values["coordinator_token_env"]).strip()
    if not re.fullmatch(r"[A-Z_][A-Z0-9_]*", coordinator_token_env):
        raise ConfigurationError("coordinator_token_env must be an uppercase environment-variable name")
    branch_prefix = str(values["git_branch_prefix"]).strip().strip("/")
    if not BRANCH_PREFIX.fullmatch(branch_prefix) or ".." in branch_prefix:
        raise ConfigurationError("git_branch_prefix is not a safe Git branch prefix")

    return GeneratorConfig(
        project_name=project_name,
        env_prefix=env_prefix,
        gem_url=_validate_gemini_url(str(values["gem_url"]), "gem_url"),
        gem_edit_url=(
            _validate_gemini_url(str(values["gem_edit_url"]), "gem_edit_url")
            if str(values.get("gem_edit_url", "")).strip()
            else ""
        ),
        gem_name=str(values["gem_name"]).strip(),
        login_name=str(values["login_name"]).strip(),
        browser_mode=browser_mode,
        debugger_address=debugger_address,
        chrome_profile_dir=chrome_profile_dir,
        state_dir=state_dir,
        repo_root=repo_root,
        source_files=source_files,
        sourcepath=sourcepath,
        pdf_subchapter_path=pdf_subchapter_path,
        target_filename=target_filename,
        target_file=target_file,
        drive_oauth_client_file=drive_oauth_client_file,
        drive_token_file=drive_token_file,
        drive_api_timeout_seconds=drive_api_timeout_seconds,
        max_drive_folders=max_drive_folders,
        package_id=str(_required(values, "package_id")).strip(),
        chapter=str(_required(values, "chapter")).strip(),
        subchapter=str(_required(values, "subchapter")).strip(),
        chapter_dir=str(_required(values, "chapter_dir")).strip(),
        section_dir=str(_required(values, "section_dir")).strip(),
        learning_boundary=str(_required(values, "learning_boundary")).strip(),
        source_id=str(_required(values, "source_id")).strip(),
        edition=str(_required(values, "edition")).strip(),
        heading=str(_required(values, "heading")).strip(),
        page_range=str(_required(values, "page_range")).strip(),
        reviewer=str(_required(values, "reviewer")).strip(),
        rights_note=str(_required(values, "rights_note")).strip(),
        drive_file_id=str(values["drive_file_id"]).strip() if values.get("drive_file_id") else None,
        existing_source_manifest=existing_path,
        max_repair_attempts=max_repair_attempts,
        ui_timeout_seconds=int(values["ui_timeout_seconds"]),
        login_timeout_seconds=int(values["login_timeout_seconds"]),
        response_timeout_seconds=int(values["response_timeout_seconds"]),
        max_gemini_session_restarts=max_gemini_session_restarts,
        log_level=str(values["log_level"]).upper(),
        model_preference_patterns=tuple(str(item) for item in values["model_preference_patterns"]),
        allow_unknown_model_fallback=bool(values["allow_unknown_model_fallback"]),
        selection_mode=selection_mode,
        worker_id=worker_id,
        coordinator_url=coordinator_url,
        coordinator_token_env=coordinator_token_env,
        coordinator_timeout_seconds=coordinator_timeout_seconds,
        lease_seconds=lease_seconds,
        heartbeat_seconds=heartbeat_seconds,
        max_job_attempts=max_job_attempts,
        git_publish=bool(values["git_publish"]),
        git_remote=str(values["git_remote"]).strip(),
        git_base_branch=str(values["git_base_branch"]).strip(),
        git_branch_prefix=branch_prefix,
        git_create_draft_pr=bool(values["git_create_draft_pr"]),
        git_run_full_tests=bool(values["git_run_full_tests"]),
    )

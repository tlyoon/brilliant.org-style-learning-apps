#!/usr/bin/env python3
"""Safely synchronize and validate a Windows generator workstation."""

from __future__ import annotations

import argparse
import hashlib
import os
import re
import shutil
import subprocess
import sys
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Mapping

from app_generator.project import (
    ProjectIdentity,
    ProjectIdentityError,
    identity_from_payload,
    load_project_identity,
    state_root_for,
    validate_project_name,
)


ROOT = Path(__file__).resolve().parents[1]
BRANCH = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._/-]*$")
REMOTE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
MAX_PROJECT_CONFIG_BYTES = 256 * 1024
PROJECT_CONFIG_RELATIVE_PATH = Path("config") / "project.toml"
MANAGED_CONFIG_HEADER = (
    "# Managed by scripts/sync_workstation.py; edit config/project.toml through Git.\n"
)
ALLOWED_PROJECT_KEYS = {
    "project": {"project_name"},
    "placeholders": {
        "sourcepath", "gemini-gem", "loginname", "pdf_subchapter_path",
        "target_filename", "target_file",
    },
    "gemini": {"gem_edit_url", "gem_name", "browser_mode"},
    "google_drive": {"drive_api_timeout_seconds", "max_drive_folders"},
    "automation": {
        "selection_mode", "coordinator_url", "coordinator_token_env",
        "coordinator_timeout_seconds", "lease_seconds", "heartbeat_seconds",
        "max_job_attempts",
    },
    "repository": {"repo_root"},
    "paths": {
        "state_root", "workstation_settings", "drive_oauth_client_file",
        "drive_token_file", "chrome_profile_dir", "state_dir",
    },
    "run": {
        "package_id", "chapter", "subchapter", "chapter_dir", "section_dir",
        "learning_boundary", "source_id", "edition", "heading", "page_range",
        "reviewer", "rights_note", "drive_file_id", "existing_source_manifest",
    },
    "limits": {
        "max_repair_attempts", "ui_timeout_seconds", "login_timeout_seconds",
        "response_timeout_seconds", "max_gemini_session_restarts", "log_level",
    },
    "git": {
        "git_publish", "git_remote", "git_base_branch", "git_branch_prefix",
        "git_create_draft_pr", "git_run_full_tests",
    },
    "models": {"model_preference_patterns", "allow_unknown_model_fallback"},
}


class WorkstationSyncError(RuntimeError):
    """A safe synchronization precondition or operation failed."""


@dataclass(frozen=True)
class SyncSettings:
    settings_path: Path
    repo_root: Path
    remote: str
    branch: str
    project_name: str
    env_prefix: str
    state_root: Path
    project_config_file: Path
    login_name: str
    oauth_client_file: Path
    oauth_token_file: Path
    generated_config_file: Path
    run_tests: bool
    run_doctor: bool


CommandRunner = Callable[[list[str], Path], str]


def _state_root(project_name: str) -> Path:
    return state_root_for(project_name)


def _default_settings_path(project_name: str) -> Path:
    return _state_root(project_name) / "workstation-sync.toml"


def _toml_string(value: str) -> str:
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def _write_initial_settings(
    path: Path,
    *,
    login_name: str,
    branch: str,
    project_name: str,
) -> None:
    state = _state_root(project_name)
    content = "\n".join(
        (
            "# Machine-local, non-secret workstation synchronization settings.",
            "[project]",
            f"project_name = {_toml_string(project_name)}",
            "",
            "[repository]",
            'remote = "origin"',
            f"branch = {_toml_string(branch)}",
            "",
            "[drive]",
            f"login_name = {_toml_string(login_name)}",
            f"oauth_client_file = {_toml_string(str(state / 'credentials' / 'drive-oauth-client.json'))}",
            f"oauth_token_file = {_toml_string(str(state / 'credentials' / 'drive-oauth-token.json'))}",
            "",
            "[output]",
            'generated_config_file = "project.local.toml"',
            "",
            "[checks]",
            "run_tests = true",
            "run_doctor = true",
            "",
        )
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".part")
    temporary.write_text(content, encoding="utf-8")
    os.replace(temporary, path)


def _read_table(payload: Mapping[str, Any], name: str) -> Mapping[str, Any]:
    value = payload.get(name, {})
    if not isinstance(value, Mapping):
        raise WorkstationSyncError(f"[{name}] must be a TOML table in the workstation settings")
    return value


def _expand_path(value: str) -> Path:
    return Path(os.path.expandvars(value)).expanduser().resolve()


def load_settings(
    path: Path,
    *,
    repo_root: Path = ROOT,
    project_name: str,
) -> SyncSettings:
    try:
        with path.open("rb") as handle:
            payload = tomllib.load(handle)
    except (OSError, tomllib.TOMLDecodeError) as exc:
        raise WorkstationSyncError(f"Could not read workstation settings {path}: {exc}") from exc
    settings_project = _read_table(payload, "project")
    recorded_name = str(settings_project.get("project_name", project_name)).strip()
    if recorded_name != project_name:
        raise WorkstationSyncError(
            f"Workstation settings belong to {recorded_name!r}, not {project_name!r}"
        )
    repository = _read_table(payload, "repository")
    drive = _read_table(payload, "drive")
    output = _read_table(payload, "output")
    checks = _read_table(payload, "checks")
    remote = str(repository.get("remote", "origin")).strip()
    branch = str(repository.get("branch", "main")).strip()
    if not REMOTE.fullmatch(remote):
        raise WorkstationSyncError(f"Unsafe Git remote name: {remote!r}")
    if not BRANCH.fullmatch(branch) or ".." in branch or branch.endswith("/"):
        raise WorkstationSyncError(f"Unsafe Git branch name: {branch!r}")
    login_name = str(drive.get("login_name", "")).strip()
    if not login_name:
        raise WorkstationSyncError("Drive login_name is required")
    identity = ProjectIdentity(
        name=validate_project_name(project_name),
        env_prefix=identity_from_payload({"project": {"project_name": project_name}}).env_prefix,
        state_root=_state_root(project_name),
    )
    state = identity.state_root
    oauth_client = _expand_path(
        str(drive.get("oauth_client_file", state / "credentials" / "drive-oauth-client.json"))
    )
    oauth_token = _expand_path(
        str(drive.get("oauth_token_file", state / "credentials" / "drive-oauth-token.json"))
    )
    for credential_path in (oauth_client, oauth_token):
        try:
            credential_path.relative_to(repo_root.resolve())
        except ValueError:
            pass
        else:
            raise WorkstationSyncError("OAuth client and token paths must remain outside the repository")
    output_name = str(output.get("generated_config_file", "project.local.toml")).strip()
    if Path(output_name).name != output_name or not re.fullmatch(
        r"(?:project|generator.*)\.local.*\.toml", output_name
    ):
        raise WorkstationSyncError(
            "generated_config_file must be an ignored project.local*.toml basename"
        )
    generated = (repo_root / output_name).resolve()
    if generated.parent != repo_root.resolve():
        raise WorkstationSyncError("The generated configuration must remain in the repository root")
    project_config = (repo_root / PROJECT_CONFIG_RELATIVE_PATH).resolve()
    return SyncSettings(
        settings_path=path.resolve(),
        repo_root=repo_root.resolve(),
        remote=remote,
        branch=branch,
        project_name=identity.name,
        env_prefix=identity.env_prefix,
        state_root=identity.state_root.resolve(),
        project_config_file=project_config,
        login_name=login_name,
        oauth_client_file=oauth_client,
        oauth_token_file=oauth_token,
        generated_config_file=generated,
        run_tests=bool(checks.get("run_tests", True)),
        run_doctor=bool(checks.get("run_doctor", True)),
    )


def _command(arguments: list[str], cwd: Path) -> str:
    try:
        result = subprocess.run(
            arguments,
            cwd=cwd,
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
    except OSError as exc:
        raise WorkstationSyncError(f"Could not execute {arguments[0]}: {exc}") from exc
    output = (result.stdout + "\n" + result.stderr).strip()
    if result.returncode:
        raise WorkstationSyncError(f"Command failed ({' '.join(arguments)}):\n{output}")
    return output


def sync_repository(settings: SyncSettings, *, runner: CommandRunner = _command) -> str:
    repo = settings.repo_root
    if not (repo / ".git").exists():
        raise WorkstationSyncError(f"Not a Git checkout: {repo}")
    if runner(["git", "status", "--porcelain", "--untracked-files=all"], repo):
        raise WorkstationSyncError(
            "The repository has local changes. Commit, stash, or remove them before synchronization."
        )
    remote = settings.remote
    branch = settings.branch
    runner(["git", "fetch", remote, "--prune"], repo)
    remote_ref = f"refs/remotes/{remote}/{branch}"
    runner(["git", "rev-parse", "--verify", remote_ref], repo)
    current = runner(["git", "branch", "--show-current"], repo).strip()
    if current != branch:
        try:
            runner(["git", "rev-parse", "--verify", f"refs/heads/{branch}"], repo)
        except WorkstationSyncError:
            runner(["git", "switch", "--track", "-c", branch, f"{remote}/{branch}"], repo)
        else:
            runner(["git", "switch", branch], repo)
    counts = runner(
        ["git", "rev-list", "--left-right", "--count", f"HEAD...{remote}/{branch}"], repo
    ).split()
    if len(counts) != 2 or not all(item.isdigit() for item in counts):
        raise WorkstationSyncError("Git returned an unexpected ahead/behind count")
    ahead, behind = (int(item) for item in counts)
    if ahead:
        raise WorkstationSyncError(
            f"Local {branch} has {ahead} commit(s) not on {remote}/{branch}; refusing to overwrite or reset them."
        )
    if behind:
        runner(["git", "merge", "--ff-only", f"{remote}/{branch}"], repo)
    local_commit = runner(["git", "rev-parse", "HEAD"], repo).strip()
    remote_commit = runner(["git", "rev-parse", f"{remote}/{branch}"], repo).strip()
    if not local_commit or local_commit != remote_commit:
        raise WorkstationSyncError("Local and remote commit IDs still differ after synchronization")
    return local_commit


def _venv_python(repo_root: Path) -> Path:
    if os.name == "nt":
        return repo_root / ".venv" / "Scripts" / "python.exe"
    return repo_root / ".venv" / "bin" / "python"


def prepare_environment(settings: SyncSettings) -> Path:
    python = _venv_python(settings.repo_root)
    if not python.is_file():
        if sys.version_info[:2] != (3, 12):
            raise WorkstationSyncError("Python 3.12 is required to create .venv")
        print("Creating the Python 3.12 virtual environment...")
        _command([sys.executable, "-m", "venv", str(settings.repo_root / ".venv")], settings.repo_root)
    version = _command(
        [str(python), "-c", "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"],
        settings.repo_root,
    ).strip()
    if version != "3.12":
        raise WorkstationSyncError(f"Existing .venv uses Python {version}; Python 3.12 is required")
    print("Installing the synchronized package into .venv...")
    _command([str(python), "-m", "pip", "install", "-e", "."], settings.repo_root)
    return python


def _validate_project_tables(payload: Mapping[str, Any]) -> None:
    required = {"project", "placeholders", "repository", "paths"}
    missing_sections = required - set(payload)
    if missing_sections:
        raise WorkstationSyncError(
            "Project configuration is missing required section(s): "
            + ", ".join(sorted(missing_sections))
        )
    unknown_sections = set(payload) - set(ALLOWED_PROJECT_KEYS)
    if unknown_sections:
        raise WorkstationSyncError(
            "Project configuration contains unsupported section(s): "
            + ", ".join(sorted(unknown_sections))
        )
    for section, raw in payload.items():
        if not isinstance(raw, Mapping):
            raise WorkstationSyncError(f"Project configuration [{section}] must be a TOML table")
        unknown = set(raw) - ALLOWED_PROJECT_KEYS[section]
        if unknown:
            names = ", ".join(f"{section}.{name}" for name in sorted(unknown))
            raise WorkstationSyncError(f"Project configuration contains disallowed key(s): {names}")
    try:
        validate_project_name(_read_table(payload, "project").get("project_name", ""))
    except ProjectIdentityError as exc:
        raise WorkstationSyncError(str(exc)) from exc


def render_project_config(raw: bytes, *, repo_root: Path, state_root: Path) -> str:
    if len(raw) > MAX_PROJECT_CONFIG_BYTES:
        raise WorkstationSyncError("Project configuration exceeds the 256 KiB size limit")
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WorkstationSyncError("Project configuration is not valid UTF-8") from exc
    try:
        unrendered = tomllib.loads(text)
        _validate_project_tables(unrendered)
        parsed_identity = identity_from_payload(unrendered)
    except (tomllib.TOMLDecodeError, ProjectIdentityError) as exc:
        raise WorkstationSyncError(f"Repository project configuration is invalid: {exc}") from exc
    identity = ProjectIdentity(
        name=parsed_identity.name,
        env_prefix=parsed_identity.env_prefix,
        state_root=state_root,
    )
    replacements = identity.tokens(repo_root=repo_root)
    for token, value in replacements.items():
        text = text.replace(token, value)
    remaining = sorted(set(re.findall(r"\$\{[A-Z0-9_]+\}", text)))
    if remaining:
        raise WorkstationSyncError("Unknown project configuration token(s): " + ", ".join(remaining))
    try:
        payload = tomllib.loads(text)
    except tomllib.TOMLDecodeError as exc:
        raise WorkstationSyncError(f"Repository project configuration is invalid TOML: {exc}") from exc
    _validate_project_tables(payload)
    if "repository" not in payload:
        raise WorkstationSyncError("Project configuration must contain a [repository] table")
    repository = _read_table(payload, "repository")
    if "repo_root" not in repository:
        raise WorkstationSyncError("Project configuration must contain repository.repo_root")
    configured_root = Path(str(repository["repo_root"])).resolve()
    if configured_root != repo_root.resolve():
        raise WorkstationSyncError("Project configuration must set repository.repo_root to ${REPO_ROOT}")
    return MANAGED_CONFIG_HEADER + text.rstrip() + "\n"


def _read_project_config(settings: SyncSettings) -> bytes:
    path = settings.project_config_file
    expected = (settings.repo_root / PROJECT_CONFIG_RELATIVE_PATH).resolve()
    if path.resolve() != expected:
        raise WorkstationSyncError(
            f"Project configuration must be the tracked repository file {PROJECT_CONFIG_RELATIVE_PATH.as_posix()}"
        )
    if path.is_symlink() or not path.is_file():
        raise WorkstationSyncError(
            f"Tracked project configuration is missing or not a regular file: {path}"
        )
    try:
        size = path.stat().st_size
        if size > MAX_PROJECT_CONFIG_BYTES:
            raise WorkstationSyncError("Project configuration exceeds the 256 KiB size limit")
        raw = path.read_bytes()
    except WorkstationSyncError:
        raise
    except OSError as exc:
        raise WorkstationSyncError(f"Could not read tracked project configuration {path}: {exc}") from exc
    if len(raw) != size:
        raise WorkstationSyncError("Project configuration changed while it was being read")
    return raw


def install_project_config(settings: SyncSettings) -> str:
    raw = _read_project_config(settings)
    rendered = render_project_config(
        raw,
        repo_root=settings.repo_root,
        state_root=settings.state_root,
    )
    temporary = settings.generated_config_file.with_name(settings.generated_config_file.name + ".part")
    from app_generator.config import load_config
    try:
        temporary.write_text(rendered, encoding="utf-8")
        config = load_config(temporary)
        if config.login_name.casefold() != settings.login_name.casefold():
            raise WorkstationSyncError(
                f"Project configuration expects {config.login_name}, but workstation settings expect "
                f"{settings.login_name}"
            )
        if config.drive_oauth_client_file != settings.oauth_client_file:
            raise WorkstationSyncError("Rendered OAuth client path does not match the project-derived path")
        if config.drive_token_file != settings.oauth_token_file:
            raise WorkstationSyncError("Rendered OAuth token path does not match the project-derived path")
        if config.chrome_profile_dir != settings.state_root / "chrome-profile":
            raise WorkstationSyncError("Rendered Chrome profile path does not match the project-derived path")
        if config.state_dir != settings.state_root / "runs":
            raise WorkstationSyncError("Rendered run-state path does not match the project-derived path")
        os.replace(temporary, settings.generated_config_file)
    except WorkstationSyncError:
        raise
    except Exception as exc:
        raise WorkstationSyncError(f"Repository generator configuration is not usable: {exc}") from exc
    finally:
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass
    digest = hashlib.sha256(raw).hexdigest()
    return digest


def run_checks(settings: SyncSettings, python: Path, *, run_generator: bool) -> None:
    if settings.run_tests:
        print("Running repository validation tests...")
        commands = (
            [str(python), "scripts/lint.py"],
            [str(python), "scripts/validate_content.py"],
            [str(python), "-m", "unittest", "discover", "-s", "tests", "-v"],
        )
        for command in commands:
            _command(command, settings.repo_root)
        node = shutil.which("node")
        if not node:
            raise WorkstationSyncError("Node.js is required for the JavaScript syntax check")
        _command([node, "--check", "app/app.js"], settings.repo_root)
    if settings.run_doctor:
        print("Running generator doctor (Drive and provenance checks; no Gemini upload)...")
        _command(
            [str(python), "-m", "app_generator", "doctor", "--config", str(settings.generated_config_file)],
            settings.repo_root,
        )
    if run_generator:
        print("Starting the explicitly requested live Gemini generation run...")
        _command(
            [str(python), "-m", "app_generator", "run", "--config", str(settings.generated_config_file)],
            settings.repo_root,
        )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--settings", type=Path)
    parser.add_argument("--projects-folder", help=argparse.SUPPRESS)
    parser.add_argument("--login-name")
    parser.add_argument("--branch")
    parser.add_argument("--post-sync", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument(
        "--init-settings-only",
        action="store_true",
        help="Create or verify project-derived workstation settings without fetching Git or running checks.",
    )
    parser.add_argument(
        "--run-generator",
        action="store_true",
        help="After synchronization and checks, explicitly start the live Gemini generation run.",
    )
    return parser


def _ensure_settings(
    args: argparse.Namespace,
    *,
    identity: ProjectIdentity,
    default_login_name: str,
) -> Path:
    path = (args.settings or identity.settings_path).expanduser().resolve()
    if path.is_file():
        return path
    login = (args.login_name or default_login_name).strip()
    branch = (args.branch or input("Git branch to synchronize [main]: ").strip() or "main").strip()
    if not login:
        raise WorkstationSyncError("Google account email is required")
    _write_initial_settings(
        path,
        login_name=login,
        branch=branch,
        project_name=identity.name,
    )
    print(f"Created machine-local settings: {path}")
    return path


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        project_path = ROOT / PROJECT_CONFIG_RELATIVE_PATH
        try:
            identity = load_project_identity(project_path)
            with project_path.open("rb") as handle:
                project_payload = tomllib.load(handle)
            default_login = str(_read_table(project_payload, "placeholders").get("loginname", "")).strip()
        except (ProjectIdentityError, OSError, tomllib.TOMLDecodeError) as exc:
            raise WorkstationSyncError(str(exc)) from exc
        settings_path = _ensure_settings(
            args,
            identity=identity,
            default_login_name=default_login,
        )
        if args.init_settings_only:
            print(f"Workstation settings ready: {settings_path}")
            return 0
        settings = load_settings(settings_path, project_name=identity.name)
        if not args.post_sync:
            commit = sync_repository(settings)
            print(f"Repository synchronized at {commit[:12]} ({settings.remote}/{settings.branch}).")
            python = prepare_environment(settings)
            command = [
                str(python), str(settings.repo_root / "scripts" / "sync_workstation.py"),
                "--settings", str(settings.settings_path), "--post-sync",
            ]
            if args.run_generator:
                command.append("--run-generator")
            return subprocess.run(command, cwd=settings.repo_root, check=False).returncode
        digest = install_project_config(settings)
        project_name = settings.project_config_file.relative_to(settings.repo_root).as_posix()
        print(
            f"Installed {project_name} as {settings.generated_config_file.name} "
            f"(sha256={digest})."
        )
        run_checks(settings, Path(sys.executable), run_generator=args.run_generator)
        print("Workstation synchronization and configured checks completed successfully.")
        return 0
    except WorkstationSyncError as exc:
        print(f"WORKSTATION_SYNC_ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

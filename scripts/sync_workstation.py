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
from types import SimpleNamespace
from typing import Any, Callable, Mapping


ROOT = Path(__file__).resolve().parents[1]
BRANCH = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._/-]*$")
REMOTE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
MAX_SHARED_CONFIG_BYTES = 256 * 1024
MANAGED_CONFIG_HEADER = "# Managed by scripts/sync_workstation.py; edit the shared template instead.\n"
ALLOWED_SHARED_KEYS = {
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
    "run": {
        "package_id", "chapter", "subchapter", "chapter_dir", "section_dir",
        "learning_boundary", "source_id", "edition", "heading", "page_range",
        "reviewer", "rights_note", "drive_file_id", "existing_source_manifest",
    },
    "limits": {
        "max_repair_attempts", "ui_timeout_seconds", "login_timeout_seconds",
        "response_timeout_seconds", "log_level",
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
    projects_folder_url: str
    shared_config_name: str
    login_name: str
    oauth_client_file: Path
    oauth_token_file: Path
    generated_config_file: Path
    run_tests: bool
    run_doctor: bool


CommandRunner = Callable[[list[str], Path], str]


def _state_root() -> Path:
    local = os.environ.get("LOCALAPPDATA")
    if local:
        return Path(local) / "BrilliantContentGenerator"
    return Path.home() / ".local" / "state" / "brilliant-content-generator"


def _default_settings_path() -> Path:
    return _state_root() / "workstation-sync.toml"


def _toml_string(value: str) -> str:
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def _strip_matching_quotes(value: str) -> str:
    """Remove one pair of quotes commonly included when a URL is pasted."""

    candidate = value.strip()
    if len(candidate) >= 2 and candidate[0] == candidate[-1] and candidate[0] in {"'", '"'}:
        return candidate[1:-1].strip()
    return candidate


def _write_initial_settings(
    path: Path,
    *,
    projects_folder_url: str,
    login_name: str,
    branch: str,
) -> None:
    state = _state_root()
    projects_folder_url = _strip_matching_quotes(projects_folder_url)
    content = "\n".join(
        (
            "# Machine-local, non-secret workstation synchronization settings.",
            "[repository]",
            'remote = "origin"',
            f"branch = {_toml_string(branch)}",
            "",
            "[drive]",
            f"projects_folder_url = {_toml_string(projects_folder_url)}",
            'shared_config_name = "generator.shared.toml"',
            f"login_name = {_toml_string(login_name)}",
            f"oauth_client_file = {_toml_string(str(state / 'credentials' / 'drive-oauth-client.json'))}",
            f"oauth_token_file = {_toml_string(str(state / 'credentials' / 'drive-oauth-token.json'))}",
            "",
            "[output]",
            'generated_config_file = "generator.shared.local.toml"',
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


def load_settings(path: Path, *, repo_root: Path = ROOT) -> SyncSettings:
    try:
        with path.open("rb") as handle:
            payload = tomllib.load(handle)
    except (OSError, tomllib.TOMLDecodeError) as exc:
        raise WorkstationSyncError(f"Could not read workstation settings {path}: {exc}") from exc
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
    projects_folder_url = _strip_matching_quotes(str(drive.get("projects_folder_url", "")))
    login_name = str(drive.get("login_name", "")).strip()
    shared_name = str(drive.get("shared_config_name", "generator.shared.toml")).strip()
    if not projects_folder_url or not login_name:
        raise WorkstationSyncError("Drive projects_folder_url and login_name are required")
    if Path(shared_name).name != shared_name or not shared_name.casefold().endswith(".toml"):
        raise WorkstationSyncError("shared_config_name must be a TOML basename")
    state = _state_root()
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
    output_name = str(output.get("generated_config_file", "generator.shared.local.toml")).strip()
    if Path(output_name).name != output_name or not re.fullmatch(r"generator.*\.local.*\.toml", output_name):
        raise WorkstationSyncError("generated_config_file must be an ignored generator*.local*.toml basename")
    generated = (repo_root / output_name).resolve()
    if generated.parent != repo_root.resolve():
        raise WorkstationSyncError("The generated configuration must remain in the repository root")
    return SyncSettings(
        settings_path=path.resolve(),
        repo_root=repo_root.resolve(),
        remote=remote,
        branch=branch,
        projects_folder_url=projects_folder_url,
        shared_config_name=shared_name,
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


def _validate_shared_tables(payload: Mapping[str, Any]) -> None:
    unknown_sections = set(payload) - set(ALLOWED_SHARED_KEYS)
    if unknown_sections:
        raise WorkstationSyncError(
            "Shared configuration contains unsupported section(s): " + ", ".join(sorted(unknown_sections))
        )
    for section, raw in payload.items():
        if not isinstance(raw, Mapping):
            raise WorkstationSyncError(f"Shared configuration [{section}] must be a TOML table")
        unknown = set(raw) - ALLOWED_SHARED_KEYS[section]
        if unknown:
            names = ", ".join(f"{section}.{name}" for name in sorted(unknown))
            raise WorkstationSyncError(f"Shared configuration contains disallowed key(s): {names}")


def render_shared_config(raw: bytes, *, repo_root: Path, state_root: Path) -> str:
    if len(raw) > MAX_SHARED_CONFIG_BYTES:
        raise WorkstationSyncError("Shared configuration exceeds the 256 KiB size limit")
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WorkstationSyncError("Shared configuration is not valid UTF-8") from exc
    replacements = {
        "${REPO_ROOT}": repo_root.resolve().as_posix(),
        "${STATE_ROOT}": state_root.resolve().as_posix(),
    }
    for token, value in replacements.items():
        text = text.replace(token, value)
    remaining = sorted(set(re.findall(r"\$\{[A-Z0-9_]+\}", text)))
    if remaining:
        raise WorkstationSyncError("Unknown shared configuration token(s): " + ", ".join(remaining))
    try:
        payload = tomllib.loads(text)
    except tomllib.TOMLDecodeError as exc:
        raise WorkstationSyncError(f"Downloaded shared configuration is invalid TOML: {exc}") from exc
    _validate_shared_tables(payload)
    if "repository" not in payload:
        raise WorkstationSyncError("Shared configuration must contain a [repository] table")
    repository = _read_table(payload, "repository")
    if "repo_root" not in repository:
        raise WorkstationSyncError("Shared configuration must contain repository.repo_root")
    configured_root = Path(str(repository["repo_root"])).resolve()
    if configured_root != repo_root.resolve():
        raise WorkstationSyncError("Shared configuration must set repository.repo_root to ${REPO_ROOT}")
    return MANAGED_CONFIG_HEADER + text.rstrip() + "\n"


def _download_shared_config(settings: SyncSettings) -> tuple[bytes, str]:
    if not settings.oauth_client_file.is_file():
        raise WorkstationSyncError(
            "The locally provisioned Drive OAuth client is missing: "
            f"{settings.oauth_client_file}. Do not place or retrieve it through the shared Drive folder."
        )
    from app_generator.sources.google_drive import DRIVE_FILES_URL, FOLDER_MIME, DriveRestClient, extract_drive_folder_id
    from app_generator.sources.google_drive_auth import authorize_google_drive

    auth_config = SimpleNamespace(
        drive_oauth_client_file=settings.oauth_client_file,
        drive_token_file=settings.oauth_token_file,
        drive_api_timeout_seconds=60,
        login_name=settings.login_name,
    )
    try:
        authorization = authorize_google_drive(auth_config)
        client = DriveRestClient(authorization.session, 60)
        folder_id = extract_drive_folder_id(settings.projects_folder_url)
        folder = client.get_item(folder_id)
        children = client.list_children(folder_id)
    except Exception as exc:
        raise WorkstationSyncError(f"Could not authorize or inspect the Projects folder: {exc}") from exc
    if folder.mime_type != FOLDER_MIME:
        raise WorkstationSyncError("The configured Projects Drive item is not a folder")
    matches = [item for item in children if item.name == settings.shared_config_name]
    if len(matches) != 1:
        raise WorkstationSyncError(
            f"Expected exactly one {settings.shared_config_name!r} in Projects; found {len(matches)}"
        )
    item = matches[0]
    if item.mime_type == FOLDER_MIME or item.can_download is False:
        raise WorkstationSyncError("The shared configuration is not a downloadable regular file")
    if item.size_bytes is not None and item.size_bytes > MAX_SHARED_CONFIG_BYTES:
        raise WorkstationSyncError("The shared configuration exceeds the 256 KiB size limit")
    try:
        response = authorization.session.get(
            f"{DRIVE_FILES_URL}/{item.file_id}",
            params={"alt": "media", "supportsAllDrives": "true"},
            timeout=60,
            stream=True,
        )
        response.raise_for_status()
        chunks: list[bytes] = []
        downloaded = 0
        for chunk in response.iter_content(chunk_size=64 * 1024):
            if not chunk:
                continue
            downloaded += len(chunk)
            if downloaded > MAX_SHARED_CONFIG_BYTES:
                raise WorkstationSyncError("The shared configuration exceeds the 256 KiB size limit")
            chunks.append(bytes(chunk))
        raw = b"".join(chunks)
    except WorkstationSyncError:
        raise
    except Exception as exc:
        raise WorkstationSyncError(f"Could not download the shared configuration: {exc}") from exc
    if item.size_bytes is not None and len(raw) != item.size_bytes:
        raise WorkstationSyncError("Shared configuration byte count does not match Drive metadata")
    return raw, authorization.email


def install_shared_config(settings: SyncSettings) -> str:
    raw, authorized_email = _download_shared_config(settings)
    rendered = render_shared_config(raw, repo_root=settings.repo_root, state_root=_state_root())
    temporary = settings.generated_config_file.with_name(settings.generated_config_file.name + ".part")
    from app_generator.config import load_config
    try:
        temporary.write_text(rendered, encoding="utf-8")
        config = load_config(temporary)
        if config.login_name.casefold() != authorized_email.casefold():
            raise WorkstationSyncError(
                f"Shared configuration expects {config.login_name}, but Drive is authorized as {authorized_email}"
            )
        os.replace(temporary, settings.generated_config_file)
    except WorkstationSyncError:
        raise
    except Exception as exc:
        raise WorkstationSyncError(f"Downloaded generator configuration is not usable: {exc}") from exc
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
    parser.add_argument("--settings", type=Path, default=_default_settings_path())
    parser.add_argument("--projects-folder")
    parser.add_argument("--login-name")
    parser.add_argument("--branch")
    parser.add_argument("--post-sync", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument(
        "--run-generator",
        action="store_true",
        help="After synchronization and checks, explicitly start the live Gemini generation run.",
    )
    return parser


def _ensure_settings(args: argparse.Namespace) -> Path:
    path = args.settings.expanduser().resolve()
    if path.is_file():
        return path
    projects = (args.projects_folder or input("Google Drive Projects folder URL: ")).strip()
    login = (args.login_name or input("Authorized Google account email: ")).strip()
    branch = (args.branch or input("Git branch to synchronize [main]: ").strip() or "main").strip()
    if not projects or not login:
        raise WorkstationSyncError("Projects folder URL and Google account email are required")
    _write_initial_settings(
        path,
        projects_folder_url=projects,
        login_name=login,
        branch=branch,
    )
    print(f"Created machine-local settings: {path}")
    return path


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        settings_path = _ensure_settings(args)
        settings = load_settings(settings_path)
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
        digest = install_shared_config(settings)
        print(
            f"Installed {settings.shared_config_name} as {settings.generated_config_file.name} "
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

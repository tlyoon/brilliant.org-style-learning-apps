#!/usr/bin/env python3
"""Safely configure the dedicated tracked project authority."""

from __future__ import annotations

import argparse
import difflib
import os
import subprocess
import tomllib
from pathlib import Path
from typing import Mapping
from urllib.parse import urlparse

from app_generator.project import ProjectIdentityError, validate_project_name


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = ROOT / "config" / "configure_project.toml"
EDITABLE_VALUES = {
    ("project", "project_name"): "project_name",
    ("placeholders", "sourcepath"): "source_root_url",
    ("placeholders", "gemini-gem"): "gem_url",
    ("placeholders", "loginname"): "login_name",
    ("gemini", "gem_name"): "gem_name",
}


class ProjectConfigurationError(RuntimeError):
    """The requested project initialization cannot be applied safely."""


def _toml_string(value: str) -> str:
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def _validate_https_url(value: str, *, hostname: str, label: str) -> str:
    parsed = urlparse(value.strip())
    if parsed.scheme != "https" or parsed.hostname != hostname:
        raise ProjectConfigurationError(f"{label} must be an https://{hostname} URL")
    return value.strip()


def validated_values(values: Mapping[str, str]) -> dict[str, str]:
    try:
        project_name = validate_project_name(values["project_name"])
    except (KeyError, ProjectIdentityError) as exc:
        raise ProjectConfigurationError(str(exc)) from exc
    login_name = values.get("login_name", "").strip()
    gem_name = values.get("gem_name", "").strip()
    if not login_name or "@" not in login_name:
        raise ProjectConfigurationError("login_name must be a non-empty account email")
    if not gem_name:
        raise ProjectConfigurationError("gem_name is required")
    return {
        "project_name": project_name,
        "source_root_url": _validate_https_url(
            values.get("source_root_url", ""), hostname="drive.google.com", label="source_root_url"
        ),
        "gem_url": _validate_https_url(
            values.get("gem_url", ""), hostname="gemini.google.com", label="gem_url"
        ),
        "login_name": login_name,
        "gem_name": gem_name,
    }


def render_project_configuration(text: str, values: Mapping[str, str]) -> str:
    requested = validated_values(values)
    try:
        payload = tomllib.loads(text)
    except tomllib.TOMLDecodeError as exc:
        raise ProjectConfigurationError(f"Existing project configuration is invalid TOML: {exc}") from exc
    if not isinstance(payload.get("project"), Mapping):
        raise ProjectConfigurationError("Existing configuration must contain a [project] table")

    section = ""
    replaced: set[tuple[str, str]] = set()
    output: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            section = stripped[1:-1].strip()
        match = next(
            (
                (key, value_name)
                for (table, key), value_name in EDITABLE_VALUES.items()
                if table == section and stripped.startswith(f"{key} =")
            ),
            None,
        )
        if match:
            key, value_name = match
            marker = (section, key)
            if marker in replaced:
                raise ProjectConfigurationError(f"Duplicate configuration key: {section}.{key}")
            line = f"{key} = {_toml_string(requested[value_name])}"
            replaced.add(marker)
        output.append(line)
    missing = set(EDITABLE_VALUES) - replaced
    if missing:
        names = ", ".join(f"{section}.{key}" for section, key in sorted(missing))
        raise ProjectConfigurationError(f"Project configuration is missing editable key(s): {names}")
    rendered = "\n".join(output).rstrip() + "\n"
    try:
        tomllib.loads(rendered)
    except tomllib.TOMLDecodeError as exc:
        raise ProjectConfigurationError(f"Rendered project configuration is invalid TOML: {exc}") from exc
    return rendered


def _require_clean_repository(root: Path) -> None:
    result = subprocess.run(
        ["git", "status", "--porcelain", "--untracked-files=all"],
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if result.returncode:
        raise ProjectConfigurationError("Could not verify the Git worktree before applying changes")
    if result.stdout.strip():
        raise ProjectConfigurationError(
            "The repository has local changes; commit, stash, or remove them before configuring a project"
        )


def apply_configuration(path: Path, rendered: str, *, repo_root: Path = ROOT) -> None:
    _require_clean_repository(repo_root)
    temporary = path.with_name(path.name + ".part")
    temporary.write_text(rendered, encoding="utf-8")
    os.replace(temporary, path)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--project-name", required=True)
    parser.add_argument("--source-root-url", required=True)
    parser.add_argument("--gem-url", required=True)
    parser.add_argument("--login-name", required=True)
    parser.add_argument("--gem-name", required=True)
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Atomically update config/configure_project.toml after verifying a clean Git worktree.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    path = args.config.expanduser().resolve()
    try:
        original = path.read_text(encoding="utf-8")
        rendered = render_project_configuration(
            original,
            {
                "project_name": args.project_name,
                "source_root_url": args.source_root_url,
                "gem_url": args.gem_url,
                "login_name": args.login_name,
                "gem_name": args.gem_name,
            },
        )
        if not args.apply:
            print("".join(difflib.unified_diff(
                original.splitlines(keepends=True),
                rendered.splitlines(keepends=True),
                fromfile=str(path),
                tofile=str(path),
            )), end="")
            print("Dry run only. Re-run with --apply after reviewing this diff.")
            return 0
        apply_configuration(path, rendered, repo_root=ROOT)
        print(f"Updated {path}. Review and commit the change through a pull request.")
        return 0
    except (OSError, ProjectConfigurationError) as exc:
        print(f"PROJECT_CONFIG_ERROR: {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

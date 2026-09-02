#!/usr/bin/env python3
"""Require operator-facing docs to move with operational interface changes."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[1]

OPERATIONAL_EXACT = {
    "sync-workstation.cmd",
    "app_generator/cli.py",
    "app_generator/config.py",
    "app_generator/project.py",
    "app_generator/runtime/auto.py",
    "app_generator/runtime/orchestrator.py",
    "scripts/sync_workstation.py",
    "scripts/sync_configured_workstation.py",
    "config/configure_project.toml",
    ".github/workflows/ensure-coordinator.yml",
}

OPERATIONAL_PREFIXES = (
    "app_generator/coordinator/",
    "coordinator/",
)

CANONICAL_DOCS = {
    "README.md",
    "app_generator/README.md",
    "config/README.md",
    "docs/CONTEXT_INDEX.md",
    "docs/PDF_TO_APP_QUICKSTART.md",
    "docs/WORKSTATION_SYNC.md",
    "docs/GENERIC_PROJECT_SETUP.md",
    "docs/CONTINUOUS_AUTO_TESTING.md",
    "docs/AUTO_MODE_COMPLETION_ROADMAP.md",
    "docs/DOCUMENTATION_MAINTENANCE.md",
}


def is_operational_path(path: str) -> bool:
    normalized = path.replace("\\", "/")
    return normalized in OPERATIONAL_EXACT or any(
        normalized.startswith(prefix) for prefix in OPERATIONAL_PREFIXES
    )


def is_canonical_doc(path: str) -> bool:
    return path.replace("\\", "/") in CANONICAL_DOCS


def documentation_required(changed_paths: Iterable[str]) -> bool:
    return any(is_operational_path(path) for path in changed_paths)


def documentation_present(changed_paths: Iterable[str]) -> bool:
    return any(is_canonical_doc(path) for path in changed_paths)


def _git(*arguments: str) -> str:
    completed = subprocess.run(
        ["git", *arguments],
        cwd=ROOT,
        text=True,
        encoding="utf-8",
        capture_output=True,
        check=False,
    )
    if completed.returncode:
        raise RuntimeError((completed.stdout + "\n" + completed.stderr).strip())
    return completed.stdout.strip()


def _committed_range() -> str | None:
    base_ref = os.environ.get("GITHUB_BASE_REF", "").strip()
    if base_ref:
        remote_base = f"origin/{base_ref}"
        try:
            merge_base = _git("merge-base", remote_base, "HEAD")
        except RuntimeError:
            merge_base = _git("merge-base", base_ref, "HEAD")
        return f"{merge_base}...HEAD"
    try:
        parent = _git("rev-parse", "HEAD^")
    except RuntimeError:
        return None
    return f"{parent}...HEAD"


def changed_paths() -> tuple[str, ...]:
    paths: set[str] = set()
    commit_range = _committed_range()
    if commit_range:
        output = _git("diff", "--name-only", commit_range)
        paths.update(line.strip() for line in output.splitlines() if line.strip())
    for arguments in (("diff", "--name-only"), ("diff", "--name-only", "--cached")):
        output = _git(*arguments)
        paths.update(line.strip() for line in output.splitlines() if line.strip())
    return tuple(sorted(paths))


def main() -> int:
    try:
        changed = changed_paths()
    except RuntimeError as exc:
        print(f"Documentation impact check could not inspect Git history: {exc}", file=sys.stderr)
        return 2

    operational = tuple(path for path in changed if is_operational_path(path))
    docs = tuple(path for path in changed if is_canonical_doc(path))

    if not operational:
        print("Documentation impact check: no operational interface files changed.")
        return 0
    if docs:
        print("Documentation impact check passed.")
        print("Operational changes:")
        for path in operational:
            print(f"- {path}")
        print("Canonical documentation updated:")
        for path in docs:
            print(f"- {path}")
        return 0

    print("Documentation impact check failed.", file=sys.stderr)
    print("Operational interface files changed:", file=sys.stderr)
    for path in operational:
        print(f"- {path}", file=sys.stderr)
    print(
        "Update at least one relevant canonical operational document in the same PR. "
        "See docs/DOCUMENTATION_MAINTENANCE.md.",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())

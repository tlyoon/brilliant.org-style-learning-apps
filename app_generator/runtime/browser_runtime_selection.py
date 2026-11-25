"""Reuse only the existing BOSLA virtualenv for one-shot local browser QA.

No package installation, arbitrary filesystem scan, model call or audit retry.
Resolve a linked Git worktree's owning checkout before the first browser attempt.
"""
from __future__ import annotations

import importlib
import os
from pathlib import Path
import subprocess
import sys

_SWITCHED = "BOSLA_BROWSER_RUNTIME_SELECTED"


def _selenium_usable() -> bool:
    try:
        importlib.import_module("selenium")
        return True
    except ImportError:
        return False


def _trusted_interpreters(root: Path) -> list[Path]:
    roots = [root.resolve()]
    try:
        result = subprocess.run(
            ["git", "-C", str(root), "rev-parse",
             "--path-format=absolute", "--git-common-dir"],
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
            text=True, timeout=8, check=False,
        )
        if result.returncode == 0:
            common = Path(result.stdout.strip()).resolve()
            if common.name == ".git" and common.is_dir():
                roots.append(common.parent)
    except (OSError, subprocess.TimeoutExpired):
        pass
    result_paths: list[Path] = []
    for directory in roots:
        for part in ("Scripts/python.exe", "bin/python"):
            candidate = directory / ".venv" / part
            if candidate.is_file() and candidate not in result_paths:
                result_paths.append(candidate)
    return result_paths


def recover_existing_browser_runtime(
    root: Path, script: Path, arguments: list[str],
) -> int | None:
    """Relaunch under a verified local BOSLA interpreter, or stop pre-audit."""
    if _selenium_usable():
        return None
    if os.environ.get(_SWITCHED) == "1":
        raise RuntimeError("BOSLA_BROWSER_RUNTIME_UNAVAILABLE")
    if not script.resolve().is_relative_to(root.resolve()):
        raise RuntimeError("BOSLA_BROWSER_SCRIPT_OUTSIDE_REPOSITORY")
    current = os.path.normcase(str(Path(sys.executable).resolve()))
    for candidate in _trusted_interpreters(root):
        if os.path.normcase(str(candidate.resolve())) == current:
            continue
        try:
            probe = subprocess.run(
                [str(candidate), "-c", "import selenium"],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                timeout=8, check=False,
            )
        except (OSError, subprocess.TimeoutExpired):
            continue
        if probe.returncode == 0:
            environment = os.environ.copy()
            environment[_SWITCHED] = "1"
            return subprocess.call(
                [str(candidate), str(script.resolve()), *arguments],
                env=environment,
            )
    raise RuntimeError("BOSLA_BROWSER_RUNTIME_UNAVAILABLE")

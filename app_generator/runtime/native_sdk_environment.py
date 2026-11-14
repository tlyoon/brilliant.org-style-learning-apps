"""Bounded local SDK repair before V3 review claims or model requests.

Only an explicitly execution-authorized native run may use this helper.
It installs the repository's EXISTING pinned dependencies in its ignored
local .venv; no global Python modifications, source PDF, or API requests.
A failed bootstrap must stop before the immutable model claim is opened.
"""
from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys

_GUARD = "BOSLA_V3_NATIVE_SDK_REEXEC"
_TEST = "from google.genai import types; assert callable(getattr(types, 'HttpRetryOptions', None))"


def _current_has_retry_guard() -> bool:
    try:
        from google.genai import types
    except ImportError:
        return False
    return callable(getattr(types, "HttpRetryOptions", None))


def _interpreter_has_retry_guard(interpreter: Path) -> bool:
    if interpreter.is_symlink() or not interpreter.is_file():
        return False
    try:
        result = subprocess.run(
            [str(interpreter), "-c", _TEST],
            capture_output=True, timeout=20, check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False
    return result.returncode == 0


def delegate_to_supported_sdk(
    repo_root: Path, original_args: list[str],
) -> int | None:
    """Return None for a usable current SDK; else repair and run exactly once.

    Running this is allowed ONLY after the normal immutable package plan,
    explicit --execute and generated-text-transfer checks have passed.
    No uncheckpointed model probe, key rotation, or request replay occurs.
    """
    if _current_has_retry_guard():
        return None
    if os.environ.get(_GUARD) == "1":
        raise RuntimeError("V3_NATIVE_SDK_REEXEC_STILL_INCOMPATIBLE")
    local_env = repo_root / ".venv"
    python = local_env / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    if local_env.is_symlink() or python.is_symlink():
        raise RuntimeError("V3_NATIVE_SDK_UNSAFE_LOCAL_RUNTIME")
    if not _interpreter_has_retry_guard(python):
        if not python.is_file():
            subprocess.run(
                [sys.executable, "-m", "venv", str(local_env)],
                cwd=repo_root, capture_output=True, check=True, timeout=90,
            )
        # Pip's retry count is zero and wall clock is bounded. This is the
        # already-locked pyproject.toml, never an ad-hoc unpinned upgrade.
        subprocess.run(
            [str(python), "-m", "pip", "install",
             "--disable-pip-version-check", "--retries", "0",
             "--timeout", "15", "-e", str(repo_root)],
            cwd=repo_root, capture_output=True, check=True, timeout=300,
        )
        if not _interpreter_has_retry_guard(python):
            raise RuntimeError("V3_NATIVE_SDK_BOOTSTRAP_INCOMPATIBLE")
    env = {**os.environ, _GUARD: "1"}
    child = subprocess.run(
        [str(python), str(repo_root / "scripts" /
                           "run_v3_native_gemini_review.py"), *original_args],
        cwd=repo_root, env=env, check=False,
    )
    return child.returncode

"""Invoke the repository's authoritative semantic validator against candidates and final files."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


def _load_validator(repo_root: Path):
    path = repo_root / "scripts" / "validate_content.py"
    spec = importlib.util.spec_from_file_location("generator_repository_validator", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load repository validator: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def validate_candidate(repo_root: Path, candidate_root: Path, package_relative_path: Path) -> list[str]:
    validator = _load_validator(repo_root)
    validator.ROOT = candidate_root
    validator.CONTENT = candidate_root / "content"
    validator.MANIFEST_ROOT = validator.CONTENT / "source-manifests"
    package = json.loads((candidate_root / package_relative_path).read_text(encoding="utf-8"))
    return validator.validate_package(package, package_relative_path.as_posix())


def run_repository_validator(repo_root: Path) -> None:
    result = subprocess.run(
        [sys.executable, str(repo_root / "scripts" / "validate_content.py")],
        cwd=repo_root,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if result.returncode:
        raise RuntimeError((result.stdout + "\n" + result.stderr).strip())

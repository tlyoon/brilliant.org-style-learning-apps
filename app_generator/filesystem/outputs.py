"""Windows-safe atomic writes and no-overwrite artifact installation."""

from __future__ import annotations

import json
import os
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Iterable

from app_generator.errors import OutputWriteError, PackageAlreadyExistsError


def write_text_atomic(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(text)
            if text and not text.endswith("\n"):
                handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    except BaseException:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
        raise


def write_json_atomic(path: Path, data: Any) -> None:
    text = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
    json.loads(text)
    write_text_atomic(path, text)
    json.loads(path.read_text(encoding="utf-8"))


@dataclass(frozen=True)
class Artifact:
    relative_path: Path
    content: str


def stage_artifacts(candidate_root: Path, artifacts: Iterable[Artifact]) -> list[Path]:
    staged: list[Path] = []
    for artifact in artifacts:
        path = candidate_root / artifact.relative_path
        write_text_atomic(path, artifact.content)
        staged.append(path)
    return staged


def preflight_artifact_install(
    repo_root: Path,
    relative_paths: Iterable[Path],
    *,
    replace_existing: bool = False,
) -> list[Path]:
    """Fail before generation when output collisions are not explicitly replaceable."""

    destinations = [repo_root / path for path in relative_paths]
    existing = [path for path in destinations if path.exists()]
    if existing and not replace_existing:
        raise PackageAlreadyExistsError(
            "Generated artifacts already exist; refusing to regenerate without --regenerate: "
            + ", ".join(map(str, existing))
        )
    return existing


def _write_bytes_atomic(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    except BaseException:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
        raise


def install_new_artifacts(
    repo_root: Path,
    candidate_root: Path,
    relative_paths: Iterable[Path],
    *,
    verify: Callable[[], None],
    replace_existing: bool = False,
) -> list[Path]:
    paths = list(relative_paths)
    destinations = [repo_root / path for path in paths]
    existing = preflight_artifact_install(
        repo_root, paths, replace_existing=replace_existing
    )
    backups = {path: path.read_bytes() for path in existing} if replace_existing else {}
    installed: list[Path] = []
    try:
        for relative, destination in zip(paths, destinations, strict=True):
            source = candidate_root / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            write_text_atomic(destination, source.read_text(encoding="utf-8"))
            installed.append(destination)
        verify()
    except BaseException as exc:
        restore_errors: list[str] = []
        for path in reversed(installed):
            try:
                if path in backups:
                    _write_bytes_atomic(path, backups[path])
                else:
                    path.unlink(missing_ok=True)
            except BaseException as restore_exc:
                restore_errors.append(f"{path}: {restore_exc}")
        detail = ""
        if restore_errors:
            detail = "; restore errors: " + "; ".join(restore_errors)
        raise OutputWriteError(
            f"Artifact installation failed and repository artifacts were restored: {exc}{detail}"
        ) from exc
    return installed

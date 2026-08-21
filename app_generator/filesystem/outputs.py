"""Windows-safe atomic writes and no-overwrite artifact installation."""

from __future__ import annotations

import json
import os
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Iterable

from app_generator.errors import OutputWriteError


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


def install_new_artifacts(
    repo_root: Path,
    candidate_root: Path,
    relative_paths: Iterable[Path],
    *,
    verify: Callable[[], None],
) -> list[Path]:
    paths = list(relative_paths)
    destinations = [repo_root / path for path in paths]
    existing = [path for path in destinations if path.exists()]
    if existing:
        raise OutputWriteError("Refusing to overwrite existing repository artifacts: " + ", ".join(map(str, existing)))
    installed: list[Path] = []
    try:
        for relative, destination in zip(paths, destinations, strict=True):
            source = candidate_root / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            write_text_atomic(destination, source.read_text(encoding="utf-8"))
            installed.append(destination)
        verify()
    except BaseException as exc:
        for path in reversed(installed):
            try:
                path.unlink()
            except FileNotFoundError:
                pass
        raise OutputWriteError(f"Artifact installation failed and newly created files were rolled back: {exc}") from exc
    return installed

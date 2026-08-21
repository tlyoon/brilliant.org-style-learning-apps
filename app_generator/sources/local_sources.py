"""Inspect local PDF copies without extracting or storing their contents."""

from __future__ import annotations

import hashlib
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

from app_generator.errors import SourceSetMismatch


@dataclass(frozen=True)
class LocalSource:
    path: Path
    controlled_filename: str
    sha256: str
    size_bytes: int

    def metadata(self) -> dict[str, str | int]:
        data = asdict(self)
        data["path"] = str(self.path)
        return data


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()


def inspect_sources(paths: Iterable[Path]) -> tuple[LocalSource, ...]:
    records = tuple(
        LocalSource(
            path=path.resolve(),
            controlled_filename=path.name,
            sha256=sha256_file(path),
            size_bytes=path.stat().st_size,
        )
        for path in paths
    )
    names = [record.controlled_filename.casefold() for record in records]
    if len(names) != len(set(names)):
        raise SourceSetMismatch("Local PDF filenames are not unique, so source provenance is ambiguous")
    return records

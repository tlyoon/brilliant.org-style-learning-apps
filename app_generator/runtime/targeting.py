"""Runtime helpers for explicitly scoped coordinated auto work."""

from __future__ import annotations

import re
from collections.abc import Iterable

from app_generator.errors import NoAvailableJob
from app_generator.sources.google_drive import ResolvedDriveSource


CHAPTER_ID = re.compile(r"^[1-9][0-9]*$")


def normalize_target_subchapter_id(target_subchapter_id: str | None) -> str | None:
    """Normalize an explicit CLI subchapter path to its terminal section id."""

    if target_subchapter_id is None:
        return None
    normalized = target_subchapter_id.strip().replace("\\", "/").rstrip("/")
    if not normalized:
        return None
    return normalized.split("/")[-1]


def normalize_target_chapter(target_chapter: str | int | None) -> str | None:
    """Normalize a chapter scope such as ``10`` without accepting path fragments."""

    if target_chapter is None:
        return None
    normalized = str(target_chapter).strip()
    if not CHAPTER_ID.fullmatch(normalized):
        raise ValueError("target chapter must be a positive integer such as 10")
    return normalized


def restrict_inventory_to_chapter(
    sources: Iterable[ResolvedDriveSource],
    target_chapter: str | int | None,
) -> tuple[ResolvedDriveSource, ...]:
    """Return all sources, or only sections belonging to one exact chapter."""

    inventory = tuple(sources)
    chapter = normalize_target_chapter(target_chapter)
    if chapter is None:
        return inventory
    matched = tuple(
        source for source in inventory
        if source.subchapter_id.partition(".")[0] == chapter
    )
    if not matched:
        raise NoAvailableJob(
            f"Chapter {chapter} was not found under the configured Google Drive source root"
        )
    return matched


def restrict_inventory_to_subchapter(
    sources: Iterable[ResolvedDriveSource],
    target_subchapter_id: str | None,
) -> tuple[ResolvedDriveSource, ...]:
    """Return all sources for normal auto mode, or only one explicit target section."""

    inventory = tuple(sources)
    target = normalize_target_subchapter_id(target_subchapter_id)
    if target is None:
        return inventory
    matched = tuple(source for source in inventory if source.subchapter_id == target)
    if not matched:
        raise NoAvailableJob(
            f"Target section {target} was not found under the configured Google Drive source root"
        )
    return matched


def restrict_auto_inventory(
    sources: Iterable[ResolvedDriveSource],
    *,
    target_subchapter_id: str | None = None,
    target_chapter: str | int | None = None,
) -> tuple[ResolvedDriveSource, ...]:
    """Apply mutually exclusive exact-section or chapter scope to an auto inventory."""

    if target_subchapter_id and target_chapter is not None:
        raise ValueError("auto mode cannot combine an exact subchapter target with a chapter scope")
    inventory = restrict_inventory_to_chapter(sources, target_chapter)
    return restrict_inventory_to_subchapter(inventory, target_subchapter_id)

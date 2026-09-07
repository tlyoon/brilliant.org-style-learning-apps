"""Runtime helpers for explicitly targeted coordinated auto work."""

from __future__ import annotations

from collections.abc import Iterable

from app_generator.errors import NoAvailableJob
from app_generator.sources.google_drive import ResolvedDriveSource


def normalize_target_subchapter_id(target_subchapter_id: str | None) -> str | None:
    """Normalize an explicit CLI subchapter path to its terminal section id."""

    if target_subchapter_id is None:
        return None
    normalized = target_subchapter_id.strip().replace("\\", "/").rstrip("/")
    if not normalized:
        return None
    return normalized.split("/")[-1]


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

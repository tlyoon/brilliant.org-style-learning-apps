"""Build and verify repository-compatible source manifests."""

from __future__ import annotations

import hashlib
import json
from datetime import date
from pathlib import Path
from typing import Any

from app_generator.config import GeneratorConfig
from app_generator.errors import RepositoryCompatibilityError
from app_generator.sources.local_sources import LocalSource
from app_generator.sources.production_source_policy import reject_multiple_authoritative_sources


def _corpus_sha256(sources: tuple[LocalSource, ...]) -> str:
    material = "\n".join(
        f"{source.controlled_filename}:{source.sha256}" for source in sources
    ).encode("utf-8")
    return hashlib.sha256(material).hexdigest()


def select_primary_source(
    sources: tuple[LocalSource, ...], target_filename: str
) -> LocalSource:
    """Select the controlled primary PDF, independent of corpus sort order.

    Multi-PDF topics must contain exactly one target_filename; silently
    selecting the first (possibly supplementary) PDF creates stale or wrong
    source-manifest identity. Preserve the prior single-PDF fallback for
    existing local/legacy imports without rewriting their provenance.
    """
    if not sources:
        raise RepositoryCompatibilityError("No controlled PDF source was supplied")
    matches = [
        source for source in sources
        if source.controlled_filename.casefold() == target_filename.casefold()
    ]
    if len(matches) == 1:
        return matches[0]
    if len(matches) > 1:
        raise RepositoryCompatibilityError(
            "Several source files match the configured primary target filename"
        )
    if len(sources) > 1:
        raise RepositoryCompatibilityError(
            "Multi-PDF source corpus has no controlled primary target filename"
        )
    return sources[0]


def build_manifest(
    config: GeneratorConfig,
    sources: tuple[LocalSource, ...],
    *,
    drive_file_id: str | None = None,
    drive_file_ids: tuple[str, ...] = (),
) -> dict[str, Any]:
    # A new production source manifest is always bound to a SINGLE textbook.
    # Historical multi-source manifests remain readable as frozen evidence
    # elsewhere; do not issue any new multi-source learning package.
    sources = reject_multiple_authoritative_sources(sources)
    primary = select_primary_source(sources, config.target_filename)
    ids = tuple(drive_file_ids) or ((drive_file_id,) if drive_file_id else ())
    source_entries = []
    for index, source in enumerate(sources):
        entry: dict[str, Any] = {
            "controlledFilename": source.controlled_filename,
            "sha256": source.sha256,
            "role": "primary" if source is primary else "supplementary",
        }
        if index < len(ids) and ids[index]:
            entry["driveFileId"] = ids[index]
        source_entries.append(entry)
    manifest: dict[str, Any] = {
        "manifestVersion": "1.1",
        "sourceId": config.source_id,
        "controlledFilename": primary.controlled_filename,
        "sha256": primary.sha256,
        "corpusSha256": _corpus_sha256(sources),
        "sources": source_entries,
        "edition": config.edition,
        "chapter": config.chapter,
        "subchapter": config.subchapter,
        "heading": config.heading,
        "pageRange": config.page_range,
        "learningBoundary": config.learning_boundary,
        "extractedOn": date.today().isoformat(),
        "reviewer": config.reviewer,
        "rightsNote": config.rights_note,
    }
    effective_drive_file_id = drive_file_id or config.drive_file_id
    if effective_drive_file_id:
        manifest["driveFileId"] = effective_drive_file_id
    return manifest


def load_existing_manifest(
    path: Path,
    source: LocalSource,
    config: GeneratorConfig | None = None,
) -> dict[str, Any]:
    manifest = json.loads(path.read_text(encoding="utf-8"))
    entries = manifest.get("sources")
    if (entries is not None and (
            not isinstance(entries, list) or len(entries) != 1
            or entries[0].get("role") != "primary"
            or entries[0].get("controlledFilename") != source.controlled_filename
            or str(entries[0].get("sha256", "")).casefold() != source.sha256.casefold())):
        raise RepositoryCompatibilityError(
            "BOSLA_SINGLE_TEXTBOOK_EXISTING_MULTISOURCE_MANIFEST_NOT_ADMISSIBLE"
        )
    if manifest.get("controlledFilename") != source.controlled_filename:
        raise RepositoryCompatibilityError("Existing manifest filename does not match the configured local source")
    if str(manifest.get("sha256", "")).casefold() != source.sha256.casefold():
        raise RepositoryCompatibilityError("Existing manifest checksum does not match the configured local source")
    if config is not None:
        expected = {
            "chapter": config.chapter,
            "subchapter": config.subchapter,
            "heading": config.heading,
            "pageRange": config.page_range,
            "learningBoundary": config.learning_boundary,
        }
        mismatched = [field for field, value in expected.items() if manifest.get(field) != value]
        if mismatched:
            raise RepositoryCompatibilityError(
                "Existing manifest conflicts with the configured learning boundary: " + ", ".join(mismatched)
            )
    return manifest

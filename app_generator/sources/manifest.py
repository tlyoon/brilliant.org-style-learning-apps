"""Build and verify repository-compatible source manifests."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any

from app_generator.config import GeneratorConfig
from app_generator.errors import RepositoryCompatibilityError
from app_generator.sources.local_sources import LocalSource


def build_manifest(
    config: GeneratorConfig,
    sources: tuple[LocalSource, ...],
    *,
    drive_file_id: str | None = None,
) -> dict[str, Any]:
    if len(sources) != 1:
        raise RepositoryCompatibilityError("Manifest schema 1.0 can represent exactly one source file")
    source = sources[0]
    manifest: dict[str, Any] = {
        "manifestVersion": "1.0",
        "sourceId": config.source_id,
        "controlledFilename": source.controlled_filename,
        "sha256": source.sha256,
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


def load_existing_manifest(path: Path, source: LocalSource, config: GeneratorConfig | None = None) -> dict[str, Any]:
    manifest = json.loads(path.read_text(encoding="utf-8"))
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

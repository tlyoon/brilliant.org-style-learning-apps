"""Materialize source-derived section metadata without retaining source text."""

from __future__ import annotations

import re
from copy import deepcopy
from dataclasses import replace
from typing import Any

from app_generator.config import GeneratorConfig
from app_generator.errors import ResponseContractError


def _compact_text(value: Any) -> str:
    return " ".join(str(value).split()) if isinstance(value, str) else ""


def materialize_source_metadata(
    config: GeneratorConfig,
    analysis: dict[str, Any],
) -> GeneratorConfig:
    """Derive the exact section label and boundary from validated PDF analysis."""

    section_id = config.pdf_subchapter_path
    title = _compact_text(analysis.get("sectionTitle"))
    title = re.sub(
        rf"^(?:section\s+)?{re.escape(section_id)}\s*(?:[-:–—]\s*)?",
        "",
        title,
        flags=re.IGNORECASE,
    ).strip()
    if not title:
        raise ResponseContractError("Source analysis did not provide an exact section title")
    section_label = f"{section_id} {title}"

    scope = analysis.get("scopeNotes", {})
    included = "; ".join(_compact_text(item) for item in scope.get("includedConcepts", []))
    excluded = "; ".join(_compact_text(item) for item in scope.get("excludedConcepts", []))
    if not included or not excluded:
        raise ResponseContractError("Source analysis did not provide a complete learning boundary")
    boundary = (
        f"Includes concepts supported by the controlled PDF for {section_label}: {included}. "
        f"Excludes: {excluded}."
    )
    return replace(
        config,
        subchapter=section_label,
        heading=section_label,
        learning_boundary=boundary,
    )


def apply_source_metadata(package: dict[str, Any], config: GeneratorConfig) -> dict[str, Any]:
    """Apply Python-owned section identity and source-location provenance."""

    updated = deepcopy(package)
    updated["subchapter"] = config.subchapter
    source_location = f"{config.heading}; {config.page_range}"
    for activity in updated.get("activities", []):
        provenance = activity.get("provenance")
        if isinstance(provenance, dict):
            provenance["sourceLocation"] = source_location
    return updated

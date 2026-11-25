"""BOSLA production authority: one operator-selected textbook PDF per topic.

Historical multi-PDF / exactly-three C3 campaigns are evidence-only; they
must not be silently imported as a production corpus or release requirement.
This pure guard does not download or upload any file.
"""
from __future__ import annotations

from typing import TypeVar, Iterable
from app_generator.errors import RepositoryCompatibilityError, SourceAmbiguous

T = TypeVar("T")


def one_configured_textbook_source(
    candidates: Iterable[T], *,
    target_filename: str,
) -> tuple[T, ...]:
    """Admit exactly the configured source; ignore unrelated sibling PDFs.

    The selected source remains authoritative, even when other PDFs happen
    to be stored in the same Google Drive folder. Caller must never download,
    attach or incorporate ignored PDFs in generation. The configured source
    is not guessed and must be unique (case-insensitively).
    """
    items = tuple(candidates)
    if not isinstance(target_filename, str) or not target_filename.strip():
        raise RepositoryCompatibilityError("BOSLA_SINGLE_TEXTBOOK_TARGET_REQUIRED")
    selected = tuple(
        item for item in items
        if str(getattr(item, "filename", getattr(item, "controlled_filename", ""))).casefold()
        == target_filename.casefold()
    )
    if len(selected) != 1:
        if not selected:
            raise RepositoryCompatibilityError(
                "BOSLA_SINGLE_TEXTBOOK_SOURCE_MISSING_NO_EXTERNAL_PDF_FALLBACK"
            )
        raise SourceAmbiguous(
            "BOSLA_SINGLE_TEXTBOOK_DUPLICATE_PRIMARY_SOURCE"
        )
    if getattr(selected[0], "can_download", True) is False:
        raise RepositoryCompatibilityError(
            "BOSLA_SINGLE_TEXTBOOK_PRIMARY_UNAVAILABLE_NO_EXTERNAL_PDF_FALLBACK"
        )
    return selected


def reject_multiple_authoritative_sources(sources: Iterable[T]) -> tuple[T, ...]:
    """Fail closed before a source-bearing model request or new manifest."""
    items = tuple(sources)
    if len(items) != 1:
        raise RepositoryCompatibilityError(
            "BOSLA_SINGLE_TEXTBOOK_EXACTLY_ONE_SELECTED_PDF_NOT_THREE"
        )
    return items

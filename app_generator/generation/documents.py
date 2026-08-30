"""Render standardized, pending-review companion records from structured package data."""

from __future__ import annotations

from app_generator.config import GeneratorConfig


def render_learning_design(config: GeneratorConfig, package: dict) -> str:
    objectives = "\n".join(f"{index}. {item}" for index, item in enumerate(package["learningObjectives"], 1))
    prerequisites = "\n".join(
        f"- `{item['id']}`: {item['description']['en']}" for item in package["prerequisites"]
    )
    misconceptions = "\n".join(
        f"- `{item['id']}`: {item['description']['en']}" for item in package["misconceptionCatalogue"]
    )
    return f"""# {config.subchapter} learning design

## Boundary

{config.learning_boundary}

## Learning objectives

{objectives}

## Prerequisites

{prerequisites}

## Misconception catalogue

{misconceptions}

## Evidence intent

The first submitted response is independent evidence. Opening a hint, retrying, or entering prerequisite recovery marks later success as assisted evidence; it does not overwrite the first attempt. This generated record is a draft pending qualified human review.
"""


def render_review_record(config: GeneratorConfig) -> str:
    return f"""# {config.subchapter} review record

## Current status

Structurally validated automated draft. The package remains `draft`, not `review` or `publishable`, until qualified reviewers record the required sign-offs.

## Automated authoring evidence

- Source filename and SHA-256 were calculated locally; the source PDF was not added to Git.
- The controlled PDF was attached only to this run's fresh Gemini Gem conversation; Gem Knowledge was not modified.
- The package was parsed as JSON and checked against the current repository schemas and content validator.
- The complete review-level 18-activity distribution and authoring fields were checked without changing publication status.
- Gemini semantic review informed targeted repairs; automated review is not a human sign-off.

## Required sign-offs

| Domain | Status | Reviewer requirement |
|---|---|---|
| Subject matter/content | Pending | Qualified subject-matter reviewer |
| Instructional design and difficulty | Pending | Instructor or learning designer |
| English | Pending | Instructor/editor |
| Malay | Pending | Competent Malay-language reviewer |
| Simplified Chinese | Pending | Competent Simplified-Chinese reviewer |
| Accessibility and interaction semantics | Pending | Accessibility reviewer |
| Provenance and originality | Pending | Instructor or maintainer with controlled-source access |

Reviewers must record name, date, outcome, and corrective action before the package status changes.
"""


def render_section_readme(config: GeneratorConfig) -> str:
    return f"""# {config.subchapter}

This directory contains an automatically generated, structurally validated draft learning-content package for `{config.package_id}`.

The package is not publishable until the sign-offs in `review-record.md` are complete. The controlled source PDF remains outside Git; provenance is recorded in `{config.manifest_relative_path.as_posix()}`.
"""

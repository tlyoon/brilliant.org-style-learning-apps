"""Render standardized companion records from structured package data."""

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

The first submitted response is independent evidence. Opening a hint, retrying, or entering prerequisite recovery marks later success as assisted evidence; it does not overwrite the first attempt. Publication is permitted once the automated repository validation and configured deployment checks succeed.
"""


def render_review_record(config: GeneratorConfig) -> str:
    return f"""# {config.subchapter} validation record

## Current status

Automated generation and repository validation completed. This record documents automated quality checks; human sign-off is not a prerequisite for publication.

## Automated authoring and validation evidence

- Source filename and SHA-256 were calculated locally; the source PDF was not added to Git.
- The controlled PDF corpus was attached only to the generation run; shared Gemini knowledge was not modified.
- The package was parsed as JSON and checked against the current repository schemas and content validator.
- The complete 18-activity distribution and required authoring fields were validated.
- Gemini semantic audit informed targeted repairs, followed by deterministic revalidation.
- Configured Git and public deployment checks must succeed before the automated run is marked complete.

## Optional manual review

Instructors or maintainers may perform additional subject-matter, instructional, language, accessibility, or provenance review at any time. Such review is advisory and does not gate automated publication.
"""


def render_section_readme(config: GeneratorConfig) -> str:
    return f"""# {config.subchapter}

This directory contains an automatically generated and structurally validated learning-content package for `{config.package_id}`.

Publication is permitted after automated repository validation and configured deployment checks succeed. Optional manual review does not gate publication. The controlled source PDF remains outside Git; provenance is recorded in `{config.manifest_relative_path.as_posix()}`.
"""

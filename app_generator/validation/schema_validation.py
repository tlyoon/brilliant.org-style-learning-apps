"""Validate package and manifest using the repository's current schemas."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker


def schema_errors(instance: Any, schema_path: Path, label: str) -> list[str]:
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    failures = sorted(validator.iter_errors(instance), key=lambda error: tuple(map(str, error.absolute_path)))
    errors: list[str] = []
    for error in failures:
        location = label + "".join(f"[{part}]" if isinstance(part, int) else f".{part}" for part in error.absolute_path)
        errors.append(f"{location}: {error.message}")
    return errors


def validate_schemas(repo_root: Path, package: Any, manifest: Any) -> list[str]:
    schema_root = repo_root / "content" / "schema"
    return (
        schema_errors(package, schema_root / "content-package.schema.json", "package")
        + schema_errors(manifest, schema_root / "source-manifest.schema.json", "manifest")
    )


def validate_manifest(repo_root: Path, manifest: Any) -> list[str]:
    return schema_errors(
        manifest,
        repo_root / "content" / "schema" / "source-manifest.schema.json",
        "manifest",
    )

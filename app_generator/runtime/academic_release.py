"""Shared automatic V3 release gate; no human academic or pilot signoff.

A complete exact-artifact AI + engineering evidence receipt is necessary.
Missing evidence queues autonomous assessment; it is never an implicit PASS.
Operational restrictions on third-party assets and real personal data remain
separate from technical-completion criteria.
"""
from __future__ import annotations

from pathlib import Path

from app_generator.errors import ValidationFailure
from app_generator.validation.autonomous_completion import (
    read_private_release_receipt,
)


def public_release_requested(config) -> bool:
    return bool(getattr(config, "git_auto_merge", False)
                or getattr(config, "public_deploy", False))


def enforce_academic_release_gate(
    repo_root: Path, package_path: Path, validation_dir: Path,
) -> dict:
    """Verify exact package and auto-derived release outcome at the real gate.

    The public publisher and standalone bundle builder call this same entry.
    There is no human review, real learner pilot or independent visual signoff.
    A missing/unresolved automated receipt fails closed without writes.
    """
    if (not isinstance(repo_root, Path) or not isinstance(package_path, Path)
        or not isinstance(validation_dir, Path)):
        raise ValueError("V3_INVALID_RELEASE_INPUT")
    if (package_path.is_symlink() or not package_path.is_file()
        or package_path.stat().st_size > 2_000_000):
        raise ValidationFailure("Autonomous V3 release cannot read exact package",
                                ["V3_PACKAGE_MISSING_OR_UNSAFE"])
    try:
        report = read_private_release_receipt(
            package_path.read_bytes(),
            validation_dir / "autonomous-v3-release-receipt.json",
        )
    except (OSError, ValueError, TypeError, KeyError) as exc:
        raise ValidationFailure(
            "Automatic release pending complete V3 AI and deterministic assessment",
            [str(exc)[:160]],
        ) from exc
    return report

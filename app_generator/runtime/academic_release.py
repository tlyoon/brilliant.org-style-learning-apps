"""Fail-closed academic gate before automatic merge or public deployment.

This gate only runs on irreversible/release paths. Local package installation
and draft PR handoff remain possible with REVIEW_REQUIRED academic evidence.
"""
from __future__ import annotations

from pathlib import Path
import hashlib

from app_generator.errors import ValidationFailure
from app_generator.filesystem.outputs import write_json_atomic
from scripts.audit_academic_qa import academic_triage


def public_release_requested(config) -> bool:
    return bool(getattr(config, "git_auto_merge", False) or getattr(config, "public_deploy", False))


def enforce_academic_release_gate(repo_root: Path, package_path: Path, validation_dir: Path) -> dict:
    """Record exact-package academic evidence and refuse unresolved public release."""
    try:
        report = academic_triage(repo_root, package_path)
    except (OSError, ValueError, TypeError, KeyError) as exc:
        raise ValidationFailure(
            "Automatic release blocked: academic verification could not be completed",
            [f"{type(exc).__name__}: {str(exc)[:300]}"],
        ) from exc
    # Reject stale/mismatched proof even when a verifier reports PASS.
    if report.get("artifactSha256") != hashlib.sha256(package_path.read_bytes()).hexdigest():
        raise ValidationFailure(
            "Automatic release blocked: academic evidence refers to another package version",
            ["academic QA artifact digest does not match the currently installed package"],
        )
    # A failed or pending gate is evidence, not permission. Save it as a
    # separately named run validation artifact for operator recovery.
    write_json_atomic(validation_dir / "academic-release-gate.json", report)
    if report.get("academicQA") != "PASS":
        pending = [key for key, outcome in report.get("gates", {}).items() if outcome != "PASS"]
        raise ValidationFailure(
            "Automatic merge/public release blocked by unresolved academic QA",
            [
                f"academicQA={report.get('academicQA', 'UNKNOWN')}",
                f"pending or failed gates: {', '.join(pending) if pending else 'unknown'}",
                f"package sha256: {report.get('artifactSha256', 'unavailable')}",
            ],
        )
    return report

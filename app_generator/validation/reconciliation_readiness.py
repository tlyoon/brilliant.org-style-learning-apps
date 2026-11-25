"""Nonexecuting C3 reconciliation preflight; never grants a PDF retry or release.

This checks only explicit local release controls and immutable *metadata*
bindings. It never reads credentials, performs Gemini/network operations,
opens PDF source bytes or verifies academic/browser provenance.
"""
from __future__ import annotations

import re
from typing import Any

from app_generator.validation.heldout_generalization_gate import validate_manifest

_GIT_SHA = re.compile(r"[a-f0-9]{40}\Z")
_SHA256 = re.compile(r"[a-f0-9]{64}\Z")
_RELEASE_FLAGS = (
    ("git", "git_publish"),
    ("git", "git_auto_merge"),
    ("automation", "public_deploy"),
    ("automation", "public_deploy_auto_merge"),
)


def inspect_reconciliation_readiness(
    config: dict[str, Any], *,
    frozen_engine_sha: str,
    candidate_engine_sha: str,
    manifest: dict[str, Any] | None = None,
    selection_witness_sha256: str | None = None,
) -> dict[str, Any]:
    """Admit only a *metadata-ready* round-two reconciliation, never execution.

    Refuses absent/true/invalid publication booleans, changed frozen engines,
    new selections, and unpinned selection witnesses. External provider access,
    receipt truth and approval deliberately cannot be inferred from any input.
    """
    if not isinstance(config, dict):
        raise ValueError("reconciliation config must be a TOML object")
    if not isinstance(frozen_engine_sha, str) or not _GIT_SHA.fullmatch(frozen_engine_sha):
        raise ValueError("frozen engine must be an exact Git SHA")
    if not isinstance(candidate_engine_sha, str) or not _GIT_SHA.fullmatch(candidate_engine_sha):
        raise ValueError("candidate engine must be an exact Git SHA")

    unsafe_flags = []
    for section, flag in _RELEASE_FLAGS:
        table = config.get(section)
        if not isinstance(table, dict) or table.get(flag) is not False:
            unsafe_flags.append(f"{section}.{flag}")

    blockers = []
    if unsafe_flags:
        blockers.append("PUBLICATION_FLAGS_NOT_EXPLICITLY_DISABLED")
    if frozen_engine_sha != candidate_engine_sha:
        blockers.append("FROZEN_ENGINE_MISMATCH")

    pinned = isinstance(selection_witness_sha256, str) and bool(
        _SHA256.fullmatch(selection_witness_sha256)
    )
    manifest_valid = False
    if manifest is None:
        blockers.append("PRIVATE_ROUND_TWO_MANIFEST_NOT_SUPPLIED")
    elif not pinned:
        blockers.append("SELECTION_WITNESS_NOT_PINNED")
    else:
        try:
            validate_manifest(manifest)
            manifest_valid = (
                manifest["round"] == 2
                and manifest["baselineGitSha"] == frozen_engine_sha
                and manifest["selectionWitnessSha256"] == selection_witness_sha256
            )
        except (TypeError, ValueError, KeyError):
            manifest_valid = False
        if not manifest_valid:
            blockers.append("FROZEN_ROUND_TWO_MANIFEST_MISMATCH")

    return {
        "status": "OFFLINE_READY_FOR_EXTERNAL_REVIEW" if not blockers else "BLOCKED_OFFLINE",
        "unsafeReleaseFlags": unsafe_flags,
        "frozenEngineMatches": frozen_engine_sha == candidate_engine_sha,
        "frozenRoundTwoManifestMatches": manifest_valid,
        "blockers": blockers,
        "metadataReadyOnly": not blockers,
        "geminiAccessVerifiedHere": False,
        "sourceAndBrowserEvidenceVerifiedHere": False,
        "independentAcademicAcceptanceGranted": False,
        "executionAuthorized": False,
        "campaignReopened": False,
        "publicationAuthorized": False,
    }

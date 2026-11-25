"""Verify Git-tracked execution bytes against historical raw-file SHA-256.

A Git blob stores canonical LF text while Windows autocrlf checkouts may
produce CRLF bytes. Accept only exact recorded SHA-256 of the authoritative
blob OR its deterministic LF->CRLF materialization. No fuzzy matching.
"""
from __future__ import annotations

from hashlib import sha1, sha256
from pathlib import Path, PurePosixPath
import re
import subprocess

_HEX40 = re.compile(r"[0-9a-f]{40}\Z")
_HEX64 = re.compile(r"[0-9a-f]{64}\Z")


def canonical_git_blob_sha1(raw: bytes) -> str:
    """Git object identity of a controlled LF-text file on Linux or Windows.

    Only deterministic CRLF -> LF checkout normalization is performed;
    no whitespace, token or content edits are tolerated. Use an independently
    frozen Git blob SHA-1 for comparison (not the current mutable HEAD).
    """
    if not isinstance(raw, bytes) or len(raw) > 2_000_000:
        raise ValueError("INVALID_GIT_TEXT_BYTES")
    canonical = raw.replace(b"\r\n", b"\n")
    prefix = b"blob " + str(len(canonical)).encode("ascii") + b"\0"
    return sha1(prefix + canonical).hexdigest()


def verify_git_checkout_sha(
    repo: Path, commit: str, path: str, recorded_raw_sha256: str,
) -> str:
    """Return EXACT_GIT_BLOB or VERIFIED_WINDOWS_CRLF; raise otherwise."""
    if not isinstance(commit, str) or not _HEX40.fullmatch(commit):
        raise ValueError("INVALID_FROZEN_REVISION")
    if not isinstance(recorded_raw_sha256, str) or not _HEX64.fullmatch(
        recorded_raw_sha256
    ):
        raise ValueError("INVALID_RAW_EXECUTION_SHA")
    if (not isinstance(path, str) or "\\" in path or
        not path or PurePosixPath(path).is_absolute() or
        any(component in ("", ".", "..") for component in path.split("/"))):
        raise ValueError("UNSAFE_GIT_SOURCE_PATH")
    try:
        result = subprocess.run(
            ["git", "-C", str(repo), "show", f"{commit}:{path}"],
            capture_output=True, check=False, timeout=10,
        )
    except (OSError, subprocess.TimeoutExpired):
        raise ValueError("FROZEN_GIT_BLOB_UNAVAILABLE") from None
    if result.returncode != 0 or len(result.stdout) > 2_000_000:
        raise ValueError("FROZEN_GIT_BLOB_UNAVAILABLE")
    blob = result.stdout
    if sha256(blob).hexdigest() == recorded_raw_sha256:
        return "EXACT_GIT_BLOB"
    # Explicitly permit *only* the known Windows newline representation.
    if b"\n" in blob and b"\r" not in blob:
        windows = blob.replace(b"\n", b"\r\n")
        if sha256(windows).hexdigest() == recorded_raw_sha256:
            return "VERIFIED_WINDOWS_CRLF"
    raise ValueError("RAW_EXECUTION_SHA_NOT_BOUND_TO_GIT")

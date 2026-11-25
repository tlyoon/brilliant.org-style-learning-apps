"""Project-bound device guard for native V3 Gemini model review.

Bosla's designated workstation is Yoga 6. This protects against accidental
remote execution on other connected PCs; it is not a cryptographic identity
check and never authorizes replay of a denied or ambiguous model request.
Read-only dry-run planning does not require or mutate a workstation.
"""
from __future__ import annotations

from pathlib import Path
import re
import socket
import tomllib

_HOST = re.compile(r"[A-Za-z0-9][A-Za-z0-9-]{0,62}\Z")


def require_authorized_native_review_host(authority: Path) -> str:
    """Reject other hosts BEFORE reading keys, creating SDK clients or claims."""
    if authority.is_symlink() or not authority.is_file():
        raise ValueError("V3_NATIVE_REVIEW_HOST_CONFIG_UNAVAILABLE")
    document = tomllib.loads(authority.read_text(encoding="utf-8"))
    project = document.get("project", {})
    expected = project.get("native_gemini_review_host") if isinstance(project, dict) else None
    if not isinstance(expected, str) or not _HOST.fullmatch(expected):
        raise ValueError("V3_NATIVE_REVIEW_HOST_NOT_CONFIGURED")
    actual = socket.gethostname()
    if not isinstance(actual, str) or actual.casefold() != expected.casefold():
        raise PermissionError("V3_NATIVE_REVIEW_WRONG_WORKSTATION")
    return expected

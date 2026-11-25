"""Read-only Windows Chrome profile occupancy gate before independent review.

The gate never opens/attaches/kills browsers, reads cookies, or sends a Gemini
request. Unknown process state is unsafe, not an excuse for profile takeover.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from app_generator.gemini.existing_login_reviewers import existing_profile_in_use

ROLES = ("physics", "semantics")


def reviewer_ownership_preflight(
    profile_root: Path, repo_root: Path,
    *, is_busy: Callable[[Path], bool] = existing_profile_in_use,
) -> dict[str, Any]:
    if not profile_root.is_absolute() or not repo_root.is_absolute():
        raise ValueError("reviewer profile and checkout roots must be absolute")
    if profile_root.resolve().is_relative_to(repo_root.resolve()):
        raise ValueError("Chrome profiles must not be inside the source repository")
    details = []
    for role in ROLES:
        profile = profile_root / "academic-reviewers" / role / "gemini-browser"
        if not profile.is_dir():
            details.append({"role":role, "status":"MISSING", "authenticated":False})
            continue
        try:
            busy=is_busy(profile)
            if type(busy) is not bool:
                raise ValueError("non-boolean Chrome process ownership result")
            status="BUSY" if busy else "EXCLUSIVE_CANDIDATE"
        except (OSError,ValueError,TypeError):
            status="UNKNOWN"
        details.append({"role":role, "status":status, "authenticated":False})
    ready=all(x["status"]=="EXCLUSIVE_CANDIDATE" for x in details)
    return {
        "status":"EXCLUSIVE_CANDIDATE" if ready else "DEFER_FOR_EXCLUSIVE_OWNERSHIP",
        "profiles":details,
        "canAttemptIndependentBrowserReview":ready,
        "authenticatedVerified":False,
        "responseCaptured":False,
        "fullAcademicPass":False,
        "publicationAuthorized":False,
    }
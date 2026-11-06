"""Prepare an exact-revision, local-only six-section instructor preview roster.

Only explicitly selected, tracked JSON learning packages are read. Never opens
PDFs, invokes AI, updates course progression, or authorizes release. The
resulting local-pilot/roster.json is gitignored and refuses overwrite.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app_generator.validation.course_pilot_readiness import (
    assess_pilot_candidates,
    validate_pilot_scope,
)

_SCOPE = re.compile(r"sourcefree-pilot-[a-z0-9-]{3,60}\Z")


def _git(root: Path, *args: str) -> bytes:
    result = subprocess.run(
        ["git", "-C", str(root), *args],
        stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, check=False,
        timeout=20,
    )
    if result.returncode:
        raise ValueError("GIT_REVISION_OR_TRACKED_PACKAGE_UNAVAILABLE")
    return result.stdout


def prepare_local_roster(
    repo_root: Path, *, chapter: int, sections: list[int], scope_id: str,
) -> dict:
    """Validate immutable tracked candidates; return a roster, without writing."""
    root = repo_root.resolve(strict=True)
    if (not root.is_dir() or type(chapter) is not int or chapter < 1
            or not isinstance(sections, list) or len(sections) != 6
            or any(type(section) is not int or section < 1 for section in sections)
            or len(set(sections)) != 6 or not isinstance(scope_id, str)
            or not _SCOPE.fullmatch(scope_id)):
        raise ValueError("EXPLICIT_SIX_SECTION_SELECTION_REQUIRED")

    toplevel = Path(_git(root, "rev-parse", "--show-toplevel").decode("utf-8").strip()).resolve()
    if root != toplevel:
        raise ValueError("EXACT_REPOSITORY_ROOT_REQUIRED")
    head = _git(root, "rev-parse", "HEAD").decode("ascii").strip()
    if not re.fullmatch(r"[a-f0-9]{40}", head):
        raise ValueError("INVALID_GIT_REVISION")

    paths = [
        f"content/chapter-{chapter}/section-{chapter}-{section}/package.json"
        for section in sections
    ]
    cases = []
    selected: dict[str, bytes] = {}
    for section, relative in zip(sections, paths):
        local_path = root.joinpath(*relative.split("/"))
        if local_path.is_symlink() or not local_path.is_file():
            raise ValueError("SELECTED_TRACKED_PACKAGE_NOT_AVAILABLE")
        if not local_path.resolve().is_relative_to(root):
            raise ValueError("SELECTED_PACKAGE_OUTSIDE_REPOSITORY")
        actual = local_path.read_bytes()
        committed = _git(root, "show", "HEAD:" + relative)
        if actual != committed:
            raise ValueError("SELECTED_PACKAGE_DIFFERS_FROM_FROZEN_COMMIT")
        cases.append({
            "sectionNumber": section,
            "packagePath": relative,
            "packageSha256": sha256(actual).hexdigest(),
        })
        selected[relative] = actual

    manifest = {
        "scopeId": scope_id,
        "baselineGitSha": head,
        "chapterNumber": chapter,
        "mode": "OFFLINE_EXISTING_PACKAGES_ONLY",
        "cases": cases,
        "modelCallsAllowed": False,
        "pdfReadsAllowed": False,
        "publicationAllowed": False,
    }
    validate_pilot_scope(manifest)
    report = assess_pilot_candidates(
        manifest, selected.__getitem__, observed_git_sha=head,
    )
    if report["status"] != "SIX_STRUCTURAL_CANDIDATES_REQUIRE_INDEPENDENT_EVIDENCE":
        raise ValueError("SELECTED_PACKAGES_NOT_STRUCTURALLY_VALID")
    return manifest


def write_local_roster(repo_root: Path, manifest: dict) -> Path:
    """Create a gitignored local roster once; never replace an earlier one."""
    root = repo_root.resolve(strict=True)
    folder = root / "local-pilot"
    output = folder / "roster.json"
    if folder.is_symlink() or output.is_symlink() or output.exists():
        raise ValueError("LOCAL_PREVIEW_ROSTER_ALREADY_EXISTS_OR_LINKED")
    if _git(root, "check-ignore", "--quiet", "local-pilot/roster.json") != b"":
        raise ValueError("LOCAL_ROSTER_IGNORE_STATE_INVALID")
    folder.mkdir(exist_ok=True)
    if folder.is_symlink() or not folder.is_dir():
        raise ValueError("UNSAFE_PREVIEW_OUTPUT_DIRECTORY")
    with output.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(manifest, stream, indent=2, ensure_ascii=True)
        stream.write("\n")
    return output


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=ROOT)
    parser.add_argument("--chapter", type=int, required=True)
    parser.add_argument("--sections", nargs=6, required=True, type=int)
    parser.add_argument("--scope-id", required=True)
    options = parser.parse_args(argv)
    try:
        manifest = prepare_local_roster(
            options.repo_root, chapter=options.chapter,
            sections=options.sections, scope_id=options.scope_id,
        )
        output = write_local_roster(options.repo_root, manifest)
    except (OSError, ValueError, UnicodeError, subprocess.TimeoutExpired):
        # No source package bytes, local filenames or raw Git errors exposed.
        print(json.dumps({
            "status": "STOP_UNSAFE_OR_INCOMPLETE_LOCAL_PREVIEW",
            "classroomPilotReady": False,
            "publicationAuthorized": False,
        }))
        return 1
    print(json.dumps({
        "status": "LOCAL_SOURCEFREE_PREVIEW_ROSTER_CREATED",
        "scopeId": manifest["scopeId"],
        "baselineGitSha": manifest["baselineGitSha"],
        "chapterNumber": manifest["chapterNumber"],
        "sectionNumbers": [item["sectionNumber"] for item in manifest["cases"]],
        "localRoster": output.relative_to(options.repo_root.resolve()).as_posix(),
        "academicQA": "REVIEW_REQUIRED",
        "classroomPilotReady": False,
        "publicationAuthorized": False,
    }))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

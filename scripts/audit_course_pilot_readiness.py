"""Inspect six explicit existing package candidates without PDF/model/browser access.

Example:
  python scripts/audit_course_pilot_readiness.py --manifest private-scope.json \
      --repo-root . --observed-git-sha <exact-40-character-commit>

Exit 0 means *structural candidate metadata only*. Academic acceptance,
institutional consent and publication remain separate, unverified gates.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app_generator.validation.course_pilot_readiness import assess_pilot_candidates


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--repo-root", default=ROOT, type=Path)
    parser.add_argument("--observed-git-sha", required=True)
    options = parser.parse_args(argv)
    try:
        if options.manifest.is_symlink():
            raise ValueError("LINKED_MANIFEST_NOT_ALLOWED")
        manifest = json.loads(options.manifest.read_text(encoding="utf-8"))
        root = options.repo_root.resolve(strict=True)
        if not root.is_dir():
            raise ValueError("INVALID_REPOSITORY_DIRECTORY")

        def loader(relative: str) -> bytes:
            # The strict manifest validator runs before any call to loader.
            candidate = root.joinpath(*relative.split("/"))
            if candidate.is_symlink():
                raise ValueError("LINKED_PACKAGE_NOT_ALLOWED")
            resolved = candidate.resolve(strict=True)
            if not resolved.is_relative_to(root) or not resolved.is_file():
                raise ValueError("PACKAGE_OUTSIDE_REPOSITORY")
            return resolved.read_bytes()

        report = assess_pilot_candidates(
            manifest, loader, observed_git_sha=options.observed_git_sha,
        )
    except (ValueError, TypeError, OSError, json.JSONDecodeError):
        # Do not expose source text, private filesystem paths, or exceptions.
        print(json.dumps({
            "status": "STOP_INVALID_PILOT_SCOPE_OR_UNREADABLE_MANIFEST",
            "classroomPilotReady": False,
            "publicationAuthorized": False,
        }))
        return 2
    print(json.dumps(report, ensure_ascii=True, indent=2))
    return 0 if report["structuralCandidateCount"] == 6 else 1


if __name__ == "__main__":
    raise SystemExit(main())

"""One-shot, source-free three-topic acceptance evidence reconciliation.

This command does NOT generate activities, run Selenium, load PDFs, send
Gemini/ChatGPT requests, certify academic correctness or publish. Every
candidate is inspected once. The private output directory is created
exclusively, so the same manifest cannot overwrite a previous disposition.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from app_generator.validation.bounded_cross_topic_acceptance import (
    assess_cross_topic_evidence, canonical_digest, validate_cross_topic_manifest,
)

MAX_ARTIFACT_BYTES = 2_000_000
MAX_MANIFEST_BYTES = 100_000


def _safe_subpath(root: Path, relative: str) -> Path:
    """Reject traversals and symlinked members before any read."""
    target = root
    for member in relative.split("/"):
        if member in ("", ".", "..") or "\\" in member or ":" in member:
            raise ValueError("invalid local evidence path")
        target = target / member
        if target.is_symlink():
            raise ValueError("symlinked local evidence not authorized")
    if not target.resolve().is_relative_to(root.resolve()):
        raise ValueError("local evidence left the authorized input root")
    return target


def _bounded_read(path: Path, maximum: int = MAX_ARTIFACT_BYTES) -> bytes:
    if not path.is_file() or path.is_symlink() or path.stat().st_size > maximum:
        raise ValueError("missing, linked or oversized evidence")
    return path.read_bytes()


def _git_head() -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, check=True,
        stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True,
        timeout=6,
    )
    return result.stdout.strip()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--input-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    args = parser.parse_args(argv)

    try:
        input_root = args.input_root.resolve(strict=True)
        output_root = args.output_root.resolve(strict=True)
        if (not input_root.is_dir() or not output_root.is_dir() or
                input_root.is_symlink() or output_root.is_symlink() or
                output_root.is_relative_to(ROOT.resolve()) or
                args.manifest.is_symlink() or
                not args.manifest.resolve().is_relative_to(input_root) or
                input_root == output_root):
            raise ValueError("private read-only inputs and separate output required")
        raw_manifest = _bounded_read(args.manifest, MAX_MANIFEST_BYTES)
        manifest = json.loads(raw_manifest.decode("utf-8"))
        validate_cross_topic_manifest(manifest)
        head = _git_head()
        if head != manifest["baselineGitSha"]:
            raise ValueError("manifest not pinned to exact inspected code revision")
        digest = canonical_digest(manifest)
        destination = output_root / (manifest["campaignId"] + "-" + digest[:12])
        # Create a new immutable run namespace. No --resume, --force or retry.
        destination.mkdir(parents=False, exist_ok=False)
        marker = {
            "manifestSha256": digest,
            "baselineGitSha": head,
            "status": "STARTED_ONCE",
            "publicationAuthorized": False,
            "sourcePdfSubmitted": False,
        }
        with (destination / "started.json").open("x", encoding="utf-8") as handle:
            json.dump(marker, handle, sort_keys=True)
        report = assess_cross_topic_evidence(
            manifest,
            lambda relative: _bounded_read(_safe_subpath(input_root, relative)),
            observed_git_sha=head,
        )
        with (destination / "disposition.json").open("x", encoding="utf-8") as handle:
            json.dump(report, handle, indent=2, sort_keys=True)
        # Public stdout contains only fixed status and the manifest digest.
        print(json.dumps({
            "status": report["status"],
            "terminalDisposition": report["terminalDisposition"],
            "manifestSha256": digest,
            "caseCount": report["caseCount"],
            "checksPerCaseMaximum": 1,
            "academicAcceptanceGranted": False,
            "publicationAuthorized": False,
        }, sort_keys=True))
        return 0 if report["terminalDisposition"] == "STOP_INDEPENDENT_VERIFICATION_REQUIRED" else 2
    except (ValueError, KeyError, TypeError, OSError, UnicodeError,
            json.JSONDecodeError, subprocess.SubprocessError):
        print(json.dumps({
            "status": "REJECTED_SOURCE_FREE_ACCEPTANCE_RUN",
            "newProviderOrPdfCallsAllowed": False,
            "academicAcceptanceGranted": False,
            "publicationAuthorized": False,
        }, sort_keys=True))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

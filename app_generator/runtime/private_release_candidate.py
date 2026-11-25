"""Build an immutable, source-bound PRIVATE local preview, never a public release.

The original controlled PDF is checked but not copied. No Git, GitHub, CDN,
account or model endpoint receives the textbook-derived package.
"""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import shutil
import tempfile
from typing import Any

from app_generator.domains import resolve_domain
from app_generator.validation.academic_batch_gap_plan import plan_exact_academic_batch

APP_FILES = ("app.js", "visual-renderers.js", "styles.css")


def _sha(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def stage_private_candidate(
    *, repo_root: Path, package_file: Path, source_pdf: Path,
    matrix_file: Path, physics_file: Path, out_dir: Path,
    expected_package_sha256: str, expected_source_sha256: str,
    expected_count: int = 18,
) -> dict[str, Any]:
    repo = repo_root.resolve()
    out = out_dir.resolve()
    if not repo.is_dir() or not (repo / "app" / "index.html").is_file():
        raise ValueError("trusted source checkout required")
    if out.is_relative_to(repo) or out.exists():
        raise ValueError("private preview must be new and outside Git checkout")
    sources = (package_file, source_pdf, matrix_file, physics_file)
    if any(not p.is_file() or p.resolve().is_relative_to(repo) for p in sources):
        raise ValueError("source package and academic receipts must remain private")
    if (_sha(package_file) != expected_package_sha256 or
        _sha(source_pdf) != expected_source_sha256):
        raise ValueError("controlled candidate or original PDF hash mismatch")
    report = plan_exact_academic_batch(
        package_file=package_file, source_pdf=source_pdf,
        matrix_file=matrix_file, physics_file=physics_file,
        expected_count=expected_count,
        first_activity_id="int-select-isolated-conditions",
    )
    if (report["activityCount"] != expected_count
        or report["verifiedSourceLocationReceipts"] != expected_count
        or report["matchedBoundedPhysicsReceipts"] != expected_count
        or report["academicCounts"] != {
            "PASS": 0, "FAIL": 0, "REVIEW_REQUIRED": expected_count
        }
        or report["fullAcademicPassCount"] != 0
        or report["publicationAuthorized"] is not False):
        raise ValueError("candidate source evidence is incomplete or falsely approved")
    # Resolve app renderer and stylesheet from the checkout domain contract.
    visuals = resolve_domain(repo)
    originals = {name: repo / "app" / name for name in APP_FILES}
    originals["domain-renderers.js"] = visuals.path("visuals", "rendererScript")
    originals["domain-styles.css"] = visuals.path("visuals", "stylesheet")
    if any(not p.is_file() or not p.resolve().is_relative_to(repo) for p in originals.values()):
        raise ValueError("controlled local player asset missing or outside checkout")
    index = (repo / "app" / "index.html").read_bytes()
    marker = b'data-package-url=""'
    if index.count(marker) != 1:
        raise ValueError("player package binding marker is missing or ambiguous")
    # The browser has to be hosted on an owner's local loopback server.
    # Keep all original source content off the repo and GitHub.
    out.parent.mkdir(parents=True, exist_ok=True)
    temp = Path(tempfile.mkdtemp(prefix=".private-rc-", dir=out.parent))
    try:
        (temp / "index.html").write_bytes(index.replace(marker, b'data-package-url="package.json"'))
        shutil.copyfile(package_file, temp / "package.json")
        for name, path in originals.items():
            shutil.copyfile(path, temp / name)
        staged = {
            name: _sha(temp / name)
            for name in sorted(("index.html", "package.json", *originals))
        }
        if staged["package.json"] != expected_package_sha256:
            raise ValueError("private preview candidate changed during staging")
        manifest = {
            "schemaVersion": 1,
            "scope": "PRIVATE_LOCAL_PREVIEW_ONLY",
            "sourceSha256": expected_source_sha256,
            "packageSha256": expected_package_sha256,
            "activityCount": expected_count,
            "sourceLocationReceipts": report["verifiedSourceLocationReceipts"],
            "boundedPhysicsReceipts": report["matchedBoundedPhysicsReceipts"],
            "fullAcademicPassCount": 0,
            "independentSemanticAndVisualReviewPending": expected_count,
            "filesSha256": staged,
            "originalPdfIncluded": False,
            "sourceContentPushedToGit": False,
            "networkUploadPerformed": False,
            "academicQA": "REVIEW_REQUIRED",
            "publicationAuthorized": False,
        }
        (temp / "private-manifest.json").write_text(
            json.dumps(manifest, sort_keys=True, indent=2) + "\n",
            encoding="utf-8",
        )
        (temp / "PRIVATE-NOT-APPROVED.txt").write_text(
            "PRIVATE LOCAL PREVIEW ONLY. NOT A PUBLISHABLE OR ACADEMICALLY APPROVED RELEASE.\n"
            "Scientific source interpretation, EN/MS/ZH meaning, and rendered\n"
            "visual validity await independent review. Do not upload this\n"
            "directory to any public service or repository. The source PDF is\n"
            "not included. For authorized local inspection, from this folder\n"
            "serve on loopback only: python -m http.server 8765 --bind 127.0.0.1\n",
            encoding="utf-8",
        )
        temp.rename(out)
    finally:
        if temp.exists():
            shutil.rmtree(temp)
    return {
        "status": "PRIVATE_PREVIEW_STAGED",
        "activityCount": expected_count,
        "sourceLocationReceipts": expected_count,
        "boundedPhysicsReceipts": expected_count,
        "fullAcademicPassCount": 0,
        "academicQA": "REVIEW_REQUIRED",
        "publicationAuthorized": False,
        "stagedFileSha256": staged,
    }
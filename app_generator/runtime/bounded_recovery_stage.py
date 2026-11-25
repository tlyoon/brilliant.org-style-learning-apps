"""Optional, checkpointed original-source rollback inside the normal academic run.

The run-specific manifest is private and explicit: never invent a baseline or
silently repair arbitrary generated STEM content. Recovery never installs data.
"""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
from typing import Any

from app_generator.runtime.run_context import RunContext
from app_generator.validation.bounded_activity_rollback import restore_known_bounded_version

REQUEST_NAME = "bounded-recovery-request.json"
STAGE_NAME = "bounded-academic-recovery"
OUT_NAME = "bounded-academic-restored"


def maybe_run_bounded_recovery(
    *, run: RunContext, repository: Path, package_file: Path, source_pdf: Path | None,
) -> dict[str, Any] | None:
    request_file = run.validation / REQUEST_NAME
    if not request_file.is_file():
        return None
    if run.validation.resolve().is_relative_to(repository.resolve()):
        raise ValueError("private recovery validation must be outside Git")
    if source_pdf is None or not source_pdf.is_file():
        raise ValueError("source PDF required for optional academic rollback")
    request = json.loads(request_file.read_text(encoding="utf-8"))
    if not isinstance(request, dict) or set(request) != {
        "version", "baselineFile", "dossierFile", "baselineSha256", "sourceSha256"
    } or request["version"] != 1:
        raise ValueError("invalid private academic recovery request schema")
    for key in ("baselineSha256", "sourceSha256"):
        val = request[key]
        if not isinstance(val, str) or len(val) != 64 or any(c not in "0123456789abcdef" for c in val):
            raise ValueError("academic recovery requires exact SHA-256 identity")
    private_files = []
    for name in ("baselineFile", "dossierFile"):
        value = request[name]
        if not isinstance(value, str):
            raise ValueError("private academic recovery file path invalid")
        raw = Path(value)
        if not raw.is_absolute() or not raw.is_file():
            raise ValueError("private academic recovery file absent")
        path = raw.resolve()
        if path.is_relative_to(repository.resolve()):
            raise ValueError("private academic receipt cannot be read from Git")
        private_files.append(path)
    if private_files[0] == private_files[1]:
        raise ValueError("baseline and independent dossier must be distinct")
    original_sha = sha256(package_file.read_bytes()).hexdigest()
    provenance = {
        "packageSha256": original_sha,
        "sourceSha256": sha256(source_pdf.read_bytes()).hexdigest(),
        "manifestSha256": sha256(request_file.read_bytes()).hexdigest(),
        "baselineSha256": request["baselineSha256"],
        "baselineFileSha256": sha256(private_files[0].read_bytes()).hexdigest(),
        "dossierFileSha256": sha256(private_files[1].read_bytes()).hexdigest(),
    }
    old = run.load_stage(STAGE_NAME)
    if old is not None:
        if not isinstance(old, dict) or any(old.get(k) != v for k, v in provenance.items()):
            raise ValueError("stale or conflicting academic recovery checkpoint")
        return {
            "nextAction": ("AUTO_INDEPENDENT_SEMANTIC_VISUAL_REVIEW"
                           if old.get("state") == "COMPLETE"
                           else "RECONCILE_PREVIOUS_ATTEMPT"),
            "state": old.get("state"), "publicationAuthorized": False,
            "academicQA": "REVIEW_REQUIRED",
        }
    run.save_stage(STAGE_NAME, {**provenance, "state": "IN_FLIGHT"})
    try:
        report = restore_known_bounded_version(
            candidate_file=package_file,
            baseline_file=private_files[0], source_pdf=source_pdf,
            baseline_dossier_file=private_files[1],
            expected_baseline_sha256=request["baselineSha256"],
            expected_source_sha256=request["sourceSha256"],
            private_output_dir=run.validation / OUT_NAME,
        )
    except (ValueError, KeyError, OSError, TypeError, json.JSONDecodeError) as exc:
        run.save_stage(STAGE_NAME, {**provenance, "state": "BLOCKED",
                                   "errorClass": type(exc).__name__})
        return {"nextAction": "AUTO_SOURCE_CHECK", "state": "BLOCKED",
                "errorClass": type(exc).__name__, "academicQA": "REVIEW_REQUIRED",
                "publicationAuthorized": False}
    run.save_stage(STAGE_NAME, {**provenance, "state": "COMPLETE",
                               "restoredPackageSha256": report["restoredPackageSha256"]})
    return {
        "activityId": report["activityId"], "state": "COMPLETE",
        "restoredPackageSha256": report["restoredPackageSha256"],
        "nextAction": "AUTO_INDEPENDENT_SEMANTIC_VISUAL_REVIEW",
        "publicationAuthorized": False, "academicQA": "REVIEW_REQUIRED",
    }
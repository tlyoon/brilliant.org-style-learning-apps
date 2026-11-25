"""Local controlled-source identity verification; does not claim semantic fidelity."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
from app_generator.validation.academic_qa import Finding

def verify_source_identity(manifest_path: Path, source_path: Path | None = None) -> Finding:
    ref = str(manifest_path)
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return Finding("source_fidelity", "REVIEW_REQUIRED", "unavailable", ref, f"manifest unreadable: {type(exc).__name__}")
    sources = manifest.get("sources")
    sha = manifest.get("sha256")
    if (not isinstance(sources, list) or len(sources) != 1 or
        not isinstance(sources[0], dict) or sources[0].get("role") != "primary" or
        not isinstance(sha, str) or len(sha) != 64):
        return Finding("source_fidelity", "REVIEW_REQUIRED", "unavailable", ref, "controlled source identity ambiguous")
    if sources[0].get("sha256") != sha:
        return Finding("source_fidelity", "FAIL", "deterministic", ref, "conflicting manifest source hashes", True)
    if source_path is None or not source_path.is_file():
        return Finding("source_fidelity", "REVIEW_REQUIRED", "manifest_only", ref,
                       "claimed source hash present; no PDF bytes verified and no textbook fidelity assessed")
    digest = hashlib.sha256()
    with source_path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1048576), b""):
            digest.update(chunk)
    if digest.hexdigest() != sha:
        return Finding("source_fidelity", "FAIL", "deterministic", str(source_path),
                       "controlled PDF bytes do not match manifest", True)
    return Finding("source_fidelity", "REVIEW_REQUIRED", "deterministic", str(source_path),
                   "source bytes match manifest; activity claims still require independent source comparison", True)

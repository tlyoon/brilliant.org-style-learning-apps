"""Exact-parent V3 generated-text repair proposal, with immutable provenance.

A repair proposal is NOT a reassessment. It never amends an old model verdict
or the frozen source package. A separately versioned candidate must undergo
fresh independent Gemini checks and deterministic scope admission before use.
"""
from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import json
import os
import shutil
import tempfile
from pathlib import Path
from typing import Any

from app_generator.validation.autonomous_completion import package_identity
from app_generator.validation.v3_locale_script_integrity import script_findings

_MAX_PACKAGE_BYTES = 2_000_000
_MAX_REPLACEMENTS = 12


def make_locale_repair(raw: bytes, activity_id: str,
                       locale: str, changes: tuple[tuple[str, str], ...],
                       ) -> tuple[bytes, dict[str, Any]]:
    """Apply only exact, pre-reviewed text substitutions in one activity/locale."""
    if (not isinstance(raw, bytes) or len(raw) > _MAX_PACKAGE_BYTES
            or locale not in ("en", "ms", "zh")
            or not isinstance(activity_id, str) or not activity_id
            or not isinstance(changes, tuple)
            or not 1 <= len(changes) <= _MAX_REPLACEMENTS
            or len({old for old, _ in changes}) != len(changes)
            or any(not isinstance(old, str) or not isinstance(new, str)
                   or not old.strip() or not new.strip() or old == new
                   for old, new in changes)):
        raise ValueError("V3_REPAIR_INVALID_REQUEST")
    original_hash, activities = package_identity(raw)
    source = json.loads(raw.decode("utf-8"))
    if sum(activity["id"] == activity_id for activity in activities) != 1:
        raise ValueError("V3_REPAIR_ACTIVITY_NOT_UNIQUE")
    updated = deepcopy(source)
    index = next(i for i, a in enumerate(activities) if a["id"] == activity_id)
    activity = updated["activities"][index]
    counts = {old: 0 for old, _ in changes}
    modified_paths: list[str] = []

    def rewrite(value: Any, path: str) -> Any:
        if isinstance(value, list):
            return [rewrite(item, f"{path}[{i}]") for i, item in enumerate(value)]
        if isinstance(value, dict):
            output = {}
            for key, item in value.items():
                if key == locale and isinstance(item, str):
                    revised = item
                    for old, new in changes:
                        if old in revised:
                            counts[old] += revised.count(old)
                            revised = revised.replace(old, new)
                    if revised != item:
                        modified_paths.append(f"{path}.{key}")
                    output[key] = revised
                else:
                    output[key] = rewrite(item, f"{path}.{key}") if isinstance(
                        item, (dict, list)) else item
            return output
        return value

    updated["activities"][index] = rewrite(activity, f"activities[{index}]")
    if not modified_paths or any(count == 0 for count in counts.values()):
        raise ValueError("V3_REPAIR_EXPECTED_SOURCE_TEXT_NOT_PRESENT")
    # Independently enforce the scope and unmodified activity identities.
    for j, (old, new) in enumerate(zip(source["activities"], updated["activities"])):
        if j != index and old != new:
            raise ValueError("V3_REPAIR_UNRELATED_ACTIVITY_CHANGED")
    if script_findings(updated):
        raise ValueError("V3_REPAIR_UNRESOLVED_SCRIPT_CONTAMINATION")
    new_bytes = (json.dumps(updated, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    new_hash, new_activities = package_identity(new_bytes)
    if (new_hash == original_hash
            or [a["id"] for a in new_activities] != [a["id"] for a in activities]):
        raise ValueError("V3_REPAIR_INVALID_RESULT")
    return new_bytes, {
        "contract": "BOSLA_V3_IMMUTABLE_VERSIONED_TEXT_REPAIR",
        "parentPackageSha256": original_hash,
        "candidatePackageSha256": new_hash,
        "activityId": activity_id,
        "activityIndex": index,
        "locale": locale,
        "changedFieldPaths": sorted(modified_paths),
        "replacementCounts": [{"oldSha256": sha256(old.encode()).hexdigest(),
                               "newSha256": sha256(new.encode()).hexdigest(),
                               "occurrences": counts[old]} for old, new in changes],
        "activityCount": len(activities),
        "status": "PENDING_FRESH_GEMINI_TWO_REVIEWER_QA",
        "publicationAuthorized": False,
        "parentModelVerdictModified": False,
        "newModelConsensusPassClaimed": False,
    }


def store_private_repair(out_root: Path, package: bytes, receipt: dict[str, Any],
                         *, authorization_to_publish: bool = False) -> Path:
    """Idempotent private candidate; never write into Git or overwrite."""
    if authorization_to_publish:
        raise ValueError("V3_REPAIR_NOT_PUBLICATION_AUTHORITY")
    repo = Path(__file__).resolve().parents[2]
    resolved_target = out_root.resolve()
    if resolved_target == repo or resolved_target.is_relative_to(repo):
        raise ValueError("V3_REPAIR_CANNOT_STORE_PRIVATE_TEXT_IN_GIT")
    if (not out_root.is_absolute() or out_root.is_symlink()
            or not isinstance(package, bytes)
            or receipt.get("candidatePackageSha256") != sha256(package).hexdigest()
            or receipt.get("publicationAuthorized") is not False
            or receipt.get("newModelConsensusPassClaimed") is not False):
        raise ValueError("V3_REPAIR_INVALID_PRIVATE_STORE")
    directory = out_root / receipt["candidatePackageSha256"]
    receipt_raw = (json.dumps(receipt, ensure_ascii=True, sort_keys=True,
                              indent=2) + "\n").encode("utf-8")
    def verify_existing() -> Path:
        if directory.is_symlink() or not directory.is_dir():
            raise ValueError("V3_REPAIR_UNSAFE_EXISTING_CANDIDATE")
        targets = (directory / "package.json", directory / "review-required.json")
        if any(p.is_symlink() or not p.is_file() for p in targets):
            raise ValueError("V3_REPAIR_UNSAFE_EXISTING_CANDIDATE")
        if targets[0].read_bytes() != package or targets[1].read_bytes() != receipt_raw:
            raise ValueError("V3_REPAIR_EXISTING_IDENTITY_CONFLICT")
        return directory

    if directory.exists() or directory.is_symlink():
        return verify_existing()
    out_root.mkdir(parents=True, exist_ok=True)
    # BSA-175: stage both complete fsynced files in a fresh SAME-FILESYSTEM
    # directory, then atomically promote the directory to the final SHA.
    # A killed worker before promotion cannot publish a half-written
    # candidate. Orphan temporary directories can be ignored/recovered on
    # the next authorized run; never silently overwrite a final candidate.
    stage = Path(tempfile.mkdtemp(prefix=".v3-repair-stage-", dir=out_root))
    try:
        for name, data in (("package.json", package),
                           ("review-required.json", receipt_raw)):
            with (stage / name).open("xb") as stream:
                stream.write(data)
                stream.flush()
                os.fsync(stream.fileno())
        try:
            stage.rename(directory)
        except OSError:
            # Another process may have atomically staged the SAME candidate.
            # A mismatch or partial final candidate always stops.
            if not (directory.exists() or directory.is_symlink()):
                raise
            return verify_existing()
        return directory
    finally:
        # On a normal exception, remove staged files. A hard crash may leave
        # this non-final folder; a fresh staging directory works next time.
        if stage.exists():
            shutil.rmtree(stage)

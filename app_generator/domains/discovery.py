"""Stage-0 textbook-level domain discovery and source-corpus binding."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math
import os
import tempfile
from pathlib import Path
from typing import Any, Callable, Iterable

from app_generator.domains.registry import DomainProfile, load_domain_registry, resolve_domain
from app_generator.errors import DomainDiscoveryError, DomainProfileRequiredError
from app_generator.generation.extraction import parse_json_response
from app_generator.llm.gemini_api import GeminiApiClient
from app_generator.sources.google_drive import DriveRestClient, ResolvedDriveSource

BINDING_SCHEMA_VERSION = "1.0"
UNSUPPORTED_DOMAIN = "unsupported"


@dataclass(frozen=True)
class DomainBinding:
    source_fingerprint: str
    domain_id: str
    domain_profile_version: str
    subject: str
    academic_level: str
    confidence: float
    sample_subchapters: tuple[str, ...]
    classifier_model: str
    selection: str

    def as_json(self) -> dict[str, Any]:
        return {
            "schemaVersion": BINDING_SCHEMA_VERSION,
            "sourceFingerprint": self.source_fingerprint,
            "domainId": self.domain_id,
            "domainProfileVersion": self.domain_profile_version,
            "subject": self.subject,
            "academicLevel": self.academic_level,
            "confidence": self.confidence,
            "sampleSubchapters": list(self.sample_subchapters),
            "classifierModel": self.classifier_model,
            "selection": self.selection,
        }


def domain_binding_path(config: Any) -> Path:
    return Path(config.state_dir).resolve().parent / "domain-binding.json"


def domain_status_path(config: Any) -> Path:
    return Path(config.state_dir).resolve().parent / "domain-discovery-status.json"


def source_inventory_fingerprint(inventory: Iterable[ResolvedDriveSource]) -> str:
    rows = sorted(
        (source.relative_path, source.job_key, source.file_id)
        for source in inventory
    )
    if not rows:
        raise DomainDiscoveryError("The Source Root contains no discoverable controlled source jobs")
    material = "\n".join(f"{path}\t{job_key}\t{file_id}" for path, job_key, file_id in rows)
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


def representative_sources(
    inventory: Iterable[ResolvedDriveSource], sample_count: int
) -> tuple[ResolvedDriveSource, ...]:
    sources = tuple(sorted(inventory, key=lambda item: _subchapter_sort_key(item.subchapter_id)))
    if not sources:
        return ()
    count = max(1, min(sample_count, len(sources)))
    if count == len(sources):
        return sources
    if count == 1:
        return (sources[len(sources) // 2],)
    indexes = []
    for position in range(count):
        index = round(position * (len(sources) - 1) / (count - 1))
        if index not in indexes:
            indexes.append(index)
    return tuple(sources[index] for index in indexes)


def _subchapter_sort_key(value: str) -> tuple[int, int, str]:
    try:
        chapter, section = value.split(".", 1)
        return int(chapter), int(section), value
    except (ValueError, TypeError):
        return (10**9, 10**9, value)


def _profiles(repo_root: Path) -> tuple[DomainProfile, ...]:
    registry = load_domain_registry(repo_root)
    profiles = tuple(
        resolve_domain(repo_root, str(item["id"]))
        for item in registry["domains"]
        if isinstance(item, dict) and isinstance(item.get("id"), str)
    )
    if not profiles:
        raise DomainDiscoveryError("No active domain profiles are registered")
    inactive = [profile.id for profile in profiles if profile.status != "active"]
    if inactive:
        raise DomainDiscoveryError(
            "Registered domain profile(s) are not active: " + ", ".join(sorted(inactive))
        )
    return profiles


def _load_binding(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def _write_json_atomic(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    except BaseException:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
        raise


def _write_binding(path: Path, binding: DomainBinding) -> None:
    _write_json_atomic(path, binding.as_json())


def _binding_profile(
    config: Any, payload: dict[str, Any] | None, fingerprint: str
) -> DomainProfile | None:
    if not payload or payload.get("schemaVersion") != BINDING_SCHEMA_VERSION:
        return None
    if payload.get("sourceFingerprint") != fingerprint:
        return None
    domain_id = payload.get("domainId")
    if not isinstance(domain_id, str) or not domain_id:
        return None
    try:
        profile = resolve_domain(Path(config.repo_root), domain_id)
    except (OSError, ValueError, json.JSONDecodeError):
        return None
    if payload.get("domainProfileVersion") != profile.profile_version:
        return None
    return profile


def _classification_prompt(
    sample_ids: tuple[str, ...], profiles: tuple[DomainProfile, ...]
) -> str:
    candidates = [
        {
            "id": profile.id,
            "displayName": profile.display_name,
            "subject": profile.manifest["subject"],
            "academicLevel": profile.manifest["academicLevel"],
            "profileVersion": profile.profile_version,
        }
        for profile in profiles
    ]
    return (
        "Stage 0 domain discovery. Treat every attached PDF as evidence from one textbook under one Source Root. "
        "The attachments correspond in order to these subchapter IDs: "
        + json.dumps(list(sample_ids))
        + ". Classify each sample independently, then classify the textbook as a whole. A mathematics-heavy chapter "
        "inside a physics textbook must not cause a subject switch. Use only the installed candidate domains below. "
        "Set matchedDomainId to an exact candidate id only when the textbook subject AND academic level are compatible. "
        "When selecting a candidate, copy that candidate's subject and academicLevel strings exactly into the whole-textbook result. "
        f"Otherwise set matchedDomainId to {UNSUPPORTED_DOMAIN!r}. Do not force a match. Set consistency to 'mixed' or 'ambiguous' "
        "when the samples do not support one coherent textbook-level classification. Keep subject and academicLevel concise. "
        "Do not quote the source. Return exactly the requested JSON object.\n\n"
        "INSTALLED DOMAIN CANDIDATES:\n"
        + json.dumps(candidates, ensure_ascii=False, indent=2)
    )


def _validate_detection(
    document: Any,
    *,
    sample_ids: tuple[str, ...],
    profiles: tuple[DomainProfile, ...],
    min_confidence: float,
) -> tuple[DomainProfile, float, str, str]:
    if not isinstance(document, dict):
        raise DomainDiscoveryError("Domain classifier did not return a JSON object")
    expected = {
        "subject", "academicLevel", "matchedDomainId", "confidence", "consistency", "sampleAssessments"
    }
    if set(document) != expected:
        raise DomainDiscoveryError("Domain classifier returned an unexpected response shape")
    matched = document.get("matchedDomainId")
    subject = document.get("subject")
    academic = document.get("academicLevel")
    confidence = document.get("confidence")
    consistency = document.get("consistency")
    assessments = document.get("sampleAssessments")
    if not isinstance(subject, str) or not subject.strip() or not isinstance(academic, str) or not academic.strip():
        raise DomainDiscoveryError("Domain classifier omitted subject or academic level")
    if not isinstance(confidence, (int, float)) or isinstance(confidence, bool) or not 0 <= float(confidence) <= 1:
        raise DomainDiscoveryError("Domain classifier returned an invalid confidence")
    if consistency not in {"consistent", "mixed", "ambiguous"}:
        raise DomainDiscoveryError("Domain classifier returned an invalid consistency state")
    candidate_ids = {profile.id for profile in profiles}
    if matched not in candidate_ids | {UNSUPPORTED_DOMAIN}:
        raise DomainDiscoveryError("Domain classifier selected an unregistered domain")
    if not isinstance(assessments, list) or len(assessments) != len(sample_ids):
        raise DomainDiscoveryError("Domain classifier did not assess every representative sample")
    assessment_by_id: dict[str, dict[str, Any]] = {}
    for item in assessments:
        if not isinstance(item, dict) or set(item) != {
            "subchapterId", "subject", "academicLevel", "matchedDomainId", "confidence"
        }:
            raise DomainDiscoveryError("Domain classifier returned an invalid sample assessment")
        subchapter_id = item.get("subchapterId")
        item_match = item.get("matchedDomainId")
        item_confidence = item.get("confidence")
        if subchapter_id in assessment_by_id or subchapter_id not in sample_ids:
            raise DomainDiscoveryError("Domain classifier returned duplicate or unexpected sample identifiers")
        if item_match not in candidate_ids | {UNSUPPORTED_DOMAIN}:
            raise DomainDiscoveryError("A sample assessment selected an unregistered domain")
        if not isinstance(item.get("subject"), str) or not item["subject"].strip():
            raise DomainDiscoveryError("A sample assessment omitted its subject")
        if not isinstance(item.get("academicLevel"), str) or not item["academicLevel"].strip():
            raise DomainDiscoveryError("A sample assessment omitted its academic level")
        if not isinstance(item_confidence, (int, float)) or isinstance(item_confidence, bool) or not 0 <= float(item_confidence) <= 1:
            raise DomainDiscoveryError("A sample assessment returned an invalid confidence")
        assessment_by_id[str(subchapter_id)] = item
    if set(assessment_by_id) != set(sample_ids):
        raise DomainDiscoveryError("Domain classifier sample identifiers do not match the requested representative set")
    if matched == UNSUPPORTED_DOMAIN:
        raise DomainProfileRequiredError(
            f"Detected textbook domain {subject.strip()!r} at academic level {academic.strip()!r}, "
            "but no compatible active domain profile is installed.",
            detail=(
                f"confidence={float(confidence):.3f}; samples={','.join(sample_ids)}; "
                "create and activate a matching profile under domains/ before generation"
            ),
        )
    if consistency != "consistent" or float(confidence) < min_confidence:
        raise DomainDiscoveryError(
            "Textbook-level domain classification is not confident and internally consistent enough to generate safely",
            detail=f"matched={matched}; confidence={float(confidence):.3f}; consistency={consistency}",
        )
    support = sum(1 for item in assessments if item["matchedDomainId"] == matched)
    required_support = max(1, math.ceil(len(sample_ids) * 0.67))
    conflicts = [
        item for item in assessments
        if item["matchedDomainId"] not in {matched, UNSUPPORTED_DOMAIN} and float(item["confidence"]) >= min_confidence
    ]
    if support < required_support or conflicts:
        raise DomainDiscoveryError(
            "Representative textbook samples disagree on the installed domain profile",
            detail=f"matched={matched}; supporting_samples={support}/{len(sample_ids)}",
        )
    profile = next(profile for profile in profiles if profile.id == matched)
    if subject.strip().casefold() != str(profile.manifest["subject"]).strip().casefold():
        raise DomainDiscoveryError("Classifier subject does not agree with the selected domain profile")
    if academic.strip().casefold() != str(profile.manifest["academicLevel"]).strip().casefold():
        raise DomainDiscoveryError("Classifier academic level does not agree with the selected domain profile")
    return profile, float(confidence), subject.strip(), academic.strip()


def ensure_drive_domain(
    config: Any,
    drive_client: DriveRestClient,
    inventory: tuple[ResolvedDriveSource, ...],
    *,
    client_factory: Callable[[Any, tuple[Path, ...]], Any] = GeminiApiClient,
) -> DomainProfile:
    """Resolve and bind one textbook-level domain before any source job is claimed."""

    profiles = _profiles(Path(config.repo_root))
    fingerprint = source_inventory_fingerprint(inventory)
    configured = str(getattr(config, "domain_id", "")).strip()
    binding_file = domain_binding_path(config)
    if configured and configured.casefold() != "auto":
        try:
            profile = resolve_domain(Path(config.repo_root), configured)
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            raise DomainProfileRequiredError(f"Configured domain profile {configured!r} is unavailable") from exc
        if profile.status != "active":
            raise DomainProfileRequiredError(f"Configured domain profile {configured!r} is not active")
        binding = DomainBinding(
            fingerprint, profile.id, profile.profile_version,
            str(profile.manifest["subject"]), str(profile.manifest["academicLevel"]),
            1.0, (), "explicit", "explicit",
        )
        _write_binding(binding_file, binding)
        status_file = domain_status_path(config)
        if status_file.exists():
            status_file.unlink()
        return profile

    cached = _binding_profile(config, _load_binding(binding_file), fingerprint)
    if cached is not None:
        status_file = domain_status_path(config)
        if status_file.exists():
            status_file.unlink()
        return cached

    sample_count = int(getattr(config, "domain_sample_count", 3))
    min_confidence = float(getattr(config, "domain_min_confidence", 0.85))
    samples = representative_sources(inventory, sample_count)
    if not samples:
        raise DomainDiscoveryError("No representative source PDFs are available for domain discovery")
    work_root = Path(config.state_dir).resolve().parent
    work_root.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="domain-discovery-", dir=work_root) as directory:
        sample_paths = tuple(
            drive_client.download_file(source, Path(directory) / f"{source.subchapter_id}-{source.filename}")
            for source in samples
        )
        client = client_factory(config, sample_paths)
        client.prepare()
        response = client.ask(
            _classification_prompt(tuple(source.subchapter_id for source in samples), profiles),
            stage="domain-discovery",
        )
        document = parse_json_response(response)
        model = str(getattr(client, "actual_model", "unknown"))
        try:
            profile, confidence, subject, academic = _validate_detection(
                document,
                sample_ids=tuple(source.subchapter_id for source in samples),
                profiles=profiles,
                min_confidence=min_confidence,
            )
        except (DomainProfileRequiredError, DomainDiscoveryError) as exc:
            _write_json_atomic(
                domain_status_path(config),
                {
                    "schemaVersion": BINDING_SCHEMA_VERSION,
                    "status": "profile-required" if isinstance(exc, DomainProfileRequiredError) else "ambiguous",
                    "sourceFingerprint": fingerprint,
                    "errorCode": exc.code,
                    "message": str(exc),
                    "detail": exc.detail or "",
                    "sampleSubchapters": [source.subchapter_id for source in samples],
                    "classifierModel": model,
                },
            )
            raise
    binding = DomainBinding(
        fingerprint, profile.id, profile.profile_version, subject, academic, confidence,
        tuple(source.subchapter_id for source in samples), model, "automatic",
    )
    _write_binding(binding_file, binding)
    status_file = domain_status_path(config)
    if status_file.exists():
        status_file.unlink()
    return profile

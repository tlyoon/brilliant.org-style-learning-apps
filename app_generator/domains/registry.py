"""Load versioned subject-domain profiles from the repository domains directory."""

from __future__ import annotations

from dataclasses import dataclass
import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

DOMAIN_REGISTRY_VERSION = "1.0"
DOMAIN_MANIFEST_VERSION = "1.0"


def _load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return data


@dataclass(frozen=True)
class DomainProfile:
    repo_root: Path
    directory: Path
    manifest: dict[str, Any]

    @property
    def id(self) -> str:
        return str(self.manifest["id"])

    @property
    def display_name(self) -> str:
        return str(self.manifest["displayName"])

    def path(self, section: str, key: str) -> Path:
        section_data = self.manifest.get(section)
        if not isinstance(section_data, dict) or not isinstance(section_data.get(key), str):
            raise ValueError(f"Domain {self.id!r} does not declare {section}.{key}")
        candidate = (self.directory / section_data[key]).resolve()
        try:
            candidate.relative_to(self.directory.resolve())
        except ValueError as exc:
            raise ValueError(f"Domain {self.id!r} path escapes its directory: {section}.{key}") from exc
        return candidate

    @property
    def trusted_renderers(self) -> dict[str, tuple[str, str]]:
        raw = self.manifest.get("trustedRenderers", {})
        if not isinstance(raw, dict):
            raise ValueError(f"Domain {self.id!r} trustedRenderers must be an object")
        result: dict[str, tuple[str, str]] = {}
        for template_id, pair in raw.items():
            if not isinstance(template_id, str) or not isinstance(pair, list) or len(pair) != 2 or not all(isinstance(value, str) and value for value in pair):
                raise ValueError(f"Domain {self.id!r} contains an invalid trusted renderer entry")
            result[template_id] = (pair[0], pair[1])
        return result

    def load_module(self, section: str, key: str) -> ModuleType:
        path = self.path(section, key)
        if not path.is_file():
            raise ValueError(f"Domain {self.id!r} module does not exist: {path}")
        safe_id = self.id.replace("-", "_")
        module_name = f"learning_app_domain_{safe_id}_{section}_{key}"
        spec = importlib.util.spec_from_file_location(module_name, path)
        if spec is None or spec.loader is None:
            raise ValueError(f"Cannot load domain module: {path}")
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        try:
            spec.loader.exec_module(module)
        except Exception:
            sys.modules.pop(module_name, None)
            raise
        return module


def load_domain_registry(repo_root: Path) -> dict[str, Any]:
    path = repo_root.resolve() / "domains" / "registry.json"
    registry = _load_json(path)
    if registry.get("schemaVersion") != DOMAIN_REGISTRY_VERSION:
        raise ValueError("Unsupported domain registry version")
    domains = registry.get("domains")
    if not isinstance(domains, list) or not domains:
        raise ValueError("Domain registry must contain at least one domain")
    return registry


def resolve_domain(repo_root: Path, domain_id: str | None = None) -> DomainProfile:
    repo_root = repo_root.resolve()
    registry = load_domain_registry(repo_root)
    selected = domain_id or registry.get("defaultDomainId")
    if not isinstance(selected, str) or not selected:
        raise ValueError("Domain registry defaultDomainId is missing")
    matches = [item for item in registry["domains"] if isinstance(item, dict) and item.get("id") == selected]
    if len(matches) != 1:
        raise ValueError(f"Domain {selected!r} is not uniquely registered")
    relative = matches[0].get("path")
    if not isinstance(relative, str) or not relative:
        raise ValueError(f"Domain {selected!r} has no directory path")
    directory = (repo_root / "domains" / relative).resolve()
    domains_root = (repo_root / "domains").resolve()
    try:
        directory.relative_to(domains_root)
    except ValueError as exc:
        raise ValueError(f"Domain {selected!r} path escapes domains/") from exc
    manifest = _load_json(directory / "domain.json")
    if manifest.get("schemaVersion") != DOMAIN_MANIFEST_VERSION:
        raise ValueError(f"Domain {selected!r} has unsupported manifest version")
    if manifest.get("id") != selected:
        raise ValueError(f"Domain manifest id {manifest.get('id')!r} does not match registry id {selected!r}")
    if manifest.get("status") != "active":
        raise ValueError(f"Domain {selected!r} is not active")
    return DomainProfile(repo_root=repo_root, directory=directory, manifest=manifest)


def domain_registry_errors(repo_root: Path) -> list[str]:
    """Validate all registered active domain manifests and their declared assets."""
    errors: list[str] = []
    try:
        registry = load_domain_registry(repo_root)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return [f"domain registry: {exc}"]
    entries = registry.get("domains", [])
    ids = [item.get("id") for item in entries if isinstance(item, dict)]
    paths = [item.get("path") for item in entries if isinstance(item, dict)]
    if len(ids) != len(entries) or any(not isinstance(value, str) or not value for value in ids):
        errors.append("domain registry: every entry requires a non-empty id")
    if len(ids) != len(set(ids)):
        errors.append("domain registry: domain ids must be unique")
    if len(paths) != len(entries) or any(not isinstance(value, str) or not value for value in paths):
        errors.append("domain registry: every entry requires a non-empty path")
    if len(paths) != len(set(paths)):
        errors.append("domain registry: domain paths must be unique")
    if registry.get("defaultDomainId") not in set(ids):
        errors.append("domain registry: defaultDomainId must reference a registered domain")
    required_paths = (
        ("instructions", "sourceAnalysis"),
        ("instructions", "activityGeneration"),
        ("instructions", "visualGeneration"),
        ("instructions", "semanticAudit"),
        ("instructions", "repair"),
        ("rules", "content"),
        ("rules", "visual"),
        ("visuals", "templateRegistry"),
        ("visuals", "styleProfiles"),
        ("visuals", "rendererScript"),
        ("visuals", "stylesheet"),
        ("simulations", "modelRegistry"),
        ("simulations", "modelsModule"),
        ("validation", "visualValidatorModule"),
        ("verification", "policy"),
    )
    for domain_id in ids:
        if not isinstance(domain_id, str):
            continue
        try:
            profile = resolve_domain(repo_root, domain_id)
            if not profile.display_name.strip():
                errors.append(f"domain {domain_id}: displayName must be non-empty")
            if not isinstance(profile.manifest.get("subject"), str) or not profile.manifest["subject"].strip():
                errors.append(f"domain {domain_id}: subject must be non-empty")
            if not isinstance(profile.manifest.get("academicLevel"), str) or not profile.manifest["academicLevel"].strip():
                errors.append(f"domain {domain_id}: academicLevel must be non-empty")
            for section, key in required_paths:
                path = profile.path(section, key)
                if not path.is_file():
                    errors.append(f"domain {domain_id}: missing {section}.{key}: {path.relative_to(repo_root)}")
            profile.trusted_renderers
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            errors.append(f"domain {domain_id}: {exc}")
    return errors

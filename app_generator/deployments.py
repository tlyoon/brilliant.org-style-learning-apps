"""Tracked public-deployment registry and generated-package inventory."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from app_generator.errors import ConfigurationError


DEFAULT_DEPLOYMENT_REGISTRY = Path("config/deployments.json")


@dataclass(frozen=True)
class DeploymentRecord:
    app_id: str
    label: str
    package_path: Path
    deployment_repository: str
    public_url: str
    deployed: bool
    variant: str = ""


@dataclass(frozen=True)
class DeploymentRow:
    app_id: str
    label: str
    package_path: str
    generated: bool
    deployed: bool
    public_url: str


def _require_text(item: dict[str, object], key: str) -> str:
    value = item.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ConfigurationError(f"Deployment registry entry requires non-empty {key}")
    return value.strip()


def load_deployment_registry(
    repo_root: Path,
    registry_path: Path = DEFAULT_DEPLOYMENT_REGISTRY,
) -> tuple[DeploymentRecord, ...]:
    root = repo_root.resolve()
    path = registry_path if registry_path.is_absolute() else root / registry_path
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ConfigurationError(f"Deployment registry does not exist: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ConfigurationError(f"Deployment registry is invalid JSON: {path}: {exc}") from exc

    if not isinstance(payload, dict) or payload.get("schemaVersion") != "1.0":
        raise ConfigurationError("Deployment registry must use schemaVersion 1.0")
    raw_entries = payload.get("deployments")
    if not isinstance(raw_entries, list):
        raise ConfigurationError("Deployment registry deployments must be a list")

    records: list[DeploymentRecord] = []
    seen_ids: set[str] = set()
    seen_urls: set[str] = set()
    for raw in raw_entries:
        if not isinstance(raw, dict):
            raise ConfigurationError("Deployment registry entries must be objects")
        app_id = _require_text(raw, "appId")
        if app_id in seen_ids:
            raise ConfigurationError(f"Duplicate deployment appId: {app_id}")
        seen_ids.add(app_id)

        package_path = Path(_require_text(raw, "packagePath"))
        if package_path.is_absolute() or ".." in package_path.parts:
            raise ConfigurationError(f"Deployment packagePath must stay inside the repository: {package_path}")

        deployed = raw.get("deployed")
        if not isinstance(deployed, bool):
            raise ConfigurationError(f"Deployment {app_id} requires boolean deployed")

        public_url = _require_text(raw, "publicUrl") if deployed else str(raw.get("publicUrl", "")).strip()
        if deployed:
            if not public_url.startswith("https://"):
                raise ConfigurationError(f"Deployment {app_id} publicUrl must use https://")
            if public_url in seen_urls:
                raise ConfigurationError(f"Duplicate deployment publicUrl: {public_url}")
            seen_urls.add(public_url)

        variant = str(raw.get("variant", "")).strip()
        records.append(
            DeploymentRecord(
                app_id=app_id,
                label=_require_text(raw, "label"),
                package_path=package_path,
                deployment_repository=_require_text(raw, "deploymentRepository"),
                public_url=public_url,
                deployed=deployed,
                variant=variant,
            )
        )
    return tuple(records)


def discover_generated_packages(repo_root: Path) -> tuple[Path, ...]:
    root = repo_root.resolve()
    content_root = root / "content"
    if not content_root.is_dir():
        return ()
    return tuple(
        sorted(
            path.relative_to(root)
            for path in content_root.glob("chapter-*/section-*/package.json")
            if path.is_file()
        )
    )


def deployment_rows(
    repo_root: Path,
    registry_path: Path = DEFAULT_DEPLOYMENT_REGISTRY,
) -> tuple[DeploymentRow, ...]:
    root = repo_root.resolve()
    records = load_deployment_registry(root, registry_path)
    generated_packages = discover_generated_packages(root)
    registered_packages = {record.package_path for record in records}

    rows = [
        DeploymentRow(
            app_id=record.app_id,
            label=record.label,
            package_path=record.package_path.as_posix(),
            generated=(root / record.package_path).is_file(),
            deployed=record.deployed,
            public_url=record.public_url,
        )
        for record in records
    ]

    for package_path in generated_packages:
        if package_path in registered_packages:
            continue
        try:
            payload = json.loads((root / package_path).read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            package_id = package_path.parent.name
        else:
            package_id = str(payload.get("packageId") or package_path.parent.name)
        rows.append(
            DeploymentRow(
                app_id=package_id,
                label=package_id,
                package_path=package_path.as_posix(),
                generated=True,
                deployed=False,
                public_url="",
            )
        )

    return tuple(sorted(rows, key=lambda row: (row.package_path, row.app_id)))


def render_deployments(rows: tuple[DeploymentRow, ...]) -> str:
    headers = ("APP", "GENERATED", "DEPLOYED", "URL")
    data = [
        (
            row.label,
            "yes" if row.generated else "no",
            "yes" if row.deployed else "no",
            row.public_url or "-",
        )
        for row in rows
    ]
    widths = [
        max(len(headers[index]), *(len(row[index]) for row in data))
        if data
        else len(headers[index])
        for index in range(len(headers))
    ]
    lines = [
        "  ".join(headers[index].ljust(widths[index]) for index in range(len(headers))),
        "  ".join("-" * widths[index] for index in range(len(headers))),
    ]
    lines.extend(
        "  ".join(row[index].ljust(widths[index]) for index in range(len(headers)))
        for row in data
    )
    return "\n".join(lines)

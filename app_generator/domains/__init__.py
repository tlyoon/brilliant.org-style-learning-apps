"""Domain-profile resolution and Stage-0 discovery."""

from app_generator.domains.prompting import compose_domain_prompt, instruction_key_for_stage
from app_generator.domains.discovery import (
    DomainBinding,
    domain_binding_path,
    domain_status_path,
    ensure_drive_domain,
    representative_sources,
    source_inventory_fingerprint,
)
from app_generator.domains.registry import (
    DomainProfile,
    domain_registry_errors,
    load_domain_registry,
    package_domain_errors,
    resolve_domain,
    resolve_package_domain,
)

__all__ = [
    "DomainBinding",
    "DomainProfile",
    "domain_binding_path",
    "domain_status_path",
    "domain_registry_errors",
    "ensure_drive_domain",
    "load_domain_registry",
    "representative_sources",
    "compose_domain_prompt",
    "instruction_key_for_stage",
    "package_domain_errors",
    "resolve_package_domain",
    "resolve_domain",
    "source_inventory_fingerprint",
]

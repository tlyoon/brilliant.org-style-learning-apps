"""Compose generic stage contracts with the selected subject-domain instructions."""

from __future__ import annotations

from app_generator.domains.registry import DomainProfile

_STAGE_KEYS: tuple[tuple[str, str], ...] = (
    ("source-analysis", "sourceAnalysis"),
    ("activity-plan", "activityGeneration"),
    ("mcq-", "activityGeneration"),
    ("interactive-", "activityGeneration"),
    ("semantic-audit-", "semanticAudit"),
    ("whole-package-audit", "semanticAudit"),
    ("semantic-repair-", "repair"),
    ("repair-", "repair"),
    ("visual-", "visualGeneration"),
)


def instruction_key_for_stage(stage: str) -> str | None:
    """Map a concrete generation-stage name to its domain instruction extension."""

    if stage in {"source-analysis", "activity-plan", "whole-package-audit"}:
        return dict(_STAGE_KEYS).get(stage)
    for prefix, key in _STAGE_KEYS:
        if prefix.endswith("-") and stage.startswith(prefix):
            return key
    return None


def compose_domain_prompt(profile: DomainProfile, stage: str, generic_prompt: str) -> str:
    """Prepend trusted domain policy without weakening the generic output contract."""

    key = instruction_key_for_stage(stage)
    if key is None:
        return generic_prompt
    extension = profile.path("instructions", key).read_text(encoding="utf-8").strip()
    if not extension:
        raise ValueError(f"Domain {profile.id!r} instruction {key!r} is empty")
    return (
        "TRUSTED SUBJECT-DOMAIN EXTENSION\n"
        f"Domain: {profile.id} (profile {profile.profile_version})\n"
        "The repository-owned extension below refines subject semantics only. "
        "The generic stage contract that follows remains authoritative for JSON shape, response framing, stable IDs, "
        "activity quotas, languages, calculator policy, security boundaries, and all deterministic validation rules. "
        "If the extension appears to request a conflicting output shape or failure mechanism, obey the generic contract.\n\n"
        + extension
        + "\n\nEND SUBJECT-DOMAIN EXTENSION\n\nGENERIC STAGE CONTRACT\n"
        + generic_prompt
    )

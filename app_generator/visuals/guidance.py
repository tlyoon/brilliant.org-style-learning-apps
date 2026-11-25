"""Validate prompt-facing renderer guidance against the actual visual schema.

Guidance is deliberately NOT an independent renderer contract. This check
prevents examples and required property names from contradicting validation.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from jsonschema import Draft202012Validator


def renderer_guidance_errors(
    repo_root: Path, guidance_path: Path, available_templates: set[str],
) -> list[str]:
    if not guidance_path.is_file():
        return []  # Other domain profiles may not yet have visual guidance.
    try:
        guidance = json.loads(guidance_path.read_text(encoding="utf-8"))
        schema = json.loads((repo_root / "content/schema/visual-spec.schema.json").read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(schema)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return [f"renderer guidance: {exc}"]
    if not isinstance(guidance, dict) or guidance.get("schemaVersion") != "1.0":
        return ["renderer guidance: schemaVersion must be 1.0"]
    templates = guidance.get("templates")
    if not isinstance(templates, dict):
        return ["renderer guidance: templates must be an object"]
    errors: list[str] = []
    unknown = sorted(set(templates) - available_templates)
    missing = sorted(available_templates - set(templates))
    if unknown:
        errors.append(f"renderer guidance: unknown or unimplemented template IDs: {', '.join(unknown)}")
    if missing:
        errors.append(f"renderer guidance: missing available template IDs: {', '.join(missing)}")
    entity_validator = Draft202012Validator({"$defs": schema["$defs"], "$ref": "#/$defs/entity"})
    for name, record in templates.items():
        if not isinstance(record, dict):
            errors.append(f"renderer guidance {name}: must be an object")
            continue
        examples = record.get("exampleEntities", [])
        if not isinstance(examples, list):
            errors.append(f"renderer guidance {name}: exampleEntities must be a list")
            continue
        required = record.get("requiredEntities")
        if required is not None:
            if not isinstance(required, dict):
                errors.append(f"renderer guidance {name}: requiredEntities must be an object")
                continue
            count_min, count_max = required.get("min"), required.get("max")
            if any(type(x) is not int for x in (count_min, count_max)) or not 1 <= count_min <= count_max <= 4:
                errors.append(f"renderer guidance {name}: entity count must be bounded from 1 to 4")
            if not isinstance(required.get("kind"), str) or not required["kind"]:
                errors.append(f"renderer guidance {name}: required entity kind missing")
        property_rules = record.get("requiredEntityProperties", {})
        if not isinstance(property_rules, dict):
            errors.append(f"renderer guidance {name}: requiredEntityProperties must be an object")
            continue
        aliases = record.get("forbiddenPropertyAliases", [])
        if not isinstance(aliases, list) or any(not isinstance(a, str) for a in aliases):
            errors.append(f"renderer guidance {name}: forbiddenPropertyAliases must be a string list")
            continue
        if set(aliases).intersection(property_rules):
            errors.append(f"renderer guidance {name}: forbidden aliases overlap required properties")
        for index, example in enumerate(examples):
            invalid = list(entity_validator.iter_errors(example))
            for item in invalid:
                errors.append(f"renderer guidance {name}.exampleEntities[{index}]: {item.message}")
            if not isinstance(example, dict):
                continue
            if isinstance(required, dict) and example.get("kind") != required.get("kind"):
                errors.append(f"renderer guidance {name}.exampleEntities[{index}]: wrong entity kind")
            props = example.get("properties", {})
            for key, rule in property_rules.items():
                if key not in props:
                    errors.append(f"renderer guidance {name}.exampleEntities[{index}]: missing {key}")
                    continue
                value = props[key]
                if rule.get("type") == "number" and (
                    type(value) not in (float, int)
                    or value < rule.get("minimum", float("-inf"))
                    or value > rule.get("maximum", float("inf"))
                ):
                    errors.append(f"renderer guidance {name}.exampleEntities[{index}]: {key} violates numeric bounds")
            if set(props).intersection(aliases):
                errors.append(f"renderer guidance {name}.exampleEntities[{index}]: contains forbidden alias")
    return errors

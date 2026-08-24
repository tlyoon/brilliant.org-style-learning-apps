"""Staged generation protocol with resumable local state."""

from __future__ import annotations

from collections import Counter
from collections.abc import Callable
from copy import deepcopy
from typing import Any, Protocol

from app_generator.generation.assembler import assemble_package, validate_activity_batch, validate_plan
from app_generator.generation.extraction import parse_json_response
from app_generator.errors import ResponseContractError, ValidationFailure
from app_generator.prompts import (
    activity_batch_prompt,
    activity_plan_prompt,
    repair_activity_prompt,
    semantic_audit_prompt,
    source_analysis_prompt,
    whole_package_audit_prompt,
)
from app_generator.runtime.run_context import RunContext


class ConversationPort(Protocol):
    def ask(self, prompt: str) -> str: ...


class GenerationProtocol:
    def __init__(self, conversation: ConversationPort, context: RunContext) -> None:
        self.conversation = conversation
        self.context = context

    def _stage(self, name: str, prompt_factory: Callable[[], str]) -> Any:
        existing = self.context.load_stage(name)
        if existing is not None:
            return existing
        response = self.conversation.ask(prompt_factory())
        self.context.save_raw_response(name, response)
        parsed = parse_json_response(response)
        self.context.save_stage(name, parsed)
        return parsed

    @staticmethod
    def _normalize_source_analysis(document: Any) -> Any:
        if not isinstance(document, dict):
            return document
        normalized = deepcopy(document)
        contracts = {
            "prerequisites": {"id", "description", "recovery"},
            "misconceptionCatalogue": {"id", "description"},
        }
        for collection, allowed in contracts.items():
            values = normalized.get(collection)
            if not isinstance(values, list):
                continue
            normalized[collection] = [
                {key: value for key, value in item.items() if key in allowed}
                if isinstance(item, dict)
                else item
                for item in values
            ]
        return normalized

    @staticmethod
    def _valid_source_analysis(document: Any) -> bool:
        if not isinstance(document, dict) or set(document) != {
            "learningObjectives", "prerequisites", "misconceptionCatalogue", "scopeNotes",
        }:
            return False
        if not all(
            isinstance(document.get(key), list) and bool(document[key])
            for key in ("learningObjectives", "prerequisites", "misconceptionCatalogue")
        ):
            return False
        scope = document.get("scopeNotes")
        return isinstance(scope, dict) and all(
            isinstance(scope.get(key), list) and bool(scope[key])
            for key in ("includedConcepts", "excludedConcepts")
        )

    def _source_analysis(self, run_metadata: dict[str, Any]) -> dict[str, Any]:
        for attempt in range(2):
            document = self._stage("source-analysis", lambda: source_analysis_prompt(run_metadata))
            normalized = self._normalize_source_analysis(document)
            if normalized != document:
                self.context.save_stage("source-analysis", normalized)
            document = normalized
            if self._valid_source_analysis(document):
                return document
            # A wrong-but-valid JSON response must not poison the plan and all
            # later resumed stages. Retain raw responses, but rebuild every
            # parsed stage from the corrected source analysis.
            self.context.discard_parsed_stages()
            if attempt == 1:
                break
        raise ResponseContractError("Source analysis did not satisfy its exact stage contract")

    @staticmethod
    def _assert_stable_activity_contract(original: dict[str, Any], replacement: dict[str, Any]) -> None:
        for field in ("id", "type", "difficulty", "objective", "interactionMode"):
            if original.get(field) != replacement.get(field):
                raise ValueError(f"Repair attempted to change stable activity field {field} for {original.get('id')}")
        if set(original.get("misconceptions", [])) != set(replacement.get("misconceptions", [])):
            raise ValueError(f"Repair attempted to change stable misconceptions for {original.get('id')}")
        original_recovery = original.get("prerequisiteRecovery", {}).get("prerequisiteId")
        replacement_recovery = replacement.get("prerequisiteRecovery", {}).get("prerequisiteId")
        if original_recovery and original_recovery != replacement_recovery:
            raise ValueError(f"Repair attempted to change the prerequisite for {original.get('id')}")
        for path in (("answerKey", "options"), ("interaction", "items"), ("interaction", "targets")):
            old_items = original.get(path[0], {}).get(path[1], [])
            new_items = replacement.get(path[0], {}).get(path[1], [])
            old_ids = {item.get("id") for item in old_items if isinstance(item, dict) and item.get("id")}
            new_ids = {item.get("id") for item in new_items if isinstance(item, dict) and item.get("id")}
            if old_ids and not old_ids.issubset(new_ids):
                raise ValueError(
                    f"Repair attempted to remove or rename stable {path[1]} IDs for {original.get('id')}"
                )

    @staticmethod
    def _assert_complete_interaction_solution(activity: dict[str, Any]) -> None:
        if activity.get("type") != "interactive":
            return
        interaction = activity.get("interaction", {})
        item_ids = [item.get("id") for item in interaction.get("items", [])]
        mode = activity.get("interactionMode")
        if mode == "ordering" and Counter(interaction.get("correctOrder", [])) != Counter(item_ids):
            raise ResponseContractError("Ordering repair must order every item ID exactly once")
        if mode in {"classification", "matching"}:
            placements = interaction.get("placements", [])
            placed_items = [placement.get("itemId") for placement in placements]
            target_ids = [target.get("id") for target in interaction.get("targets", [])]
            placed_targets = [placement.get("targetId") for placement in placements]
            if Counter(placed_items) != Counter(item_ids):
                raise ResponseContractError("Placement repair must place every item ID exactly once")
            if any(target not in target_ids for target in placed_targets):
                raise ResponseContractError("Placement repair references an unknown target ID")
            if mode == "matching" and set(placed_targets) != set(target_ids):
                raise ResponseContractError("Matching repair must use every target ID")
        if mode == "selection":
            selections = interaction.get("correctSelections", [])
            if any(item not in item_ids for item in selections) or len(selections) >= len(item_ids):
                raise ResponseContractError("Selection repair must select declared items and leave one unselected")

    def _repair_stage(
        self,
        name: str,
        original: dict[str, Any],
        prompt_factory: Callable[[], str],
    ) -> dict[str, Any]:
        for attempt in range(3):
            try:
                replacement = self._stage(name, prompt_factory)
                if not isinstance(replacement, dict):
                    raise ResponseContractError("Activity repair must return one complete activity object")
                self._assert_stable_activity_contract(original, replacement)
                plan = {
                    key: original.get(key)
                    for key in (
                        "id", "type", "difficulty", "objective", "misconceptions", "interactionMode",
                    )
                }
                recovery = original.get("prerequisiteRecovery")
                plan["prerequisiteId"] = (
                    recovery.get("prerequisiteId") if isinstance(recovery, dict) else None
                )
                validate_activity_batch({"activities": [replacement]}, [plan])
                self._assert_complete_interaction_solution(replacement)
                return replacement
            except (ResponseContractError, ValueError):
                self.context.discard_stage(name)
                if attempt == 2:
                    raise ResponseContractError(
                        f"Activity repair for {original.get('id')} did not preserve its stable contract"
                    )
        raise AssertionError("unreachable")

    def _audit_stage(self, name: str, prompt_factory: Callable[[], str]) -> dict[str, Any]:
        for attempt in range(3):
            try:
                audit = self._stage(name, prompt_factory)
                if not isinstance(audit, dict) or set(audit) != {"findings"}:
                    raise ResponseContractError("Audit must contain exactly one findings key")
                findings = audit["findings"]
                if not isinstance(findings, list):
                    raise ResponseContractError("Audit findings must be an array")
                required = {"activityId", "severity", "code", "message"}
                if any(
                    not isinstance(finding, dict)
                    or not required.issubset(finding)
                    or finding.get("severity") not in {"blocker", "warning"}
                    for finding in findings
                ):
                    raise ResponseContractError("Audit returned an invalid finding object")
                return audit
            except ResponseContractError:
                self.context.discard_stage(name)
                if attempt == 2:
                    raise ResponseContractError(
                        f"Audit stage {name} did not return its exact findings contract"
                    )
        raise AssertionError("unreachable")

    def _activity_batch(
        self,
        name: str,
        analysis: dict[str, Any],
        planned: list[dict[str, Any]],
        source_location: str,
    ) -> dict[str, Any]:
        single_names = [f"{name}-{item['id']}" for item in planned]
        has_partial_fallback = any(self.context.load_stage(single_name) is not None for single_name in single_names)
        if not has_partial_fallback:
            for _ in range(2):
                try:
                    batch = self._stage(
                        name,
                        lambda: activity_batch_prompt(analysis, planned, source_location=source_location),
                    )
                    validate_activity_batch(batch, planned)
                    return batch
                except ResponseContractError:
                    # Retain the raw response for diagnosis, but never reuse a
                    # parsed batch that violates the immutable plan or schema.
                    self.context.discard_stage(name)
        try:
            activities: list[dict[str, Any]] = []
            for item in planned:
                single_name = f"{name}-{item['id']}"
                single: Any = None
                for cache_attempt in range(3):
                    try:
                        single = self._stage(
                            single_name,
                            lambda item=item: activity_batch_prompt(
                                analysis,
                                [item],
                                source_location=source_location,
                            ),
                        )
                        validate_activity_batch(single, [item])
                    except ResponseContractError:
                        # Parsing and schema failures are both retryable for a
                        # bounded single-activity fallback.
                        self.context.discard_stage(single_name)
                        if cache_attempt < 2:
                            continue
                        raise ResponseContractError(
                            f"Single-activity fallback for {item['id']} returned an invalid batch"
                        )
                    else:
                        break
                activities.extend(single["activities"])
            combined = {"activities": activities}
            self.context.save_stage(name, combined)
            return combined
        except ResponseContractError:
            raise

    def generate(
        self,
        *,
        config: Any,
        run_metadata: dict[str, Any],
        source_location: str,
    ) -> tuple[dict[str, Any], dict[str, Any], list[dict[str, Any]]]:
        analysis = self._source_analysis(run_metadata)
        plan = self._stage("activity-plan", lambda: activity_plan_prompt(analysis))
        prerequisite_ids = [
            item.get("id")
            for item in analysis.get("prerequisites", [])
            if isinstance(item, dict) and isinstance(item.get("id"), str) and item.get("id")
        ]
        try:
            planned = validate_plan(
                plan,
                fallback_prerequisite_id=prerequisite_ids[0] if prerequisite_ids else None,
            )
        except ResponseContractError:
            self.context.discard_stage("activity-plan")
            plan = self._stage("activity-plan", lambda: activity_plan_prompt(analysis))
            planned = validate_plan(
                plan,
                fallback_prerequisite_id=prerequisite_ids[0] if prerequisite_ids else None,
            )
        batches: list[dict[str, Any]] = []
        for activity_type in ("mcq", "interactive"):
            for difficulty in ("easy", "moderate", "challenging"):
                slice_ = [item for item in planned if item["type"] == activity_type and item["difficulty"] == difficulty]
                name = f"{activity_type}-{difficulty}"
                batch = self._activity_batch(name, analysis, slice_, source_location)
                batches.append(batch)
        package = assemble_package(config, analysis, plan, batches)
        return package, analysis, batches

    def audit_and_repair(self, package: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
        findings: list[dict[str, Any]] = []
        for index in range(0, len(package["activities"]), 3):
            group = package["activities"][index:index + 3]
            name = f"semantic-audit-{index // 3 + 1:02d}"
            audit = self._audit_stage(name, lambda group=group: semantic_audit_prompt(group))
            findings.extend(audit.get("findings", []))
        whole_audit = self._audit_stage(
            "whole-package-audit",
            lambda: whole_package_audit_prompt(package),
        )
        findings.extend(whole_audit.get("findings", []))
        blockers = [item for item in findings if item.get("severity") == "blocker"]
        by_id = {item["id"]: item for item in package["activities"]}
        unresolved = [item for item in blockers if item.get("activityId") not in by_id]
        if unresolved:
            raise ValidationFailure(
                "Semantic audit returned blocker findings without a valid activity ID",
                [str(item) for item in unresolved],
            )
        for activity_id in sorted({item.get("activityId") for item in blockers if item.get("activityId")}):
            activity_findings = [item.get("message", "unspecified blocker") for item in blockers if item.get("activityId") == activity_id]
            name = f"semantic-repair-{activity_id}"
            replacement = self._repair_stage(
                name,
                by_id[activity_id],
                lambda activity_id=activity_id, activity_findings=activity_findings: repair_activity_prompt(
                    by_id[activity_id], activity_findings,
                ),
            )
            by_id[activity_id] = replacement
        package["activities"] = [by_id[item["id"]] for item in package["activities"]]
        return package, findings

    def repair_validation_errors(self, package: dict[str, Any], errors: list[str], attempt: int) -> dict[str, Any]:
        import re

        indices = sorted({int(match.group(1)) for error in errors if (match := re.search(r"activity\[(\d+)\]", error))})
        if not indices:
            return package
        for index in indices:
            activity = package["activities"][index]
            relevant = [error for error in errors if f"activity[{index}]" in error]
            name = f"repair-{attempt:02d}-activity-{index:02d}"
            replacement = self._repair_stage(
                name,
                activity,
                lambda: repair_activity_prompt(activity, relevant),
            )
            package["activities"][index] = replacement
        return package
